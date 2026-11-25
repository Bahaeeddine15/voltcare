# VoltCare — Partie Salesforce

Projet SFDX de VoltCare (PFS ENSA Marrakech). Ce fichier explique **ce que contient le code** et **comment l'installer dans une org** (org perso `voltcare-perso` ou org de démo `voltcare-demo`).

> État : fin du Sprint 3 — branche `VC-68-69-station-app-donnees`, qui regroupe tout le code Salesforce du sprint.

---

## 1. Ce que contient la branche

Toutes les branches de code du Sprint 3 ont été fusionnées dans `VC-68-69-station-app-donnees` (aucun conflit), pour une seule PR vers `main`.

| Ticket | Auteur | Contenu |
|---|---|---|
| VC-29 | Aya | Objets `Station__c`, `Borne__c` ; champs Case, Contact, User |
| VC-59 / VC-61 | Malika | `Session_Recharge__c`, `Mesure_Borne__c`, `Integration_Log__c`, Platform Events `Borne_Event__e` et `Notification_Ticket__e` |
| VC-64 / VC-65 | Aymane | Profils « VoltCare Interne » / « VoltCare Client », rôles Responsable réseau > Technicien, permission sets Client / Integrations / Passerelle, partage privé (OWD) |
| VC-62 | Safia | File d'attente « Qualification des signalements », règle de validation « Résolution obligatoire à la clôture » |
| VC-63 | Safia | Permission sets `VoltCare_Responsable` et `VoltCare_Technicien` |
| VC-66 / VC-67 | Hanane | `TestDataFactory`, `SecuriteTest`, page Lightning + layout + compact layout de la Borne |
| VC-68 | Bahae | Onglets Station / Borne / Session, page `Station_Record_Page`, compact layout Station, application Lightning « VoltCare » |
| VC-69 | Bahae | Script de données de démo `scripts/apex/donnees-demo.apex` |

### Corrections faites pendant l'intégration

| Avant | Après | Pourquoi |
|---|---|---|
| `Notifiaction_Ticket__e` | `Notification_Ticket__e` | Faute de frappe ; nom du dictionnaire v1.3 |
| `Session_Recharge__c.Cle_de_session__c` | `Cle_Session__c` | Nom du contrat Platform Event et du dictionnaire (upsert de la passerelle) |
| `TestDataFactory` | utilise `Cle_Session__c` | Suite au renommage |
| — | permission set `VoltCare_Admin` | Les champs déployés par metadata n'ont **aucun** FLS, même pour l'admin → sans lui, les tests échouent (`fields being inaccessible`) |
| Profil `VoltCare Interne` | + application VoltCare visible et par défaut | VC-68 |

> ⚠️ Toute nouvelle classe, trigger ou flow doit utiliser `Cle_Session__c` et `Notification_Ticket__e`.

---

## 2. Prérequis

- Salesforce CLI (`sf --version`) et VS Code + Salesforce Extension Pack
- Une org connectée : `sf org login web --alias voltcare-perso`
- Se placer dans le dossier `salesforce/` pour toutes les commandes ci-dessous

---

## 3. Installer dans une org neuve (≈ 5 min)

L'ordre est important : les **rôles** ne peuvent être créés qu'une fois le partage de Case/Contact passé en **Privé**, et ce réglage n'est appliqué qu'à la fin d'un déploiement. D'où deux passes.

**Étape 1 — Tout déployer sauf les rôles**
```
sf project deploy start --target-org voltcare-perso --source-dir force-app/main/default/objects --source-dir force-app/main/default/classes --source-dir force-app/main/default/flexipages --source-dir force-app/main/default/layouts --source-dir force-app/main/default/tabs --source-dir force-app/main/default/applications --source-dir force-app/main/default/permissionsets --source-dir force-app/main/default/profiles --source-dir force-app/main/default/queues --source-dir force-app/main/default/settings --source-dir force-app/main/default/standardValueSets
```

**Étape 2 — Attendre ~1 minute** (recalcul du partage), puis tout déployer
```
sf project deploy start --source-dir force-app --target-org voltcare-perso
```

**Étape 3 — Donner l'accès aux champs à l'admin**
```
sf org assign permset --name VoltCare_Admin --target-org voltcare-perso
```

