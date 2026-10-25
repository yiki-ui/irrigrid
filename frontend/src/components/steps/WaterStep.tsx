"use client";

import React, { useMemo } from "react";
import { useIrriGridStore } from "@/lib/store";
import { MonthlyWaterBalance } from "@/lib/types";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { Droplets, TrendingDown, Layers, BarChart } from "lucide-react";

export default function WaterStep() {
  const { monthlyClimate, monthlyRainfall, crop, location, setWaterBalance } = useIrriGridStore();

  // Compute month-by-month crop water balance
  const balanceRows: MonthlyWaterBalance[] = useMemo(() => {
    return monthlyClimate.map((c, idx) => {
      const rain = monthlyRainfall[idx]?.effective_rain_mm || 0;
      // Determine Kc for month based on planting date and growth stage
      // For general seasonal estimation, interpolate between kc_init, kc_mid, kc_end
      let kc = crop.kc_mid;
      if (idx < 2 || idx > 10) kc = crop.kc_init;
      else if (idx >= 2 && idx <= 5) kc = crop.kc_mid;
      else kc = crop.kc_end;

      const daysInMonth = 30.4;
      const etcMmMonth = Math.round(c.eto * kc * daysInMonth * 10) / 10;
      const nirMm = Math.max(0, Math.round((etcMmMonth - rain) * 10) / 10);
      const nirM3 = Math.round(nirMm * 10 * location.area_ha * 10) / 10;

      return {
        month: c.month,
        eto_mm_day: c.eto,
        kc: Math.round(kc * 100) / 100,
        etc_mm_month: etcMmMonth,
        effective_rain_mm: rain,
        nir_mm: nirMm,
        nir_m3: nirM3,
        // new field names
        eto_mm: parseFloat((c.eto * 30).toFixed(1)),
        etc_mm: etcMmMonth,
        rainfall_mm: monthlyRainfall[idx]?.rainfall_mm || 0,
        net_irrigation_mm: nirMm,
      };
    });
  }, [monthlyClimate, monthlyRainfall, crop, location.area_ha]);

  // Save to store
  React.useEffect(() => {
    setWaterBalance(balanceRows);
  }, [balanceRows, setWaterBalance]);

  const totalEtcMm = Math.round(balanceRows.reduce((s, r) => s + r.etc_mm_month, 0));
  const totalNirMm = Math.round(balanceRows.reduce((s, r) => s + r.nir_mm, 0));
  const totalNirM3 = Math.round(balanceRows.reduce((s, r) => s + r.nir_m3, 0));
  const totalGirM3 = Math.round(totalNirM3 / 0.9); // 90% drip efficiency

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <Droplets size={18} />
            Step 06: Crop Evapotranspiration (ETc) & Net Irrigation Demand (NIR)
          </div>
          <span className="badge-tag">FAO-56 Water Balance</span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-dim)", marginBottom: "1rem" }}>
          Net Irrigation Requirement (NIR) is calculated as ETc minus effective precipitation. Volume reflects your specific field area of {location.area_ha} ha.
        </p>

        {/* Summary Metric Cards */}
        <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Net Irrigation Vol."
            value={totalNirM3.toLocaleString()}
            unit="m³"
            subtext={`${totalNirMm} mm depth`}
            color="var(--primary)"
          />
          <StatCard
            label="Gross Irrigation Vol."
            value={totalGirM3.toLocaleString()}
            unit="m³"
            subtext="90% Drip Efficiency (GIR)"
            color="var(--accent)"
          />
          <StatCard
            label="Total Crop Water (ETc)"
            value={totalEtcMm}
            unit="mm"
            subtext={`ETo × Kc for ${crop.name}`}
          />
          <StatCard
            label="Rainfall Offset"
            value={Math.round(totalEtcMm - totalNirMm)}
            unit="mm"
            subtext="Supplied by natural rain"
            color="var(--success)"
          />
        </div>

        {/* Demand vs Rain Visual Comparison */}
        <div style={{ background: "rgba(10, 15, 30, 0.7)", border: "1px solid var(--border)", borderRadius: "4px", padding: "1rem", marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <div style={{ fontSize: "0.75rem", color: "var(--primary)", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "6px" }}>
              <BarChart size={14} /> Monthly Water Balance (ETc vs Effective Rain vs Net Deficit)
            </div>
            <div style={{ display: "flex", gap: "12px", fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
              <span style={{ color: "var(--text-bright)" }}>■ ETc (Need)</span>
              <span style={{ color: "var(--success)" }}>■ Rain (Free)</span>
              <span style={{ color: "var(--danger)" }}>■ NIR (To Irrigate)</span>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-end", height: "110px", gap: "6px" }}>
            {balanceRows.map((r) => {
              const maxScale = 160;
              const etcH = Math.min(100, Math.max(5, (r.etc_mm_month / maxScale) * 100));
              const rainH = Math.min(100, Math.max(5, (r.effective_rain_mm / maxScale) * 100));
              const nirH = Math.min(100, Math.max(0, (r.nir_mm / maxScale) * 100));

              return (
                <div key={r.month} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", height: "100%", justifyContent: "flex-end" }}>
                  <div style={{ display: "flex", gap: "2px", alignItems: "flex-end", width: "100%", height: "80px" }}>
                    <div style={{ flex: 1, height: `${etcH}%`, background: "rgba(255, 255, 255, 0.4)", borderRadius: "2px 2px 0 0" }} title={`ETc: ${r.etc_mm_month}mm`} />
                    <div style={{ flex: 1, height: `${rainH}%`, background: "var(--success)", borderRadius: "2px 2px 0 0" }} title={`Rain: ${r.effective_rain_mm}mm`} />
                    <div style={{ flex: 1, height: `${nirH}%`, background: "var(--danger)", borderRadius: "2px 2px 0 0" }} title={`NIR: ${r.nir_mm}mm`} />
                  </div>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "4px" }}>{r.month}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Monthly Balance Table */}
        <div className="hud-table-container">
          <table className="hud-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>ETo (mm/d)</th>
                <th>Kc</th>
                <th>ETc (mm/mo)</th>
                <th>Eff. Rain (mm)</th>
                <th style={{ color: "var(--danger)" }}>NIR (mm)</th>
                <th style={{ color: "var(--primary)" }}>NIR Volume (m³)</th>
              </tr>
            </thead>
            <tbody>
              {balanceRows.map((r) => (
                <tr key={r.month}>
                  <td style={{ fontWeight: 600, color: "var(--text-bright)" }}>{r.month}</td>
                  <td>{r.eto_mm_day.toFixed(1)}</td>
                  <td>{r.kc.toFixed(2)}</td>
                  <td>{r.etc_mm_month.toFixed(1)}</td>
                  <td style={{ color: "var(--success)" }}>{r.effective_rain_mm.toFixed(1)}</td>
                  <td style={{ fontWeight: 700, color: r.nir_mm > 0 ? "var(--danger)" : "var(--text-dim)" }}>
                    {r.nir_mm.toFixed(1)}
                  </td>
                  <td style={{ fontWeight: 700, color: "var(--primary)" }}>{r.nir_m3.toLocaleString()}</td>
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
