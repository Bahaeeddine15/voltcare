import csv
import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import paho.mqtt.client as mqtt

from config import BORNES, MQTT_HOST, MQTT_PASSWORD, MQTT_PORT, MQTT_USERNAME

from historique import enregistrer


LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
CSV_LOG_PATH = Path(os.getenv("CSV_LOG_PATH", str(BASE_DIR / "messages.csv")))

_MESSAGE_TYPES = {
    "boot": (1, False),
    "status": (1, True),
    "session/start": (1, False),
    "session/stop": (1, False),
    "meter": (0, False),
    "heartbeat": (0, False),
}

_REQUIRED_FIELDS = {
    "boot": {
        "code_station",
        "fabricant",
        "modele",
        "puissance_max_kw",
    },
    "status": {"connecteur_id", "statut", "code_erreur"},
    "session/start": {
        "connecteur_id",
        "transaction_id",
        "id_tag",
        "compteur_debut_wh",
    },
    "session/stop": {
        "transaction_id",
        "id_tag",
        "compteur_fin_wh",
        "raison",
    },
    "meter": {
        "connecteur_id",
        "transaction_id",
        "energie_wh",
        "puissance_w",
        "tension_v",
        "courant_a",
        "temperature_c",
    },
    "heartbeat": set(),
}

_OPTIONAL_FIELDS = {
    "boot": {"firmware"},
    "status": {"info"},
    "session/start": set(),
    "session/stop": set(),
    "meter": set(),
    "heartbeat": set(),
}

_client: mqtt.Client | None = None
_client_lock = threading.Lock()
_csv_lock = threading.Lock()
_connected = threading.Event()


def _on_connect(client, userdata, flags, reason_code, properties=None) -> None:
    if reason_code == mqtt.MQTT_ERR_SUCCESS:
        _connected.set()
    else:
        LOGGER.error("Connexion MQTT refusée (code %s).", reason_code)


def _on_disconnect(client, userdata, reason_code, properties=None) -> None:
    _connected.clear()


def _get_client() -> mqtt.Client:
    global _client

    with _client_lock:
        if _client is None:
            if not MQTT_USERNAME or not MQTT_PASSWORD:
                raise RuntimeError(
                    "MQTT_USERNAME et MQTT_PASSWORD doivent être définis dans .env."
                )

            client = mqtt.Client()
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            client.reconnect_delay_set(min_delay=1, max_delay=120)
            client.on_connect = _on_connect
            client.on_disconnect = _on_disconnect
            client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_start()
            _client = client
        else:
            client = _client

    if not _connected.wait(timeout=10):
        raise RuntimeError(
            f"Connexion MQTT impossible sur {MQTT_HOST}:{MQTT_PORT} après 10 secondes."
        )
    return client


def _enregistrer_csv(topic: str, message: Mapping[str, Any]) -> None:
    with _csv_lock:
        CSV_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        write_header = not CSV_LOG_PATH.exists() or CSV_LOG_PATH.stat().st_size == 0

        with CSV_LOG_PATH.open("a", encoding="utf-8", newline="") as fichier:
            writer = csv.DictWriter(fichier, fieldnames=("topic", "payload"))
            if write_header:
                writer.writeheader()
            writer.writerow(
                {
                    "topic": topic,
                    "payload": json.dumps(
                        message,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                }
            )


def publier(type: str, code_borne: str, donnees: Mapping[str, Any]) -> dict[str, Any]:
    """Publie un message conforme au contrat MQTT VoltCare v1.0."""
    if type not in _MESSAGE_TYPES:
        raise ValueError(f"Type de message MQTT inconnu : {type!r}.")
    if not isinstance(code_borne, str) or not code_borne or "/" in code_borne:
        raise ValueError("code_borne doit être un code non vide sans '/'.")
    if not isinstance(donnees, Mapping):
        raise TypeError("donnees doit être un mapping de champs du contrat.")

    donnees_message = dict(donnees)
    if type == "boot":
        borne = next((borne for borne in BORNES if borne.code == code_borne), None)
        if borne is not None:
            configuration_boot = {
                "code_station": borne.station_code,
                "fabricant": borne.fabricant,
                "modele": borne.modele,
                "puissance_max_kw": borne.puissance_kw,
            }
            if borne.firmware is not None:
                configuration_boot["firmware"] = borne.firmware
            for champ, valeur in configuration_boot.items():
                donnees_message.setdefault(champ, valeur)

    allowed_fields = _REQUIRED_FIELDS[type] | _OPTIONAL_FIELDS[type]
    missing_fields = _REQUIRED_FIELDS[type] - donnees_message.keys()
    extra_fields = donnees_message.keys() - allowed_fields
    if missing_fields or extra_fields:
        details = []
        if missing_fields:
            details.append(f"champs requis absents : {sorted(missing_fields)}")
        if extra_fields:
            details.append(f"champs inconnus : {sorted(extra_fields)}")
        raise ValueError(f"Message {type!r} invalide ({'; '.join(details)}).")

    topic = f"voltcare/bornes/{code_borne}/{type}"
    message = {
        "version": "1.0",
        "message_id": str(uuid.uuid4()),
        "code_borne": code_borne,
        "horodatage": (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        ),
        **donnees_message,
    }
    qos, retain = _MESSAGE_TYPES[type]
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":"))

    result = _get_client().publish(topic, payload, qos=qos, retain=retain)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError(
            f"Échec de publication MQTT sur {topic} (code {result.rc})."
        )

    # Enregistrement dans l'historique structure du simulateur.
    enregistrer(topic, message)

    try:
        _enregistrer_csv(topic, message)
    except OSError:
        LOGGER.exception("Impossible d'enregistrer le message MQTT dans le CSV.")
        raise

    return message
