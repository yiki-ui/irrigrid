"use client";
import React, { useState, useMemo } from "react";
import {
  ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Area,
} from "recharts";
import { useIrriGridStore } from "@/lib/store";
import { AlertTriangle, Calendar, CheckCircle, RefreshCw } from "lucide-react";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function getSeason(i: number): string {
  if ([8, 9, 10, 11, 0].includes(i)) return "Season A (Short Rains)";
  if ([1, 2, 3, 4].includes(i)) return "Season B (Long Rains)";
  return "Dry Season";
}

const ROW_STYLE: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "30px 60px 200px 110px 110px 110px",
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
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "8px 12px", fontSize: 11, boxShadow: "0 6px 20px rgba(0,0,0,0.15)" }}>
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

export default function CropPatternPanel() {
  const { crop, monthlyClimate, monthlyRainfall, setSidebarStep } = useIrriGridStore();
  const [applied, setApplied] = useState(false);
  const [showChart, setShowChart] = useState(true);

  // Growth stages calculation matching cropwat_02_crop_soil_input.py
  const stages = crop.stages || { initial: 25, development: 40, mid: 45, late: 25 };
  const totalDays = (stages.initial || 25) + (stages.development || 40) + (stages.mid || 45) + (stages.late || 25);
  const totalMonths = Math.max(1, Math.round(totalDays / 30.0)); // e.g. 4 months

  // Rwanda Season B starts in Feb (month index 1)
  const plantingMonthIdx = 1;
  const harvestMonthIdx = (plantingMonthIdx + totalMonths - 1) % 12;

  // Monthly Kc and ETc distribution
  const rows = useMemo(() => {
    const kcInit = crop.kc_init || 0.6;
    const kcMid = crop.kc_mid || 1.15;
    const kcEnd = crop.kc_end || 0.8;

    let maxEtc = 0;
    let peakIdx = plantingMonthIdx;

    const data = MONTHS.map((month, i) => {
      const season = getSeason(i);
      const isGrowing = i >= plantingMonthIdx && i < plantingMonthIdx + totalMonths;

      let kc: number | null = null;
      if (isGrowing) {
        const offset = i - plantingMonthIdx;
        const progress = offset / Math.max(1, totalMonths - 1);
        if (progress < 0.25) kc = kcInit;
        else if (progress < 0.75) kc = kcMid;
        else kc = kcEnd;
      }

      const eto = monthlyClimate[i]?.eto ?? 4.0;
      const etc = kc !== null ? eto * kc * 30.0 : 0;
      const effRain = monthlyRainfall[i]?.effective_rain_mm ?? 0;

      if (etc > maxEtc) {
        maxEtc = etc;
        peakIdx = i;
      }

      return {
        idx: i + 1,
        month,
        season,
        kc: kc !== null ? kc.toFixed(2) : "-",
        kcNum: kc !== null ? kc : 0,
        etc: etc > 0 ? etc.toFixed(1) : "-",
        etcNum: etc,
        effRain: effRain.toFixed(1),
        effRainNum: effRain,
      };
    });

    return { data, maxEtc, peakIdx };
  }, [crop, monthlyClimate, monthlyRainfall, totalMonths]);

  const peakMonth = MONTHS[rows.peakIdx];
  const peakEtcVal = rows.maxEtc.toFixed(1);
  const isPeakInDrySeason = [5, 6, 7, 8].includes(rows.peakIdx);

  function handleApply() {
    setApplied(true);
    setTimeout(() => {
      setApplied(false);
      setSidebarStep(8); // Switch to step 8 (Irrig. Sched.)
    }, 1500);
  }

  const chartData = rows.data.map(r => ({
    month: r.month,
    "ETc (mm)": r.etcNum,
    "Eff. Rain (mm)": r.effRainNum,
    "Kc (x100)": +(r.kcNum * 100).toFixed(0),
  }));

  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 14, maxWidth: 960 }}>
      {/* Header */}
      <div>
        <h2 style={{ color: "var(--primary)", fontSize: 18, fontWeight: "bold", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
          <Calendar size={18} color="var(--primary)" /> Crop Pattern &amp; Planting Calendar (Rwanda)
        </h2>
      </div>

      {/* Agronomic Assessment Box */}
      <div style={{ background: "rgba(0,229,255,0.03)", border: "1px solid rgba(0,229,255,0.15)", borderRadius: 4, padding: "10px 14px" }}>
        <div style={{ color: "var(--text-dim)", fontSize: 10, fontWeight: "bold", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" }}>
          Agronomic Assessment
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 11 }}>
          <div>
            <span style={{ color: "var(--text-dim)" }}>Recommended Crop: </span>
            <span style={{ color: "var(--text)", fontWeight: "bold" }}>{crop.name || "Tomato"}</span>
          </div>
          <div>
            <span style={{ color: "var(--text-dim)" }}>Planting Window: </span>
            <span style={{ color: "var(--text)", fontWeight: "bold" }}>
              {MONTHS[plantingMonthIdx]} (Start of Season B / Long Rains)
            </span>
          </div>
          <div>
            <span style={{ color: "var(--text-dim)" }}>Harvest Window: </span>
            <span style={{ color: "var(--text)", fontWeight: "bold" }}>{MONTHS[harvestMonthIdx]}</span>
          </div>
          <div>
            <span style={{ color: "var(--text-dim)" }}>Peak Water Demand Month: </span>
            <span style={{ color: "var(--primary)", fontWeight: "bold" }}>
              {peakMonth} ({peakEtcVal} mm)
            </span>
          </div>
        </div>

        {/* Dry Season Warning */}
        {isPeakInDrySeason && (
          <div style={{
            marginTop: 10,
            padding: "8px 12px",
            background: "rgba(255,183,77,0.1)",
            border: "1px solid rgba(255,183,77,0.3)",
            borderRadius: 4,
            color: "#ffb74d",
            fontSize: 11,
            lineHeight: 1.4,
          }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <AlertTriangle size={14} /> <strong>WARNING:</strong> Peak demand for {crop.name || "Tomato"} falls in the Dry Season ({peakMonth}).
            </span>
            This will require a full irrigation load. Consider staggering with a drought-tolerant crop (e.g., Beans)
            or shifting planting date to leverage historical rainfall.
          </div>
        )}
      </div>

      {/* Monthly Table */}
      <div>
        <div style={{ color: "var(--text)", fontSize: 11, fontWeight: "bold", marginBottom: 6 }}>
          Monthly Water Demand Curve:
        </div>
        <div style={{ border: "1px solid rgba(0,229,255,0.15)", borderRadius: 4, overflowX: "auto" }}>
          <div style={HEADER_STYLE}>
            <span>#</span>
            <span>Month</span>
            <span>Season</span>
            <span>Kc Value</span>
            <span>ETc (mm)</span>
            <span>Eff. Rain (mm)</span>
          </div>
          {rows.data.map((r, i) => (
            <div
              key={r.month}
              style={{
                ...ROW_STYLE,
                background: i % 2 === 0 ? "transparent" : "rgba(0,229,255,0.02)",
              }}
            >
              <span style={{ color: "var(--text-dim)" }}>{r.idx}</span>
              <span style={{ color: "var(--text)", fontWeight: 500 }}>{r.month}</span>
              <span style={{
                color: r.season.includes("Season B") ? "var(--primary)"
                     : r.season.includes("Season A") ? "var(--accent)"
                     : "var(--text-dim)",
              }}>
                {r.season}
              </span>
              <span style={{ color: r.kc !== "-" ? "var(--accent)" : "var(--text-dim)" }}>{r.kc}</span>
              <span style={{ color: r.etc !== "-" ? "var(--primary)" : "var(--text-dim)", fontWeight: r.etc !== "-" ? 600 : 400 }}>
                {r.etc}
              </span>
              <span style={{ color: "var(--text-dim)" }}>{r.effRain}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <button
          className="hud-btn"
          onClick={() => {}}
          style={{ padding: "10px 0", fontSize: 11, fontWeight: "bold", cursor: "pointer" }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <RefreshCw size={13} /> Generate Pattern
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
            {applied ? " Applied to Schedule!" : " Apply to Schedule"}
          </span>
        </button>
      </div>

      {/* Demand Curve Chart */}
      <div style={{ background: "rgba(0,229,255,0.02)", border: "1px solid rgba(0,229,255,0.12)", borderRadius: 6, padding: "12px 16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <div style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold" }}>
            Monthly Water Demand Curve vs Effective Rain (mm)
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={chartData} margin={{ top: 4, right: 10, bottom: 4, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,229,255,0.08)" />
            <XAxis dataKey="month" tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
            <YAxis tick={{ fill: "#5a8c9a", fontSize: 9 }} axisLine={{ stroke: "rgba(0,229,255,0.15)" }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 9, color: "#5a8c9a" }} />
            <Area dataKey="ETc (mm)" fill="rgba(0,229,255,0.2)" stroke="#00e5ff" strokeWidth={2} dot={{ r: 3, fill: "#00e5ff" }} />
            <Bar dataKey="Eff. Rain (mm)" fill="#00ff88" radius={[2, 2, 0, 0]} opacity={0.6} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
