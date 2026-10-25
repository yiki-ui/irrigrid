"use client";
import React, { useState } from "react";
import { AlertCircle, AlertTriangle, CloudSun, Satellite, Calculator, Download, RefreshCw, CheckCircle } from "lucide-react";
import { useIrriGridStore } from "@/lib/store";
import { fetchNASAClimatology } from "@/lib/api";
import { estimateFAO56ETo } from "@/lib/calculations";

export default function ClimatePanel() {
  const { location, monthlyClimate, updateClimateMonth, setMonthlyClimate, setMonthlyRainfall } = useIrriGridStore();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [statusType, setStatusType] = useState<"success" | "error" | "info">("info");
  const [country, setCountry] = useState("Rwanda");
  const [station, setStation] = useState(location.district || "Musanze");

  async function fetchNASA() {
    setLoading(true);
    setStatus("Connecting to NASA POWER API (30-year agroclimatology)...");
    setStatusType("info");
    try {
      const data = await fetchNASAClimatology(location.lat, location.lon, location.elevation_m);
      if (data?.monthly_climate && data.monthly_climate.length === 12) {
        setMonthlyClimate(data.monthly_climate);
        if (data.monthly_rainfall && data.monthly_rainfall.length === 12) {
          setMonthlyRainfall(data.monthly_rainfall);
        }
        const src = data.source === "nasa_power_live" ? "Live NASA POWER Satellite Agrometeorology" : "Cached 30-Year Climatology";
        setStatus(`${src} synchronized (${location.lat.toFixed(3)}°, ${location.lon.toFixed(3)}°)`);
        setStatusType("success");
      } else {
        throw new Error("Invalid payload structure");
      }
    } catch (err: any) {
      console.warn("NASA fetch error:", err);
      // Recalculate ETo using local FAO-56 PM
      const updated = monthlyClimate.map((m, idx) => {
        const eto = estimateFAO56ETo(m.tmin, m.tmax, m.rhmin, m.rhmax, m.wind_speed, m.sunshine_hours, location.lat, location.elevation_m || 1500, (idx + 1) * 30);
        return { ...m, eto };
      });
      setMonthlyClimate(updated);
      setStatus("NASA live server unavailable - calculated via FAO-56 Penman-Monteith baseline");
      setStatusType("error");
    } finally {
      setLoading(false);
    }
  }

  function handleRecalculateAllETo() {
    const updated = monthlyClimate.map((m, idx) => {
      const dayOfYear = Math.round(((idx + 0.5) / 12) * 365);
      const eto = estimateFAO56ETo(m.tmin, m.tmax, m.rhmin, m.rhmax, m.wind_speed, m.sunshine_hours, location.lat, location.elevation_m || 1500, dayOfYear);
      return { ...m, eto: +eto.toFixed(2) };
    });
    setMonthlyClimate(updated);
    setStatus("Recalculated all 12 monthly ETo values using FAO-56 Penman-Monteith");
    setStatusType("success");
  }

  return (
    <div style={{ padding: 4 }}>
      {/* Header */}
      <h2 style={{ color: "var(--primary)", fontSize: 18, margin: "0 0 16px", display: "flex", alignItems: "center", gap: 8 }}>
        <CloudSun size={20} color="var(--primary)" /> Climate / ETo - Monthly Data
      </h2>

      {/* Location Station Section */}
      <div className="hud-box" style={{ marginBottom: 16 }}>
        <div className="hud-box-title">Location Station &amp; Sensor Origin</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 20px" }}>
          <div>
            <label className="hud-label">Country</label>
            <select className="hud-select" value={country} onChange={e => setCountry(e.target.value)}>
              <option>Rwanda</option><option>Kenya</option><option>Uganda</option><option>Tanzania</option>
            </select>
          </div>
          <div>
            <label className="hud-label">District / Station</label>
            <select className="hud-select" value={station} onChange={e => setStation(e.target.value)}>
              <option value={location.district || "Musanze"}>{location.district || "Musanze"} (Active)</option>
              <option>Kigali</option><option>Musanze</option><option>Huye</option><option>Rubavu</option><option>Nyagatare</option>
            </select>
          </div>
          <div>
            <label className="hud-label">Altitude (m)</label>
            <input type="number" className="hud-input" value={location.elevation_m} readOnly />
          </div>
          <div>
            <label className="hud-label">Latitude (°)</label>
            <input type="number" className="hud-input" value={location.lat.toFixed(4)} readOnly />
          </div>
          <div>
            <label className="hud-label">Longitude (°)</label>
            <input type="number" className="hud-input" value={location.lon.toFixed(4)} readOnly />
          </div>
        </div>
      </div>

      {/* Monthly Climate Table */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div style={{ fontWeight: 600, color: "var(--text-dim)", fontSize: 11, letterSpacing: 1 }}>
          Monthly Agrometeorological Climatology (NASA POWER / FAO-56):
        </div>
        <button
          className="hud-btn"
          onClick={fetchNASA}
          disabled={loading}
          style={{
            fontSize: 11,
            padding: "4px 12px",
            background: "rgba(0, 229, 255, 0.12)",
            color: "var(--primary)",
            borderColor: "var(--primary)",
            display: "flex",
            alignItems: "center",
            gap: 6
          }}
        >
          {loading ? <RefreshCw size={12} className="spin" /> : <Satellite size={12} />}
          {loading ? "Fetching NASA..." : "Fetch Data from NASA"}
        </button>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table className="hud-table" style={{ minWidth: 680 }}>
          <thead>
            <tr>
              <th style={{ width: 28 }}>#</th>
              <th>Month</th>
              <th>Min Temp (°C)</th>
              <th>Max Temp (°C)</th>
              <th>Humidity (%)</th>
              <th>Wind (km/day)</th>
              <th>Sun (hours)</th>
              <th>Rs (MJ/m²/da)</th>
              <th>ETo (mm/day)</th>
            </tr>
          </thead>
          <tbody>
            {monthlyClimate.map((m, i) => {
              const rs = (m.sunshine_hours * 1.8 + 5).toFixed(2);
              return (
                <tr key={m.month}>
                  <td className="row-num">{i + 1}</td>
                  <td>{["January","February","March","April","May","June","July","August","September","October","November","December"][i]}</td>
                  <td><input className="hud-input" style={{ width: 60 }} type="number" value={m.tmin} step={0.1} onChange={e => updateClimateMonth(i, { tmin: parseFloat(e.target.value) || 0 })} /></td>
                  <td><input className="hud-input" style={{ width: 60 }} type="number" value={m.tmax} step={0.1} onChange={e => updateClimateMonth(i, { tmax: parseFloat(e.target.value) || 0 })} /></td>
                  <td><input className="hud-input" style={{ width: 55 }} type="number" value={m.rhmax} step={1} onChange={e => updateClimateMonth(i, { rhmax: parseFloat(e.target.value) || 0 })} /></td>
                  <td><input className="hud-input" style={{ width: 65 }} type="number" value={(m.wind_speed * 86.4).toFixed(0)} step={1} onChange={e => updateClimateMonth(i, { wind_speed: (parseFloat(e.target.value) || 0) / 86.4 })} /></td>
                  <td><input className="hud-input" style={{ width: 55 }} type="number" value={m.sunshine_hours} step={0.1} onChange={e => updateClimateMonth(i, { sunshine_hours: parseFloat(e.target.value) || 0 })} /></td>
                  <td style={{ color: "var(--text-dim)" }}>{rs}</td>
                  <td style={{ color: "var(--accent)", fontWeight: 600 }}>{m.eto.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {status && (
        <div style={{
          color: statusType === "success" ? "var(--success)" : statusType === "error" ? "var(--danger)" : "var(--primary)",
          fontSize: 11,
          marginTop: 8,
          display: "flex",
          alignItems: "center",
          gap: 6
        }}>
          {statusType === "success" ? <CheckCircle size={13} /> : statusType === "error" ? <AlertCircle size={13} /> : <Satellite size={13} />}
          <span>{status}</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="action-row" style={{ marginTop: 16, display: "flex", gap: 10 }}>
        <button className="hud-btn primary" onClick={handleRecalculateAllETo} disabled={loading} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Calculator size={13} /> Calculate All ETo (FAO-56 PM)
        </button>
      </div>
    </div>
  );
}


