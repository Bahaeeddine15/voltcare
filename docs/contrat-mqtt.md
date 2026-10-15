# Contrat d'interface — Messages MQTT des bornes

| | |
|---|---|
| **Version** | 1.0 |
| **Ticket** | VC-10 |
| **Producteur** | Simulateur de bornes (`simulator/`) — serveur central OCPP qui republie sur MQTT |
| **Consommateur** | Passerelle MQTT → Salesforce (`gateway/`) |
| **Broker** | Mosquitto |
| **Statut** | Validé par l'équipe |

---

## 1. Principes

- Les messages reprennent les messages standard **OCPP 1.6** (BootNotification, StatusNotification, StartTransaction, StopTransaction, MeterValues, Heartbeat).
- Format : **JSON**, encodage UTF-8.
- Noms de champs : **snake_case en français**, cohérents avec les champs Salesforce.
- Valeurs énumérées (statuts, codes d'erreur, raisons d'arrêt) : **valeurs OCPP 1.6 telles quelles**, en anglais.
- Dates : **UTC, ISO 8601** (`2026-10-15T12:40:00Z`).
- Simplification retenue : **1 connecteur par borne** (`connecteur_id` toujours égal à 1).

## 2. Identifiants

| Élément | Format | Exemple |
|---|---|---|
| Code borne | `{VILLE}-{NNN}` | `MRK-001` |
| Code station | `ST-{VILLE}-{NN}` | `ST-MRK-01` |
| Villes | `MRK` (Marrakech), `CAS` (Casablanca), `RBT` (Rabat) | |

Le **code borne** est la clé commune à toute la chaîne : il deviendra l'External ID `Code_Borne__c` dans Salesforce.

## 3. Topics

Tous les topics suivent la forme `voltcare/bornes/{code_borne}/{type}`.

| Topic | Message OCPP | Quand | QoS | Retain |
|---|---|---|---|---|
| `voltcare/bornes/{code}/boot` | BootNotification | Au démarrage de la borne | 1 | non |
| `voltcare/bornes/{code}/status` | StatusNotification | À chaque changement de statut | 1 | **oui** |
| `voltcare/bornes/{code}/session/start` | StartTransaction | Début d'une recharge | 1 | non |
| `voltcare/bornes/{code}/session/stop` | StopTransaction | Fin d'une recharge | 1 | non |
| `voltcare/bornes/{code}/meter` | MeterValues | Toutes les **30 s** | 0 | non |
| `voltcare/bornes/{code}/heartbeat` | Heartbeat | Toutes les **60 s** | 0 | non |

- **Retain sur `status`** : si la passerelle redémarre, elle reçoit immédiatement le dernier statut connu de chaque borne.
- **QoS 1** pour les événements qu'on ne doit pas perdre, **QoS 0** pour les mesures périodiques (une mesure perdue est remplacée 30 s plus tard).
- La passerelle s'abonne avec le joker : `voltcare/bornes/+/#`

## 4. Enveloppe commune

Tous les messages contiennent ces champs :

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `version` | string | oui | Version du contrat, `"1.0"` |
| `message_id` | string (UUID v4) | oui | Identifiant unique — permet à la passerelle d'ignorer les doublons (QoS 1 peut livrer deux fois) |
| `code_borne` | string | oui | Ex. `"MRK-001"` — doit correspondre au `{code}` du topic |
| `horodatage` | string (ISO 8601 UTC) | oui | Moment de l'événement côté borne |

## 5. Messages

### 5.1 `boot` — démarrage de la borne

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `code_station` | string | oui | Ex. `"ST-MRK-01"` |
| `fabricant` | string | oui | Ex. `"VoltSim"` |
| `modele` | string | oui | Ex. `"VS-22"` |
| `puissance_max_kw` | number | oui | Ex. `22` |
| `firmware` | string | non | Ex. `"1.4.2"` |

