# Dictionnaire de données — VoltCare

| | |
|---|---|
| **Version** | 1.1 |
| **Sprint** | S2 — Conception |
| **Diagramme** | `modele-donnees.puml` / `modele-donnees.png` |
| **Contrats liés** | `contrat-mqtt.md`, `contrat-platform-event.md`, `contrat-api-ia.md` (v1.0) |

Colonne **Rempli par** : *Trigger* = trigger Apex sur `Borne_Event__e` · *IA* = Queueable Apex après l'appel à l'API IA · *Flow* = automatisation de maintenance · *Saisie* = saisie manuelle ou import initial · *Système* = calculé par Salesforce.

---

## 1. Choix de conception

| Choix | Raison |
|---|---|
| **Station → Borne → Session / Mesure en Master-Detail** | Une borne n'existe pas sans station, une session ou une mesure n'existe pas sans borne. Le Master-Detail donne la **suppression en cascade** (utile pour la purge des mesures) et les **roll-ups** (nombre de bornes, énergie délivrée) sans code |
| **Borne → Case en Lookup** | Un ticket doit survivre même si la borne est supprimée ou remplacée, et le Case est un objet standard avec ses propres règles de partage |
| **Tickets = objet standard Case** | Exigé par le cahier des charges (BF-01). Il apporte les files d'attente, l'affectation, l'historique et l'application mobile du technicien |
| **Clients = Contact rattachés au compte « Clients VoltCare »** | Experience Cloud exige qu'un utilisateur du portail soit un Contact rattaché à un Account. Un seul compte suffit pour tous les particuliers |
| **External IDs sur chaque objet alimenté par la passerelle** | Les upserts rendent le traitement **idempotent** : recevoir deux fois le même événement ne crée pas de doublon |
| **`Energie_kWh__c` et `Duree_Minutes__c` en Number, pas en formule** | Un roll-up `SUM` sur la borne doit pouvoir les additionner. Ils sont calculés par le trigger à la fin de la session |
| **Valeurs OCPP en Text, statut Salesforce en Picklist** | Les valeurs OCPP sont stockées brutes pour la traçabilité ; la Picklist `Statut__c` (3 valeurs) sert aux rapports, filtres et règles |
| **Technicien du secteur sur la Station** | L'affectation d'un ticket (BF-05) lit `Borne__c.Station__c.Technicien__c` : pas de table de correspondance à maintenir |
| **`Telegram_Chat_Id__c` sur User** | La notification Telegram (BF-09) doit savoir à quel chat écrire pour chaque technicien et responsable |

---

## 2. `Station__c` — Station de recharge

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `Name` | Nom de la station | Text(80) | ✔ | Saisie | Ex. « Station Guéliz » |
| `Code_Station__c` | Code station | Text(20) · **External ID, unique** | ✔ | Saisie / Trigger (BOOT) | Ex. `ST-MRK-01` |
| `Ville__c` | Ville | Picklist : Marrakech, Casablanca, Rabat | ✔ | Saisie | |
| `Adresse__c` | Adresse | Text(255) | | Saisie | Affichée sur le portail |
| `Localisation__c` | Localisation | Geolocation (6 décimales) | ✔ | Saisie | Position des marqueurs sur la carte Leaflet (BF-08) |
| `Technicien__c` | Technicien du secteur | Lookup(User) | ✔ | Saisie | Destinataire des tickets de cette station (BF-05) |
| `Nb_Bornes__c` | Nombre de bornes | Roll-up COUNT(Borne__c) | | Système | |
| `Nb_Bornes_Hors_Service__c` | Bornes hors service | Roll-up COUNT(Borne__c) où `Statut__c = Hors service` | | Système | Tableau de bord (BF-07) |

**Données initiales** : 6 stations (2 par ville), par exemple `ST-MRK-01` Guéliz et `ST-MRK-02` Hivernage.

---

