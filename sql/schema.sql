CREATE TABLE IF NOT EXISTS dim_city (
    city_key    SERIAL PRIMARY KEY,
    city_id     VARCHAR(50) UNIQUE NOT NULL,
    city_name   VARCHAR(100) NOT NULL,
    country     VARCHAR(10) NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_time (
    time_key      SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMPTZ UNIQUE NOT NULL,
    date          DATE NOT NULL,
    hour          SMALLINT NOT NULL,
    day           SMALLINT NOT NULL,
    month         SMALLINT NOT NULL,
    year          SMALLINT NOT NULL,
    day_of_week   SMALLINT NOT NULL,
    day_name      VARCHAR(10) NOT NULL,
    is_weekend    BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_air_quality (
    fact_id     BIGSERIAL PRIMARY KEY,
    city_key    INTEGER NOT NULL REFERENCES dim_city(city_key),
    time_key    INTEGER NOT NULL REFERENCES dim_time(time_key),
    aqi         SMALLINT,      -- indice OpenWeatherMap 1 (bon) à 5 (très mauvais)
    co          DOUBLE PRECISION,   -- µg/m3
    no          DOUBLE PRECISION,   -- µg/m3
    no2         DOUBLE PRECISION,   -- µg/m3
    o3          DOUBLE PRECISION,   -- µg/m3
    so2         DOUBLE PRECISION,   -- µg/m3
    pm2_5       DOUBLE PRECISION,   -- µg/m3
    pm10        DOUBLE PRECISION,   -- µg/m3
    nh3         DOUBLE PRECISION,   -- µg/m3
    UNIQUE (city_key, time_key)     -- garantit une seule mesure par ville/heure
);

CREATE INDEX IF NOT EXISTS idx_fact_city ON fact_air_quality(city_key);
CREATE INDEX IF NOT EXISTS idx_fact_time ON fact_air_quality(time_key);