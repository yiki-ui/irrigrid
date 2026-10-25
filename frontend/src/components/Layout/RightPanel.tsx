"use client";

import React, { useState, useEffect } from "react";
import { AlertTriangle, Bot, Settings, Cpu, Send, Zap, RefreshCw, CheckCircle, Eye, SlidersHorizontal, User } from "lucide-react";
import { useIrriGridStore } from "@/lib/store";
import { optimizeIrrigation, askAgronomist, fetchAiStatus } from "@/lib/api";

/** Renders markdown: **bold**, [links](url), newlines, and bullet lines — no extra packages. */
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, li) => {
        const trimmed = line.trimStart();
        const isBullet = trimmed.startsWith("•") || trimmed.startsWith("- ") || trimmed.startsWith("* ");
        
        let content = line;
        if (trimmed.startsWith("•")) {
          content = trimmed.slice(1).trim();
        } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          content = trimmed.slice(2).trim();
        }

        // Parse inline spans: [link](url) and **bold**
        const parseSpans = (src: string): React.ReactNode[] => {
          // If wrapped in **[link](url)**, clean outer asterisks so link parses cleanly
          const clean = src.replace(/\*\*(\[[^\]]+\]\(https?:\/\/[^\s)]+\))\*\*/g, "$1");
          const out: React.ReactNode[] = [];
          const re = /(\*\*([^*]+)\*\*|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\))/g;
          let last = 0;
          let m: RegExpExecArray | null;
          let keyIdx = 0;
          while ((m = re.exec(clean)) !== null) {
            if (m.index > last) out.push(clean.slice(last, m.index));
            if (m[2]) {
              out.push(<strong key={keyIdx++}>{m[2]}</strong>);
            } else if (m[3] && m[4]) {
              out.push(
                <a
                  key={keyIdx++}
                  href={m[4]}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "var(--primary)", textDecoration: "underline", fontWeight: 600 }}
                >
                  {m[3]}
                </a>
              );
            }
            last = m.index + m[0].length;
          }
          if (last < clean.length) out.push(clean.slice(last));
          return out;
        };

        // Empty lines → small vertical gap
        if (!content.trim()) {
          return <div key={li} style={{ height: 6 }} />;
        }

        return (
          <div key={li} style={{ marginTop: isBullet ? 4 : 0 }}>
            {isBullet ? (
              <div style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
                <span style={{ color: "var(--primary)", flexShrink: 0, lineHeight: 1.55 }}>•</span>
                <span style={{ flex: 1 }}>{parseSpans(content)}</span>
              </div>
            ) : (
              <span>{parseSpans(content)}</span>
            )}
          </div>
        );
      })}
    </>
  );
}

