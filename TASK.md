# Task Allocation — AQI Pipeline

## Overview

| Member | Scope |
|---|---|
| Nomena | API acquisition → `data/raw/` |
| Gaetan | Transformation & validation → `data/clean/` |
| Miarintsoa | Modeling & loading → Neon |
| Mahefa | Orchestration & automation |
| Christian | Coordination, infrastructure, deliverables |

---

## 1. Nomena

**Scope:** acquisition of raw data from the air quality API

**Files under responsibility:**
- `src/collect.py`
- `src/backfill.py`

**Expected deliverables:**
- Hourly collection of current data for the 5 cities
- Replayable historical backfill (configurable number of months)
- One raw JSON file per city and per API call, stored in `data/raw/`

**Acceptance criteria:**
- No modification of `raw/` files after they are written
- Script resilient to API errors (timeout, city unavailable) without interrupting the other cities
- API key handled exclusively via environment variable

**Dependencies:** none — can start as soon as the API key is obtained

---

## 2. Gaetan

**Scope:** transformation of `raw/` into a clean, validated dataset

**Files under responsibility:**
- `src/build_clean.py`
- `src/validate_clean.py`

**Expected deliverables:**
- Full rebuild of `clean.csv` on every run
- Deduplication on the (city, hour) key, chronological sort
- Validation script checking: expected columns, absence of duplicates, sort order, minimum time coverage, AQI value consistency

**Acceptance criteria:**
- `clean.csv` can be regenerated identically from `raw/` alone
- The validation script fails explicitly (non-zero exit code) on non-compliance

**Dependencies:** requires a sample of `raw/` files (real or mock) to develop and test

---

## 3. Miarintsoa

**Scope:** dimensional modeling and loading into Neon

**Files under responsibility:**
- `sql/schema.sql`
- `src/load_warehouse.py`

**Expected deliverables:**
- Star schema: `dim_city`, `dim_time`, `fact_air_quality`
- Idempotent loading script (upsert), no duplication on re-run

**Acceptance criteria:**
- No measures in the dimensions, no descriptive columns in the fact table
- Uniqueness constraint `(city_key, time_key)` on the fact table
- Secure (SSL) connection via `DATABASE_URL`

**Dependencies:** requires a `clean.csv` (real or mock) to develop and test

---

## 4. Mahefa

**Scope:** end-to-end orchestration and automation

**Files under responsibility:**
- `.github/workflows/hourly_collect.yml`
- `.github/workflows/manual_backfill.yml`

**Expected deliverables:**
- Hourly collection workflow (cron)
- Manually triggerable backfill workflow
- Full chain: collect/backfill → transform → validate → load → automatic commit

**Acceptance criteria:**
- Successful runs visible in the Actions tab, across multiple distinct days
- Secrets (`OWM_API_KEY`, `DATABASE_URL`) managed exclusively via GitHub Secrets
- Concurrency handling between workflows (no overlapping runs)

**Dependencies:** requires the scripts from the three preceding roles, at least in a minimally functional version

---

## 5. Christian

**Scope:** overall coordination, shared infrastructure, cross-cutting deliverables

**Files under responsibility:**
- `cities.json`, `requirements.txt`, `.gitignore`, `.env.example`
- `ARCHITECTURE.md`, `README.md`
- Project report, demo video

**Expected deliverables:**
- Complete documentation (architecture, data contract, warehouse schema)
- Provisioning of shared infrastructure (Neon project, GitHub secrets)
- Git coordination (branching structure, Pull Request review)
- Final project report and demo video

**Acceptance criteria:**
- Documentation allowing a third party (e.g. the IA1 course) to consume the data without ambiguity
- Git history reflecting the contribution of all 5 members

**Dependencies:** coordinates the deliverables of the 4 other roles, without blocking their individual progress

---

Want me to also translate the dependency diagram and export this as a downloadable `.md` file?
