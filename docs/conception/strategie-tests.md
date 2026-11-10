# Stratégie de test et scénario de démonstration — VoltCare

| | |
|---|---|
| **Version** | 1.0 (brouillon) |
| **Sprint** | S2 — Conception |
| **Exigences visées** | Qualité : couverture Apex ≥ 75 %, collection Postman pour chaque API · Temps réel : statut à jour en moins de 10 s · Critère d'acceptation du cahier des charges |
| **Documents liés** | `user-stories.md`, contrats v1.0, diagrammes de séquence, `securite.md` v1.1 |

---

## 1. Objectifs

1. Prouver que chaque exigence (BF-01 à BF-11 et besoins non fonctionnels) est respectée : chaque exigence est reliée à au moins un test (matrice §7).
2. Détecter les régressions le plus tôt possible : **chaque Pull Request contient ses tests**.
3. Arriver à la soutenance avec une démonstration **répétée, chronométrée et avec un plan B** pour chaque point fragile.

**Critère d'acceptation du cahier des charges** : *en démonstration, une borne simulée tombe en panne ; son statut change dans Salesforce, un ticket est créé et affecté, le technicien est notifié et le tableau de bord se met à jour.* → scénario E2E-1.

---

## 2. Les niveaux de test

```
              ▲  Démo de soutenance (1 répétition générale)
             ▲▲▲  Tests de bout en bout E2E-1 à E2E-9 (chaque vendredi)
           ▲▲▲▲▲  Tests d'intégration : Postman, simulateur + Mosquitto + passerelle
        ▲▲▲▲▲▲▲▲  Tests unitaires : pytest, classes de test Apex, Jest (à chaque PR)
```

Plus on monte, plus les tests sont lents et rares. La majorité des erreurs doit être trouvée en bas de la pyramide.

---

## 3. Tests unitaires et d'intégration par brique

### 3.1 Simulateur et passerelle (Python — `pytest`)

| Test | Vérifie |
|---|---|
| Format des messages | Chaque message produit est validé contre un **schéma JSON** tiré du contrat MQTT (champs obligatoires, valeurs OCPP autorisées, UUID, dates UTC) |
| Topics | Le topic correspond au type de message et au code borne |
| Dédoublonnage | Un `message_id` reçu deux fois n'est traité qu'une fois |
| Message invalide | Il est republié sur `voltcare/erreurs` et ignoré |
| Agrégation horaire | 120 mesures donnent la bonne moyenne, le bon maximum et le bon index d'énergie |
| Injoignable | 3 min sans heartbeat produisent un seul `INJOIGNABLE`, puis `JOIGNABLE` à la reprise |
| Envoi par lots | Plus de 200 événements sont découpés en plusieurs appels |
| Réessais | Une réponse 503 simulée provoque 3 essais (2 s, 4 s, 8 s) puis l'écriture dans `gateway/echecs/` ; une réponse 401 provoque un nouveau jeton |

Les appels à Salesforce sont **simulés** (bibliothèque `responses` ou `unittest.mock`) : les tests ne consomment aucun appel API.

**Test d'intégration local** : Mosquitto lancé dans Docker, simulateur avec 3 bornes, passerelle branchée sur une org perso. On vérifie à la main qu'une panne arrive dans Salesforce.

### 3.2 Service IA (Python — `pytest` + `TestClient` de FastAPI)

| Test | Vérifie |
|---|---|
| Calcul des indicateurs | Les 10 indicateurs calculés à partir des mesures brutes de `tests/exemples_indicateurs.json` sont exactement ceux attendus (même fichier que les tests Apex) |
| `POST /v1/predict` sans clé ou avec une mauvaise clé | 401 |
| Requête invalide (champ manquant, valeur hors plage, plus de 50 bornes) | 422 |
| Moins de 6 mesures | `score_risque: null`, `niveau: INDETERMINE` |
| Cas nominal | Un score entre 0 et 100, un niveau cohérent avec les seuils 40 / 70, de 1 à 3 facteurs |
| `GET /v1/health` | 200 et version du modèle |

**Qualité du modèle** (mesurée une fois, sur un jeu de test séparé) : précision, rappel, matrice de confusion. Objectif proposé : **rappel ≥ 0,80** sur la classe « panne » — rater une panne coûte plus cher qu'une fausse alerte.

### 3.3 Salesforce (classes de test Apex)