## 3. `Borne__c` — Borne de recharge

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `Name` | Nom | Text(80) | ✔ | Trigger (BOOT) | Égal au code borne |
| `Code_Borne__c` | Code borne | Text(20) · **External ID, unique** | ✔ | Trigger (BOOT) | Ex. `MRK-001` — clé commune à toute la chaîne |
| `Station__c` | Station | **Master-Detail**(Station__c) | ✔ | Trigger (BOOT) | Retrouvée par `Code_Station__c` |
| `Statut__c` | Statut | Picklist restreinte : Disponible, En charge, Hors service | ✔ | Trigger (STATUT) | Converti depuis le statut OCPP (contrat Platform Event §6.3) |
| `Statut_OCPP__c` | Statut OCPP | Text(20) | | Trigger (STATUT) | Valeur brute, ex. `Faulted` |
| `Dernier_Code_Erreur__c` | Dernier code d'erreur | Text(40) | | Trigger (STATUT) | Ex. `HighTemperature`, `NoError` |
| `Date_Dernier_Statut__c` | Date du dernier statut | DateTime | | Trigger (STATUT) | Sert à ignorer les événements arrivés en retard |
| `Joignable__c` | Joignable | Checkbox, vrai par défaut | | Trigger | Faux après `INJOIGNABLE`, vrai après tout autre événement |
| `Date_Dernier_Contact__c` | Dernier contact | DateTime | | Trigger | |
| `Fabricant__c` | Fabricant | Text(40) | | Trigger (BOOT) | |
| `Modele__c` | Modèle | Text(40) | | Trigger (BOOT) | |
| `Firmware__c` | Firmware | Text(20) | | Trigger (BOOT) | |
| `Puissance_Max_kW__c` | Puissance max (kW) | Number(5,1) | | Trigger (BOOT) | |
| `Date_Mise_En_Service__c` | Mise en service | Date | ✔ | Saisie | Sert à calculer `age_mois` pour l'IA |
| `Score_Risque__c` | Score de risque | Number(3,0) | | IA | 0 à 100 |
| `Niveau_Risque__c` | Niveau de risque | Picklist : Faible, Moyen, Élevé, Indéterminé | | IA | |
| `Facteurs_Risque__c` | Facteurs du risque | Text(255) | | IA | Séparés par des virgules |
| `Date_Score__c` | Date du score | DateTime | | IA | |
| `Version_Modele__c` | Version du modèle | Text(40) | | IA | Ex. `rf-2026-10-28` |
| `Nb_Sessions__c` | Nombre de sessions | Roll-up COUNT(Session_Recharge__c) | | Système | |
| `Energie_Delivree_kWh__c` | Énergie délivrée (kWh) | Roll-up SUM(Session_Recharge__c.Energie_kWh__c) | | Système | |

---

## 4. `Session_Recharge__c` — Session de recharge

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `Name` | N° | Auto Number `SES-{000000}` | ✔ | Système | |
| `Cle_Session__c` | Clé de session | Text(40) · **External ID, unique** | ✔ | Trigger | `{code borne}-{transaction}`, ex. `MRK-001-1287` |
| `Borne__c` | Borne | **Master-Detail**(Borne__c) | ✔ | Trigger | |
| `Client__c` | Client | Lookup(Contact) | | Trigger | Retrouvé par `Contact.Badge_RFID__c = Id_Tag__c` ; vide si badge inconnu |
| `Transaction_Id__c` | N° de transaction OCPP | Number(18,0) | ✔ | Trigger | Unique par borne seulement |
| `Id_Tag__c` | Badge | Text(20) | ✔ | Trigger | Valeur brute, conservée même si le client est inconnu |
| `Date_Debut__c` | Début | DateTime | ✔ | Trigger (SESSION_DEBUT) | |
| `Date_Fin__c` | Fin | DateTime | | Trigger (SESSION_FIN) | |
| `Compteur_Debut_Wh__c` | Compteur début (Wh) | Number(18,0) | ✔ | Trigger (SESSION_DEBUT) | |
| `Compteur_Fin_Wh__c` | Compteur fin (Wh) | Number(18,0) | | Trigger (SESSION_FIN) | |
| `Energie_kWh__c` | Énergie (kWh) | Number(8,2) | | Trigger (SESSION_FIN) | `(fin − début) / 1000` |
| `Duree_Minutes__c` | Durée (min) | Number(6,0) | | Trigger (SESSION_FIN) | |
| `Statut__c` | Statut | Picklist : En cours, Terminée, Interrompue | ✔ | Trigger | **Interrompue** si la raison d'arrêt est `EmergencyStop`, `PowerLoss` ou `Other` |
| `Raison_Arret__c` | Raison d'arrêt | Text(20) | | Trigger (SESSION_FIN) | Valeur OCPP brute |

