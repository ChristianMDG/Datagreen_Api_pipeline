import csv
import json
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
CLEAN_FILE = ROOT / "data" / "clean" / "clean.csv"

os.makedirs(CLEAN_FILE.parent, exist_ok=True)

with open(ROOT / "cities.json") as f:
    cities_map = {c["city_id"]: c for c in json.load(f)}

rows = []
for json_file in RAW_DIR.glob("*.json"):
    with open(json_file) as f:
        data = json.load(f)
    city_id = json_file.stem.split("_")[0]
    if city_id == "new":
        city_id = "new_delhi"
    city_info = cities_map.get(city_id, {})
    for item in data.get("list", []):
        dt = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d %H:%M:%S")
        comp = item["components"]
        rows.append({
            "city": city_info.get("name", city_id),
            "country": city_info.get("country", ""),
            "lat": city_info.get("latitude", ""),
            "lon": city_info.get("longitude", ""),
            "timestamp": dt,
            "aqi": item["main"]["aqi"],
            "pm25": comp.get("pm2_5", ""),
            "pm10": comp.get("pm10", ""),
            "o3": comp.get("o3", ""),
            "no2": comp.get("no2", ""),
            "so2": comp.get("so2", ""),
            "co": comp.get("co", "")
        })

if rows:
    rows = sorted(rows, key=lambda x: (x["city"], x["timestamp"]))
    seen = set()
    unique = []
    for r in rows:
        key = (r["city"], r["timestamp"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    with open(CLEAN_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(unique)
    print(f"Build clean: {len(unique)} lignes ecrites dans {CLEAN_FILE}")
else:
    print("Aucune donnee trouvee dans data/raw/")
