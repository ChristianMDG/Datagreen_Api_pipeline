"""
validate_clean.py
Valide que data/clean/clean.csv respecte le contrat de données.
Retourne un code de sortie != 0 si une règle est violée
(utile pour bloquer le pipeline CI/CD en cas de problème).
"""
import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH = os.path.join(BASE_DIR, "data", "clean", "clean.csv")

REQUIRED_COLUMNS = [
    "city_id", "city_name", "country", "latitude", "longitude",
    "timestamp_utc", "aqi", "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3",
]


def fail(msg):
    print(f"[FAIL] {msg}")
    return False


def main():
    ok = True

    if not os.path.exists(CLEAN_PATH):
        print(f"[FAIL] {CLEAN_PATH} introuvable.")
        sys.exit(1)

    df = pd.read_csv(CLEAN_PATH, parse_dates=["timestamp_utc"])

    # 1. Colonnes attendues
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        ok = fail(f"Colonnes manquantes: {missing}")
    else:
        print("[OK] Toutes les colonnes requises sont présentes.")

    # 2. Au moins 5 villes
    n_cities = df["city_id"].nunique()
    if n_cities < 5:
        ok = fail(f"Seulement {n_cities} villes (5 minimum requis).")
    else:
        print(f"[OK] {n_cities} villes présentes.")

    # 3. Pas de doublons (ville, heure)
    dups = df.duplicated(subset=["city_id", "timestamp_utc"]).sum()
    if dups > 0:
        ok = fail(f"{dups} doublons (city_id, timestamp_utc) détectés.")
    else:
        print("[OK] Aucun doublon (ville, heure).")

    # 4. Tri chronologique par ville
    for city_id, group in df.groupby("city_id"):
        if not group["timestamp_utc"].is_monotonic_increasing:
            ok = fail(f"Données non triées chronologiquement pour {city_id}.")
    else:
        print("[OK] Données triées chronologiquement par ville.")

    # 5. Pas de AQI manquant/négatif
    if df["aqi"].isna().any():
        ok = fail("Valeurs AQI manquantes détectées.")
    elif (df["aqi"] < 0).any():
        ok = fail("Valeurs AQI négatives détectées.")
    else:
        print("[OK] Colonne AQI valide.")

    # 6. Couverture temporelle minimale (>= 3 mois)
    span_days = (df["timestamp_utc"].max() - df["timestamp_utc"].min()).days
    if span_days < 89:
        ok = fail(f"Couverture temporelle trop courte: {span_days} jours (3 mois minimum).")
    else:
        print(f"[OK] Couverture temporelle: {span_days} jours.")

    print(f"\nTotal lignes: {len(df)}")

    if not ok:
        sys.exit(1)
    print("\nValidation réussie.")


if __name__ == "__main__":
    main()
