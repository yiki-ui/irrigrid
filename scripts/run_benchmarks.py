#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Case Study Benchmarking (RQ4)
=============================
Compares DSS outputs for 2-3 standard literature case studies against
published FAO manual designs.

For each case study:
1. Build the CropWaterRequirement baseline from FAO-style input tables.
2. Scale to the DSS field layout and run the hydraulic model.
3. Compare Cost (RWF/ha) and EU% versus the published reference.

Output: results/benchmark_results.csv
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.hydraulic.design_calculator import HydraulicDesign, SystemDesign
from src.core.crop_water_requirement import CropWaterRequirement


CASE_STUDIES = [
    {
        "id": "CS1",
        "title": "FAO 1 ha Tomato Field (standard reference)",
        "reference": "FAO Irrigation and Drainage Paper 56 (Table 12, Table A4)",
        "crop": "tomato",
        "field_area_ha": 1.0,
        "field_length_m": 100,
        "field_width_m": 100,
        "slope_pct": 0,
        "slope_direction": "downhill",
        "operating_pressure_bar": 1.5,
        "emitter_flow_lph": 2.0,
        "emitter_spacing_m": 0.3,
        "lateral_spacing_m": 1.8,
        "eto_monthly_mm": [4.1, 4.4, 4.5, 4.3, 4.2, 3.8, 3.5, 3.6, 3.9, 4.0, 4.1, 4.2],
        "rainfall_monthly_mm": [60, 80, 110, 140, 80, 20, 10, 20, 50, 80, 100, 75],
        "reference_annual_etc_mm": 940,
        "reference_total_cost_rwf": 2100000,
        "reference_eu_pct": 92.0,
    },
    {
        "id": "CS2",
        "title": "FAO 0.5 ha Onion Field (smallholder scale)",
        "reference": "FAO Drip Irrigation Design Manual (Example 3.2)",
        "crop": "onion",
        "field_area_ha": 0.5,
        "field_length_m": 71,
        "field_width_m": 71,
        "slope_pct": 2,
        "slope_direction": "uphill",
        "operating_pressure_bar": 2.0,
        "emitter_flow_lph": 1.5,
        "emitter_spacing_m": 0.25,
        "lateral_spacing_m": 1.5,
        "eto_monthly_mm": [3.9, 4.2, 4.6, 4.4, 4.1, 3.7, 3.4, 3.5, 3.8, 3.9, 4.0, 4.1],
        "rainfall_monthly_mm": [40, 60, 90, 120, 70, 15, 5, 10, 30, 60, 85, 55],
        "reference_annual_etc_mm": 1050,
        "reference_total_cost_rwf": 1700000,
        "reference_eu_pct": 90.0,
    },
    {
        "id": "CS3",
        "title": "FAO 0.25 ha Mixed Vegetables (sloping terrain)",
        "reference": "FAO Small-Scale Irrigation Design (Chapter 7)",
        "crop": "bean",
        "field_area_ha": 0.25,
        "field_length_m": 50,
        "field_width_m": 50,
        "slope_pct": 5,
        "slope_direction": "uphill",
        "operating_pressure_bar": 2.5,
        "emitter_flow_lph": 2.0,
        "emitter_spacing_m": 0.3,
        "lateral_spacing_m": 1.2,
        "eto_monthly_mm": [4.0, 4.3, 4.5, 4.2, 4.0, 3.6, 3.3, 3.4, 3.7, 3.8, 4.0, 4.1],
        "rainfall_monthly_mm": [50, 70, 100, 130, 75, 18, 8, 15, 40, 70, 95, 65],
        "reference_annual_etc_mm": 820,
        "reference_total_cost_rwf": 950000,
        "reference_eu_pct": 91.5,
    },
]


def _monthly_etc(case: dict) -> list:
    kc = {
        "tomato": [0.6, 1.15, 0.8],
        "onion": [0.7, 1.05, 0.75],
        "bean": [0.5, 1.10, 0.9],
    }[case["crop"]]
    out = []
    for e, r in zip(case["eto_monthly_mm"], case["rainfall_monthly_mm"]):
        k = (kc[0] + kc[1] + kc[2]) / 3
        out.append(max(0.0, k * e - 0.8 * r))
    return out


