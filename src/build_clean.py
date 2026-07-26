
import json
import logging

import pandas as pd

from src.collect import RAW_DIR, CLEAN_DIR
from src.validate_clean import validate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_FILE = CLEAN_DIR / "aqi_clean.csv"

FINAL_COLUMNS = [
    "city",
    "country",
    "latitude",
    "longitude",
    "timestamp_utc",
    "aqi",
    "co",
    "no",
    "no2",
    "o3",
    "so2",
    "pm25",
    "pm10",
    "nh3",
]

NUMERIC_COLUMNS = [
    "latitude",
    "longitude",
    "aqi",
    "co",
    "no",
    "no2",
    "o3",
    "so2",
    "nh3",
    "pm25",
    "pm10",
]

def read_raw_files(folder):
    rows = []
    files = list(folder.rglob("*.json"))
    logger.info(f"{len(files)} raw files found")

    for file in files:
        try:
            with open(file, encoding="utf-8") as f:
                data = json.load(f)
            rows.append(
                {
                    "data": data,
                    "file_time": file.stat().st_mtime,
                    "path": file,
                }
            )
        except Exception as e:
            logger.error(f"{file}: {e}")

    return rows

def extract_row(data: dict):
    entry = (data.get("list") or [{}])[0]

    main = entry.get("main", {})
    components = entry.get("components", {})
    coordinates = data.get("coordinates", {})

    return {
        "city": data.get("city"),
        "country": data.get("country"),
        "latitude": coordinates.get("latitude"),
        "longitude": coordinates.get("longitude"),
        "timestamp_utc": data.get("timestamp"),
        "aqi": main.get("aqi"),
        "co": components.get("co"),
        "no": components.get("no"),
        "no2": components.get("no2"),
        "o3": components.get("o3"),
        "so2": components.get("so2"),
        "nh3": components.get("nh3"),
        "pm25": components.get("pm2_5"),
        "pm10": components.get("pm10"),
    }

def clean_dataframe(df):
    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"], errors="coerce", utc=True
    )

    df = df.dropna(subset=["city", "timestamp_utc"])

    df[NUMERIC_COLUMNS] = df[NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")

    df["hour"] = df["timestamp_utc"].dt.floor("h")

    df = df.sort_values(["city", "hour", "file_time"])

    df = df.drop_duplicates(["city", "hour"], keep="last")

    return df

def write_clean(df, output):
    output.parent.mkdir(parents=True, exist_ok=True)

    df[FINAL_COLUMNS].to_csv(output, index=False)

def main():
    raw_items = read_raw_files(RAW_DIR)

    if not raw_items:
        logger.info("No raw files found in the data lake")
        return

    rows = []
    for item in raw_items:
        row = extract_row(item["data"])
        row["file_time"] = item["file_time"]
        rows.append(row)

    df = pd.DataFrame(rows)
    df = clean_dataframe(df)
    df = validate(df)
    write_clean(df, OUTPUT_FILE)

    logger.info(f"{len(df)} clean rows written to {OUTPUT_FILE} (full history)")


if __name__ == "__main__":
    main()