"use client";

import React, { useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { optimizeIrrigation } from "@/lib/api";
import { FileDown, CheckCircle, RefreshCw, AlertCircle } from "lucide-react";

export default function ResultsPanel() {
  const { design, location, crop, soil, layoutPngBase64 } = useIrriGridStore();
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState("");

  async function handleDownloadPdf() {
    setPdfLoading(true);
    setPdfError("");
    try {
      // Call the backend optimizer to get a real server-side design_id with a PDF record
      const result = await optimizeIrrigation({
        crop_name: crop?.name || "Tomato",
        soil_type: soil?.name || "Volcanic Loam",
        location_name: location.district ? `${location.district}, Rwanda` : "Rwanda",
        field_area_ha: location.area_ha || design?.field_area_ha || 0.25,
        polygon_coordinates: location.polygon
          ? location.polygon.map(([lat, lon]) => [lat, lon])
          : undefined,
        water_source_coords: location.water_source
          ? [location.water_source[0], location.water_source[1]]
          : undefined,
        slope_percent: location.slope_pct || design?.slope_percent || 2.0,
        lateral_spacing: design?.recommended_design?.lateral_spacing_m,
        emitter_spacing: design?.recommended_design?.emitter_spacing_m,
        layout_image_base64: layoutPngBase64 || undefined,
        climate_data: useIrriGridStore.getState().monthlyClimate,
        soil_detail: soil,
        water_balance: useIrriGridStore.getState().waterBalance,
        schedule_summary: useIrriGridStore.getState().scheduleSummary,
      });
      if (result?.pdf_url) {
        const url = result.pdf_url.startsWith("http")
          ? result.pdf_url
          : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${result.pdf_url}`;
        window.open(url, "_blank");
      } else {
        throw new Error("No PDF URL returned from server");
      }
    } catch (err: any) {
      console.error("PDF download error:", err);
      setPdfError("Backend PDF unavailable — check that the server is running.");
    } finally {
      setPdfLoading(false);
    }
  }

  if (!design) {
    return (
      <div>
        <div style={{ color: "var(--primary)", fontSize: "12px", fontWeight: 600, marginBottom: "10px" }}>
          Executive System Summary &amp; Export
        </div>
        <div style={{ color: "var(--text-dim)", fontSize: "11px", lineHeight: 1.5 }}>
          Run the NSGA-II optimization in the Design panel (Step 10) to generate engineering specs and download the official PDF report.
        </div>
      </div>
    );
  }

  const d = design.recommended_design;

  return (
    <div>
      <div style={{ color: "var(--primary)", fontSize: "12px", fontWeight: 600, marginBottom: "10px" }}>
        Executive Design Results &amp; PDF
      </div>
      <div style={{ color: "var(--success)", fontSize: "11px", marginBottom: "12px", display: "flex", alignItems: "center", gap: 6 }}>
        <CheckCircle size={13} />
        <span>Optimization Complete · {design.total_candidates_passing} passing configurations</span>
      </div>
      <div className="hud-row"><span>Emission Uniformity</span><span style={{ fontFamily: "var(--font-mono)", color: "var(--success)", fontWeight: 600 }}>{d?.emission_uniformity_percent}%</span></div>
      <div className="hud-row"><span>Pump Power</span><span style={{ fontFamily: "var(--font-mono)", color: "var(--primary)", fontWeight: 600 }}>{d?.pump_power_kw?.toFixed(2)} kW</span></div>
      <div className="hud-row"><span>Total System Cost</span><span style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontWeight: 600 }}>{d ? (d.total_cost_rwf / 1e6).toFixed(2) : "—"}M RWF</span></div>
      <div className="hud-row"><span>Lateral Pipe</span><span style={{ fontFamily: "var(--font-mono)" }}>{d?.lateral_diameter_mm} mm @ {d?.lateral_spacing_m} m</span></div>
      <div className="hud-row"><span>Mainline Pipe</span><span style={{ fontFamily: "var(--font-mono)" }}>{d?.main_diameter_mm} mm PVC</span></div>
      <div className="hud-row"><span>Emitter Spacing</span><span style={{ fontFamily: "var(--font-mono)" }}>{d?.emitter_spacing_m} m ({d?.emitter_flow_lph} L/h)</span></div>
      <div className="hud-row"><span>Total Emitters</span><span style={{ fontFamily: "var(--font-mono)", color: "var(--text)" }}>{d?.total_emitters?.toLocaleString()}</span></div>

      <button
        className="hud-btn hud-btn-full primary"
        onClick={handleDownloadPdf}
        disabled={pdfLoading}
        style={{
          marginTop: "14px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          padding: "8px 14px",
          fontWeight: "bold",
          fontSize: 11,
          width: "100%",
          opacity: pdfLoading ? 0.7 : 1,
          cursor: pdfLoading ? "wait" : "pointer",
        }}
      >
        {pdfLoading ? <RefreshCw size={14} className="spin" /> : <FileDown size={14} />}
        {pdfLoading ? "Generating PDF..." : "Download PDF Report"}
      </button>

      {pdfError && (
        <div style={{ color: "var(--danger)", fontSize: 10, marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
          <AlertCircle size={11} />
          <span>{pdfError}</span>
        </div>
      )}
    </div>
  );
}
