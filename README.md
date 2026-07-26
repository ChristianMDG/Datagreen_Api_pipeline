# AQI Pipeline — Data Warehouse

An automated 24/7 data pipeline collecting air quality (AQI) measurements for 5 cities, feeding a dimensionally modeled data warehouse (star schema).

See also [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full rationale behind our technical choices.

## 1. Cities Tracked

| city_id | City | Country | Latitude | Longitude |
|---|---|---|---|---|
| paris | Paris | FR | 48.8566 | 2.3522 |
| antananarivo | Antananarivo | MG | -18.8792 | 47.5079 |
| new_delhi | New Delhi | IN | 28.6139 | 77.2090 |
| beijing | Beijing | CN | 39.9042 | 116.4074 |
| nairobi | Nairobi | KE | -1.2921 | 36.8219 |

(Configurable in `cities.json`.)

## 2. Data Source

**API:** [OpenWeatherMap Air Pollution API](https://openweathermap.org/api/air-pollution)
- Current endpoint: `/data/2.5/air_pollution`
- Historical endpoint: `/data/2.5/air_pollution/history` (available since Nov 27, 2020)

The **AQI** index provided by this API follows OpenWeatherMap's own scale, from **1 (Good)** to **5 (Very Poor)** — this is **not** the US EPA 0–500 scale. This distinction is documented here to remove any ambiguity for downstream consumers (IA1 course).

## 3. Data Contract — `data/clean/clean.csv`

One row = one city, one hour. Sorted by `city_id` then `timestamp_utc`, no duplicates.

| Column | Type | Unit / Scale | Description |
|---|---|---|---|
| `city_id` | string | — | technical city identifier |
| `city_name` | string | — | human-readable name |
| `country` | string | 2-letter ISO code | country |
| `latitude` | float | decimal degrees | |
| `longitude` | float | decimal degrees | |
| `timestamp_utc` | ISO 8601 (UTC) | — | measurement timestamp, rounded to the hour |
| `aqi` | int | 1 to 5 (OpenWeatherMap scale) | air quality index |
| `co` | float | µg/m³ | carbon monoxide |
| `no` | float | µg/m³ | nitrogen monoxide |
| `no2` | float | µg/m³ | nitrogen dioxide |
| `o3` | float | µg/m³ | ozone |
| `so2` | float | µg/m³ | sulphur dioxide |
| `pm2_5` | float | µg/m³ | fine particulate matter ≤ 2.5 µm |
| `pm10` | float | µg/m³ | fine particulate matter ≤ 10 µm |
| `nh3` | float | µg/m³ | ammonia |

## 4. The `raw/` Zone

`data/raw/<city_id>/<city_id>_<timestamp>.json` — one file per city and per API call, never modified after being written. Each file contains the raw API response plus collection metadata. This is the single source of truth: `clean/` can be regenerated at any time with:

```bash
python src/build_clean.py
python src/validate_clean.py
```

## 5. Data Warehouse Schema (Star)

```
                    dim_city
                    ─────────
                    city_key (PK)
                    city_id
                    city_name
                    country
                    latitude
                    longitude
                        │
                        │ 1
                        │
                        ▼ N
                 fact_air_quality              N ▲
                 ──────────────────               │ 1
                 fact_id (PK)                      │
                 city_key (FK)  ─────────────────► │
                 time_key (FK)  ─────────────────► dim_time
                 aqi                               ─────────
                 co, no, no2, o3, so2               time_key (PK)
                 pm2_5, pm10, nh3                   timestamp_utc
                                                     date, hour
                                                     day, month, year
                                                     day_of_week, day_name
                                                     is_weekend
```

See [`sql/schema.sql`](./sql/schema.sql) for the full DDL.

Modeling rules enforced:
- no measures (aqi, pollutants) in the dimension tables;
- no descriptive columns (city name, day name...) in the fact table — foreign keys and measures only.

## 6. Coverage Period / Known Gaps

Backfill (12 months requested) + hourly collection, covering **April 26, 2026 to July 26, 2026** (~91 days, 2,184 hours) at time of writing, for all 5 cities.

| City | Measurements | Coverage |
|---|---|---|
| Antananarivo | 2,103 | 96.3% |
| Beijing | 2,079 | 95.2% |
| Nairobi | 2,103 | 96.3% |
| New Delhi | 2,055 | 94.1% |
| Paris | 2,103 | 96.3% |

Gaps (~4–6%) are due to intermittent upstream API gaps (offline monitoring stations, rate limits during backfill) and a known GitHub Actions limitation whereby scheduled (`cron`) workflows can be delayed or skipped during peak platform load. One such gap (~4h20) was observed on July 26, 2026 between 00:09 and 04:33 UTC across all cities simultaneously; the pipeline resumed normal operation automatically at the next run, with no data corruption. See `RAPPORT_PROJET.md`, difficulties section, for the full root-cause analysis.

Expected consistency check: `fact_air_quality rows ≈ number_of_cities × number_of_hours_covered`. Any material deviation is documented above.

## 7. Database Connection (Neon)

- **Provider:** [Neon](https://neon.tech) — serverless Postgres
- Connection string: **to be filled in by the team** (Neon Console → your project → Connect → Connection string)
- Format: `postgresql://<user>:<password>@<host>.neon.tech/<database>?sslmode=require`
- The warehouse can be queried via the Neon Console **SQL Editor**, via `psql`, or through a dedicated read-only account provided to the grader / to the IA1 course.

Example verification query:

```sql
SELECT c.city_name, COUNT(*) AS measurement_count,
       MIN(t.timestamp_utc) AS since, MAX(t.timestamp_utc) AS until
FROM fact_air_quality f
JOIN dim_city c ON c.city_key = f.city_key
JOIN dim_time t ON t.time_key = f.time_key
GROUP BY c.city_name
ORDER BY c.city_name;
```

Duplicate check (should always return zero rows):

```sql
SELECT city_key, time_key, COUNT(*)
FROM fact_air_quality
GROUP BY city_key, time_key
HAVING COUNT(*) > 1;
```

## 8. Local Setup / Execution

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in OWM_API_KEY and DATABASE_URL
export $(cat .env | xargs)

# Initial backfill (3 to 12 months)
python src/backfill.py --months 12

# Rebuild clean.csv and validate
python src/build_clean.py
python src/validate_clean.py

# Load the warehouse
python src/load_warehouse.py

# One-off collection (same as the hourly cron)
python src/collect.py
```

## 9. Automated Deployment (Production)

1. Create a [Neon](https://neon.tech) project (free tier) → retrieve `DATABASE_URL` (Connect → Connection string, including `?sslmode=require`).
2. Create an API key at [openweathermap.org](https://openweathermap.org/api/air-pollution).
3. In the GitHub repo: **Settings → Secrets and variables → Actions**, add:
   - `OWM_API_KEY`
   - `DATABASE_URL`
4. Manually trigger the **Manual AQI Backfill** workflow (Actions tab) to populate the initial historical dataset.
5. The **Hourly AQI Collection** workflow then runs automatically, every hour, 24/7.
6. Check the repo's **Actions** tab to view the run history (proof of automation).

---

*This document constitutes the storage-layer deliverable required by the project specification: cities tracked, data contract for `clean/`, warehouse schema, coverage period, known gaps, and database connection details.*
