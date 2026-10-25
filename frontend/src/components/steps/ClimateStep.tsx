"use client";

import React, { useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { fetchWeather } from "@/lib/api";
import { estimateFAO56ETo } from "@/lib/calculations";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { Sun, CloudLightning, RefreshCw, BarChart2, Zap } from "lucide-react";

export default function ClimateStep() {
  const { location, monthlyClimate, updateClimateMonth, setMonthlyClimate } = useIrriGridStore();
  const [loadingNasa, setLoadingNasa] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  const handleFetchNASA = async () => {
    try {
      setLoadingNasa(true);
      setSyncStatus("Connecting to NASA POWER agrometeorology API...");
      const data = await fetchWeather(location.lat, location.lon);

      if (data && data.monthly_climate) {
        // Map NASA climate to store format
        const updated = monthlyClimate.map((m, idx) => {
          const fetched = data.monthly_climate[idx] || {};
          const tmin = fetched.tmin ?? m.tmin;
          const tmax = fetched.tmax ?? m.tmax;
          const rhmin = fetched.rhmin ?? m.rhmin;
          const rhmax = fetched.rhmax ?? m.rhmax;
          const wind = fetched.wind_speed ?? m.wind_speed;
          const sun = fetched.sunshine_hours ?? m.sunshine_hours;
          const eto = estimateFAO56ETo(tmin, tmax, rhmin, rhmax, wind, sun, location.lat, location.elevation_m, (idx + 1) * 30);

          return {
            ...m,
            tmin,
            tmax,
            rhmin,
            rhmax,
            wind_speed: wind,
            sunshine_hours: sun,
            eto,
          };
        });
        setMonthlyClimate(updated);
        setSyncStatus(`Synchronized with NASA POWER (${data.source || "cached"})`);
      }
    } catch (err: any) {
      setSyncStatus("Failed to fetch live NASA data; using regional defaults.");
    } finally {
      setLoadingNasa(false);
    }
  };

  const handleCellChange = (index: number, field: string, val: number) => {
    const row = monthlyClimate[index];
    const updatedRow = { ...row, [field]: val };
    // Recalculate FAO-56 ETo for this month
    const newETo = estimateFAO56ETo(
      field === "tmin" ? val : row.tmin,
      field === "tmax" ? val : row.tmax,
      field === "rhmin" ? val : row.rhmin,
      field === "rhmax" ? val : row.rhmax,
      field === "wind_speed" ? val : row.wind_speed,
      field === "sunshine_hours" ? val : row.sunshine_hours,
      location.lat,
      location.elevation_m,
      (index + 1) * 30
    );
    updateClimateMonth(index, { [field]: val, eto: newETo });
  };

  // Summary metrics
  const avgTemp = Math.round(
    monthlyClimate.reduce((sum, m) => sum + (m.tmin + m.tmax) / 2, 0) / monthlyClimate.length * 10
  ) / 10;
  const annualEtoMm = Math.round(monthlyClimate.reduce((sum, m) => sum + m.eto * 30.4, 0));
  const peakEtoMonth = [...monthlyClimate].sort((a, b) => b.eto - a.eto)[0];

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <Sun size={18} />
            Step 02: Agrometeorological Parameters & FAO-56 Reference ETo
          </div>
          <button
            onClick={handleFetchNASA}
            disabled={loadingNasa}
            className="btn btn-outline"
            style={{ padding: "4px 10px", fontSize: "0.75rem" }}
          >
            <CloudLightning size={14} />
            {loadingNasa ? "Fetching NASA..." : "Auto-Fetch NASA POWER"}
          </button>
        </div>

        {syncStatus && (
          <div style={{ fontSize: "0.78rem", color: "var(--accent)", marginBottom: "0.85rem", fontFamily: "var(--font-mono)" }}>
            ⚡ {syncStatus}
          </div>
        )}

        <div className="grid-3" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Annual Reference ETo"
            value={annualEtoMm}
            unit="mm/year"
            subtext="FAO-56 Penman-Monteith"
            color="var(--primary)"
          />
          <StatCard
            label="Mean Temperature"
            value={avgTemp}
            unit="°C"
            subtext="Annual daily average"
          />
          <StatCard
            label="Peak ETo Demand"
            value={peakEtoMonth.eto}
            unit="mm/day"
            subtext={`Month: ${peakEtoMonth.month}`}
            color="var(--warning)"
          />
        </div>

        {/* ETo Visual Spark Bar Chart */}
        <div style={{ background: "rgba(10, 15, 30, 0.7)", border: "1px solid var(--border)", borderRadius: "4px", padding: "1rem", marginBottom: "1.25rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--primary)", textTransform: "uppercase", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}>
            <BarChart2 size={14} /> Monthly ETo Distribution (mm/day)
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", height: "90px", gap: "8px" }}>
            {monthlyClimate.map((m) => {
              const heightPct = Math.min(100, Math.max(15, (m.eto / 5.0) * 100));
              return (
                <div key={m.month} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", height: "100%", justifyContent: "flex-end" }}>
                  <span style={{ fontSize: "0.68rem", color: "var(--text-bright)", fontFamily: "var(--font-mono)", marginBottom: "4px" }}>
                    {m.eto}
                  </span>
                  <div
                    style={{
                      width: "100%",
                      height: `${heightPct}%`,
                      background: "linear-gradient(180deg, var(--primary) 0%, rgba(0, 229, 255, 0.2) 100%)",
                      borderRadius: "2px 2px 0 0",
                      border: "1px solid var(--primary)",
                    }}
                  />
                  <span style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "4px" }}>{m.month}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Editable Climate Data Grid */}
        <div className="hud-table-container">
          <table className="hud-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>T Min (°C)</th>
                <th>T Max (°C)</th>
                <th>RH Min (%)</th>
                <th>RH Max (%)</th>
                <th>Wind (m/s)</th>
                <th>Sun (h)</th>
                <th style={{ color: "var(--accent)" }}>ETo (mm/d)</th>
              </tr>
            </thead>
            <tbody>
              {monthlyClimate.map((m, idx) => (
                <tr key={m.month}>
                  <td style={{ fontWeight: 600, color: "var(--text-bright)" }}>{m.month}</td>
                  <td>
                    <input
                      type="number"
                      step="0.1"
                      value={m.tmin}
                      onChange={(e) => handleCellChange(idx, "tmin", parseFloat(e.target.value) || 0)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.1"
                      value={m.tmax}
                      onChange={(e) => handleCellChange(idx, "tmax", parseFloat(e.target.value) || 0)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="1"
                      value={m.rhmin}
                      onChange={(e) => handleCellChange(idx, "rhmin", parseFloat(e.target.value) || 0)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="1"
                      value={m.rhmax}
                      onChange={(e) => handleCellChange(idx, "rhmax", parseFloat(e.target.value) || 0)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.1"
                      value={m.wind_speed}
                      onChange={(e) => handleCellChange(idx, "wind_speed", parseFloat(e.target.value) || 0)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.1"
                      value={m.sunshine_hours}
                      onChange={(e) => handleCellChange(idx, "sunshine_hours", parseFloat(e.target.value) || 0)}
                    />
                  </td>
                  <td style={{ fontWeight: 700, color: "var(--accent)" }}>{m.eto.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <StepNav />
    </div>
  );
}