export default function RightPanel() {
  const [activeTab, setActiveTab] = useState<"controls" | "ai">("controls");
  const {
    location,
    setLocation,
    crop,
    soil,
    design,
    setDesign,
    layout2DOptions,
    setLayout2DOption,
  } = useIrriGridStore();

  const [emitterSpacing, setEmitterSpacing] = useState(0.3);
  const [lateralSpacing, setLateralSpacing] = useState(1.0);
  const [emitterFlow, setEmitterFlow] = useState(2.0);
  const [isRunningHydraulics, setIsRunningHydraulics] = useState(false);
  const [hydraulicStatus, setHydraulicStatus] = useState<string | null>(null);

  // AI chat state
  const [aiStatus, setAiStatus] = useState<{ is_live_llm: boolean; provider: string; model: string } | null>(null);

  useEffect(() => {
    fetchAiStatus().then(setAiStatus).catch(() => {});
  }, []);

  const [messages, setMessages] = useState<Array<{ role: "user" | "ai"; text: string; source?: string }>>([
    {
      role: "ai",
      text: `Hello! I am your AI Agronomist for Rwanda. I see your field is in ${location.district || "Musanze"} (${location.elevation_m || 1850}m a.s.l.) with ${crop?.name || "Tomato"} in ${soil?.name || "Volcanic Loam"}. How can I assist your irrigation design today?`,
      source: "offline_agronomist_engine",
    },
  ]);

  // Synchronize greeting when location, crop, soil, or area change
  useEffect(() => {
    setMessages((prev) => {
      if (prev.length <= 1) {
        const dist = location.district || "Musanze";
        const elev = location.elevation_m || 1850;
        const cName = crop?.name || "Tomato";
        const sName = soil?.name || "Volcanic Loam";
        const areaStr = location.area_ha ? ` (${location.area_ha.toFixed(2)} ha)` : "";
        return [
          {
            role: "ai",
            text: `Hello! I am your AI Agronomist for Rwanda. I see your field is in **${dist}** (${elev}m a.s.l.)${areaStr} with **${cName}** on **${sName}**. How can I assist your irrigation design today?`,
            source: "offline_agronomist_engine",
          },
        ];
      }
      return prev;
    });
  }, [location.district, location.elevation_m, location.area_ha, crop?.name, soil?.name]);

  // Automatically sync hydraulicStatus from design state whenever available
  useEffect(() => {
    const rec = (design?.recommended_design || design) as any;
    if (rec && typeof rec === "object") {
      const eu = rec.emission_uniformity_percent != null && !isNaN(rec.emission_uniformity_percent)
        ? `${Number(rec.emission_uniformity_percent).toFixed(1)}%`
        : "—";
      const cost = rec.total_cost_rwf != null && !isNaN(rec.total_cost_rwf)
        ? `${(Number(rec.total_cost_rwf) / 1e6).toFixed(2)}M RWF`
        : "—";
      if (eu !== "—" || cost !== "—") {
        setHydraulicStatus(`✓ EU ${eu} | ${cost}`);
      }
    }
  }, [design]);

  const [inputMessage, setInputMessage] = useState("");
  const [isAiThinking, setIsAiThinking] = useState(false);

  const handleRunHydraulics = async () => {
    setIsRunningHydraulics(true);
    setHydraulicStatus("Optimizing NSGA-II hydraulics...");
    try {
      const area = location.area_ha || 0.25;
      const waterSource = location.water_source
        ? [location.water_source[0], location.water_source[1]] as [number, number]
        : undefined;

      const res = await optimizeIrrigation({
        crop_name: crop?.name || "Tomato",
        soil_type: soil?.name || "Volcanic Loam",
        location_name: location.district ? `${location.district}, Rwanda` : "Rwanda",
        field_area_ha: area,
        polygon_coordinates: location.polygon,
        water_source_coords: waterSource,
        slope_percent: location.slope_pct || 2.0,
        min_eu_threshold: 90.0,
        climate_data: useIrriGridStore.getState().monthlyClimate,
        soil_detail: soil,
        water_balance: useIrriGridStore.getState().waterBalance,
        schedule_summary: useIrriGridStore.getState().scheduleSummary,
      });

      setDesign(res);
      const rec = (res?.recommended_design || res) as any;
      const eu = rec?.emission_uniformity_percent != null && !isNaN(rec.emission_uniformity_percent)
        ? `${Number(rec.emission_uniformity_percent).toFixed(1)}%`
        : "—";
      const cost = rec?.total_cost_rwf != null && !isNaN(rec.total_cost_rwf)
        ? `${(Number(rec.total_cost_rwf) / 1e6).toFixed(2)}M RWF`
        : "—";
      setHydraulicStatus(`✓ EU ${eu} | ${cost}`);
    } catch (err: any) {
      console.warn("Hydraulic run error:", err);
      setHydraulicStatus("⚠ Optimization failed — check connection");
    } finally {
      setIsRunningHydraulics(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isAiThinking) return;
    const userText = inputMessage.trim();
    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setInputMessage("");
    setIsAiThinking(true);

    try {
      const resp = await askAgronomist({
        prompt: userText,
        crop_name: crop?.name || "Tomato",
        location_name: location.district ? `${location.district}, Rwanda` : "Rwanda",
        field_area_ha: location.area_ha || 0.25,
        soil_type: soil?.name || "Volcanic Loam",
      });

      if (resp && resp.advice) {
        setMessages((prev) => [...prev, { role: "ai", text: resp.advice, source: resp.source }]);
      } else {
        throw new Error("Empty response from AI advice");
      }
    } catch (err) {
      console.warn("Backend AI request failed, utilizing local agronomist:", err);
      const district = location.district || "Rwanda";
      const cropName = crop?.name || "your crop";
      const soilName = soil?.name || "Loam";
      const area = location.area_ha || 0.25;
      const areaStr = area < 0.1 ? `${area.toFixed(3)} ha (${Math.round(area * 10000)} m²)` : `${area.toFixed(2)} ha`;
      let reply = `Based on your field in ${district} (${areaStr}) and ${soilName} soil: `;
      const lower = userText.toLowerCase();
      if (lower.includes("drip") || lower.includes("irrigation") || lower.includes("emitter") || lower.includes("pipe")) {
        reply += `We recommend 16mm drip laterals with ${emitterSpacing}m inline emitter spacing operating at 1.0 bar pressure. For ${cropName}, this gives ~91.5% emission uniformity with 35% water savings compared to sprinklers.`;
      } else if (lower.includes("soil") || lower.includes("water") || lower.includes("moisture")) {
        const tam = soil?.available_water_mm_m || 180;
        reply += `${soilName} has a Total Available Moisture (TAM) of ${tam} mm/m. We suggest keeping depletion below 40% (RAW = ${(tam * 0.4).toFixed(1)} mm/m) to prevent crop stress.`;
      } else if (lower.includes("crop") || lower.includes("fertilizer") || lower.includes("season")) {
        reply += `For ${cropName} in Rwanda's high altitude zone, peak water demand occurs between Day 45 and 90 (flowering and fruit development). Fertigation via venturi injector can be combined with irrigation.`;
      } else {
        const lat = location.lat != null ? location.lat.toFixed(3) : "-1.500";
        const lon = location.lon != null ? location.lon.toFixed(3) : "29.630";
        reply += `I have analyzed your spatial parameters. Your location at ${lat}°, ${lon}° receives ~1100 mm annual precipitation. Supplemental irrigation during dry spells will maximize yield.`;
      }
      setMessages((prev) => [...prev, { role: "ai", text: reply, source: "offline_agronomist_engine" }]);
    } finally {
      setIsAiThinking(false);
    }
  };

  return (
    <div
      className="right-sidebar"
      style={{
        width: 330,
        minWidth: 320,
        maxWidth: 350,
        background: "var(--bg-widget)",
        borderLeft: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
      }}
    >
      {/* ── Tabs ── */}
      <div className="right-tabs" style={{ display: "flex", borderBottom: "1px solid var(--border-subtle)", flexShrink: 0 }}>
        <div
          className={`right-tab ${activeTab === "controls" ? "active" : ""}`}
          onClick={() => setActiveTab("controls")}
          style={{
            flex: 1,
            padding: "10px 14px",
            textAlign: "center",
            cursor: "pointer",
            color: activeTab === "controls" ? "#ffffff" : "var(--text-dim)",
            borderBottom: activeTab === "controls" ? "2px solid var(--primary)" : "1px solid var(--border-subtle)",
            fontSize: 11,
            fontWeight: "bold",
            letterSpacing: 0.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
            background: activeTab === "controls" ? "var(--primary)" : "var(--bg-widget)",
          }}
        >
          <Settings size={13} color={activeTab === "controls" ? "#ffffff" : "var(--text-dim)"} /> Controls
        </div>
        <div
          className={`right-tab ${activeTab === "ai" ? "active" : ""}`}
          onClick={() => setActiveTab("ai")}
          style={{
            flex: 1,
            padding: "10px 14px",
            textAlign: "center",
            cursor: "pointer",
            color: activeTab === "ai" ? "#ffffff" : "var(--text-dim)",
            borderBottom: activeTab === "ai" ? "2px solid var(--primary)" : "1px solid var(--border-subtle)",
            fontSize: 11,
            fontWeight: "bold",
            letterSpacing: 0.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
            background: activeTab === "ai" ? "var(--primary)" : "var(--bg-widget)",
          }}
        >
          <Cpu size={13} color={activeTab === "ai" ? "#ffffff" : "var(--text-dim)"} /> AI Expert
        </div>
      </div>

      {/* ── Content ── */}
      <div className="right-content" style={{ padding: "14px", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: 14 }}>
        {activeTab === "controls" && (
          <>
            {/* Irrigation System Design */}
            <div className="hud-box">
              <div className="hud-box-title" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
                <SlidersHorizontal size={13} /> Irrigation System Design
              </div>
              <div style={{ color: "var(--text-dim)", fontSize: 10, fontStyle: "italic", marginBottom: 10 }}>
                Configure your emitter and lateral pipe parameters
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div className="hud-row">
                  <span style={{ fontSize: 11 }}>System Type</span>
                  <select className="hud-select" defaultValue="drip" style={{ width: 110, fontSize: 11 }}>
                    <option value="drip">Drip</option>
                    <option value="sprinkler">Sprinkler</option>
                    <option value="surface">Surface</option>
                  </select>
                </div>

                <div className="hud-row">
                  <span style={{ fontSize: 11 }}>
                    Area (ha)
                    {location.polygon && (
                      <span title="Auto-filled from traced field boundary" style={{ marginLeft: 4, fontSize: 9, color: "var(--primary)", fontWeight: "bold" }}>traced</span>
                    )}
                  </span>
                  <input
                    type="number"
                    className="hud-input"
                    value={location.area_ha ?? 2.5}
                    step={0.01}
                    readOnly={!!location.polygon}
                    onChange={(e) => {
                      if (!location.polygon) setLocation({ area_ha: parseFloat(e.target.value) || 0 });
                    }}
                    title={location.polygon ? "Area locked — computed from traced boundary. Clear polygon to edit manually." : "Enter field area"}
                    style={{ width: 110, fontSize: 11, opacity: location.polygon ? 0.7 : 1, cursor: location.polygon ? "not-allowed" : "text" }}
                  />
                </div>

                <div className="hud-row">
                  <span style={{ fontSize: 11 }}>Emitter Type</span>
                  <select className="hud-select" defaultValue="inline" style={{ width: 110, fontSize: 11 }}>
                    <option value="inline">Inline</option>
                    <option value="button">Button</option>
                    <option value="pc">Pressure Compensating</option>
                  </select>
                </div>

                <div className="hud-row">
                  <span style={{ fontSize: 11 }}>Emitter Flow (L/hr)</span>
                  <input
                    type="number"
                    className="hud-input"
                    value={emitterFlow}
                    step={0.1}
                    onChange={(e) => setEmitterFlow(parseFloat(e.target.value) || 2.0)}
                    style={{ width: 110, fontSize: 11 }}
                  />
                </div>

                <div className="hud-row">
                  <span style={{ fontSize: 11 }}>Emitter Spacing (m)</span>
                  <input
                    type="number"
                    className="hud-input"
                    value={emitterSpacing}
                    step={0.05}
                    onChange={(e) => setEmitterSpacing(parseFloat(e.target.value) || 0.3)}
                    style={{ width: 110, fontSize: 11 }}
                  />
                </div>

                <div className="hud-row">
                  <span style={{ fontSize: 11 }}>Lateral Spacing (m)</span>
                  <input
                    type="number"
                    className="hud-input"
                    value={lateralSpacing}
                    step={0.1}
                    onChange={(e) => setLateralSpacing(parseFloat(e.target.value) || 1.0)}
                    style={{ width: 110, fontSize: 11 }}
                  />
                </div>

                {/* Rerunnable Hydraulic Analysis Button */}
                <div style={{ marginTop: 8 }}>
                  <button
                    className="hud-btn primary"
                    onClick={handleRunHydraulics}
                    disabled={isRunningHydraulics}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 8,
                      fontWeight: "bold",
                      fontSize: 11,
                      background: "var(--primary)",
                      borderColor: "var(--primary)",
                      color: "#ffffff",
                    }}
                  >
                    {isRunningHydraulics ? (
                      <RefreshCw size={13} className="spin" color="#ffffff" />
                    ) : (
                      <Zap size={13} color="#ffffff" />
                    )}
                    {isRunningHydraulics ? "Running Analysis..." : "Run Hydraulic Analysis"}
                  </button>
                  {hydraulicStatus && (
                    <div style={{
                      fontSize: 10,
                      marginTop: 6,
                      textAlign: "center",
                      color: hydraulicStatus.startsWith("✓") ? "var(--success)" : "var(--accent)"
                    }}>
                      {hydraulicStatus}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 2D Visualization Options (Functional) */}
            <div className="hud-box">
              <div className="hud-box-title" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
                <Eye size={13} /> 2D Visualization Options
              </div>
              <div style={{ color: "var(--text-dim)", fontSize: 10, fontStyle: "italic", marginBottom: 8 }}>
                Live layer visibility controls for the 2D Engineering Layout
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 11 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Show Lateral Lines</span>
                  <input
                    type="checkbox"
                    checked={layout2DOptions.showLaterals}
                    onChange={(e) => setLayout2DOption("showLaterals", e.target.checked)}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Show Emitter Dots</span>
                  <input
                    type="checkbox"
                    checked={layout2DOptions.showEmitters}
                    onChange={(e) => setLayout2DOption("showEmitters", e.target.checked)}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Show Mainline Pipe</span>
                  <input
                    type="checkbox"
                    checked={layout2DOptions.showMainline}
                    onChange={(e) => setLayout2DOption("showMainline", e.target.checked)}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Show Pump / Water Source</span>
                  <input
                    type="checkbox"
                    checked={layout2DOptions.showPump}
                    onChange={(e) => setLayout2DOption("showPump", e.target.checked)}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Pressure Zone Shading</span>
                  <input
                    type="checkbox"
                    checked={layout2DOptions.showPressureShading}
                    onChange={(e) => setLayout2DOption("showPressureShading", e.target.checked)}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Summary &amp; Scale Info</span>
                  <input
                    type="checkbox"
                    checked={layout2DOptions.showDimensions}
                    onChange={(e) => setLayout2DOption("showDimensions", e.target.checked)}
                  />
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === "ai" && (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
            {/* AI Engine Status Header */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "6px 10px",
                background: "var(--bg-subtle)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 6,
                marginBottom: 8,
                fontSize: 10,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    background: aiStatus?.is_live_llm ? "#10b981" : "#f59e0b",
                    boxShadow: aiStatus?.is_live_llm ? "0 0 6px #10b981" : "none",
                  }}
                />
                <span style={{ color: "var(--text)" }}>
                  {aiStatus?.is_live_llm ? (
                    <span>Model: <strong>{aiStatus.provider}</strong></span>
                  ) : (
                    <span>Engine: <strong>Local Offline Rules</strong></span>
                  )}
                </span>
              </div>
              {!aiStatus?.is_live_llm && (
                <a
                  href="https://console.groq.com/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: "var(--primary)",
                    fontSize: 9.5,
                    fontWeight: 600,
                    textDecoration: "none",
                  }}
                  title="Add free GROQ_API_KEY to .env for real Llama 3.3"
                >
                  + Free Groq key →
                </a>
              )}
            </div>

            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10, paddingRight: 4 }}>
              {messages.map((m, i) => (
                <div
                  key={i}
                  style={{
                    padding: "8px 12px",
                    borderRadius: 6,
                    fontSize: 11,
                    lineHeight: 1.45,
                    background: m.role === "user" ? "var(--bg-subtle)" : "var(--bg-card)",
                    border: "1px solid var(--border)",
                    alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                    maxWidth: "92%",
                    color: m.role === "user" ? "var(--text-bright)" : "var(--text)",
                  }}
                >
                  <div style={{ fontSize: 9, color: "var(--text-dim)", marginBottom: 4, fontWeight: "bold", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                    <span>{m.role === "user" ? "👤 YOU" : "🤖 AGRI-EXPERT AI"}</span>
                    {m.role === "ai" && (
                      <span
                        style={{
                          fontSize: 8.5,
                          fontWeight: 600,
                          padding: "1px 5px",
                          borderRadius: 4,
                          background: m.source?.startsWith("groq") ? "rgba(16, 185, 129, 0.15)" : m.source?.startsWith("openrouter") ? "rgba(59, 130, 246, 0.15)" : "rgba(245, 158, 11, 0.15)",
                          color: m.source?.startsWith("groq") ? "#10b981" : m.source?.startsWith("openrouter") ? "#3b82f6" : "#f59e0b",
                        }}
                      >
                        {m.source?.startsWith("groq") ? "Groq AI" : m.source?.startsWith("openrouter") ? "OpenRouter" : "Offline Engine"}
                      </span>
                    )}
                  </div>
                  <div style={{ lineHeight: 1.55 }}>
                    {m.role === "ai" ? renderMarkdown(m.text) : m.text}
                  </div>
                </div>
              ))}
              {isAiThinking && (
                <div style={{ fontSize: 10, color: "var(--accent)", fontStyle: "italic", padding: "4px 8px" }}>
                  Agronomist AI is formulating response…
                </div>
              )}
            </div>

            {/* Quick suggestion chips */}
            {messages.length <= 2 && !isAiThinking && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 6 }}>
                {[
                  "💧 Watering schedule",
                  "🔧 Drip system setup",
                  "🌱 Fertigation plan",
                  "🪱 Pest & disease",
                  "💰 System cost",
                  "🌾 Expected yield",
                ].map((chip) => (
                  <button
                    key={chip}
                    onClick={() => {
                      setInputMessage(chip.replace(/^[^\s]+ /, ""));
                    }}
                    style={{
                      background: "var(--primary-06)",
                      border: "1px solid var(--border)",
                      borderRadius: 12,
                      padding: "3px 9px",
                      fontSize: 10,
                      color: "var(--primary)",
                      cursor: "pointer",
                      fontWeight: 600,
                      transition: "background 0.12s",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = "var(--primary-12)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "var(--primary-06)")}
                  >
                    {chip}
                  </button>
                ))}
              </div>
            )}

            <div style={{ display: "flex", gap: 6, marginTop: 8, paddingTop: 8, borderTop: "1px solid var(--border-subtle)" }}>
              <input
                type="text"
                className="hud-input"
                placeholder={isAiThinking ? "Waiting for response…" : "e.g. How much water does my crop need?"}
                value={inputMessage}
                disabled={isAiThinking}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                style={{ flex: 1, fontSize: 11 }}
              />
              <button
                className="hud-btn primary"
                disabled={isAiThinking || !inputMessage.trim()}
                onClick={handleSendMessage}
                style={{ padding: "6px 10px", fontSize: 11, opacity: (isAiThinking || !inputMessage.trim()) ? 0.6 : 1 }}
              >
                <Send size={12} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
