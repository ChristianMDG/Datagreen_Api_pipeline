CREATE TABLE IF NOT EXISTS dim_city (
    city_id SERIAL PRIMARY KEY,
    city VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_time (
    time_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP UNIQUE NOT NULL,
    hour INTEGER,
    day INTEGER,
    month INTEGER,
    year INTEGER,
    weekday INTEGER
);

CREATE TABLE IF NOT EXISTS fact_air_quality (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES dim_city(city_id),
    time_id INTEGER REFERENCES dim_time(time_id),
    aqi INTEGER,
    pm25 FLOAT,
    pm10 FLOAT,
    o3 FLOAT,
    no2 FLOAT,
    so2 FLOAT,
    co FLOAT
);

CREATE INDEX IF NOT EXISTS idx_fact_city ON fact_air_quality(city_id);
CREATE INDEX IF NOT EXISTS idx_fact_time ON fact_air_quality(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_city_time ON fact_air_quality(city_id, time_id);

INSERT INTO dim_city (city, country) VALUES
('Paris', 'FR'),
('Antananarivo', 'MG'),
('New Delhi', 'IN'),
('Beijing', 'CN'),
('Nairobi', 'KE')
ON CONFLICT (city) DO NOTHING;

INSERT INTO dim_time (timestamp, hour, day, month, year, weekday) VALUES
('2026-01-01 11:00:00', 11, 1, 1, 2026, 4),
('2026-01-01 12:00:00', 12, 1, 1, 2026, 4),
('2026-01-01 13:00:00', 13, 1, 1, 2026, 4)
ON CONFLICT (timestamp) DO NOTHING;

INSERT INTO fact_air_quality (city_id, time_id, aqi, pm25, pm10, o3, no2, so2, co)
SELECT 
    c.city_id,
    t.time_id,
    f.aqi,
    f.pm25,
    f.pm10,
    f.o3,
    f.no2,
    f.so2,
    f.co
FROM (
    VALUES 
        ('Paris', '2026-01-01 11:00:00', 3, 17.9, 25.3, 30.5, 22.1, 4.8, 310.4),
        ('Paris', '2026-01-01 12:00:00', 3, 18.4, 26.0, 29.8, 23.0, 5.0, 315.2),
        ('Antananarivo', '2026-01-01 11:00:00', 2, 12.4, 18.7, 45.3, 8.2, 2.1, 230.1),
        ('Antananarivo', '2026-01-01 12:00:00', 2, 13.1, 19.2, 44.1, 8.9, 2.3, 235.0),
        ('Antananarivo', '2026-01-01 13:00:00', 3, 14.2, 20.1, 42.0, 9.5, 2.5, 240.5),
        ('New Delhi', '2026-01-01 11:00:00', 4, 45.2, 67.8, 25.1, 35.4, 8.2, 450.3),
        ('New Delhi', '2026-01-01 12:00:00', 4, 47.1, 69.3, 24.5, 36.2, 8.5, 455.7),
        ('Beijing', '2026-01-01 11:00:00', 3, 25.3, 38.7, 35.2, 28.1, 6.3, 380.2),
        ('Beijing', '2026-01-01 12:00:00', 3, 26.1, 39.5, 34.8, 29.0, 6.5, 385.1),
        ('Nairobi', '2026-01-01 11:00:00', 2, 10.2, 15.3, 50.1, 5.2, 1.2, 180.3),
        ('Nairobi', '2026-01-01 12:00:00', 2, 10.8, 15.9, 49.5, 5.5, 1.3, 182.7)
) AS f(city_name, timestamp, aqi, pm25, pm10, o3, no2, so2, co)
JOIN dim_city c ON c.city = f.city_name
JOIN dim_time t ON t.timestamp = f.timestamp::timestamp;

SELECT * FROM dim_city;
SELECT * FROM fact_air_quality;

SELECT 
    c.city,
    c.country,
    t.timestamp,
    t.hour,
    t.day,
    t.month,
    t.year,
    f.aqi,
    f.pm25,
    f.pm10,
    f.o3,
    f.no2,
    f.so2,
    f.co
FROM fact_air_quality f
JOIN dim_city c ON f.city_id = c.city_id
JOIN dim_time t ON f.time_id = t.time_id
ORDER BY t.timestamp, c.city;

SELECT 
    c.city,
    COUNT(*) as nb_mesures,
    ROUND(AVG(f.aqi)::numeric, 2) as aqi_moyen,
    ROUND(AVG(f.pm25)::numeric, 2) as pm25_moyen,
    ROUND(AVG(f.pm10)::numeric, 2) as pm10_moyen
FROM fact_air_quality f
JOIN dim_city c ON f.city_id = c.city_id
GROUP BY c.city
ORDER BY aqi_moyen DESC;

SELECT 
    t.month,
    t.year,
    COUNT(*) as nb_mesures,
    ROUND(AVG(f.aqi)::numeric, 2) as aqi_moyen
FROM fact_air_quality f
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY t.year, t.month
ORDER BY t.year, t.month;

SELECT 
    c.city,
    t.hour,
    ROUND(AVG(f.aqi)::numeric, 2) as aqi_moyen
FROM fact_air_quality f
JOIN dim_city c ON f.city_id = c.city_id
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY c.city, t.hour
ORDER BY c.city, t.hour;

SELECT 
    c.city,
    t.timestamp,
    f.aqi,
    f.pm25,
    f.pm10
FROM fact_air_quality f
JOIN dim_city c ON f.city_id = c.city_id
JOIN dim_time t ON f.time_id = t.time_id
ORDER BY t.timestamp DESC
LIMIT 10;

SELECT 
    c.country,
    COUNT(*) as nb_mesures,
    ROUND(AVG(f.aqi)::numeric, 2) as aqi_moyen
FROM fact_air_quality f
JOIN dim_city c ON f.city_id = c.city_id
GROUP BY c.country
ORDER BY aqi_moyen DESC;
