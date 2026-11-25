# VoltCare – Mosquitto

## 1. Présentation

Ce dossier contient la configuration du broker MQTT Mosquitto utilisé dans le projet VoltCare.

Mosquitto permet aux différents composants du système de communiquer en échangeant des messages MQTT.

Le broker est lancé avec Docker Compose depuis la racine du projet.

## 2. Structure

```text
mosquitto/
├── mosquitto.conf
├── passwd
└── data/
```

- `mosquitto.conf` : configuration du broker MQTT.
- `passwd` : fichier contenant les utilisateurs et les mots de passe hachés.
- `data/` : données persistantes du broker.

**Important :** les fichiers `passwd` et le contenu de `data/` sont locaux et ne doivent pas être envoyés sur Git.

## 3. Prérequis

- Docker Desktop installé et démarré.
- Docker Compose disponible.

Vérifier Docker :

```powershell
docker version
docker compose version
```

## 4. Configuration des identifiants

Depuis la racine du projet `voltcare`, créer le fichier `passwd` :

```powershell
docker run --rm -it -v "${PWD}/mosquitto:/mosquitto/config" eclipse-mosquitto:2 mosquitto_passwd -c /mosquitto/config/passwd voltcare
```

Saisir un mot de passe, puis le confirmer.

La saisie est invisible dans le terminal : c'est normal.

Chaque membre doit utiliser ses propres identifiants pour son environnement local.

Si le fichier `passwd` existe déjà, ne pas relancer cette commande avec `-c` : cela remplacerait le fichier existant.

### Permissions du fichier

Mosquitto doit pouvoir lire le fichier `passwd`.

Si nécessaire, depuis la racine du projet, exécuter :

```powershell
docker run --rm --user root -v "${PWD}/mosquitto:/mosquitto/config" --entrypoint sh eclipse-mosquitto:2 -c "chmod 644 /mosquitto/config/passwd"
```

## 5. Démarrer Mosquitto

Depuis la racine du projet :

```powershell
docker compose up -d
```

Vérifier l'état du conteneur :

```powershell
docker compose ps
```

Le conteneur `voltcare-mosquitto` doit avoir le statut `Up`.

Consulter les logs :

```powershell
docker compose logs -f mosquitto
```

Pour arrêter le service :

```powershell
docker compose down
```

Cette commande arrête et supprime le conteneur et le réseau Compose, mais conserve le volume Docker nommé `mosquitto_data`.

## 6. Tester la communication MQTT

Ouvrir deux terminaux PowerShell depuis la racine du projet.

### Terminal 1 : abonnement

```powershell
docker compose exec mosquitto mosquitto_sub -h localhost -p 1883 -u voltcare -P "VOTRE_MOT_DE_PASSE" -t "voltcare/#" -v
```

Remplacer `VOTRE_MOT_DE_PASSE` par le mot de passe local.

### Terminal 2 : publication

```powershell
docker compose exec mosquitto mosquitto_pub -h localhost -p 1883 -u voltcare -P "VOTRE_MOT_DE_PASSE" -t "voltcare/test" -m "Hello VoltCare"
```

Le premier terminal doit afficher :

```text
voltcare/test Hello VoltCare
```

Ce résultat confirme que le broker reçoit et transmet correctement les messages MQTT.

## 7. Informations de connexion

| Paramètre | Valeur |
|---|---|
| Hôte local | `localhost` |
| Port MQTT | `1883` |
| Utilisateur local | `voltcare` |
| Authentification | Obligatoire |

Si un composant s'exécute dans un autre conteneur Docker du même réseau Compose, utiliser le nom du service `mosquitto` comme hôte au lieu de `localhost`.

