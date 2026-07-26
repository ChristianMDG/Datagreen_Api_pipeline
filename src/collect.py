import json
from pathlib import Path
import requests


CONFIG_FILE = Path("cities.json")
OUTPUT_FILE = Path("data/raw/air_quality_raw.json")
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
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_data(data):
    """
    Sauvegarde les données collectées dans un fichier JSON.
    """

    OUTPUT_FILE.parent.mkdir(
        exist_ok=True
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def main():

    cities = load_cities()

    print(f"{len(cities)} villes chargées\n")

    results = []

    for city in cities:

        print(f"Collecte : {city['name']}...")

        try:
            air_data = get_air_quality(city)

            results.append({
                "city": city,
                "air_quality": air_data
            })

        except requests.exceptions.RequestException as e:
            print(f"Erreur pour {city['name']} : {e}")

    save_data(results)

    print("\nCollecte terminée.")
    print(f"Fichier créé : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()