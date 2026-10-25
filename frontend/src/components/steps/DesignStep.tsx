"use client";

import React, { useState, useEffect } from "react";
import { useIrriGridStore } from "@/lib/store";
import { optimizeIrrigation } from "@/lib/api";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { AlertTriangle, Wrench, Play, ShieldCheck, DollarSign, Zap, LayoutGrid, CheckCircle } from "lucide-react";

export default function DesignStep() {
  const { location, crop, soil, design, setDesign, isOptimizing, setIsOptimizing } = useIrriGridStore();
  const [minEu, setMinEu] = useState(90.0);
  const [optError, setOptError] = useState<string | null>(null);

  const handleRunOptimizer = async () => {
    try {
      setIsOptimizing(true);
      setOptError(null);

      const res = await optimizeIrrigation({
        crop_name: crop.name,
        soil_type: soil.name,
        location_name: `${location.district}, ${location.province}`,
        field_area_ha: location.area_ha,
        polygon_coordinates: location.polygon,
        slope_percent: location.slope_pct,
        min_eu_threshold: minEu,
      });

      setDesign(res);
    } catch (err: any) {
      setOptError(err.message || "Optimization request failed");
    } finally {
      setIsOptimizing(false);
    }
  };

  // Auto-run if no design yet
  useEffect(() => {
    if (!design && !isOptimizing) {
      handleRunOptimizer();
    }
  }, []);

  const opt = design?.optimal_design;
  const bom = design?.bom || [];

  const getEuBadge = (eu: number) => {
    if (eu >= 90) return <span className="badge-eu-high">{eu}% EU (Excellent)</span>;
    if (eu >= 85) return <span className="badge-eu-mid">{eu}% EU (Good)</span>;
    return <span className="badge-eu-low">{eu}% EU (Borderline)</span>;
  };

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <Wrench size={18} />
            Step 08: NSGA-II Hydraulic Optimization & Bill of Materials
          </div>
          <button
            onClick={handleRunOptimizer}
            disabled={isOptimizing}
            className="btn btn-primary"
            style={{ padding: "5px 12px", fontSize: "0.78rem" }}
          >
            <Play size={14} />
            {isOptimizing ? "Optimizing Hydraulics..." : "Re-Run Optimizer"}
          </button>
        </div>

        {optError && (
          <div style={{ color: "var(--danger)", fontSize: "0.8rem", marginBottom: "0.85rem" }}>
            ⚠️ {optError}
          </div>
        )}

        {isOptimizing && (
          <div style={{ padding: "2rem", textAlign: "center", background: "rgba(0, 229, 255, 0.05)", borderRadius: "6px", marginBottom: "1.25rem", border: "1px dashed var(--primary)" }}>
            <div style={{ color: "var(--primary)", fontSize: "1rem", fontWeight: 700, marginBottom: "0.5rem" }}>
              Running NSGA-II Multi-Objective Optimization...
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
              Evaluating pipe diameters, Hazen-Williams friction losses, elevation gradient ({location.slope_pct}%), and Christiansen uniformity coefficient.
            </div>
          </div>
        )}

        {opt && (
          <>
            {/* Design Metrics */}
            <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
              <StatCard
                label="System Cost"
                value={`${(opt.total_cost_rwf || 0).toLocaleString()} RWF`}
                subtext="Total hardware CAPEX"
                color="var(--accent)"
              />
              <StatCard
                label="Emission Uniformity"
                value={`${opt.emission_uniformity_pct || 92.5}%`}
                subtext={opt.emission_uniformity_pct >= 90 ? "Uniform distribution" : "Acceptable"}
                color="var(--success)"
              />
              <StatCard
                label="Pump Power"
                value={opt.pump_power_kw || 0.75}
                unit="kW"
                subtext={`${((opt.pump_power_kw || 0.75) * 1.341).toFixed(1)} HP`}
              />
              <StatCard
                label="Operating Pressure"
                value={opt.operating_pressure_bar || 1.2}
                unit="bar"
                subtext="Emitter head nominal"
              />
            </div>

            {/* Split View: Technical Specs + 2D SVG Field Layout */}
            <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
              {/* Left Column: Hydraulic Specifications */}
              <div style={{ background: "rgba(10, 15, 30, 0.7)", border: "1px solid var(--border)", borderRadius: "6px", padding: "1.25rem" }}>
                <div style={{ fontSize: "0.82rem", color: "var(--primary)", textTransform: "uppercase", fontWeight: 700, marginBottom: "1rem", display: "flex", alignItems: "center", gap: "6px" }}>
                  <ShieldCheck size={16} /> Hydraulic Network Specifications
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", fontSize: "0.82rem", fontFamily: "var(--font-mono)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0, 229, 255, 0.1)", paddingBottom: "4px" }}>
                    <span style={{ color: "var(--text-dim)" }}>Lateral Pipe Diameter:</span>
                    <span style={{ color: "var(--text-bright)", fontWeight: 700 }}>{opt.lateral_diameter_mm || 16} mm PE</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0, 229, 255, 0.1)", paddingBottom: "4px" }}>
                    <span style={{ color: "var(--text-dim)" }}>Manifold / Submain:</span>
                    <span style={{ color: "var(--text-bright)", fontWeight: 700 }}>{opt.manifold_diameter_mm || 32} mm PVC</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0, 229, 255, 0.1)", paddingBottom: "4px" }}>
                    <span style={{ color: "var(--text-dim)" }}>Mainline Delivery Pipe:</span>
                    <span style={{ color: "var(--text-bright)", fontWeight: 700 }}>{opt.mainline_diameter_mm || 50} mm HDPE</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0, 229, 255, 0.1)", paddingBottom: "4px" }}>
                    <span style={{ color: "var(--text-dim)" }}>Emitter Spacing:</span>
                    <span style={{ color: "var(--text-bright)" }}>{opt.emitter_spacing_m || 0.3} m on-line</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0, 229, 255, 0.1)", paddingBottom: "4px" }}>
                    <span style={{ color: "var(--text-dim)" }}>Lateral Row Spacing:</span>
                    <span style={{ color: "var(--text-bright)" }}>{opt.lateral_spacing_m || 1.0} m crop rows</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0, 229, 255, 0.1)", paddingBottom: "4px" }}>
                    <span style={{ color: "var(--text-dim)" }}>Emitter Nominal Flow:</span>
                    <span style={{ color: "var(--text-bright)" }}>{opt.emitter_discharge_lph || 2.0} L/hr</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "4px" }}>
                    <span style={{ color: "var(--text-dim)" }}>Uniformity Quality:</span>
                    <span>{getEuBadge(opt.emission_uniformity_pct || 92.5)}</span>
                  </div>
                </div>
              </div>

              {/* Right Column: 2D Field Layout SVG Schematic */}
              <div style={{ background: "rgba(10, 15, 30, 0.7)", border: "1px solid var(--border)", borderRadius: "6px", padding: "1.25rem", display: "flex", flexDirection: "column" }}>
                <div style={{ fontSize: "0.82rem", color: "var(--primary)", textTransform: "uppercase", fontWeight: 700, marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}>
                  <LayoutGrid size={16} /> 2D Field Layout Schematic
                </div>

                <div style={{ flex: 1, minHeight: "220px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <svg viewBox="0 0 400 240" style={{ width: "100%", height: "100%", maxHeight: "230px" }}>
                    {/* Field Boundary */}
                    <rect x="20" y="20" width="360" height="200" fill="rgba(0, 229, 255, 0.04)" stroke="var(--primary)" strokeWidth="1.5" strokeDasharray="4,4" rx="4" />

                    {/* Water source / pump marker */}
                    <circle cx="45" cy="45" r="12" fill="#00e5ff" />
                    <text x="45" y="49" fontSize="10" fontWeight="bold" textAnchor="middle" fill="#050510">P</text>
                    <text x="65" y="48" fontSize="11" fill="var(--primary)" fontFamily="var(--font-mono)">PUMP ({opt.pump_power_kw || 0.75} kW)</text>

                    {/* Mainline (Deep Blue) */}
                    <line x1="45" y1="57" x2="45" y2="190" stroke="#00b0ff" strokeWidth="4" />
                    <text x="55" y="125" fontSize="10" fill="#00b0ff" fontFamily="var(--font-mono)">Mainline ({opt.mainline_diameter_mm || 50}mm)</text>

                    {/* Manifold across field */}
                    <line x1="45" y1="190" x2="360" y2="190" stroke="#00e5ff" strokeWidth="3" />
                    <text x="210" y="208" fontSize="10" fill="#00e5ff" textAnchor="middle" fontFamily="var(--font-mono)">Submain Manifold ({opt.manifold_diameter_mm || 32}mm)</text>

                    {/* Laterals (vertical cyan lines) */}
                    {[90, 135, 180, 225, 270, 315, 355].map((x, i) => (
                      <g key={i}>
                        <line x1={x} y1="40" x2={x} y2="190" stroke="rgba(0, 255, 200, 0.65)" strokeWidth="1.5" />
                        {/* Emitter dots */}
                        {[60, 85, 110, 135, 160].map((y, j) => (
                          <circle key={j} cx={x} cy={y} r="2" fill="var(--accent)" />
                        ))}
                      </g>
                    ))}

                    <text x="360" y="32" fontSize="9" fill="var(--text-dim)" textAnchor="end" fontFamily="var(--font-mono)">Laterals ({opt.lateral_diameter_mm || 16}mm) & Emitters</text>
                  </svg>
                </div>
              </div>
            </div>

            {/* Bill of Materials (BOM) Table */}
            <div style={{ marginBottom: "0.75rem", fontSize: "0.78rem", color: "var(--primary)", textTransform: "uppercase", fontWeight: 700 }}>
              Itemized Bill of Materials (Local Market Quotation)
            </div>

            <div className="hud-table-container">
              <table className="hud-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Component</th>
                    <th>Specification</th>
                    <th>Qty</th>
                    <th>Unit</th>
                    <th>Unit Cost (RWF)</th>
                    <th style={{ color: "var(--accent)" }}>Total (RWF)</th>
                  </tr>
                </thead>
                <tbody>
                  {bom.map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ color: "var(--text-dim)" }}>{item.category}</td>
                      <td style={{ fontWeight: 600, color: "var(--text-bright)" }}>{item.item}</td>
                      <td>{item.specification}</td>
                      <td>{item.quantity.toLocaleString()}</td>
                      <td>{item.unit}</td>
                      <td>{item.unit_price_rwf.toLocaleString()}</td>
                      <td style={{ fontWeight: 700, color: "var(--accent)" }}>{item.total_rwf.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      <StepNav />
    </div>
  );
}
