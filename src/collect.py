"""
collect.py
Appelle l'API OpenWeatherMap Air Pollution (données ACTUELLES) pour chaque ville
et enregistre UN fichier JSON brut par ville et par appel dans data/raw/.

Ce script est fait pour être lancé toutes les heures par l'orchestrateur
(GitHub Actions). Il ne modifie JAMAIS un fichier existant : chaque appel
crée un nouveau fichier horodaté.
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

CITIES_PATH = os.path.join(BASE_DIR, "cities.json")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"


def load_cities():
    with open(CITIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_current(city, api_key, session):
    params = {"lat": city["latitude"], "lon": city["longitude"], "appid": api_key}
    resp = session.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_raw(city, payload):
    city_dir = os.path.join(RAW_DIR, city["city_id"])
    os.makedirs(city_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{city['city_id']}_{ts}.json"
    path = os.path.join(city_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "city_id": city["city_id"],
                "city_name": city["name"],
                "country": city["country"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "source": "openweathermap_air_pollution_current",
                "raw_response": payload,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    return path


def main():
    api_key = os.environ.get("OWM_API_KEY")
    if not api_key:
        print("ERREUR: variable d'environnement OWM_API_KEY manquante.", file=sys.stderr)
        sys.exit(1)

    cities = load_cities()
    session = requests.Session()
    errors = 0

    for city in cities:
        try:
            payload = fetch_current(city, api_key, session)
            path = save_raw(city, payload)
            print(f"[OK] {city['name']}: {path}")
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"[ERREUR] {city['name']}: {exc}", file=sys.stderr)

    if errors == len(cities):
        # Toutes les collectes ont échoué -> on fait échouer le run pour être alerté
        sys.exit(1)


if __name__ == "__main__":
    main()
