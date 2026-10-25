"use client";
import React, { useState, useMemo } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Cell, Line, ComposedChart,
} from "recharts";
import { useIrriGridStore } from "@/lib/store";
import { BarChart3, CheckCircle, Minimize2, RefreshCw } from "lucide-react";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Rwanda season classification per month index
function getSeason(monthIdx: number): string {
  if ([5, 6, 7].includes(monthIdx)) return "Dry Season";
  if ([8, 9, 10, 11, 0].includes(monthIdx)) return "Season A (Short Rains)";
  return "Season B (Long Rains)";
}

const ROW_STYLE: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "30px 60px 80px 90px 150px 110px 110px",
  gap: 0,
  fontSize: 11,
  fontFamily: "var(--font-mono)",
  borderBottom: "1px solid rgba(0,229,255,0.06)",
  padding: "5px 8px",
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
    <div style={{ background: "#07111e", border: "1px solid rgba(0,229,255,0.3)", borderRadius: 4, padding: "8px 12px", fontSize: 11 }}>
      <div style={{ color: "var(--primary)", fontWeight: "bold", marginBottom: 4 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color, display: "flex", gap: 10, justifyContent: "space-between" }}>
          <span>{p.name}:</span>
          <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{Number(p.value).toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
};

export default function SchedulePanel() {
  const { scheduleSummary, waterBalance, monthlyRainfall } = useIrriGridStore();
  const [showCharts, setShowCharts] = useState(false);
  const [generated, setGenerated] = useState(true);
  const [applied, setApplied] = useState(false);

  // Build per-month schedule table following Rwanda agronomic logic
  const rows = useMemo(() => MONTHS.map((m, i) => {
    const wb = waterBalance[i];
    const etc = wb?.etc_mm ?? 0;
    const effRain = wb?.effective_rain_mm ?? (monthlyRainfall[i]?.effective_rain_mm ?? 0);
    const nir = wb?.net_irrigation_mm ?? Math.max(0, etc - effRain);
    const season = getSeason(i);
    const isDry = season === "Dry Season";

    let status = "Off-Season";
    let freq = "-";
    let duration = "-";

    if (etc > 0) {
      if (effRain >= 0.75 * etc && etc > 0) {
        status = "No Irrigation Needed";
      } else {
        status = "Irrigation Required";
        const interval = isDry ? 1 : 2;
        const durHours = ((nir / 30.0) / 2.0 * interval).toFixed(1);
        freq = `Every ${interval} days`;
        duration = `${durHours} hrs`;
      }
    } else {
      status = "Off-Season";
    }

    return {
      idx: i + 1,
      month: m,
      etc: etc.toFixed(1),
      effRain: effRain.toFixed(1),
      status,
      freq,
      duration,
      nir,
    };
  }), [waterBalance, monthlyRainfall]);

  const activeMonths = rows.filter(r => r.status === "Irrigation Required").length;
  const recommendedFreq = activeMonths > 0 ? "Every 3 days" : "Every 3 days";
  const sessionDuration = activeMonths > 0 ? "2.0 hours" : "2.0 hours";

  const chartData = rows.map(r => ({
    month: r.month,
    "ETc (mm)": +r.etc,
    "Eff. Rain (mm)": +r.effRain,
    "Irrig. Need (mm)": +r.nir.toFixed(1),
  }));

  function handleGenerate() {
    setGenerated(true);
  }

  function handleApply() {
    setApplied(true);
    setTimeout(() => setApplied(false), 2500);
  }

  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 14, maxWidth: 960 }}>
      {/* Header */}
      <div>
        <h2 style={{ color: "var(--primary)", fontSize: 18, fontWeight: "bold", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
          □ Irrigation Schedule (Rwanda Agronomy)
        </h2>
      </div>

      {/* Schedule Assessment */}
      <div style={{ background: "rgba(0,229,255,0.03)", border: "1px solid rgba(0,229,255,0.15)", borderRadius: 4, padding: "10px 14px" }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>
          Schedule Assessment
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 11 }}>
          <div>
            <span style={{ color: "var(--text-dim)" }}>Recommended Frequency: </span>
            <span style={{ color: "var(--text)", fontWeight: "bold" }}>{recommendedFreq}</span>
          </div>
          <div>
            <span style={{ color: "var(--text-dim)" }}>Session Duration: </span>
            <span style={{ color: "var(--text)", fontWeight: "bold" }}>{sessionDuration}</span>
          </div>
          <div>
            <span style={{ color: "var(--text-dim)" }}>Active Irrigation Months: </span>
            <span style={{ color: "var(--primary)", fontWeight: "bold" }}>{activeMonths} out of 12</span>
          </div>
        </div>
      </div>

      {/* Monthly Irrigation Schedule Table */}
      <div>
        <div style={{ color: "var(--text)", fontSize: 11, fontWeight: "bold", marginBottom: 6 }}>
          Monthly Irrigation Schedule:
        </div>
        <div style={{ border: "1px solid rgba(0,229,255,0.15)", borderRadius: 4, overflowX: "auto" }}>
          <div style={HEADER_STYLE}>
            <span>#</span>
            <span>Month</span>
            <span>ETc (mm)</span>
            <span>Eff. Rain (mm)</span>
            <span>Status</span>
            <span>Frequency</span>
            <span>Duration/Session</span>
          </div>
          {rows.map((r, i) => (
            <div
              key={r.month}
              style={{
                ...ROW_STYLE,
                background: i % 2 === 0 ? "transparent" : "rgba(0,229,255,0.02)",
              }}
            >
              <span style={{ color: "var(--text-dim)" }}>{r.idx}</span>
              <span style={{ color: "var(--text)", fontWeight: 500 }}>{r.month}</span>
              <span style={{ color: "var(--text)" }}>{r.etc}</span>
              <span style={{ color: "var(--text-dim)" }}>{r.effRain}</span>
              <span style={{
                color: r.status === "No Irrigation Needed" ? "#00ffc8"
                     : r.status === "Irrigation Required" ? "#ffb74d"
                     : "var(--text-dim)",
                fontWeight: r.status !== "Off-Season" ? 600 : 400,
              }}>
                {r.status}
              </span>
              <span style={{ color: r.freq !== "-" ? "var(--primary)" : "var(--text-dim)" }}>{r.freq}</span>
              <span style={{ color: r.duration !== "-" ? "var(--primary)" : "var(--text-dim)" }}>{r.duration}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons: Generate & Apply Strategy */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <button
          className="hud-btn"
          onClick={handleGenerate}
          style={{ padding: "10px 0", fontSize: 11, fontWeight: "bold", cursor: "pointer" }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <RefreshCw size={13} /> Generate Irrigation Schedule
          </span>
        </button>
        <button
          className="hud-btn"
          onClick={handleApply}
          style={{
            padding: "10px 0",
            fontSize: 11,
            fontWeight: "bold",
            cursor: "pointer",
            background: applied ? "rgba(0,255,200,0.25)" : "rgba(0,255,200,0.08)",
            borderColor: "var(--accent)",
            color: "var(--accent)",
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <CheckCircle size={12} color="var(--success)" />
            {applied ? " Applied to Strategy!" : " Apply Strategy"}
          </span>
        </button>
      </div>

      {/* Schedule Chart */}
      <div style={{ background: "rgba(0,229,255,0.02)", border: "1px solid rgba(0,229,255,0.12)", borderRadius: 6, padding: "12px 16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold" }}>
            Monthly Irrigation Demand Schedule (mm)
          </div>
          <button
            onClick={() => setShowCharts(!showCharts)}
            style={{
              background: "transparent",
              border: "1px solid rgba(0,229,255,0.3)",
              color: "var(--primary)",
              borderRadius: 3,
              padding: "2px 8px",
              fontSize: 10,
              cursor: "pointer",
            }}
          >
            {showCharts ? (
              <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <Minimize2 size={12} /> Compact View
              </span>
            ) : (
              <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <BarChart3 size={12} /> Expanded View
              </span>
            )}
          </button>
        </div>
        <ResponsiveContainer width="100%" height={showCharts ? 260 : 180}>
          <BarChart data={chartData} margin={{ top: 4, right: 10, bottom: 4, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,229,255,0.08)" />
            <XAxis dataKey="month" tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
            <YAxis tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 9, color: "#5a8c9a" }} />
            <Bar dataKey="ETc (mm)" fill="#00e5ff" radius={[2, 2, 0, 0]} />
            <Bar dataKey="Eff. Rain (mm)" fill="#00ff88" radius={[2, 2, 0, 0]} />
            <Bar dataKey="Irrig. Need (mm)" fill="#ffb74d" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
