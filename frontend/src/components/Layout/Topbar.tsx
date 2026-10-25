"use client";
import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Search, MapPin, Satellite, CheckCircle, X,
  Loader2, CloudRain, Wind, Thermometer, Sun, Moon, Globe, Info,
} from "lucide-react";
import { useIrriGridStore } from "@/lib/store";
import { fetchNASAClimatology } from "@/lib/api";

const STEP_TITLES: Record<number, string> = {
  1: "Start Project",
  2: "Location Database & GIS",
  3: "Climate / ETo Monthly",
  4: "Rainfall & Effective Rain",
  5: "Crop Growth Stages & Kc",
  6: "Soil Water Capacity",
  7: "Water Requirements",
  8: "Irrigation Schedule",
  9: "Crop Pattern (Rwanda)",
  10: "Hydraulic System Design",
  11: "2D Engineering Layout",
  13: "Executive Results & PDF",
};

// ── Types ──────────────────────────────────────────────────────────────────────

interface NominatimResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type: string;
  class: string;
  address?: {
    district?: string;
    county?: string;
    state?: string;
    state_district?: string;
    country?: string;
    village?: string;
    town?: string;
    suburb?: string;
    city?: string;
    municipality?: string;
  };
}

interface PlaceResult {
  id: number;
  label: string;        // short human label
  sublabel: string;     // breadcrumb (sector / district / province)
  type: string;         // village, suburb, district, etc.
  lat: number;
  lon: number;
  elevation: number;    // estimated from lat (Rwanda highlands)
  district: string;
  province: string;
  sector?: string;
}

