
from publisher import publier
from historique import attendre_ecriture

# Test 1 : publier les informations de la borne
publier("boot", "MRK-001", {})

# Test 2 : publier le statut de la borne
publier("status", "MRK-001", {
    "connecteur_id": 1,
    "statut": "Available",
    "code_erreur": "NoError"
})

# Test 3 : publier les mesures
publier("meter", "MRK-001", {
    "connecteur_id": 1,
    "transaction_id": None,
    "energie_wh": 12500,
    "puissance_w": 7200,
    "tension_v": 230,
    "courant_a": 31.3,
    "temperature_c": 35
})

# Attendre que les messages soient écrits dans le CSV
attendre_ecriture()

print("Tests terminés !")
