# VoltCare – Python Simulator

## 1. Présentation

Le simulateur Python de VoltCare permet de représenter les bornes de recharge électrique du projet et de préparer leur communication avec les autres composants du système.

Il centralise les caractéristiques des bornes et les paramètres nécessaires à la communication MQTT et à l'utilisation du protocole OCPP.

## 2. Structure

```text
simulator/
├── config.py
├── requirements.txt
├── .env
├── .env.example
└── tests/
    └── test_config.py
```

- `config.py` : configuration des 15 bornes et paramètres de connexion.
- `requirements.txt` : dépendances Python nécessaires.
- `.env` : variables d'environnement privées.
- `.env.example` : modèle de configuration à copier.
- `tests/test_config.py` : tests automatisés de la configuration.

Le dossier `.venv/` est créé localement par chaque développeur et ne doit pas être versionné.

## 3. Prérequis

- Python 3.11 ou version compatible.
- Docker Desktop installé et démarré pour utiliser le broker MQTT.
- Git pour récupérer le projet.

Vérifier Python :

```powershell
python --version
```

## 4. Créer l'environnement virtuel

Depuis le dossier `simulator` :

```powershell
python -m venv .venv
```

Activer l'environnement virtuel sous Windows PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
```

Le préfixe `(.venv)` doit apparaître dans le terminal.

## 5. Installer les dépendances

```powershell
pip install -r requirements.txt
```

Les principales bibliothèques utilisées sont :

| Bibliothèque | Utilité |
|---|---|
| `ocpp` | Gestion du protocole OCPP |
| `websockets` | Communication WebSocket |
| `paho-mqtt` | Communication MQTT |
| `python-dotenv` | Chargement des variables d'environnement |
| `pytest` | Exécution des tests |

## 6. Configurer les variables d'environnement

Créer son fichier `.env` à partir du modèle :

```powershell
Copy-Item .env.example .env
```

Ouvrir `.env` et renseigner les paramètres :

```dotenv
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=voltcare
MQTT_PASSWORD=VOTRE_MOT_DE_PASSE
OCPP_PORT=9000
```

Remplacer `VOTRE_MOT_DE_PASSE` par le mot de passe choisi lors de la création du fichier `mosquitto/passwd`.

Les identifiants doivent correspondre à ceux configurés dans Mosquitto.

**Important :**
- Ne jamais partager son fichier `.env` sur Git.
- Ne jamais remplacer `.env.example` par son fichier privé.
- En environnement Docker, utiliser le nom du service `mosquitto` comme hôte MQTT plutôt que `localhost`.

## 7. Vérifier la configuration

Depuis le dossier `simulator` :

```powershell
python config.py
```

La configuration doit afficher :

```text
Configuration valid: 15 chargers
```

Les 15 bornes doivent ensuite être affichées avec leurs stations, fabricants, modèles et puissances.

## 8. Exécuter les tests

Depuis le dossier `simulator` :

```powershell
python -m pytest -v
```

Les tests vérifient notamment :

- Le nombre total de bornes.
- L'unicité des codes.
- La présence de cinq bornes par ville.
- La cohérence des affectations aux stations.
- La validation générale de la configuration.

Les tests doivent se terminer sans erreur.

## 9. Démarrage du broker MQTT

Avant de lancer un composant du simulateur qui communique avec MQTT, vérifier que Mosquitto est démarré.

Depuis la racine du projet :

```powershell
docker compose up -d
docker compose ps
```

Le broker doit être accessible sur :

```text
localhost:1883
```

## 10. Remarques

- Le port MQTT est `1883`.
- Le port OCPP configuré est `9000`. Il est destiné au serveur OCPP et ne signifie pas que ce serveur est déjà démarré.
- Chaque développeur configure son propre environnement local.
- Les identifiants et les environnements virtuels ne doivent pas être versionnés.