```json
{
  "version": "1.0",
  "message_id": "6f1c2a9e-3b4d-4e8a-9c1f-2d7b8e5a0c11",
  "code_borne": "MRK-001",
  "horodatage": "2026-10-15T08:00:00Z",
  "code_station": "ST-MRK-01",
  "fabricant": "VoltSim",
  "modele": "VS-22",
  "puissance_max_kw": 22,
  "firmware": "1.4.2"
}
```

### 5.2 `status` — changement de statut

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `connecteur_id` | integer | oui | Toujours `1` |
| `statut` | enum | oui | Statut OCPP (voir §6.1) |
| `code_erreur` | enum | oui | Code d'erreur OCPP (voir §6.2) — `"NoError"` si tout va bien |
| `info` | string | non | Détail libre, max 50 caractères |

```json
{
  "version": "1.0",
  "message_id": "a3e4b5c6-7d8e-4f90-a1b2-c3d4e5f60718",
  "code_borne": "MRK-001",
  "horodatage": "2026-10-15T12:40:00Z",
  "connecteur_id": 1,
  "statut": "Faulted",
  "code_erreur": "HighTemperature",
  "info": "Température module 82 °C"
}
```

### 5.3 `session/start` — début de recharge

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `connecteur_id` | integer | oui | Toujours `1` |
| `transaction_id` | integer | oui | Identifiant de session, unique **par borne** |
| `id_tag` | string | oui | Badge RFID du client (simulé), ex. `"CLI-0042"` |
| `compteur_debut_wh` | integer | oui | Index du compteur d'énergie au début (Wh) |

```json
{
  "version": "1.0",
  "message_id": "b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e",
  "code_borne": "MRK-001",
  "horodatage": "2026-10-15T09:15:00Z",
  "connecteur_id": 1,
  "transaction_id": 1287,
  "id_tag": "CLI-0042",
  "compteur_debut_wh": 1534200
}
```

### 5.4 `session/stop` — fin de recharge

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `transaction_id` | integer | oui | Même valeur qu'au `session/start` |
| `id_tag` | string | oui | Badge RFID du client |
| `compteur_fin_wh` | integer | oui | Index du compteur à la fin (Wh) |
| `raison` | enum | oui | Raison d'arrêt OCPP (voir §6.3) |

L'énergie délivrée se calcule : `compteur_fin_wh − compteur_debut_wh`.

```json
{
  "version": "1.0",
  "message_id": "c9d8e7f6-a5b4-4c3d-9e2f-1a0b9c8d7e6f",
  "code_borne": "MRK-001",
  "horodatage": "2026-10-15T10:02:00Z",
  "transaction_id": 1287,
  "id_tag": "CLI-0042",
  "compteur_fin_wh": 1552600,
  "raison": "EVDisconnected"
}
```

### 5.5 `meter` — mesures périodiques

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `connecteur_id` | integer | oui | Toujours `1` |
| `transaction_id` | integer \| null | oui | Session en cours, `null` si la borne est libre |
| `energie_wh` | integer | oui | Index du compteur (OCPP `Energy.Active.Import.Register`) |
| `puissance_w` | number | oui | Puissance instantanée, `0` si libre |
| `tension_v` | number | oui | Tension, ex. `230.4` |
| `courant_a` | number | oui | Courant, `0` si libre |
| `temperature_c` | number | oui | Température interne, 1 décimale |

```json
{
  "version": "1.0",
  "message_id": "d4e5f6a7-b8c9-4d0e-8f1a-2b3c4d5e6f70",
  "code_borne": "MRK-001",
  "horodatage": "2026-10-15T09:30:00Z",
  "connecteur_id": 1,
  "transaction_id": 1287,
  "energie_wh": 1539800,
  "puissance_w": 21800,
  "tension_v": 230.4,
  "courant_a": 31.6,
  "temperature_c": 47.2
}
```

### 5.6 `heartbeat` — signal de vie

Uniquement l'enveloppe commune (§4). Si la passerelle ne reçoit aucun heartbeat d'une borne pendant **3 minutes**, elle considère la borne comme **injoignable** (traité dans le contrat Platform Event).