---

## 5. `Mesure_Borne__c` — Mesure agrégée (1 par borne et par heure)

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `Name` | N° | Auto Number `MES-{000000}` | ✔ | Système | |
| `Message_Id__c` | Identifiant du message | Text(36) · **External ID, unique** | ✔ | Trigger | UUID de l'événement `MESURE_AGREGEE` |
| `Borne__c` | Borne | **Master-Detail**(Borne__c) | ✔ | Trigger | |
| `Periode_Debut__c` | Début de période | DateTime | ✔ | Trigger | |
| `Periode_Fin__c` | Fin de période | DateTime | ✔ | Trigger | |
| `Nb_Mesures__c` | Nombre de mesures | Number(4,0) | ✔ | Trigger | 120 attendues par heure |
| `Energie_Wh__c` | Index d'énergie (Wh) | Number(18,0) | ✔ | Trigger | Dernier index de la période |
| `Puissance_Moy_W__c` | Puissance moyenne (W) | Number(8,1) | ✔ | Trigger | |
| `Temperature_Moy_C__c` | Température moyenne (°C) | Number(4,1) | ✔ | Trigger | |
| `Temperature_Max_C__c` | Température max (°C) | Number(4,1) | ✔ | Trigger | |
| `Tension_Moy_V__c` | Tension moyenne (V) | Number(5,1) | ✔ | Trigger | |

**Rétention** : supprimées après **72 heures** par une purge planifiée chaque nuit.

---

## 6. `Case` — Ticket de maintenance (objet standard)

**Champs standard utilisés**

| Champ | Valeurs / usage |
|---|---|
| `Type` | **Panne** (borne `Faulted`) · **Maintenance préventive** (score > 70) · **Signalement** (portail client) |
| `Origin` | **Borne** · **Prédiction IA** · **Portail client** |
| `Status` | Nouveau → En cours → Clôturé |
| `Priority` | Haute (panne), Moyenne (préventive, signalement) |
| `OwnerId` | Le technicien du secteur (`Station__c.Technicien__c`) |
| `ContactId` | Le client, pour un signalement |
| `Subject` / `Description` | Générés automatiquement ou saisis par le client |

**Champs ajoutés**

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `Borne__c` | Borne | Lookup(Borne__c) | ✔ | Flow / portail | |
| `Code_Erreur__c` | Code d'erreur | Text(40) | | Flow | Code OCPP au moment de la panne |
| `Score_Risque_Creation__c` | Score à la création | Number(3,0) | | Flow | Pour un ticket préventif |
| `Type_Probleme_Client__c` | Type de problème | Picklist : La recharge ne démarre pas, La recharge s'est arrêtée, Câble ou prise endommagé, Écran ou badge, Autre | | Portail | |
| `Duree_Reparation_Heures__c` | Délai de réparation (h) | Formule Number : `(ClosedDate − CreatedDate) × 24` | | Système | Indicateur du tableau de bord (BF-07) |
| `Notifier_Client__c` | Prévenir le client par email | Checkbox, faux par défaut | | Portail | Case « Me prévenir par email de l'avancement » du formulaire de signalement |

