# Contrat d'interface — Platform Event `Borne_Event__e`

| | |
|---|---|
| **Version** | 1.0 |
| **Ticket** | VC-11 |
| **Producteur** | Passerelle MQTT → Salesforce (`gateway/`) |
| **Consommateur** | Salesforce — trigger Apex sur `Borne_Event__e` (`salesforce/`) |
| **Contrat amont** | `contrat-mqtt.md` v1.0 |
| **Statut** | Validé par l'équipe |

---

## 1. Principes

- La passerelle transforme les messages MQTT en **un seul type de Platform Event** : `Borne_Event__e`. Le champ `Type__c` indique de quel événement il s'agit.
- Un seul événement = **un seul trigger** à écrire et à tester côté Salesforce.
- La passerelle **ne contient aucune règle métier** : elle traduit, filtre, agrège et envoie. Toutes les décisions (statut Salesforce, création de ticket…) sont prises **dans Salesforce**.
- Les valeurs OCPP (statut, code d'erreur, raison d'arrêt) sont transmises **brutes** ; la conversion vers les statuts Salesforce est faite dans Salesforce (décision du contrat MQTT).

## 2. Ce que la passerelle envoie (et n'envoie pas)

| Message MQTT | Envoyé à Salesforce ? | `Type__c` | Délai |
|---|---|---|---|
| `boot` | Oui | `BOOT` | Immédiat |
| `status` | Oui | `STATUT` | Immédiat |
| `session/start` | Oui | `SESSION_DEBUT` | Immédiat |
| `session/stop` | Oui | `SESSION_FIN` | Immédiat |
| `meter` | **Agrégé** : 1 événement par borne et par **heure** | `MESURE_AGREGEE` | En fin d'heure |
| `heartbeat` | **Non**. La passerelle les surveille elle-même | — | — |
| Absence de heartbeat pendant 3 min | Oui | `INJOIGNABLE` | Immédiat |
| Reprise des heartbeats après un `INJOIGNABLE` | Oui | `JOIGNABLE` | Immédiat |

**Pourquoi agréger les mesures ?** 15 bornes × 1 mesure toutes les 30 s = 43 200 mesures par jour. Le stockage de la Developer Edition est limité, et chaque enregistrement compte pour environ 2 Ko. En agrégeant par heure, on passe à **360 enregistrements par jour**. La détection de panne n'est pas ralentie, car elle repose sur les événements `STATUT`, envoyés immédiatement.

## 3. Définition du Platform Event

**Objet** : `Borne_Event__e` — Label « Événement Borne » — Publish Behavior : *Publish After Commit*.

Les Platform Events n'acceptent pas les listes de sélection : les valeurs énumérées sont des champs **Texte**.

### 3.1 Champs communs (tous les types)

| Champ API | Type | Obligatoire | Source MQTT | Description |
|---|---|---|---|---|
| `Type__c` | Text(20) | oui | — | `BOOT`, `STATUT`, `SESSION_DEBUT`, `SESSION_FIN`, `MESURE_AGREGEE`, `INJOIGNABLE`, `JOIGNABLE` |
| `Message_Id__c` | Text(36) | oui | `message_id` | UUID, pour détecter les doublons. Pour `MESURE_AGREGEE`, `INJOIGNABLE` et `JOIGNABLE`, généré par la passerelle |
| `Code_Borne__c` | Text(20) | oui | `code_borne` | Ex. `MRK-001` |
| `Horodatage__c` | DateTime | oui | `horodatage` | Moment de l'événement côté borne |

### 3.2 Champs par type

