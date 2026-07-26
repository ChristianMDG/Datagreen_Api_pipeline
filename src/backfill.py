import json
from pathlib import Path
from datetime import datetime
import requests


CONFIG_FILE = Path("cities.json")
RAW_FOLDER = Path("data/raw")

AIR_QUALITY_API = "https://air-quality-api.open-meteo.com/v1/air-quality"


# Période historique à récupérer
START_DATE = "2026-01-01"
END_DATE = "2026-07-01"


def load_cities():
    """
    Charge la liste des villes.
    """
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_historical_air_quality(city):
    """
    Récupère les données historiques de qualité de l'air.
    """

    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "ozone"
        ],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "timezone": "auto"
    }

    response = requests.get(
        AIR_QUALITY_API,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_backfill(city, data):
    """
    Sauvegarde les données historiques d'une ville.
    """

    RAW_FOLDER.mkdir(
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"{city['city_id']}_history_{timestamp}.json"
    )

    filepath = RAW_FOLDER / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "city": city,
                "period": {
                    "start_date": START_DATE,
                    "end_date": END_DATE
                },
                "air_quality": data
            },
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"Sauvegardé : {filepath}")


def main():

    cities = load_cities()

    print(
        f"Backfill pour {len(cities)} villes\n"
    )

    for city in cities:

        print(
            f"Historique : {city['name']}..."
        )

        try:

            data = get_historical_air_quality(city)

            save_backfill(
                city,
                data
            )

        except requests.exceptions.RequestException as e:

            print(
                f"Erreur API pour {city['name']} : {e}"
            )


if __name__ == "__main__":
    main()