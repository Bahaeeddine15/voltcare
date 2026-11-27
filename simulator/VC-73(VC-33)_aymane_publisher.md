# VC-73 (VC-33) — Publisher MQTT

## Objectif

Publier les événements d'une borne sur Mosquitto au format du contrat MQTT
VoltCare v1.0, défini dans `docs/contrat-mqtt.md` §§ 3 à 5.

Le livrable applicatif de ce ticket est `simulator/publisher.py`. Le serveur
central OCPP, le client borne et le modèle physique des mesures relèvent de
tickets distincts.

## Fonction de publication

Le serveur central peut appeler :

```python
from publisher import publier

publier("status", "MRK-001", {
    "connecteur_id": 1,
    "statut": "Available",
    "code_erreur": "NoError",
})
```

La signature est `publier(type, code_borne, donnees)`. La fonction vérifie le
type et les champs attendus, construit l'enveloppe, publie sur MQTT et renvoie
le message construit.

Pour `boot`, les champs `code_station`, `fabricant`, `modele` et
`puissance_max_kw` sont repris de `BORNES` dans `config.py` lorsque
`code_borne` correspond à une borne configurée. `firmware` est ajouté si la
configuration en contient un. Les autres données métier sont fournies par
l'appelant.

## Topics et options MQTT

| Type | Topic | QoS | Retain |
|---|---|---:|---|
| `boot` | `voltcare/bornes/{code_borne}/boot` | 1 | non |
| `status` | `voltcare/bornes/{code_borne}/status` | 1 | oui |
| `session/start` | `voltcare/bornes/{code_borne}/session/start` | 1 | non |
| `session/stop` | `voltcare/bornes/{code_borne}/session/stop` | 1 | non |
| `meter` | `voltcare/bornes/{code_borne}/meter` | 0 | non |
| `heartbeat` | `voltcare/bornes/{code_borne}/heartbeat` | 0 | non |

Chaque payload JSON contient l'enveloppe commune :

- `version`: `"1.0"`
- `message_id`: UUID v4
- `code_borne`: code correspondant au topic
- `horodatage`: date UTC au format ISO 8601

Les champs métier sont ensuite ajoutés en snake_case selon le type. Les champs
obligatoires manquants et les champs inconnus sont refusés avant publication.

## Connexion et journal CSV

La connexion utilise `MQTT_HOST`, `MQTT_PORT`, `MQTT_USERNAME` et
`MQTT_PASSWORD` chargés par `config.py` depuis `simulator/.env`. Le client Paho
utilise la reconnexion automatique et attend la connexion initiale avant de
publier. Une erreur de connexion ou de publication est signalée à l'appelant.

Après acceptation par le client MQTT, chaque message est ajouté à un CSV avec
les colonnes `topic` et `payload`. Par défaut, le fichier est
`simulator/messages.csv`. Son emplacement peut être défini par la variable
d'environnement `CSV_LOG_PATH`.

**Limite d'intégration :** aucun enregistreur CSV commun de la sous-tâche US-07
n'a été trouvé dans le dépôt au moment de ce ticket. Le publisher écrit donc
dans son propre fichier; son raccord au logger US-07 reste à coordonner si ce
logger fournit une API commune.

## Tests et vérifications

Depuis `simulator/`, exécuter les tests automatisés :

```powershell
python -m pytest -q
```

Les tests couvrent les six types, les topics, les champs de l'enveloppe,
les niveaux QoS/retain, les validations, l'utilisation de la configuration
`BORNES`, les identifiants MQTT, l'enregistrement CSV et la gestion d'un échec
de publication.

La vérification manuelle effectuée avec Mosquitto a confirmé :

- la réception des six types par un abonnement à
  `voltcare/bornes/+/#` ;
- la réception immédiate du dernier `status` retenu lors d'un nouvel
  abonnement ;
- la reprise des publications après le redémarrage du broker.

Pour reproduire l'écoute depuis la racine du dépôt, remplacer le texte
indicatif par les identifiants locaux :

```powershell
docker compose exec mosquitto mosquitto_sub -h localhost -p 1883 `
  -u voltcare -P "MOT_DE_PASSE" -t "voltcare/bornes/+/#" -v
```

Le mot de passe réel ne doit pas être ajouté à ce document ni commité.
