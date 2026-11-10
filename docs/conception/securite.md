# Sécurité et droits d'accès — VoltCare

| | |
|---|---|
| **Version** | 1.0 — validée par l'équipe |
| **Sprint** | S2 — Conception |
| **Exigence** | Besoins non fonctionnels — Sécurité : profils et Permission Sets par acteur, Named Credentials, aucun secret dans le code, OAuth 2.0 pour la passerelle |
| **Documents liés** | `dictionnaire-donnees.md` v1.1, contrats v1.0, diagrammes de séquence |

---

## 1. Principes

1. **Moindre privilège** : chaque utilisateur reçoit uniquement les droits dont son rôle a besoin.
2. **Profils minimaux, droits dans les Permission Sets** : les profils ne donnent presque rien ; les droits métier sont portés par un Permission Set par acteur. Les Permission Sets sont plus simples à versionner dans Git que les profils, qui créent des conflits.
3. **Deux niveaux de contrôle** :
   - les **droits sur l'objet et les champs** (Permission Sets) disent *ce qu'un utilisateur peut faire* ;
   - le **partage** (Org-Wide Defaults, hiérarchie des rôles, Sharing Sets) dit *sur quels enregistrements*.
4. **Aucun secret dans le code ni sur GitHub** : Named Credentials côté Salesforce, fichiers `.env` côté Python, paramètres d'application côté Azure.

---

## 2. Utilisateurs de l'org de démo

| Utilisateur | Licence | Profil | Permission Sets | Rôle |
|---|---|---|---|---|
| Administrateur (intégrateur) | Salesforce | System Administrator | `VoltCare_Integrations` | — |
| Responsable réseau (démo) | Salesforce | `VoltCare Interne` (copie de *Minimum Access - Salesforce*) | `VoltCare_Responsable` | Responsable réseau |
| Technicien (démo) | Salesforce | `VoltCare Interne` | `VoltCare_Technicien` | Technicien |
| Passerelle VoltCare | **Salesforce Integration** | *Minimum Access - API Only Integrations* | `VoltCare_Passerelle` | — |
| 3 clients de démo | **Customer Community Login** | `VoltCare Client` (copie de *Customer Community Login User*) | `VoltCare_Client` | — |
| *Automated Process* (système) | — | — | — | Exécute le trigger du Platform Event |

**Limite de licences** : l'org n'a que 2 licences Salesforce libres, donc **un seul technicien de démo**. Pour la démonstration, il est indiqué comme `Technicien__c` des 6 stations.

### Hiérarchie des rôles

```
Responsable réseau
 └── Technicien
```
La hiérarchie permet au responsable de voir et de réaffecter les tickets de tous les techniciens, sans droit « Tout voir » sur l'objet.

---

## 3. Partage par défaut (Org-Wide Defaults)

| Objet | Interne | Externe (portail) | Justification |
|---|---|---|---|
| `Station__c` | Public lecture/écriture | Public lecture seule | Tous les internes lisent les stations ; seuls ceux qui en ont le droit sur l'objet (responsable, admin) les modifient. Les clients en ont besoin pour la carte |
| `Borne__c` | Contrôlé par le parent | Contrôlé par le parent | Master-Detail de `Station__c` |
| `Session_Recharge__c` | Contrôlé par le parent | Contrôlé par le parent | Master-Detail de `Borne__c` — voir §5 pour l'accès des clients |
| `Mesure_Borne__c` | Contrôlé par le parent | Contrôlé par le parent | Master-Detail de `Borne__c` ; aucun droit sur l'objet pour les clients |
| `Case` | **Privé** | **Privé** | Un technicien voit ses tickets ; le responsable voit tout grâce à la hiérarchie ; un client voit ses propres signalements grâce à un **Sharing Set** |
| `Contact` | Privé (contrôlé par le compte) | Privé | Un client ne voit que son propre contact |
| `Integration_Log__c` | Privé | Privé | Journal technique réservé à l'administrateur et au responsable |

