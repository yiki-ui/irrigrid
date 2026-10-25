"use client";

import React from "react";
import { useIrriGridStore } from "@/lib/store";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { CloudRain, BarChart, Info } from "lucide-react";

export default function RainfallStep() {
  const { monthlyRainfall, updateRainfallMonth } = useIrriGridStore();

  const totalRainMm = Math.round(monthlyRainfall.reduce((s, r) => s + r.rainfall_mm, 0));
  const totalEffRainMm = Math.round(monthlyRainfall.reduce((s, r) => s + r.effective_rain_mm, 0));
  const effPct = totalRainMm > 0 ? Math.round((totalEffRainMm / totalRainMm) * 100) : 0;

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <CloudRain size={18} />
            Step 03: Monthly Precipitation & USDA Effective Rainfall
          </div>
          <span className="badge-tag">USDA SCS Method</span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-dim)", marginBottom: "1rem" }}>
          Rainfall is converted to crop-available effective precipitation using the USDA Soil Conservation Service method, excluding surface runoff and deep percolation.
        </p>

        <div className="grid-3" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Total Annual Rainfall"
            value={totalRainMm}
            unit="mm"
            subtext="Rwanda bimodal pattern"
            color="var(--primary)"
          />
          <StatCard
            label="Effective Rainfall"
            value={totalEffRainMm}
            unit="mm"
            subtext="Plant-usable water"
            color="var(--success)"
          />
          <StatCard
            label="Rain Efficiency"
            value={effPct}
            unit="%"
            subtext="Effective vs Total"
          />
        </div>

        {/* Rainfall Comparison Chart */}
        <div style={{ background: "rgba(10, 15, 30, 0.7)", border: "1px solid var(--border)", borderRadius: "4px", padding: "1rem", marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <div style={{ fontSize: "0.75rem", color: "var(--primary)", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "6px" }}>
              <BarChart size={14} /> Total vs Effective Rain (mm)
            </div>
            <div style={{ display: "flex", gap: "12px", fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-dim)" }}>
                <span style={{ width: 8, height: 8, background: "rgba(0, 229, 255, 0.4)", borderRadius: 2 }} /> Total
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--success)" }}>
                <span style={{ width: 8, height: 8, background: "var(--success)", borderRadius: 2 }} /> Effective
              </span>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-end", height: "110px", gap: "6px" }}>
            {monthlyRainfall.map((r) => {
              const maxScale = 200;
              const totalHeight = Math.min(100, Math.max(5, (r.rainfall_mm / maxScale) * 100));
              const effHeight = Math.min(100, Math.max(5, (r.effective_rain_mm / maxScale) * 100));

              return (
                <div key={r.month} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", height: "100%", justifyContent: "flex-end" }}>
                  <div style={{ display: "flex", gap: "2px", alignItems: "flex-end", width: "100%", height: "80px" }}>
                    <div
                      style={{
                        flex: 1,
                        height: `${totalHeight}%`,
                        background: "rgba(0, 229, 255, 0.35)",
                        borderRadius: "2px 2px 0 0",
                      }}
                      title={`Total: ${r.rainfall_mm}mm`}
                    />
                    <div
                      style={{
                        flex: 1,
                        height: `${effHeight}%`,
                        background: "var(--success)",
                        borderRadius: "2px 2px 0 0",
                      }}
                      title={`Effective: ${r.effective_rain_mm}mm`}
                    />
                  </div>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "4px" }}>{r.month}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Table */}
        <div className="hud-table-container">
          <table className="hud-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Total Rainfall (mm)</th>
                <th style={{ color: "var(--success)" }}>Effective Rainfall (mm)</th>
                <th>Runoff / Infiltration Loss (mm)</th>
              </tr>
            </thead>
            <tbody>
              {monthlyRainfall.map((r, idx) => (
                <tr key={r.month}>
                  <td style={{ fontWeight: 600, color: "var(--text-bright)" }}>{r.month}</td>
                  <td>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="1000"
                      value={r.rainfall_mm}
                      onChange={(e) => updateRainfallMonth(idx, parseFloat(e.target.value) || 0)}
                    />
                  </td>
                  <td style={{ fontWeight: 700, color: "var(--success)" }}>{r.effective_rain_mm}</td>
                  <td style={{ color: "var(--text-dim)" }}>
                    {Math.max(0, Math.round((r.rainfall_mm - r.effective_rain_mm) * 10) / 10)}
                  </td>
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
