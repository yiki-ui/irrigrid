#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid SoilGrids v2.0 Ingestion & Pedotransfer Processing
Fetches sand, silt, and clay fractions from ISRIC SoilGrids REST API,
uses thickness-weighted averaging for 0-30 cm layers, classifies USDA texture,
and computes field capacity, wilting point, TAM, and infiltration rate.

Cache: only SUCCESSFUL SoilGrids lookups are cached. Fallbacks are never cached
so that a timeout on one request does not permanently pin a location to the fallback.
"""

import os
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("soilgrids")

# Cache: (round(lat,3), round(lon,3)) -> dict  (SoilGrids results only)
_SOIL_CACHE: Dict[tuple, Dict] = {}

# Depth-layer weights by thickness (cm): 0-5=5, 5-15=10, 15-30=15
_LAYER_WEIGHTS = {"0-5cm": 5.0, "5-15cm": 10.0, "15-30cm": 15.0}

# Hydraulic presets by USDA texture class. FC and WP in %, infiltration in mm/h.
USDA_PROPERTIES = {
    "Clay":            {"fc": 40.0, "wp": 25.0, "inf": 2.5,  "desc": "Heavy clay soil, high water holding, low infiltration"},
    "Silty Clay":      {"fc": 38.0, "wp": 22.0, "inf": 3.5,  "desc": "Fine textured silty clay, slow drainage"},
    "Sandy Clay":      {"fc": 32.0, "wp": 18.0, "inf": 5.0,  "desc": "Clayey soil with coarse sand grains"},
    "Clay Loam":       {"fc": 35.0, "wp": 18.0, "inf": 8.0,  "desc": "Balanced soil with substantial clay, good moisture retention"},
    "Silty Clay Loam": {"fc": 35.0, "wp": 17.0, "inf": 8.0,  "desc": "Silt and clay blend, moderate to high water capacity"},
    "Sandy Clay Loam": {"fc": 28.0, "wp": 15.0, "inf": 15.0, "desc": "Well-drained loam with moderate clay and sand content"},
    "Loam":            {"fc": 30.0, "wp": 13.0, "inf": 13.0, "desc": "Ideal medium-texture agricultural soil with balanced aeration and drainage"},
    "Silt Loam":       {"fc": 33.0, "wp": 13.0, "inf": 10.0, "desc": "Soft, floury soil high in silt with high plant-available moisture"},
    "Silt":            {"fc": 31.0, "wp": 9.0,  "inf": 10.0, "desc": "Fine silty deposit, smooth texture, moderate drainage"},
    "Sandy Loam":      {"fc": 22.0, "wp": 10.0, "inf": 25.0, "desc": "Gritty, free-draining soil, warms quickly, requires frequent irrigation"},
    "Loamy Sand":      {"fc": 14.0, "wp": 6.0,  "inf": 40.0, "desc": "Predominantly coarse sand with minor binder, low retention"},
    "Sand":            {"fc": 10.0, "wp": 4.0,  "inf": 50.0, "desc": "Coarse sandy soil, very rapid drainage and low moisture storage"},
    "Volcanic Loam":   {"fc": 34.0, "wp": 16.0, "inf": 25.0, "desc": "Rich volcanic andisol typical of Northern Rwanda (Virunga highlands)"},
}

# District-level default soil mapping (from NISR agricultural survey)
_DISTRICT_SOILS: Dict[str, str] = {}
try:
    csv_path = Path(__file__).resolve().parent.parent / "data" / "nisr_ag_survey.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            d_name = str(row["district"]).strip().lower()
            _DISTRICT_SOILS[d_name] = str(row["typical_soil"]).strip()
except Exception as e:
    logger.warning("Could not pre-load NISR district soil table: %s", e)


def classify_usda_texture(sand: float, silt: float, clay: float) -> str:
    """Classify sand, silt, and clay percentages into USDA soil texture class."""
    if silt + 1.5 * clay < 15:
        return "Sand"
    elif silt + 2 * clay < 30:
        return "Loamy Sand"
    elif (clay >= 7 and clay < 20 and sand > 52 and silt + 2 * clay >= 30) or (clay < 7 and silt < 50 and silt + 2 * clay >= 30):
        return "Sandy Loam"
    elif (clay >= 7 and clay < 27 and silt >= 28 and silt < 50 and sand <= 52):
        return "Loam"
    elif (silt >= 50 and clay >= 12 and clay < 27) or (silt >= 50 and silt < 80 and clay < 12):
        return "Silt Loam"
    elif silt >= 80 and clay < 12:
        return "Silt"
    elif clay >= 20 and clay < 35 and silt < 28 and sand >= 45:
        return "Sandy Clay Loam"
    elif clay >= 27 and clay < 40 and sand > 20 and sand <= 45:
        return "Clay Loam"
    elif clay >= 27 and clay < 40 and sand <= 20:
        return "Silty Clay Loam"
    elif clay >= 35 and sand >= 45:
        return "Sandy Clay"
    elif clay >= 40 and silt >= 40:
        return "Silty Clay"
    elif clay >= 40:
        return "Clay"
    return "Loam"


def get_soil_properties(lat: float, lon: float, district: Optional[str] = None) -> Dict:
    """
    Fetch and compute soil properties with fallback chain:
    1. ISRIC SoilGrids v2.0 REST API (10s timeout)
    2. District-level default from NISR survey  (not cached)
    3. Generic Loam default                      (not cached)

    Only the SoilGrids result is cached. Fallbacks are never stored so that
    a single timeout does not permanently lock this location to the fallback.
    """
    cache_key = (round(lat, 3), round(lon, 3))
    if cache_key in _SOIL_CACHE:
        return _SOIL_CACHE[cache_key]

    # 1. Try ISRIC SoilGrids v2.0
    try:
        url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
        params = {
            "lat": lat,
            "lon": lon,
            "property": ["sand", "silt", "clay"],
            "depth": ["0-5cm", "5-15cm", "15-30cm"],
            "value": "mean"
        }
        contact_email = os.getenv("CONTACT_EMAIL", "").strip()
        headers = {
            "User-Agent": f"IrriGrid-Shamba/1.0 ({contact_email})" if contact_email else "IrriGrid-Shamba/1.0 (soilgrids-client)"
        }
        res = requests.get(url, params=params, headers=headers, timeout=10)

        if res.status_code == 429:
            logger.warning("SoilGrids rate limited (HTTP 429). Using fallback.")
        elif res.status_code == 200:
            payload = res.json()
            layers = payload.get("properties", {}).get("layers", [])

            # Thickness-weighted average for sand, silt, clay (SoilGrids unit: g/kg)
            totals: Dict[str, float] = {}
            weight_sums: Dict[str, float] = {}
            for layer in layers:
                prop_name = layer.get("name")
                for depth_entry in layer.get("depths", []):
                    depth_label = depth_entry.get("label", "")
                    mean_val = depth_entry.get("values", {}).get("mean")
                    weight = _LAYER_WEIGHTS.get(depth_label, 0.0)
                    if mean_val is not None and weight > 0:
                        totals[prop_name] = totals.get(prop_name, 0.0) + mean_val * weight
                        weight_sums[prop_name] = weight_sums.get(prop_name, 0.0) + weight

            if "sand" in totals and "silt" in totals and "clay" in totals:
                # Convert g/kg -> % (divide by 10), then normalise to 100%
                raw_sand = (totals["sand"] / weight_sums["sand"]) / 10.0
                raw_silt = (totals["silt"] / weight_sums["silt"]) / 10.0
                raw_clay = (totals["clay"] / weight_sums["clay"]) / 10.0
                total = raw_sand + raw_silt + raw_clay
                if total > 0:
                    sand_pct = round((raw_sand / total) * 100, 1)
                    silt_pct = round((raw_silt / total) * 100, 1)
                    clay_pct = round((raw_clay / total) * 100, 1)
                else:
                    sand_pct, silt_pct, clay_pct = 33.3, 33.3, 33.4

                texture = classify_usda_texture(sand_pct, silt_pct, clay_pct)
                props = USDA_PROPERTIES.get(texture, USDA_PROPERTIES["Loam"])
                tam = round((props["fc"] - props["wp"]) * 10)

                result = {
                    "name": texture,
                    "texture": texture,
                    "description": props["desc"],
                    "field_capacity": props["fc"],   # %
                    "wilting_point": props["wp"],     # %
                    "available_water_mm_m": tam,      # mm/m
                    "max_infiltration_rate": props["inf"],  # mm/h
                    "sand_pct": sand_pct,
                    "silt_pct": silt_pct,
                    "clay_pct": clay_pct,
                    "source": "ISRIC SoilGrids v2.0",
                    "isAuto": True,
                }
                # Only cache successful SoilGrids results
                _SOIL_CACHE[cache_key] = result
                return result
        else:
            logger.warning("SoilGrids returned HTTP %s. Using fallback.", res.status_code)

    except requests.exceptions.Timeout:
        logger.warning("SoilGrids timed out. Using fallback.")
    except Exception as e:
        logger.warning("SoilGrids lookup failed: %s. Using fallback.", e)

    # 2. Fallback to NISR District Baseline (NOT cached)
    if district:
        dist_clean = district.strip().lower()
        if dist_clean in _DISTRICT_SOILS:
            fallback_name = _DISTRICT_SOILS[dist_clean]
            props = USDA_PROPERTIES.get(fallback_name, USDA_PROPERTIES["Loam"])
            tam = round((props["fc"] - props["wp"]) * 10)
            return {
                "name": fallback_name,
                "texture": fallback_name,
                "description": props["desc"],
                "field_capacity": props["fc"],
                "wilting_point": props["wp"],
                "available_water_mm_m": tam,
                "max_infiltration_rate": props["inf"],
                # Grain fractions are unknown for district fallbacks; return null
                "sand_pct": None,
                "silt_pct": None,
                "clay_pct": None,
                "source": f"NISR District Baseline ({district})",
                "isAuto": True,
            }

    # 3. Final Fallback: Standard Loam (NOT cached)
    default_props = USDA_PROPERTIES["Loam"]
    return {
        "name": "Loam",
        "texture": "Loam",
        "description": default_props["desc"],
        "field_capacity": default_props["fc"],
        "wilting_point": default_props["wp"],
        "available_water_mm_m": 170,
        "max_infiltration_rate": default_props["inf"],
        # No measured fractions for generic default
        "sand_pct": None,
        "silt_pct": None,
        "clay_pct": None,
        "source": "Standard Agronomic Default",
        "isAuto": True,
    }
