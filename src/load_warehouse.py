import csv
import os
import sys
import psycopg2
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
CLEAN_FILE = ROOT / "data" / "clean" / "clean.csv"

def load_warehouse():
    print("Connexion à PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=os.getenv("PG_PORT", "5432"),
            database=os.getenv("PG_DATABASE", "postgres"),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASSWORD", "")
        )
        cur = conn.cursor()
        print("✅ Connecté à PostgreSQL")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        sys.exit(1)

    print("Création des tables...")
    with open("sql/schema.sql", "r") as f:
        cur.execute(f.read())
    conn.commit()
    print("✅ Tables créées")

    if not CLEAN_FILE.exists():
        print(f"❌ Fichier {CLEAN_FILE} introuvable")
        sys.exit(1)

    print("Chargement des données...")
    with open(CLEAN_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cur.execute("""
                INSERT INTO dim_city (city, country)
                VALUES (%s, %s)
                ON CONFLICT (city) DO NOTHING
            """, (row["city"], row["country"]))

            cur.execute("SELECT city_id FROM dim_city WHERE city = %s", (row["city"],))
            city_id = cur.fetchone()[0]

            dt = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO dim_time (timestamp, hour, day, month, year, weekday)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO NOTHING
            """, (dt, dt.hour, dt.day, dt.month, dt.year, dt.weekday()))

            cur.execute("SELECT time_id FROM dim_time WHERE timestamp = %s", (dt,))
            time_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO fact_air_quality (city_id, time_id, aqi, pm25, pm10, o3, no2, so2, co)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (city_id, time_id, row["aqi"], row["pm25"], row["pm10"],
                  row["o3"], row["no2"], row["so2"], row["co"]))
            count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ {count} lignes chargées dans PostgreSQL")

if __name__ == "__main__":
    load_warehouse()
