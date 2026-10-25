#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Headless Validation Harness for Irrigation DSS
Runs 27 scenarios automatically: 3 field sizes × 3 slopes × 3 crops

For each scenario:
1. ETOCalculator → get ETo for Kigali climate data
2. CropWaterRequirement → get ETc, irrigation req
3. HydraulicDesign → get EU%, pipe sizes, cost RWF
4. Record all outputs to CSV, plus memory and timing profiles

Output:
- results/validation_results.csv
- results/validation_summary.txt
"""

import csv
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Third-party
import pandas as pd

# Import core modules (NO GUI IMPORTS - runs headless)
from src.core.eto_calculator import ETOCalculator
from src.core.crop_water_requirement import CropWaterRequirement
from src.hydraulic.design_calculator import HydraulicDesign, SystemDesign


# ============= KIGALI CLIMATE DATA =============
# Kigali, Rwanda: -1.9403°S, 29.8739°E, elevation 1567m
KIGALI_LATITUDE = -1.9403
KIGALI_ELEVATION = 1567  # meters

# Monthly climate data for Kigali (from src/models/climate_enhanced.py)
KIGALI_CLIMATE = [
    {"month": 1, "tmin": 15.5, "tmax": 27.0, "rhmin": 65, "rhmax": 85, "wind_speed": 2.5, "sunshine": 6.5},
    {"month": 2, "tmin": 15.8, "tmax": 27.5, "rhmin": 63, "rhmax": 83, "wind_speed": 2.6, "sunshine": 6.8},
    {"month": 3, "tmin": 16.0, "tmax": 27.2, "rhmin": 66, "rhmax": 86, "wind_speed": 2.4, "sunshine": 6.2},
    {"month": 4, "tmin": 16.2, "tmax": 26.8, "rhmin": 68, "rhmax": 88, "wind_speed": 2.3, "sunshine": 5.8},
    {"month": 5, "tmin": 16.0, "tmax": 26.5, "rhmin": 67, "rhmax": 87, "wind_speed": 2.25, "sunshine": 6.0},
    {"month": 6, "tmin": 15.2, "tmax": 27.8, "rhmin": 55, "rhmax": 75, "wind_speed": 2.7, "sunshine": 7.5},
    {"month": 7, "tmin": 14.8, "tmax": 28.5, "rhmin": 52, "rhmax": 72, "wind_speed": 2.75, "sunshine": 8.0},
    {"month": 8, "tmin": 15.0, "tmax": 28.8, "rhmin": 53, "rhmax": 73, "wind_speed": 2.8, "sunshine": 8.2},
    {"month": 9, "tmin": 15.5, "tmax": 28.2, "rhmin": 58, "rhmax": 78, "wind_speed": 2.6, "sunshine": 7.5},
    {"month": 10, "tmin": 15.8, "tmax": 27.5, "rhmin": 62, "rhmax": 82, "wind_speed": 2.5, "sunshine": 6.8},
    {"month": 11, "tmin": 15.6, "tmax": 26.8, "rhmin": 67, "rhmax": 87, "wind_speed": 2.4, "sunshine": 6.0},
    {"month": 12, "tmin": 15.4, "tmax": 26.5, "rhmin": 66, "rhmax": 86, "wind_speed": 2.4, "sunshine": 6.2},
]

# Monthly rainfall (mm) for Kigali
KIGALI_RAINFALL = [75, 90, 115, 150, 85, 15, 10, 25, 70, 95, 110, 85]


# ============= CROP Kc VALUES (FAO-56) =============
# Kc values for different crops (FAO-56 Table 12)
CROP_KC = {
    "tomato": {
        "kc_initial": 0.6,
        "kc_mid": 1.15,
        "kc_end": 0.8,
        "growth_stages": [25, 40, 45, 25],  # initial, mid, late, harvest
    },
    "bean": {
        "kc_initial": 0.5,
        "kc_mid": 1.10,
        "kc_end": 0.9,
        "growth_stages": [20, 30, 30, 15],  # bush bean
    },
    "onion": {
        "kc_initial": 0.7,
        "kc_mid": 1.05,
        "kc_end": 0.75,
        "growth_stages": [15, 25, 70, 40],
    },
}


# ============= CROPWAT REFERENCE ETc VALUES (mm/year) =============
# FAO-56 Table A4: Annual ETc values for Kigali region (tropical highland)
# These are ANNUAL TOTALS in mm (12 months of crop growth)
# Based on FAO-56 Table 12 (Kc values) × local ETo
CROPWAT_REFERENCE_ETC = {
    "tomato": 940,   # Annual total for continuous tomato cultivation
    "bean": 780,     # Annual total for continuous bean cultivation
    "onion": 1100,   # Annual total for continuous onion cultivation
}


# ============= SOIL PARAMETERS =============
# Default soil for Rwanda (Nitisols/Loam)
SOIL_TYPE = "Loam"
SOIL_AVAILABLE_WATER = 0.17  # mm/mm


def calculate_eTo_monthly() -> list:
    """Calculate monthly ETo for Kigali using FAO-56 Penman-Monteith"""
    eto_monthly = []

    for i, climate in enumerate(KIGALI_CLIMATE):
        day_of_year = 15 + i * 30

        eto = ETOCalculator.calculate_eto(
            tmin=climate["tmin"],
            tmax=climate["tmax"],
            rhmin=climate["rhmin"],
            rhmax=climate["rhmax"],
            wind_speed=climate["wind_speed"],
            sunshine_hours=climate["sunshine"],
            latitude=KIGALI_LATITUDE,
            elevation=KIGALI_ELEVATION,
            day_of_year=day_of_year
        )
        eto_monthly.append(round(eto, 2))

    return eto_monthly


def _monthly_from_annual(total_annual: float, eto_monthly: list) -> list:
    """
    Derive monthly reference ETc (mm/month) from an annual total by
    distributing proportionally to monthly ETo. Standard academic
    approximation when only CROPWAT seasonal totals are available.
    """
    s = sum(eto_monthly)
    return [round(total_annual * (e / s), 2) if s > 0 else 0.0 for e in eto_monthly]


def get_crop_kc_values(crop_name: str, growing_season_length: int = 120) -> list:
    """
    Generate Kc values for entire crop growing season
    Interpolates between initial, mid, and end Kc values
    """
    crop_data = CROP_KC[crop_name.lower()]
    kc_initial = crop_data["kc_initial"]
    kc_mid = crop_data["kc_mid"]
    kc_end = crop_data["kc_end"]
    stages = crop_data["growth_stages"]

    kc_values = []

    # Initial stage
    for _ in range(stages[0]):
        kc_values.append(kc_initial)

    # Development stage (linear increase to mid)
    dev_days = stages[1]
    for i in range(dev_days):
        kc = kc_initial + (kc_mid - kc_initial) * (i + 1) / dev_days
        kc_values.append(round(kc, 2))

    # Mid stage
    for _ in range(stages[2]):
        kc_values.append(kc_mid)

    # Late stage (decrease to end)
    late_days = stages[3]
    for i in range(late_days):
        kc = kc_mid + (kc_end - kc_mid) * (i + 1) / late_days
        kc_values.append(round(kc, 2))

    return kc_values[:growing_season_length]


def calculate_crop_water_requirement(crop_name: str, eto_monthly: list) -> dict:
    """
    Calculate crop water requirements using CropWaterRequirement
    Returns ETc and irrigation requirement
    """
    kc_values = get_crop_kc_values(crop_name, len(eto_monthly))

    if len(kc_values) < len(eto_monthly):
        kc_values.extend([kc_values[-1]] * (len(eto_monthly) - len(kc_values)))
    elif len(kc_values) > len(eto_monthly):
        kc_values = kc_values[:len(eto_monthly)]

    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    eto_monthly_totals = [eto * days for eto, days in zip(eto_monthly, days_per_month)]

    effective_rainfall = [rain * 0.80 for rain in KIGALI_RAINFALL]

    crop_water = CropWaterRequirement(
        eto_data=eto_monthly_totals,  # Monthly totals now
        kc_values=kc_values,
        rainfall=KIGALI_RAINFALL,
        effective_rain=effective_rainfall
    )

    etc_values = crop_water.calculate_etc()
    total_etc = sum(etc_values)
    avg_etc = sum(etc_values) / len(etc_values)

    irrigation_values = crop_water.calculate_irrigation_requirement()
    total_irrigation = sum(irrigation_values)

    return {
        "etc_values": etc_values,
        "total_etc": round(total_etc, 2),
        "avg_etc": round(avg_etc, 2),
        "total_irrigation": round(total_irrigation, 2),
    }


def calculate_hydraulic_design(
    field_area_ha: float,
    slope_pct: float,
    crop_name: str,
    irrigation_req_mm: float
) -> dict:
    """
    Calculate hydraulic design using Hazen-Williams method
    Returns EU%, pipe sizes, and cost
    """
    field_side = (field_area_ha * 10000) ** 0.5  # meters

    if slope_pct <= 1:
        emitter_spacing = 0.3
        lateral_spacing = 1.8
    elif slope_pct <= 3:
        emitter_spacing = 0.3
        lateral_spacing = 1.5
    else:
        emitter_spacing = 0.25
        lateral_spacing = 1.2

    base_emitter_flow = 2.0
    if slope_pct > 3:
        emitter_flow = 1.5
    else:
        emitter_flow = base_emitter_flow

    if slope_pct <= 1:
        operating_pressure = 1.5
    elif slope_pct <= 3:
        operating_pressure = 2.0
    else:
        operating_pressure = 2.5

    design = SystemDesign(
        field_area=field_area_ha,
        field_length=field_side,
        field_width=field_side,
        crop_name=crop_name,
        soil_type=SOIL_TYPE,
        emitter_flow=emitter_flow,
        emitter_spacing=emitter_spacing,
        lateral_spacing=lateral_spacing,
        operating_pressure=operating_pressure,
        slope_percent=slope_pct,
        slope_direction='downhill',
    )

    hydraulic = HydraulicDesign(design)
    results = hydraulic.calculate_complete_system()

    eu_percent = results['uniformity']['emission_uniformity_percent']
    lateral_diameter = results['pipes']['lateral_diameter_mm']
    main_diameter = results['pipes']['main_diameter_mm']
    total_cost = results['costs']['total_rwf']

    return {
        "eu_percent": round(eu_percent, 2),
        "lateral_diameter_mm": lateral_diameter,
        "main_diameter_mm": main_diameter,
        "total_cost_rwf": round(total_cost, 0),
    }


def run_scenario(scenario_id: int, field_size_ha: float, slope_pct: float,
                 crop: str, eto_monthly: list) -> dict:
    """Run a single scenario and return results with profiling data"""
    tracemalloc.reset_peak()
    tracemalloc.start()
    start_time = time.perf_counter()

    water_req = calculate_crop_water_requirement(crop, eto_monthly)

    hydraulic = calculate_hydraulic_design(
        field_area_ha=field_size_ha,
        slope_pct=slope_pct,
        crop_name=crop,
        irrigation_req_mm=water_req['total_irrigation']
    )

    end_time = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    processing_time = end_time - start_time

    avg_eto = sum(eto_monthly) / len(eto_monthly)

    return {
        "scenario_id": scenario_id,
        "field_size_ha": field_size_ha,
        "slope_pct": slope_pct,
        "crop": crop,
        "eto_mm": round(avg_eto, 2),
        "etc_mm": water_req["total_etc"],
        "irrigation_req_mm": water_req["total_irrigation"],
        "eu_percent": hydraulic["eu_percent"],
        "pipe_diameter_mm": hydraulic["lateral_diameter_mm"],
        "total_cost_rwf": hydraulic["total_cost_rwf"],
        "processing_time_seconds": round(processing_time, 6),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
    }


def calculate_rmse(scenarios: list, reference_etc: dict) -> float:
    """
    Calculate Root Mean Square Error (RMSE) over all scenarios.
    Each scenario's calculated annual ETc is compared to the reference annual ETc
    for its crop.
    """
    squared_errors = []
    for s in scenarios:
        crop = s["crop"]
        if crop in reference_etc:
            ref = reference_etc[crop]
            calc = s["etc_mm"]
            if ref > 0:
                squared_errors.append((calc - ref) ** 2)
    if not squared_errors:
        return 0.0
    return round((sum(squared_errors) / len(squared_errors)) ** 0.5, 4)


def calculate_mape(scenarios: list, reference_etc: dict) -> float:
    """
    Calculate Mean Absolute Percentage Error (MAPE) over all scenarios.
    Each scenario's calculated annual ETc is compared to the reference annual ETc
    for its crop.
    """
    errors = []
    for s in scenarios:
        crop = s["crop"]
        if crop in reference_etc:
            ref = reference_etc[crop]
            calc = s["etc_mm"]
            if ref > 0:
                errors.append(abs(calc - ref) / ref * 100)
    return round(sum(errors) / len(errors), 2) if errors else 0.0


def main():
    """Main validation runner"""
    print("=" * 60)
    print("IRRIGATION DSS VALIDATION HARNESS")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    field_sizes = [0.10, 0.25, 0.50]
    slopes = [0, 2, 5]
    crops = ["tomato", "bean", "onion"]

    print("Calculating ETo for Kigali climate...")
    eto_monthly = calculate_eTo_monthly()
    print(f"Monthly ETo values: {eto_monthly}")
    print()

    scenarios = []
    scenario_id = 1

    print("Running 27 scenarios...")
    print("-" * 60)

    for field_size in field_sizes:
        for slope in slopes:
            for crop in crops:
                print(f"Scenario {scenario_id:2d}: {crop:6s}, {field_size:.2f}ha, {slope}% slope")

                result = run_scenario(
                    scenario_id=scenario_id,
                    field_size_ha=field_size,
                    slope_pct=slope,
                    crop=crop,
                    eto_monthly=eto_monthly,
                )

                scenarios.append(result)
                scenario_id += 1

    print("-" * 60)
    print()

    # Write CSV results
    csv_path = results_dir / "validation_results.csv"
    fieldnames = [
        "scenario_id", "field_size_ha", "slope_pct", "crop",
        "eto_mm", "etc_mm", "irrigation_req_mm",
        "eu_percent", "pipe_diameter_mm", "total_cost_rwf",
        "processing_time_seconds", "peak_memory_mb",
    ]

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scenarios)

    print(f"CSV results saved to: {csv_path}")

    # ----- Pandas Summary -----
    df = pd.DataFrame(scenarios)

    rmse_total = calculate_rmse(scenarios, CROPWAT_REFERENCE_ETC)
    mape_total = calculate_mape(scenarios, CROPWAT_REFERENCE_ETC)

    # Per-crop aggregate
    crop_means = {}
    crop_mape = {}
    for crop in crops:
        crop_df = df[df["crop"] == crop]
        crop_means[crop] = round(crop_df["etc_mm"].mean(), 2)
        ref = CROPWAT_REFERENCE_ETC[crop]
        if ref > 0:
            crop_mape[crop] = round(abs(crop_means[crop] - ref) / ref * 100, 2)
        else:
            crop_mape[crop] = 0.0

    summary_path = results_dir / "validation_summary.txt"

    with open(summary_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("IRRIGATION DSS VALIDATION SUMMARY\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: Kigali, Rwanda ({KIGALI_LATITUDE}°S, {KIGALI_ELEVATION}m)\n")
        f.write(f"Total Scenarios: {len(scenarios)}\n")
        f.write("\n")

        f.write("SCENARIO PARAMETERS:\n")
        f.write(f"  Field Sizes: {field_sizes} ha\n")
        f.write(f"  Slopes: {slopes} %\n")
        f.write(f"  Crops: {crops}\n")
        f.write("\n")

        f.write("-" * 60 + "\n")
        f.write("RESULTS SUMMARY (Pandas-generated)\n")
        f.write("-" * 60 + "\n")

        summary_stats = df[["eu_percent", "total_cost_rwf", "processing_time_seconds", "peak_memory_mb"]].describe()
        f.write(summary_stats.to_string())
        f.write("\n\n")

        f.write(f"Mean EU% across all scenarios: {df['eu_percent'].mean():.2f}%\n")
        f.write(f"Std  EU% across all scenarios: {df['eu_percent'].std():.2f}%\n")
        f.write(f"Min  EU% across all scenarios: {df['eu_percent'].min():.2f}%\n")
        f.write(f"Max  EU% across all scenarios: {df['eu_percent'].max():.2f}%\n")
        f.write(f"Mean peak memory usage: {df['peak_memory_mb'].mean():.3f} MB\n")
        f.write(f"Max peak memory usage: {df['peak_memory_mb'].max():.3f} MB\n")
        f.write(f"Mean processing time per scenario: {df['processing_time_seconds'].mean():.6f} seconds\n")
        f.write("\n")

        failures = df[df["eu_percent"] < 90]
        f.write(f"Scenarios with EU < 90% (FAILURES): {len(failures)}\n")
        if not failures.empty:
            f.write("\nFailure Details:\n")
            for _, fail in failures.iterrows():
                f.write(f"  - Scenario {fail['scenario_id']}: {fail['crop']}, "
                        f"{fail['field_size_ha']}ha, {fail['slope_pct']}% slope, "
                        f"EU = {fail['eu_percent']}%\n")
        else:
            f.write("  All scenarios meet EU >= 90% requirement\n")
        f.write("\n")

        f.write("RMSE vs CROPWAT Reference (E<sub>tc</sub> annual, mm/year):\n")
        f.write(f"  Overall RMSE: {rmse_total} mm/year\n")
        for crop in crops:
            f.write(f"  {crop.capitalize()}: {crop_means[crop]} mm/year (ref {CROPWAT_REFERENCE_ETC[crop]})\n")
        f.write("\n")

        f.write("MAPE vs CROPWAT Reference (E<sub>tc</sub> annual, %):\n")
        f.write(f"  Overall MAPE: {mape_total}%\n")
        for crop, mape in crop_mape.items():
            f.write(f"  {crop.capitalize()}: {mape}%\n")
        f.write("\n")

        f.write("-" * 60 + "\n")
        f.write("SCENARIO RESULTS TABLE\n")
        f.write("-" * 60 + "\n")

        f.write(f"{'ID':<3} {'Crop':<7} {'Size':<6} {'Slope':<6} {'ETo':<6} {'ETc':<7} "
                f"{'IrrReq':<8} {'EU%':<6} {'Pipe':<5} {'Cost(RWF)':<12} {'Time(s)':<10} {'Mem(MB)':<8}\n")
        f.write("-" * 110 + "\n")

        for _, s in df.iterrows():
            f.write(f"{s['scenario_id']:<3} {s['crop']:<7} {s['field_size_ha']:<6} "
                    f"{s['slope_pct']:<6} {s['eto_mm']:<6} {s['etc_mm']:<7} "
                    f"{s['irrigation_req_mm']:<8} {s['eu_percent']:<6} "
                    f"{s['pipe_diameter_mm']:<5} {s['total_cost_rwf']:<12.0f} "
                    f"{s['processing_time_seconds']:<10.6f} {s['peak_memory_mb']:<8.3f}\n")

        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write("VALIDATION COMPLETE\n")
        f.write("=" * 60 + "\n")

    print(f"Summary saved to: {summary_path}")
    print()
    print("=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print(f"Mean EU%: {df['eu_percent'].mean():.2f}%")
    print(f"Failures (EU < 90%): {len(failures)}")
    print(f"Mean processing time: {df['processing_time_seconds'].mean():.6f}s")
    print(f"Overall RMSE vs CROPWAT: {rmse_total} mm/year")
    print(f"Overall MAPE vs CROPWAT: {mape_total}%")
    print(f"Peak memory (mean): {df['peak_memory_mb'].mean():.3f} MB")
    print()

    return scenarios


if __name__ == "__main__":
    main()
