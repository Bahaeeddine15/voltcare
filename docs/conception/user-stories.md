# User stories — VoltCare

| | |
|---|---|
| **Version** | 1.0 |
| **Sprint** | S2 — Conception |
| **Nombre** | 28 stories · 111 points |

Format : *En tant que … je veux … afin de …*, avec des critères d'acceptation vérifiables. Les points suivent la suite 1, 2, 3, 5, 8 (effort relatif). Le sprint indiqué suit le planning du cahier des charges.

## Définition de « terminé » (pour toutes les stories)

- Le code est relu et fusionné par Pull Request
- Les tests Apex passent et la couverture globale reste ≥ 75 %
- Les métadonnées sont déployées sans erreur dans l'org de démo
- Les critères d'acceptation ont été vérifiés pendant la démo du vendredi
- La documentation concernée (contrats, dictionnaire, diagrammes) est à jour

## Vue d'ensemble

| ID | Story | Epic | Exigence | Priorité | Points | Sprint |
|---|---|---|---|---|:-:|:-:|
| US-01 | Créer les objets et champs du modèle de données | E2 | BF-01 | Indispensable | 5 | S3 |
| US-02 | Configurer profils, Permission Sets, rôles et partage | E2 | BF-01 | Indispensable | 5 | S3 |
| US-03 | Construire la fiche Borne et la fiche Station | E2 | BF-01 | Indispensable | 3 | S3 |
| US-04 | Charger les données de démonstration | E2 | BF-01 | Indispensable | 2 | S3 |
| US-05 | Simuler 15 bornes OCPP | E3 | BF-02 | Indispensable | 8 | S4 |
| US-06 | Injecter des pannes et réparer une borne | E3 | BF-02 | Indispensable | 3 | S4 |
| US-07 | Enregistrer l'historique brut en CSV | E3 | BF-02 | Indispensable | 2 | S4 |
| US-08 | Mettre à jour le statut des bornes en temps réel | E4 | BF-03 | Indispensable | 8 | S5 |
| US-09 | Enregistrer les sessions de recharge | E4 | BF-03 | Indispensable | 5 | S5 |
| US-10 | Agréger les mesures et purger l'historique | E4 | BF-03 | Indispensable | 3 | S5 |
| US-11 | Détecter une borne injoignable | E4 | BF-03 | Indispensable | 2 | S5 |
| US-12 | Consulter le journal d'intégration | E4 | BF-03 | Indispensable | 2 | S5 |
| US-13 | Entraîner le modèle de prédiction des pannes | E5 | BF-04 | Indispensable | 8 | S6 |
| US-14 | Exposer l'API de prédiction | E5 | BF-04 | Indispensable | 5 | S6 |
| US-15 | Mettre à jour le score de risque toutes les heures | E5 | BF-04 | Indispensable | 5 | S6 |
| US-16 | Créer et affecter automatiquement un ticket de panne | E6 | BF-05 | Indispensable | 5 | S7 |
| US-17 | Créer un ticket de maintenance préventive | E6 | BF-05 | Indispensable | 2 | S7 |
| US-18 | Suivre et clôturer une intervention | E6 | BF-06 | Indispensable | 3 | S7 |
| US-19 | Construire le tableau de bord du responsable | E6 | BF-07 | Indispensable | 5 | S7 |
| US-20 | Réaffecter un ticket | E6 | BF-05 | Indispensable | 1 | S7 |
| US-21 | Créer un compte client et enregistrer son badge | E7 | BF-08 | Souhaité | 3 | S8 |
| US-22 | Trouver une borne disponible sur la carte | E7 | BF-08 | Souhaité | 5 | S8 |
| US-23 | Consulter l'historique de ses recharges | E7 | BF-08 | Souhaité | 3 | S8 |
| US-24 | Signaler un problème sur une borne | E7 | BF-08 | Souhaité | 5 | S8 |
| US-25 | Qualifier un signalement non confirmé | E7 | BF-08 | Souhaité | 2 | S8 |
| US-26 | Recevoir une alerte Telegram | E7 | BF-09 | Souhaité | 3 | S8 |
| US-27 | Payer une session en mode test | E8 | BF-10 | Bonus | 5 | S9 |
| US-28 | Obtenir un résumé IA de la borne | E8 | BF-11 | Bonus | 3 | S9 |

