#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Headless NSGA-II Optimizer Benchmarking
========================================
Runs the pymoo-based multi-objective optimization headlessly across
the same 27 scenarios as scripts/run_validation.py to validate:

- Convergence time per scenario
- Peak memory usage per scenario
- Pareto front cardinality
- Constraint satisfaction rate (EU >= 90%)

The problem reuses the project's real HydraulicDesign / SystemDesign
classes so benchmark numbers reflect actual design outcomes.

Output: results/optimizer_benchmark.csv
"""

import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

try:
    from pymoo.core.problem import Problem
    from pymoo.optimize import minimize
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PolynomialMutation as PM
    from pymoo.operators.sampling.rnd import FloatRandomSampling as IntegerRandomSampling
    PYMOO_AVAILABLE = True
except ImportError:
    PYMOO_AVAILABLE = False

from src.hydraulic.design_calculator import HydraulicDesign, SystemDesign


if not PYMOO_AVAILABLE:
    print("ERROR: pymoo is not installed. Install with: pip install pymoo")
    sys.exit(1)


ALLOWED_LATERALS = [16.0, 20.0, 25.0, 32.0]
ALLOWED_MAINS = [32.0, 40.0, 50.0, 63.0, 75.0, 90.0]
ALLOWED_EMITTER_SPACING = [0.2, 0.25, 0.3, 0.35, 0.4, 0.5]
ALLOWED_LATERAL_SPACING = [0.5, 0.75, 1.0, 1.25, 1.5]

PRICE_MAP = {
    16.0: 150, 20.0: 200, 25.0: 300, 32.0: 500,
    40.0: 800, 50.0: 1200, 63.0: 1800, 75.0: 2500, 90.0: 3500
}


def _field_side(ha: float) -> float:
    return (ha * 10000) ** 0.5


SCENARIOS = [
    {"id": i, "crop": crop, "field_area_ha": area, "slope_pct": slope,
     "field_length_m": _field_side(area), "field_width_m": _field_side(area)}
    for i, (crop, area, slope) in enumerate([
        ("tomato", 0.10, 0), ("bean", 0.10, 0), ("onion", 0.10, 0),
        ("tomato", 0.10, 2), ("bean", 0.10, 2), ("onion", 0.10, 2),
        ("tomato", 0.10, 5), ("bean", 0.10, 5), ("onion", 0.10, 5),
        ("tomato", 0.25, 0), ("bean", 0.25, 0), ("onion", 0.25, 0),
        ("tomato", 0.25, 2), ("bean", 0.25, 2), ("onion", 0.25, 2),
        ("tomato", 0.25, 5), ("bean", 0.25, 5), ("onion", 0.25, 5),
        ("tomato", 0.50, 0), ("bean", 0.50, 0), ("onion", 0.50, 0),
        ("tomato", 0.50, 2), ("bean", 0.50, 2), ("onion", 0.50, 2),
        ("tomato", 0.50, 5), ("bean", 0.50, 5), ("onion", 0.50, 5),
    ], start=1)
]


def _default_design(crop, area, slope, length, width):
    if slope <= 1:
        emitter_flow = 2.0
        op_pressure = 1.5
        lat_sp = 1.8
    elif slope <= 3:
        emitter_flow = 2.0
        op_pressure = 2.0
        lat_sp = 1.5
    else:
        emitter_flow = 1.5
        op_pressure = 2.5
        lat_sp = 1.2
    return SystemDesign(
        field_area=area,
        field_length=length,
        field_width=width,
        crop_name=crop,
        soil_type="Loam",
        emitter_flow=emitter_flow,
        emitter_spacing=0.3,
        lateral_spacing=lat_sp,
        operating_pressure=op_pressure,
        slope_percent=slope,
        slope_direction="downhill",
    )


def build_problem(scenario: dict):
    crop = scenario["crop"]
    field_area = scenario["field_area_ha"]
    slope_pct = scenario["slope_pct"]
    field_length = scenario["field_length_m"]
    field_width = scenario["field_width_m"]

    base_design = _default_design(crop, field_area, slope_pct, field_length, field_width)

    class DripProblem(Problem):
        def __init__(self):
            super().__init__(
                n_var=4,
                n_obj=2,
                n_ieq_constr=1,
                xl=[0, 0, 0, 0],
                xu=[
                    len(ALLOWED_LATERALS) - 1,
                    len(ALLOWED_MAINS) - 1,
                    len(ALLOWED_EMITTER_SPACING) - 1,
                    len(ALLOWED_LATERAL_SPACING) - 1,
                ],
            )

        def _evaluate(self, X, out, **kwargs):
            costs = []
            eus = []
            g = []

            for x in X:
                ld = ALLOWED_LATERALS[int(x[0])]
                md = ALLOWED_MAINS[int(x[1])]
                es = ALLOWED_EMITTER_SPACING[int(x[2])]
                ls = ALLOWED_LATERAL_SPACING[int(x[3])]

                nl = max(1, int(field_width / ls))
                lc = field_width * nl * PRICE_MAP.get(ld, 9999)
                mc = field_length * PRICE_MAP.get(md, 9999)
                cost = lc + mc

                design = SystemDesign(
                    field_area=field_area,
                    field_length=field_length,
                    field_width=field_width,
                    crop_name=crop,
                    soil_type="Loam",
                    emitter_flow=base_design.emitter_flow,
                    emitter_spacing=es,
                    lateral_spacing=ls,
                    operating_pressure=base_design.operating_pressure,
                    slope_percent=slope_pct,
                    slope_direction="downhill",
                    lateral_diameter_mm=ld,
                    main_diameter_mm=md,
                )

                try:
                    hydraulic = HydraulicDesign(design)
                    res = hydraulic.calculate_complete_system()
                    eu = float(res["uniformity"]["emission_uniformity_percent"])
                except Exception:
                    eu = 0.0

                costs.append(cost)
                eus.append(eu)
                g.append(90.0 - eu)

            out["F"] = np.column_stack([costs, -np.array(eus)])
            out["G"] = np.column_stack(g)

    return DripProblem()


def run_scenario_benchmark(scenario: dict) -> dict:
    problem = build_problem(scenario)

    algorithm = NSGA2(
        pop_size=40,
        sampling=IntegerRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True,
    )

    tracemalloc.reset_peak()
    tracemalloc.start()
    t0 = time.perf_counter()

    try:
        result = minimize(
            problem,
            algorithm,
            ("n_gen", 20),
            verbose=False,
            seed=42,
        )
    except Exception as exc:
        t1 = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "scenario_id": scenario["id"],
            "crop": scenario["crop"],
            "field_size_ha": scenario["field_area_ha"],
            "slope_pct": scenario["slope_pct"],
            "wall_time_seconds": round(t1 - t0, 6),
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
            "pareto_solutions": 0,
            "feasible_solutions": 0,
            "feasibility_rate_pct": 0.0,
            "best_cost_feasible": None,
            "best_eu_feasible": None,
            "min_cost_overall": None,
            "max_eu_overall": None,
            "error": str(exc),
        }

    t1 = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if result.F is None:
        return {
            "scenario_id": scenario["id"],
            "crop": scenario["crop"],
            "field_size_ha": scenario["field_area_ha"],
            "slope_pct": scenario["slope_pct"],
            "wall_time_seconds": round(t1 - t0, 6),
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
            "pareto_solutions": 0,
            "feasible_solutions": 0,
            "feasibility_rate_pct": 0.0,
            "best_cost_feasible": None,
            "best_eu_feasible": None,
            "min_cost_overall": None,
            "max_eu_overall": None,
            "error": "NSGA-II returned no feasible solution set (result.F is None)",
        }

    all_costs = result.F[:, 0]
    all_eus = -result.F[:, 1]
    feasible_mask = all_eus >= 90
    n_feasible = int(np.count_nonzero(feasible_mask))

    return {
        "scenario_id": scenario["id"],
        "crop": scenario["crop"],
        "field_size_ha": scenario["field_area_ha"],
        "slope_pct": scenario["slope_pct"],
        "wall_time_seconds": round(t1 - t0, 6),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
        "pareto_solutions": int(len(all_costs)),
        "feasible_solutions": n_feasible,
        "feasibility_rate_pct": round(n_feasible / max(1, len(all_costs)) * 100, 2),
        "best_cost_feasible": round(float(all_costs[feasible_mask].min()), 2) if n_feasible > 0 else None,
        "best_eu_feasible": round(float(all_eus[feasible_mask].max()), 2) if n_feasible > 0 else None,
        "min_cost_overall": round(float(all_costs.min()), 2),
        "max_eu_overall": round(float(all_eus.max()), 2),
        "error": None,
    }


def main():
    print("=" * 60)
    print("NSGA-II OPTIMIZER BENCHMARK")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scenarios to benchmark: {len(SCENARIOS)}")
    print()

    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    records = []
    for scenario in SCENARIOS:
        print(f"Benchmarking scenario {scenario['id']}: "
              f"{scenario['crop']}, {scenario['field_area_ha']}ha, {scenario['slope_pct']}% slope ...")
        rec = run_scenario_benchmark(scenario)
        records.append(rec)
        print(f"  -> time={rec['wall_time_seconds']}s, "
              f"peak_mem={rec['peak_memory_mb']}MB, "
              f"feasible={rec['feasible_solutions']}/{rec['pareto_solutions']}")

    df = pd.DataFrame(records)
    csv_path = results_dir / "optimizer_benchmark.csv"
    df.to_csv(csv_path, index=False)
    print()
    print(f"Results saved to: {csv_path}")
    print()

    print("=" * 60)
    print("AGGREGATE STATISTICS")
    print("=" * 60)
    print(df[["wall_time_seconds", "peak_memory_mb", "feasible_solutions", "feasibility_rate_pct"]].describe().to_string())
    print()
    print(f"Mean wall time: {df['wall_time_seconds'].mean():.4f}s")
    print(f"Mean peak memory: {df['peak_memory_mb'].mean():.3f} MB")
    print(f"Mean feasible solutions: {df['feasible_solutions'].mean():.1f}")
    print(f"Mean feasibility rate: {df['feasibility_rate_pct'].mean():.2f}%")
    print()
    print("BENCHMARK COMPLETE")


if __name__ == "__main__":
    main()
