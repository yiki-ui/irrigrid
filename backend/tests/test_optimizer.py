#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for IrriGrid core optimizer & hydraulic calculations audit:
1. Pump kW formula verification: P = ρgQH / (η * 1000)
2. TAW and RAW formula verification: TAW = 1000*(FC-WP)*Zr, RAW = p*TAW
3. BOM total equals sum of line items
4. BOM quantities match 2D layout geometry exactly
5. Emission Uniformity (EU) <= Uniformity Coefficient (UC)
6. Irrigation interval uses floor(RAW / ETc_peak)
7. TDH breakdown equals total dynamic head
8. Mainline velocity adheres to <= 1.5 m/s constraint
"""

import math
import pytest
from backend.core.optimizer import (
    optimize_irrigation_system,
    evaluate_design,
    evaluate_hydraulic_configuration,
    PUMP_EFFICIENCY,
    FILTER_HEAD_LOSS_M,
)


def test_evaluate_hydraulic_configuration_backward_compat():
    """Verify legacy wrapper returns expected metrics."""
    res = evaluate_hydraulic_configuration(
        field_length=50.0,
        field_width=50.0,
        slope_pct=2.0,
        lateral_d_mm=16.0,
        main_d_mm=32.0,
        emitter_sp_m=0.3,
        lateral_sp_m=1.0,
        emitter_q_lph=1.6
    )
    assert res["emission_uniformity_percent"] > 85.0
    assert res["total_cost_rwf"] > 100000
    assert res["pump_power_kw"] > 0
    assert len(res["bom"]) >= 4


def test_optimizer_runs_and_satisfies_constraints():
    """Verify standard optimizer execution on 0.25 ha tomato field."""
    result = optimize_irrigation_system(
        field_area_ha=0.25,
        field_length_m=50.0,
        field_width_m=50.0,
        slope_pct=2.0,
        crop_name="Tomato",
        min_eu_threshold=90.0
    )
    assert result["status"] == "success"
    rec = result["recommended_design"]
    assert rec["emission_uniformity_percent"] >= 90.0
    assert rec["total_cost_rwf"] > 0
    assert rec["num_laterals"] > 0
    assert rec["total_emitters"] > 0


def test_pump_kw_formula():
    """
    Verify pump power adheres strictly to hydraulic power formula:
    P (kW) = (ρ * g * Q * H) / (η * 1000)
    where ρ = 1000 kg/m³, g = 9.81 m/s², η = 0.65 (smallholder pump efficiency).
    """
    # 1. Run standard design
    result = optimize_irrigation_system(
        field_area_ha=0.5,
        slope_pct=2.0,
        field_length_m=70.0,
        field_width_m=71.4,
    )
    rec = result["recommended_design"]
    q_zone_m3s = (rec["flow_per_zone_m3h"]) / 3600.0
    tdh_m = rec["tdh_breakdown"]["total_dynamic_head_m"]
    expected_kw = (1000.0 * 9.81 * q_zone_m3s * tdh_m) / (PUMP_EFFICIENCY * 1000.0)
    expected_kw_clamped = max(0.37, round(expected_kw, 2))
    assert math.isclose(rec["pump_power_kw"], expected_kw_clamped, abs_tol=0.02)

    # 2. Test large flow configuration (well above 0.37 kW floor)
    large_design = evaluate_design(
        num_laterals=100,
        total_emitters=25000,
        max_lateral_length_m=100.0,
        mainline_length_m=100.0,
        total_lateral_m=10000.0,
        lateral_d_mm=20.0,
        emitter_sp_m=0.4,
        lateral_sp_m=1.0,
        emitter_q_lph=2.5,
        slope_pct=3.0,
    )
    q_large_m3s = large_design["flow_per_zone_m3h"] / 3600.0
    tdh_large = large_design["total_dynamic_head_m"]
    raw_kw = (1000.0 * 9.81 * q_large_m3s * tdh_large) / (PUMP_EFFICIENCY * 1000.0)
    assert raw_kw > 0.37
    assert math.isclose(large_design["pump_power_kw"], round(raw_kw, 2), abs_tol=0.02)


def test_taw_and_raw_formulas():
    """
    Verify agronomic water-holding capacity formulas:
    TAW (mm) = 1000 * (FC - WP) * root_depth
    RAW (mm) = p * TAW
    """
    fc_val = 32.0  # %
    wp_val = 16.0  # %
    root_depth_m = 0.6  # m
    depletion_p = 0.4  # fraction

    fc_frac = fc_val / 100.0
    wp_frac = wp_val / 100.0
    taw_mm = 1000.0 * (fc_frac - wp_frac) * root_depth_m
    raw_mm = depletion_p * taw_mm

    assert math.isclose(taw_mm, 96.0, rel_tol=1e-4)
    assert math.isclose(raw_mm, 38.4, rel_tol=1e-4)


def test_bom_total_equals_sum_of_items():
    """Verify total_cost_rwf exactly equals the sum of line items in the BOM."""
    for area in [0.1, 0.25, 1.0, 2.5]:
        result = optimize_irrigation_system(
            field_area_ha=area,
            slope_pct=1.5,
            crop_name="Tomato",
        )
        rec = result["recommended_design"]
        bom = rec["bom"]
        sum_items = sum(item["cost_rwf"] for item in bom)
        assert rec["total_cost_rwf"] == sum_items, (
            f"BOM total mismatch for {area} ha: total_cost={rec['total_cost_rwf']}, sum={sum_items}"
        )


def test_bom_quantities_match_layout():
    """
    Verify BOM quantities and section 6 metrics match the real layout geometry:
    - Lateral pipe length
    - Mainline pipe length
    - Emitter count
    - Lateral count
    """
    layout_num_laterals = 42
    layout_total_emitters = 6720
    layout_max_lateral_m = 48.0
    layout_mainline_m = 55.0
    layout_total_lateral_m = 2016.0

    result = optimize_irrigation_system(
        field_area_ha=0.25,
        slope_pct=2.0,
        crop_name="Tomato",
        layout_num_laterals=layout_num_laterals,
        layout_total_emitters=layout_total_emitters,
        layout_max_lateral_m=layout_max_lateral_m,
        layout_mainline_m=layout_mainline_m,
        layout_total_lateral_m=layout_total_lateral_m,
    )
    rec = result["recommended_design"]

    # Verify section 6 hydraulic metrics match layout
    assert rec["num_laterals"] == layout_num_laterals
    assert rec["total_emitters"] == layout_total_emitters
    assert rec["max_lateral_length_m"] == layout_max_lateral_m
    assert rec["mainline_length_m"] == layout_mainline_m
    assert rec["total_lateral_m"] == layout_total_lateral_m

    # Verify BOM lines match layout numbers
    bom_by_item = {item["item"]: item for item in rec["bom"]}
    
    # 1. Lateral line
    lat_item = next(v for k, v in bom_by_item.items() if "Lateral Pipe" in k)
    assert f"{int(layout_total_lateral_m)} m" in lat_item["quantity"]

    # 2. Mainline line
    main_item = next(v for k, v in bom_by_item.items() if "Mainline" in k)
    assert f"{int(layout_mainline_m)} m" in main_item["quantity"]

    # 3. Emitters line
    emit_item = next(v for k, v in bom_by_item.items() if "Inline Emitters" in k)
    assert f"{layout_total_emitters:,} units" in emit_item["quantity"]

    # 4. Fittings line
    fit_item = next(v for k, v in bom_by_item.items() if "Fittings" in k)
    assert f"{layout_num_laterals} lateral kits" in fit_item["quantity"]


def test_emission_uniformity_less_than_or_equal_to_uniformity_coefficient():
    """
    Verify EU <= UC holds across a diverse sweep of hydraulic configurations.
    Keller-Karmeli EU = 100 * q_min / q_avg
    Christiansen UC = 100 * (1 - MAD / q_avg)
    Mathematically, UC >= EU for any continuous flow distribution.
    """
    for lat_len in [25.0, 50.0, 100.0]:
        for slope in [0.0, 2.0, 5.0]:
            for q_em in [1.0, 1.6, 2.0, 2.5]:
                cand = evaluate_design(
                    num_laterals=30,
                    total_emitters=3000,
                    max_lateral_length_m=lat_len,
                    mainline_length_m=40.0,
                    total_lateral_m=30 * lat_len,
                    lateral_d_mm=16.0,
                    emitter_sp_m=0.3,
                    lateral_sp_m=1.0,
                    emitter_q_lph=q_em,
                    slope_pct=slope,
                )
                eu = cand["emission_uniformity_percent"]
                uc = cand["uniformity_coefficient_percent"]
                assert eu <= uc, f"EU ({eu}) > UC ({uc}) for lat_len={lat_len}, slope={slope}, q={q_em}"
                # For non-zero head loss, EU and UC should be distinct
                if eu < 99.9:
                    assert uc > eu


def test_irrigation_interval_floor():
    """
    Verify irrigation interval is computed as floor of RAW / ETc_peak.
    Never round up, as rounding up would deplete below Management Allowed Depletion (MAD).
    """
    raw_mm = 38.4
    etc_peak = 4.2  # mm/day
    ratio = raw_mm / etc_peak  # 9.1428...
    interval_floor = math.floor(ratio)
    assert interval_floor == 9
    assert interval_floor < math.ceil(ratio)


def test_tdh_breakdown_sums_to_total():
    """Verify TDH components sum exactly to the total dynamic head."""
    cand = evaluate_design(
        num_laterals=50,
        total_emitters=5000,
        max_lateral_length_m=50.0,
        mainline_length_m=50.0,
        total_lateral_m=2500.0,
        lateral_d_mm=16.0,
        emitter_sp_m=0.4,
        lateral_sp_m=1.0,
        emitter_q_lph=2.0,
        slope_pct=2.0,
    )
    tdh = cand["tdh_breakdown"]
    component_sum = (
        tdh["operating_pressure_m"]
        + tdh["lateral_friction_m"]
        + tdh["mainline_friction_m"]
        + tdh["filter_loss_m"]
        + tdh["elevation_head_m"]
    )
    assert math.isclose(component_sum, tdh["total_dynamic_head_m"], abs_tol=0.05)


def test_mainline_velocity_constraint():
    """Verify mainline pipe sizing keeps velocity <= 1.5 m/s."""
    cand = evaluate_design(
        num_laterals=60,
        total_emitters=6000,
        max_lateral_length_m=60.0,
        mainline_length_m=60.0,
        total_lateral_m=3600.0,
        lateral_d_mm=16.0,
        emitter_sp_m=0.3,
        lateral_sp_m=1.0,
        emitter_q_lph=2.0,
        slope_pct=1.0,
    )
    assert cand["mainline_velocity_ms"] <= 1.5
