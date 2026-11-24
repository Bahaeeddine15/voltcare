# US-02 — Réalisation des profils, rôles et règles de partage

**Auteur :** Aymane  
**Exigence :** BF-01 — Indispensable  
**Sprint :** S3  
**Référence :** `securite.md` v1.1  
**Date de mise à jour :** 22 novembre 2026

## Objectif

Ce document présente les travaux réalisés pour mettre en place la séparation des droits, les profils, les rôles, les Permission Sets et les paramètres de partage du projet VoltCare.

## Configuration des profils

Les deux profils suivants ont été créés dans les métadonnées Salesforce :

- `VoltCare Interne`
- `VoltCare Client`

### VoltCare Interne

- Licence utilisateur : `Salesforce`
- Profil personnalisé créé
- Utilisé comme profil interne de base
- Aucun droit métier spécialisé n’est placé directement dans ce profil

Fichier :

- `salesforce/force-app/main/default/profiles/VoltCare Interne.profile-meta.xml`

### VoltCare Client

- Licence utilisateur : `Customer Community Login`
- Profil personnalisé créé
- Configuré pour les utilisateurs du portail client

Fichier :

- `salesforce/force-app/main/default/profiles/VoltCare Client.profile-meta.xml`

## Hiérarchie des rôles

La hiérarchie suivante a été créée :

```text
Responsable réseau
└── Technicien
```

Les rôles Salesforce sont présents dans les métadonnées :

- `Responsable réseau`
- `Technicien`

Fichiers :

- `salesforce/force-app/main/default/roles/Responsable_r_seau.role-meta.xml`
- `salesforce/force-app/main/default/roles/Technicien.role-meta.xml`

## Permission Sets

Trois Permission Sets ont été ajoutés au projet.

### VoltCare_Passerelle

Le Permission Set `VoltCare_Passerelle` a été créé pour l’utilisation technique de la passerelle.

Il contient :

- le droit système `API Enabled` ;
- un accès prévu à `Borne_Event__e`.

Fichier :

- `salesforce/force-app/main/default/permissionsets/VoltCare_Passerelle.permissionset-meta.xml`

### VoltCare_Client

Le Permission Set `VoltCare_Client` a été créé pour les utilisateurs du portail.

Il donne :

- la lecture de `Station__c` ;
- la lecture de `Borne__c` ;
- la lecture de `Case` ;
- la création de `Case` ;
- la lecture de `Contact` ;
- l’accès lecture à `Borne__c.Puissance_Max_kW__c` ;
- l’accès lecture à `Case.Borne__c` ;
- l’accès lecture/création aux champs :
  - `Case.Type_Probleme_Client__c`
  - `Case.Notifier_Client__c`

Aucun droit de suppression n’a été ajouté au Permission Set.

Fichier :

- `salesforce/force-app/main/default/permissionsets/VoltCare_Client.permissionset-meta.xml`

### VoltCare_Integrations

Le Permission Set `VoltCare_Integrations` a été créé comme point d’intégration pour les besoins externes futurs.

Fichier :

- `salesforce/force-app/main/default/permissionsets/VoltCare_Integrations.permissionset-meta.xml`

## Paramètres de partage

Un fichier de paramètres Salesforce a été ajouté :

- `salesforce/force-app/main/default/settings/Sharing.settings-meta.xml`

Ce fichier active les paramètres nécessaires au partage externe et contient notamment :

- le partage des utilisateurs portail ;
- le partage externe ;
- la visibilité standard des rapports ;
- les paramètres de partage des assets.

Les métadonnées des objets contiennent également les modèles de partage suivants :

| Objet | Modèle configuré |
|---|---|
| `Station__c` | Lecture/écriture |
| `Borne__c` | Contrôlé par le parent |
| `Session_Recharge__c` | Contrôlé par le parent |
| `Mesure_Borne__c` | Contrôlé par le parent |
| `Case` | Privé |
| `Contact` | Privé |
| `Integration_Log__c` | Privé |

## Manifestes Salesforce

Les métadonnées de sécurité ont été ajoutées aux manifestes.

Le manifest de référence contient notamment :

- les Permission Sets ;
- les profils ;
- les rôles `Responsable_r_seau` et `Technicien` ;
- les paramètres de partage `Sharing`.

Fichiers concernés :

- `VoltCare/manifest/package.xml`
- `salesforce/manifest/package.xml`

## Métadonnées Salesforce ajoutées

Les éléments suivants sont désormais présents dans le projet Salesforce :

- trois Permission Sets ;
- deux profils personnalisés ;
- deux rôles ;
- les paramètres `Sharing.settings-meta.xml` ;
- les droits de champ nécessaires au Permission Set client ;
- les références de sécurité dans les manifestes.

## Validation technique

Une validation à blanc a été exécutée depuis le projet Salesforce connecté à l’organisation `VoltCareOrg`.

Le dry-run Salesforce a été accepté sans erreur bloquante. Cette validation vérifie que les composants du manifest peuvent être lus par l’API Salesforce et préparés pour un déploiement.
