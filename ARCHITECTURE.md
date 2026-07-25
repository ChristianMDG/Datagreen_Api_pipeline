# ARCHITECTURE.md

## Vue d'ensemble

```
OpenWeatherMap Air Pollution API (5 villes)
        │  collecte horaire (collect.py) + backfill (backfill.py)
        ▼
GitHub Actions (cron horaire, 24h/24)
        ▼
data/raw/<ville>/*.json        (1 fichier par ville et par appel, jamais modifié)
        │  build_clean.py (reconstruction complète, dédup)
        ▼
data/clean/clean.csv           (1 fichier unique, toutes villes, trié, sans doublons)
        │  load_warehouse.py (upsert)
        ▼
Supabase Postgres — schéma en étoile
  fact_air_quality ── dim_city
                   └── dim_time
```

## Choix techniques et justification

| Composant | Choix | Justification |
|---|---|---|
| **API source** | OpenWeatherMap Air Pollution API | Clé gratuite, couvre nos 5 villes, endpoint `history` disponible depuis nov. 2020 (permet un backfill de 12 mois), format JSON stable et documenté. |
| **Orchestrateur** | GitHub Actions (`cron` horaire) | Déjà hébergé avec notre repo, aucun serveur à payer/maintenir, tourne réellement 24h/24 y compris quand personne n'est devant l'écran, l'historique des runs sert directement de preuve d'exécution. |
| **Stockage raw/clean** | Dossiers `data/raw/` et `data/clean/` versionnés dans le repo Git, committés automatiquement par le workflow | Simplicité maximale pour un groupe étudiant (pas de compte cloud supplémentaire à gérer/partager), traçabilité native via l'historique Git, accessible publiquement pour la correction. |
| **Data warehouse** | Neon (Postgres serverless, offre gratuite) | Base SQL standard (compatible avec tout ce qui a été vu en cours), URL de connexion publique et vérifiable par un correcteur ou par IA1, SQL Editor web inclus, scale-to-zero donc aucun coût entre deux collectes. |
| **Modélisation** | Schéma en étoile (1 table de faits + 2 dimensions) | Les deux dimensions (temps, ville) sont indépendantes et à faible cardinalité par rapport aux faits : pas besoin de flocon, l'étoile suffit et reste plus simple à interroger. |
| **Langage** | Python (requests, pandas, psycopg2) | Langage commun à tout le groupe, écosystème mature pour l'ETL, bibliothèque `pandas` pratique pour la déduplication et le tri. |

## Pourquoi ce stack est le plus facile à déployer

- **Zéro infrastructure à administrer** : ni VM, ni Docker, ni cron système à maintenir sur une machine perso.
- **Secrets centralisés** : `OWM_API_KEY` et `DATABASE_URL` vivent uniquement dans *GitHub Settings → Secrets and variables → Actions*, jamais dans le code.
- **Gratuit** : GitHub Actions (2000 min/mois gratuites pour un repo public), Neon (offre gratuite jusqu'à 0,5 Go de stockage, largement suffisant pour ce volume de données).
- **Vérifiable** : n'importe qui avec les identifiants Neon peut se connecter (SQL Editor web ou `psql`) et lancer une requête SQL ; l'historique des Actions GitHub montre les runs passés avec horodatage.

## Continuité après le rendu

Le workflow `hourly_collect.yml` reste actif tant que le repo GitHub existe et que le compte a du quota Actions restant. Aucune action manuelle n'est nécessaire pour que la collecte continue.
