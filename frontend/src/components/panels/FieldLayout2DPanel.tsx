"use client";

import React, { useEffect, useRef, useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { fetchFieldLayout, LayoutGeometryResponse } from "@/lib/api";

/* ============================================================================
   HOW TO REPLACE EMOJIS WITH REAL ICONS (do this in every other component too)
   ============================================================================

   STEP 1 — Find every emoji left in the app. Run this from `frontend/`:

       grep -rP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}\x{2190}-\x{21FF}]' src/ \
            --include="*.tsx" --include="*.ts"

       This catches real emojis (📍 ⚡ ✅) AND symbol characters that read the
       same way (⟳ ✓ ⚠ →). Every hit is a spot to fix.

   STEP 2 — Import the icon you need from lucide-react (already a dependency):

       import { MapPin, Zap, CheckCircle } from "lucide-react";

   STEP 3 — Swap the character for the component. Emoji lives in a string;
       an icon is a JSX element, so it needs braces/tags, not quotes:

       BEFORE:  <span>📍 Location</span>
       AFTER:   <span style={{ display:"flex", alignItems:"center", gap:6 }}>
                  <MapPin size={13} /> Location
                </span>

       Note the flex + gap — without it the icon and text won't align nicely,
       since an SVG sits on the baseline differently than a text glyph.

   STEP 4 — Sizing/color. Use `size` (px) and `color`. Prefer CSS vars so
       icons follow the theme instead of hardcoding hex:

       <Zap size={14} color="var(--primary)" />

   COMMON MAPPINGS for this codebase:
       📍 → MapPin        ⚡ → Zap            ✅ ✓ → CheckCircle
       ⚠️ → AlertTriangle  ❌ → XCircle        🔍 → Search
       📁 → Folder        💧 → Droplet        🌱 → Sprout
       📊 → BarChart3     🌧 → CloudRain      ☀️ → CloudSun
       ⟳ 🔄 → Loader2 (add className="spin", see STEP 5)
       📄 → FileText      ⬇️ → Download       ⚙️ → Settings

   STEP 5 — For spinners, lucide has no animation built in. Add this once to
       your global CSS (e.g. src/app/globals.css), then reuse `.spin` anywhere:

       @keyframes spin { to { transform: rotate(360deg); } }
       .spin { animation: spin 1s linear infinite; }

   STEP 6 — Keep imports clean. Only import icons you actually render;
       unused imports are dead weight and trip most lint configs.
       (This file previously imported Layers, CheckCircle, Activity and
       AlertCircle without using any of them — they've been removed below.)
   ========================================================================= */

import {
  Ruler,
  Gauge,
  Filter,
  Download,
  Loader2, // ← added: replaces the ⟳ character in the loading overlay
} from "lucide-react";

export default function FieldLayout2DPanel() {
  const containerRef = useRef<HTMLDivElement>(null);
  const plotlyInstanceRef = useRef<any>(null);
  const { location, design, crop, soil, layout2DOptions, setLayout2DOption, setLayoutPngBase64 } = useIrriGridStore();

  const [loadingPlot, setLoadingPlot] = useState(true);
  const [layoutGeom, setLayoutGeom] = useState<LayoutGeometryResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Resolved hydraulic and geometric parameters
  const rec = design?.recommended_design;
  const lateralSpacing = rec?.lateral_spacing_m || 1.0;
  const emitterSpacing = rec?.emitter_spacing_m || 0.3;
  const emitterFlowLph = rec?.emitter_flow_lph || 2.0;
  const totalFlowM3h = rec?.flow_rate_m3h || (layoutGeom ? (layoutGeom.total_emitters * emitterFlowLph) / 1000 : 12.4);
  const operatingPressureBar = 1.0;
  const filterMesh = 120;
  const emissionUniformity = rec?.emission_uniformity_percent || 91.5;
  const lateralDia = rec?.lateral_diameter_mm || 16;
  const mainDia = rec?.main_diameter_mm || 50;

  // 1. Backend engine geometry is the single source of truth
  useEffect(() => {
    let active = true;
    setLoadingPlot(true);
    setErrorMsg(null);

    // If design already returned layout geometry from /optimize, use it directly
    if (design?.layout_geometry) {
      setLayoutGeom(design.layout_geometry);
      setLoadingPlot(false);
      return;
    }

    const polygonCoords: [number, number][] | undefined = location.polygon && location.polygon.length >= 3
      ? location.polygon.map(([lat, lon]) => [lat, lon])
      : undefined;

    const waterSourceCoords: [number, number] | undefined = location.water_source
      ? [location.water_source[0], location.water_source[1]]
      : undefined;

    fetchFieldLayout({
      polygon_coords: polygonCoords,
      water_source_coords: waterSourceCoords,
      lateral_spacing: lateralSpacing,
      emitter_spacing: emitterSpacing,
      field_area_ha: location.area_ha || design?.field_area_ha || 0.5,
      lateral_diameter_mm: lateralDia,
      main_diameter_mm: mainDia,
      emitter_flow_lph: emitterFlowLph,
      emission_uniformity_pct: emissionUniformity,
    })
      .then((data) => {
        if (!active) return;
        setLayoutGeom(data);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Backend layout compute failed:", err);
        setErrorMsg("Failed to compute 2D layout on server.");
        setLayoutGeom(null);
      })
      .finally(() => {
        if (active) setLoadingPlot(false);
      });

    return () => {
      active = false;
    };
  }, [
    design?.layout_geometry,
    location.polygon,
    location.water_source,
    location.area_ha,
    design?.field_area_ha,
    lateralSpacing,
    emitterSpacing,
    lateralDia,
    mainDia,
    emitterFlowLph,
    emissionUniformity,
  ]);

  // 2. Render Plotly chart whenever layoutGeom or layer controls change
  useEffect(() => {
    if (typeof window === "undefined" || !containerRef.current || !layoutGeom) return;

    let isMounted = true;

    import("plotly.js-dist-min").then((PlotlyModule) => {
      if (!isMounted || !containerRef.current) return;
      const Plotly = PlotlyModule.default || PlotlyModule;

      const traces: any[] = [];

      // 1. Field Boundary Polygon
      traces.push({
        x: layoutGeom.boundary_x,
        y: layoutGeom.boundary_y,
        mode: "lines",
        line: { color: "#00ffc8", width: 2.8 },
        fill: "toself",
        fillcolor: "rgba(0, 255, 200, 0.07)",
        name: "Field Boundary",
        hoverinfo: "name",
      });

      // 2. Pressure Zone Shading (gradient background fill)
      if (layout2DOptions.showPressureShading) {
        traces.push({
          x: layoutGeom.boundary_x,
          y: layoutGeom.boundary_y,
          mode: "none",
          fill: "toself",
          fillcolor: "rgba(0, 160, 255, 0.05)",
          name: "Zone Nominal Pressure (1.0 bar)",
          hoverinfo: "skip",
          showlegend: true,
        });
      }

      // 3. Drip Laterals
      if (layout2DOptions.showLaterals && layoutGeom.lateral_segments.length > 0) {
        const latX: (number | null)[] = [];
        const latY: (number | null)[] = [];
        for (const seg of layoutGeom.lateral_segments) {
          latX.push(seg[0], seg[2], null);
          latY.push(seg[1], seg[3], null);
        }
        traces.push({
          x: latX,
          y: latY,
          mode: "lines",
          line: { color: "#00e5ff", width: 1.4 },
          name: `Laterals (${layoutGeom.num_laterals} lines @ ${layoutGeom.lateral_spacing_m}m)`,
          hoverinfo: "name",
        });
      }

      // 4. Sub-main Connectors
      if (layout2DOptions.showMainline && layoutGeom.sub_segments.length > 0) {
        const subX: (number | null)[] = [];
        const subY: (number | null)[] = [];
        for (const seg of layoutGeom.sub_segments) {
          subX.push(seg[0], seg[2], null);
          subY.push(seg[1], seg[3], null);
        }
        traces.push({
          x: subX,
          y: subY,
          mode: "lines",
          line: { color: "#ffb74d", width: 1.2, dash: "dot" },
          name: "Sub-Main Connectors",
          hoverinfo: "skip",
        });
      }

      // 5. Mainline Pipe (snapped to nearest edge)
      if (layout2DOptions.showMainline) {
        const ml = layoutGeom.mainline;
        traces.push({
          x: [ml[0], ml[2]],
          y: [ml[1], ml[3]],
          mode: "lines",
          line: { color: "#ffa726", width: 4.5 },
          name: `Mainline (${mainDia}mm PVC, ${layoutGeom.mainline_length_m}m Snapped)`,
          hoverinfo: "name",
        });
      }

      // 6. Emitter Dots
      if (layout2DOptions.showEmitters && layoutGeom.emitter_x.length > 0) {
        traces.push({
          x: layoutGeom.emitter_x,
          y: layoutGeom.emitter_y,
          mode: "markers",
          marker: {
            size: 3.5,
            color: "#00e5ff",
            opacity: 0.75,
            symbol: "circle",
          },
          name: `Emitters (${layoutGeom.total_emitters.toLocaleString()} @ ${layoutGeom.emitter_spacing_m}m)`,
          hovertemplate: "Emitter<br>X: %{x:.1f} m<br>Y: %{y:.1f} m<extra></extra>",
        });
      }

      // 7. Pump Station & Supply Line
      if (layout2DOptions.showPump) {
        // Supply line: pump -> mainline foot
        traces.push({
          x: [layoutGeom.pump_x, layoutGeom.supply_foot_x],
          y: [layoutGeom.pump_y, layoutGeom.supply_foot_y],
          mode: "lines",
          line: { color: "#29b6f6", width: 2.2, dash: "dash" },
          name: "Supply Line",
          hoverinfo: "skip",
          showlegend: false,
        });

        // Pump Marker
        traces.push({
          x: [layoutGeom.pump_x],
          y: [layoutGeom.pump_y],
          mode: "markers+text",
          marker: {
            size: 16,
            color: "#29b6f6",
            symbol: "diamond",
            line: { color: "#ffffff", width: 1.5 },
          },
          text: ["Pump Station"],
          textposition: "top center",
          textfont: { color: "#29b6f6", size: 11, family: "monospace" },
          name: "Pump & Filtration Head",
          hovertemplate: "Water Source / Pump<br>X: %{x:.1f} m<br>Y: %{y:.1f} m<extra></extra>",
        });
      }

      const layout: any = {
        title: {
          text: `<b>2D DRIP IRRIGATION ENGINEERING LAYOUT</b> — ${crop?.name?.toUpperCase() || "CROP"} (${layoutGeom.area_ha.toFixed(3)} ha)`,
          font: { color: "#00e5ff", size: 13, family: "var(--font)" },
          x: 0.02,
          y: 0.98,
        },
        paper_bgcolor: "#030712",
        plot_bgcolor: "#070e1c",
        autosize: true,
        margin: { l: 60, r: 20, t: 40, b: 60 },
        hovermode: "closest",
        showlegend: true,
        legend: {
          orientation: "h",
          x: 0.02,
          y: -0.15,
          font: { color: "#9ca3af", size: 10 },
          bgcolor: "rgba(10, 17, 30, 0.7)",
          bordercolor: "rgba(0, 229, 255, 0.2)",
          borderwidth: 1,
        },
        xaxis: {
          title: "<b>East–West (Meters)</b>",
          color: "#9ca3af",
          gridcolor: "rgba(255, 255, 255, 0.05)",
          zeroline: false,
          scaleanchor: "y",
          scaleratio: 1,
        },
        yaxis: {
          title: "<b>North–South (Meters)</b>",
          color: "#9ca3af",
          gridcolor: "rgba(255, 255, 255, 0.05)",
          zeroline: false,
        },
      };

      const config: any = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ["lasso2d", "select2d"],
        displaylogo: false,
      };

      Plotly.newPlot(containerRef.current, traces, layout, config).then(async (fig: any) => {
        plotlyInstanceRef.current = fig;

        // Auto-capture the rendered chart as a base64 PNG for PDF export
        try {
          const pngBase64 = await Plotly.toImage(fig, {
            format: "png",
            width: 900,
            height: 580,
            scale: 1.5,
          });
          setLayoutPngBase64(pngBase64);
        } catch (e) {
          console.warn("Failed to capture layout PNG for PDF:", e);
          setLayoutPngBase64(null);
        }
      });
    });

    return () => {
      isMounted = false;
      const el = containerRef.current;
      if (el) {
        // Synchronous purge to avoid race conditions
        import("plotly.js-dist-min").then((PlotlyModule) => {
          const Plotly = PlotlyModule.default || PlotlyModule;
          try {
            Plotly.purge(el);
          } catch {
            // ignore purge errors
          }
        });
        plotlyInstanceRef.current = null;
      }
    };
  }, [layoutGeom, layout2DOptions, lateralDia, mainDia, lateralSpacing, emitterSpacing, crop?.name]);

  function handleExportPng() {
    const el = containerRef.current;
    if (typeof window === "undefined" || !el) return;
    import("plotly.js-dist-min").then((PlotlyModule) => {
      const Plotly = PlotlyModule.default || PlotlyModule;
      Plotly.toImage(el, {
        format: "png",
        width: 1200,
        height: 800,
        scale: 1.5,
      }).then((dataUrl) => {
        const a = document.createElement("a");
        a.href = dataUrl;
        a.download = `irrigrid_layout_2d_${crop?.name || "field"}.png`;
        a.click();
      }).catch((err) => {
        console.error("PNG export failed:", err);
      });
    });
  }

  return (
    <div style={{ flex: 1, display: "flex", height: "100%", overflow: "hidden", background: "var(--bg-main)" }}>
      {/* ── Left Engineering Drawing Canvas ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100%", position: "relative", minWidth: 0 }}>
        {/* Top bar with quick scale & mainline status */}
        <div style={{
          height: 38,
          background: "var(--bg-widget)",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 16px",
          fontSize: 11,
          color: "var(--text-dim)",
          flexShrink: 0
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Ruler size={13} color="var(--primary)" />
            <span style={{ color: "var(--text)", fontWeight: "bold" }}>
              Orthogonal 1:1 Metric Coordinate System
            </span>
            <span style={{ color: layoutGeom?.is_real_polygon ? "var(--primary)" : "var(--accent)", marginLeft: 6 }}>
              {layoutGeom?.is_real_polygon ? "(Real Traced Field Polygon)" : "(Synthesized Rectangular Baseline)"}
            </span>
            {layoutGeom && (
              <span style={{
                background: "rgba(0, 255, 200, 0.12)",
                color: "var(--primary)",
                padding: "2px 8px",
                borderRadius: 4,
                fontSize: 10,
                fontWeight: 600,
                marginLeft: 8,
              }}>
                Mainline Snapped: {layoutGeom.mainline_edge_angle_deg}°
              </span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span>Dimensions: <strong style={{ color: "#fff" }}>{layoutGeom?.field_width_m}m × {layoutGeom?.field_height_m}m</strong></span>
            <span>Total Lateral Pipe: <strong style={{ color: "var(--primary)" }}>{layoutGeom?.total_lateral_m.toLocaleString()} m</strong></span>
            <button
              onClick={handleExportPng}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                padding: "3px 8px",
                fontSize: 11,
                borderRadius: 4,
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                cursor: "pointer"
              }}
              title="Download 2D Layout PNG"
            >
              <Download size={12} /> PNG Export
            </button>
          </div>
        </div>

        {/* Plotly Canvas */}
        <div style={{ flex: 1, position: "relative", minHeight: 0 }}>
          <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
          {loadingPlot && (
            <div style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              // gap added so the spinner icon and the text don't collide —
              // an SVG needs explicit spacing where an emoji had a built-in space
              gap: 8,
              background: "#030712",
              color: "var(--primary)",
              fontSize: 12,
              fontFamily: "var(--font-mono)",
            }}>
              {/* WAS: ⟳ Computing... — replaced with a real spinning icon.
                  `.spin` comes from the @keyframes rule described in STEP 5 above;
                  add it to globals.css once and it works for every spinner. */}
              <Loader2 size={14} className="spin" />
              Computing Precision Edge-Snapped Field Layout...
            </div>
          )}
        </div>
      </div>

      {/* ── Right Engineering Specification Sidebar ── */}
      <div style={{
        width: 320,
        minWidth: 300,
        background: "var(--bg-widget)",
        borderLeft: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflowY: "auto",
        padding: 14,
        gap: 14,
      }}>
        {/* Field Summary Card */}
        <div className="hud-box">
          <div className="hud-box-title" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
            <Ruler size={13} /> Field Layout Summary
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 11, marginTop: 4 }}>
            <div className="hud-row">
              <span>Field Area</span>
              <span style={{ color: "var(--accent)", fontWeight: "bold" }}>
                {layoutGeom ? `${layoutGeom.area_ha.toFixed(3)} ha (${layoutGeom.area_m2.toLocaleString()} m²)` : "—"}
              </span>
            </div>
            <div className="hud-row">
              <span>Traced Vertices</span>
              <span>{location.polygon?.length || (layoutGeom?.is_real_polygon ? 4 : "Default")} points</span>
            </div>
            <div className="hud-row">
              <span>Mainline Snapping</span>
              <span style={{ color: "var(--success)", fontWeight: "bold" }}>
                Active (Edge @ {layoutGeom?.mainline_edge_angle_deg}°)
              </span>
            </div>
            <div className="hud-row">
              <span>Mainline Length</span>
              <span style={{ color: "#ffa726", fontWeight: "bold" }}>{layoutGeom?.mainline_length_m} m</span>
            </div>
            <div className="hud-row">
              <span>Drip Lateral Count</span>
              <span style={{ color: "var(--primary)", fontWeight: "bold" }}>{layoutGeom?.num_laterals} lines</span>
            </div>
            <div className="hud-row">
              <span>Total Emitters</span>
              <span style={{ color: "var(--success)", fontWeight: "bold" }}>{layoutGeom?.total_emitters.toLocaleString()}</span>
            </div>
            <div className="hud-row">
              <span>Lateral Spacing</span>
              <span>{lateralSpacing} m</span>
            </div>
            <div className="hud-row">
              <span>Emitter Spacing</span>
              <span>{emitterSpacing} m</span>
            </div>
            <div className="hud-row">
              <span>Sub-Main Stubs</span>
              <span>{layoutGeom?.sub_segments.length || 0} connections</span>
            </div>
          </div>
        </div>

        {/* Hydraulic Design Parameters Card */}
        <div className="hud-box">
          <div className="hud-box-title" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
            <Gauge size={13} /> Hydraulic Hardware Parameters
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 11, marginTop: 4 }}>
            <div className="hud-row">
              <span>Total System Flow</span>
              <span style={{ color: "var(--primary)", fontWeight: "bold" }}>{totalFlowM3h.toFixed(2)} m³/h</span>
            </div>
            <div className="hud-row">
              <span>Emitter Nominal Flow</span>
              <span>{emitterFlowLph.toFixed(1)} L/hr</span>
            </div>
            <div className="hud-row">
              <span>Operating Pressure</span>
              <span>{operatingPressureBar.toFixed(1)} bar</span>
            </div>
            <div className="hud-row">
              <span>Recommended Filter</span>
              <span style={{ color: "var(--accent)", fontWeight: "bold" }}>{filterMesh} mesh screen/disc</span>
            </div>
            <div className="hud-row">
              <span>Emission Uniformity</span>
              <span style={{ color: "var(--success)", fontWeight: "bold" }}>{emissionUniformity.toFixed(1)}%</span>
            </div>
            <div className="hud-row">
              <span>Lateral Pipe Size</span>
              <span>{lateralDia} mm LDPE</span>
            </div>
            <div className="hud-row">
              <span>Mainline Pipe Size</span>
              <span>{mainDia} mm PVC</span>
            </div>
          </div>
        </div>

        {/* Layer Controls Card */}
        <div className="hud-box">
          <div className="hud-box-title" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
            <Filter size={13} /> Layer Controls
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 11, marginTop: 6 }}>
            {([
              { key: "showLaterals", label: "Drip Laterals" },
              { key: "showEmitters", label: "Emitter Dots" },
              { key: "showMainline", label: "Mainline & Sub-mains" },
              { key: "showPump", label: "Pump Station" },
              { key: "showPressureShading", label: "Pressure Zone Shading" },
            ] as { key: keyof typeof layout2DOptions; label: string }[]).map(({ key, label }) => (
              <label key={key} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", color: layout2DOptions[key] ? "var(--text)" : "var(--text-dim)" }}>
                <input
                  type="checkbox"
                  checked={layout2DOptions[key]}
                  onChange={(e) => setLayout2DOption(key, e.target.checked)}
                  style={{ accentColor: "var(--primary)", width: 13, height: 13 }}
                />
                {label}
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}