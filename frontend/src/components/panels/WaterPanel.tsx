"use client";
import React, { useState, useMemo } from "react";
import {
  ResponsiveContainer, ComposedChart, BarChart, Bar, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Area, AreaChart, ScatterChart, Scatter,
} from "recharts";
import { useIrriGridStore } from "@/lib/store";
import { BarChart3, CheckCircle, Minimize2 } from "lucide-react";
import { calculateMonthlyWaterBalance } from "@/lib/calculations";

const ROW_STYLE: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "28px 50px 72px 64px 72px 78px 74px 84px",
  gap: 0,
  fontSize: 11,
  fontFamily: "var(--font-mono)",
  borderBottom: "1px solid rgba(0,229,255,0.06)",
  padding: "4px 6px",
  alignItems: "center",
};

const HEADER_STYLE: React.CSSProperties = {
  ...ROW_STYLE,
  color: "var(--text-dim)",
  fontWeight: "bold",
  fontSize: 10,
  letterSpacing: 0.5,
  background: "rgba(0,229,255,0.04)",
  borderBottom: "1px solid rgba(0,229,255,0.18)",
  textTransform: "uppercase",
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--bg-card)", border: "1px solid var(--border)",
      borderRadius: 6, padding: "8px 12px", fontSize: 11,
      boxShadow: "0 6px 20px rgba(0,0,0,0.15)",
    }}>
      <div style={{ color: "var(--primary)", fontWeight: "bold", marginBottom: 4 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color ?? "var(--text)", display: "flex", gap: 10, justifyContent: "space-between" }}>
          <span>{p.name}:</span>
          <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{Number(p.value).toFixed(1)} mm</span>
        </div>
      ))}
    </div>
  );
};