**Sharing Set** (Experience Cloud) : un utilisateur client a accès aux `Case` dont `ContactId` = son contact.

---

## 4. Matrice des droits par Permission Set

L = lecture · C = création · M = modification · S = suppression · — = aucun accès

| Objet | Admin | `VoltCare_Responsable` | `VoltCare_Technicien` | `VoltCare_Passerelle` | `VoltCare_Client` |
|---|:-:|:-:|:-:|:-:|:-:|
| `Station__c` | L C M S | L M | L | — | L |
| `Borne__c` | L C M S | L M | L | — | L *(champs limités, §6)* |
| `Session_Recharge__c` | L C M S | L | L | — | — *(via contrôleur, §5)* |
| `Mesure_Borne__c` | L C M S | L | L | — | — |
| `Case` | L C M S | L C M | L M | — | L C |
| `Contact` | L C M S | L | L | — | L |
| `Integration_Log__c` | L S | L | — | — | — |
| `Borne_Event__e` (Platform Event) | L C | — | — | **C** | — |

**Droits système** : le Permission Set `VoltCare_Passerelle` donne aussi *API Enabled*. Aucun utilisateur humain, hormis l'administrateur, n'a *Modify All Data* ni *View All Data*.

**Pourquoi la passerelle n'a aucun droit sur les objets métier** : elle ne fait que publier des `Borne_Event__e`. C'est le trigger, exécuté par Salesforce, qui écrit dans `Borne__c`, `Session_Recharge__c` et `Mesure_Borne__c`. Si ses identifiants fuitaient, ils ne permettraient ni de lire ni de modifier les données.

---

## 5. Accès des clients à leur historique de recharges

Les sessions sont en Master-Detail de la borne. Si un client avait le droit de lire l'objet `Session_Recharge__c`, il verrait **les sessions de tous les clients** sur les bornes qu'il peut lire.

**Solution retenue** : les clients **n'ont aucun droit** sur `Session_Recharge__c`. La page « Mes recharges » appelle un contrôleur Apex `MesRechargesController` qui :
- s'exécute sans partage (`without sharing`) ;
- filtre **toujours** sur `Client__c = ` le contact de l'utilisateur connecté (`UserInfo` → `User.ContactId`) ;
- ne renvoie que les champs affichés sur la page.

Ce filtre est la seule barrière : il doit être couvert par un test Apex qui vérifie qu'un client ne reçoit jamais la session d'un autre.

*Alternative écartée* : passer `Session_Recharge__c` en Lookup avec un Sharing Set. C'est plus « natif », mais on perdrait le roll-up de l'énergie délivrée sur la borne et la suppression en cascade.

---

## 6. Sécurité au niveau des champs (FLS)