| Champ API | Type | `BOOT` | `STATUT` | `SESSION_DEBUT` | `SESSION_FIN` | `MESURE_AGREGEE` | `INJOIGNABLE` | Source MQTT |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| `Code_Station__c` | Text(20) | ● | | | | | | `code_station` |
| `Fabricant__c` | Text(40) | ● | | | | | | `fabricant` |
| `Modele__c` | Text(40) | ● | | | | | | `modele` |
| `Puissance_Max_kW__c` | Number(5,1) | ● | | | | | | `puissance_max_kw` |
| `Statut_OCPP__c` | Text(20) | | ● | | | | | `statut` |
| `Code_Erreur__c` | Text(40) | | ● | | | | | `code_erreur` |
| `Info__c` | Text(50) | | ○ | | | | | `info` |
| `Transaction_Id__c` | Number(18,0) | | | ● | ● | | | `transaction_id` |
| `Id_Tag__c` | Text(20) | | | ● | ● | | | `id_tag` |
| `Compteur_Debut_Wh__c` | Number(18,0) | | | ● | | | | `compteur_debut_wh` |
| `Compteur_Fin_Wh__c` | Number(18,0) | | | | ● | | | `compteur_fin_wh` |
| `Raison_Arret__c` | Text(20) | | | | ● | | | `raison` |
| `Periode_Debut__c` | DateTime | | | | | ● | | calculé |
| `Periode_Fin__c` | DateTime | | | | | ● | | calculé |
| `Nb_Mesures__c` | Number(4,0) | | | | | ● | | calculé (120 attendues par heure) |
| `Energie_Wh__c` | Number(18,0) | | | | | ● | | dernier `energie_wh` de la période |
| `Puissance_Moy_W__c` | Number(8,1) | | | | | ● | | moyenne de `puissance_w` |
| `Temperature_Moy_C__c` | Number(4,1) | | | | | ● | | moyenne de `temperature_c` |
| `Temperature_Max_C__c` | Number(4,1) | | | | | ● | | maximum de `temperature_c` |
| `Tension_Moy_V__c` | Number(5,1) | | | | | ● | | moyenne de `tension_v` |
| `Dernier_Heartbeat__c` | DateTime | | | | | | ● | calculé |

● obligatoire ○ facultatif

L'événement `JOIGNABLE` ne contient que les champs communs (§3.1).

## 4. Exemples

### 4.1 `STATUT` — une borne tombe en panne

```json
{
  "attributes": { "type": "Borne_Event__e" },
  "Type__c": "STATUT",
  "Message_Id__c": "a3e4b5c6-7d8e-4f90-a1b2-c3d4e5f60718",
  "Code_Borne__c": "MRK-001",
  "Horodatage__c": "2026-10-15T12:40:00Z",
  "Statut_OCPP__c": "Faulted",
  "Code_Erreur__c": "HighTemperature",
  "Info__c": "Température module 82 °C"
}
```

### 4.2 `MESURE_AGREGEE` — bilan d'une heure

```json
{
  "attributes": { "type": "Borne_Event__e" },
  "Type__c": "MESURE_AGREGEE",
  "Message_Id__c": "e7f8a9b0-c1d2-4e3f-8a4b-5c6d7e8f9a0b",
  "Code_Borne__c": "MRK-001",
  "Horodatage__c": "2026-10-15T10:00:00Z",
  "Periode_Debut__c": "2026-10-15T09:00:00Z",
  "Periode_Fin__c": "2026-10-15T10:00:00Z",
  "Nb_Mesures__c": 120,
  "Energie_Wh__c": 1552600,
  "Puissance_Moy_W__c": 14250.5,
  "Temperature_Moy_C__c": 44.8,
  "Temperature_Max_C__c": 51.3,
  "Tension_Moy_V__c": 229.7
}
```

## 5. Envoi depuis la passerelle

### 5.1 Authentification

- Flux **OAuth 2.0 Client Credentials**, via une **Connected App** (ou une *External Client App*, son successeur, selon ce que propose l'org).
- L'application s'exécute en tant qu'un utilisateur dédié **« Passerelle VoltCare »**, avec la licence **Salesforce Integration** (accès API uniquement, pas de connexion à l'interface).
- Cet utilisateur a un seul Permission Set, `VoltCare_Passerelle`, qui donne uniquement le droit de **créer** des `Borne_Event__e`. Il n'a accès à aucun autre objet.
- `client_id`, `client_secret` et l'URL de l'org sont dans le `.env` de la passerelle, **jamais** sur GitHub.
- Sur une réponse **401** (jeton expiré), la passerelle redemande un jeton puis renvoie la requête.

