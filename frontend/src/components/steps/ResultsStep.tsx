"use client";

import React, { useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { getDesignPdfUrl, askAgronomist, optimizeIrrigation } from "@/lib/api";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import {
  FileDown,
  Sparkles,
  Send,
  RotateCcw,
  CheckCircle2,
  Cpu,
  Droplets,
  Wrench,
  RefreshCw,
} from "lucide-react";

export default function ResultsStep() {
  const { location, crop, soil, design, setDesign, waterBalance, scheduleSummary, monthlyClimate, layoutPngBase64, resetAll } = useIrriGridStore();

  const [aiPrompt, setAiPrompt] = useState(
    "What are the best practices for fertigation and emitter maintenance during flowering stage?"
  );
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [isAskingAi, setIsAskingAi] = useState(false);
  const [aiSource, setAiSource] = useState<string | null>(null);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);

  const opt = design?.optimal_design;
  const designId = design?.design_id;

  const totalNirM3 = Math.round(waterBalance.reduce((s, r) => s + r.nir_m3, 0));

  const handleDownloadPdf = async () => {
    if (designId) {
      const url = getDesignPdfUrl(designId);
      window.open(url, "_blank");
      return;
    }

    try {
      setIsGeneratingPdf(true);
      const res = await optimizeIrrigation({
        crop_name: crop.name,
        soil_type: soil.name,
        location_name: location.district ? `${location.district}, Rwanda` : "Rwanda",
        field_area_ha: location.area_ha || 0.25,
        polygon_coordinates: location.polygon,
        water_source_coords: location.water_source,
        slope_percent: location.slope_pct || 2.0,
        layout_image_base64: layoutPngBase64 || undefined,
        climate_data: monthlyClimate,
        soil_detail: soil,
        water_balance: waterBalance,
        schedule_summary: scheduleSummary,
      });
      setDesign(res);
      if (res?.pdf_url) {
        const url = res.pdf_url.startsWith("http")
          ? res.pdf_url
          : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${res.pdf_url}`;
        window.open(url, "_blank");
      }
    } catch (e) {
      console.error("PDF download failed:", e);
      alert("Could not generate PDF. Please ensure backend is reachable.");
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const handleAskAi = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiPrompt.trim()) return;

    try {
      setIsAskingAi(true);
      const res = await askAgronomist({
        prompt: aiPrompt,
        crop_name: crop.name,
        location_name: location.district,
        field_area_ha: location.area_ha,
        soil_type: soil.name,
      });
      setAiResponse(res.advice);
      setAiSource(res.source);
    } catch (err) {
      setAiResponse(
        `For ${crop.name} in ${location.district}: Apply light, frequent irrigations (every ${scheduleSummary.intervalDays || 4} days) during vegetative development. Check filter screens after every 24 hours of pumping.`
      );
      setAiSource("offline_rules");
    } finally {
      setIsAskingAi(false);
    }
  };

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <CheckCircle2 size={18} />
            Step 09: Executive Summary, AI Agronomist & PDF Generation
          </div>
          <button
            onClick={handleDownloadPdf}
            disabled={isGeneratingPdf}
            className="btn btn-primary"
            style={{ padding: "6px 14px" }}
          >
            {isGeneratingPdf ? <RefreshCw size={16} className="spin" /> : <FileDown size={16} />}
            {isGeneratingPdf ? "Generating PDF..." : "Download Engineering PDF"}
          </button>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-dim)", marginBottom: "1.25rem" }}>
          Stateless design report compiled for <strong>{crop.name}</strong> on <strong>{location.area_ha} ha</strong> in <strong>{location.district} District</strong>. Download the official PDF containing hydraulics calculations, operational schedule, and bill of materials.
        </p>

        {/* Multi-Section Executive Dashboard */}
        <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Total CAPEX Cost"
            value={`${(opt?.total_cost_rwf || 0).toLocaleString()} RWF`}
            subtext="Complete Bill of Materials"
            color="var(--accent)"
          />
          <StatCard
            label="Emission Uniformity"
            value={`${opt?.emission_uniformity_pct || 92.5}%`}
            subtext="Christiansen EU Coefficient"
            color="var(--success)"
          />
          <StatCard
            label="Irrigation Schedule"
            value={`Every ${scheduleSummary.intervalDays} Days`}
            subtext={`${scheduleSummary.durationHrs} hrs per shift`}
            color="var(--primary)"
          />
          <StatCard
            label="Seasonal Net Water"
            value={totalNirM3.toLocaleString()}
            unit="m³"
            subtext="Field seasonal demand"
          />
        </div>

        {/* Detailed Breakdown Card */}
        <div style={{ background: "rgba(10, 15, 30, 0.7)", border: "1px solid var(--border)", borderRadius: "6px", padding: "1.25rem", marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "0.82rem", color: "var(--primary)", textTransform: "uppercase", fontWeight: 700, marginBottom: "0.85rem" }}>
            Comprehensive Project Specifications
          </div>

          <div className="grid-3" style={{ fontSize: "0.82rem", fontFamily: "var(--font-mono)" }}>
            <div>
              <div style={{ color: "var(--text-dim)", marginBottom: "4px" }}>FIELD & TERRAIN:</div>
              <div>• District: {location.district} ({location.province})</div>
              <div>• Field Area: {location.area_ha} ha ({Math.round(location.area_ha * 10000)} m²)</div>
              <div>• Terrain Slope: {location.slope_pct}%</div>
              <div>• Elevation: {location.elevation_m} m a.s.l.</div>
            </div>

            <div>
              <div style={{ color: "var(--text-dim)", marginBottom: "4px" }}>CROP & SOIL:</div>
              <div>• Crop: {crop.name} ({crop.planting_date})</div>
              <div>• Soil Texture: {soil.name}</div>
              <div>• Field Capacity: {soil.field_capacity}% | WP: {soil.wilting_point}%</div>
              <div>• NDVI Health: {crop.ndvi ?? 0.68} ({crop.ndvi_status || "Healthy"})</div>
            </div>

            <div>
              <div style={{ color: "var(--text-dim)", marginBottom: "4px" }}>HYDRAULIC HARDWARE:</div>
              <div>• Mainline: {opt?.mainline_diameter_mm || 50} mm HDPE</div>
              <div>• Manifold: {opt?.manifold_diameter_mm || 32} mm PVC</div>
              <div>• Laterals: {opt?.lateral_diameter_mm || 16} mm PE</div>
              <div>• Pump: {opt?.pump_power_kw || 0.75} kW ({((opt?.pump_power_kw || 0.75) * 1.341).toFixed(1)} HP)</div>
            </div>
          </div>
        </div>

        {/* AI Agronomist Interactive Advice Panel */}
        <div style={{ background: "rgba(6, 12, 28, 0.9)", border: "1px solid var(--accent)", borderRadius: "6px", padding: "1.25rem", marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.85rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--accent)", fontWeight: 700, fontSize: "0.9rem", textTransform: "uppercase" }}>
              <Sparkles size={18} />
              AI Agronomist Expert (Rwanda Agriculture Support)
            </div>
            {aiSource && (
              <span className="badge-tag">
                Source: {aiSource?.startsWith("groq") ? "Groq AI" : aiSource?.startsWith("openrouter") ? "OpenRouter" : "Agronomy Rules"}
              </span>
            )}
          </div>

          <form onSubmit={handleAskAi} style={{ display: "flex", gap: "8px", marginBottom: "1rem" }}>
            <input
              type="text"
              className="form-input"
              style={{ flex: 1 }}
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="Ask the agronomist about fertigation, pest management, or emitter maintenance..."
            />
            <button
              type="submit"
              disabled={isAskingAi}
              className="btn btn-primary"
              style={{ padding: "0 1.25rem", flexShrink: 0 }}
            >
              <Send size={15} />
              {isAskingAi ? "Thinking..." : "Ask Expert"}
            </button>
          </form>

          {aiResponse && (
            <div
              style={{
                background: "rgba(0, 255, 200, 0.05)",
                borderLeft: "3px solid var(--accent)",
                padding: "0.85rem 1rem",
                borderRadius: "0 4px 4px 0",
                fontSize: "0.85rem",
                lineHeight: 1.6,
                color: "var(--text-bright)",
              }}
            >
              {aiResponse}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem" }}>
          <button
            onClick={() => {
              if (confirm("Reset and start a new design session?")) {
                resetAll();
              }
            }}
            className="btn btn-secondary"
          >
            <RotateCcw size={16} />
            Start New Field Design
          </button>

          <button
            onClick={handleDownloadPdf}
            disabled={isGeneratingPdf}
            className="btn btn-primary"
            style={{ padding: "0.65rem 1.5rem" }}
          >
            {isGeneratingPdf ? <RefreshCw size={18} className="spin" /> : <FileDown size={18} />}
            {isGeneratingPdf ? "Generating Report..." : "Download Complete PDF Report"}
          </button>
        </div>
      </div>

      <StepNav nextLabel="Complete Workflow" />
    </div>
  );
}