### Charge par sprint

| Sprint | Points |
|---|:-:|
| S3 | 15 |
| S4 | 13 |
| S5 | 20 |
| S6 | 18 |
| S7 | 16 |
| S8 | 21 |
| S9 | 8 |

## E2 - Modèle de données Salesforce

### US-01 — Créer les objets et champs du modèle de données

**BF-01 · Indispensable · 5 points · S3**

> En tant que **administrateur**, je veux que tous les objets, champs, relations et External IDs du modèle de données existent dans Salesforce, afin de que les autres briques puissent s'y brancher.

**Critères d'acceptation**

- [ ] Les objets Station__c, Borne__c, Session_Recharge__c, Mesure_Borne__c, Integration_Log__c et les Platform Events Borne_Event__e et Notification_Ticket__e existent avec les champs et types du dictionnaire v1.3
- [ ] Les champs ajoutés sur Case, Contact et User existent, avec les valeurs de liste de Type, Origin, Status et Resolution__c
- [ ] Les relations Master-Detail et Lookup, les roll-ups et les External IDs uniques sont conformes au diagramme
- [ ] Toute la métadonnée est dans salesforce/ sur GitHub et se déploie sans erreur avec sf project deploy start

*Références : dictionnaire-donnees.md v1.3, modele-donnees.puml*

### US-02 — Configurer profils, Permission Sets, rôles et partage

**BF-01 · Indispensable · 5 points · S3**

> En tant que **administrateur**, je veux que chaque acteur ait exactement les droits prévus, afin de de respecter le principe du moindre privilège.

**Critères d'acceptation**

- [ ] Les Permission Sets VoltCare_Responsable, VoltCare_Technicien, VoltCare_Passerelle, VoltCare_Client et VoltCare_Integrations correspondent à la matrice de securite.md §4 et §6
- [ ] Les Org-Wide Defaults, la hiérarchie Responsable > Technicien, le Sharing Set des Cases et la file « Qualification des signalements » sont configurés
- [ ] Étant donné un technicien connecté, quand il ouvre la liste des tickets, alors il ne voit que les siens
- [ ] Étant donné l'utilisateur Passerelle, quand il tente de lire Borne__c par l'API, alors l'accès est refusé

*Références : securite.md v1.1*

### US-03 — Construire la fiche Borne et la fiche Station

**BF-01 · Indispensable · 3 points · S3**

> En tant que **responsable réseau**, je veux une fiche Borne claire avec son statut, son risque et ses tickets, afin de de comprendre l'état d'une borne en un coup d'œil.

**Critères d'acceptation**

- [ ] La page Lightning de Borne__c reprend la maquette fiche-borne.png : en-tête, champs clés, onglets Sessions / Tickets / Détails
- [ ] Les champs remplis par le système sont en lecture seule sur la page
- [ ] La page Station__c affiche ses bornes et son technicien du secteur

*Références : maquettes/fiche-borne.png*

### US-04 — Charger les données de démonstration

**BF-01 · Indispensable · 2 points · S3**

> En tant que **équipe**, je veux des données de départ identiques dans chaque org, afin de de pouvoir tester et faire la démo.

**Critères d'acceptation**

- [ ] Un script ou un fichier d'import crée 6 stations (2 par ville) avec leur localisation, 15 bornes MRK/CAS/RBT-001 à 005, 3 clients avec badge et le compte « Clients VoltCare »
- [ ] Le script peut être relancé sans créer de doublons (upsert sur les External IDs)

*Références : dictionnaire-donnees.md §2*

## E3 - Simulation des bornes

### US-05 — Simuler 15 bornes OCPP

**BF-02 · Indispensable · 8 points · S4**