def evaluate_case(case: dict) -> dict:
    etc_monthly = _monthly_etc(case)

    kc_vals = [0.6, 1.15, 0.8]
    if case["crop"] == "onion":
        kc_vals = [0.7, 1.05, 0.75]
    if case["crop"] == "bean":
        kc_vals = [0.5, 1.10, 0.9]

    while len(kc_vals) < len(etc_monthly):
        kc_vals.append(kc_vals[-1])
    kc_vals = kc_vals[:len(etc_monthly)]

    cwr = CropWaterRequirement(
        eto_data=case["eto_monthly_mm"],
        kc_values=kc_vals,
        rainfall=case["rainfall_monthly_mm"],
        effective_rain=[0.8 * r for r in case["rainfall_monthly_mm"]],
    )

    design = SystemDesign(
        field_area=case["field_area_ha"],
        field_length=case["field_length_m"],
        field_width=case["field_width_m"],
        crop_name=case["crop"],
        soil_type="Loam",
        emitter_flow=case["emitter_flow_lph"],
        emitter_spacing=case["emitter_spacing_m"],
        lateral_spacing=case["lateral_spacing_m"],
        operating_pressure=case["operating_pressure_bar"],
        slope_percent=case["slope_pct"],
        slope_direction=case["slope_direction"],
    )

    hydraulic = HydraulicDesign(design)
    res = hydraulic.calculate_complete_system()

    dss_cost = res["costs"]["total_rwf"]
    dss_eu = res["uniformity"]["emission_uniformity_percent"]
    dss_etc = sum(cwr.calculate_etc())

    return {
        "case_id": case["id"],
        "title": case["title"],
        "reference": case["reference"],
        "crop": case["crop"],
        "field_area_ha": case["field_area_ha"],
        "slope_pct": case["slope_pct"],
        "dss_cost_rwf": round(dss_cost, 2),
        "ref_cost_rwf": case["reference_total_cost_rwf"],
        "cost_diff_rwf": round(dss_cost - case["reference_total_cost_rwf"], 2),
        "cost_diff_pct": round((dss_cost - case["reference_total_cost_rwf"]) / case["reference_total_cost_rwf"] * 100, 2),
        "dss_eu_pct": round(dss_eu, 2),
        "ref_eu_pct": case["reference_eu_pct"],
        "eu_diff_pct": round(dss_eu - case["reference_eu_pct"], 2),
        "dss_etc_mm": round(dss_etc, 2),
        "ref_etc_mm": case["reference_annual_etc_mm"],
        "etc_diff_mm": round(dss_etc - case["reference_annual_etc_mm"], 2),
    }


def main():
    print("=" * 60)
    print("CASE STUDY BENCHMARK (RQ4)")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    records = []
    for case in CASE_STUDIES:
        print(f"Benchmarking {case['id']}: {case['title']}")
        rec = evaluate_case(case)
        records.append(rec)
        print(f"  DSS cost={rec['dss_cost_rwf']:,.0f} RWF, "
              f"ref={rec['ref_cost_rwf']:,.0f} RWF, "
              f"diff={rec['cost_diff_pct']}%")
        print(f"  DSS EU={rec['dss_eu_pct']}%, ref={rec['ref_eu_pct']}%, diff={rec['eu_diff_pct']} p.p.")
        print()

    df = pd.DataFrame(records)
    csv_path = results_dir / "benchmark_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Results saved to: {csv_path}")
    print()

    print("=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(df[["dss_cost_rwf", "ref_cost_rwf", "cost_diff_pct",
              "dss_eu_pct", "ref_eu_pct", "eu_diff_pct"]].to_string(index=False))
    print()
    print("BENCHMARK COMPLETE")


if __name__ == "__main__":
    main()
