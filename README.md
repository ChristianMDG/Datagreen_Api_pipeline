# Pipeline AQI — Data Warehouse

Pipeline de collecte automatique 24h/24 de la qualité de l'air (AQI) pour 5 villes,
avec data warehouse en modélisation dimensionnelle (schéma en étoile).

Voir aussi [`ARCHITECTURE.md`](./ARCHITECTURE.md) pour le détail des choix techniques.

## 1. Villes suivies

| city_id | Ville | Pays | Latitude | Longitude |
|---|---|---|---|---|
| paris | Paris | FR | 48.8566 | 2.3522 |
| antananarivo | Antananarivo | MG | -18.8792 | 47.5079 |
| new_delhi | New Delhi | IN | 28.6139 | 77.2090 |
| beijing | Beijing | CN | 39.9042 | 116.4074 |
| nairobi | Nairobi | KE | -1.2921 | 36.8219 |

(Modifiable dans `cities.json`.)

## 2. Source des données

**API :** [OpenWeatherMap Air Pollution API](https://openweathermap.org/api/air-pollution)
- Endpoint courant : `/data/2.5/air_pollution`
- Endpoint historique : `/data/2.5/air_pollution/history` (disponible depuis le 27/11/2020)

L'indice **AQI** fourni par cette API est l'échelle propre à OpenWeatherMap, de **1 (Bon)** à
**5 (Très mauvais)** — ce n'est PAS l'échelle US EPA 0-500. C'est précisé ici pour lever
toute ambiguïté pour IA1.

## 3. Contrat de données — `data/clean/clean.csv`

Une ligne = une ville, une heure. Trié par `city_id` puis `timestamp_utc`, sans doublons.

| Colonne | Type | Unité / échelle | Description |
|---|---|---|---|
| `city_id` | string | — | identifiant technique de la ville |
| `city_name` | string | — | nom lisible |
| `country` | string | code ISO 2 lettres | pays |
| `latitude` | float | degrés décimaux | |
| `longitude` | float | degrés décimaux | |
| `timestamp_utc` | ISO 8601 (UTC) | — | horodatage de la mesure, arrondi à l'heure |
| `aqi` | int | 1 à 5 (échelle OpenWeatherMap) | indice de qualité de l'air |
| `co` | float | µg/m³ | monoxyde de carbone |
| `no` | float | µg/m³ | monoxyde d'azote |
| `no2` | float | µg/m³ | dioxyde d'azote |
| `o3` | float | µg/m³ | ozone |
| `so2` | float | µg/m³ | dioxyde de soufre |
| `pm2_5` | float | µg/m³ | particules fines ≤ 2.5 µm |
| `pm10` | float | µg/m³ | particules fines ≤ 10 µm |
| `nh3` | float | µg/m³ | ammoniac |

## 4. Zone `raw/`

`data/raw/<city_id>/<city_id>_<horodatage>.json` — un fichier par ville et par appel API,
jamais modifié après écriture. Contient la réponse brute de l'API + métadonnées de collecte.
C'est la source de vérité : `clean/` peut être régénéré à tout moment avec :

```bash
python src/build_clean.py
python src/validate_clean.py
```

## 5. Schéma du data warehouse (étoile)

```
                    dim_city
                    ─────────
                    city_key (PK)
                    city_id
                    city_name
                    country
                    latitude
                    longitude
                        │
                        │ 1
                        │
                        ▼ N
                 fact_air_quality              N ▲
                 ──────────────────               │ 1
                 fact_id (PK)                      │
                 city_key (FK)  ─────────────────► │
                 time_key (FK)  ─────────────────► dim_time
                 aqi                               ─────────
                 co, no, no2, o3, so2               time_key (PK)
                 pm2_5, pm10, nh3                   timestamp_utc
                                                     date, hour
                                                     day, month, year
                                                     day_of_week, day_name
                                                     is_weekend
```

Voir [`sql/schema.sql`](./sql/schema.sql) pour le DDL complet.

Règles respectées :
- aucune mesure (aqi, polluants) dans les dimensions ;
- aucune colonne descriptive (nom de ville, jour de la semaine...) dans la table de faits,
  uniquement des clés étrangères + mesures.

## 6. Période couverte / trous connus

À compléter après le premier backfill, par ex. :
> Backfill du 25/04/2026 au 25/07/2026 (3 mois) pour les 5 villes.
> Trou connu : Beijing, 12–14/06/2026 (panne API amont, voir issue #X).

Cohérence attendue : `lignes fact_air_quality ≈ nb_villes × nb_heures_couvertes`.
Tout écart significatif doit être documenté ici.

## 7. Connexion à la base (Supabase)

- Host / URL de connexion : **à compléter par le groupe** (Project Settings → Database → Connection string)
- Le warehouse est interrogeable en lecture seule via un compte dédié fourni au correcteur / à IA1.
- Exemple de requête de vérification :

```sql
SELECT c.city_name, COUNT(*) AS nb_mesures,
       MIN(t.timestamp_utc) AS depuis, MAX(t.timestamp_utc) AS jusqua
FROM fact_air_quality f
JOIN dim_city c ON c.city_key = f.city_key
JOIN dim_time t ON t.time_key = f.time_key
GROUP BY c.city_name
ORDER BY c.city_name;
```

## 8. Installation / exécution locale

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis remplir OWM_API_KEY et DATABASE_URL
export $(cat .env | xargs)

# Backfill initial (3 à 12 mois)
python src/backfill.py --months 12

# Reconstruire clean.csv et valider
python src/build_clean.py
python src/validate_clean.py

# Charger le warehouse
python src/load_warehouse.py

# Collecte ponctuelle (comme le fait le cron toutes les heures)
python src/collect.py
```

## 9. Déploiement automatique (production)

1. Créer un projet [Supabase](https://supabase.com) (gratuit) → récupérer `DATABASE_URL`.
2. Créer une clé API sur [openweathermap.org](https://openweathermap.org/api/air-pollution).
3. Dans le repo GitHub : **Settings → Secrets and variables → Actions**, ajouter :
   - `OWM_API_KEY`
   - `DATABASE_URL`
4. Lancer manuellement le workflow **Backfill manuel** (onglet Actions) pour l'historique initial.
5. Le workflow **Collecte horaire AQI** tourne ensuite automatiquement, toutes les heures, 24h/24.
6. Vérifier l'onglet **Actions** du repo pour voir l'historique des runs (preuve d'automatisation).
