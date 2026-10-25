#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Cache Seed Script
Pre-populates backend/cache/data.db with:
1. All 30 Rwanda district baselines from NISR CSV
2. Pre-fetched NASA POWER weather data for key demo locations (Musanze, Kigali, Bugesera, Nyabihu, Huye)
3. Pre-computed NDVI vegetation indices
Produces a static data.db build artifact ready to be committed to git.
"""

import json
import sqlite3
from pathlib import Path
import sys

_BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE_DIR.parent))

from backend.ingestion.nisr_baseline import init_nisr_table
from backend.ingestion.nasa_power import init_nasa_cache
from backend.ingestion.ndvi import init_ndvi_cache

DB_PATH = _BASE_DIR / "cache" / "data.db"

DEMO_LOCATIONS = [
    {"name": "Musanze", "lat": -1.50, "lon": 29.63, "t_min": 14.5, "t_max": 24.8, "humidity": 74.0, "solar": 18.2, "rain": 4.1, "ndvi": 0.72},
    {"name": "Kigali", "lat": -1.94, "lon": 30.06, "t_min": 16.8, "t_max": 27.2, "humidity": 65.0, "solar": 19.5, "rain": 2.8, "ndvi": 0.58},
    {"name": "Bugesera", "lat": -2.15, "lon": 30.20, "t_min": 17.5, "t_max": 28.5, "humidity": 60.0, "solar": 20.1, "rain": 1.9, "ndvi": 0.48},
    {"name": "Nyabihu", "lat": -1.65, "lon": 29.50, "t_min": 12.8, "t_max": 22.5, "humidity": 78.0, "solar": 17.4, "rain": 4.8, "ndvi": 0.75},
    {"name": "Huye", "lat": -2.60, "lon": 29.74, "t_min": 15.6, "t_max": 26.0, "humidity": 69.0, "solar": 18.8, "rain": 3.4, "ndvi": 0.64},
]


def seed_database():
    print(f"Initializing & seeding SQLite database at {DB_PATH}...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Seed NISR baseline
    init_nisr_table(DB_PATH)

    # 2. Seed NASA cache & NDVI cache tables
    init_nasa_cache(DB_PATH)
    init_ndvi_cache(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for loc in DEMO_LOCATIONS:
        cache_key = f"{round(loc['lat'], 2)}_{round(loc['lon'], 2)}"

        # Weather payload
        weather_data = {
            "location_name": loc["name"],
            "t_min": loc["t_min"],
            "t_max": loc["t_max"],
            "humidity": loc["humidity"],
            "wind_speed_2m": 2.1,
            "solar_radiation_mj": loc["solar"],
            "rainfall_mm": loc["rain"],
            "source": "pre_seeded_cache"
        }
        cur.execute(
            "INSERT OR REPLACE INTO nasa_power_cache (cache_key, latitude, longitude, data_json) VALUES (?, ?, ?, ?)",
            (cache_key, loc["lat"], loc["lon"], json.dumps(weather_data))
        )

        # NDVI payload
        ndvi_data = {
            "location_name": loc["name"],
            "ndvi": loc["ndvi"],
            "status": "Dense / High Vigor Crop" if loc["ndvi"] >= 0.65 else "Moderate Vigor / Developing Crop",
            "kc_multiplier": round(min(1.2, max(0.4, 1.2 * loc["ndvi"] + 0.15)), 2),
            "source": "pre_seeded_cache"
        }
        cur.execute(
            "INSERT OR REPLACE INTO ndvi_cache (cache_key, latitude, longitude, ndvi_value, data_json) VALUES (?, ?, ?, ?, ?)",
            (cache_key, loc["lat"], loc["lon"], loc["ndvi"], json.dumps(ndvi_data))
        )

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