### 5.2 Requête

Les événements sont envoyés **par lots** avec l'API *sObject Collections* : jusqu'à **200 événements en un seul appel API**.

```http
POST {instance_url}/services/data/v{XX}.0/composite/sobjects
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "allOrNone": false,
  "records": [
    { "attributes": { "type": "Borne_Event__e" }, "Type__c": "STATUT", "...": "..." },
    { "attributes": { "type": "Borne_Event__e" }, "Type__c": "SESSION_DEBUT", "...": "..." }
  ]
}
```

- `{XX}` : la même version d'API que `sourceApiVersion` dans `salesforce/sfdx-project.json`.
- `allOrNone: false` : un événement refusé n'empêche pas les autres de passer.

### 5.3 Rythme d'envoi

- La passerelle accumule les événements dans un tampon et l'envoie **toutes les 2 secondes** s'il n'est pas vide.
- Les `MESURE_AGREGEE` des 15 bornes partent ensemble au début de chaque heure (1 seul appel).
- Estimation : quelques centaines d'appels API par jour, à comparer aux **15 000 par 24 h** de la Developer Edition.

### 5.4 Erreurs côté passerelle

| Cas | Comportement |
|---|---|
| Un événement refusé (réponse `success: false`) | Journalisé avec le message d'erreur Salesforce ; **pas** de nouvel essai (l'erreur vient des données) |
| Erreur réseau ou réponse 5xx | Jusqu'à **3 nouveaux essais** (après 2 s, 4 s puis 8 s) |
| Échec après 3 essais | Lot écrit dans `gateway/echecs/AAAA-MM-JJ.jsonl` pour être renvoyé à la main |

## 6. Traitement côté Salesforce

### 6.1 Identifiants externes (External ID)

C'est grâce à eux que Salesforce retrouve un enregistrement à partir d'un code, sans connaître son Id Salesforce.

| Objet | Champ | Type | Propriétés | Exemple |
|---|---|---|---|---|
| `Station__c` | `Code_Station__c` | Text(20) | External ID, Unique, obligatoire | `ST-MRK-01` |
| `Borne__c` | `Code_Borne__c` | Text(20) | External ID, Unique, obligatoire | `MRK-001` |
| `Session_Recharge__c` | `Cle_Session__c` | Text(40) | External ID, Unique | `MRK-001-1287` (code borne + transaction) |
| `Mesure_Borne__c` | `Message_Id__c` | Text(36) | External ID, Unique | UUID de l'événement |

`transaction_id` n'est unique que **par borne** : c'est pour cela que la clé de session combine les deux.

### 6.2 Effet de chaque type d'événement

| `Type__c` | Effet dans Salesforce |
|---|---|
| `BOOT` | Crée ou met à jour la `Borne__c` (upsert sur `Code_Borne__c`) et la rattache à sa `Station__c` |
| `STATUT` | Met à jour la borne : `Statut__c` (converti, voir §6.3), `Statut_OCPP__c`, `Dernier_Code_Erreur__c`, `Date_Dernier_Statut__c`. Si `Faulted` → déclenche la création du ticket (BF-05, hors de ce contrat) |
| `SESSION_DEBUT` | Crée la `Session_Recharge__c` (upsert sur `Cle_Session__c`), statut « En cours », client retrouvé par son badge `Id_Tag__c` |
| `SESSION_FIN` | Complète la session : date de fin, énergie délivrée (`fin − début`), durée, statut « Terminée » |
| `MESURE_AGREGEE` | Crée un `Mesure_Borne__c` (upsert sur `Message_Id__c`) |
| `INJOIGNABLE` | La borne **garde son statut**. `Joignable__c` passe à `false` et `Date_Dernier_Contact__c` reçoit `Dernier_Heartbeat__c`. **Aucun ticket n'est créé** (la cause peut être le réseau, la passerelle ou l'arrêt du simulateur). Le tableau de bord affiche le nombre de bornes injoignables |
| `JOIGNABLE` | `Joignable__c` repasse à `true` |