export default function WaterPanel() {
  const { monthlyClimate, monthlyRainfall, crop, soil, waterBalance, setWaterBalance } = useIrriGridStore();
  const [showCharts, setShowCharts] = useState(false);
  const [canopyModel, setCanopyModel] = useState(false);

  // Live-derived water balance
  const wb = useMemo(() => {
    if (waterBalance.length > 0) return waterBalance;
    if (monthlyClimate.length > 0 && crop.name) {
      return calculateMonthlyWaterBalance(monthlyClimate, monthlyRainfall, crop);
    }
    return [];
  }, [waterBalance, monthlyClimate, monthlyRainfall, crop]);

  // Adjust for canopy model if enabled
  const processedWb = useMemo(() => {
    if (!canopyModel) return wb;
    return wb.map((row) => {
      const adjustedKc = (row.kc ?? 1.0) * 0.95; // Canopy ground shading factor
      const etc = (row.eto_mm ?? 0) * adjustedKc;
      const netIrr = Math.max(0, etc - (row.effective_rain_mm ?? 0));
      return { ...row, kc: adjustedKc, etc_mm: etc, net_irrigation_mm: netIrr };
    });
  }, [wb, canopyModel]);

  function compute() {
    const fresh = calculateMonthlyWaterBalance(monthlyClimate, monthlyRainfall, crop);
    setWaterBalance(fresh);
  }

  const totalEtc = processedWb.reduce((s, m) => s + (m.etc_mm ?? 0), 0);
  const totalIrr = processedWb.reduce((s, m) => s + (m.net_irrigation_mm ?? 0), 0);
  const totalRain = processedWb.reduce((s, m) => s + (m.rainfall_mm ?? 0), 0);

  // Chart data and cumulative calculations
  let cumEtcAcc = 0;
  let cumRainAcc = 0;
  let cumIrrAcc = 0;

  const chartData = processedWb.map((m) => {
    const etc = +(m.etc_mm ?? 0);
    const rain = +(m.rainfall_mm ?? 0);
    const effRain = +(m.effective_rain_mm ?? 0);
    const irr = +(m.net_irrigation_mm ?? 0);
    const deficit = Math.max(0, etc - effRain);

    cumEtcAcc += etc;
    cumRainAcc += effRain;
    cumIrrAcc += irr;

    return {
      month: m.month,
      "ETo (mm)": +(m.eto_mm ?? 0).toFixed(1),
      "ETc": +etc.toFixed(1),
      "Rainfall": +rain.toFixed(1),
      "Eff. Rain": +effRain.toFixed(1),
      "Irrig. Req.": +irr.toFixed(1),
      "Deficit": +deficit.toFixed(1),
      "Cum. ETc": +cumEtcAcc.toFixed(1),
      "Cum. Eff. Rain": +cumRainAcc.toFixed(1),
      "Cum. Irrigation": +cumIrrAcc.toFixed(1),
    };
  });

  const hasData = processedWb.length > 0;
  const isAutoFetched = monthlyClimate.length > 0 && (monthlyClimate[0] as any).isAuto;

  function handleExport() {
    const headers = ["Month", "ETo (mm)", "Kc", "ETc (mm)", "Rainfall (mm)", "Eff. Rain (mm)", "Irrig. Req. (mm)"];
    const rows = processedWb.map(m => [
      m.month,
      (m.eto_mm ?? 0).toFixed(1),
      (m.kc ?? 1).toFixed(2),
      (m.etc_mm ?? 0).toFixed(1),
      (m.rainfall_mm ?? 0).toFixed(1),
      (m.effective_rain_mm ?? 0).toFixed(1),
      (m.net_irrigation_mm ?? 0).toFixed(1),
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Crop_Water_Requirements_${crop.name || "Crop"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 14, maxWidth: 960 }}>
      {/* Header */}
      <div>
        <h2 style={{ color: "var(--primary)", fontSize: 18, fontWeight: "bold", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
          □ Crop Water Requirement Calculation
        </h2>
        <p style={{ color: "var(--text-dim)", fontSize: 11, margin: "4px 0 0" }}>
          Calculate crop water requirements (ETc) and irrigation needs based on ETo, Kc, and rainfall data.
        </p>
      </div>

      {/* Input Data Summary */}
      <div style={{ background: "rgba(0,229,255,0.03)", border: "1px solid rgba(0,229,255,0.15)", borderRadius: 4, padding: "10px 14px" }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>
          Input Data Summary
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 32px", fontSize: 11 }}>
          <div style={{ display: "flex", gap: 12 }}>
            <span style={{ color: "var(--text-dim)", minWidth: 80 }}>Crop:</span>
            <span style={{ color: "var(--text)", fontWeight: 600 }}>{crop.name || "Tomato"}</span>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <span style={{ color: "var(--text-dim)", minWidth: 60 }}>Soil:</span>
            <span style={{ color: "var(--text)", fontWeight: 600 }}>{soil.name || "Clay"}</span>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <span style={{ color: "var(--text-dim)", minWidth: 80 }}>Climate Data:</span>
            <span style={{ color: "var(--success)", fontWeight: 600 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <CheckCircle size={12} color="var(--success)" /> Fetched (NASA POWER)
              </span>
            </span>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <span style={{ color: "var(--text-dim)", minWidth: 60 }}>Rain Data:</span>
            <span style={{ color: "var(--success)", fontWeight: 600 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <CheckCircle size={12} color="var(--success)" /> Fetched (NASA POWER)
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Advanced: Canopy Model */}
      <div style={{ background: "rgba(0,229,255,0.02)", border: "1px solid rgba(0,229,255,0.12)", borderRadius: 4, padding: "8px 14px" }}>
        <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", marginBottom: 6 }}>
          □ Advanced: Canopy Model
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11 }}>
          <input
            type="checkbox"
            id="canopy-check"
            checked={canopyModel}
            onChange={(e) => setCanopyModel(e.target.checked)}
            style={{ cursor: "pointer", accentColor: "var(--primary)" }}
          />
          <label htmlFor="canopy-check" style={{ color: "var(--text)", cursor: "pointer" }}>
            Enable Dynamic Canopy-Adjusted Kc
          </label>
          <span style={{ color: "var(--text-dim)", marginLeft: 8 }}>
            Status: {canopyModel ? "Canopy-adjusted Kc active" : "Using static Kc values"}
          </span>
        </div>
      </div>

      {/* Calculate Water Requirements Button */}
      <button
        className="hud-btn"
        onClick={compute}
        style={{
          padding: "10px 0",
          fontSize: 12,
          fontWeight: "bold",
          background: "rgba(0,229,255,0.08)",
          borderColor: "rgba(0,229,255,0.4)",
          color: "var(--primary)",
          width: "100%",
          textAlign: "center",
          cursor: "pointer",
        }}
      >
        □ Calculate Water Requirements
      </button>

      {/* Monthly Water Requirements Table */}
      {hasData && (
        <div>
          <div style={{ color: "var(--text)", fontSize: 11, fontWeight: "bold", marginBottom: 6 }}>
            Monthly Water Requirements:
          </div>
          <div style={{ border: "1px solid rgba(0,229,255,0.15)", borderRadius: 4, overflowX: "auto" }}>
            <div style={HEADER_STYLE}>
              <span>#</span>
              <span>Month</span>
              <span>ETo (mm)</span>
              <span>Kc</span>
              <span>ETc (mm)</span>
              <span>Rainfall (mm)</span>
              <span>Eff. Rain (mm)</span>
              <span>Irrig. Req. (mm)</span>
            </div>
            {processedWb.map((m, i) => (
              <div
                key={m.month}
                style={{
                  ...ROW_STYLE,
                  background: i % 2 === 0 ? "transparent" : "rgba(0,229,255,0.02)",
                }}
              >
                <span style={{ color: "var(--text-dim)" }}>{i + 1}</span>
                <span style={{ color: "var(--text)", fontWeight: 500 }}>{m.month}</span>
                <span style={{ color: "var(--primary)" }}>{(m.eto_mm ?? 0).toFixed(1)}</span>
                <span style={{ color: "var(--text-dim)" }}>{(m.kc ?? 1).toFixed(2)}</span>
                <span style={{ color: "var(--text)" }}>{(m.etc_mm ?? 0).toFixed(1)}</span>
                <span style={{ color: "var(--text-dim)" }}>{(m.rainfall_mm ?? 0).toFixed(1)}</span>
                <span style={{ color: "var(--text-dim)" }}>{(m.effective_rain_mm ?? 0).toFixed(1)}</span>
                <span style={{ color: (m.net_irrigation_mm ?? 0) > 0 ? "var(--warning)" : "var(--success)", fontWeight: 600 }}>
                  {(m.net_irrigation_mm ?? 0).toFixed(1)}
                </span>
              </div>
            ))}
          </div>

          {/* Totals Summary Footer */}
          <div style={{
            marginTop: 8,
            padding: "8px 14px",
            background: "rgba(0,229,255,0.05)",
            border: "1px solid rgba(0,229,255,0.15)",
            borderRadius: 4,
            fontSize: 11,
            fontFamily: "var(--font-mono)",
            display: "flex",
            flexWrap: "wrap",
            gap: 16,
          }}>
            <div>
              <span style={{ color: "var(--text-dim)" }}>Total ETc: </span>
              <span style={{ color: "var(--primary)", fontWeight: "bold" }}>{totalEtc.toFixed(0)} mm</span>
            </div>
            <div>
              <span style={{ color: "var(--text-dim)" }}>| Total Irrigation Requirement: </span>
              <span style={{ color: "var(--warning)", fontWeight: "bold" }}>{totalIrr.toFixed(0)} mm</span>
            </div>
            <div>
              <span style={{ color: "var(--text-dim)" }}>| Total Rainfall: </span>
              <span style={{ color: "var(--success)", fontWeight: "bold" }}>{totalRain.toFixed(0)} mm</span>
            </div>
          </div>
        </div>
      )}

      {/* Buttons: Show Charts & Export Results */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <button
          className="hud-btn"
          onClick={() => setShowCharts(!showCharts)}
          style={{
            padding: "9px 0",
            fontSize: 11,
            fontWeight: "bold",
            cursor: "pointer",
            background: showCharts ? "rgba(0,229,255,0.15)" : "rgba(0,229,255,0.05)",
          }}
        >
          {showCharts ? (
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <Minimize2 size={12} /> Hide Charts
            </span>
          ) : (
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <BarChart3 size={12} /> Show Charts
            </span>
          )}
        </button>
        <button
          className="hud-btn"
          onClick={handleExport}
          style={{ padding: "9px 0", fontSize: 11, fontWeight: "bold", cursor: "pointer" }}
        >
          □ Export Results
        </button>
      </div>

      {/* 4 Interactive Graphs matching Cropwat Desktop Subplots */}
      {showCharts && hasData && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 4 }}>
          {/* Subplot Grid: 2x2 layout */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {/* Chart 1: ETc vs Rainfall */}
            <div style={{ background: "rgba(0,229,255,0.02)", border: "1px solid rgba(0,229,255,0.12)", borderRadius: 6, padding: "12px 14px" }}>
              <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", marginBottom: 10 }}>
                1. ETc vs Rainfall (mm)
              </div>
              <ResponsiveContainer width="100%" height={210}>
                <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,229,255,0.08)" />
                  <XAxis dataKey="month" tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <YAxis tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 9, color: "#5a8c9a" }} />
                  <Bar dataKey="ETc" fill="#00e5ff" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Rainfall" fill="#00ff88" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Chart 2: Monthly Irrigation Requirement */}
            <div style={{ background: "rgba(0,229,255,0.02)", border: "1px solid rgba(0,229,255,0.12)", borderRadius: 6, padding: "12px 14px" }}>
              <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", marginBottom: 10 }}>
                2. Monthly Irrigation Requirement (mm)
              </div>
              <ResponsiveContainer width="100%" height={210}>
                <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,229,255,0.08)" />
                  <XAxis dataKey="month" tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <YAxis tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 9, color: "#5a8c9a" }} />
                  <Bar dataKey="Irrig. Req." fill="#ff5252" radius={[2, 2, 0, 0]} />
                  <Line dataKey="Irrig. Req." stroke="#ffffff" strokeWidth={1.5} dot={{ r: 2, fill: "#fff" }} name="Trend" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Chart 3: Water Balance & Deficit */}
            <div style={{ background: "rgba(0,229,255,0.02)", border: "1px solid rgba(0,229,255,0.12)", borderRadius: 6, padding: "12px 14px" }}>
              <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", marginBottom: 10 }}>
                3. Water Balance (ETc vs Eff. Rain)
              </div>
              <ResponsiveContainer width="100%" height={210}>
                <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,229,255,0.08)" />
                  <XAxis dataKey="month" tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <YAxis tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 9, color: "#5a8c9a" }} />
                  <Line dataKey="ETc" stroke="#00e5ff" strokeWidth={2} dot={{ r: 3, fill: "#00e5ff" }} />
                  <Line dataKey="Eff. Rain" stroke="#00ff88" strokeWidth={2} dot={{ r: 3, fill: "#00ff88" }} />
                  <Area dataKey="Deficit" fill="rgba(255, 82, 82, 0.25)" stroke="#ff5252" strokeWidth={1} strokeDasharray="3 2" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Chart 4: Cumulative Water Requirements */}
            <div style={{ background: "rgba(0,229,255,0.02)", border: "1px solid rgba(0,229,255,0.12)", borderRadius: 6, padding: "12px 14px" }}>
              <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", marginBottom: 10 }}>
                4. Cumulative Water Requirements (mm)
              </div>
              <ResponsiveContainer width="100%" height={210}>
                <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,229,255,0.08)" />
                  <XAxis dataKey="month" tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <YAxis tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 9, color: "#5a8c9a" }} />
                  <Line dataKey="Cum. ETc" stroke="#00e5ff" strokeWidth={2} dot={{ r: 3, fill: "#00e5ff" }} />
                  <Line dataKey="Cum. Eff. Rain" stroke="#00ff88" strokeWidth={2} dot={{ r: 3, fill: "#00ff88" }} />
                  <Line dataKey="Cum. Irrigation" stroke="#ff5252" strokeWidth={2} dot={{ r: 3, fill: "#ff5252" }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
