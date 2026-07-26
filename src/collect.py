import json
from pathlib import Path


CONFIG_FILE = Path("cities.json")


def load_cities():
    """
    Charge la liste des villes depuis le fichier JSON.
    """
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cities = load_cities()

    print(f"{len(cities)} villes chargées :\n")

    for city in cities:
        print(
            f"- {city['name']} ({city['country']}) "
            f"[{city['latitude']}, {city['longitude']}]"
        )


if __name__ == "__main__":
    main()