## 6. Valeurs autorisées (OCPP 1.6)

### 6.1 `statut`

| Valeur OCPP | Signification | Statut Salesforce (BF-03) |
|---|---|---|
| `Available` | Libre | Disponible |
| `Reserved` | Réservée | Disponible |
| `Preparing` | Câble branché, en attente | En charge |
| `Charging` | Recharge en cours | En charge |
| `SuspendedEV` | Pause demandée par le véhicule | En charge |
| `SuspendedEVSE` | Pause demandée par la borne | En charge |
| `Finishing` | Fin de session, câble encore branché | En charge |
| `Unavailable` | Désactivée (maintenance) | Hors service |
| `Faulted` | En panne | Hors service |

La passerelle transmet la **valeur OCPP brute** ; la conversion vers les 3 statuts Salesforce est faite **dans Salesforce** (décision d'équipe).

### 6.2 `code_erreur`

Valeurs OCPP 1.6 utilisées par le simulateur :

| Valeur | Utilisée pour simuler |
|---|---|
| `NoError` | Fonctionnement normal |
| `HighTemperature` | Surchauffe (principal scénario de démo) |
| `GroundFailure` | Défaut de terre |
| `OverCurrentFailure` | Surintensité |
| `OverVoltage` / `UnderVoltage` | Problème de tension réseau |
| `ConnectorLockFailure` | Verrouillage du câble défaillant |
| `PowerMeterFailure` | Compteur d'énergie défaillant |
| `EVCommunicationError` | Dialogue impossible avec le véhicule |
| `InternalError` | Erreur interne générique |
| `OtherError` | Autre |

### 6.3 `raison` (arrêt de session)

`Local` (arrêt par le client), `EVDisconnected`, `Remote`, `EmergencyStop`, `PowerLoss`, `Other`.

## 7. Règles de traitement côté passerelle

1. **Message invalide** (JSON mal formé, champ obligatoire manquant, valeur hors liste) : ignoré, journalisé, et republié tel quel sur `voltcare/erreurs` pour analyse.
2. **Doublon** (`message_id` déjà vu dans les 10 dernières minutes) : ignoré.
3. **Incohérence topic / contenu** (`{code}` du topic ≠ `code_borne`) : traité comme message invalide.
4. **Mesures** : la passerelle ne transmet pas chaque mesure à Salesforce ; elle les **agrège** (détail dans le contrat Platform Event) pour respecter les limites de la Developer Edition.

## 8. Sécurité

- Accès anonyme au broker **désactivé**.
- Deux comptes Mosquitto : `simulateur` (publication sur `voltcare/bornes/#`) et `passerelle` (lecture sur `voltcare/bornes/#`, publication sur `voltcare/erreurs`).
- Identifiants dans un fichier `.env`, **jamais** dans le code ni sur GitHub.

## 9. Décisions d'équipe

- [x] Nombre de bornes simulées : **15**
- [x] Fréquence des mesures : **30 s**
- [x] Répartition : **5 Marrakech, 5 Casablanca, 5 Rabat**, soit les codes `MRK-001` à `MRK-005`, `CAS-001` à `CAS-005`, `RBT-001` à `RBT-005`
- [x] Conversion OCPP → statut Salesforce : **dans Salesforce**
- [x] Pas de topic de commande Salesforce → borne en version 1.0. La remise en service après réparation se fait **manuellement dans le simulateur** (commande `reparer {code_borne}`, qui publie un `status` à `Available` / `NoError`). Un topic `voltcare/bornes/{code}/commande` (OCPP `ChangeAvailability`) reste une amélioration possible en semaine 9.

## Historique

| Version | Date | Modification |
|---|---|---|
| 1.0 | 15/10/2026 | Premier jet |
| 1.0 | 15/10/2026 | Décisions d'équipe : 15 bornes, 30 s, 5/5/5, conversion dans Salesforce, pas de commande retour (réparation manuelle dans le simulateur) |
