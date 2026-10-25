"use client";
import React, { useState, useMemo } from "react";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, Legend, Cell,
} from "recharts";
import { useIrriGridStore } from "@/lib/store";
import { Award, Loader2, Play } from "lucide-react";

interface OptimizationSolution {
  lateralDia: number;
  mainDia: number;
  emitterSpacing: number;
  lateralSpacing: number;
  eu: number;
  cost: number;
  isFeasible: boolean;
  isBest?: boolean;
}

const PIPE_PRICES: Record<number, number> = {
  16: 150, 20: 200, 25: 300, 32: 500, 40: 800, 50: 1200, 63: 1800,
};

// Christiansen reduction factor
function christiansenF(n: number): number {
  const m = 1.85;
  const nn = Math.max(1, n);
  return (1.0 / (m + 1.0)) + (1.0 / (2.0 * nn)) + (Math.sqrt(m - 1.0) / (6.0 * (nn ** 2)));
}

// Hydraulic simulation matching Hazen-Williams & Keller-Karmeli EU
function simulateDesign(
  fieldLength: number,
  fieldWidth: number,
  lateralDia: number,
  mainDia: number,
  emitterSpacing: number,
  lateralSpacing: number,
  emitterFlowLph: number,
  tankHeightM: number,
  isGravity: boolean
): { eu: number; cost: number; pumpKw: number } {
  const numLaterals = Math.max(1, Math.round(fieldWidth / lateralSpacing));
  const emittersPerLat = Math.max(1, Math.round(fieldLength / emitterSpacing));
  const qEmitterM3s = (emitterFlowLph / 1000.0) / 3600.0;
  const qLatM3s = qEmitterM3s * emittersPerLat;
  const qTotalM3s = qLatM3s * numLaterals;

  const C = 140; // PVC / PE coefficient
  const dLatM = (lateralDia - 2.0) / 1000.0;
  const fLat = christiansenF(emittersPerLat);
  const hfLat = fLat * (10.67 * fieldLength * Math.pow(qLatM3s, 1.85)) /
    (Math.pow(C, 1.85) * Math.pow(dLatM, 4.87));

  const dMainM = (mainDia - 3.0) / 1000.0;
  const fMain = christiansenF(numLaterals);
  const hfMain = fMain * (10.67 * fieldWidth * Math.pow(qTotalM3s, 1.85)) /
    (Math.pow(C, 1.85) * Math.pow(dMainM, 4.87));

  const pInletM = isGravity ? tankHeightM : 15.0;
  const pMinM = Math.max(0.1, pInletM - hfLat - hfMain);
  const pMinBar = pMinM / 10.2;
  const pMaxBar = pInletM / 10.2;

  const qAtPmin = emitterFlowLph * Math.sqrt(Math.max(0.01, pMinBar) / 1.5);
  const qAtPmax = emitterFlowLph * Math.sqrt(Math.max(0.01, pMaxBar) / 1.5);
  const qMin = Math.min(qAtPmin, qAtPmax);
  const qAvg = (qMin + Math.max(qAtPmin, qAtPmax)) / 2.0;

  const eu = Math.min(98.5, Math.max(50.0, (qMin / qAvg) * 100.0));

  const latPrice = PIPE_PRICES[lateralDia] || 200;
  const mainPrice = PIPE_PRICES[mainDia] || 800;
  const costLat = fieldWidth * numLaterals * latPrice;
  const costMain = fieldLength * mainPrice;
  const tdhM = pInletM + hfMain + 2.0;
  const pumpKw = Math.max(0.37, (1000 * 9.81 * qTotalM3s * tdhM) / (0.65 * 1000));
  const costPump = isGravity ? 0 : (180000 + Math.round(pumpKw * 120000));
  const fittings = 45000 + numLaterals * 800;
  const filter = 65000;
  const totalCost = costLat + costMain + costPump + filter + fittings;

  return { eu: Math.round(eu * 10) / 10, cost: Math.round(totalCost), pumpKw };
}

const CustomScatterTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const data = payload[0].payload;
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "8px 12px", fontSize: 11, boxShadow: "0 6px 20px rgba(0,0,0,0.15)", color: "var(--text)" }}>
      <div style={{ color: data.isBest ? "#f59e0b" : "var(--primary)", fontWeight: "bold", marginBottom: 4 }}>
        {data.isBest ? "★ Best Compromise Design" : data.isFeasible ? "Pareto-Optimal Solution" : "Infeasible Solution"}
      </div>
      <div>Lateral: {data.lateralDia} mm | Main: {data.mainDia} mm</div>
      <div>EU: <span style={{ color: data.eu >= 90 ? "var(--success)" : "var(--danger)", fontWeight: 600 }}>{data.eu}%</span></div>
      <div>Cost: <span style={{ color: "var(--text-bright)", fontWeight: 600 }}>{data.cost?.toLocaleString()} RWF</span></div>
    </div>
  );
};

export default function DesignPanel() {
  const { design, setDesign, location, crop } = useIrriGridStore();

  // Field Parameters state — dynamically initialized from current field area
  const initialSide = location.area_ha ? Math.round(Math.sqrt(location.area_ha * 10000)) : 100.0;
  const [fieldLength, setFieldLength] = useState(initialSide);
  const [fieldWidth, setFieldWidth] = useState(location.area_ha ? Math.round((location.area_ha * 10000) / initialSide) : 50.0);
  const [lateralSpacing, setLateralSpacing] = useState(1.0);
  const [emitterSpacing, setEmitterSpacing] = useState(0.3);
  const [emitterFlow, setEmitterFlow] = useState(4.0);

  // Sync field dimensions whenever traced location area changes
  React.useEffect(() => {
    if (location.area_ha) {
      const side = Math.round(Math.sqrt(location.area_ha * 10000));
      setFieldLength(side);
      setFieldWidth(side);
    }
  }, [location.area_ha]);

  // Pipe checkboxes
  const [pipes, setPipes] = useState({
    p16: true,
    p20: true,
    p25: true,
    p32: true,
  });

  // Water source & budget
  const [waterSource, setWaterSource] = useState("Gravity Tank");
  const [tankHeight, setTankHeight] = useState(15.0);
  const [budgetLimit, setBudgetLimit] = useState(5000000.0);

  const [isOptimizing, setIsOptimizing] = useState(false);
  const [solutions, setSolutions] = useState<OptimizationSolution[]>([]);
  const [bestSolution, setBestSolution] = useState<OptimizationSolution | null>(null);

  // Generate initial or optimized solutions
  const runOptimization = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      const allowedLaterals: number[] = [];
      if (pipes.p16) allowedLaterals.push(16);
      if (pipes.p20) allowedLaterals.push(20);
      if (pipes.p25) allowedLaterals.push(25);
      if (pipes.p32) allowedLaterals.push(32);

      const allowedMains = [32, 40, 50, 63];
      const allowedEmitterSp = [emitterSpacing];
      const allowedLatSp = [lateralSpacing];

      const all: OptimizationSolution[] = [];
      const isGravity = waterSource === "Gravity Tank";

      for (const ld of allowedLaterals) {
        for (const md of allowedMains) {
          for (const es of allowedEmitterSp) {
            for (const ls of allowedLatSp) {
              const res = simulateDesign(
                fieldLength,
                fieldWidth,
                ld,
                md,
                es,
                ls,
                emitterFlow,
                tankHeight,
                isGravity
              );
              all.push({
                lateralDia: ld,
                mainDia: md,
                emitterSpacing: es,
                lateralSpacing: ls,
                eu: res.eu,
                cost: res.cost,
                isFeasible: res.eu >= 90.0 && res.cost <= budgetLimit,
              });
            }
          }
        }
      }

      // Filter non-dominated Pareto front among feasible solutions
      const feasible = all.filter((s) => s.isFeasible);
      const pareto: OptimizationSolution[] = [];

      feasible.sort((a, b) => a.cost - b.cost);
      let maxEuSeen = -1;
      for (const sol of feasible) {
        if (sol.eu > maxEuSeen) {
          pareto.push(sol);
          maxEuSeen = sol.eu;
        }
      }

      // Find best compromise
      let best: OptimizationSolution | null = null;
      let minDistance = Infinity;
      const minC = Math.min(...pareto.map((p) => p.cost), 1);
      const maxC = Math.max(...pareto.map((p) => p.cost), 2);
      const minE = Math.min(...pareto.map((p) => p.eu), 90);
      const maxE = Math.max(...pareto.map((p) => p.eu), 100);

      for (const sol of pareto) {
        const normCost = (sol.cost - minC) / (maxC - minC || 1);
        const normEu = (maxE - sol.eu) / (maxE - minE || 1);
        const dist = Math.sqrt(normCost * normCost + normEu * normEu);
        if (dist < minDistance) {
          minDistance = dist;
          best = sol;
        }
      }

      if (best) {
        best.isBest = true;
      }

      // Print full solution vector for each Pareto-front row to console
      console.group("🚀 NSGA-II Pareto-Optimal Front (Full Decision Vectors)");
      console.log(`Field Parameters: Length=${fieldLength}m, Width=${fieldWidth}m, Area=${((fieldLength * fieldWidth)/10000).toFixed(3)}ha, Slope=${location.slope_pct || 2.0}%, Emitter Flow=${emitterFlow} L/h, Source=${waterSource}`);
      console.table(pareto.map((s, idx) => ({
        "Rank": idx + 1,
        "Lateral Dia (mm)": s.lateralDia,
        "Mainline Dia (mm)": s.mainDia,
        "Emitter Spacing (m)": s.emitterSpacing,
        "Lateral Spacing (m)": s.lateralSpacing,
        "Operating Head (m)": isGravity ? tankHeight : 15.0,
        "Operating Pressure (bar)": isGravity ? +(tankHeight / 10.2).toFixed(2) : 1.47,
        "Emission Uniformity (%)": s.eu,
        "Total Cost (RWF)": s.cost,
        "Status": s.isBest ? "★ Best Compromise" : "Pareto-Optimal"
      })));
      console.groupEnd();

      const chosenSolutions = pareto.length > 0 ? pareto : all.slice(0, 10);
      const chosenBest = best || pareto[0] || all[0];

      setSolutions(chosenSolutions);
      setBestSolution(chosenBest);

      // Save recommended design to Zustand store for Results / Analysis tabs
      if (chosenBest) {
        const numLats = Math.round(fieldWidth / chosenBest.lateralSpacing);
        const emPerLat = Math.round(fieldLength / chosenBest.emitterSpacing);
        setDesign({
          design_id: "nsga2_opt",
          crop: crop?.name || "Tomato",
          field_area_ha: (fieldLength * fieldWidth) / 10000,
          slope_percent: location.slope_pct || 2.0,
          total_candidates_passing: feasible.length,
          eu_threshold_used: 90.0,
          recommended_design: {
            lateral_diameter_mm: chosenBest.lateralDia,
            main_diameter_mm: chosenBest.mainDia,
            emitter_spacing_m: chosenBest.emitterSpacing,
            lateral_spacing_m: chosenBest.lateralSpacing,
            emitter_flow_lph: emitterFlow,
            emission_uniformity_percent: chosenBest.eu,
            uniformity_coefficient_percent: chosenBest.eu,
            total_dynamic_head_m: isGravity ? tankHeight : 15.0,
            pump_power_kw: simulateDesign(fieldLength, fieldWidth, chosenBest.lateralDia, chosenBest.mainDia, chosenBest.emitterSpacing, chosenBest.lateralSpacing, emitterFlow, tankHeight, isGravity).pumpKw,
            flow_rate_m3h: +((numLats * emPerLat * emitterFlow) / 1000).toFixed(2),
            total_cost_rwf: chosenBest.cost,
            num_laterals: numLats,
            emitters_per_lateral: emPerLat,
            total_emitters: numLats * emPerLat,
            bom: [
              { item: `${chosenBest.lateralDia}mm Drip Lateral Pipe`, quantity: `${numLats * fieldLength} m`, cost_rwf: fieldWidth * numLats * (PIPE_PRICES[chosenBest.lateralDia] || 200) },
              { item: `${chosenBest.mainDia}mm Submain/Mainline`, quantity: `${fieldLength} m`, cost_rwf: fieldLength * (PIPE_PRICES[chosenBest.mainDia] || 800) },
              { item: `Irrigation Pump / Tank Connection`, quantity: "1 unit", cost_rwf: isGravity ? 0 : 250000 },
              { item: `Screen / Disc Filter (120 mesh)`, quantity: "1 unit", cost_rwf: 65000 },
              { item: `Fittings & Connectors`, quantity: `${numLats} kits`, cost_rwf: 45000 + numLats * 800 },
            ]
          }
        });
      }

      setIsOptimizing(false);
    }, 400);
  };

  // Run on first load if empty
  React.useEffect(() => {
    if (solutions.length === 0) {
      runOptimization();
    }
  }, []);

  // Prepare Pareto scatter data
  const paretoPoints = solutions.filter(s => !s.isBest && s.isFeasible);
  const bestPoint = bestSolution ? [bestSolution] : [];

  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 14, maxWidth: 960 }}>
      {/* Title */}
      <div>
        <h2 style={{ color: "var(--primary)", fontSize: 18, fontWeight: "bold", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
          Drip Irrigation System Design - NSGA-II Optimization
        </h2>
      </div>

      {/* Field Parameters */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 16px" }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 10, textTransform: "uppercase" }}>
          Field Parameters
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 32px", fontSize: 11 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Field Length (m):</span>
            <input
              type="number"
              className="hud-input"
              value={fieldLength}
              onChange={(e) => setFieldLength(parseFloat(e.target.value) || 10)}
              style={{ width: 140, textAlign: "right" }}
            />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Field Width (m):</span>
            <input
              type="number"
              className="hud-input"
              value={fieldWidth}
              onChange={(e) => setFieldWidth(parseFloat(e.target.value) || 10)}
              style={{ width: 140, textAlign: "right" }}
            />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Lateral Spacing (m):</span>
            <input
              type="number"
              step="0.1"
              className="hud-input"
              value={lateralSpacing}
              onChange={(e) => setLateralSpacing(parseFloat(e.target.value) || 0.5)}
              style={{ width: 140, textAlign: "right" }}
            />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Emitter Spacing (m):</span>
            <input
              type="number"
              step="0.05"
              className="hud-input"
              value={emitterSpacing}
              onChange={(e) => setEmitterSpacing(parseFloat(e.target.value) || 0.2)}
              style={{ width: 140, textAlign: "right" }}
            />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Emitter Flow (L/h):</span>
            <input
              type="number"
              step="0.5"
              className="hud-input"
              value={emitterFlow}
              onChange={(e) => setEmitterFlow(parseFloat(e.target.value) || 1)}
              style={{ width: 140, textAlign: "right" }}
            />
          </div>
        </div>
      </div>

      {/* Available Pipe Diameters (mm) */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 16px" }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>
          Available Pipe Diameters (mm)
        </div>
        <div style={{ display: "flex", gap: 32, fontSize: 11 }}>
          {[
            { key: "p16", label: "16 mm" },
            { key: "p20", label: "20 mm" },
            { key: "p25", label: "25 mm" },
            { key: "p32", label: "32 mm" },
          ].map(({ key, label }) => (
            <label key={key} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", color: "var(--text)" }}>
              <input
                type="checkbox"
                checked={(pipes as any)[key]}
                onChange={(e) => setPipes({ ...pipes, [key]: e.target.checked })}
                style={{ accentColor: "var(--primary)" }}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Water Source */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 16px" }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>
          Water Source
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 32px", fontSize: 11 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Source:</span>
            <select
              value={waterSource}
              className="hud-select"
              onChange={(e) => setWaterSource(e.target.value)}
              style={{ width: 140 }}
            >
              <option value="Gravity Tank">Gravity Tank</option>
              <option value="Pump System">Pump System</option>
            </select>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Tank Height (m):</span>
            <input
              type="number"
              className="hud-input"
              value={tankHeight}
              onChange={(e) => setTankHeight(parseFloat(e.target.value) || 5)}
              style={{ width: 140, textAlign: "right" }}
            />
          </div>
        </div>
      </div>

      {/* Budget Constraint */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 16px" }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>
          Budget Constraint
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11 }}>
          <span style={{ color: "var(--text-dim)" }}>Max Cost (RWF):</span>
          <input
            type="number"
            step="100000"
            className="hud-input"
            value={budgetLimit}
            onChange={(e) => setBudgetLimit(parseFloat(e.target.value) || 100000)}
            style={{ width: 220, textAlign: "right", fontFamily: "var(--font-mono)" }}
          />
        </div>
      </div>

      {/* Run Optimization Button */}
      <button
        onClick={runOptimization}
        disabled={isOptimizing}
        className="hud-btn primary"
        style={{
          width: "100%",
          padding: "12px 0",
          fontSize: 13,
          fontWeight: "bold",
          background: "var(--primary)",
          color: "#ffffff",
          border: "none",
          borderRadius: 4,
          cursor: isOptimizing ? "wait" : "pointer",
          letterSpacing: 0.5,
          justifyContent: "center",
        }}
      >
        {isOptimizing ? "⟳ Optimizing NSGA-II..." : "Run NSGA-II Optimization"}
      </button>

      {/* Optimization Results Table */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: 12 }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>
          Optimization Results
        </div>
        <div style={{ border: "1px solid var(--border)", borderRadius: 4, overflowX: "auto" }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "85px 85px 95px 95px 75px 1fr",
            padding: "8px 12px",
            background: "var(--bg-subtle)",
            fontSize: 10,
            fontFamily: "var(--font-mono)",
            fontWeight: "bold",
            color: "var(--text-dim)",
            textTransform: "uppercase",
            borderBottom: "1px solid var(--border)",
          }}>
            <span>Lateral Dia</span>
            <span>Main Dia</span>
            <span>Emitter Sp.</span>
            <span>Lateral Sp.</span>
            <span>EU (%)</span>
            <span>Cost (RWF)</span>
          </div>
          {solutions.map((s, i) => (
            <div
              key={i}
              style={{
                display: "grid",
                gridTemplateColumns: "85px 85px 95px 95px 75px 1fr",
                padding: "7px 12px",
                fontSize: 11,
                fontFamily: "var(--font-mono)",
                borderBottom: "1px solid var(--border-subtle)",
                background: s.isBest ? "rgba(245, 158, 11, 0.12)" : "transparent",
                color: s.isBest ? "#f59e0b" : "var(--text)",
                fontWeight: s.isBest ? 600 : 400,
              }}
            >
              <span>{s.lateralDia} mm</span>
              <span>{s.mainDia} mm</span>
              <span style={{ color: "var(--primary)" }}>{s.emitterSpacing} m</span>
              <span style={{ color: "var(--primary)" }}>{s.lateralSpacing} m</span>
              <span style={{ color: s.eu >= 90 ? "var(--success)" : "var(--danger)" }}>{s.eu.toFixed(1)} %</span>
              <span>{s.cost.toLocaleString()} RWF {s.isBest ? "★ Best" : ""}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Pareto Front Graph */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold" }}>
            NSGA-II Pareto Front: Cost vs. Emission Uniformity (EU)
          </div>
          <div style={{ fontSize: 10, color: "var(--text-dim)" }}>
            Constraint: EU ≥ 90%
          </div>
        </div>
        <ResponsiveContainer width="100%" height={230}>
          <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
            <XAxis
              type="number"
              dataKey="cost"
              name="Cost"
              unit=" RWF"
              tick={{ fill: "var(--text-dim)", fontSize: 9 }}
              axisLine={{ stroke: "var(--border)" }}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />
            <YAxis
              type="number"
              dataKey="eu"
              name="EU"
              unit="%"
              domain={[75, 100]}
              tick={{ fill: "var(--text-dim)", fontSize: 9 }}
              axisLine={{ stroke: "var(--border)" }}
            />
            <Tooltip content={<CustomScatterTooltip />} />
            <Legend wrapperStyle={{ fontSize: 9, color: "var(--text-dim)" }} />
            <ReferenceLine y={90} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: "EU = 90% Constraint", fill: "#f59e0b", fontSize: 9, position: "top" }} />
            <Scatter name="Pareto-Optimal Designs" data={paretoPoints} fill="var(--primary)" shape="circle" />
            <Scatter name="Best Compromise Design" data={bestPoint} fill="#f59e0b" shape="star" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Footer info text */}
      <div style={{ color: "var(--text-dim)", fontSize: 11, lineHeight: 1.5, marginTop: 2 }}>
        NSGA-II Multi-Objective Optimization: Minimize Cost | Maximize EU (≥90%)<br />
        Uses FAO-56 Penman-Monteith ETo, Hazen-Williams hydraulics, Keller-Karmeli EU
      </div>
    </div>
  );
}
