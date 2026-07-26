import logging

logger = logging.getLogger(__name__)

POLLUTANT_COLUMNS = ["co", "no", "no2", "o3", "so2", "nh3", "pm25", "pm10"]


def validate(df):

    if df.empty:
        raise Exception("Empty dataframe")

    before = len(df)

    df = df[df["aqi"].between(1, 5)]

    for column in POLLUTANT_COLUMNS:
        df = df[~(df[column] < 0)]

    dropped = before - len(df)
    if dropped:
        logger.warning(f"{dropped} invalid row(s) dropped during validation")

    if df.empty:
        raise Exception("All rows invalid after validation")

    return df