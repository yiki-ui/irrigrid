"use client";
import React, { useEffect, useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { ArrowUpRight, BarChart3, Sprout } from "lucide-react";
import { fetchCrops } from "@/lib/api";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
} from "recharts";

const COMMON_CROPS = ["Tomato","Maize","Beans","Pepper","Onion","Cabbage","Potato","Wheat","Sorghum","Cassava"];

export default function CropPanel() {
  const { crop, setCrop } = useIrriGridStore();
  const [crops, setCrops] = useState<any[]>([]);
  const [showKcChart, setShowKcChart] = useState(false);

  useEffect(() => {
    fetchCrops().then(setCrops).catch(() => {});
  }, []);

  const options = crops.length > 0 ? crops.map(c => c.name) : COMMON_CROPS;

  function handleSelect(name: string) {
    const found = crops.find(c => c.name === name);
    if (found) setCrop({ name: found.name, kc_init: found.kc_init, kc_mid: found.kc_mid, kc_end: found.kc_end, root_depth_m: found.root_depth_m, depletion_fraction: found.depletion_fraction, stages: found.stages });
    else setCrop({ name });
  }

  // Calculate total days & harvest date
  const stages = crop.stages || { initial: 30, development: 40, mid: 45, late: 30 };
  const totalDays = stages.initial + stages.development + stages.mid + stages.late;
  const plantDate = new Date(crop.planting_date || "2026-09-15");
  const harvestDate = new Date(plantDate);
  harvestDate.setDate(harvestDate.getDate() + totalDays);
  const harvestStr = harvestDate.toISOString().split("T")[0];

  // Build Kc curve data points for the chart
  const kcCurveData = (() => {
    const kc_init = crop.kc_init ?? 0.5;
    const kc_mid = crop.kc_mid ?? 1.0;
    const kc_end = crop.kc_end ?? 0.6;
    const { initial, development, mid, late } = stages;
    const points: { day: number; Kc: number; stage: string }[] = [];
    // Initial
    points.push({ day: 0, Kc: kc_init, stage: "Initial" });
    points.push({ day: initial, Kc: kc_init, stage: "Initial" });
    // Development (linear ramp)
    points.push({ day: initial + development, Kc: kc_mid, stage: "Development" });
    // Mid-season
    points.push({ day: initial + development + mid, Kc: kc_mid, stage: "Mid-Season" });
    // Late
    points.push({ day: totalDays, Kc: kc_end, stage: "Late" });
    return points;
  })();

  function exportCsvData() {
    const kc_init = crop.kc_init ?? 0.5;
    const kc_mid = crop.kc_mid ?? 1.0;
    const kc_end = crop.kc_end ?? 0.6;
    const rows = [
      ["Crop Name", crop.name || "Unknown"],
      ["Planting Date", crop.planting_date || "2026-09-15"],
      ["Harvest Date", harvestStr],
      ["Total Days", totalDays],
      [],
      ["Stage", "Days", "Kc Value", "Root Depth (m)"],
      ["Initial", stages.initial, kc_init, (crop.root_depth_m * 0.5).toFixed(2)],
      ["Development", stages.development, ((kc_init + kc_mid) / 2).toFixed(2), (crop.root_depth_m * 0.6).toFixed(2)],
      ["Mid-Season", stages.mid, kc_mid, crop.root_depth_m.toFixed(2)],
      ["Late Season", stages.late, kc_end, crop.root_depth_m.toFixed(2)],
      [],
      ["Kc Init", kc_init],
      ["Kc Mid", kc_mid],
      ["Kc End", kc_end],
      ["Root Depth (m)", crop.root_depth_m ?? 0.5],
      ["Critical Depletion Fraction", crop.depletion_fraction ?? 0.5],
    ];
    const csv = rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `IrriGrid_Crop_${crop.name || "data"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={{ padding: 4 }}>
      <h2 style={{ color: "var(--primary)", fontSize: 18, margin: "0 0 16px", display: "flex", alignItems: "center", gap: 8 }}>
        <Sprout size={18} color="var(--primary)" /> Crop Data - Growth Stages &amp; Kc Values
      </h2>

      {/* Crop Selection */}
      <div className="hud-box" style={{ marginBottom: 16 }}>
        <div className="hud-box-title">Crop Selection</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 20px" }}>
          <div>
            <label className="hud-label">Crop Name</label>
            <select className="hud-select" value={crop.name} onChange={e => handleSelect(e.target.value)}>
              {options.map(name => <option key={name}>{name}</option>)}
            </select>
          </div>
          <div>
            <label className="hud-label">Planting Date</label>
            <input type="date" className="hud-input" value={crop.planting_date || "2026-09-15"} onChange={e => setCrop({ planting_date: e.target.value })} />
          </div>
          <div>
            <label className="hud-label">Harvest Date</label>
            <input type="text" className="hud-input" value={harvestStr} readOnly style={{ color: "var(--text-dim)" }} />
          </div>
          <div>
            <label className="hud-label">Total Days</label>
            <input type="number" className="hud-input" value={totalDays} readOnly style={{ color: "var(--primary)" }} />
          </div>
        </div>
      </div>

      {/* Growth Stages & Kc Table */}
      <div style={{ fontWeight: 600, color: "var(--text-dim)", fontSize: 11, marginBottom: 8, letterSpacing: 1 }}>Kc Values &amp; Growth Stages:</div>
      <table className="hud-table" style={{ width: "100%", marginBottom: 16 }}>
        <thead>
          <tr>
            <th>#</th>
            <th>Stage</th>
            <th>Days</th>
            <th>Kc Value</th>
            <th>Rooting Depth</th>
          </tr>
        </thead>
        <tbody>
          {[
            { name: "Initial",    days: stages.initial,     kc: crop.kc_init, depth: (crop.root_depth_m ?? 0.5) * 0.5 },
            { name: "Development",days: stages.development,  kc: ((crop.kc_init ?? 0.5) + (crop.kc_mid ?? 1.0)) / 2, depth: (crop.root_depth_m ?? 0.5) * 0.6 },
            { name: "Mid-Season", days: stages.mid,          kc: crop.kc_mid,  depth: crop.root_depth_m ?? 0.5 },
            { name: "Late Season",days: stages.late,         kc: crop.kc_end,  depth: crop.root_depth_m ?? 0.5 },
          ].map((row, i) => (
            <tr key={row.name}>
              <td className="row-num">{i + 1}</td>
              <td>{row.name}</td>
              <td><input className="hud-input" style={{ width: 55 }} type="number" defaultValue={row.days} /></td>
              <td style={{ color: "var(--primary)" }}>{(row.kc ?? 0).toFixed(2)}</td>
              <td style={{ color: "var(--text-dim)" }}>{(row.depth ?? 0).toFixed(2)} m</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Kc Curve Chart */}
      {showKcChart && (
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 8px", marginBottom: 16 }}>
          <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", marginBottom: 8 }}>
            FAO-56 Kc Curve — {crop.name || "Crop"} ({totalDays} days)
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={kcCurveData} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="day" tick={{ fill: "var(--text-dim)", fontSize: 9 }} axisLine={{ stroke: "var(--border)" }} label={{ value: "Day", position: "insideBottom", offset: -2, fill: "var(--text-dim)", fontSize: 9 }} />
              <YAxis domain={[0, 1.4]} tick={{ fill: "var(--text-dim)", fontSize: 9 }} axisLine={{ stroke: "var(--border)" }} />
              <Tooltip contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 11, color: "var(--text)" }} />
              <ReferenceLine y={1.0} stroke="var(--border)" strokeDasharray="3 3" label={{ value: "Kc=1.0", fill: "var(--text-dim)", fontSize: 8 }} />
              <Line type="linear" dataKey="Kc" stroke="var(--primary)" strokeWidth={2} dot={{ fill: "var(--primary)", r: 4 }} name="Kc" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Additional Parameters */}
      <div className="hud-box" style={{ marginBottom: 16 }}>
        <div className="hud-box-title">Additional Parameters</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 20px" }}>
          <div>
            <label className="hud-label">Critical Depletion (fraction)</label>
            <input type="number" className="hud-input" defaultValue={crop.depletion_fraction} step={0.01} />
          </div>
          <div>
            <label className="hud-label">Yield Response Factor (Ky)</label>
            <input type="number" className="hud-input" defaultValue={1.05} step={0.01} />
          </div>
          <div>
            <label className="hud-label">Max Rooting Depth (m)</label>
            <input type="number" className="hud-input" value={crop.root_depth_m} step={0.1} onChange={e => setCrop({ root_depth_m: parseFloat(e.target.value) })} />
          </div>
          <div>
            <label className="hud-label">Expected Yield (tons/ha)</label>
            <input type="number" className="hud-input" defaultValue={55.0} step={0.1} />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-row">
        <button className="hud-btn" onClick={() => setShowKcChart(v => !v)}>
          <BarChart3 size={12} /> {showKcChart ? "Hide Kc Curve" : "Show Kc Curve"}
        </button>
        <button className="hud-btn primary" onClick={exportCsvData}>
          <ArrowUpRight size={12} /> Export Crop Data
        </button>
      </div>
    </div>
  );
}
