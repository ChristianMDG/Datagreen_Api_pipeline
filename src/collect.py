import json
from pathlib import Path
import requests


CONFIG_FILE = Path("cities.json")

AIR_QUALITY_API = "https://air-quality-api.open-meteo.com/v1/air-quality"


def load_cities():
    """
    Charge la liste des villes depuis le fichier JSON.
    """
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_air_quality(city):
    """
    Récupère la qualité de l'air pour une ville.
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
        params=params
    )

    response.raise_for_status()

    return response.json()


def main():

    cities = load_cities()

    print(f"{len(cities)} villes chargées\n")

    city = cities[0]

    print(f"Récupération des données pour {city['name']}...")

    air_data = get_air_quality(city)

    print("\nDonnées reçues :")
    print(air_data.keys())


if __name__ == "__main__":
    main()