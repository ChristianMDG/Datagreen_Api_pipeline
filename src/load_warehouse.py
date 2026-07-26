"""
load_warehouse.py
Charge data/clean/clean.csv dans le data warehouse Postgres (schéma en étoile).
Rejouable : utilise des UPSERT (ON CONFLICT) partout, donc relancer ce
script plusieurs fois ne crée jamais de doublons.

Nécessite la variable d'environnement DATABASE_URL.
"""
import os
import sys

import pandas as pd
import psycopg2
import psycopg2.extras

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH = os.path.join(BASE_DIR, "data", "clean", "clean.csv")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")

DAY_NAMES_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERREUR: variable d'environnement DATABASE_URL manquante.", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(database_url)


def ensure_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def upsert_cities(conn, df):
    cities = df[["city_id", "city_name", "country", "latitude", "longitude"]].drop_duplicates("city_id")
    rows = list(cities.itertuples(index=False, name=None))
    sql = """
        INSERT INTO dim_city (city_id, city_name, country, latitude, longitude)
        VALUES %s
        ON CONFLICT (city_id) DO UPDATE SET
            city_name = EXCLUDED.city_name,
            country = EXCLUDED.country,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT city_id, city_key FROM dim_city")
        return dict(cur.fetchall())


def build_time_rows(df):
    ts = pd.to_datetime(df["timestamp_utc"], utc=True).drop_duplicates().sort_values()
    rows = []
    for t in ts:
        rows.append((
            t.to_pydatetime(),
            t.date(),
            int(t.hour),
            int(t.day),
            int(t.month),
            int(t.year),
            int(t.dayofweek),
            DAY_NAMES_FR[t.dayofweek],
            bool(t.dayofweek >= 5),
        ))
    return rows


def upsert_time(conn, df):
    rows = build_time_rows(df)
    sql = """
        INSERT INTO dim_time
            (timestamp_utc, date, hour, day, month, year, day_of_week, day_name, is_weekend)
        VALUES %s
        ON CONFLICT (timestamp_utc) DO NOTHING
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT timestamp_utc, time_key FROM dim_time")
        return {ts.isoformat(): key for ts, key in cur.fetchall()}


def upsert_facts(conn, df, city_key_map, time_key_map):
    pollutants = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]
    rows = []
    for row in df.itertuples(index=False):
        city_key = city_key_map[row.city_id]
        ts_key_lookup = row.timestamp_utc.isoformat()
        time_key = time_key_map.get(ts_key_lookup)
        if time_key is None:
            continue
        values = [getattr(row, p) for p in pollutants]
        values = [None if pd.isna(v) else v for v in values]
        aqi_val = None if pd.isna(row.aqi) else int(row.aqi)
        rows.append((city_key, time_key, aqi_val, *values))

    sql = """
        INSERT INTO fact_air_quality
            (city_key, time_key, aqi, co, no, no2, o3, so2, pm2_5, pm10, nh3)
        VALUES %s
        ON CONFLICT (city_key, time_key) DO UPDATE SET
            aqi = EXCLUDED.aqi,
            co = EXCLUDED.co, no = EXCLUDED.no, no2 = EXCLUDED.no2,
            o3 = EXCLUDED.o3, so2 = EXCLUDED.so2,
            pm2_5 = EXCLUDED.pm2_5, pm10 = EXCLUDED.pm10, nh3 = EXCLUDED.nh3
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def main():
    if not os.path.exists(CLEAN_PATH):
        print(f"ERREUR: {CLEAN_PATH} introuvable. Lancez build_clean.py d'abord.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(CLEAN_PATH, parse_dates=["timestamp_utc"])
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)

    conn = get_connection()
    try:
        ensure_schema(conn)
        city_key_map = upsert_cities(conn, df)
        time_key_map = upsert_time(conn, df)
        n = upsert_facts(conn, df, city_key_map, time_key_map)
        print(f"Warehouse chargé: {n} lignes upsertées dans fact_air_quality.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()