
import csv

from datetime import datetime, timezone

import historique


def creer_message(type_message, donnees=None):
    """Construit un message MQTT de test."""

    message = {
        "version": "1.0",
        "message_id": "test-123",
        "code_borne": "MRK-001",
        "horodatage": "2026-11-28T09:30:00Z",
    }

    if donnees:
        message.update(donnees)

    topic = f"voltcare/bornes/MRK-001/{type_message}"

    return topic, message


def lire_csv(chemin):
    with chemin.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as fichier:
        return list(csv.DictReader(fichier))


def test_colonnes_csv():
    assert historique.COLONNES == [
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


def test_enregistrer_meter(monkeypatch, tmp_path):
    monkeypatch.setattr(
        historique,
        "DATA_DIR",
        tmp_path
    )

    topic, message = creer_message(
        "meter",
        {
            "transaction_id": 12,
            "energie_wh": 1539800,
            "puissance_w": 21800,
            "tension_v": 230.4,
            "temperature_c": 47.2,
            "courant_a": 31.6,
            "connecteur_id": 1,
        }
    )

    historique.enregistrer(topic, message)
    historique.attendre_ecriture()

    chemin = tmp_path / "historique_2026-11-28.csv"

    assert chemin.exists()

    lignes = lire_csv(chemin)

    assert len(lignes) == 1

    ligne = lignes[0]

    assert ligne["code_borne"] == "MRK-001"
    assert ligne["code_station"] == "ST-MRK-01"
    assert ligne["type"] == "meter"
    assert ligne["temperature_c"] == "47.2"
    assert ligne["tension_v"] == "230.4"
    assert ligne["energie_wh"] == "1539800"


def test_session_start_et_stop(monkeypatch, tmp_path):
    monkeypatch.setattr(
        historique,
        "DATA_DIR",
        tmp_path
    )

    topic_start, message_start = creer_message(
        "session/start",
        {
            "transaction_id": 12,
            "id_tag": "CLI-0042",
            "compteur_debut_wh": 10000,
            "connecteur_id": 1,
        }
    )

    topic_stop, message_stop = creer_message(
        "session/stop",
        {
            "transaction_id": 12,
            "id_tag": "CLI-0042",
            "compteur_fin_wh": 15000,
            "raison": "EVDisconnected",
        }
    )

    historique.enregistrer(topic_start, message_start)
    historique.enregistrer(topic_stop, message_stop)

    historique.attendre_ecriture()

    chemin = tmp_path / "historique_2026-11-28.csv"
    lignes = lire_csv(chemin)

    assert len(lignes) == 2

    assert lignes[0]["compteur_wh"] == "10000"
    assert lignes[1]["compteur_wh"] == "15000"
    assert lignes[1]["raison_arret"] == "EVDisconnected"


def test_status(monkeypatch, tmp_path):
    monkeypatch.setattr(
        historique,
        "DATA_DIR",
        tmp_path
    )

    topic, message = creer_message(
        "status",
        {
            "connecteur_id": 1,
            "statut": "Faulted",
            "code_erreur": "HighTemperature",
        }
    )

    historique.enregistrer(topic, message)
    historique.attendre_ecriture()

    lignes = lire_csv(
        tmp_path / "historique_2026-11-28.csv"
    )

    assert lignes[0]["statut"] == "Faulted"
    assert lignes[0]["code_erreur"] == "HighTemperature"


def test_en_tete_ecrit_une_seule_fois(monkeypatch, tmp_path):
    monkeypatch.setattr(
        historique,
        "DATA_DIR",
        tmp_path
    )

    for numero in range(3):
        topic, message = creer_message(
            "heartbeat",
            {
                "message_id": f"test-{numero}"
            }
        )

        historique.enregistrer(topic, message)

    historique.attendre_ecriture()

    chemin = tmp_path / "historique_2026-11-28.csv"

    with chemin.open(
        "r",
        encoding="utf-8"
    ) as fichier:
        lignes = fichier.readlines()

    assert len(lignes) == 4
    assert lignes[0].count("horodatage") == 1


def test_fichiers_differents_selon_date(monkeypatch, tmp_path):
    monkeypatch.setattr(
        historique,
        "DATA_DIR",
        tmp_path
    )

    dates = [
        "2026-11-28T23:59:00Z",
        "2026-11-29T00:01:00Z",
    ]

    for date_message in dates:
        topic, message = creer_message("heartbeat")
        message["horodatage"] = date_message

        historique.enregistrer(topic, message)

    historique.attendre_ecriture()

    assert (
        tmp_path / "historique_2026-11-28.csv"
    ).exists()

    assert (
        tmp_path / "historique_2026-11-29.csv"
    ).exists()


def test_date_mise_en_service(monkeypatch, tmp_path):
    monkeypatch.setattr(
        historique,
        "DATA_DIR",
        tmp_path
    )

    topic, message = creer_message("boot")

    historique.enregistrer(topic, message)
    historique.attendre_ecriture()

    ligne = lire_csv(
        tmp_path / "historique_2026-11-28.csv"
    )[0]

    assert ligne["date_mise_en_service"] == (
        historique.BORNES_PAR_CODE["MRK-001"]
        .date_mise_en_service.isoformat()
    )
