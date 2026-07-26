# ARCHITECTURE.md

## Overview

```
OpenWeatherMap Air Pollution API (5 cities)
        │  hourly collection (collect.py) + backfill (backfill.py)
        ▼
GitHub Actions (hourly cron, 24/7)
        ▼
data/raw/<city>/*.json          (1 file per city and per API call, never modified)
        │  build_clean.py (full rebuild, deduplication)
        ▼
data/clean/clean.csv             (1 single file, all cities, sorted, no duplicates)
        │  load_warehouse.py (upsert)
        ▼
Neon Postgres — star schema
  fact_air_quality ── dim_city
                   └── dim_time
```

## Technical Choices and Rationale

| Component | Choice | Rationale |
|---|---|---|
| **Data source** | OpenWeatherMap Air Pollution API | Free API key, covers all 5 of our cities, `history` endpoint available since Nov. 2020 (enables a 12-month backfill), stable and well-documented JSON format. |
| **Orchestrator** | GitHub Actions (hourly `cron`) | Already hosted alongside our repository, no server to pay for or maintain, genuinely runs 24/7 even when no one is watching, and the run history directly serves as proof of execution. |
| **Raw/clean storage** | `data/raw/` and `data/clean/` folders, version-controlled in the Git repo, committed automatically by the workflow | Maximum simplicity for a student team (no extra cloud account to manage or share), native traceability through Git history, publicly accessible for grading. |
| **Data warehouse** | Neon (serverless Postgres, free tier) | Standard SQL database (compatible with everything covered in class), publicly connectable and verifiable by a grader or by the IA1 course, built-in web SQL Editor, scale-to-zero so no cost between collection runs. |
| **Modeling** | Star schema (1 fact table + 2 dimensions) | Both dimensions (time, city) are independent and low-cardinality relative to the facts: no need for a snowflake schema — a star is sufficient and simpler to query. |
| **Language** | Python (requests, pandas, psycopg2) | Common language across the team, mature ecosystem for ETL work, `pandas` is convenient for deduplication and sorting. |

## Why This Stack Is the Easiest to Deploy

- **Zero infrastructure to administer**: no VM, no Docker, no system cron to maintain on a personal machine.
- **Centralized secrets**: `OWM_API_KEY` and `DATABASE_URL` live only in *GitHub Settings → Secrets and variables → Actions*, never in the code.
- **Free**: GitHub Actions (2,000 free minutes/month for a public repo), Neon (free tier up to 0.5 GB of storage, comfortably enough for this data volume).
- **Verifiable**: anyone with Neon credentials can connect (web SQL Editor or `psql`) and run a query; the GitHub Actions history shows past runs with timestamps.

## Continuity After Submission

The `hourly_collect.yml` workflow remains active for as long as the GitHub repository exists and the account has remaining Actions quota. No manual action is required for the collection to keep running.

## Compliance with the Assignment Requirements

This architecture satisfies every constraint set by the assignment:

| Requirement | How it's met |
|---|---|
| API for ≥ 5 cities, hourly collection + backfill (12mo ideal, 3mo min) | 5 cities configured in `cities.json`; `collect.py` runs hourly; `backfill.py` supports a configurable `--months` (12 used) |
| API key kept as a secret, never in code or Git history | `OWM_API_KEY` stored exclusively in GitHub Actions Secrets |
| `raw/` never modified; `clean/` fully rebuildable from `raw/` | `build_clean.py` only reads `raw/` and fully regenerates `clean.csv` on every run |
| `clean/` rebuilt each run (or appended with deduplication) | Full rebuild each run, with deduplication on `(city_id, timestamp_utc)` |
| No-code orchestrator → exported workflow versioned in repo | Not applicable here: our orchestrator (GitHub Actions) is itself code-based and versioned directly in `.github/workflows/` |
| Fact table + dimensions; no measures in dimensions; no descriptive columns in facts | Enforced in `sql/schema.sql` and verified in `load_warehouse.py` |
| Verifiable deliverable (no private storage, no dead links, responsive database) | Public GitHub repo + Neon database reachable via a shared connection string |
