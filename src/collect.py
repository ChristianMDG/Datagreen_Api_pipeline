import json
from pathlib import Path
from datetime import datetime
import requests


CONFIG_FILE = Path("cities.json")
RAW_FOLDER = Path("data/raw")

AIR_QUALITY_API = "https://air-quality-api.open-meteo.com/v1/air-quality"


def load_cities():
    """
    Charge les villes depuis cities.json.
    """
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_air_quality(city):
    """
    Appelle l'API Open-Meteo pour une ville.
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
        "timezone": "auto"
    }

    response = requests.get(
        AIR_QUALITY_API,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_raw_data(city, data):
    """
    Sauvegarde un fichier JSON par ville.
    """

    RAW_FOLDER.mkdir(
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"{city['city_id']}_{timestamp}.json"
    )

    filepath = RAW_FOLDER / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "city": city,
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
        f"{len(cities)} villes chargées\n"
    )

    for city in cities:

        print(
            f"Collecte : {city['name']}..."
        )

        try:
            data = get_air_quality(city)

            save_raw_data(
                city,
                data
            )

        except requests.exceptions.RequestException as e:

            print(
                f"Erreur API pour {city['name']} : {e}"
            )


if __name__ == "__main__":
    main()