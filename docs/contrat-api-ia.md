# Contrat d'interface — API IA de prédiction des pannes

| | |
|---|---|
| **Version** | 1.0 |
| **Ticket** | VC-12 |
| **Producteur** | Service IA FastAPI (`ai-service/`) |
| **Consommateur** | Salesforce — Queueable Apex lancé par un Scheduled Apex (`salesforce/`) |
| **Contrats liés** | `contrat-mqtt.md` v1.0, `contrat-platform-event.md` v1.0 |
| **Statut** | Validé par l'équipe |

---

## 1. Principes

- Salesforce **calcule les indicateurs** (features) de chaque borne à partir de ses propres données, puis les envoie à l'API.
- L'API **ne stocke rien** et ne lit aucune autre source : elle reçoit des indicateurs, applique le modèle et renvoie un score. Elle est donc simple à tester avec Postman.
- Un seul appel pour **toutes les bornes** (envoi par lot), et non un appel par borne.
- Le score va de **0** (aucun risque) à **100** (panne quasi certaine). Au-dessus de **70**, Salesforce crée un ticket de maintenance préventive (BF-05).

## 2. Déroulement

```
Scheduled Apex (toutes les heures, à HH:05)
   → Queueable Apex : calcule les indicateurs des 15 bornes
   → POST /v1/predict (1 seul appel)
   → met à jour le score sur chaque Borne__c
   → si score > 70 et aucun ticket ouvert : crée un Case
```

L'appel a lieu à **HH:05** pour que les `MESURE_AGREGEE` de l'heure écoulée (envoyées à HH:00) soient déjà arrivées.