Une classe `TestDataFactory` crée les données de test (stations, bornes, clients, utilisateurs) pour toutes les classes.

| Classe de test | Cas couverts |
|---|---|
| `BorneEventTriggerTest` | Chaque `Type__c` (BOOT, STATUT, SESSION_DEBUT, SESSION_FIN, MESURE_AGREGEE, INJOIGNABLE, JOIGNABLE) · conversion des 9 statuts OCPP · événement en retard ignoré · borne inconnue journalisée · même événement reçu deux fois sans doublon · **lot de 200 événements** (limites Salesforce) — avec `Test.getEventBus().deliver()` |
| `TicketAutomatisationTest` | Ticket créé quand une borne passe Hors service · pas de deuxième ticket si un ticket est ouvert · affectation au technicien de la station · clôture → borne Disponible · résolution obligatoire |
| `PredictionQueueableTest` | Réponse 200 (scores mis à jour) · score > 70 → ticket préventif, une seule fois · 401, 500 et délai dépassé → anciens scores conservés et journal — avec `HttpCalloutMock` |
| `NotificationTelegramTest` | Publication de `Notification_Ticket__e` à la création et à la réaffectation · appel Telegram simulé · erreur journalisée · ticket À qualifier → responsable seulement |
| `SignalementControllerTest` | Les 5 branches du tri (ticket existant, limite de 3 sur 24 h, signalement ouvert sur la borne, crédible, non confirmé) · client marqué à vérifier · `ContactId` toujours celui de l'utilisateur connecté — avec `System.runAs` d'un utilisateur du portail |
| `MesRechargesControllerTest` | **Un client ne reçoit jamais la session d'un autre client** (deux clients, `System.runAs`) |
| `PurgeTest` | Mesures de plus de 72 h et journaux de plus de 7 jours supprimés, les autres conservés |
| `SecuriteTest` | Un technicien ne voit pas les tickets d'un autre · l'utilisateur Passerelle ne peut pas lire `Borne__c` |

**Couverture** : objectif **85 %** pour l'équipe, seuil bloquant **75 %** (exigence du cahier des charges et seuil de déploiement Salesforce). Commande :

```powershell
sf apex run test --test-level RunLocalTests --code-coverage --result-format human --target-org voltcare-perso
```

**Les Flows** (affectation, ticket de panne, clôture) sont couverts par les classes de test ci-dessus, qui créent et modifient des enregistrements et vérifient le résultat.

### 3.4 Composants du portail (LWC — Jest)

Le projet Salesforce contient déjà `jest.config.js`. Tests proposés :
- la carte affiche un marqueur par borne, de la couleur de son statut ;
- le formulaire de signalement refuse l'envoi sans borne, sans type ou sans description ;
- la page « Mes recharges » affiche un message quand il n'y a aucune session.

```powershell
cd salesforce
npm install
npm run test:unit
```

### 3.5 Collections Postman (exigence du cahier des charges)

Dossier `docs/postman/` :

| Collection | Requêtes |
|---|---|
| `VoltCare - Salesforce` | Jeton OAuth Client Credentials · publication d'un lot de `Borne_Event__e` (un exemple par type) · lecture des limites (`/limits`) |
| `VoltCare - API IA` | `GET /v1/health` · `POST /v1/predict` nominal · sans clé (401) · requête invalide (422) · données insuffisantes |

Chaque requête contient des **assertions** (onglet *Tests*), par exemple le code HTTP attendu. Les secrets sont dans un **environnement Postman local**, jamais exporté dans le repo.

---

## 4. Tests de bout en bout (chaque vendredi)

Réalisés sur l'**org de démo**, avec le simulateur, la passerelle et l'API IA réels. Le résultat est noté dans le tableau de suivi (§6).