interface NasaClimateData {
  source: string;
  latitude: number;
  longitude: number;
  elevation: number;
  monthly_climate: Array<{
    month: string; tmin: number; tmax: number;
    rhmin: number; rhmax: number;
    wind_speed: number; sunshine_hours: number; eto: number;
  }>;
  monthly_rainfall: Array<{
    month: string; rainfall_mm: number; effective_rain_mm: number;
  }>;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

/** Rough elevation estimate from latitude for Rwanda (1300–2200 m). */
function estimateElevation(lat: number, lon: number): number {
  // Rwanda elevation roughly correlates with distance from Kigali and northwest highlands
  const distFromNW = Math.sqrt(Math.pow(lat + 1.5, 2) + Math.pow(lon - 29.5, 2));
  return Math.round(Math.max(1300, Math.min(2200, 1900 - distFromNW * 80)));
}

function buildPlaceResult(r: NominatimResult): PlaceResult {
  const addr = r.address || {};
  const rawDistrict = (
    addr.district ||
    addr.county ||
    (addr as any).city_district ||
    addr.city ||
    addr.state_district ||
    addr.municipality ||
    ""
  ).replace(/\s*district\s*$/i, "").trim();

  const province = addr.state || "";

  // Build a short label from the first part of display_name
  const parts = r.display_name.split(",").map(s => s.trim());
  const label = parts[0];
  const sublabel = parts.slice(1, 4).join(", ");

  const lat = parseFloat(r.lat);
  const lon = parseFloat(r.lon);

  return {
    id: r.place_id,
    label,
    sublabel,
    type: r.type || r.class,
    lat,
    lon,
    elevation: estimateElevation(lat, lon),
    district: rawDistrict || label,
    province,
    sector: label,
  };
}

const PLACE_TYPE_COLORS: Record<string, string> = {
  district: "#00e5ff",
  administrative: "#00e5ff",
  village: "#66bb6a",
  hamlet: "#66bb6a",
  suburb: "#a5d6a7",
  neighbourhood: "#a5d6a7",
  town: "#29b6f6",
  city: "#29b6f6",
  farm: "#ffca28",
  waterway: "#81d4fa",
  natural: "#80cbc4",
};

function typeColor(type: string): string {
  return PLACE_TYPE_COLORS[type] || "#90a4ae";
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function Topbar() {
  const { sidebarStep, location, setLocation, setMonthlyClimate, setMonthlyRainfall } =
    useIrriGridStore();
  const activeTitle = STEP_TITLES[sidebarStep] || "GIS & Site Assessment";

  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<PlaceResult[]>([]);
  const [noResults, setNoResults] = useState(false);

  const [fetching, setFetching] = useState(false);
  const [nasaData, setNasaData] = useState<NasaClimateData | null>(null);
  const [selected, setSelected] = useState<PlaceResult | null>(null);
  const [showModal, setShowModal] = useState(false);

  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const saved = (typeof window !== "undefined" ? localStorage.getItem("irrigrid_theme") : null) as "light" | "dark" | null;
    const initial = saved || "light";
    setTheme(initial);
    document.documentElement.setAttribute("data-theme", initial);
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("irrigrid_theme", next);
  };

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Nominatim geocode ──────────────────────────────────────────────────────
  const geocode = useCallback(async (q: string) => {
    if (q.trim().length < 2) { setResults([]); setNoResults(false); return; }
    setSearching(true);
    setNoResults(false);
    try {
      const url = new URL("https://nominatim.openstreetmap.org/search");
      url.searchParams.set("q", q + " Rwanda");
      url.searchParams.set("countrycodes", "rw");
      url.searchParams.set("format", "json");
      url.searchParams.set("limit", "8");
      url.searchParams.set("addressdetails", "1");
      url.searchParams.set("accept-language", "en");

      const resp = await fetch(url.toString(), {
        headers: { "User-Agent": "IrriGrid-Shamba/1.0 (irrigation planning app)" },
      });
      if (!resp.ok) throw new Error("Nominatim error");
      const data: NominatimResult[] = await resp.json();
      const places = data.map(buildPlaceResult);
      setResults(places);
      setNoResults(places.length === 0);
    } catch {
      setResults([]);
      setNoResults(true);
    } finally {
      setSearching(false);
    }
  }, []);

  // Debounce input → geocode
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length >= 2) {
      debounceRef.current = setTimeout(() => geocode(query), 420);
    } else {
      setResults([]);
      setNoResults(false);
    }
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, geocode]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current && !inputRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // ── Select a place → fetch NASA ────────────────────────────────────────────
  const selectPlace = useCallback(async (place: PlaceResult) => {
    setSelected(place);
    setOpen(false);
    setQuery(place.label);
    setResults([]);
    setFetching(true);
    try {
      const data: NasaClimateData = await fetchNASAClimatology(place.lat, place.lon, place.elevation);
      setNasaData(data);
      setShowModal(true);
    } catch (err) {
      console.error("NASA fetch failed:", err);
      alert("Could not fetch NASA POWER climate data. Check the backend is running.");
    } finally {
      setFetching(false);
    }
  }, []);

  // ── Apply NASA data to project ─────────────────────────────────────────────
  function applyData() {
    if (!nasaData || !selected) return;
    setMonthlyClimate(nasaData.monthly_climate.map(m => ({ ...m, isAuto: true })));
    setMonthlyRainfall(nasaData.monthly_rainfall.map(m => ({ ...m, isAuto: true })));
    setLocation({
      district: selected.district || selected.label,
      province: selected.province,
      sector: selected.sector || selected.label,
      lat: selected.lat,
      lon: selected.lon,
      elevation_m: selected.elevation,
    });
    setShowModal(false);
  }

  function dismissModal() {
    setShowModal(false);
    setNasaData(null);
  }

  const displayValue = location.district
    ? `${location.district}, ${location.province || "Rwanda"}`
    : "";

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      <div className="topbar">
        {/* Left: brand + active stage */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div className="topbar-brand" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span className="topbar-title" style={{ fontSize: 16, fontWeight: 800, letterSpacing: 0.5, color: "var(--text-bright)" }}>
              Irrigrid
            </span>
            <span style={{ fontSize: 11, color: "var(--text-dim)", padding: "2px 8px", background: "var(--bg-subtle)", borderRadius: 4, border: "1px solid var(--border-subtle)", whiteSpace: "nowrap" }}>
              Built for NISR Big Data Hackathon 2026 · Track 1: Agricultural Productivity
            </span>
          </div>
          <div className="active-stage-pill" style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 12px", background: "var(--bg-subtle)", border: "1px solid var(--border)", borderRadius: 4 }}>
            <span style={{ color: "var(--primary)", fontSize: 11, fontWeight: "bold", textTransform: "uppercase", letterSpacing: 0.8 }}>
              Active Stage:
            </span>
            <span style={{ color: "var(--primary)", fontSize: 11, fontWeight: 600 }}>
              {activeTitle}
            </span>
          </div>
        </div>

        {/* Right: search + location pill + theme toggle */}
        <div className="topbar-right" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ position: "relative" }}>
            {/* Input */}
            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
              {(searching || fetching) ? (
                <Loader2 size={13} style={{ position: "absolute", left: 10, color: "var(--primary)", pointerEvents: "none", animation: "spin 1s linear infinite" }} />
              ) : (
                <Search size={13} style={{ position: "absolute", left: 10, color: "var(--text-dim)", pointerEvents: "none" }} />
              )}
              <input
                ref={inputRef}
                className="topbar-search"
                type="text"
                placeholder="Search any place in Rwanda…"
                style={{ paddingLeft: 30, paddingRight: query ? 28 : 10, width: 270 }}
                value={open || query ? query : displayValue}
                onChange={e => { setQuery(e.target.value); setOpen(true); }}
                onFocus={() => { setQuery(""); setOpen(true); }}
              />
              {query && (
                <button
                  onClick={() => { setQuery(""); setResults([]); setOpen(false); }}
                  style={{ position: "absolute", right: 8, background: "none", border: "none", cursor: "pointer", color: "var(--text-dim)", padding: 0, display: "flex" }}
                >
                  <X size={12} />
                </button>
              )}
            </div>

            {/* Dropdown */}
            {open && (query.length >= 2) && (
              <div
                ref={dropdownRef}
                style={{
                  position: "absolute",
                  top: "calc(100% + 4px)",
                  right: 0,
                  width: 340,
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  boxShadow: "0 12px 36px rgba(0,0,0,0.2)",
                  zIndex: 9999,
                  overflow: "hidden",
                }}
              >
                <div style={{ padding: "6px 12px 4px", fontSize: 10, color: "var(--text-dim)", fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.8, borderBottom: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", gap: 6 }}>
                  <Globe size={10} style={{ color: "var(--primary)" }} />
                  OpenStreetMap · Rwanda
                </div>

                {searching && (
                  <div style={{ padding: "14px 12px", color: "var(--text-dim)", fontSize: 12, display: "flex", alignItems: "center", gap: 8 }}>
                    <Loader2 size={12} style={{ animation: "spin 1s linear infinite", color: "var(--primary)" }} />
                    Searching…
                  </div>
                )}

                {!searching && results.map(place => (
                  <button
                    key={place.id}
                    onMouseDown={e => { e.preventDefault(); selectPlace(place); }}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 10,
                      width: "100%",
                      padding: "9px 12px",
                      background: "transparent",
                      border: "none",
                      borderBottom: "1px solid var(--border-subtle)",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-widget)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                  >
                    <MapPin size={12} style={{ color: typeColor(place.type), marginTop: 2, flexShrink: 0 }} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ color: "var(--text-bright)", fontSize: 13, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {place.label}
                      </div>
                      <div style={{ color: "var(--text-dim)", fontSize: 11, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {place.sublabel}
                      </div>
                    </div>
                    <span style={{ marginLeft: "auto", fontSize: 10, padding: "2px 6px", borderRadius: 10, background: "var(--bg-widget)", color: typeColor(place.type), whiteSpace: "nowrap", flexShrink: 0 }}>
                      {place.type}
                    </span>
                  </button>
                ))}

                {!searching && noResults && (
                  <div style={{ padding: "12px 14px", color: "var(--text-dim)", fontSize: 12 }}>
                    No results in Rwanda for "{query}"
                  </div>
                )}

                <div style={{ padding: "5px 12px 6px", fontSize: 10, color: "var(--primary)", display: "flex", alignItems: "center", gap: 4, borderTop: "1px solid var(--border-subtle)" }}>
                  <Satellite size={9} />
                  Select to auto-fetch 30-year NASA POWER climatology
                </div>
              </div>
            )}
          </div>

          {/* Location pill */}
          {location.district && (
            <div
              className="location-pill"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontSize: 11,
                color: "var(--primary)",
                background: "var(--bg-widget)",
                padding: "5px 12px",
                borderRadius: 6,
                border: "1px solid var(--border)",
              }}
            >
              <MapPin size={12} color="var(--primary)" />
              <span style={{ fontWeight: 600 }}>{location.district} ({location.elevation_m || 1850}m)</span>
            </div>
          )}

          {/* Theme toggle (Light / Dark Black) */}
          <button
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            aria-label="Toggle dark mode"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "5px 10px",
              borderRadius: 6,
              background: "var(--bg-widget)",
              border: "1px solid var(--border)",
              color: "var(--primary)",
              cursor: "pointer",
              fontSize: 11,
              fontWeight: 600,
              transition: "all 0.15s ease",
            }}
          >
            {theme === "dark" ? (
              <>
                <Sun size={13} style={{ color: "#f59e0b" }} />
                <span style={{ color: "#ffffff" }}>Light</span>
              </>
            ) : (
              <>
                <Moon size={13} style={{ color: "var(--primary)" }} />
                <span>Dark</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── NASA DATA MODAL ─────────────────────────────────────────────────── */}
      {showModal && nasaData && selected && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 10000,
            background: "rgba(15, 23, 42, 0.65)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backdropFilter: "blur(4px)",
            padding: 16,
          }}
          onClick={e => { if (e.target === e.currentTarget) dismissModal(); }}
        >
          <div
            style={{
              width: "min(960px, 96vw)",
              maxHeight: "92vh",
              overflowY: "auto",
              background: theme === "dark" ? "#0f172a" : "#ffffff",
              border: theme === "dark" ? "1px solid rgba(255,255,255,0.12)" : "1px solid #bfdbfe",
              borderRadius: 12,
              boxShadow: theme === "dark"
                ? "0 25px 60px -15px rgba(0,0,0,0.85)"
                : "0 20px 50px -12px rgba(15, 23, 42, 0.25)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            {/* Header banner: Rich royal blue */}
            <div
              style={{
                padding: "14px 22px",
                background: "linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                color: "#ffffff",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <Satellite size={20} style={{ color: "#ffffff" }} />
                <span style={{ fontSize: 17, fontWeight: 700, letterSpacing: 0.2 }}>
                  NASA POWER Climate Data
                </span>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 5,
                    fontSize: 10.5,
                    fontWeight: 700,
                    padding: "3px 10px",
                    borderRadius: 9999,
                    background: "#16a34a",
                    color: "#ffffff",
                    letterSpacing: 0.5,
                    textTransform: "uppercase",
                  }}
                >
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#ffffff", display: "inline-block" }} />
                  {nasaData.source === "nasa_power_live" ? "Live" : nasaData.source === "nasa_power_cache" ? "Cached" : "Fallback"}
                </span>
              </div>
              <button
                onClick={dismissModal}
                style={{
                  background: "rgba(255, 255, 255, 0.18)",
                  border: "1px solid rgba(255, 255, 255, 0.25)",
                  borderRadius: 6,
                  width: 28,
                  height: 28,
                  padding: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  color: "#ffffff",
                  transition: "background 0.15s",
                }}
                title="Close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Subheader info strip */}
            <div
              style={{
                padding: "14px 24px 10px",
                borderBottom: theme === "dark" ? "1px solid rgba(255,255,255,0.06)" : "1px solid #f1f5f9",
              }}
            >
              <div style={{ fontSize: 13, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 6 }}>
                <span style={{ color: theme === "dark" ? "#60a5fa" : "#1d4ed8", fontWeight: 700 }}>
                  {selected.label}
                </span>
                <span style={{ color: theme === "dark" ? "#475569" : "#94a3b8" }}>|</span>
                <span style={{ color: theme === "dark" ? "#94a3b8" : "#475569" }}>
                  {selected.sublabel}
                </span>
                <span style={{ color: theme === "dark" ? "#475569" : "#94a3b8" }}>|</span>
                <span style={{ color: theme === "dark" ? "#94a3b8" : "#475569" }}>
                  {selected.lat.toFixed(4)}°, {selected.lon.toFixed(4)}°
                </span>
                <span style={{ color: theme === "dark" ? "#475569" : "#94a3b8" }}>|</span>
                <span style={{ color: theme === "dark" ? "#94a3b8" : "#475569" }}>
                  ~{selected.elevation} m a.s.l.
                </span>
              </div>
              <div style={{ color: theme === "dark" ? "#64748b" : "#64748b", fontSize: 11.5, marginTop: 3 }}>
                30-year monthly climatology
              </div>
            </div>

            {/* 4 KPI Stat Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, padding: "12px 24px 14px" }}>
              {/* Card 1: Temp Range */}
              <div
                style={{
                  background: theme === "dark" ? "rgba(37, 99, 235, 0.12)" : "#eff6ff",
                  border: theme === "dark" ? "1px solid rgba(59, 130, 246, 0.3)" : "1px solid #bfdbfe",
                  borderRadius: 10,
                  padding: "12px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <Thermometer size={28} strokeWidth={2.2} style={{ color: theme === "dark" ? "#60a5fa" : "#1d4ed8", flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.6, color: theme === "dark" ? "#93c5fd" : "#1d4ed8", marginBottom: 2 }}>
                    Avg Temp Range
                  </div>
                  <div style={{ fontSize: 21, fontWeight: 800, color: theme === "dark" ? "#dbeafe" : "#1d4ed8", letterSpacing: "-0.3px" }}>
                    {`${(nasaData.monthly_climate.reduce((s, m) => s + m.tmin, 0) / 12).toFixed(1)}–${(nasaData.monthly_climate.reduce((s, m) => s + m.tmax, 0) / 12).toFixed(1)} °C`}
                  </div>
                </div>
              </div>

              {/* Card 2: Annual Rainfall */}
              <div
                style={{
                  background: theme === "dark" ? "rgba(2, 132, 199, 0.12)" : "#eff6ff",
                  border: theme === "dark" ? "1px solid rgba(2, 132, 199, 0.3)" : "1px solid #bfdbfe",
                  borderRadius: 10,
                  padding: "12px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <CloudRain size={28} strokeWidth={2.2} style={{ color: theme === "dark" ? "#38bdf8" : "#0284c7", flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.6, color: theme === "dark" ? "#38bdf8" : "#0284c7", marginBottom: 2 }}>
                    Annual Rainfall
                  </div>
                  <div style={{ fontSize: 21, fontWeight: 800, color: theme === "dark" ? "#f1f5f9" : "#0f172a", letterSpacing: "-0.3px" }}>
                    {`${nasaData.monthly_rainfall.reduce((s, m) => s + m.rainfall_mm, 0).toFixed(0)} mm`}
                  </div>
                </div>
              </div>

              {/* Card 3: Avg Wind Speed */}
              <div
                style={{
                  background: theme === "dark" ? "rgba(22, 163, 74, 0.12)" : "#f0fdf4",
                  border: theme === "dark" ? "1px solid rgba(34, 197, 94, 0.3)" : "1px solid #bbf7d0",
                  borderRadius: 10,
                  padding: "12px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <Wind size={28} strokeWidth={2.2} style={{ color: theme === "dark" ? "#4ade80" : "#16a34a", flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.6, color: theme === "dark" ? "#4ade80" : "#15803d", marginBottom: 2 }}>
                    Avg Wind Speed
                  </div>
                  <div style={{ fontSize: 21, fontWeight: 800, color: theme === "dark" ? "#86efac" : "#15803d", letterSpacing: "-0.3px" }}>
                    {`${(nasaData.monthly_climate.reduce((s, m) => s + m.wind_speed, 0) / 12).toFixed(2)} m/s`}
                  </div>
                </div>
              </div>

              {/* Card 4: Annual ETo */}
              <div
                style={{
                  background: theme === "dark" ? "rgba(217, 119, 6, 0.12)" : "#fffbeb",
                  border: theme === "dark" ? "1px solid rgba(245, 158, 11, 0.3)" : "1px solid #fde68a",
                  borderRadius: 10,
                  padding: "12px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <Sun size={28} strokeWidth={2.2} style={{ color: theme === "dark" ? "#fbbf24" : "#d97706", flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.6, color: theme === "dark" ? "#fbbf24" : "#b45309", marginBottom: 2 }}>
                    Annual ETo
                  </div>
                  <div style={{ fontSize: 21, fontWeight: 800, color: theme === "dark" ? "#fef3c7" : "#b45309", letterSpacing: "-0.3px" }}>
                    {`${nasaData.monthly_climate.reduce((s, m) => s + m.eto, 0).toFixed(1)} mm`}
                  </div>
                </div>
              </div>
            </div>

            {/* Section title */}
            <div style={{ padding: "4px 24px 8px", fontSize: 13, fontWeight: 800, textTransform: "uppercase", letterSpacing: 0.6, color: theme === "dark" ? "#93c5fd" : "#1e3a8a" }}>
              Monthly Climate & Rainfall
            </div>

            {/* Monthly table */}
            <div style={{ padding: "0 24px" }}>
              <div
                style={{
                  borderRadius: 10,
                  overflow: "hidden",
                  border: theme === "dark" ? "1px solid rgba(255,255,255,0.1)" : "1px solid #bfdbfe",
                  background: theme === "dark" ? "rgba(15, 23, 42, 0.6)" : "#ffffff",
                }}
              >
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
                  <thead>
                    <tr
                      style={{
                        background: theme === "dark" ? "rgba(30, 41, 59, 0.9)" : "#eff6ff",
                        borderBottom: theme === "dark" ? "1px solid rgba(255,255,255,0.12)" : "1px solid #bfdbfe",
                      }}
                    >
                      {[
                        { title: "MONTH", align: "left" },
                        { title: "T MIN (°C)", align: "center" },
                        { title: "T MAX (°C)", align: "center" },
                        { title: "RH MIN (%)", align: "center" },
                        { title: "RH MAX (%)", align: "center" },
                        { title: "WIND (M/S)", align: "center" },
                        { title: "SUN (H)", align: "center" },
                        { title: "ETO (MM/D)", align: "center" },
                        { title: "RAIN (MM)", align: "center" },
                        { title: "EFF. RAIN (MM)", align: "center" },
                      ].map((col, idx) => (
                        <th
                          key={col.title}
                          style={{
                            padding: "9px 10px",
                            textAlign: col.align as any,
                            paddingLeft: idx === 0 ? 18 : 10,
                            color: theme === "dark" ? "#60a5fa" : "#1d4ed8",
                            fontWeight: 700,
                            fontSize: 10.5,
                            letterSpacing: 0.5,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {col.title}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {nasaData.monthly_climate.map((m, i) => {
                      const rain = nasaData.monthly_rainfall[i];
                      const isAlternate = i % 2 === 1;
                      return (
                        <tr
                          key={m.month}
                          style={{
                            background: isAlternate
                              ? (theme === "dark" ? "rgba(255,255,255,0.02)" : "#fafcff")
                              : "transparent",
                            borderBottom: theme === "dark"
                              ? "1px solid rgba(255,255,255,0.05)"
                              : "1px solid #f1f5f9",
                          }}
                        >
                          {/* Month */}
                          <td style={{ padding: "8px 10px 8px 18px", textAlign: "left", fontWeight: 700, color: theme === "dark" ? "#60a5fa" : "#1d4ed8" }}>
                            {m.month}
                          </td>
                          {/* T Min */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 700, color: theme === "dark" ? "#f87171" : "#dc2626" }}>
                            {m.tmin.toFixed(1)}
                          </td>
                          {/* T Max */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 700, color: theme === "dark" ? "#fbbf24" : "#ea580c" }}>
                            {m.tmax.toFixed(1)}
                          </td>
                          {/* RH Min */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 500, color: theme === "dark" ? "#cbd5e1" : "#475569" }}>
                            {m.rhmin.toFixed(0)}
                          </td>
                          {/* RH Max */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 500, color: theme === "dark" ? "#cbd5e1" : "#475569" }}>
                            {m.rhmax.toFixed(0)}
                          </td>
                          {/* Wind */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 700, color: theme === "dark" ? "#4ade80" : "#16a34a" }}>
                            {m.wind_speed.toFixed(2)}
                          </td>
                          {/* Sun */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 500, color: theme === "dark" ? "#94a3b8" : "#475569" }}>
                            {m.sunshine_hours.toFixed(1)}
                          </td>
                          {/* ETo */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 700, color: theme === "dark" ? "#38bdf8" : "#0284c7" }}>
                            {m.eto.toFixed(2)}
                          </td>
                          {/* Rain */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 800, color: theme === "dark" ? "#60a5fa" : "#1d4ed8" }}>
                            {rain ? rain.rainfall_mm.toFixed(1) : "—"}
                          </td>
                          {/* Effective Rain */}
                          <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 500, color: theme === "dark" ? "#94a3b8" : "#475569" }}>
                            {rain ? rain.effective_rain_mm.toFixed(1) : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Actions & info banner */}
            <div
              style={{
                padding: "14px 24px 18px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 16,
                borderTop: theme === "dark" ? "1px solid rgba(255,255,255,0.08)" : "1px solid #f1f5f9",
                marginTop: 14,
              }}
            >
              {/* Info banner */}
              <div
                style={{
                  background: theme === "dark" ? "rgba(37, 99, 235, 0.12)" : "#eff6ff",
                  border: theme === "dark" ? "1px solid rgba(59, 130, 246, 0.25)" : "1px solid #bfdbfe",
                  borderRadius: 8,
                  padding: "10px 14px",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  flex: 1,
                }}
              >
                <Info size={20} style={{ color: theme === "dark" ? "#60a5fa" : "#2563eb", flexShrink: 0 }} />
                <div style={{ fontSize: 12, lineHeight: 1.45, color: theme === "dark" ? "#93c5fd" : "#1e40af" }}>
                  Applying will load this NASA POWER data into the project Climate & Rainfall tables and set the active location to{" "}
                  <strong style={{ color: theme === "dark" ? "#ffffff" : "#1d4ed8" }}>{selected.label}</strong>.
                  You can still edit any value manually afterwards.
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
                <button
                  onClick={dismissModal}
                  style={{
                    padding: "9px 22px",
                    background: theme === "dark" ? "rgba(255,255,255,0.06)" : "#f8fafc",
                    border: theme === "dark" ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                    borderRadius: 6,
                    color: theme === "dark" ? "#e2e8f0" : "#334155",
                    fontSize: 13,
                    cursor: "pointer",
                    fontWeight: 600,
                    transition: "all 0.15s",
                  }}
                >
                  Dismiss
                </button>
                <button
                  onClick={applyData}
                  style={{
                    padding: "9px 22px",
                    background: "linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)",
                    border: "none",
                    borderRadius: 6,
                    color: "#ffffff",
                    fontSize: 13,
                    cursor: "pointer",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    boxShadow: "0 2px 8px rgba(37, 99, 235, 0.35)",
                    transition: "opacity 0.15s",
                  }}
                >
                  <CheckCircle size={16} />
                  Apply to Project
                </button>
              </div>
            </div>
          </div>
        </div>
      )}


      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  );
}