**Tout événement reçu** d'une borne (quel que soit son type) remet aussi `Joignable__c` à `true` et met à jour `Date_Dernier_Contact__c`.

Champs correspondants sur `Borne__c` : `Joignable__c` (Checkbox, vrai par défaut) et `Date_Dernier_Contact__c` (DateTime).

### 6.3 Conversion du statut OCPP

| `Statut_OCPP__c` | `Borne__c.Statut__c` |
|---|---|
| `Available`, `Reserved` | Disponible |
| `Preparing`, `Charging`, `SuspendedEV`, `SuspendedEVSE`, `Finishing` | En charge |
| `Unavailable`, `Faulted` | Hors service |

### 6.4 Règles de robustesse

1. **Ordre** : si `Horodatage__c` est plus ancien que `Date_Dernier_Statut__c` de la borne, l'événement `STATUT` est ignoré (il est arrivé en retard).
2. **Doublons** : les upserts sur External ID rendent le traitement **idempotent** — recevoir deux fois le même événement ne crée pas de doublon.
3. **Borne inconnue** (événement autre que `BOOT` pour un code absent de Salesforce) : événement ignoré et ligne écrite dans `Integration_Log__c`.
4. **Toute erreur** de traitement est écrite dans `Integration_Log__c` (date, source `PASSERELLE`, type d'événement, code borne, message d'erreur, contenu de l'événement) ; une erreur sur un événement ne bloque pas les autres du lot.

### 6.5 Rétention des mesures

Un traitement planifié (Scheduled Apex) supprime chaque nuit les `Mesure_Borne__c` de plus de **72 heures** (environ 1 080 enregistrements conservés). L'historique complet reste côté Python, où il sert à entraîner le modèle IA.

## 7. Performance (exigence « temps réel < 10 s »)

| Étape | Délai estimé |
|---|---|
| Borne → Mosquitto → passerelle | < 0,1 s |
| Attente dans le tampon de la passerelle | ≤ 2 s |
| Appel API + livraison au trigger | 1 à 3 s |
| **Total** | **≈ 5 s maximum** |

## 8. Décisions d'équipe

- [x] Agrégation des mesures : **par heure** (360 enregistrements par jour)
- [x] Rétention des `Mesure_Borne__c` : **72 h** (environ 1 080 enregistrements, soit ≈ 2,2 Mo sur les **5 Mo** de Data Storage de l'org)
- [x] Événement `INJOIGNABLE` : simple **indicateur** `Joignable__c = false`, **sans changement de statut ni ticket**. Seul un statut `Faulted` (panne confirmée) crée un ticket (BF-05). Ajout du type `JOIGNABLE` pour signaler le retour du contact
- [x] Identification du client : champ **`Badge_RFID__c`** (Text(20), External ID, Unique) sur le **Contact**

**Vigilance stockage** : avec 5 Mo, les mesures occupent déjà près de la moitié de l'espace. Les sessions, tickets et contacts s'accumulent aussi. Le simulateur ne doit donc **pas tourner en continu** en dehors des séances de travail et de la démo, et l'équipe vérifie **Setup → Storage Usage** chaque vendredi. En cas de besoin, l'historique des mesures pourra être archivé dans un **Big Object** (1 000 000 d'enregistrements disponibles, non comptés dans les 5 Mo).

## Historique

| Version | Date | Modification |
|---|---|---|
| 1.0 | 15/10/2026 | Premier jet |
| 1.0 | 15/10/2026 | Décisions d'équipe : agrégation par heure, rétention 72 h, injoignable = indicateur sans ticket (+ type `JOIGNABLE`), badge RFID sur le Contact |
