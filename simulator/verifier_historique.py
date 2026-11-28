
import pandas as pd

from pathlib import Path


fichier = (
    Path(__file__).resolve().parent
    / "data"
    / "historique_2026-11-28.csv"
)

df = pd.read_csv(fichier)

# Conversion des dates.
df["horodatage"] = pd.to_datetime(
    df["horodatage"],
    utc=True
)

# Sélection d'une borne.
code_borne = "MRK-001"

borne = df[df["code_borne"] == code_borne].copy()

print("Historique de la borne :")
print(borne)

# Mesures des dernières 24 heures.
maintenant = borne["horodatage"].max()

mesures_24h = borne[
    (borne["horodatage"] >= maintenant - pd.Timedelta(hours=24))
    & (borne["type"] == "meter")
]

# Température moyenne et maximale sur 24 h.
temperature_moy_24h = mesures_24h["temperature_c"].mean()
temperature_max_24h = mesures_24h["temperature_c"].max()

# Température maximale sur 1 h.
mesures_1h = mesures_24h[
    mesures_24h["horodatage"] >= maintenant - pd.Timedelta(hours=1)
]

temperature_max_1h = mesures_1h["temperature_c"].max()

# Tension moyenne sur 24 h.
tension_moy_24h = mesures_24h["tension_v"].mean()

# Nombre de sessions terminées sur 24 h.
sessions_24h = borne[
    (borne["type"] == "session/stop")
    & (borne["horodatage"] >= maintenant - pd.Timedelta(hours=24))
]

nb_sessions_24h = len(sessions_24h)

# Nombre de mesures disponibles sur 24 h.
nb_mesures_24h = len(mesures_24h)

print("\nIndicateurs disponibles :")
print("Température moyenne 24h :", temperature_moy_24h)
print("Température maximale 24h :", temperature_max_24h)
print("Température maximale 1h :", temperature_max_1h)
print("Tension moyenne 24h :", tension_moy_24h)
print("Nombre de sessions 24h :", nb_sessions_24h)
print("Nombre de mesures 24h :", nb_mesures_24h)
