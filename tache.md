# Répartition des responsabilités — Pipeline AQI

## Vue d'ensemble

| Membre | Périmètre |
|---|---|---|
| Nomena | Acquisition API → `data/raw/` |
| Gaetan | Transformation & validation → `data/clean/` |
| Miarintsoa | Modélisation & chargement → Neon |
| Mahefa | Orchestration & automatisation |
| Christian | Coordination, infrastructure, livrables |

---

## 1. Nomena 

**Périmètre :** acquisition des données brutes depuis l'API de qualité de l'air

**Fichiers sous responsabilité :**
- `src/collect.py`
- `src/backfill.py`

**Livrables attendus :**
- Collecte horaire des données courantes pour les 5 villes
- Backfill historique rejouable (paramétrable en nombre de mois)
- Un fichier JSON brut par ville et par appel API, stocké dans `data/raw/`

**Critères d'acceptation :**
- Aucune modification des fichiers `raw/` après écriture
- Script résilient aux erreurs API (timeout, ville indisponible) sans interrompre les autres villes
- Gestion de la clé API exclusivement via variable d'environnement

**Dépendances :** aucune — peut démarrer dès l'obtention de la clé API

---

## 2. Gaetan

**Périmètre :** transformation de `raw/` vers un jeu de données propre et validé

**Fichiers sous responsabilité :**
- `src/build_clean.py`
- `src/validate_clean.py`

**Livrables attendus :**
- Reconstruction complète de `clean.csv` à chaque exécution
- Déduplication sur la clé (ville, heure), tri chronologique
- Script de validation vérifiant : colonnes attendues, absence de doublons, tri, couverture temporelle minimale, cohérence des valeurs AQI

**Critères d'acceptation :**
- `clean.csv` régénérable à l'identique à partir de `raw/` uniquement
- Le script de validation échoue explicitement (code de sortie non nul) en cas de non-conformité

**Dépendances :** nécessite un échantillon de fichiers `raw/` (réels ou factices) pour développer et tester

---

## 3. Miarintsoa 

**Périmètre :** modélisation dimensionnelle et chargement dans Neon

**Fichiers sous responsabilité :**
- `sql/schema.sql`
- `src/load_warehouse.py`

**Livrables attendus :**
- Schéma en étoile : `dim_city`, `dim_time`, `fact_air_quality`
- Script de chargement idempotent (upsert), sans duplication en cas de réexécution

**Critères d'acceptation :**
- Aucune mesure dans les dimensions, aucune colonne descriptive dans les faits
- Contrainte d'unicité `(city_key, time_key)` sur la table de faits
- Connexion sécurisée (SSL) via `DATABASE_URL`

**Dépendances :** nécessite un `clean.csv` (réel ou factice) pour développer et tester

---

## 4. Mahefa

**Périmètre :** orchestration et automatisation de bout en bout

**Fichiers sous responsabilité :**
- `.github/workflows/hourly_collect.yml`
- `.github/workflows/manual_backfill.yml`

**Livrables attendus :**
- Workflow de collecte horaire (cron)
- Workflow de backfill déclenchable manuellement
- Enchaînement complet : collecte/backfill → transformation → validation → chargement → commit automatique

**Critères d'acceptation :**
- Runs visibles et réussis dans l'onglet Actions, sur plusieurs jours distincts
- Secrets (`OWM_API_KEY`, `DATABASE_URL`) exclusivement gérés via GitHub Secrets
- Gestion de la concurrence entre workflows (pas d'exécutions qui se chevauchent)

**Dépendances :** nécessite les scripts des trois rôles précédents, au moins dans une version fonctionnelle minimale

---

## 5. Christian

**Périmètre :** coordination générale, infrastructure partagée, livrables transverses

**Fichiers sous responsabilité :**
- `cities.json`, `requirements.txt`, `.gitignore`, `.env.example`
- `ARCHITECTURE.md`, `README.md`
- Rapport de projet, vidéo de démonstration

**Livrables attendus :**
- Documentation complète (architecture, contrat de données, schéma warehouse)
- Provisioning de l'infrastructure partagée (projet Neon, secrets GitHub)
- Coordination Git (structure de branches, revue des Pull Requests)
- Rapport de projet et vidéo de démonstration finale

**Critères d'acceptation :**
- Documentation permettant à un tiers (ex. IA1) de consommer les données sans ambiguïté
- Historique Git reflétant la contribution des 5 membres

**Dépendances :** coordonne les livrables des 4 autres rôles, sans bloquer leur avancement individuel

---
