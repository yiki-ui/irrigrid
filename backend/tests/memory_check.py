#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory & Execution Time Profiler for IrriGrid
Measures peak RSS and execution time across field sizes (0.35, 2.5, 10, 50 ha).
"""

import os
import sys
import time
import math
import resource
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

def get_peak_mb() -> float:
    # ru_maxrss is in KB on Linux
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

# 1. Measure baseline memory immediately after importing backend modules
t_start = time.time()
peak_startup_before = get_peak_mb()

from backend.core.optimizer import optimize_irrigation_system
from backend.core.pdf_export import generate_irrigation_pdf
import backend.main

peak_startup_after = get_peak_mb()

print("=" * 70)
print(f"BASELINE STARTUP PEAK MEMORY: {peak_startup_after:.2f} MB (pre-import: {peak_startup_before:.2f} MB)")
print("=" * 70)

# Full 12-month climate dataset
SAMPLE_CLIMATE = [
    {"month": "Jan", "tmin": 13.5, "tmax": 24.2, "rhmax": 82, "wind_speed": 1.8, "eto": 3.8},
    {"month": "Feb", "tmin": 13.8, "tmax": 24.8, "rhmax": 80, "wind_speed": 1.9, "eto": 4.1},
    {"month": "Mar", "tmin": 14.2, "tmax": 24.5, "rhmax": 85, "wind_speed": 1.7, "eto": 3.9},
    {"month": "Apr", "tmin": 14.5, "tmax": 23.8, "rhmax": 88, "wind_speed": 1.5, "eto": 3.5},
    {"month": "May", "tmin": 14.0, "tmax": 23.5, "rhmax": 86, "wind_speed": 1.6, "eto": 3.4},
    {"month": "Jun", "tmin": 12.8, "tmax": 24.1, "rhmax": 78, "wind_speed": 1.8, "eto": 3.7},
    {"month": "Jul", "tmin": 12.2, "tmax": 24.6, "rhmax": 75, "wind_speed": 2.0, "eto": 3.9},
    {"month": "Aug", "tmin": 13.1, "tmax": 25.2, "rhmax": 76, "wind_speed": 2.1, "eto": 4.2},
    {"month": "Sep", "tmin": 13.7, "tmax": 24.7, "rhmax": 81, "wind_speed": 1.9, "eto": 4.0},
    {"month": "Oct", "tmin": 14.0, "tmax": 24.0, "rhmax": 85, "wind_speed": 1.7, "eto": 3.7},
    {"month": "Nov", "tmin": 13.9, "tmax": 23.6, "rhmax": 87, "wind_speed": 1.6, "eto": 3.5},
    {"month": "Dec", "tmin": 13.6, "tmax": 23.9, "rhmax": 84, "wind_speed": 1.7, "eto": 3.6},
]

SAMPLE_SOIL = {
    "source": "ISRIC SoilGrids v2.0",
    "name": "Clay Loam",
    "field_capacity": 35.0,
    "wilting_point": 18.0,
    "available_water_mm_m": 170,
    "max_infiltration_rate": 8.0,
    "sand_pct": 28.5,
    "silt_pct": 40.2,
    "clay_pct": 31.3,
}

SAMPLE_WATER_BALANCE = [
    {"month": m["month"], "eto_mm": m["eto"], "kc": 1.0, "etc_mm": m["eto"] * 30, "rainfall_mm": 80, "net_irrigation_mm": max(0, m["eto"] * 30 - 56)}
    for m in SAMPLE_CLIMATE
]

SAMPLE_SCHEDULE = {
    "intervalDays": 3,
    "appNetMm": 15.5,
    "appGrossMm": 17.2,
    "durationHrs": 1.65,
}

def make_square_polygon(area_ha: float):
    # Area in m2
    area_m2 = area_ha * 10000.0
    side_m = math.sqrt(area_m2)
    lat0, lon0 = -1.50, 29.63
    dlat = side_m / 111320.0
    dlon = side_m / (111320.0 * math.cos(math.radians(lat0)))
    return [
        [lat0, lon0],
        [lat0, lon0 + dlon],
        [lat0 - dlat, lon0 + dlon],
        [lat0 - dlat, lon0],
        [lat0, lon0],
    ]

FIELD_SIZES = [0.35, 2.5, 10.0, 50.0]
RUNS_PER_SIZE = 5

print(f"{'Area (ha)':<10} | {'Run':<5} | {'Time (s)':<10} | {'Peak (MB)':<12} | {'PDF Size (KB)':<14}")
print("-" * 60)

for area in FIELD_SIZES:
    poly = make_square_polygon(area)
    side_m = math.sqrt(area * 10000.0)
    for run_idx in range(1, RUNS_PER_SIZE + 1):
        t0 = time.time()
        
        # 1. Run optimization
        opt = optimize_irrigation_system(
            field_area_ha=area,
            slope_pct=2.0,
            crop_name="Tomato",
            min_eu_threshold=90.0,
        )
        
        # 2. Run PDF generation
        pdf_bytes = generate_irrigation_pdf(
            design_data=opt,
            crop_name="Tomato",
            field_area_ha=area,
            location_name="Musanze, Rwanda",
            soil_type=SAMPLE_SOIL["name"],
            polygon_coords=poly,
            climate_data=SAMPLE_CLIMATE,
            soil_detail=SAMPLE_SOIL,
            water_balance=SAMPLE_WATER_BALANCE,
            schedule_summary=SAMPLE_SCHEDULE,
        )
        
        elapsed = time.time() - t0
        peak_mb = get_peak_mb()
        pdf_kb = len(pdf_bytes) / 1024.0
        
        print(f"{area:<10.2f} | {run_idx:<5} | {elapsed:<10.3f} | {peak_mb:<12.2f} | {pdf_kb:<14.1f}")
        sys.stdout.flush()

print("=" * 60)
print(f"FINAL PEAK MEMORY: {get_peak_mb():.2f} MB")
print("=" * 60)
