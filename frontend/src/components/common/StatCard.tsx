import React from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  color?: string;
}

export default function StatCard({ label, value, unit, subtext, color }: StatCardProps) {
  return (
    <div className="stat-box">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={color ? { color } : undefined}>
        {value}
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
      {subtext && (
        <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: "0.25rem" }}>
          {subtext}
        </div>
      )}
    </div>
  );
}
