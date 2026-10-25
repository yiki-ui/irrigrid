"use client";
import React, { useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { ArrowUp, BarChart3, CloudRain, RefreshCw } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const MONTHS_LONG = ["January","February","March","April","May","June","July","August","September","October","November","December"];

// Rwanda long-term monthly defaults (mm) — Northern Province highland pattern
const DEFAULT_RAIN: number[] = [126, 125, 206, 183, 142, 73, 45, 92, 139, 190, 218, 154];

/** USDA Soil Conservation method for effective rainfall */
function usdaEffective(r: number): number {
  if (r <= 0) return 0;
  if (r <= 75) return r * (0.8 - 0.000984 * r);
  return r * (0.6 - 0.000984 * r) + 15;
}

/** Fixed 80% method */
function fixed80(r: number): number {
  return r * 0.8;
}

/** Dependable rain (75th percentile estimate = 70%) */
function dependable(r: number): number {
  return r * 0.7;
}

export default function RainfallPanel() {
  const { monthlyRainfall, updateRainfallMonth, setMonthlyRainfall, location } = useIrriGridStore();
  const [effMethod, setEffMethod] = useState("USDA S.C. Method");
  const [showChart, setShowChart] = useState(false);

  const totalRain = monthlyRainfall.reduce((s, m) => s + m.rainfall_mm, 0);
  const totalEffective = monthlyRainfall.reduce((s, m) => s + m.effective_rain_mm, 0);

  function loadDefaults() {
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    setMonthlyRainfall(
      DEFAULT_RAIN.map((rain, i) => ({
        month: months[i],
        rainfall_mm: rain,
        effective_rain_mm: Math.round(usdaEffective(rain) * 10) / 10,
      }))
    );
  }

  function recalcEffective() {
    const effFn = effMethod === "USDA S.C. Method" ? usdaEffective
      : effMethod === "Fixed Percentage (80%)" ? fixed80
      : dependable;
    setMonthlyRainfall(
      monthlyRainfall.map(m => ({
        ...m,
        effective_rain_mm: Math.round(effFn(m.rainfall_mm) * 10) / 10,
      }))
    );
  }

  const chartData = MONTHS.map((m, i) => ({
    month: m,
    Rain: monthlyRainfall[i]?.rainfall_mm ?? 0,
    "Eff. Rain": monthlyRainfall[i]?.effective_rain_mm ?? 0,
  }));

  return (
    <div style={{ padding: 4 }}>
      <h2 style={{ color: "var(--primary)", fontSize: 18, margin: "0 0 16px", display: "flex", alignItems: "center", gap: 8 }}>
        <CloudRain size={18} color="var(--primary)" /> Rain &amp; Effective Rain
      </h2>

      {/* Settings */}
      <div className="hud-box" style={{ marginBottom: 16 }}>
        <div className="hud-box-title">Settings</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 20px" }}>
          <div>
            <label className="hud-label">Station</label>
            <input className="hud-input" defaultValue={location.district || "Kigali"} />
          </div>
          <div>
            <label className="hud-label">Eff. Rain Method</label>
            <select className="hud-select" value={effMethod} onChange={e => setEffMethod(e.target.value)}>
              <option>USDA S.C. Method</option>
              <option>Fixed Percentage (80%)</option>
              <option>Dependable Rain</option>
            </select>
          </div>
        </div>
      </div>

      {/* Monthly Rainfall Table */}
      <div style={{ fontWeight: 600, color: "var(--text-dim)", fontSize: 11, marginBottom: 8, letterSpacing: 1 }}>Monthly Rainfall Data:</div>
      <table className="hud-table" style={{ width: "100%" }}>
        <thead>
          <tr>
            <th style={{ width: 28 }}>#</th>
            <th>Month</th>
            <th>Rain (mm)</th>
            <th>Eff. Rain (mm)</th>
          </tr>
        </thead>
        <tbody>
          {MONTHS_LONG.map((month, i) => (
            <tr key={month}>
              <td className="row-num">{i + 1}</td>
              <td>{month}</td>
              <td>
                <input
                  className="hud-input"
                  style={{ width: 80 }}
                  type="number"
                  value={monthlyRainfall[i]?.rainfall_mm ?? 0}
                  onChange={e => updateRainfallMonth(i, parseFloat(e.target.value) || 0)}
                />
              </td>
              <td style={{ color: "var(--accent)", fontWeight: 600 }}>
                {(monthlyRainfall[i]?.effective_rain_mm ?? 0).toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Summary */}
      <div style={{ marginTop: 12, padding: "8px 12px", background: "var(--bg-card)", border: "1px solid var(--border)", fontSize: 11, color: "var(--text-dim)", borderRadius: 4 }}>
        Total Annual Rain: <span style={{ color: "var(--primary)" }}>{totalRain.toFixed(0)} mm</span>
        &nbsp;|&nbsp;
        Total Effective Rain: <span style={{ color: "var(--accent)" }}>{totalEffective.toFixed(0)} mm</span>
        &nbsp;|&nbsp;
        Efficiency: <span style={{ color: totalRain > 0 ? "var(--success)" : "var(--text-dim)" }}>
          {totalRain > 0 ? ((totalEffective / totalRain) * 100).toFixed(0) : "—"}%
        </span>
      </div>

      {/* Chart */}
      {showChart && (
        <div style={{ marginTop: 16, background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 8px" }}>
          <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", marginBottom: 8 }}>
            Monthly Rainfall vs Effective Rainfall (mm)
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="month" tick={{ fill: "var(--text-dim)", fontSize: 9 }} axisLine={{ stroke: "var(--border)" }} />
              <YAxis tick={{ fill: "var(--text-dim)", fontSize: 9 }} axisLine={{ stroke: "var(--border)" }} />
              <Tooltip
                contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 11, color: "var(--text)" }}
              />
              <Legend wrapperStyle={{ fontSize: 10, color: "var(--text-dim)" }} />
              <Bar dataKey="Rain" fill="var(--primary)" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Eff. Rain" fill="var(--accent)" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Action Buttons */}
      <div className="action-row" style={{ marginTop: 12 }}>
        <button className="hud-btn" onClick={loadDefaults}>
          <ArrowUp size={12} /> Load Default Rain Data
        </button>
        <button className="hud-btn primary" onClick={recalcEffective}>
          <RefreshCw size={12} /> Calculate Effective Rain
        </button>
        <button className="hud-btn" onClick={() => setShowChart(v => !v)}>
          <BarChart3 size={12} /> {showChart ? "Hide Chart" : "Show Chart"}
        </button>
      </div>
    </div>
  );
}