## 3. Endpoints

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/v1/predict` | Calcule le score de risque d'une ou plusieurs bornes |
| `GET` | `/v1/health` | Vérifie que le service répond et indique la version du modèle |

Le `/v1` dans le chemin permet de faire évoluer l'API plus tard sans casser Salesforce.

## 4. Sécurité

- Chaque requête porte l'en-tête **`X-API-Key`**. Sans clé ou avec une mauvaise clé : réponse **401**.
- Côté Salesforce, l'URL et la clé sont stockées dans un **Named Credential** (`VoltCare_IA`) associé à un **External Credential** : **aucune clé dans le code Apex**.
- Côté API, la clé attendue est lue dans une variable d'environnement (`API_KEY`), **jamais** écrite dans le code ni sur GitHub.
- HTTPS obligatoire (fourni par Azure App Service via `*.azurewebsites.net`, ou par ngrok en secours).
- Sur Azure, la clé est définie dans les **paramètres d'application** (*Environment variables*) du service, pas dans un fichier.

## 5. `POST /v1/predict`

### 5.1 Requête

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `date_calcul` | string (ISO 8601 UTC) | oui | Moment du calcul des indicateurs |
| `bornes` | tableau (1 à 50 éléments) | oui | Une entrée par borne |

Chaque élément de `bornes` :

| Champ | Type | Obligatoire | Plage | Description |
|---|---|---|---|---|
| `code_borne` | string | oui | | Ex. `"MRK-001"` |
| `age_mois` | integer | oui | 0 – 240 | Ancienneté de la borne |
| `temperature_moy_24h` | number | oui | −20 – 120 | Moyenne des `Temperature_Moy_C__c` des dernières 24 h |
| `temperature_max_24h` | number | oui | −20 – 120 | Maximum des `Temperature_Max_C__c` des dernières 24 h |
| `temperature_max_1h` | number | oui | −20 – 120 | `Temperature_Max_C__c` de la dernière heure |
| `tension_moy_24h` | number | oui | 0 – 300 | Moyenne des `Tension_Moy_V__c` des dernières 24 h |
| `energie_24h_kwh` | number | oui | ≥ 0 | Énergie délivrée sur 24 h |
| `nb_sessions_24h` | integer | oui | ≥ 0 | Sessions terminées sur 24 h |
| `nb_pannes_30j` | integer | oui | ≥ 0 | Tickets de panne créés sur 30 jours |
| `jours_depuis_maintenance` | integer | oui | ≥ 0 | Jours depuis la dernière clôture de ticket (ou depuis la mise en service si aucun) |
| `nb_mesures_24h` | integer | oui | 0 – 24 | Nombre de `Mesure_Borne__c` disponibles sur 24 h (qualité des données) |

```json
{
  "date_calcul": "2026-10-15T13:05:00Z",
  "bornes": [
    {
      "code_borne": "MRK-001",
      "age_mois": 38,
      "temperature_moy_24h": 52.4,
      "temperature_max_24h": 78.9,
      "temperature_max_1h": 81.2,
      "tension_moy_24h": 226.1,
      "energie_24h_kwh": 184.6,
      "nb_sessions_24h": 9,
      "nb_pannes_30j": 2,
      "jours_depuis_maintenance": 41,
      "nb_mesures_24h": 24
    },
    {
      "code_borne": "CAS-003",
      "age_mois": 6,
      "temperature_moy_24h": 38.7,
      "temperature_max_24h": 46.0,
      "temperature_max_1h": 41.5,
      "tension_moy_24h": 230.2,
      "energie_24h_kwh": 96.3,
      "nb_sessions_24h": 5,
      "nb_pannes_30j": 0,
      "jours_depuis_maintenance": 183,
      "nb_mesures_24h": 24
    }
  ]
}
```

### 5.2 Réponse `200 OK`

| Champ | Type | Description |
|---|---|---|
| `version_modele` | string | Ex. `"rf-2026-10-28"` (type de modèle + date d'entraînement) |
| `resultats` | tableau | Une entrée par borne, **dans le même ordre** que la requête |

Chaque élément de `resultats` :

| Champ | Type | Description |
|---|---|---|
| `code_borne` | string | Repris de la requête |
| `score_risque` | integer \| null | 0 à 100 ; `null` si la borne n'a pas pu être évaluée |
| `niveau` | string | `FAIBLE` (0–39), `MOYEN` (40–70), `ELEVE` (71–100), ou `INDETERMINE` |
| `facteurs` | tableau de string | Les 1 à 3 indicateurs qui ont le plus pesé dans le score — affichés au technicien |
| `avertissement` | string \| null | Ex. `"Données incomplètes : 9 mesures sur 24"` |

```json
{
  "version_modele": "rf-2026-10-28",
  "resultats": [
    {
      "code_borne": "MRK-001",
      "score_risque": 84,
      "niveau": "ELEVE",
      "facteurs": ["temperature_max_1h", "nb_pannes_30j", "temperature_max_24h"],
      "avertissement": null
    },
    {
      "code_borne": "CAS-003",
      "score_risque": 12,
      "niveau": "FAIBLE",
      "facteurs": ["age_mois"],
      "avertissement": null
    }
  ]
}
```

### 5.3 Données insuffisantes

Si `nb_mesures_24h` est inférieur à **6**, l'API ne calcule pas de score pour cette borne : `score_risque: null`, `niveau: "INDETERMINE"`, et un avertissement. Les autres bornes du lot sont évaluées normalement.

### 5.4 Erreurs

| Code | Cas | Corps |
|---|---|---|
| `401` | Clé API absente ou invalide | `{ "detail": "Clé API invalide" }` |
| `422` | Requête mal formée (champ manquant, valeur hors plage, plus de 50 bornes) — format standard de FastAPI | `{ "detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }` |
| `500` | Erreur interne du modèle | `{ "detail": "Erreur interne" }` |
| `503` | Modèle non chargé | `{ "detail": "Modèle indisponible" }` |

## 6. `GET /v1/health`

Pas de clé API requise.

```json
{ "statut": "ok", "version_modele": "rf-2026-10-28", "modele_charge": true }
```

## 7. Règle d'or : des indicateurs calculés de la même façon partout

Le modèle est entraîné en Python sur l'historique du simulateur, puis utilisé avec des indicateurs calculés **en Apex**. Si les deux calculs diffèrent (une moyenne sur 12 h d'un côté, sur 24 h de l'autre), le modèle se trompe sans qu'aucune erreur n'apparaisse.

Les définitions du §5.1 font donc foi **des deux côtés** :

- le script d'entraînement (`ai-service/`) calcule les indicateurs **exactement** comme décrit ;
- la classe Apex qui prépare la requête aussi ;
- les deux sont testés avec **le même jeu d'exemples** (`ai-service/tests/exemples_indicateurs.json`), qui donne pour une borne fictive ses mesures brutes et les indicateurs attendus.

## 8. Traitement côté Salesforce

### 8.1 Champs sur `Borne__c`

| Champ | Type | Rempli par |
|---|---|---|
| `Date_Mise_En_Service__c` | Date | Saisie à la création de la borne (sert à calculer `age_mois`) |
| `Score_Risque__c` | Number(3,0) | `score_risque` |
| `Niveau_Risque__c` | Picklist : Faible, Moyen, Élevé, Indéterminé | `niveau` |
| `Facteurs_Risque__c` | Text(255) | `facteurs`, séparés par des virgules |
| `Date_Score__c` | DateTime | Moment de la réponse |
| `Version_Modele__c` | Text(40) | `version_modele` |

### 8.2 Règles

1. **Score > 70** et **aucun Case ouvert** sur la borne → création d'un Case de type « Maintenance préventive », affecté au technicien du secteur (BF-05). S'il existe déjà un Case ouvert, on ne crée rien.
2. **Score `null`** → le score précédent est conservé, seul `Niveau_Risque__c` passe à « Indéterminé ».
3. **Erreur ou délai dépassé** → les scores précédents sont conservés, aucun ticket n'est créé, et une ligne est écrite dans `Integration_Log__c` (source `API_IA`, code HTTP, message).
4. **Délai d'attente** de l'appel Apex : **120 secondes** (le maximum autorisé). Avec Azure et *Always On*, le service ne se met pas en veille, mais cette marge couvre un redémarrage du service ou le passage en secours sur ngrok.

## 9. Volumétrie

- 24 appels par jour (1 par heure), chacun avec 15 bornes.
- Temps de réponse visé, service réveillé : **< 2 s**.
- Limite Salesforce : 100 appels sortants par transaction ; on en fait 1.

## 10. Décisions d'équipe

- [x] Fréquence : **toutes les heures**, à HH:05
- [x] Seuils : **FAIBLE < 40, MOYEN 40–70, ELEVE > 70**
- [x] L'API renvoie les **facteurs** du score
- [x] Hébergement : **Azure App Service** (Linux, Python), offre **Azure for Students**, avec l'option **Always On** activée pour éviter la mise en veille. Solution de secours : API en local exposée avec **ngrok**
- [x] Données d'entraînement : le **simulateur** écrit aussi chaque message dans un **fichier CSV** local, qui sert d'historique brut pour entraîner le modèle

## Historique

| Version | Date | Modification |
|---|---|---|
| 1.0 | 15/10/2026 | Premier jet |
| 1.0 | 15/10/2026 | Décisions d'équipe : toutes les heures, seuils 40/70, facteurs renvoyés, hébergement Azure App Service (secours ngrok), historique CSV écrit par le simulateur |