| ID | Scénario | Étapes | Résultat attendu |
|---|---|---|---|
| **E2E-1** | **Panne détectée** (critère d'acceptation) | Provoquer une surchauffe sur `MRK-001` | Statut « Hors service » en **moins de 10 s** · ticket Panne créé et affecté · alerte Telegram reçue · tableau de bord à jour |
| E2E-2 | Réparation | Technicien : En cours, puis `reparer MRK-001`, puis Clôturé (Réparé) | Borne Disponible · ticket Clôturé · aucun « Faulted » rejoué |
| E2E-3 | Prédiction | Faire monter la température de `CAS-004`, puis lancer la prédiction à la main | Score > 70 · ticket Maintenance préventive · un seul ticket même si on relance |
| E2E-4 | Borne injoignable | Couper les heartbeats de `RBT-004` pendant 4 min, puis les rétablir | Injoignable, statut inchangé, aucun ticket · puis Joignable |
| E2E-5 | Signalement crédible | Un client qui vient de recharger sur `MRK-002` signale un problème | Ticket Nouveau pour le technicien · alerte Telegram · email au client |
| E2E-6 | Signalement non confirmé | Un client qui n'a jamais rechargé signale `MRK-003` (qui fonctionne) | Ticket À qualifier pour le responsable · rejet en « Non reproduit » · compteur du client à 1 · même message affiché au client |
| E2E-7 | Isolation des clients | Deux clients consultent « Mes recharges » | Chacun ne voit que ses propres sessions |
| E2E-8 | Robustesse | Arrêter la passerelle 1 min pendant que le simulateur tourne, puis la relancer · couper l'API IA pendant un calcul | Les derniers statuts sont rejoués sans doublon · erreur IA journalisée, anciens scores conservés |
| E2E-9 | Endurance | Faire tourner les 15 bornes pendant 1 h | Appels API et événements publiés sous les limites (`/limits`) · stockage relevé dans *Storage Usage* |

**Lancer la prédiction sans attendre HH:05** (Developer Console → *Execute Anonymous*) :

```apex
System.enqueueJob(new PredictionQueueable());
```

---

## 5. Tests non fonctionnels

| Exigence | Comment on la mesure | Seuil |
|---|---|---|
| Temps réel | Écart entre `Horodatage__c` de l'événement et `LastModifiedDate` de la borne, sur 20 changements de statut | **< 10 s** pour 100 % des cas, ≈ 5 s en moyenne |
| Limites Salesforce | Requête `/limits` après E2E-9 : `DailyApiRequests`, `HourlyPublishedPlatformEvents` | Moins de 50 % de la limite |
| Stockage | *Setup → Storage Usage* chaque vendredi | < 4 Mo sur 5 Mo |
| Sécurité | `SecuriteTest`, `MesRechargesControllerTest`, et recherche de secrets dans le repo (`git grep -i "secret\|token\|api_key"` ou l'outil `gitleaks`) | Aucun accès non autorisé, aucun secret dans Git |
| Ergonomie | Portail ouvert sur un téléphone (carte, historique, signalement) | Utilisable sans zoom |
| Couverture Apex | `sf apex run test … --code-coverage` | ≥ 75 % (objectif 85 %) |

---

## 6. Organisation

- **À chaque PR** : les tests unitaires de la brique passent ; le relecteur vérifie qu'un test accompagne chaque nouvelle règle.
- **Chaque vendredi** : l'intégrateur déploie `main` dans l'org de démo, puis l'équipe déroule les scénarios E2E déjà réalisables.
- **Anomalies** : un ticket Jira de type **Bug**, lié à la story concernée, avec les étapes pour reproduire.
- **Suivi** : tableau `docs/tests/resultats.md` — une ligne par scénario et par semaine (✅ / ❌ / non testé). Il servira tel quel dans le rapport.
- **Semaine 9** : campagne complète (tous les tests unitaires, Postman, E2E-1 à E2E-9, tests non fonctionnels) puis correction des anomalies.

---

## 7. Matrice de traçabilité

| Exigence | Stories | Tests unitaires / intégration | Bout en bout |
|---|---|---|---|
| BF-01 Modèle de données | US-01 à US-04 | Déploiement sans erreur, `SecuriteTest` | Tous |
| BF-02 Simulation | US-05 à US-07 | pytest simulateur | E2E-1, E2E-9 |
| BF-03 Temps réel | US-08 à US-12 | pytest passerelle, `BorneEventTriggerTest`, `PurgeTest`, Postman Salesforce | E2E-1, E2E-4, E2E-8 |
| BF-04 Prédiction IA | US-13 à US-15 | pytest IA, `PredictionQueueableTest`, Postman API IA | E2E-3, E2E-8 |
| BF-05 Tickets | US-16, US-17, US-20 | `TicketAutomatisationTest` | E2E-1, E2E-3 |
| BF-06 Intervention | US-18 | `TicketAutomatisationTest` | E2E-2 |
| BF-07 Tableau de bord | US-19 | — (vérification visuelle) | E2E-1 |
| BF-08 Portail | US-21 à US-25 | `SignalementControllerTest`, `MesRechargesControllerTest`, Jest | E2E-5 à E2E-7 |
| BF-09 Telegram | US-26 | `NotificationTelegramTest` | E2E-1, E2E-5 |
| BF-10 Stripe (bonus) | US-27 | À définir si réalisé | — |
| BF-11 Agentforce (bonus) | US-28 | À définir si réalisé | — |
| Sécurité, temps réel, limites, qualité | — | §5 | E2E-7 à E2E-9 |

---

## 8. Scénario de la démonstration finale (≈ 10 minutes)

### 8.1 Rôles des 6 membres

| Rôle | Écran | Ce qu'il fait |
|---|---|---|
| Présentateur | — | Raconte l'histoire et enchaîne les étapes |
| Opérateur simulateur | Terminal (simulateur + passerelle) | Provoque la panne, puis la réparation |
| Responsable réseau | Salesforce (fiche borne, tableau de bord) | Montre les mises à jour en direct |
| Technicien | Téléphone (app Salesforce + Telegram), projeté | Reçoit l'alerte, traite le ticket |
| Client | Portail sur téléphone ou navigateur | Carte, historique, signalement |
| Responsable IA | Notebook ou API | Explique le modèle et le score |

### 8.2 Déroulé

| Minute | Étape | Ce que le jury voit |
|---|---|---|
| 0:00 | **Contexte** : le problème des pannes détectées trop tard | Diagramme d'architecture |
| 1:00 | **Le réseau en direct** | Tableau de bord : 15 bornes, carte du portail |
| 2:00 | **La panne** (E2E-1) : surchauffe de `MRK-001` | En moins de 10 s : borne rouge sur le tableau de bord et la carte, ticket créé et affecté, alerte Telegram sur le téléphone du technicien |
| 4:00 | **L'intervention** (E2E-2) | Le technicien prend le ticket, répare, clôture : la borne redevient verte |
| 5:30 | **L'anticipation** (E2E-3) : la température de `CAS-004` monte | Lancement du calcul : score 80+, facteurs affichés, ticket préventif créé avant toute panne |
| 7:00 | **Le client** (E2E-5) | Carte des bornes disponibles, historique, signalement d'un problème → ticket |
| 8:30 | **La qualité** | Rapport de couverture Apex, résultats des tests E2E, journal d'intégration |
| 9:30 | **Conclusion** | Ce qui a été réalisé, limites, perspectives |

### 8.3 Plan B

| Risque | Plan B |
|---|---|
| L'API IA sur Azure ne répond pas | API lancée en local et exposée avec ngrok · changer l'URL du Named Credential (≈ 1 min, préparé à l'avance) |
| Pas de Wi-Fi à l'école | Partage de connexion d'un téléphone (simulateur, passerelle et Salesforce n'ont besoin que d'Internet) |
| Telegram ne reçoit rien | Montrer l'alerte dans l'app Salesforce et la ligne dans `Integration_Log__c` |
| La démo en direct échoue | **Vidéo de la démo complète enregistrée la veille**, prête à lancer |
| Org polluée par les essais | Script de remise à zéro des données de démo (US-04) lancé avant la soutenance |

### 8.4 Check-list

**La veille**
- [ ] `main` déployé dans l'org de démo, tous les tests Apex verts
- [ ] Données de démo réinitialisées, stockage < 4 Mo
- [ ] Prédiction planifiée (HH:05) active, API IA répond sur `/v1/health`
- [ ] Bot Telegram testé avec le téléphone du technicien
- [ ] Vidéo de secours enregistrée
- [ ] Répétition générale chronométrée

**Une heure avant**
- [ ] Simulateur et passerelle lancés (15 bornes connectées)
- [ ] Onglets ouverts : tableau de bord, fiche `MRK-001`, portail client, liste des tickets
- [ ] Téléphones chargés, notifications des autres applications coupées
- [ ] Commande de prédiction prête dans *Execute Anonymous*

---

## 9. Points à valider en équipe

- [ ] Objectif de rappel du modèle : **≥ 0,80** ?
- [ ] Objectif de couverture : **85 %** (seuil bloquant 75 %) ?
- [ ] Répartition des 6 rôles de la démonstration (§8.1) ?

## Historique

| Version | Date | Modification |
|---|---|---|
| 1.0 | 10/11/2026 | Premier jet |
