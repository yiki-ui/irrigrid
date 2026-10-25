#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Ingestion: NASA POWER Weather Service
Fetches daily agrometeorology from NASA POWER API.
Guaranteed to fail gracefully to cached SQLite data without crashing if unreachable.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional
import requests

_BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = _BASE_DIR / "cache" / "data.db"
NASA_API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Pre-computed climatological monthly averages for Rwanda demo locations
DEFAULT_CLIMATE_FALLBACK = {
    "t_min": 15.2, "t_max": 25.8, "humidity": 68.0,
    "wind_speed_2m": 2.1, "solar_radiation_mj": 18.5, "rainfall_mm": 3.2,
    "source": "climatology_fallback"
}


def init_nasa_cache(db_path: Path = DB_PATH) -> None:
    """Ensure SQLite cache table exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nasa_power_cache (
                cache_key TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL,
                data_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nasa_climatology_cache (
                cache_key TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL,
                data_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def _calculate_effective_rainfall(rain_mm: float) -> float:
    """USDA SCS method for monthly effective rainfall."""
    if rain_mm <= 0:
        return 0.0
    if rain_mm <= 250:
        eff = (rain_mm * (125.0 - 0.2 * rain_mm)) / 125.0
        return max(0.0, round(eff, 1))
    eff = 125.0 + 0.1 * rain_mm
    return round(eff, 1)


def get_nasa_climatology(lat: float, lon: float, elevation: float = 1500.0, timeout_sec: int = 8, db_path: Path = DB_PATH) -> Dict:
    """
    Fetch 12-month 30-year climatology from NASA POWER for Rwanda coordinate.
    Returns structured monthly_climate, monthly_rainfall, and raw metrics.
    Gracefully falls back to SQLite cache or regional averages.
    """
    init_nasa_cache(db_path)
    cache_key = f"{round(lat, 2)}_{round(lon, 2)}"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # 1. Attempt live fetch from NASA POWER
    try:
        from src.weather.nasa_power import NASAPowerAPI
        api = NASAPowerAPI(timeout=timeout_sec)
        res = api.get_irrigation_parameters(latitude=lat, longitude=lon, elevation=elevation)
        if res and "temp_min" in res and len(res["temp_min"]) == 12:
            monthly_climate = []
            monthly_rainfall = []
            for i in range(12):
                tmin = round(float(res["temp_min"][i]), 1)
                tmax = round(float(res["temp_max"][i]), 1)
                hum = round(float(res.get("humidity", [70] * 12)[i]), 1)
                rhmin = max(20.0, round(hum * 0.65, 1))
                rhmax = min(98.0, round(hum * 1.15, 1))
                ws = round(float(res.get("wind_speed", [2.0] * 12)[i]), 2)
                rad = round(float(res.get("solar_radiation_mj", [18] * 12)[i]), 1)
                sun = round(rad * 0.45, 1)
                eto = round(float(res.get("eto_daily_mm", [3.8] * 12)[i]), 2)
                rain_m = round(float(res.get("rainfall_mm", [80] * 12)[i]), 1)

                monthly_climate.append({
                    "month": months[i],
                    "tmin": tmin,
                    "tmax": tmax,
                    "rhmin": rhmin,
                    "rhmax": rhmax,
                    "wind_speed": ws,
                    "sunshine_hours": sun,
                    "eto": eto
                })
                monthly_rainfall.append({
                    "month": months[i],
                    "rainfall_mm": rain_m,
                    "effective_rain_mm": _calculate_effective_rainfall(rain_m)
                })

            payload = {
                "source": "nasa_power_live",
                "latitude": lat,
                "longitude": lon,
                "elevation": elevation,
                "monthly_climate": monthly_climate,
                "monthly_rainfall": monthly_rainfall,
                "raw": {
                    "temp_min": res["temp_min"],
                    "temp_max": res["temp_max"],
                    "rainfall_mm": res["rainfall_mm"],
                    "eto_daily_mm": res["eto_daily_mm"],
                    "eto_monthly_mm": res.get("eto_monthly_mm", []),
                    "solar_radiation_mj": res.get("solar_radiation_mj", []),
                }
            }

            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO nasa_climatology_cache (cache_key, latitude, longitude, data_json) VALUES (?, ?, ?, ?)",
                    (cache_key, lat, lon, json.dumps(payload))
                )
                conn.commit()
            return payload
    except Exception as e:
        print(f"[NASA Ingestion] Live fetch warning (will use cache/fallback): {e}")

    # 2. Check SQLite climatology cache
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT data_json FROM nasa_climatology_cache WHERE cache_key = ?", (cache_key,))
            row = cur.fetchone()
        if row:
            cached = json.loads(row[0])
            cached["source"] = "nasa_power_cache"
            return cached
    except Exception:
        pass

    # 3. Regional Rwanda highland climatology baseline
    tmin_base = [13.5, 13.8, 14.2, 14.5, 14.0, 12.8, 12.2, 13.1, 13.7, 14.0, 13.9, 13.6]
    tmax_base = [24.2, 24.8, 24.5, 23.8, 23.5, 24.1, 24.6, 25.2, 24.7, 24.0, 23.6, 23.9]
    rain_base = [75.0, 85.0, 140.0, 185.0, 120.0, 35.0, 18.0, 42.0, 90.0, 130.0, 155.0, 95.0]
    eto_base = [3.8, 4.1, 3.9, 3.5, 3.4, 3.7, 3.9, 4.2, 4.0, 3.7, 3.5, 3.6]

    monthly_climate = []
    monthly_rainfall = []
    for i in range(12):
        monthly_climate.append({
            "month": months[i],
            "tmin": tmin_base[i],
            "tmax": tmax_base[i],
            "rhmin": 52.0 if rain_base[i] < 70 else 64.0,
            "rhmax": 80.0 if rain_base[i] < 70 else 88.0,
            "wind_speed": 1.8,
            "sunshine_hours": 6.5 if rain_base[i] < 70 else 5.2,
            "eto": eto_base[i]
        })
        monthly_rainfall.append({
            "month": months[i],
            "rainfall_mm": rain_base[i],
            "effective_rain_mm": _calculate_effective_rainfall(rain_base[i])
        })

    return {
        "source": "climatology_fallback",
        "latitude": lat,
        "longitude": lon,
        "elevation": elevation,
        "monthly_climate": monthly_climate,
        "monthly_rainfall": monthly_rainfall
    }


def get_weather_data(lat: float, lon: float, timeout_sec: int = 5, db_path: Path = DB_PATH) -> Dict:
    """
    Fetch weather parameters (temperature, humidity, wind, radiation) for coordinate.
    If network is down or API fails, returns cached or baseline data gracefully.
    """
    init_nasa_cache(db_path)
    cache_key = f"{round(lat, 2)}_{round(lon, 2)}"

    # 1. Attempt live API fetch
    try:
        params = {
            "parameters": "T2M_MIN,T2M_MAX,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": "20240101",
            "end": "20240107",
            "format": "JSON"
        }
        contact_email = os.getenv("CONTACT_EMAIL", "").strip()
        headers = {
            "User-Agent": f"IrriGrid-Shamba/1.0 ({contact_email})" if contact_email else "IrriGrid-Shamba/1.0 (irrigation-planning)"
        }
        resp = requests.get(NASA_API_URL, params=params, headers=headers, timeout=timeout_sec)
        if resp.status_code == 200:
            payload = resp.json()
            props = payload.get("properties", {}).get("parameter", {})

            # Extract recent means
            t_min = float(list(props.get("T2M_MIN", {}).values())[-1])
            t_max = float(list(props.get("T2M_MAX", {}).values())[-1])
            rh = float(list(props.get("RH2M", {}).values())[-1])
            ws = float(list(props.get("WS2M", {}).values())[-1])
            rad = float(list(props.get("ALLSKY_SFC_SW_DWN", {}).values())[-1])
            rain = float(list(props.get("PRECTOTCORR", {}).values())[-1])

            data = {
                "t_min": t_min if t_min > -50 else 15.0,
                "t_max": t_max if t_max > -50 else 26.0,
                "humidity": rh if rh >= 0 else 70.0,
                "wind_speed_2m": ws if ws >= 0 else 2.0,
                "solar_radiation_mj": rad if rad >= 0 else 18.0,
                "rainfall_mm": max(0.0, rain),
                "source": "nasa_power_live"
            }

            # Cache the successful result
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO nasa_power_cache (cache_key, latitude, longitude, data_json) VALUES (?, ?, ?, ?)",
                    (cache_key, lat, lon, json.dumps(data))
                )
                conn.commit()
            return data
    except Exception:
        pass  # Fail gracefully to cache

    # 2. Check SQLite cache
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT data_json FROM nasa_power_cache WHERE cache_key = ?", (cache_key,))
            row = cur.fetchone()
        if row:
            cached = json.loads(row[0])
            cached["source"] = "nasa_power_cache"
            return cached
    except Exception:
        pass

    # 3. Final graceful baseline
    return DEFAULT_CLIMATE_FALLBACK.copy()


if __name__ == "__main__":
    init_nasa_cache()
    w = get_weather_data(-1.4998, 29.6349, timeout_sec=2)
    print(f"NASA POWER weather test: {w}")
