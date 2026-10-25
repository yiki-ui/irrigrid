#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PolynomialMutation as PM
from pymoo.operators.sampling.rnd import FloatRandomSampling as IntegerRandomSampling

from scripts.validate_optimizer import build_problem, ALLOWED_LATERALS, ALLOWED_MAINS, ALLOWED_EMITTER_SPACING, ALLOWED_LATERAL_SPACING

def main():
    scenario = {
        "id": 10,
        "crop": "tomato",
        "field_area_ha": 0.25,
        "slope_pct": 0,
        "field_length_m": 50.0,
        "field_width_m": 50.0
    }
    
    problem = build_problem(scenario)
    
    algorithm = NSGA2(
        pop_size=100,
        sampling=IntegerRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True,
    )
    
    print("Running NSGA-II optimization for 0.25ha Tomato...")
    result = minimize(
        problem,
        algorithm,
        ("n_gen", 50),
        verbose=True,
        seed=42,
    )
    
    if result.F is None:
        print("No feasible solutions found.")
        return
        
    all_costs = result.F[:, 0]
    all_eus = -result.F[:, 1]
    
    # Extract decision variables
    X = result.X
    
    records = []
    for i, x in enumerate(X):
        ld = ALLOWED_LATERALS[int(x[0])]
        md = ALLOWED_MAINS[int(x[1])]
        es = ALLOWED_EMITTER_SPACING[int(x[2])]
        ls = ALLOWED_LATERAL_SPACING[int(x[3])]
        
        records.append({
            "Rank": i + 1,
            "Lateral (mm)": ld,
            "Main (mm)": md,
            "Emitter Sp (m)": es,
            "Lateral Sp (m)": ls,
            "Est. Cost (RWF)": all_costs[i],
            "EU%": all_eus[i]
        })
        
    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["Est. Cost (RWF)", "EU%"]).reset_index(drop=True)
    df["Rank"] = df.index + 1
    df = df.sort_values(by="Est. Cost (RWF)")
    
    out_dir = Path("/home/yiki-yiris/dissertation/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = out_dir / "pareto_front.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved {len(df)} Pareto optimal solutions to {csv_path}")
    print(df.head(15))
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(df["Est. Cost (RWF)"], df["EU%"], c='blue', alpha=0.7)
    plt.plot(df["Est. Cost (RWF)"], df["EU%"], 'r-', alpha=0.3)
    plt.title("NSGA-II Pareto Front: Cost vs Emission Uniformity\n(0.25 ha Tomato, 2% slope)")
    plt.xlabel("Estimated Cost (RWF)")
    plt.ylabel("Emission Uniformity (%)")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add horizontal line for EU threshold
    plt.axhline(y=90.0, color='g', linestyle='--', label='90% EU Threshold')
    plt.legend()
    
    plot_path = out_dir / "pareto_front_plot.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {plot_path}")

if __name__ == "__main__":
    main()
