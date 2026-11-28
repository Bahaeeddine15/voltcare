
"""Enregistrement asynchrone des messages MQTT dans un CSV quotidien."""

import atexit
import csv
import logging
import queue
import threading

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from config import BORNES


LOGGER = logging.getLogger(__name__)

# Dossier contenant les historiques quotidiens.
DATA_DIR = Path(__file__).resolve().parent / "data"

# Colonnes du fichier CSV, dans l'ordre défini par le ticket.
COLONNES = [
    "horodatage",
    "code_borne",
    "code_station",
    "type",
    "statut",
    "code_erreur",
    "transaction_id",
    "id_tag",
    "compteur_wh",
    "energie_wh",
    "puissance_w",
    "tension_v",
    "temperature_c",
    "raison_arret",
    "date_mise_en_service",
]

# Correspondance entre les codes des bornes et leur configuration.
BORNES_PAR_CODE = {
    borne.code: borne
    for borne in BORNES
}

# File d'attente partagée entre le Publisher et le thread CSV.
_file_attente = queue.Queue()

_thread = None
_lock = threading.Lock()

# Objet spécial signalant au thread qu'il doit s'arrêter.
_ARRET = object()


def _demarrer_thread():
    """Démarre le thread d'écriture une seule fois."""

    global _thread

    with _lock:
        if _thread is None or not _thread.is_alive():

            _thread = threading.Thread(
                target=_traiter_messages,
                name="historique-csv",
                daemon=True,
            )

            _thread.start()


def _extraire_type(topic: str) -> str:
    """Extrait le type du message depuis son topic MQTT."""

    parties = topic.split("/")

    if len(parties) < 4 or parties[:2] != ["voltcare", "bornes"]:
        raise ValueError(f"Topic MQTT invalide : {topic}")

    return "/".join(parties[3:])


def _convertir_en_datetime(horodatage: str) -> datetime:
    """Convertit un horodatage ISO 8601 en date UTC."""

    valeur = datetime.fromisoformat(
        horodatage.replace("Z", "+00:00")
    )

    if valeur.tzinfo is None:
        valeur = valeur.replace(tzinfo=timezone.utc)

    return valeur.astimezone(timezone.utc)


def _construire_ligne(
    topic: str,
    message: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un message MQTT en ligne CSV."""

    code_borne = message["code_borne"]
    horodatage = message["horodatage"]

    type_message = _extraire_type(topic)

    # Vérification de la cohérence entre le topic et le message.
    parties = topic.split("/")
    if parties[2] != code_borne:
        raise ValueError(
            "Le code borne du topic ne correspond pas au payload."
        )

    # Informations complémentaires issues de config.py.
    borne = BORNES_PAR_CODE.get(code_borne)

    ligne = {
        colonne: ""
        for colonne in COLONNES
    }

    ligne.update({
        "horodatage": horodatage,
        "code_borne": code_borne,
        "code_station": borne.station_code if borne else "",
        "type": type_message,
        "date_mise_en_service": (
            borne.date_mise_en_service.isoformat()
            if borne else ""
        ),
    })

    # Champs communs à certains types de messages.
    champs_directs = (
        "statut",
        "code_erreur",
        "transaction_id",
        "id_tag",
        "energie_wh",
        "puissance_w",
        "tension_v",
        "temperature_c",
    )

    for champ in champs_directs:
        if champ in message:
            ligne[champ] = message[champ]

    # Compteur de début ou de fin de session.
    if type_message == "session/start":
        ligne["compteur_wh"] = message.get(
            "compteur_debut_wh", ""
        )

    elif type_message == "session/stop":
        ligne["compteur_wh"] = message.get(
            "compteur_fin_wh", ""
        )

        ligne["raison_arret"] = message.get(
            "raison", ""
        )

    return ligne


def _ecrire_message(topic: str, message: Mapping[str, Any]):
    """Écrit un message dans le fichier CSV correspondant à sa date."""

    ligne = _construire_ligne(topic, message)

    # Le fichier est choisi selon la date UTC du message.
    date_message = _convertir_en_datetime(
        ligne["horodatage"]
    )

    nom_fichier = (
        f"historique_{date_message:%Y-%m-%d}.csv"
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    chemin = DATA_DIR / nom_fichier

    # L'en-tête est écrit uniquement si le fichier est nouveau ou vide.
    ecrire_entete = (
        not chemin.exists()
        or chemin.stat().st_size == 0
    )

    with chemin.open(
        "a",
        encoding="utf-8",
        newline=""
    ) as fichier:

        writer = csv.DictWriter(
            fichier,
            fieldnames=COLONNES,
            extrasaction="ignore",
        )

        if ecrire_entete:
            writer.writeheader()

        writer.writerow(ligne)

        # Rend la ligne disponible sans attendre la fermeture du fichier.
        fichier.flush()


def _traiter_messages():
    """Consomme la Queue et écrit les messages sur le disque."""

    while True:
        element = _file_attente.get()

        try:
            if element is _ARRET:
                return

            topic, message = element

            try:
                _ecrire_message(topic, message)

            except Exception:
                LOGGER.exception(
                    "Erreur lors de l'enregistrement CSV du message."
                )

        finally:
            _file_attente.task_done()


def enregistrer(
    topic: str,
    message: Mapping[str, Any]
) -> None:
    """Place un message MQTT dans la file d'attente sans écrire sur le disque."""

    if not isinstance(message, Mapping):
        raise TypeError("message doit être un mapping.")

    copie_message = dict(message)

    _demarrer_thread()

    _file_attente.put_nowait(
        (topic, copie_message)
    )


def attendre_ecriture() -> None:
    """Attend que tous les messages en attente soient écrits."""

    _file_attente.join()


def fermer() -> None:
    """Vide la Queue et arrête proprement le thread d'écriture."""

    global _thread

    with _lock:
        thread = _thread

        if thread is None:
            return

        _file_attente.put(_ARRET)

    # Attend la fin de toutes les écritures.
    _file_attente.join()
    thread.join()

    with _lock:
        if _thread is thread:
            _thread = None


# Garantit un arrêt propre à la fermeture normale du processus.
atexit.register(fermer)