> En tant que **équipe**, je veux 15 bornes simulées qui démarrent, rechargent et envoient leurs mesures, afin de de disposer de données réalistes sans vraies bornes.

**Critères d'acceptation**

- [ ] Les 15 bornes se connectent au serveur central en OCPP 1.6 et envoient BootNotification, StatusNotification, StartTransaction, StopTransaction, MeterValues (30 s) et Heartbeat (60 s)
- [ ] Le serveur central republie chaque message sur Mosquitto au format exact du contrat MQTT v1.0 (topics, QoS, retain)
- [ ] Les sessions démarrent et s'arrêtent de façon aléatoire et réaliste ; l'énergie et la température évoluent de façon cohérente
- [ ] Les identifiants Mosquitto sont lus dans .env

*Références : contrat-mqtt.md v1.0*

### US-06 — Injecter des pannes et réparer une borne

**BF-02 · Indispensable · 3 points · S4**

> En tant que **équipe**, je veux provoquer une panne et la réparer à la demande, afin de de dérouler les scénarios de démo.

**Critères d'acceptation**

- [ ] Une commande provoque une panne sur une borne choisie (ex. surchauffe : la température monte puis la borne passe Faulted / HighTemperature)
- [ ] La commande « reparer MRK-001 » renvoie Available / NoError
- [ ] Des pannes aléatoires peuvent aussi se produire, avec une probabilité configurable

*Références : contrat-mqtt.md §6, §9*

### US-07 — Enregistrer l'historique brut en CSV

**BF-02 · Indispensable · 2 points · S4**

> En tant que **équipe IA**, je veux l'historique complet des messages des bornes, afin de d'entraîner le modèle de prédiction.

**Critères d'acceptation**

- [ ] Chaque message publié est aussi écrit dans un fichier CSV local, une ligne par message
- [ ] Le fichier contient tout ce qu'il faut pour calculer les indicateurs du contrat API IA §5.1

*Références : contrat-api-ia.md §7*

## E4 - Intégration temps réel

### US-08 — Mettre à jour le statut des bornes en temps réel

**BF-03 · Indispensable · 8 points · S5**

> En tant que **responsable réseau**, je veux que le statut d'une borne dans Salesforce reflète la réalité en moins de 10 secondes, afin de de réagir vite à une panne.

**Critères d'acceptation**

- [ ] La passerelle s'authentifie en OAuth 2.0 Client Credentials avec l'utilisateur Passerelle VoltCare
- [ ] Elle valide les messages, ignore les doublons et publie des Borne_Event__e par lots toutes les 2 s (composite/sobjects)
- [ ] Étant donné une borne Disponible, quand le simulateur la met en Faulted, alors Borne__c.Statut__c vaut « Hors service » en moins de 10 s
- [ ] Un STATUT plus ancien que Date_Dernier_Statut__c est ignoré ; une borne inconnue produit une ligne dans Integration_Log__c
- [ ] En cas d'erreur réseau : 3 nouveaux essais puis écriture dans gateway/echecs/

*Références : contrat-platform-event.md v1.0, seq-1*

### US-09 — Enregistrer les sessions de recharge

**BF-03 · Indispensable · 5 points · S5**

> En tant que **responsable réseau**, je veux que chaque recharge soit enregistrée et rattachée au client, afin de de suivre l'utilisation du réseau.

**Critères d'acceptation**

- [ ] SESSION_DEBUT crée une Session_Recharge__c (clé MRK-001-1287) rattachée au Contact dont Badge_RFID__c = id_tag
- [ ] SESSION_FIN complète la session : fin, énergie en kWh, durée, statut Terminée ou Interrompue selon la raison d'arrêt
- [ ] Recevoir deux fois le même événement ne crée pas de doublon

*Références : dictionnaire-donnees.md §4*

### US-10 — Agréger les mesures et purger l'historique

**BF-03 · Indispensable · 3 points · S5**

> En tant que **administrateur**, je veux une mesure agrégée par borne et par heure, conservée 72 h, afin de de rester sous les 5 Mo de stockage.

