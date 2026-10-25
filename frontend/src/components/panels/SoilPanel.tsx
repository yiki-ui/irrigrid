"use client";
import React, { useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { Check, Mountain, Plus, RefreshCw } from "lucide-react";

const SOIL_PRESETS = [
  { name: "Volcanic Loam",   texture: "Volcanic Loam",   fc: 0.34, wp: 0.16, tam: 180, inf: 600, root: 200 },
  { name: "Clay Loam",       texture: "Clay Loam",       fc: 0.35, wp: 0.18, tam: 170, inf: 192, root: 170 },
  { name: "Loam",            texture: "Loam",            fc: 0.30, wp: 0.13, tam: 170, inf: 312, root: 180 },
  { name: "Sandy Clay Loam", texture: "Sandy Clay Loam", fc: 0.28, wp: 0.15, tam: 130, inf: 360, root: 160 },
  { name: "Sandy Loam",      texture: "Sandy Loam",      fc: 0.22, wp: 0.10, tam: 120, inf: 600, root: 200 },
  { name: "Silty Loam",      texture: "Silty Loam",      fc: 0.33, wp: 0.13, tam: 200, inf: 240, root: 180 },
  { name: "Silty Clay Loam", texture: "Silty Clay Loam", fc: 0.35, wp: 0.17, tam: 180, inf: 190, root: 170 },
  { name: "Sandy Clay",      texture: "Sandy Clay",      fc: 0.32, wp: 0.18, tam: 140, inf: 120, root: 150 },
  { name: "Clay",            texture: "Clay",            fc: 0.40, wp: 0.25, tam: 150, inf: 48,  root: 150 },
  { name: "Sand",            texture: "Sand",            fc: 0.12, wp: 0.05, tam: 70,  inf: 1200, root: 150 },
  { name: "Silty Clay",      texture: "Silty Clay",      fc: 0.38, wp: 0.22, tam: 160, inf: 120, root: 160 },
];

export default function SoilPanel() {
  const { soil, setSoil } = useIrriGridStore();
  const [manualInput, setManualInput] = useState(false);
  const [depletion, setDepletion] = useState(50);

  const selected = SOIL_PRESETS.find(s => s.name === soil.name) || SOIL_PRESETS[0];
  const availMoisture = (selected.tam * (1 - depletion / 100)).toFixed(1);

  function handlePresetChange(name: string) {
    const p = SOIL_PRESETS.find(s => s.name === name);
    if (p) {
      setSoil({
        name: p.name,
        texture: p.texture,
        field_capacity: p.fc * 100,
        wilting_point: p.wp * 100,
        available_water_mm_m: p.tam,
        max_infiltration_rate: p.inf / 24, // mm/h
        source: "Manual Selection"
      });
    }
  }

  return (
    <div style={{ padding: 4 }}>
      <h2 style={{ color: "var(--primary)", fontSize: 18, margin: "0 0 16px", display: "flex", alignItems: "center", gap: 8 }}>
        <Mountain size={18} color="var(--primary)" /> Soil Properties &amp; Water Holding Capacity
      </h2>

      {/* Soil Type Selection */}
      <div className="hud-box" style={{ marginBottom: 16 }}>
        <div className="hud-box-title">Soil Type &amp; Detection</div>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
          <div style={{ flex: 1 }}>
            <label className="hud-label">Soil Type</label>
            <select className="hud-select" value={soil.name} onChange={e => handlePresetChange(e.target.value)}>
              {SOIL_PRESETS.map(s => <option key={s.name}>{s.name}</option>)}
            </select>
          </div>
          <button
            className="hud-btn"
            onClick={() => setManualInput(m => !m)}
            style={{ whiteSpace: "nowrap" }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
              {manualInput ? <Check size={12} color="var(--success)" /> : <Plus size={12} />}
              {manualInput ? " Manual Mode" : " Enable Manual Input"}
            </span>
          </button>
        </div>
        {soil.source && (
          <div style={{ fontSize: 11, color: "var(--accent)", marginTop: 8 }}>
            Data Source: <strong>{soil.source}</strong>
            {soil.sand_pct != null ? (
              <span style={{ color: "var(--text-dim)", marginLeft: 8 }}>
                (Sand: {soil.sand_pct}% · Silt: {soil.silt_pct}% · Clay: {soil.clay_pct}%)
              </span>
            ) : (
              <span style={{ color: "var(--text-dim)", marginLeft: 8 }}>
                (Grain composition: Not measured)
              </span>
            )}
          </div>
        )}
      </div>

      {/* Soil Water Properties */}
      <div className="hud-box" style={{ marginBottom: 16 }}>
        <div className="hud-box-title">Soil Water Properties</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 20px" }}>
          <div>
            <label className="hud-label">Field Capacity (FC)</label>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input type="number" className="hud-input" value={selected.fc.toFixed(3)} step={0.001} readOnly={!manualInput} />
              <span style={{ color: "var(--text-dim)", fontSize: 10 }}>m³/m³</span>
            </div>
          </div>
          <div>
            <label className="hud-label">Wilting Point (WP)</label>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input type="number" className="hud-input" value={selected.wp.toFixed(3)} step={0.001} readOnly={!manualInput} />
              <span style={{ color: "var(--text-dim)", fontSize: 10 }}>m³/m³</span>
            </div>
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <label className="hud-label">Total Available Moisture (TAM)</label>
            <input
              type="number"
              className="hud-input"
              value={selected.tam}
              readOnly={!manualInput}
              style={{ background: selected.tam > 150 ? "rgba(0,255,200,0.12)" : undefined, color: "var(--accent)", fontWeight: 600 }}
            />
            <span style={{ color: "var(--text-dim)", fontSize: 10, marginLeft: 6 }}>mm/meter (FC - WP)</span>
          </div>
          <div>
            <label className="hud-label">Max Infiltration Rate</label>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input type="number" className="hud-input" value={selected.inf} readOnly={!manualInput} />
              <span style={{ color: "var(--text-dim)", fontSize: 10 }}>mm/day</span>
            </div>
          </div>
          <div>
            <label className="hud-label">Max Rooting Depth</label>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input type="number" className="hud-input" value={selected.root} readOnly={!manualInput} />
              <span style={{ color: "var(--text-dim)", fontSize: 10 }}>cm</span>
            </div>
          </div>
        </div>
      </div>

      {/* Initial Soil Moisture Conditions */}
      <div className="hud-box" style={{ marginBottom: 16 }}>
        <div className="hud-box-title">Initial Soil Moisture Conditions</div>
        <div className="hud-row">
          <span>Initial Soil Moisture Depletion</span>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="number"
              className="hud-input"
              style={{ width: 60 }}
              value={depletion}
              onChange={e => setDepletion(parseFloat(e.target.value) || 0)}
            />
            <span style={{ color: "var(--text-dim)", fontSize: 11 }}>% TAM</span>
          </div>
        </div>
        <div className="hud-row">
          <span>Initial Available Soil Moisture</span>
          <span style={{ color: "var(--primary)" }}>{availMoisture} <span style={{ color: "var(--text-dim)", fontSize: 10 }}>mm/meter</span></span>
        </div>
        <div style={{ marginTop: 10 }}>
          <button className="hud-btn full"><RefreshCw size={12} /> Update Initial Moisture</button>
        </div>
      </div>

      {/* Available Soil Types Table */}
      <div style={{ fontWeight: 600, color: "var(--text-dim)", fontSize: 11, marginBottom: 8, letterSpacing: 1 }}>Available Soil Types:</div>
      <div style={{ overflowX: "auto" }}>
        <table className="hud-table" style={{ width: "100%" }}>
          <thead>
            <tr>
              <th>#</th>
              <th>Soil Type</th>
              <th>Texture</th>
              <th>FC</th>
              <th>WP</th>
              <th>TAM (mm)</th>
              <th>Infilt. (mm)</th>
              <th>Root Depth</th>
            </tr>
          </thead>
          <tbody>
            {SOIL_PRESETS.map((s, i) => (
              <tr
                key={s.name}
                onClick={() => handlePresetChange(s.name)}
                style={{ cursor: "pointer", background: soil.name === s.name ? "rgba(0,229,255,0.08)" : undefined }}
              >
                <td className="row-num">{i + 1}</td>
                <td style={{ color: soil.name === s.name ? "var(--primary)" : undefined }}>{s.name}</td>
                <td>{s.texture}</td>
                <td>{s.fc.toFixed(2)}</td>
                <td>{s.wp.toFixed(2)}</td>
                <td style={{ color: "var(--accent)" }}>{s.tam}</td>
                <td>{s.inf}</td>
                <td>{s.root}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
