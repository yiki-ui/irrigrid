"use client";

import React, { useEffect, useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { fetchSoils } from "@/lib/api";
import { calculateSoilMoisture } from "@/lib/calculations";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { Layers, Droplet, Check } from "lucide-react";

export default function SoilStep() {
  const { soil, setSoil, crop } = useIrriGridStore();
  const [soilList, setSoilList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadSoils() {
      try {
        setLoading(true);
        const data = await fetchSoils();
        setSoilList(data);
      } catch (err) {
        console.error("Soils load fallback:", err);
      } finally {
        setLoading(false);
      }
    }
    loadSoils();
  }, []);

  const moisture = calculateSoilMoisture(
    soil.field_capacity,
    soil.wilting_point,
    crop.root_depth_m || 0.6,
    crop.depletion_fraction || 0.4
  );

  const handleSelectSoil = (s: any) => {
    setSoil({
      name: s.name,
      description: s.description || "",
      field_capacity: s.field_capacity ?? 30,
      wilting_point: s.wilting_point ?? 15,
      available_water_mm_m: s.available_water_mm_m ?? 150,
      max_infiltration_rate: s.max_infiltration_rate ?? 25,
    });
  };

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <Layers size={18} />
            Step 05: Soil Moisture Profile &amp; Water Retention
          </div>
          <span className="badge-tag">
            {soil.source || "ISRIC SoilGrids v2.0"}
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.85rem", flexWrap: "wrap", gap: 8 }}>
          <p style={{ fontSize: "0.85rem", color: "var(--text-dim)", margin: 0 }}>
            Soil properties determine how much water the root zone can hold between irrigations.
          </p>
          <div style={{ fontSize: "0.8rem", color: "var(--accent)" }}>
            Current Soil: <strong>{soil.name}</strong>
            {soil.sand_pct != null ? (
              <span style={{ color: "var(--text-dim)", marginLeft: 6 }}>
                (Sand {soil.sand_pct}% · Silt {soil.silt_pct}% · Clay {soil.clay_pct}%)
              </span>
            ) : (
              <span style={{ color: "var(--text-dim)", marginLeft: 6 }}>
                (Grain composition: Not measured)
              </span>
            )}
          </div>
        </div>

        {/* Moisture Metrics */}
        <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Total Available (TAW)"
            value={moisture.taw}
            unit="mm"
            subtext={`Across ${crop.root_depth_m}m root zone`}
            color="var(--primary)"
          />
          <StatCard
            label="Readily Available (RAW)"
            value={moisture.raw}
            unit="mm"
            subtext={`p = ${crop.depletion_fraction * 100}% threshold`}
            color="var(--accent)"
          />
          <StatCard
            label="Field Capacity"
            value={soil.field_capacity}
            unit="%"
            subtext="Upper retention limit"
          />
          <StatCard
            label="Wilting Point"
            value={soil.wilting_point}
            unit="%"
            subtext="Lower plant limit"
          />
        </div>

        {/* Soil Moisture Visual Bar */}
        <div style={{ background: "rgba(10, 15, 30, 0.7)", border: "1px solid var(--border)", borderRadius: "4px", padding: "1rem", marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: "0.5rem" }}>
            <span>Wilting Point ({soil.wilting_point}%)</span>
            <span style={{ color: "var(--accent)" }}>RAW: {moisture.raw} mm</span>
            <span style={{ color: "var(--primary)" }}>Field Capacity ({soil.field_capacity}%)</span>
          </div>

          <div style={{ height: "18px", width: "100%", background: "rgba(255, 23, 68, 0.15)", borderRadius: "4px", overflow: "hidden", position: "relative", display: "flex" }}>
            {/* TAW bar */}
            <div
              style={{
                width: `${Math.min(100, Math.max(20, (moisture.taw / 150) * 100))}%`,
                background: "linear-gradient(90deg, rgba(0, 229, 255, 0.3), var(--primary))",
                height: "100%",
                position: "relative",
              }}
            >
              {/* RAW fraction */}
              <div
                style={{
                  width: `${crop.depletion_fraction * 100}%`,
                  height: "100%",
                  background: "var(--accent)",
                  opacity: 0.85,
                }}
                title={`RAW: ${moisture.raw} mm`}
              />
            </div>
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: "0.35rem", display: "flex", justifyContent: "space-between" }}>
            <span>Permanent Wilting (Zero uptake)</span>
            <span style={{ color: "var(--accent)" }}>■ Readily Available (Comfort Zone)</span>
            <span style={{ color: "var(--primary)" }}>■ Saturated / Field Capacity</span>
          </div>
        </div>

        {/* Soil Catalog Selection */}
        <div style={{ marginBottom: "1.25rem" }}>
          <div className="form-label" style={{ marginBottom: "0.5rem" }}>Select Soil Type (Rwanda Georeferenced Profiles)</div>
          <div className="grid-3">
            {(soilList.length > 0
              ? soilList
              : [
                  { name: "Volcanic Loam", field_capacity: 34, wilting_point: 16, available_water_mm_m: 180, max_infiltration_rate: 25, description: "Northern volcanic soils (Musanze, Nyabihu, Burera)" },
                  { name: "Clay Loam", field_capacity: 32, wilting_point: 18, available_water_mm_m: 140, max_infiltration_rate: 15, description: "Common throughout Central and Southern Plateau" },
                  { name: "Sandy Clay Loam", field_capacity: 28, wilting_point: 14, available_water_mm_m: 140, max_infiltration_rate: 20, description: "Eastern Province (Nyagatare, Bugesera, Kayonza)" },
                  { name: "Sandy Loam", field_capacity: 22, wilting_point: 10, available_water_mm_m: 120, max_infiltration_rate: 35, description: "Light valley and riverbed soils" },
                  { name: "Clay", field_capacity: 38, wilting_point: 22, available_water_mm_m: 160, max_infiltration_rate: 8, description: "Heavy marshland and bottomland valley soils" },
                  { name: "Silt Loam", field_capacity: 30, wilting_point: 12, available_water_mm_m: 180, max_infiltration_rate: 18, description: "Deep alluvial deposits" },
                ]
            ).map((s) => {
              const isSelected = soil.name.toLowerCase() === s.name.toLowerCase();
              return (
                <div
                  key={s.name}
                  onClick={() => handleSelectSoil(s)}
                  className={`selection-card ${isSelected ? "selected" : ""}`}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div className="selection-card-title">{s.name}</div>
                    {isSelected && <Check size={18} style={{ color: "var(--primary)" }} />}
                  </div>
                  <div className="selection-card-desc">{s.description || `Infiltration: ${s.max_infiltration_rate} mm/h`}</div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                    FC: {s.field_capacity}% • WP: {s.wilting_point}% • TAW: {s.available_water_mm_m} mm/m
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Manual Overrides */}
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Field Capacity (%)</label>
            <input
              type="number"
              step="0.5"
              className="form-input"
              value={soil.field_capacity}
              onChange={(e) => setSoil({ field_capacity: parseFloat(e.target.value) || 20 })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Wilting Point (%)</label>
            <input
              type="number"
              step="0.5"
              className="form-input"
              value={soil.wilting_point}
              onChange={(e) => setSoil({ wilting_point: parseFloat(e.target.value) || 10 })}
            />
          </div>
        </div>
      </div>

      <StepNav />
    </div>
  );
}
