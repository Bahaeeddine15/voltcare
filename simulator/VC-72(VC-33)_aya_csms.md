# CSMS OCPP 1.6 — Serveur central VoltCare

## Objectif

Mettre en place un serveur central CSMS (*Charging Station Management System*) capable de recevoir et de traiter les messages OCPP 1.6J envoyés par les bornes simulées.

Le serveur utilise les bibliothèques Python `ocpp` et `websockets`. Chaque borne se connecte à l'adresse `ws://localhost:9000/{code_borne}`.

Le livrable principal de cette tâche est `simulator/csms.py`. La publication MQTT est déléguée à `simulator/publisher.py`, développé dans une sous-tâche distincte. Le client borne et le modèle physique des mesures ne font pas partie de ce ticket.

Référence : `docs/contrat-mqtt.md` §§ 1 et 3.

## Connexion des bornes

Le CSMS écoute sur `127.0.0.1`, port `9000`, avec le sous-protocole WebSocket `ocpp1.6`.

Chaque connexion est associée au code de la borne, extrait de l'URL. Le serveur vérifie que ce code est présent dans la configuration `BORNES` de `config.py`.

Exemple de connexion :

```text
ws://localhost:9000/MRK-001
```

Une connexion utilisant un code inconnu ou un sous-protocole non autorisé est refusée.

Le serveur gère les connexions des bornes de manière asynchrone avec `asyncio`.

## Messages OCPP pris en charge

Les six handlers OCPP suivants sont implémentés dans la classe `BorneOCPP`.

| Message OCPP | Traitement du CSMS | Réponse |
|---|---|---|
| `BootNotification` | Reçoit les informations du fabricant et du modèle | `Accepted`, heartbeat toutes les 60 s |
| `StatusNotification` | Reçoit le statut de la borne et son code d'erreur | Confirmation de réception |
| `StartTransaction` | Vérifie le connecteur et crée un identifiant de transaction | `transaction_id`, `idTagInfo: Accepted` |
| `StopTransaction` | Vérifie la transaction active et traite sa fin | `idTagInfo: Accepted` si valide |
| `MeterValues` | Extrait les mesures électriques et thermiques | Confirmation de réception |
| `Heartbeat` | Reçoit le signal de présence de la borne | Date et heure UTC du serveur |

Le CSMS prend en charge un seul connecteur par borne (`connector_id = 1`), conformément au contrat MQTT.

### Gestion des transactions

Lors d'un `StartTransaction`, le serveur attribue un identifiant numérique unique pendant son exécution.

Les transactions actives sont conservées en mémoire pour vérifier les messages `StopTransaction` et éviter qu'une même connexion démarre plusieurs transactions simultanément.

Les identifiants ne sont pas conservés après redémarrage du CSMS. La persistance des transactions n'est pas implémentée dans cette tâche.

### Traitement des mesures

Le handler `MeterValues` extrait les indicateurs suivants :

| Mesure OCPP | Champ transmis au publisher |
|---|---|
| `Energy.Active.Import.Register` | `energie_wh` |
| `Power.Active.Import` | `puissance_w` |
| `Voltage` | `tension_v` |
| `Current.Import` | `courant_a` |
| `Temperature` | `temperature_c` |

Les valeurs d'énergie en `kWh` et de puissance en `kW` sont converties respectivement en `Wh` et en `W`.

Les mesures incomplètes, les unités non prises en charge et les valeurs numériques invalides sont signalées dans les logs. Une mesure incomplète n'est pas transmise au publisher.

## Intégration avec le module MQTT

Chaque handler transmet les données reçues à la fonction `publier()` du module `publisher.py`.

Exemple :

```python
await mqtt_publier("status", self.code_borne, {
    "connecteur_id": 1,
    "statut": status,
    "code_erreur": error_code,
})
```

La fonction `mqtt_publier()` sert d'intermédiaire entre les handlers OCPP et le publisher MQTT existant.

| Message OCPP | Type transmis au publisher |
|---|---|
| `BootNotification` | `boot` |
| `StatusNotification` | `status` |
| `StartTransaction` | `session/start` |
| `StopTransaction` | `session/stop` |
| `MeterValues` | `meter` |
| `Heartbeat` | `heartbeat` |

Le CSMS ne construit pas directement les messages MQTT et n'établit pas lui-même de connexion au broker. La construction des payloads JSON, la validation des champs, les topics et les paramètres QoS/retain sont gérés par `publisher.py`.

La publication est lancée dans une tâche asynchrone pour éviter qu'une indisponibilité de Mosquitto bloque les réponses OCPP.

**Limite d'intégration :** cette version ne garantit pas la livraison ni l'ordre des publications MQTT en cas de panne ou d'arrêt immédiat du serveur. Les erreurs de publication sont journalisées.

## Lancement du serveur

Depuis la racine du dépôt, avec l'environnement Python et les dépendances installés :

```powershell
python simulator/csms.py
```

Le serveur affiche un message indiquant qu'il écoute sur le port `9000` :

```text
CSMS VoltCare pret sur ws://localhost:9000/{code_borne}
```

Le processus doit rester actif pendant les tests des bornes.

Pour arrêter le serveur, utiliser `Ctrl + C`.

Le serveur fonctionne localement, sans TLS ni authentification d'une borne physique. Il est destiné à la simulation et aux tests du projet.

## Logs et suivi des événements

Le serveur utilise le module Python `logging` pour afficher les informations de connexion et les événements OCPP reçus.

Les logs permettent de suivre :

- la connexion et la déconnexion d'une borne ;
- le type de message OCPP reçu ;
- les changements de statut et les codes d'erreur ;
- le démarrage et la fin d'une transaction ;
- la réception des mesures et des heartbeats ;
- les publications MQTT réussies ou échouées.

Les fermetures normales des connexions WebSocket sont distinguées des interruptions anormales.

Les logs sont affichés directement dans le terminal. Le CSMS n'implémente pas de système de stockage supplémentaire.

## Tests et vérifications

Les tests automatisés se trouvent dans `simulator/tests/test_csms.py`.

Le CSMS doit être démarré dans un premier terminal avant leur exécution.

Depuis la racine du dépôt, lancer :

```powershell
python -m pytest simulator/tests/test_csms.py -v
```

Les tests couvrent les six handlers OCPP ainsi qu'un scénario complet de session de recharge.

La vérification effectuée a confirmé :

- la connexion d'une borne de test au serveur ;
- la réception des six types de messages OCPP ;
- le retour de réponses OCPP valides ;
- l'attribution et la réutilisation du même identifiant entre le début et la fin d'une session ;
- la transmission des événements au module MQTT ;
- la réponse du CSMS à `BootNotification` même lorsque Mosquitto est indisponible.

Le test effectué avec Mosquitto arrêté a réussi en **2,39 secondes**, ce qui confirme que la publication MQTT ne bloque pas la réponse OCPP dans ce scénario.

## Limites et périmètre

Le serveur CSMS est destiné à une simulation locale. Les fonctionnalités suivantes ne sont pas couvertes par cette tâche :

- développement du client de simulation des bornes ;
- génération physique des mesures ;
- implémentation du publisher MQTT ;
- persistance des transactions entre redémarrages ;
- sécurisation des connexions par TLS ou authentification des bornes ;
- intégration directe avec Salesforce.

Ces éléments relèvent d'autres sous-tâches du projet ou d'évolutions ultérieures.

Le CSMS fournit ainsi la partie serveur OCPP nécessaire à la communication entre les bornes simulées et le module de publication MQTT.