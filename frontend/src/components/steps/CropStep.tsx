"use client";

import React, { useEffect, useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { fetchCrops, fetchNDVI } from "@/lib/api";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { Sprout, Calendar, Activity, Check } from "lucide-react";

export default function CropStep() {
  const { crop, setCrop, location } = useIrriGridStore();
  const [cropList, setCropList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [ndviData, setNdviData] = useState<{ ndvi: number; status: string } | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [cropsRes, ndviRes] = await Promise.allSettled([
          fetchCrops(),
          fetchNDVI(location.lat, location.lon),
        ]);

        if (cropsRes.status === "fulfilled") {
          setCropList(cropsRes.value);
        }
        if (ndviRes.status === "fulfilled") {
          setNdviData(ndviRes.value);
          if (ndviRes.value.ndvi) {
            setCrop({ ndvi: ndviRes.value.ndvi, ndvi_status: ndviRes.value.status });
          }
        }
      } catch (err) {
        console.error("Crops load fallback:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [location.lat, location.lon]);

  const handleSelectCrop = (c: any) => {
    const totalDays = (c.stages?.initial || 30) + (c.stages?.development || 40) + (c.stages?.mid || 45) + (c.stages?.late || 30);
    const startDate = new Date(crop.planting_date || "2026-09-15");
    const endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + totalDays);

    setCrop({
      name: c.name,
      category: c.category || "Horticulture",
      kc_init: c.kc_init ?? 0.6,
      kc_mid: c.kc_mid ?? 1.15,
      kc_end: c.kc_end ?? 0.8,
      root_depth_m: c.root_depth_m ?? 0.6,
      depletion_fraction: c.depletion_fraction ?? 0.4,
      stages: c.stages || { initial: 30, development: 40, mid: 45, late: 30 },
      harvest_date: endDate.toISOString().split("T")[0],
    });
  };

  const handlePlantingDateChange = (dateStr: string) => {
    const totalDays = (crop.stages.initial || 30) + (crop.stages.development || 40) + (crop.stages.mid || 45) + (crop.stages.late || 30);
    const startDate = new Date(dateStr);
    const endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + totalDays);

    setCrop({
      planting_date: dateStr,
      harvest_date: endDate.toISOString().split("T")[0],
    });
  };

  const totalSeasonDays = (crop.stages.initial || 0) + (crop.stages.development || 0) + (crop.stages.mid || 0) + (crop.stages.late || 0);

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <Sprout size={18} />
            Step 04: Crop Selection & FAO Growth Stages
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="badge-tag">
              NDVI: {crop.ndvi ?? 0.68} ({crop.ndvi_status || "Vigorous"})
            </span>
          </div>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-dim)", marginBottom: "1rem" }}>
          Select the target crop. FAO-56 crop coefficients (Kc) dynamically determine evapotranspiration throughout each phenological stage.
        </p>

        {/* Selected Crop Summary */}
        <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Selected Crop"
            value={crop.name}
            subtext={`${totalSeasonDays} Days Cycle`}
            color="var(--primary)"
          />
          <StatCard
            label="Peak Kc Mid"
            value={crop.kc_mid}
            subtext={`Init: ${crop.kc_init} | End: ${crop.kc_end}`}
            color="var(--accent)"
          />
          <StatCard
            label="Root Depth"
            value={crop.root_depth_m}
            unit="m"
            subtext="Effective root zone"
          />
          <StatCard
            label="Depletion Fraction (p)"
            value={crop.depletion_fraction}
            subtext="Allowable RAW depletion"
          />
        </div>

        {/* Crop Selection Grid */}
        <div style={{ marginBottom: "1.25rem" }}>
          <div className="form-label" style={{ marginBottom: "0.5rem" }}>Available Crops (Rwanda Agro-ecological Catalog)</div>
          <div className="grid-3">
            {(cropList.length > 0
              ? cropList
              : [
                  { name: "Tomato", kc_init: 0.6, kc_mid: 1.15, kc_end: 0.8, root_depth_m: 0.6, stages: { initial: 30, development: 40, mid: 45, late: 30 } },
                  { name: "Potato (Irish)", kc_init: 0.5, kc_mid: 1.15, kc_end: 0.75, root_depth_m: 0.5, stages: { initial: 25, development: 30, mid: 45, late: 25 } },
                  { name: "Maize", kc_init: 0.3, kc_mid: 1.2, kc_end: 0.5, root_depth_m: 1.0, stages: { initial: 25, development: 35, mid: 40, late: 30 } },
                  { name: "French Beans", kc_init: 0.5, kc_mid: 1.05, kc_end: 0.9, root_depth_m: 0.5, stages: { initial: 20, development: 25, mid: 30, late: 15 } },
                  { name: "Onion", kc_init: 0.7, kc_mid: 1.05, kc_end: 0.75, root_depth_m: 0.4, stages: { initial: 20, development: 35, mid: 45, late: 20 } },
                  { name: "Cabbage", kc_init: 0.7, kc_mid: 1.05, kc_end: 0.95, root_depth_m: 0.5, stages: { initial: 25, development: 30, mid: 40, late: 20 } },
                ]
            ).map((c) => {
              const isSelected = crop.name.toLowerCase() === c.name.toLowerCase();
              return (
                <div
                  key={c.name}
                  onClick={() => handleSelectCrop(c)}
                  className={`selection-card ${isSelected ? "selected" : ""}`}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div className="selection-card-title">{c.name}</div>
                    {isSelected && <Check size={18} style={{ color: "var(--primary)" }} />}
                  </div>
                  <div className="selection-card-desc">
                    Kc: {c.kc_init} → {c.kc_mid} → {c.kc_end} • Root: {c.root_depth_m || 0.6}m
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                    Cycle: {(c.stages?.initial || 25) + (c.stages?.development || 35) + (c.stages?.mid || 40) + (c.stages?.late || 25)} days
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Growth Stages & Planting Date */}
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Planting Date</label>
            <input
              type="date"
              className="form-input"
              value={crop.planting_date}
              onChange={(e) => handlePlantingDateChange(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Estimated Harvest Date</label>
            <input
              type="date"
              className="form-input"
              value={crop.harvest_date}
              readOnly
              style={{ opacity: 0.8 }}
            />
          </div>
        </div>
      </div>

      <StepNav />
    </div>
  );
}
