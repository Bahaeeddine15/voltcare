import csv
import json
from datetime import datetime
from types import SimpleNamespace

import paho.mqtt.client as mqtt
import pytest

import publisher


class FakeClient:
    def __init__(self):
        self.published = []
        self.username = None
        self.reconnect_delays = None
        self.connected_to = None
        self.loop_started = False
        self.on_connect = None
        self.on_disconnect = None

    def username_pw_set(self, username, password):
        self.username = (username, password)

    def reconnect_delay_set(self, min_delay, max_delay):
        self.reconnect_delays = (min_delay, max_delay)

    def connect_async(self, host, port, keepalive):
        self.connected_to = (host, port, keepalive)

    def loop_start(self):
        self.loop_started = True
        self.on_connect(self, None, {}, mqtt.MQTT_ERR_SUCCESS)

    def publish(self, topic, payload, qos, retain):
        self.published.append((topic, json.loads(payload), qos, retain))
        return SimpleNamespace(rc=mqtt.MQTT_ERR_SUCCESS)


@pytest.fixture
def fake_mqtt(monkeypatch, tmp_path):
    client = FakeClient()
    monkeypatch.setattr(publisher.mqtt, "Client", lambda: client)
    monkeypatch.setattr(publisher, "MQTT_USERNAME", "simulateur")
    monkeypatch.setattr(publisher, "MQTT_PASSWORD", "secret")
    monkeypatch.setattr(publisher, "MQTT_HOST", "localhost")
    monkeypatch.setattr(publisher, "MQTT_PORT", 1883)
    monkeypatch.setattr(publisher, "CSV_LOG_PATH", tmp_path / "messages.csv")
    monkeypatch.setattr(publisher, "_client", None)
    publisher._connected.clear()
    return client


@pytest.mark.parametrize(
    ("message_type", "data", "expected_qos", "expected_retain"),
    [
        (
            "boot",
            {
                "code_station": "ST-MRK-01",
                "fabricant": "VoltSim",
                "modele": "VS-22",
                "puissance_max_kw": 22,
                "firmware": "1.4.2",
            },
            1,
            False,
        ),
        (
            "status",
            {
                "connecteur_id": 1,
                "statut": "Available",
                "code_erreur": "NoError",
            },
            1,
            True,
        ),
        (
            "session/start",
            {
                "connecteur_id": 1,
                "transaction_id": 1287,
                "id_tag": "CLI-0042",
                "compteur_debut_wh": 1534200,
            },
            1,
            False,
        ),
        (
            "session/stop",
            {
                "transaction_id": 1287,
                "id_tag": "CLI-0042",
                "compteur_fin_wh": 1552600,
                "raison": "EVDisconnected",
            },
            1,
            False,
        ),
        (
            "meter",
            {
                "connecteur_id": 1,
                "transaction_id": None,
                "energie_wh": 1539800,
                "puissance_w": 0,
                "tension_v": 230.4,
                "courant_a": 0,
                "temperature_c": 47.2,
            },
            0,
            False,
        ),
        ("heartbeat", {}, 0, False),
    ],
)
def test_publier_envelope_topics_qos_retain_and_csv(
    fake_mqtt, message_type, data, expected_qos, expected_retain
):
    message = publisher.publier(message_type, "MRK-001", data)

    topic, published_message, qos, retain = fake_mqtt.published[0]
    assert topic == f"voltcare/bornes/MRK-001/{message_type}"
    assert published_message == message
    assert qos == expected_qos
    assert retain is expected_retain
    assert message["version"] == "1.0"
    assert message["code_borne"] == "MRK-001"
    assert message["message_id"]
    assert set(message) == {
        "version",
        "message_id",
        "code_borne",
        "horodatage",
        *data.keys(),
    }
    assert datetime.fromisoformat(message["horodatage"].replace("Z", "+00:00"))

    with (publisher.CSV_LOG_PATH).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [
        {
            "topic": topic,
            "payload": json.dumps(
                message,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
    ]


def test_publier_rejects_fields_outside_contract(fake_mqtt):
    with pytest.raises(ValueError, match="champs inconnus"):
        publisher.publier("heartbeat", "MRK-001", {"extra": True})

    assert not fake_mqtt.published


def test_boot_uses_existing_borne_configuration(fake_mqtt):
    message = publisher.publier("boot", "MRK-001", {})

    borne = next(b for b in publisher.BORNES if b.code == "MRK-001")
    assert message["code_station"] == borne.station_code
    assert message["fabricant"] == borne.fabricant
    assert message["modele"] == borne.modele
    assert message["puissance_max_kw"] == borne.puissance_kw


def test_publier_surfaces_mqtt_failure(monkeypatch, fake_mqtt):
    def fail_publish(*args, **kwargs):
        return SimpleNamespace(rc=mqtt.MQTT_ERR_NO_CONN)

    monkeypatch.setattr(fake_mqtt, "publish", fail_publish)
    with pytest.raises(RuntimeError, match="Échec de publication MQTT"):
        publisher.publier("heartbeat", "MRK-001", {})

    assert not publisher.CSV_LOG_PATH.exists()


def test_client_uses_credentials_and_reconnects(fake_mqtt):
    publisher.publier("heartbeat", "MRK-001", {})

    assert fake_mqtt.username == ("simulateur", "secret")
    assert fake_mqtt.reconnect_delays == (1, 120)
    assert fake_mqtt.connected_to == ("localhost", 1883, 60)
    assert fake_mqtt.loop_started
