#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design Optimizer — Multi-Configuration Grid Search
Satisfies Research Objective 3:
  "Automated optimization routines that minimize total system cost
   while maintaining emission uniformity above industry standards (EU ≥ 90%)"

Strategy:
  1. Define a grid of design parameters (spacing, flow, pressure)
  2. For each combination, run the full hydraulic simulation
  3. Filter: keep only designs with EU ≥ 90%
  4. Rank by total cost (ascending)
  5. Return the optimal design + summary of all candidates tested
"""

import time
from typing import Dict, List, Optional, Tuple
from src.hydraulic.design_calculator import HydraulicDesign, SystemDesign


# Default search grids
DEFAULT_GRIDS = {
    'emitter_spacing': [0.2, 0.3, 0.4, 0.5],       # meters
    'lateral_spacing': [0.5, 0.7, 1.0, 1.2],        # meters
    'emitter_flow':    [1.0, 1.5, 2.0, 4.0],         # L/hr
    'operating_pressure': [1.0, 1.5, 2.0],           # bar
}

MIN_EU_THRESHOLD = 90.0  # percent — industry standard


def optimize_design(
    field_area: float,
    field_length: float,
    field_width: float,
    crop_name: str = 'Tomato',
    soil_type: str = 'Loam',
    slope_percent: float = 0.0,
    grids: Optional[Dict] = None,
    eu_threshold: float = MIN_EU_THRESHOLD,
) -> Dict:
    """
    Run grid-search optimization over irrigation design parameters.

    Args:
        field_area: Field area in hectares
        field_length: Field length in meters
        field_width: Field width in meters
        crop_name: Crop type name
        soil_type: Soil type name
        slope_percent: Terrain slope percentage
        grids: Custom parameter grids (uses DEFAULT_GRIDS if None)
        eu_threshold: Minimum emission uniformity (default 90%)

    Returns:
        Dictionary with:
          - 'best': best design results (or None if none pass EU threshold)
          - 'best_params': parameters of best design
          - 'candidates': list of all passing designs
          - 'total_tested': number of configurations tested
          - 'total_passed': number passing EU threshold
          - 'elapsed_seconds': computation time
          - 'eu_threshold': the threshold used
    """
    if grids is None:
        grids = DEFAULT_GRIDS

    em_spacings = grids.get('emitter_spacing', [0.3, 0.4])
    lat_spacings = grids.get('lateral_spacing', [0.7, 1.0])
    em_flows = grids.get('emitter_flow', [1.5, 2.0])
    pressures = grids.get('operating_pressure', [1.5])

    candidates = []
    total_tested = 0
    t0 = time.time()

    for em_sp in em_spacings:
        for lat_sp in lat_spacings:
            for em_fl in em_flows:
                for pres in pressures:
                    total_tested += 1
                    try:
                        design = SystemDesign(
                            field_area=field_area,
                            field_length=field_length,
                            field_width=field_width,
                            crop_name=crop_name,
                            soil_type=soil_type,
                            emitter_flow=em_fl,
                            emitter_spacing=em_sp,
                            lateral_spacing=lat_sp,
                            operating_pressure=pres,
                            slope_percent=slope_percent,
                        )
                        hd = HydraulicDesign(design)
                        results = hd.calculate_complete_system()

                        eu = results['uniformity']['emission_uniformity_percent']
                        cost = results['costs']['total_rwf']

                        if eu >= eu_threshold:
                            candidates.append({
                                'params': {
                                    'emitter_spacing': em_sp,
                                    'lateral_spacing': lat_sp,
                                    'emitter_flow': em_fl,
                                    'operating_pressure': pres,
                                },
                                'eu_percent': round(eu, 1),
                                'cost_rwf': round(cost),
                                'results': results,
                            })
                    except Exception:
                        # Skip invalid configurations silently
                        pass

    elapsed = time.time() - t0

    # Sort candidates by cost (cheapest first)
    candidates.sort(key=lambda c: c['cost_rwf'])

    best = candidates[0] if candidates else None

    return {
        'best': best['results'] if best else None,
        'best_params': best['params'] if best else None,
        'best_eu': best['eu_percent'] if best else None,
        'best_cost': best['cost_rwf'] if best else None,
        'candidates': candidates,
        'total_tested': total_tested,
        'total_passed': len(candidates),
        'elapsed_seconds': round(elapsed, 2),
        'eu_threshold': eu_threshold,
    }


def format_optimization_summary(result: Dict) -> str:
    """Format optimization result as a human-readable summary string."""
    lines = [
        "═" * 60,
        "DESIGN OPTIMIZATION SUMMARY",
        "═" * 60,
        f"Configurations tested:  {result['total_tested']}",
        f"Configurations passed:  {result['total_passed']} (EU ≥ {result['eu_threshold']}%)",
        f"Computation time:       {result['elapsed_seconds']:.2f} seconds",
        "",
    ]

    if result['best']:
        bp = result['best_params']
        lines += [
            "OPTIMAL DESIGN:",
            f"  Emitter spacing:      {bp['emitter_spacing']} m",
            f"  Lateral spacing:      {bp['lateral_spacing']} m",
            f"  Emitter flow rate:    {bp['emitter_flow']} L/hr",
            f"  Operating pressure:   {bp['operating_pressure']} bar",
            f"  Emission Uniformity:  {result['best_eu']}%",
            f"  Total System Cost:    {result['best_cost']:,} RWF",
            "",
        ]

        # Show top 5 alternatives
        if len(result['candidates']) > 1:
            lines.append("TOP 5 ALTERNATIVES:")
            for i, c in enumerate(result['candidates'][1:6], 2):
                lines.append(
                    f"  #{i}: EU={c['eu_percent']}%, "
                    f"Cost={c['cost_rwf']:,} RWF, "
                    f"ES={c['params']['emitter_spacing']}m, "
                    f"LS={c['params']['lateral_spacing']}m"
                )
    else:
        lines.append("⚠ No configurations met the EU threshold.")
        lines.append("  Consider relaxing constraints or adjusting field parameters.")

    lines.append("═" * 60)
    return "\n".join(lines)


# ── Quick test ──
if __name__ == '__main__':
    print("Running design optimization for Musanze 0.25ha tomato farm...")
    result = optimize_design(
        field_area=0.25,
        field_length=50,
        field_width=50,
        crop_name='Tomato',
        soil_type='Volcanic Clay Loam',
        slope_percent=5.0,
    )
    print(format_optimization_summary(result))
