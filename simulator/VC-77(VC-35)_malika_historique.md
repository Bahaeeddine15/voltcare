# Ticket – Enregistreur CSV de l'historique brut

## 1. Objectif

Mettre en place un système d'enregistrement des messages MQTT dans des fichiers CSV afin de conserver un historique brut des événements et des mesures des bornes.

Cet historique servira de source de données pour l'entraînement et l'exploitation du module IA, notamment pour l'analyse et la prédiction des pannes.

## 2. Implémentation réalisée

### `historique.py`

Création d'un module dédié à l'enregistrement des messages MQTT.

Fonctionnalités implémentées :

- Réception des messages publiés par `publisher.py`.
- Enregistrement d'une ligne par message reçu.
- Utilisation d'une `Queue` et d'un thread dédié pour effectuer les écritures de manière non bloquante.
- Création automatique d'un fichier CSV par jour.
- Ajout de l'en-tête uniquement lors de la création du fichier.
- Ajout automatique de l'horodatage, du code de la station et de la date de mise en service à partir de la configuration des bornes.
- Vérification de la cohérence entre le code de la borne présent dans le topic MQTT et celui du message.

### Format des fichiers générés

Les fichiers sont enregistrés dans :

```text
simulator/
└── data/
    └── historique_AAAA-MM-JJ.csv
```

Chaque fichier contient les 15 colonnes suivantes :

```text
horodatage
code_borne
code_station
type
statut
code_erreur
transaction_id
id_tag
compteur_wh
energie_wh
puissance_w
tension_v
temperature_c
raison_arret
date_mise_en_service
```

Chaque message correspond à une seule ligne dans le CSV.

### Intégration avec `publisher.py`

Le module `historique.py` a été intégré au processus de publication MQTT.

Après la publication réussie d'un message, `publisher.py` transmet le topic et le contenu du message à la fonction `enregistrer()`.

L'enregistrement est ensuite effectué en arrière-plan par le thread dédié.

Le fichier `messages.csv` existant est conservé comme journal technique des publications MQTT. Le nouvel historique structuré est enregistré séparément dans le dossier `data/`.

## 3. Tests et vérifications

### Tests unitaires

Ajout et exécution des tests du module d'historisation dans :

```text
tests/test_historique.py
```

Exécuter les tests avec :

```powershell
python -m pytest tests/test_historique.py -v
```

Pour exécuter l'ensemble des tests :

```powershell
python -m pytest tests/ -v
```

### Test de publication et d'enregistrement

Un fichier `test_csv.py` a été utilisé pour tester manuellement l'intégration entre `publisher.py` et `historique.py`.

Il permet de publier plusieurs types de messages (`boot`, `status`, `meter`) et de vérifier leur enregistrement dans les CSV.

Exécution :

```powershell
python test_csv.py
```

### Vérification des fichiers générés

Lister les fichiers d'historique :

```powershell
dir data
```

Afficher leur contenu :

```powershell
Import-Csv .\data\historique_*.csv | Format-Table -AutoSize
```

Vérifier le nombre de messages enregistrés par type :

```powershell
Import-Csv .\data\historique_*.csv | Group-Object type
```

Le fichier `verifier_historique.py` sert également à faciliter la consultation et la vérification des données enregistrées.

## 4. Exploitation des données pour l'IA

L'objectif est de disposer d'un historique suffisamment structuré pour permettre son exploitation par le module IA.

La validation prévue consiste à :

1. Laisser le système collecter les données pendant une heure.
2. Lire le fichier CSV avec Pandas.
3. Sélectionner les données d'une borne.
4. Calculer les indicateurs définis dans la section 5.1 du ticket.
5. Vérifier que les données enregistrées permettent d'effectuer ces calculs.

Les fichiers CSV constituent ainsi la base de données historique destinée aux traitements IA.

## 5. Gestion des fichiers

Le dossier `simulator/data/` est exclu du dépôt Git afin de ne pas versionner les fichiers CSV générés pendant l'exécution.

Les fichiers `test_csv.py` et `verifier_historique.py` sont des outils de développement et de validation. Ils pourront être supprimés ou déplacés lorsque les tests et l'intégration du module IA seront finalisés.

## 6. Résultat

L'enregistreur CSV est intégré au processus de publication MQTT.

Les messages publiés sont conservés dans des fichiers quotidiens, avec une structure commune de 15 colonnes et une ligne par message.

L'historique obtenu peut être exploité avec Pandas pour préparer les données et calculer les indicateurs nécessaires au module IA.