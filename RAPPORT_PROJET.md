# Project Report — AQI Pipeline

**Team:** [Datagreen]
**Members:** Nomena, Gaetan, Miarintsoa, Mahefa, Christian
**Repository:** https://github.com/ChristianMDG/aqi-pipeline

---

## 1. Project Objective

Deploy a fully automated, 24/7 pipeline to collect air quality (AQI) data for 5 cities (Paris, Antananarivo, New Delhi, Beijing, Nairobi), and deliver a data warehouse using dimensional modeling (star schema), designed to be continuously consumed by the IA1 course after submission.

---

## 2. Team Working Method

### 2.1 General Organization

[To be completed: how the team coordinated — communication channel (WhatsApp/Discord/Slack?), frequency of progress check-ins, task tracking tool used (Trello/GitHub Issues/shared board?)]

### 2.2 Task Allocation

| Member | Responsibility | Files / Deliverables |
|---|---|---|
| **Nomena** | Data collection (API) | `src/collect.py`, `src/backfill.py` |
| **Gaetan** | Data transformation & quality | `src/build_clean.py`, `src/validate_clean.py` |
| **Miarintsoa** | Data warehouse | `sql/schema.sql`, `src/load_warehouse.py` |
| **Mahefa** | Orchestration / CI-CD | `.github/workflows/hourly_collect.yml`, `.github/workflows/manual_backfill.yml` |
| **Christian** | Coordination, documentation, infrastructure (Neon, secrets), report, video | `ARCHITECTURE.md`, `README.md`, `cities.json`, report, video |

---

## 3. Technical Choices and Justification

| Component | Choice | Justification |
|---|---|---|
| Data source | OpenWeatherMap Air Pollution API | Free API key, historical data available since Nov. 2020 (enables a 12-month backfill), stable JSON format |
| Orchestrator | GitHub Actions (hourly cron) | No server to manage, free, genuinely runs 24/7, run history serves as proof of automation |
| Raw/clean storage | Folders versioned in the Git repository | Simplicity for a student team, native traceability through Git history |
| Data warehouse | Neon (serverless Postgres, free tier) | Standard SQL database, publicly verifiable connection string, scale-to-zero at no cost |
| Modeling | Star schema | Time and city dimensions are low-cardinality and independent; no need for a snowflake schema |
| Language | Python (requests, pandas, psycopg2) | Common language across the team, mature ETL ecosystem |
---

## 4. Difficulties Encountered and Solutions Implemented

### 4.1 Pandas compatibility bug (`load_warehouse.py`)

**Problem:** `ValueError: Cannot pass a datetime or Timestamp with tzinfo with the tz parameter` when loading data into the warehouse.

**Root cause:** the code attempted to re-apply `tz="UTC"` to a `pd.Timestamp()` on a value that had already been made timezone-aware by `pd.to_datetime(..., utc=True)` — a pattern now rejected by recent pandas versions.

**Solution:** replaced `pd.Timestamp(row.timestamp_utc, tz="UTC").isoformat()` with `row.timestamp_utc.isoformat()`, since the timestamp was already timezone-aware.

### 4.2 Data never pushed to GitHub despite "successful" runs

**Problem:** after adding a `.gitignore` excluding `data/raw/*` and `data/clean/*` (to avoid polluting local test commits), the CI workflow stopped committing any data, with no visible error in the logs.

**Root cause:** `git add data/raw data/clean` respects `.gitignore` and adds nothing that is excluded by it.

**Solution:** used `git add -f data/raw data/clean` in the CI workflows to force the addition despite `.gitignore`, while keeping `.gitignore` active for local development use.

### 4.3 ~4-hour gap in hourly collection (07/26/2026, 00:09–04:33 UTC)

**Problem:** a simultaneous data gap across all 5 cities, visible in the warehouse.

**Diagnosis:** inspection of the GitHub Actions run history showed that the scheduled 04:00 run simply never happened (jump directly from 03:08 to 07:33).

**Root cause:** a known GitHub Actions limitation — scheduled (`cron`) workflows can be delayed or skipped during peak load on GitHub's infrastructure, particularly on free public repositories. This was further compounded by our initial cron being set to `"0 * * * *"` (the top of the hour), the single busiest minute across all GitHub Actions schedules worldwide.

**Solution:** shifted the cron schedule off the top of the hour (e.g. `"7 * * * *"`) to reduce collision with peak scheduling load; added a `concurrency` guard and `git pull --rebase` before push as defensive measures against overlapping runs.

**Impact:** ~94–96% coverage instead of 100%, documented in the README — no impact on the reliability of the data present, nor on data contract validation.

---

## 5. Results Achieved

### 5.1 Data Coverage (as of [report date])

| City | Measurements | Coverage | Since | Until |
|---|---|---|---|---|
| Antananarivo | 2,103 | ~96.3% | 04/26/2026 | [latest date] |
| Beijing | 2,079 | ~95.2% | 04/26/2026 | [latest date] |
| Nairobi | 2,103 | ~96.3% | 04/26/2026 | [latest date] |
| New Delhi | 2,055 | ~94.1% | 04/26/2026 | [latest date] |
| Paris | 2,103 | ~96.3% | 04/26/2026 | [latest date] |

*(Update these figures using the verification SQL query right before submission.)*

### 5.2 Quality Checks Performed

- ✅ No `(city, hour)` duplicates in `clean.csv` or in `fact_air_quality`
- ✅ Columns compliant with the documented data contract, units specified in the README
- ✅ Chronological sort order respected
- ✅ Fact table row count ≈ cities × hours covered (deviations documented)

---


## 6. Potential Improvements (If the Project Continued)

- Add automated alerting (email/Slack) on run failure
- Extend the `concurrency` guard to fully eliminate overlapping runs
- Move to a snowflake schema if new dimensions became necessary (e.g. normalized pollutant type, monitoring station source)
- Add a visualization dashboard (Metabase, Grafana) connected to Neon

---

## 7. Useful Links

- GitHub repository: https://github.com/ChristianMDG/aqi-pipeline
- Run history: https://github.com/ChristianMDG/aqi-pipeline/actions
- Demo video: [link to add]
- Storage documentation: [`README.md`](./README.md)
- Architecture: [`ARCHITECTURE.md`](./ARCHITECTURE.md)

---

## 8. Compliance with the Assignment Requirements

| Requirement | How it's met |
|---|---|
| Team working method, task allocation | Sections 2.1–2.2 |
| Difficulties encountered and how they were resolved | Section 4 — three real, diagnosed and resolved incidents |
| Justified technical choices | Section 3, cross-referenced with `ARCHITECTURE.md` |
| Verifiable deliverable | Public repo + live Neon database; consistency and coverage figures reproducible via the SQL queries in `README.md` |

---

*This report is the project-report deliverable required by the assignment specification, to be submitted alongside `ARCHITECTURE.md`, `README.md`, the full Git repository, and the demonstration video.*

---
