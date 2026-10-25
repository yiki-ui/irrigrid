"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useIrriGridStore } from "@/lib/store";
import { fetchCrops } from "@/lib/api";
import { CloudRain, Lightbulb, Map, MapPin, Mountain, Ruler, Sprout, Zap } from "lucide-react";
import nisrYieldData from "@/lib/nisr_yield.json";

const FALLBACK_CROPS = [
  "Tomato", "Maize", "Beans", "Pepper", "Onion",
  "Cabbage", "Potato", "Wheat", "Sorghum",
];

export default function StartPanel() {
  const { crop, setCrop, setSidebarStep, location } = useIrriGridStore();
  const [apiCrops, setApiCrops] = useState<any[]>([]);
  const [loadingCrops, setLoadingCrops] = useState(true);
  const [districtsData, setDistrictsData] = useState<any>(null);

  useEffect(() => {
    fetchCrops()
      .then(setApiCrops)
      .catch(() => {})
      .finally(() => setLoadingCrops(false));
    
    fetch("/data/rwanda_districts_data.json")
      .then(r => r.json())
      .then(setDistrictsData)
      .catch(() => {});
  }, []);

  const cropNames = apiCrops.length > 0 ? apiCrops.map((c) => c.name) : FALLBACK_CROPS;

  function handleSelect(name: string) {
    const found = apiCrops.find((c) => c.name === name);
    if (found) {
      setCrop({
        name: found.name,
        kc_init: found.kc_init,
        kc_mid: found.kc_mid,
        kc_end: found.kc_end,
        root_depth_m: found.root_depth_m,
        depletion_fraction: found.depletion_fraction,
        stages: found.stages,
      });
    } else {
      setCrop({ name });
    }
  }

  const reco = useMemo(() => {
    if (!crop.name || !districtsData) {
      return {
        zones: "All provinces of Rwanda",
        soil: "Loam, Sandy Loam",
        rainfall: "800–1400 mm/yr",
        note: "Select a crop above to see tailored recommendations for Rwanda."
      };
    }

    // A simple deterministic recommendation generator
    const kcMax = Math.max(crop.kc_init || 0.5, crop.kc_mid || 1.0, crop.kc_end || 0.5);
    let targetRain = "";
    let targetZone = "";
    let note = "";
    
    if (kcMax > 1.1) {
      targetRain = "1000–1600 mm/yr";
      targetZone = "Northern & Western Provinces (High Rainfall)";
      note = "Requires consistent moisture. Supplemental irrigation highly recommended during dry spells.";
    } else if (kcMax > 0.8) {
      targetRain = "800–1200 mm/yr";
      targetZone = "Southern Province & Kigali City (Moderate)";
      note = "Moderate water requirements. Monitor soil moisture carefully during the mid-season.";
    } else {
      targetRain = "600–900 mm/yr";
      targetZone = "Eastern Province (Drought Tolerant)";
      note = "Drought-tolerant crop. Good for drier areas. Avoid over-watering.";
    }

    // Default basic soil
    let soil = "Loam, Sandy Loam";
    if (crop.root_depth_m && crop.root_depth_m < 0.5) {
        soil = "Sandy Loam, Sandy Clay (Well drained)";
    } else if (crop.root_depth_m && crop.root_depth_m > 1.0) {
        soil = "Deep Loam, Clay Loam";
    }

    // Custom overrides based on name for better flavor
    if (crop.name === "Tomato" || crop.name === "Potato") {
      soil = "Volcanic Loam";
    }

    // NISR SAS 2025 yield citation
    if (crop.name && location?.district) {
      const cleanDistrict = location.district.replace(/\s*district\s*$/i, "").trim().toLowerCase();
      const distMap = (nisrYieldData as any).district_yield_kg_ha || {};
      const matchedDistrictKey = Object.keys(distMap).find(
        (k) => k.toLowerCase() === cleanDistrict
      );

      if (matchedDistrictKey) {
        const districtEntry = distMap[matchedDistrictKey];
        const cropLower = crop.name.trim().toLowerCase();
        let yieldKgHa: number | null = null;
        let citedCropName: string | null = null;

        if (cropLower === "maize") {
          yieldKgHa = districtEntry["Maize"] ?? null;
          citedCropName = "Maize";
        } else if (cropLower === "beans") {
          yieldKgHa = districtEntry["Beans"] ?? null;
          citedCropName = "Beans";
        } else if (cropLower === "irish potato" || cropLower === "potato") {
          yieldKgHa = districtEntry["Irish Potato"] ?? null;
          citedCropName = crop.name.trim() === "Potato" ? "Potato" : "Irish Potato";
        } else if (cropLower === "banana") {
          citedCropName = "Banana";
          const cooking = districtEntry["Cooking Banana"];
          const dessert = districtEntry["Dessert Banana"];
          const beer = districtEntry["Banana for Beer"];
          const vals = [cooking, dessert, beer].filter((v): v is number => typeof v === "number");
          if (vals.length > 0) {
            yieldKgHa = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
          }
        }

        if (yieldKgHa !== null && citedCropName !== null) {
          const sentence = `In ${matchedDistrictKey}, NISR's 2025 Seasonal Agricultural Survey reports average yields of ${yieldKgHa} kg/ha for ${citedCropName}.`;
          note = note ? `${note} ${sentence}` : sentence;
        }
      }
    }

    return { zones: targetZone, soil, rainfall: targetRain, note };
  }, [crop, districtsData, location]);

  const totalDays = crop.stages
    ? crop.stages.initial + crop.stages.development + crop.stages.mid + crop.stages.late
    : 145;

  return (
    <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 20, maxWidth: 780 }}>
      {/* Header */}
      <div>
        <h2 style={{ color: "var(--text-bright)", fontSize: 20, fontWeight: "bold", margin: 0, letterSpacing: 0.5, display: "flex", alignItems: "center", gap: 10 }}>
          <Sprout size={18} color="var(--accent)" /> Start Project
        </h2>
        <p style={{ color: "var(--text-dim)", fontSize: 12, margin: "6px 0 0" }}>
          Select your crop below to receive an agronomic recommendation, then move to Location to find your field.
        </p>
      </div>

      {/* Workflow Guide */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 18px", display: "flex", gap: 0 }}>
        {[
          { num: "1", icon: <Sprout size={15} color="var(--primary)" />, label: "Select Crop", desc: "Choose Below" },
          { num: "2", icon: <MapPin size={15} color="var(--primary)" />, label: "Set Location", desc: "Tab 02 - GPS or search" },
          { num: "3", icon: <Ruler size={15} color="var(--primary)" />, label: "Trace Field", desc: "Draw boundary on satellite map" },
          { num: "4", icon: <Zap size={15} color="var(--primary)" />, label: "Auto Design", desc: "All calculations run automatically" },
        ].map((s, i) => (
          <div key={s.num} style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4, paddingRight: i < 3 ? 16 : 0, borderRight: i < 3 ? "1px solid var(--border-subtle)" : "none", marginRight: i < 3 ? 16 : 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{
                background: "var(--primary)",
                color: "#ffffff",
                borderRadius: "50%",
                width: 18,
                height: 18,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 10,
                fontWeight: "bold",
                flexShrink: 0,
              }}>{s.num}</span>
              <span style={{ fontSize: 12, color: "var(--text-bright)", fontWeight: "bold", display: "flex", alignItems: "center", gap: 4 }}>{s.icon} {s.label}</span>
            </div>
            <p style={{ margin: 0, fontSize: 10, color: "var(--text-dim)", paddingLeft: 24 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Crop Picker */}
      <div className="hud-box">
        <div className="hud-box-title" style={{ fontSize: 13, marginBottom: 12, display: "flex", alignItems: "center", gap: 6, color: "var(--primary)" }}>
          <Sprout size={14} color="var(--primary)" /> Crop Selection
        </div>

        {loadingCrops ? (
          <div style={{ color: "var(--text-dim)", fontSize: 12, fontStyle: "italic" }}>Loading crop database…</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {cropNames.map((name) => (
                <button
                  key={name}
                  onClick={() => handleSelect(name)}
                  style={{
                    padding: "7px 15px",
                    borderRadius: 4,
                    border: crop.name === name ? "2px solid var(--primary)" : "1px solid var(--border)",
                    background: crop.name === name ? "var(--primary-12)" : "var(--bg-input)",
                    color: crop.name === name ? "var(--primary)" : "var(--text)",
                    fontSize: 12,
                    fontWeight: crop.name === name ? "bold" : "normal",
                    cursor: "pointer",
                    transition: "all 0.12s",
                  }}
                >
                  {name}
                </button>
              ))}
            </div>

            {crop.name && (
              <div style={{ display: "flex", gap: 20, padding: "8px 12px", background: "var(--bg-subtle)", border: "1px solid var(--border)", borderRadius: 4, fontSize: 11, flexWrap: "wrap", fontFamily: "var(--font-mono)" }}>
                <span><span style={{ color: "var(--text-dim)" }}>Kc: </span><span style={{ color: "var(--primary)" }}>{crop.kc_init?.toFixed(2)} / {crop.kc_mid?.toFixed(2)} / {crop.kc_end?.toFixed(2)}</span></span>
                <span><span style={{ color: "var(--text-dim)" }}>Root: </span><span style={{ color: "var(--text)" }}>{crop.root_depth_m} m</span></span>
                <span><span style={{ color: "var(--text-dim)" }}>Season: </span><span style={{ color: "var(--text)" }}>{totalDays} days</span></span>
                <span><span style={{ color: "var(--text-dim)" }}>RAW: </span><span style={{ color: "var(--text)" }}>{(crop.depletion_fraction * 100).toFixed(0)}% FC</span></span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* AI Recommendation */}
      <div className="hud-box ai-reco-box" style={{ background: "var(--bg-subtle)" }}>
        <div className="hud-box-title" style={{ color: "var(--primary)", fontSize: 13, marginBottom: 14 }}>
          <Lightbulb size={14} color="var(--primary)" /> AI Agronomic Recommendation — {crop.name || "Select a crop above"}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 12, lineHeight: 1.6 }}>
          <div style={{ display: "flex", gap: 12 }}>
            <Map size={16} color="var(--primary)" />
            <div><strong style={{ color: "var(--primary)", fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>Where it grows well in Rwanda</strong><div style={{ color: "var(--text)", marginTop: 2 }}>{reco.zones}</div></div>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <Mountain size={16} color="var(--primary)" />
            <div><strong style={{ color: "var(--primary)", fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>Ideal soil</strong><div style={{ color: "var(--text)", marginTop: 2 }}>{reco.soil}</div></div>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <CloudRain size={16} color="var(--primary)" />
            <div><strong style={{ color: "var(--primary)", fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>Rainfall range</strong><div style={{ color: "var(--text)", marginTop: 2 }}>{reco.rainfall}</div></div>
          </div>
          <div className="ai-reco-note" style={{ padding: "8px 12px", background: "#e4effb", borderLeft: "3px solid var(--primary)", borderRadius: "0 4px 4px 0", color: "#436384", fontStyle: "italic" }}>
            {reco.note}
          </div>
        </div>
      </div>

      {/* Next Step CTA */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 18px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6 }}>
        <div style={{ flex: 1 }}>
          <div style={{ color: "var(--text-bright)", fontSize: 13, fontWeight: "bold" }}>Ready? Go to Location →</div>
          <div style={{ color: "var(--text-dim)", fontSize: 11, marginTop: 2 }}>Select Location (Tab 02) to automatically fetch climate and soil data.</div>
        </div>
        <button
          className="hud-btn primary"
          onClick={() => setSidebarStep(2)}
          style={{ padding: "8px 20px", fontSize: 12, fontWeight: "bold", background: "var(--primary)", color: "#ffffff", borderColor: "var(--primary)", whiteSpace: "nowrap", flexShrink: 0, borderRadius: 6 }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <MapPin size={14} /> Go to Location
          </span>
        </button>
      </div>
    </div>
  );
}