| Champ | Responsable | Technicien | Client |
|---|---|---|---|
| `Borne__c` : code, station, statut, puissance max | L | L | L |
| `Borne__c` : statut OCPP, dernier code d'erreur, joignable | L | L | — |
| `Borne__c` : score, niveau, facteurs de risque | L | L | — |
| `Borne__c` : fabricant, modèle, firmware | L | L | — |
| `Borne__c` : date de mise en service | L M | L | — |
| `Station__c.Technicien__c` | L M | L | — |
| `Case` : champs ajoutés (borne, code d'erreur, score) | L | L | Borne seulement |
| `Case.Type_Probleme_Client__c`, `Notifier_Client__c` | L | L | L C |
| `Contact.Badge_RFID__c` | L | — | L |
| `User.Telegram_Chat_Id__c` | — | — | — |

Les champs remplis par le système (statut, score, mesures) sont **en lecture seule pour tous les humains**, administrateur compris dans les mises en page.

---

## 7. Sécurité des intégrations

| Intégration | Méthode | Où est le secret | Qui y a accès |
|---|---|---|---|
| Passerelle → Salesforce | OAuth 2.0 *Client Credentials*, Connected App (ou External Client App) « VoltCare Passerelle », exécutée en tant qu'utilisateur Passerelle VoltCare, portée `api` uniquement | `client_id` / `client_secret` dans `gateway/.env` | L'équipe, en local ; jamais sur GitHub |
| Salesforce → API IA | Named Credential `VoltCare_IA` + External Credential (en-tête `X-API-Key`) | External Credential (Salesforce) et paramètre `API_KEY` d'Azure App Service | Utilisateurs ayant `VoltCare_Integrations` |
| Salesforce → Telegram | Named Credential `Telegram` (le jeton du bot fait partie de l'URL de l'API Telegram) | Configuration du Named Credential | Utilisateurs ayant `VoltCare_Integrations` |
| Simulateur ↔ Mosquitto | Identifiants Mosquitto, accès anonyme désactivé | `simulator/.env` et `gateway/.env` | L'équipe, en local |

### Qui exécute les appels sortants

Avec les Named Credentials récents, **l'utilisateur qui exécute l'appel** doit avoir accès à l'External Credential par un Permission Set (`VoltCare_Integrations`).

- **Prédiction IA** : le Scheduled Apex s'exécute en tant que l'administrateur qui l'a planifié → il a `VoltCare_Integrations`. ✅
- **Notifications Telegram** : le Queueable s'exécuterait en tant que l'utilisateur qui a créé le ticket, c'est-à-dire le processus système, un technicien, ou **un client du portail**. Donner l'accès aux secrets Telegram à un client n'est pas acceptable.
  - **Décision** : le trigger du `Case` publie un événement interne `Notification_Ticket__e`. Son abonné est configuré (`PlatformEventSubscriberConfig`) pour s'exécuter en tant que l'administrateur, et c'est lui qui lance le Queueable Telegram (séquences 2 et 4, dictionnaire v1.2).

---

## 8. Portail client

- **Connexion obligatoire** pour toutes les pages, y compris la carte.
- **Inscription libre** activée (*Configurable Self-Reg Page*) : le client saisit son email, reçoit un code de vérification et choisit son mot de passe. Il devient automatiquement un Contact du compte « Clients VoltCare », avec le profil `VoltCare Client`.
  - Limite : **10 comptes clients** au maximum (5 *Customer Community Login* + 5 *Customer Community*).
  - Prérequis : **Setup → Deliverability → All email**, sinon le code de vérification n'est pas envoyé.
  - Seule la page d'inscription est accessible sans connexion (utilisateur *guest*).
- **Badge RFID** : un nouveau client saisit son numéro de badge sur une page « Mon compte » du portail, qui renseigne `Contact.Badge_RFID__c`. Tant qu'il ne l'a pas fait, ses recharges ne lui sont pas rattachées.
- Le contrôleur de signalement vérifie que la borne choisie existe et renseigne lui-même `ContactId` à partir de l'utilisateur connecté : un client ne peut pas créer un ticket au nom d'un autre.

---

## 9. Traçabilité

- **Historique des champs** activé sur `Borne__c.Statut__c`, `Borne__c.Niveau_Risque__c`, `Case.Status` et `Case.OwnerId`.
- Toutes les erreurs d'intégration sont écrites dans `Integration_Log__c` (conservé 7 jours).

---

## 10. Décisions d'équipe

- [x] Carte du portail : **connexion obligatoire**, avec inscription libre (§8)
- [x] Historique des recharges servi par un **contrôleur Apex filtré** (§5)
- [x] Notifications Telegram exécutées par l'administrateur via l'événement **`Notification_Ticket__e`** (§7)

## Historique

| Version | Date | Modification |
|---|---|---|
| 1.0 | 10/11/2026 | Premier jet, décisions validées : connexion obligatoire avec inscription libre, contrôleur filtré, `Notification_Ticket__e` |
