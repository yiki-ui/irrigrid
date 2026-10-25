"use client";
import React, { useEffect } from "react";
import { useIrriGridStore } from "@/lib/store";
import { Database, Cpu, Globe, Zap, Droplet, CloudRain } from "lucide-react";

export default function BottomBar() {
  const {
    design,
    monthlyClimate,
    monthlyRainfall,
    crop,
    location,
    health,
    runHealthChecks,
    cropExpectedYield,
    fetchCropYield,
  } = useIrriGridStore();

  const eu = design?.recommended_design?.emission_uniformity_percent;

  // Average ETo from monthlyClimate
  const avgETo =
    monthlyClimate.length > 0
      ? monthlyClimate.reduce((sum, m) => sum + (m.eto ?? 0), 0) / monthlyClimate.length
      : null;

  // Annual rainfall from monthlyRainfall
  const annualRain =
    monthlyRainfall.length > 0
      ? monthlyRainfall.reduce((sum, m) => sum + (m.rainfall_mm ?? 0), 0)
      : null;

  // Run health checks on mount and every 30s
  useEffect(() => {
    runHealthChecks();
    const interval = setInterval(runHealthChecks, 30_000);
    return () => clearInterval(interval);
  }, [runHealthChecks]);

  // Fetch crop yield when crop or district changes
  useEffect(() => {
    if (crop.name) {
      fetchCropYield(crop.name, location.district);
    }
  }, [crop.name, location.district, fetchCropYield]);

  const HealthDot = ({ status, label }: { status: "unknown" | "healthy" | "unhealthy"; label: string }) => {
    const colors = {
      healthy: "var(--success)",
      unhealthy: "var(--danger)",
      unknown: "#94a3b8",
    };
    return (
      <span style={{ display: "inline-flex", alignItems: "center", gap: 5, color: "var(--text)", fontWeight: 500, fontSize: 11 }}>
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: colors[status],
          }}
        />
        {label}
      </span>
    );
  };

  return (
    <div className="bottom-bar">
      <div className="bottom-stats">
        <div className="bottom-stat eff">
          <Zap size={12} color="var(--accent)" />
          <span>System Efficiency:</span>
          <span style={{ fontWeight: 600 }}>{eu != null ? `${eu.toFixed(1)}%` : "—"}</span>
        </div>
        <div className="bottom-stat">
          <Zap size={12} color="var(--accent)" />
          <span>Performance:</span>
          <span style={{ fontWeight: 600 }}>{cropExpectedYield != null ? `${cropExpectedYield.toFixed(1)} tons/ha` : "—"}</span>
        </div>
        <div className="bottom-stat">
          <Droplet size={12} color="var(--accent)" />
          <span>ETo:</span>
          <span style={{ fontWeight: 600 }}>{avgETo != null ? `${avgETo.toFixed(1)} mm/day` : "—"}</span>
        </div>
        <div className="bottom-stat">
          <CloudRain size={12} color="var(--accent)" />
          <span>Rain:</span>
          <span style={{ fontWeight: 600 }}>{annualRain != null ? `${Math.round(annualRain)} mm/yr` : "—"}</span>
        </div>
      </div>
      <div className="bottom-stats" style={{ gap: 14 }}>
        <HealthDot status={health.db} label="DB" />
        <HealthDot status={health.ai} label="AI" />
        <HealthDot status={health.gis} label="GIS" />
      </div>
    </div>
  );
}