**Critères d'acceptation**

- [ ] La passerelle envoie un MESURE_AGREGEE par borne et par heure ; le trigger crée un Mesure_Borne__c
- [ ] Une purge planifiée supprime chaque nuit les mesures de plus de 72 h et les journaux de plus de 7 jours

*Références : contrat-platform-event.md §2, §6.5*

### US-11 — Détecter une borne injoignable

**BF-03 · Indispensable · 2 points · S5**

> En tant que **responsable réseau**, je veux savoir quelles bornes ne donnent plus de nouvelles, afin de de distinguer une panne d'une coupure de communication.

**Critères d'acceptation**

- [ ] Après 3 min sans heartbeat, la passerelle envoie INJOIGNABLE : Joignable__c passe à faux, le statut ne change pas et aucun ticket n'est créé
- [ ] Au retour des heartbeats (JOIGNABLE) ou de tout autre événement, Joignable__c repasse à vrai

*Références : etats-borne.puml*

### US-12 — Consulter le journal d'intégration

**BF-03 · Indispensable · 2 points · S5**

> En tant que **administrateur**, je veux un journal des erreurs d'intégration, afin de de diagnostiquer rapidement un problème.

**Critères d'acceptation**

- [ ] Toute erreur de traitement (passerelle, API IA, Telegram) crée une ligne Integration_Log__c avec la source, le message et le contenu
- [ ] Une vue de liste « Erreurs des dernières 24 h » existe

*Références : dictionnaire-donnees.md §9*

## E5 - Prédiction IA

### US-13 — Entraîner le modèle de prédiction des pannes

**BF-04 · Indispensable · 8 points · S6**

> En tant que **équipe IA**, je veux un modèle entraîné sur l'historique du simulateur, avec ses performances mesurées, afin de de prédire les pannes de façon fiable.

**Critères d'acceptation**

- [ ] Le jeu de données est construit à partir du CSV, avec les 10 indicateurs calculés exactement comme dans le contrat API IA §5.1
- [ ] Le modèle est évalué sur un jeu de test séparé : précision, rappel, matrice de confusion documentés dans ai-service/
- [ ] Le fichier ai-service/tests/exemples_indicateurs.json donne des cas de référence partagés avec l'Apex

*Références : contrat-api-ia.md §7*

### US-14 — Exposer l'API de prédiction

**BF-04 · Indispensable · 5 points · S6**

> En tant que **développeur Salesforce**, je veux une API /v1/predict protégée et toujours disponible, afin de d'obtenir les scores des bornes.

**Critères d'acceptation**

- [ ] POST /v1/predict et GET /v1/health respectent le contrat API IA v1.0 (formats, 401, 422, INDETERMINE si moins de 6 mesures)
- [ ] L'API est déployée sur Azure App Service avec Always On ; la clé API est un paramètre d'application
- [ ] Une collection Postman couvre les cas nominaux et d'erreur

*Références : contrat-api-ia.md v1.0*

### US-15 — Mettre à jour le score de risque toutes les heures

**BF-04 · Indispensable · 5 points · S6**

> En tant que **responsable réseau**, je veux le score de risque de chaque borne mis à jour toutes les heures, afin de d'anticiper les pannes.

**Critères d'acceptation**

- [ ] À HH:05, le Scheduled Apex lance le Queueable, qui appelle l'API via le Named Credential VoltCare_IA en un seul appel
- [ ] Les champs Score_Risque__c, Niveau_Risque__c, Facteurs_Risque__c, Date_Score__c et Version_Modele__c sont mis à jour
- [ ] En cas d'erreur ou de délai dépassé, les anciens scores sont conservés et l'erreur est journalisée

*Références : seq-3-prediction-ia*

## E6 - Maintenance & tableau de bord

### US-16 — Créer et affecter automatiquement un ticket de panne

**BF-05 · Indispensable · 5 points · S7**

> En tant que **technicien**, je veux recevoir automatiquement un ticket quand une borne de mon secteur tombe en panne, afin de d'intervenir sans attendre une plainte.

