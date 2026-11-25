
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# ENVIRONMENT CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

OCPP_PORT = int(os.getenv("OCPP_PORT", "9000"))

# CHARGING STATION CONFIGURATION

@dataclass(frozen=True)
class BorneConfig:
    code: str
    ville: str
    station_code: str
    fabricant: str
    modele: str
    puissance_kw: float
    firmware: str | None = None


# Characteristics copied from donnees-demo.apex.
# The same five charger configurations are repeated
# in each city.

BORNE_MODELES = (
    {
        "fabricant": "ABB",
        "modele": "Terra AC W22",
        "puissance_kw": 22,
    },
    {
        "fabricant": "Schneider Electric",
        "modele": "EVlink Pro AC",
        "puissance_kw": 22,
    },
    {
        "fabricant": "Wallbox",
        "modele": "Commander 2",
        "puissance_kw": 11,
    },
    {
        "fabricant": "ABB",
        "modele": "Terra AC W22",
        "puissance_kw": 22,
    },
    {
        "fabricant": "Schneider Electric",
        "modele": "EVlink Pro AC",
        "puissance_kw": 22,
    },
)

VILLES = ("MRK", "CAS", "RBT")


def build_bornes() -> list[BorneConfig]:
    bornes = []

    for ville in VILLES:
        for numero, modele in enumerate(BORNE_MODELES, start=1):

            station_numero = "01" if numero <= 3 else "02"

            borne = BorneConfig(
                code=f"{ville}-{numero:03d}",
                ville=ville,
                station_code=f"ST-{ville}-{station_numero}",
                **modele,
            )

            bornes.append(borne)

    return bornes


BORNES = build_bornes()

# CONFIGURATION VALIDATION

def validate_configuration() -> None:
    if len(BORNES) != 15:
        raise ValueError("Exactly 15 chargers are required.")

    codes = [borne.code for borne in BORNES]

    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate charger codes found.")

    for ville in VILLES:
        bornes_ville = [
            borne for borne in BORNES
            if borne.ville == ville
        ]

        if len(bornes_ville) != 5:
            raise ValueError(f"Expected 5 chargers for {ville}.")

    for borne in BORNES:
        numero = int(borne.code[-3:])

        expected_station = (
            f"ST-{borne.ville}-01"
            if numero <= 3
            else f"ST-{borne.ville}-02"
        )

        if borne.station_code != expected_station:
            raise ValueError(
                f"Incorrect station assignment for {borne.code}."
            )

        if not borne.fabricant or not borne.modele:
            raise ValueError(f"Missing metadata for {borne.code}.")

        if borne.puissance_kw <= 0:
            raise ValueError(f"Invalid power for {borne.code}.")


if __name__ == "__main__":
    validate_configuration()

    print(f"Configuration valid: {len(BORNES)} chargers")

    for borne in BORNES:
        print(
            f"{borne.code} | {borne.station_code} | "
            f"{borne.fabricant} | {borne.modele} | "
            f"{borne.puissance_kw} kW"
        )
