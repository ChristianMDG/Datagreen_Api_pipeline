"""
build_clean.py
Reconstruit ENTIEREMENT data/clean/clean.csv à partir de data/raw/.
Ne lit et ne modifie jamais raw/ autrement qu'en lecture.

Règle: une ligne par (ville, heure), triée chronologiquement, sans doublons.
En cas de doublon (même ville + même heure présente dans plusieurs fichiers
raw, ex: collecte horaire ET backfill qui se chevauchent), on garde
l'enregistrement le plus récemment collecté (collected_at_utc le plus grand).
"""
import glob
import json
import os
from datetime import datetime, timezone

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
CLEAN_PATH = os.path.join(CLEAN_DIR, "clean.csv")

POLLUTANT_KEYS = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]


def parse_raw_file(path):
    """Retourne une liste de dict (une ligne par point horaire) depuis un fichier raw."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    city_id = doc["city_id"]
    city_name = doc["city_name"]
    country = doc["country"]
    lat = doc["latitude"]
    lon = doc["longitude"]
    collected_at = doc["collected_at_utc"]

    rows = []
    for point in doc.get("raw_response", {}).get("list", []):
        ts = point.get("dt")
        if ts is None:
            continue
        row = {
            "city_id": city_id,
            "city_name": city_name,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "timestamp_utc": datetime.fromtimestamp(ts, tz=timezone.utc),
            "aqi": point.get("main", {}).get("aqi"),
            "collected_at_utc": collected_at,
        }
        components = point.get("components", {})
        for key in POLLUTANT_KEYS:
            row[key] = components.get(key)
        rows.append(row)
    return rows


def main():
    os.makedirs(CLEAN_DIR, exist_ok=True)
    files = glob.glob(os.path.join(RAW_DIR, "**", "*.json"), recursive=True)
    print(f"{len(files)} fichiers raw trouvés.")

    all_rows = []
    for path in files:
        try:
            all_rows.extend(parse_raw_file(path))
        except Exception as exc:  # noqa: BLE001
            print(f"[SKIP] {path}: {exc}")

    if not all_rows:
        print("Aucune donnée trouvée dans raw/. Rien à écrire.")
        return

    df = pd.DataFrame(all_rows)

    # Déduplication (ville, heure) : on garde la collecte la plus récente
    df["collected_at_utc"] = pd.to_datetime(df["collected_at_utc"])
    df = df.sort_values("collected_at_utc")
    df = df.drop_duplicates(subset=["city_id", "timestamp_utc"], keep="last")

    # Tri chronologique final, colonnes ordonnées, drop colonne technique
    df = df.drop(columns=["collected_at_utc"])
    df = df.sort_values(["city_id", "timestamp_utc"]).reset_index(drop=True)

    ordered_cols = [
        "city_id", "city_name", "country", "latitude", "longitude",
        "timestamp_utc", "aqi",
    ] + POLLUTANT_KEYS
    df = df[ordered_cols]

    df.to_csv(CLEAN_PATH, index=False, date_format="%Y-%m-%dT%H:%M:%SZ")
    print(f"clean.csv écrit: {CLEAN_PATH} ({len(df)} lignes, {df['city_id'].nunique()} villes)")


if __name__ == "__main__":
    main()
