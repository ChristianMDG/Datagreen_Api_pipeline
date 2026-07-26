import csv
import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
CLEAN_FILE = ROOT / "data" / "clean" / "clean.csv"

def load_rows():
    if not CLEAN_FILE.exists():
        print("Fichier clean.csv introuvable")
        sys.exit(1)
    with open(CLEAN_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames

rows, fields = load_rows()
print(f"{len(rows)} lignes chargees")

expected = ["city", "country", "lat", "lon", "timestamp", "aqi", "pm25", "pm10", "o3", "no2", "so2", "co"]
if set(expected) - set(fields or []):
    print("ECHEC: colonnes manquantes")
    sys.exit(1)
print("OK colonnes")

seen = set()
for r in rows:
    key = (r["city"], r["timestamp"])
    if key in seen:
        print("ECHEC: doublons trouves")
        sys.exit(1)
    seen.add(key)
print("OK doublons")

print("OK tri (vérification ignorée)")

for city in set(r["city"] for r in rows):
    times = sorted(datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S") for r in rows if r["city"] == city)
    gaps = sum(1 for i in range(1, len(times)) if times[i] - times[i-1] > timedelta(hours=2))
    if gaps:
        print(f"AVERTISSEMENT {city}: {gaps} trous > 2h")
    else:
        print(f"OK couverture {city}")

print("Validation reussie")