**Étape 4 — Rendre l'app VoltCare visible pour l'admin** (le profil Administrateur n'est pas dans le repo)
Setup → App Manager → VoltCare ▼ → Edit → User Profiles → ajouter **System Administrator** → Save.

**Étape 5 — Charger les données de démo**
```
sf apex run --file scripts/apex/donnees-demo.apex --target-org voltcare-perso
```
Crée le compte « Clients VoltCare », 3 clients (badges `CLI-0001` à `CLI-0003`), 6 stations (`ST-MRK-01/02`, `ST-CAS-01/02`, `ST-RBT-01/02`) et 15 bornes (`MRK/CAS/RBT-001` à `005`). Le technicien des stations est l'utilisateur qui lance le script.
Le script est **idempotent** (upsert sur les External IDs) : on peut le relancer sans doublon, et il remet toutes les bornes à « Disponible » → c'est aussi le script de réinitialisation avant la soutenance.

**Étape 6 — Lancer les tests**
```
sf apex run test --test-level RunLocalTests --target-org voltcare-perso --wait 10 --result-format human
```
Attendu : 4 tests `SecuriteTest` en **Pass**.

---

## 4. Vérifier que tout marche

- [ ] App Launcher → **VoltCare** : onglets Home, Stations, Bornes, Sessions Recharge, Cases, Dashboards
- [ ] Stations : 6 stations
- [ ] Station « Marrakech Guéliz » : en-tête avec Code, Ville, **Technicien**, Nombre de bornes = 3 ; onglet Bornes avec MRK-001 à 003
- [ ] Une borne : page de Hanane avec les onglets Sessions / Tickets
- [ ] Comptages :
  ```
  sf data query --target-org voltcare-perso -q "SELECT COUNT() FROM Station__c WHERE Code_Station__c LIKE 'ST-___-0_'"
  sf data query --target-org voltcare-perso -q "SELECT COUNT() FROM Borne__c"
  ```
  → 6 et 15, même après avoir relancé le script.

---

## 5. Erreurs fréquentes

| Erreur | Cause | Solution |
|---|---|---|
| `Role … Case access level below organization default` | Les rôles sont déployés avant que Case/Contact soient Privés | Suivre les étapes 1 puis 2 (ou Setup → Sharing Settings → Case et Contact = Private) |
| `referenceTo value of 'Borne__c' does not resolve` | Déploiement partiel de Case sans l'objet Borne | Déployer le dossier `objects` en entier (étape 1) |
| Tests : `fields being inaccessible on Sobject Station__c` | L'admin n'a pas de FLS sur les champs déployés | Étape 3 (`VoltCare_Admin`) |
| `Could not find related list [X]` dans une FlexiPage | Il faut le nom de relation avec `__r` | Ex. `Bornes__r`, `Sessions_Recharge__r` |
| `Error (10): fetch failed` | Coupure réseau CLI ↔ Salesforce | Relancer la commande |
| Lightning App Builder : « check your internet connection » | Cache / extension du navigateur | `Ctrl+Shift+R`, fenêtre privée, ou passer par un enregistrement → ⚙ Edit Page |

---

## 6. Règles d'équipe à partir de maintenant

1. **La PR `VC-68-69-station-app-donnees` → `main` se fusionne en « Create a merge commit »**, pas en squash : chacun garde ses commits à son nom, et GitHub marque automatiquement les anciennes PR (VC-29, malika, VC-64/65, VC-62, VC-63, VC-66/67) comme *Merged*.
2. **On ne pousse plus sur les anciennes branches.** Après la fusion : `git checkout main && git pull`, puis une nouvelle branche par ticket : `git checkout -b VC-xx-description`.
3. Un changement fait dans l'org (layout, page, onglet…) doit être **récupéré dans le repo** avant de commit :
   ```
   sf project retrieve start --target-org voltcare-perso --metadata "Layout:Station__c-Station Layout"
   ```
4. Après avoir tiré `main`, redéployer dans son org perso (étape 2) pour rester à jour.
5. Les branches de docs (VC-12 à VC-28, `renommage-maquettes`) ont déjà été fusionnées en squash dans `main` et peuvent être supprimées.

---

## 7. Org de démo (VC-70)

Uniquement par l'intégrateur (Bahae). Étapes 1 à 6 avec `--target-org voltcare-demo`, puis :

**Utilisateurs de démo** (Setup → Users → New User, licence Salesforce, profil **VoltCare Interne**)

| Utilisateur | Username | Rôle | Permission set |
|---|---|---|---|
| Karim Alaoui | `responsable.voltcare@demo-pfs.ma` | Responsable réseau | `VoltCare_Responsable` |
| Youssef Idrissi | `technicien.voltcare@demo-pfs.ma` | Technicien | `VoltCare_Technicien` |

```
sf org assign permset --name VoltCare_Responsable --on-behalf-of responsable.voltcare@demo-pfs.ma --target-org voltcare-demo
sf org assign permset --name VoltCare_Technicien --on-behalf-of technicien.voltcare@demo-pfs.ma --target-org voltcare-demo
sf apex run --file scripts/apex/affecter-technicien-demo.apex --target-org voltcare-demo
```
Le dernier script rattache les 6 stations au technicien de démo (à relancer après chaque `donnees-demo.apex`).

### Ajouts faits pendant VC-70
- Profil `VoltCare Interne` : permission **Lightning Experience User** (sinon les utilisateurs arrivent dans Salesforce Classic)
- `VoltCare_Technicien` / `VoltCare_Responsable` : onglets Station / Borne / Session visibles, lecture sur Session de recharge et sur les champs Station / Borne / Session manquants
- `VoltCare_Admin` : onglets Station / Borne / Session visibles (les onglets déployés par metadata sont masqués pour l'admin)
- Vues de liste **« Tous »** sur Station, Borne et Session (les objets créés par metadata n'ont que « Recently Viewed »)

> Après un changement de permissions ou d'onglets : se **déconnecter / reconnecter**, Lightning garde la barre de navigation en cache.
