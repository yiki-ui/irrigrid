#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Core Optimizer — Polygon-Aware Hydraulic Design
Uses real polygon layout geometry (from field_layout.py) to size pipes,
compute zones, and generate an accurate BOM.
"""

import math
import time
from typing import Dict, List, Optional

# Pipe catalog & prices (RWF per meter or unit)
ALLOWED_LATERALS = [16.0, 20.0, 25.0]  # mm outer diameter
ALLOWED_MAINS = [32.0, 40.0, 50.0, 63.0, 75.0, 90.0]  # mm outer diameter
ALLOWED_EMITTER_SPACING = [0.20, 0.30, 0.40, 0.50]  # m
ALLOWED_LATERAL_SPACING = [0.80, 1.00, 1.20, 1.50]  # m
ALLOWED_EMITTER_FLOW = [1.0, 1.6, 2.0, 2.5]  # L/hr

PIPE_COST_PER_METER = {
    16.0: 150, 20.0: 200, 25.0: 300, 32.0: 500,
    40.0: 800, 50.0: 1200, 63.0: 1800, 75.0: 2500, 90.0: 3200,
}

# Standard inner diameters (OD minus wall thickness)
PIPE_ID_MM = {
    16.0: 14.0, 20.0: 17.0, 25.0: 22.0, 32.0: 29.0,
    40.0: 37.0, 50.0: 46.0, 63.0: 58.0, 75.0: 69.0, 90.0: 83.0,
}

DAILY_PUMPING_WINDOW_H = 12.0  # max hours a smallholder can pump per day
PUMP_EFFICIENCY = 0.65
FILTER_HEAD_LOSS_M = 3.0  # screen/disc filter
OPERATING_PRESSURE_BAR = 1.0
C_HAZEN_WILLIAMS = 150.0  # PE/PVC pipe


def christiansen_f_factor(num_outlets: int, m: float = 1.85) -> float:
    """Christiansen reduction factor F for multiple-outlet pipelines."""
    n = max(1, num_outlets)
    return (1.0 / (m + 1.0)) + (1.0 / (2.0 * n)) + (math.sqrt(m - 1.0) / (6.0 * (n ** 2)))


def hazen_williams_head_loss(length_m: float, flow_m3s: float, id_mm: float,
                              c: float = 150.0) -> float:
    """Hazen-Williams friction head loss in metres."""
    d_m = id_mm / 1000.0
    if d_m < 0.001 or flow_m3s < 1e-10:
        return 0.0
    return 10.67 * length_m * (flow_m3s ** 1.85) / ((c ** 1.85) * (d_m ** 4.87))


def select_mainline_diameter(flow_m3s: float, max_velocity: float = 1.5) -> float:
    """Pick smallest standard OD where velocity <= max_velocity."""
    for od in sorted(ALLOWED_MAINS):
        id_m = PIPE_ID_MM[od] / 1000.0
        area = math.pi * (id_m / 2.0) ** 2
        v = flow_m3s / area if area > 0 else 999
        if v <= max_velocity:
            return od
    return max(ALLOWED_MAINS)  # largest available


def evaluate_hydraulic_configuration(
    field_length: float,
    field_width: float,
    slope_pct: float,
    lateral_d_mm: float,
    main_d_mm: float,
    emitter_sp_m: float,
    lateral_sp_m: float,
    emitter_q_lph: float,
) -> Dict:
    """Evaluate one hydraulic configuration with square field approximation (backward compatible)."""
    num_laterals = max(1, int(round(field_width / lateral_sp_m)))
    emitters_per_lat = max(1, int(round(field_length / emitter_sp_m)))
    total_emitters = num_laterals * emitters_per_lat
    return evaluate_design(
        num_laterals=num_laterals,
        total_emitters=total_emitters,
        max_lateral_length_m=field_length,
        mainline_length_m=field_width,
        total_lateral_m=num_laterals * field_length,
        lateral_d_mm=lateral_d_mm,
        emitter_sp_m=emitter_sp_m,
        lateral_sp_m=lateral_sp_m,
        emitter_q_lph=emitter_q_lph,
        slope_pct=slope_pct,
    )


def evaluate_design(
    # Real polygon geometry (from compute_field_layout)
    num_laterals: int,
    total_emitters: int,
    max_lateral_length_m: float,
    mainline_length_m: float,
    total_lateral_m: float,
    # Design parameters
    lateral_d_mm: float,
    emitter_sp_m: float,
    lateral_sp_m: float,
    emitter_q_lph: float,
    slope_pct: float = 0.0,
) -> Dict:
    """
    Evaluate one hydraulic configuration using real polygon geometry.
    Returns metrics dict with EU, UC, zones, TDH breakdown, pump power, BOM.
    """
    # --- Flow rates ---
    q_emitter_m3s = (emitter_q_lph / 1000.0) / 3600.0
    emitters_per_max_lateral = max(1, int(round(max_lateral_length_m / emitter_sp_m)))
    q_lateral_m3s = q_emitter_m3s * emitters_per_max_lateral  # worst-case lateral
    q_total_m3s = q_emitter_m3s * total_emitters
    q_total_m3h = q_total_m3s * 3600.0

    # --- Application rate & run time ---
    # Ia = emitter flow / (emitter spacing x lateral spacing)  [mm/h]
    application_rate_mmh = emitter_q_lph / (emitter_sp_m * lateral_sp_m)

    # --- Lateral friction (Hazen-Williams with Christiansen F) ---
    lat_id_mm = PIPE_ID_MM.get(lateral_d_mm, lateral_d_mm - 2.0)
    f_lat = christiansen_f_factor(emitters_per_max_lateral)
    hf_lat_friction = f_lat * hazen_williams_head_loss(
        max_lateral_length_m, q_lateral_m3s, lat_id_mm, C_HAZEN_WILLIAMS
    )

    # Elevation along lateral
    dz_lateral = max_lateral_length_m * (slope_pct / 100.0)
    hf_lat_total = hf_lat_friction + dz_lateral

    # --- Pressure variation → EU and UC ---
    p_operating_m = OPERATING_PRESSURE_BAR * 10.2  # bar → metres head
    p_inlet_m = p_operating_m + hf_lat_total  # inlet must overcome friction + elevation
    p_outlet_m = max(0.1, p_operating_m)  # end of lateral at operating pressure

    # Emitter discharge q = k * P^0.5
    q_at_inlet = emitter_q_lph * ((p_inlet_m / p_operating_m) ** 0.5) if p_operating_m > 0 else emitter_q_lph
    q_at_outlet = emitter_q_lph  # at design operating pressure
    q_min = min(q_at_inlet, q_at_outlet)
    q_max = max(q_at_inlet, q_at_outlet)
    q_avg = (q_min + q_max) / 2.0

    # Keller-Karmeli EU: EU = 100 * q_min / q_avg
    eu_pct = (q_min / q_avg) * 100.0 if q_avg > 0 else 0.0

    # Christiansen UC: UC = 100 * (1 - Σ|qi - q̄| / (n·q̄))
    # For uniform distribution between q_min and q_max:
    # mean absolute deviation = (q_max - q_min) / 4
    if q_avg > 0:
        mad = (q_max - q_min) / 4.0
        uc_pct = (1.0 - mad / q_avg) * 100.0
    else:
        uc_pct = 0.0

    # --- Zones ---
    # We need gross depth to compute run time, but gross depth depends on
    # the schedule (RAW / system_eff). Use a representative value here.
    # The PDF will show the actual computed run time from the water balance.
    # For optimizer ranking, estimate with a typical gross depth of 20 mm.
    est_gross_depth_mm = 20.0
    run_time_h = est_gross_depth_mm / application_rate_mmh if application_rate_mmh > 0 else 1.0

    # Number of zones: fit within daily pumping window
    if run_time_h > 0:
        max_zones = max(1, int(DAILY_PUMPING_WINDOW_H / run_time_h))
    else:
        max_zones = 1

    # Also limit zone flow to ~15 m³/h for smallholder pump sizing
    min_zones_for_flow = max(1, math.ceil(q_total_m3h / 15.0))
    n_zones = max(1, min(max_zones, min_zones_for_flow))

    # If total field can run in one zone within the window, use 1 zone
    if q_total_m3h <= 15.0 and run_time_h <= DAILY_PUMPING_WINDOW_H:
        n_zones = 1

    q_zone_m3h = q_total_m3h / n_zones
    q_zone_m3s = q_zone_m3h / 3600.0

    # --- Mainline sizing (based on zone flow, v <= 1.5 m/s) ---
    main_d_mm = select_mainline_diameter(q_zone_m3s, max_velocity=1.5)
    main_id_mm = PIPE_ID_MM[main_d_mm]
    main_id_m = main_id_mm / 1000.0
    main_area = math.pi * (main_id_m / 2.0) ** 2
    main_velocity = q_zone_m3s / main_area if main_area > 0 else 0.0

    # Mainline head loss (Hazen-Williams, no Christiansen F — single outlet)
    laterals_per_zone = max(1, num_laterals // n_zones)
    f_main = christiansen_f_factor(laterals_per_zone)
    hf_main = f_main * hazen_williams_head_loss(
        mainline_length_m, q_zone_m3s, main_id_mm, C_HAZEN_WILLIAMS
    )

    # --- TDH breakdown ---
    hf_elevation = max_lateral_length_m * (slope_pct / 100.0)
    tdh_m = p_operating_m + hf_lat_friction + hf_main + FILTER_HEAD_LOSS_M + hf_elevation
    tdh_breakdown = {
        "operating_pressure_m": round(p_operating_m, 2),
        "lateral_friction_m": round(hf_lat_friction, 2),
        "mainline_friction_m": round(hf_main, 2),
        "filter_loss_m": FILTER_HEAD_LOSS_M,
        "elevation_head_m": round(hf_elevation, 2),
        "total_dynamic_head_m": round(tdh_m, 2),
    }

    # --- Pump power: P = ρgQH / (η × 1000) ---
    pump_kw = (1000.0 * 9.81 * q_zone_m3s * tdh_m) / (PUMP_EFFICIENCY * 1000.0)
    pump_kw = max(0.37, pump_kw)  # minimum practical pump

    # --- BOM (uses real layout quantities) ---
    cost_lateral = int(total_lateral_m) * PIPE_COST_PER_METER.get(lateral_d_mm, 200)
    cost_main = int(mainline_length_m) * PIPE_COST_PER_METER.get(main_d_mm, 1000)
    cost_emitters = total_emitters * 50  # inline emitters ~50 RWF each
    cost_pump = 180000 + int(pump_kw * 120000)
    cost_filtration = 65000
    cost_fittings = 45000 + (num_laterals * 800)
    total_cost_rwf = cost_lateral + cost_main + cost_emitters + cost_pump + cost_filtration + cost_fittings

    bom = [
        {"item": f"{lateral_d_mm}mm Drip Lateral Pipe", "quantity": f"{int(total_lateral_m)} m", "cost_rwf": cost_lateral},
        {"item": f"{main_d_mm}mm HDPE Mainline", "quantity": f"{int(mainline_length_m)} m", "cost_rwf": cost_main},
        {"item": f"Inline Emitters ({emitter_q_lph} L/h)", "quantity": f"{total_emitters:,} units", "cost_rwf": cost_emitters},
        {"item": f"Irrigation Pump ({round(pump_kw, 2)} kW)", "quantity": "1 unit", "cost_rwf": cost_pump},
        {"item": "Screen / Disc Filter (120 mesh)", "quantity": "1 unit", "cost_rwf": cost_filtration},
        {"item": "Fittings, Valves & Connectors", "quantity": f"{num_laterals} lateral kits", "cost_rwf": cost_fittings},
    ]

    return {
        "lateral_diameter_mm": lateral_d_mm,
        "main_diameter_mm": main_d_mm,
        "emitter_spacing_m": emitter_sp_m,
        "lateral_spacing_m": lateral_sp_m,
        "emitter_flow_lph": emitter_q_lph,
        "num_laterals": num_laterals,
        "total_emitters": total_emitters,
        "max_lateral_length_m": round(max_lateral_length_m, 1),
        "mainline_length_m": round(mainline_length_m, 1),
        "total_lateral_m": round(total_lateral_m, 1),
        # Uniformity
        "emission_uniformity_percent": round(eu_pct, 1),
        "uniformity_coefficient_percent": round(uc_pct, 1),
        # Zones
        "num_zones": n_zones,
        "flow_per_zone_m3h": round(q_zone_m3h, 2),
        "flow_rate_m3h": round(q_total_m3h, 2),
        "application_rate_mmh": round(application_rate_mmh, 2),
        "run_time_per_zone_h": round(run_time_h, 2),
        "daily_pumping_window_h": DAILY_PUMPING_WINDOW_H,
        # Mainline
        "mainline_velocity_ms": round(main_velocity, 2),
        # TDH
        "tdh_breakdown": tdh_breakdown,
        "total_dynamic_head_m": round(tdh_m, 1),
        # Pump
        "pump_power_kw": round(pump_kw, 2),
        "pump_efficiency": PUMP_EFFICIENCY,
        # Cost
        "total_cost_rwf": int(total_cost_rwf),
        "bom": bom,
    }


def optimize_irrigation_system(
    field_area_ha: float,
    slope_pct: float = 0.0,
    crop_name: str = "Tomato",
    min_eu_threshold: float = 90.0,
    lateral_spacing: Optional[float] = None,
    emitter_spacing: Optional[float] = None,
    # Real polygon geometry from compute_field_layout
    layout_num_laterals: Optional[int] = None,
    layout_total_emitters: Optional[int] = None,
    layout_max_lateral_m: Optional[float] = None,
    layout_mainline_m: Optional[float] = None,
    layout_total_lateral_m: Optional[float] = None,
    # Legacy square fallback params (only used if no layout provided)
    field_length_m: Optional[float] = None,
    field_width_m: Optional[float] = None,
) -> Dict:
    """
    Evaluate all allowed hydraulic configurations and pick the cheapest
    that meets the EU threshold. Uses real polygon geometry when available.
    """
    # If no layout geometry provided, fall back to square approximation
    if layout_num_laterals is None:
        if not field_length_m or not field_width_m:
            side = math.sqrt(max(100.0, field_area_ha * 10000.0))
            field_length_m = side
            field_width_m = side

    allowed_lats = [lateral_spacing] if lateral_spacing and lateral_spacing > 0 else ALLOWED_LATERAL_SPACING
    allowed_emitters = [emitter_spacing] if emitter_spacing and emitter_spacing > 0 else ALLOWED_EMITTER_SPACING

    candidates = []
    for ld in ALLOWED_LATERALS:
        for es in allowed_emitters:
            for ls in allowed_lats:
                for ef in ALLOWED_EMITTER_FLOW:
                    # Compute geometry for this spacing combination
                    if layout_num_laterals is not None:
                        # Real polygon: use exact counts from layout
                        n_lat = layout_num_laterals
                        n_emit = layout_total_emitters
                        max_lat_len = layout_max_lateral_m
                        ml_len = layout_mainline_m
                        tot_lat_m = layout_total_lateral_m
                    else:
                        # Square fallback
                        n_lat = max(1, int(round(field_width_m / ls)))
                        epl = max(1, int(round(field_length_m / es)))
                        n_emit = n_lat * epl
                        max_lat_len = field_length_m
                        ml_len = field_width_m
                        tot_lat_m = field_length_m * n_lat

                    cand = evaluate_design(
                        num_laterals=n_lat,
                        total_emitters=n_emit,
                        max_lateral_length_m=max_lat_len,
                        mainline_length_m=ml_len,
                        total_lateral_m=tot_lat_m,
                        lateral_d_mm=ld,
                        emitter_sp_m=es,
                        lateral_sp_m=ls,
                        emitter_q_lph=ef,
                        slope_pct=slope_pct,
                    )
                    if cand["emission_uniformity_percent"] >= min_eu_threshold:
                        candidates.append(cand)

    candidates.sort(key=lambda c: c["total_cost_rwf"])
    fallback_ls = allowed_lats[0]
    fallback_es = allowed_emitters[0]

    if candidates:
        best = candidates[0]
    else:
        # No config met threshold — use conservative defaults
        if layout_num_laterals is not None:
            best = evaluate_design(
                layout_num_laterals, layout_total_emitters, layout_max_lateral_m,
                layout_mainline_m, layout_total_lateral_m,
                16.0, fallback_es, fallback_ls, 1.6, slope_pct,
            )
        else:
            n_lat = max(1, int(round(field_width_m / fallback_ls)))
            epl = max(1, int(round(field_length_m / fallback_es)))
            best = evaluate_design(
                n_lat, n_lat * epl, field_length_m, field_width_m,
                field_length_m * n_lat,
                16.0, fallback_es, fallback_ls, 1.6, slope_pct,
            )

    return {
        "status": "success",
        "crop": crop_name,
        "field_area_ha": field_area_ha,
        "slope_percent": slope_pct,
        "recommended_design": best,
        "total_candidates_passing": len(candidates),
        "eu_threshold_used": min_eu_threshold,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("IrriGrid Standalone Optimizer Verification")
    print("Scenario: 0.25 ha Tomato in Musanze, Rwanda (2.0% slope)")
    print("=" * 60)
    t0 = time.time()
    result = optimize_irrigation_system(0.25, 2.0, "Tomato",
                                         field_length_m=50.0, field_width_m=50.0)
    elapsed = time.time() - t0

    design = result["recommended_design"]
    print(f"Time: {elapsed:.3f} seconds | Valid Configurations: {result['total_candidates_passing']}")
    print(f"Optimal Lateral: {design['lateral_diameter_mm']} mm | Main: {design['main_diameter_mm']} mm")
    print(f"Emitter Spacing: {design['emitter_spacing_m']} m | Lateral Spacing: {design['lateral_spacing_m']} m")
    print(f"Discharge: {design['emitter_flow_lph']} L/hr | EU: {design['emission_uniformity_percent']}% | UC: {design['uniformity_coefficient_percent']}%")
    print(f"Zones: {design['num_zones']} | Flow/zone: {design['flow_per_zone_m3h']} m³/h | Run time: {design['run_time_per_zone_h']} h")
    print(f"Mainline velocity: {design['mainline_velocity_ms']} m/s")
    print(f"Pump: {design['pump_power_kw']} kW | TDH: {design['total_dynamic_head_m']} m")
    print(f"TDH breakdown: {design['tdh_breakdown']}")
    print(f"Total Cost: {design['total_cost_rwf']:,} RWF")
    print("\nBill of Materials:")
    for item in design["bom"]:
        print(f"  - {item['item']}: {item['quantity']} -> {item['cost_rwf']:,} RWF")
    print("=" * 60)
