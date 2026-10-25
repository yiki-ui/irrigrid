"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useIrriGridStore } from "@/lib/store";
import { fetchDistricts } from "@/lib/api";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { MapPin, Mountain, TrendingUp, Maximize2 } from "lucide-react";

// Dynamic import with ssr: false for Leaflet
const FieldMap = dynamic(() => import("@/components/map/FieldMap"), {
  ssr: false,
  loading: () => (
    <div style={{ height: 460, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(5,5,16,0.8)", border: "1px solid var(--border)", color: "var(--text-dim)" }}>
      Loading satellite imagery & GIS engine...
    </div>
  ),
});

export default function LocationStep() {
  const { location, setLocation } = useIrriGridStore();
  const [districts, setDistricts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    async function loadDistricts() {
      try {
        setLoading(true);
        const data = await fetchDistricts();
        setDistricts(data);
      } catch (err) {
        console.error("Districts load fallback:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDistricts();
  }, []);

  const handleDistrictChange = (districtName: string) => {
    const selected = districts.find((d) => d.name === districtName);
    if (selected) {
      setLocation({
        district: selected.name,
        province: selected.province || location.province,
        elevation_m: selected.elevation_m || location.elevation_m,
        slope_pct: selected.slope_pct || location.slope_pct,
      });
    } else {
      setLocation({ district: districtName });
    }
  };

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <MapPin size={18} />
            Step 01: Field Boundary & Location (Rwanda)
          </div>
          <span className="badge-tag">GIS Polygon Engine</span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-dim)", marginBottom: "1rem" }}>
          Click on the satellite map to trace your field boundaries. IrriGrid will compute the field area in hectares and extract elevation and slope profiles.
        </p>

        <div style={{ marginBottom: "1.25rem" }}>
          {mounted ? (
            <FieldMap />
          ) : (
            <div style={{ height: 460, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(5,5,16,0.8)", border: "1px solid var(--border)", color: "var(--text-dim)" }}>
              Loading satellite imagery & GIS engine...
            </div>
          )}
        </div>

        <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Field Area"
            value={location.area_ha}
            unit="ha"
            subtext={`${Math.round(location.area_ha * 10000)} m²`}
            color="var(--primary)"
          />
          <StatCard
            label="District"
            value={location.district}
            subtext={location.province}
            color="var(--accent)"
          />
          <StatCard
            label="Elevation"
            value={location.elevation_m}
            unit="m"
            subtext="SRTM 30m DEM"
          />
          <StatCard
            label="Field Slope"
            value={location.slope_pct}
            unit="%"
            subtext="Terrain gradient"
          />
        </div>

        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Select Administrative District</label>
            <select
              className="form-select"
              value={location.district}
              onChange={(e) => handleDistrictChange(e.target.value)}
            >
              {districts.length > 0 ? (
                districts.map((d) => (
                  <option key={d.name} value={d.name}>
                    {d.name} ({d.province}) — {d.elevation_m || 1500}m
                  </option>
                ))
              ) : (
                <>
                  <option value="Musanze">Musanze (Northern)</option>
                  <option value="Nyabihu">Nyabihu (Western)</option>
                  <option value="Bugesera">Bugesera (Eastern)</option>
                  <option value="Huye">Huye (Southern)</option>
                  <option value="Gasabo">Gasabo (Kigali)</option>
                </>
              )}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Manual Area Override (Hectares)</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="50"
              className="form-input"
              value={location.area_ha}
              onChange={(e) => setLocation({ area_ha: parseFloat(e.target.value) || 0.1 })}
            />
          </div>
        </div>

        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Field Slope (%)</label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="45"
              className="form-input"
              value={location.slope_pct}
              onChange={(e) => setLocation({ slope_pct: parseFloat(e.target.value) || 0 })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Elevation (m a.s.l.)</label>
            <input
              type="number"
              step="10"
              className="form-input"
              value={location.elevation_m}
              onChange={(e) => setLocation({ elevation_m: parseFloat(e.target.value) || 1500 })}
            />
          </div>
        </div>
      </div>

      <StepNav />
    </div>
  );
}
