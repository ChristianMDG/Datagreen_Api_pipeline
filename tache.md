## 👤 Nomena — Collecte (API → raw/)
**Fichiers :** `src/collect.py`, `src/backfill.py`
- Appel API données courantes + historique, sauvegarde 1 fichier JSON par ville par appel dans `data/raw/`
- Peut commencer tout de suite (juste besoin de la clé API)

## 👤 Gaetan — Transformation & qualité (raw/ → clean/)
**Fichiers :** `src/build_clean.py`, `src/validate_clean.py`
- Parcourt `data/raw/`, extrait chaque point (ville, heure), déduplique, trie, écrit `data/clean/clean.csv`
- Script de validation (colonnes, doublons, tri, couverture temporelle)
- Peut créer 2-3 fichiers JSON factices pour tester sans attendre Nomena

## 👤 Miharintsoa — Data warehouse (clean/ → Neon)
**Fichiers :** `sql/schema.sql`, `src/load_warehouse.py`
- DDL du schéma en étoile (dim_city, dim_time, fact_air_quality)
- Script d'upsert des dimensions puis des faits depuis `clean.csv`
- Peut créer un `clean.csv` factice pour avancer sans attendre Gaetan

## 👤 Mahefa — Orchestrateur / CI-CD
**Fichiers :** `.github/workflows/hourly_collect.yml`, `.github/workflows/manual_backfill.yml`
- Écrit les workflows qui enchaînent collect/backfill → build_clean → validate → load_warehouse → commit & push
- Configure les secrets GitHub, débogue les erreurs CI
- Dépend des 3 autres scripts (même en version basique) pour pouvoir les assembler

## 👤 Christian — le reste
- `cities.json`, `requirements.txt`, `.gitignore`, `.env.example`
- `ARCHITECTURE.md`, `README.md`
- Rapport de projet, vidéo de démo
- Coordination Git (branches, revue des PR), création du projet Neon, secrets GitHub