**Critères d'acceptation**

- [ ] Étant donné une borne sans ticket ouvert, quand elle passe Hors service, alors un Case Panne / Borne / priorité Haute est créé avec le code d'erreur
- [ ] Le Flow d'affectation renseigne OwnerId avec le technicien de la station de la borne
- [ ] Si la borne a déjà un ticket ouvert, aucun nouveau ticket n'est créé

*Références : seq-2-panne-ticket*

### US-17 — Créer un ticket de maintenance préventive

**BF-05 · Indispensable · 2 points · S7**

> En tant que **responsable réseau**, je veux qu'un ticket préventif soit créé quand le risque dépasse 70, afin de d'intervenir avant la panne.

**Critères d'acceptation**

- [ ] Étant donné une borne sans ticket ouvert, quand son score dépasse 70, alors un Case Maintenance préventive / Prédiction IA est créé avec le score
- [ ] Le ticket est affecté et notifié comme un ticket de panne

*Références : seq-3-prediction-ia*

### US-18 — Suivre et clôturer une intervention

**BF-06 · Indispensable · 3 points · S7**

> En tant que **technicien**, je veux mettre à jour et clôturer mon ticket depuis l'application mobile, afin de que la borne soit remise en service.

**Critères d'acceptation**

- [ ] Le technicien passe le ticket En cours puis Clôturé depuis l'application mobile Salesforce
- [ ] La clôture exige une Resolution__c (règle de validation)
- [ ] À la clôture d'un ticket Panne, la borne repasse Disponible et Date_Dernier_Statut__c reçoit l'heure de clôture

*Références : etats-ticket.puml*

### US-19 — Construire le tableau de bord du responsable

**BF-07 · Indispensable · 5 points · S7**

> En tant que **responsable réseau**, je veux un tableau de bord avec les indicateurs clés du réseau, afin de de piloter l'activité.

**Critères d'acceptation**

- [ ] Le tableau de bord affiche : taux d'occupation, énergie délivrée, nombre de pannes, bornes à risque (score > 70), délai moyen de réparation
- [ ] Il contient l'énergie par jour et par ville, les pannes par code d'erreur, les bornes les plus à risque et les tickets ouverts
- [ ] Il reprend la maquette tableau-de-bord.png et se met à jour après une panne de démo

*Références : maquettes/tableau-de-bord.png*

### US-20 — Réaffecter un ticket

**BF-05 · Indispensable · 1 points · S7**

> En tant que **responsable réseau**, je veux réaffecter un ticket à un autre technicien, afin de de répartir la charge.

**Critères d'acceptation**

- [ ] Le responsable change le propriétaire d'un ticket ; le nouveau technicien reçoit une alerte (REAFFECTATION)

*Références : securite.md §2*

## E7 - Portail client & notifications

### US-21 — Créer un compte client et enregistrer son badge

**BF-08 · Souhaité · 3 points · S8**

> En tant que **client conducteur**, je veux créer mon compte sur le portail et y associer mon badge, afin de de retrouver mes recharges.

**Critères d'acceptation**

- [ ] L'inscription libre (Configurable Self-Reg) crée un Contact du compte « Clients VoltCare » avec le profil VoltCare Client, après un code de vérification par email
- [ ] La page « Mon compte » permet de saisir le badge (Badge_RFID__c unique)
- [ ] Toutes les pages du portail exigent une connexion

*Références : securite.md §8*

### US-22 — Trouver une borne disponible sur la carte

**BF-08 · Souhaité · 5 points · S8**

> En tant que **client conducteur**, je veux voir les bornes sur une carte avec leur statut en temps réel, afin de de trouver une borne libre près de moi.

**Critères d'acceptation**

- [ ] Un LWC Leaflet / OpenStreetMap affiche les bornes à la position de leur station, en couleur selon leur statut
- [ ] Une liste filtrable (disponibles uniquement, ville) accompagne la carte ; un clic ouvre la fiche avec « Itinéraire » et « Signaler un problème »
- [ ] Le client ne voit ni les scores ni les codes d'erreur
- [ ] La page est utilisable sur mobile