**Règles**
- **Affectation** : un Flow avant enregistrement, commun aux 3 origines, renseigne `OwnerId = Borne__r.Station__r.Technicien__c`.
- **Clôture** : à la clôture d'un ticket de type Panne, la borne repasse **Disponible** et `Date_Dernier_Statut__c` reçoit l'heure de clôture (BF-06).

---

## 7. `Contact` — Client (objet standard)

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `AccountId` | Compte | Lookup(Account) | ✔ | Saisie | Toujours le compte « Clients VoltCare » |
| `Badge_RFID__c` | Badge RFID | Text(20) · **External ID, unique** | | Saisie | Ex. `CLI-0042` — relie les sessions au client |

---

## 8. `User` — Technicien et responsable (objet standard)

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `Telegram_Chat_Id__c` | Chat Telegram | Text(30) | | Saisie | Identifiant du chat pour les alertes (BF-09) |

---

## 9. `Integration_Log__c` — Journal d'intégration

| Champ API | Libellé | Type | Oblig. | Rempli par | Description |
|---|---|---|:-:|---|---|
| `Name` | N° | Auto Number `LOG-{000000}` | ✔ | Système | |
| `Source__c` | Source | Picklist : PASSERELLE, API_IA, TELEGRAM | ✔ | Apex | |
| `Niveau__c` | Niveau | Picklist : INFO, ERREUR | ✔ | Apex | |
| `Type_Evenement__c` | Type d'événement | Text(30) | | Apex | Ex. `STATUT`, `POST /v1/predict` |
| `Code_Borne__c` | Code borne | Text(20) | | Apex | |
| `Code_HTTP__c` | Code HTTP | Number(3,0) | | Apex | Pour les appels sortants |
| `Message__c` | Message | Long Text Area(5000) | ✔ | Apex | Message d'erreur |
| `Contenu__c` | Contenu | Long Text Area(32768) | | Apex | Événement ou requête concerné |

**Rétention** : supprimés après **7 jours** par la même purge planifiée que les mesures.

---

## 10. `Borne_Event__e` — Platform Event

Non stocké : il est consommé par le trigger. Ses champs sont définis dans `contrat-platform-event.md` v1.0, §3.

---

## 11. Estimation du stockage (Developer Edition : 5 Mo)

Chaque enregistrement compte pour environ 2 Ko.

| Objet | Volume | Enregistrements | Stockage |
|---|---|---|---|
| `Station__c` | 6 | 6 | ≈ 12 Ko |
| `Borne__c` | 15 | 15 | ≈ 30 Ko |
| `Mesure_Borne__c` | 360 / jour, conservées 72 h | ≈ 1 080 | ≈ 2,2 Mo |
| `Session_Recharge__c` | ≈ 60 / jour de simulation | ≈ 600 sur 10 jours de simulation | ≈ 1,2 Mo |
| `Case` | Quelques dizaines | ≈ 50 | ≈ 100 Ko |
| `Contact` (clients) | 20 | 20 | ≈ 40 Ko |
| `Integration_Log__c` | Conservés 7 jours | ≈ 100 | ≈ 200 Ko |
| **Total** | | | **≈ 3,8 Mo sur 5 Mo** |

⚠️ La marge est faible : le simulateur ne doit tourner que pendant les séances de travail et la démo, et la consommation est vérifiée chaque vendredi dans **Setup → Storage Usage**. Si les sessions s'accumulent trop, on ajoutera une purge des sessions de plus de 30 jours.

## Historique

| Version | Date | Modification |
|---|---|---|
| 1.0 | 10/11/2026 | Premier jet, décisions validées en équipe |
| 1.1 | 10/11/2026 | Ajout de `Case.Notifier_Client__c` et des règles d'affectation et de clôture (issus des diagrammes de séquence) |
