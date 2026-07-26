"""
backfill.py
Récupère l'historique de qualité de l'air pour chaque ville depuis l'API
OpenWeatherMap Air Pollution History et enregistre UN fichier JSON brut
par ville et par appel dans data/raw/.

Rejouable : relancer ce script ne casse rien, il crée simplement de
nouveaux fichiers raw (la déduplication se fait plus tard, dans
build_clean.py, jamais dans raw/).

Usage:
    python src/backfill.py --months 3
    python src/backfill.py --months 12 --chunk-days 7
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITIES_PATH = os.path.join(BASE_DIR, "cities.json")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

API_URL = "http://api.openweathermap.org/data/2.5/air_pollution/history"

# L'historique OpenWeatherMap n'est disponible qu'à partir du 27/11/2020
EARLIEST_AVAILABLE = datetime(2020, 11, 27, tzinfo=timezone.utc)


def load_cities():
    with open(CITIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_history(city, start, end, api_key, session):
    params = {
        "lat": city["latitude"],
        "lon": city["longitude"],
        "start": int(start.timestamp()),
        "end": int(end.timestamp()),
        "appid": api_key,
    }
    resp = session.get(API_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def save_raw(city, payload, start, end):
    city_dir = os.path.join(RAW_DIR, city["city_id"])
    os.makedirs(city_dir, exist_ok=True)
    fname = (
        f"{city['city_id']}_history_"
        f"{start.strftime('%Y%m%dT%H%MZ')}_{end.strftime('%Y%m%dT%H%MZ')}.json"
    )
    path = os.path.join(city_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "city_id": city["city_id"],
                "city_name": city["name"],
                "country": city["country"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "source": "openweathermap_air_pollution_history",
                "requested_start_utc": start.isoformat(),
                "requested_end_utc": end.isoformat(),
                "raw_response": payload,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    return path


def daterange_chunks(start, end, chunk_days):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=chunk_days), end)
        yield cur, nxt
        cur = nxt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=3, help="Nombre de mois à backfiller (3 min, 12 idéal)")
    parser.add_argument("--chunk-days", type=int, default=7, help="Taille des tranches par appel API")
    parser.add_argument("--sleep", type=float, default=1.0, help="Pause entre appels (secondes) pour respecter le rate limit")
    args = parser.parse_args()

    api_key = os.environ.get("OWM_API_KEY")
    if not api_key:
        print("ERREUR: variable d'environnement OWM_API_KEY manquante.", file=sys.stderr)
        sys.exit(1)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.months * 30)
    start = max(start, EARLIEST_AVAILABLE)

    cities = load_cities()
    session = requests.Session()
    total_calls = 0
    total_errors = 0

    for city in cities:
        print(f"=== Backfill {city['name']} : {start.date()} -> {end.date()} ===")
        for chunk_start, chunk_end in daterange_chunks(start, end, args.chunk_days):
            try:
                payload = fetch_history(city, chunk_start, chunk_end, api_key, session)
                path = save_raw(city, payload, chunk_start, chunk_end)
                n = len(payload.get("list", []))
                print(f"  [OK] {chunk_start.date()} -> {chunk_end.date()} ({n} points) -> {path}")
                total_calls += 1
            except Exception as exc:  # noqa: BLE001
                total_errors += 1
                print(f"  [ERREUR] {chunk_start.date()} -> {chunk_end.date()}: {exc}", file=sys.stderr)
            time.sleep(args.sleep)

    print(f"\nTerminé. Appels réussis: {total_calls}, erreurs: {total_errors}")
    if total_calls == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