*Références : maquettes/portail-carte.png, portail-mobile.png*

### US-23 — Consulter l'historique de ses recharges

**BF-08 · Souhaité · 3 points · S8**

> En tant que **client conducteur**, je veux voir l'historique de mes recharges, afin de de suivre ma consommation.

**Critères d'acceptation**

- [ ] La page « Mes recharges » affiche le résumé du mois et la liste des sessions du client
- [ ] Les données viennent de MesRechargesController, qui filtre toujours sur le contact connecté
- [ ] Un test Apex prouve qu'un client ne reçoit jamais la session d'un autre client

*Références : securite.md §5*

### US-24 — Signaler un problème sur une borne

**BF-08 · Souhaité · 5 points · S8**

> En tant que **client conducteur**, je veux signaler un problème sur une borne, afin de qu'il soit réparé.

**Critères d'acceptation**

- [ ] Le formulaire suit la maquette (borne, type, description, photo, me prévenir par email)
- [ ] Si la borne a déjà un ticket ouvert, le signalement est ajouté en commentaire
- [ ] Au-delà de 3 signalements sur 24 h, ou s'il existe déjà un signalement ouvert du client sur la borne, l'envoi est refusé
- [ ] Un signalement crédible crée un ticket Nouveau pour le technicien ; sinon un ticket À qualifier pour le responsable ; le message affiché au client est identique dans les deux cas

*Références : seq-4-signalement, dictionnaire-donnees.md §6*

### US-25 — Qualifier un signalement non confirmé

**BF-08 · Souhaité · 2 points · S8**

> En tant que **responsable réseau**, je veux confirmer ou rejeter un signalement non confirmé, afin de de ne pas déplacer un technicien pour rien.

**Critères d'acceptation**

- [ ] Le responsable voit la file « Qualification des signalements »
- [ ] Confirmer passe le ticket en Nouveau et l'affecte au technicien ; rejeter le clôture en « Non reproduit » et incrémente le compteur du client
- [ ] À partir de 3 signalements non fondés, les signalements du client passent tous À qualifier

*Références : etats-ticket.puml*

### US-26 — Recevoir une alerte Telegram

**BF-09 · Souhaité · 3 points · S8**

> En tant que **technicien**, je veux recevoir une alerte Telegram pour chaque nouveau ticket, afin de de réagir même hors de l'application.

**Critères d'acceptation**

- [ ] Notification_Ticket__e est publié à la création et à la réaffectation ; son abonné s'exécute en tant qu'administrateur
- [ ] Le message (borne, cause, n° de ticket) arrive au technicien et au responsable ; un ticket À qualifier n'alerte que le responsable
- [ ] Le jeton du bot est dans le Named Credential Telegram ; une erreur d'envoi est journalisée

*Références : seq-2-panne-ticket, securite.md §7*

## E8 - Bonus (Stripe, Agentforce)

### US-27 — Payer une session en mode test

**BF-10 · Bonus · 5 points · S9**

> En tant que **client conducteur**, je veux payer une recharge par carte (mode test Stripe), afin de de régler ma session en ligne.

**Critères d'acceptation**

- [ ] Depuis l'historique, le client paie une session terminée avec une carte de test Stripe
- [ ] Le statut de paiement est enregistré sur la session ; les clés Stripe sont dans un Named Credential

*Références : cahier des charges BF-10*

### US-28 — Obtenir un résumé IA de la borne

**BF-11 · Bonus · 3 points · S9**

> En tant que **technicien**, je veux un résumé de l'historique de la borne généré par Agentforce, afin de de préparer mon intervention plus vite.

**Critères d'acceptation**

- [ ] Depuis le ticket, le technicien obtient un résumé : pannes récentes, tendance de température, score et facteurs

*Références : cahier des charges BF-11*

## Historique

| Version | Date | Modification |
|---|---|---|
| 1.0 | 10/11/2026 | Premier jet |
