"use client";

import React, { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { useIrriGridStore } from "@/lib/store";
import { AlertTriangle, BarChart3, BookOpen, CheckCircle, Globe, Loader2, MapPin, Satellite, Target, X } from "lucide-react";
import * as turf from "@turf/turf";

interface NominatimHit {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type: string;
  class: string;
  address?: {
    district?: string;
    county?: string;
    city_district?: string;
    state_district?: string;
    state?: string;
    municipality?: string;
    village?: string;
    town?: string;
    suburb?: string;
    city?: string;
    sector?: string;
    neighbourhood?: string;
    [key: string]: string | undefined;
  };
}

interface DistrictInfo {
  name: string;
  province: string;
  lat: number;
  lng: number;
  altitude: number;
  area_km2: number;
  population: number;
  sectors: string[];
  climate_zone: string;
  avg_rainfall_mm: number;
  avg_temp_c: number;
  soil_types: string[];
}

interface OfflineLocation {
  province: string;
  district: string;
  sector: string;
  cell: string;
  village: string;
  lat: number;
  lng: number;
  altitude: number;
  climate_zone: string;
}

const PROVINCES = [
  "Northern Province",
  "Southern Province",
  "Eastern Province",
  "Western Province",
  "Kigali City",
];

export default function LocationPanel() {
  const { location, setLocation } = useIrriGridStore();

  const [districtsData, setDistrictsData] = useState<Record<string, DistrictInfo>>({});
  const [offlineLocations, setOfflineLocations] = useState<OfflineLocation[]>([]);
  const [districtGeoJSON, setDistrictGeoJSON] = useState<any>(null);

  // ── OSM Live Search state ──
  const [searchText, setSearchText] = useState("");
  const [osmResults, setOsmResults] = useState<NominatimHit[]>([]);
  const [osmSearching, setOsmSearching] = useState(false);
  const [osmOpen, setOsmOpen] = useState(false);
  const [osmNoResults, setOsmNoResults] = useState(false);
  const osmDebounce = useRef<ReturnType<typeof setTimeout> | null>(null);
  const osmInputRef = useRef<HTMLInputElement>(null);
  const osmDropRef = useRef<HTMLDivElement>(null);

  const [gridSearchText, setGridSearchText] = useState("");
  const [gridError, setGridError] = useState("");
  const [gridSuccess, setGridSuccess] = useState("");

  const [selectedProvince, setSelectedProvince] = useState(location.province || "Northern Province");
  const [selectedDistrict, setSelectedDistrict] = useState(location.district || "Musanze");
  const [selectedSector, setSelectedSector] = useState(location.sector || "Musanze");
  const [selectedCell, setSelectedCell] = useState(location.cell || "");

  // Geolocation state
  const [geoStatus, setGeoStatus] = useState<"idle" | "requesting" | "granted" | "denied" | "unavailable">("idle");
  const [geoDistrict, setGeoDistrict] = useState("");

  // Load all data
  useEffect(() => {
    fetch("/data/rwanda_districts_data.json")
      .then((r) => r.json())
      .then(setDistrictsData)
      .catch((e) => console.error("districts_data:", e));

    fetch("/data/rwanda_admin_locations.json")
      .then((r) => r.json())
      .then(setOfflineLocations)
      .catch((e) => console.error("admin_locations:", e));

    fetch("/data/rwanda_districts.geojson")
      .then((r) => r.json())
      .then(setDistrictGeoJSON)
      .catch((e) => console.error("districts.geojson:", e));
  }, []);

  // Request geolocation on mount
  useEffect(() => {
    if (!("geolocation" in navigator)) {
      setGeoStatus("unavailable");
      return;
    }
    setGeoStatus("requesting");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setGeoStatus("granted");
        // Only adopt browser GPS if inside Rwanda
        const inRwanda = latitude >= -2.95 && latitude <= -1.0 && longitude >= 28.8 && longitude <= 30.95;
        if (inRwanda) {
          setLocation({ lat: latitude, lon: longitude });
        }
      },
      () => {
        setGeoStatus("denied");
      },
      { timeout: 10000 }
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Point-in-polygon: resolve district from GPS once geojson is loaded
  useEffect(() => {
    if (geoStatus !== "granted" || !districtGeoJSON || !location.lat || !location.lon) return;

    const pt = turf.point([location.lon, location.lat]);
    let matchedFeature: any = null;

    for (const feature of districtGeoJSON.features) {
      try {
        if (turf.booleanPointInPolygon(pt, feature)) {
          matchedFeature = feature;
          break;
        }
      } catch {
        // skip malformed features
      }
    }

    if (matchedFeature) {
      const distName = matchedFeature.properties?.NAME_2 || matchedFeature.properties?.name || "";
      const distInfo = Object.values(districtsData).find(
        (d) => d.name.toLowerCase() === distName.toLowerCase()
      );
      const province = distInfo?.province || location.province || "Northern Province";
      const sectors = distInfo?.sectors || [];

      setGeoDistrict(distName);
      setSelectedProvince(province);
      setSelectedDistrict(distName);
      setSelectedSector(sectors[0] || distName);
      setSelectedCell("");
      setLocation({
        province,
        district: distName,
        sector: sectors[0] || distName,
        cell: "",
        elevation_m: distInfo?.altitude || location.elevation_m,
      });
    } else {
      // GPS is in Rwanda but PIP found no match (edge/border) — show warning
      setGeoDistrict("(outside Rwanda boundary data)");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geoStatus, districtGeoJSON, districtsData]);

  // Sync dropdowns from store
  useEffect(() => {
    if (location.province && location.province !== selectedProvince) setSelectedProvince(location.province);
    if (location.district && location.district !== selectedDistrict) setSelectedDistrict(location.district);
    if (location.sector && location.sector !== selectedSector) setSelectedSector(location.sector);
    if (location.cell !== undefined && location.cell !== selectedCell) setSelectedCell(location.cell);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.province, location.district, location.sector, location.cell]);

  // Filter districts by province
  const availableDistricts = useMemo(() =>
    Object.values(districtsData).filter((d) =>
      d.province.toLowerCase() === selectedProvince.toLowerCase()
    ),
  [districtsData, selectedProvince]);

  const availableSectors = useMemo(() => {
    const dist = districtsData[selectedDistrict];
    if (dist?.sectors?.length > 0) return dist.sectors;
    const secSet = new Set<string>();
    offlineLocations
      .filter((l) => l.district.toLowerCase() === selectedDistrict.toLowerCase())
      .forEach((l) => l.sector && secSet.add(l.sector));
    return Array.from(secSet);
  }, [districtsData, offlineLocations, selectedDistrict]);

  const availableCells = useMemo(() => {
    const cellSet = new Set<string>();
    offlineLocations
      .filter((l) =>
        l.district.toLowerCase() === selectedDistrict.toLowerCase() &&
        l.sector.toLowerCase() === selectedSector.toLowerCase()
      )
      .forEach((l) => l.cell && cellSet.add(l.cell));
    return Array.from(cellSet);
  }, [offlineLocations, selectedDistrict, selectedSector]);

  const districtOptions = useMemo(() => {
    const list = availableDistricts.map((d) => d.name);
    if (selectedDistrict && !list.some((d) => d.toLowerCase() === selectedDistrict.toLowerCase())) {
      list.unshift(selectedDistrict);
    }
    return list;
  }, [availableDistricts, selectedDistrict]);

  const sectorOptions = useMemo(() => {
    const list = [...availableSectors];
    if (selectedSector && !list.some((s) => s.toLowerCase() === selectedSector.toLowerCase())) {
      list.unshift(selectedSector);
    }
    return list;
  }, [availableSectors, selectedSector]);

  const searchMatches = useMemo(() => {
    const q = searchText.trim().toLowerCase();
    if (!q) return [];
    const out: OfflineLocation[] = [];
    for (const loc of offlineLocations) {
      if (
        loc.district.toLowerCase().includes(q) ||
        loc.sector.toLowerCase().includes(q) ||
        loc.cell.toLowerCase().includes(q) ||
        loc.province.toLowerCase().includes(q)
      ) {
        out.push(loc);
        if (out.length >= 8) break;
      }
    }
    return out;
  }, [searchText, offlineLocations]);

  // ── Nominatim geocode ──────────────────────────────────────────────────────
  const geocodeOSM = useCallback(async (q: string) => {
    if (q.trim().length < 2) { setOsmResults([]); setOsmNoResults(false); return; }
    setOsmSearching(true);
    setOsmNoResults(false);
    try {
      const url = new URL("https://nominatim.openstreetmap.org/search");
      url.searchParams.set("q", q + " Rwanda");
      url.searchParams.set("countrycodes", "rw");
      url.searchParams.set("format", "json");
      url.searchParams.set("limit", "8");
      url.searchParams.set("addressdetails", "1");
      url.searchParams.set("accept-language", "en");
      const resp = await fetch(url.toString(), {
        headers: { "User-Agent": "IrriGrid-Shamba/1.0 irrigation-planning" },
      });
      const data: NominatimHit[] = await resp.json();
      setOsmResults(data);
      setOsmNoResults(data.length === 0);
    } catch {
      setOsmResults([]);
      setOsmNoResults(true);
    } finally {
      setOsmSearching(false);
    }
  }, []);

  useEffect(() => {
    if (osmDebounce.current) clearTimeout(osmDebounce.current);
    if (searchText.trim().length >= 2) {
      osmDebounce.current = setTimeout(() => geocodeOSM(searchText), 400);
    } else {
      setOsmResults([]);
      setOsmNoResults(false);
    }
    return () => { if (osmDebounce.current) clearTimeout(osmDebounce.current); };
  }, [searchText, geocodeOSM]);

  // Close OSM dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        osmDropRef.current && !osmDropRef.current.contains(e.target as Node) &&
        osmInputRef.current && !osmInputRef.current.contains(e.target as Node)
      ) setOsmOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleOSMSelect(hit: NominatimHit) {
    const addr = hit.address || {};
    const lat = parseFloat(hit.lat);
    const lon = parseFloat(hit.lon);

    const parts = hit.display_name.split(",").map((s: string) => s.trim());
    const searchedName = parts[0] || "";

    // Candidate district names from address details and display parts
    const candidates = [
      addr.district,
      addr.county,
      addr.city_district,
      addr.city,
      addr.state_district,
      addr.municipality,
      addr.town,
      ...parts,
    ].filter(Boolean) as string[];

    let matchedDist: DistrictInfo | undefined;
    for (const cand of candidates) {
      const clean = cand.replace(/\s*district\s*$/i, "").trim().toLowerCase();
      const found = Object.values(districtsData).find(
        (d) => d.name.toLowerCase() === clean
      );
      if (found) {
        matchedDist = found;
        break;
      }
    }

    if (!matchedDist) {
      const dNameLower = hit.display_name.toLowerCase();
      matchedDist = Object.values(districtsData).find((d) =>
        dNameLower.includes(d.name.toLowerCase())
      );
    }

    const resolvedProvince = matchedDist?.province || addr.state || selectedProvince;
    const resolvedDistrict = matchedDist?.name || (candidates[0] ? candidates[0].replace(/\s*district\s*$/i, "").trim() : selectedDistrict);

    // Resolve sector: check if searched place matches a sector in the district
    let resolvedSector = "";
    const allKnownSectors = matchedDist?.sectors || [];

    for (const cand of [searchedName, addr.city_district, addr.suburb, addr.village, addr.neighbourhood, ...parts]) {
      if (!cand) continue;
      const clean = cand.replace(/\s*sector\s*$/i, "").trim().toLowerCase();
      const found = allKnownSectors.find((s) => s.toLowerCase() === clean);
      if (found) {
        resolvedSector = found;
        break;
      }
    }

    if (!resolvedSector) {
      for (const cand of [searchedName, addr.city_district, addr.suburb, addr.village, addr.neighbourhood]) {
        if (!cand) continue;
        const clean = cand.replace(/\s*sector\s*$/i, "").trim().toLowerCase();
        const found = offlineLocations.find(
          (l) => l.district.toLowerCase() === resolvedDistrict.toLowerCase() && l.sector.toLowerCase() === clean
        );
        if (found) {
          resolvedSector = found.sector;
          break;
        }
      }
    }

    if (!resolvedSector) {
      if (searchedName && searchedName.toLowerCase() !== resolvedDistrict.toLowerCase()) {
        resolvedSector = searchedName;
      } else {
        resolvedSector = allKnownSectors[0] || resolvedDistrict;
      }
    }

    // Altitude
    const distFromNW = Math.sqrt(Math.pow(lat + 1.5, 2) + Math.pow(lon - 29.5, 2));
    const elev = matchedDist?.altitude || Math.round(Math.max(1300, Math.min(2200, 1900 - distFromNW * 80)));

    setSelectedProvince(resolvedProvince);
    setSelectedDistrict(resolvedDistrict);
    setSelectedSector(resolvedSector);
    setSelectedCell("");

    setLocation({
      province: resolvedProvince,
      district: resolvedDistrict,
      sector: resolvedSector,
      cell: "",
      lat,
      lon,
      elevation_m: elev,
    });

    setSearchText(parts.slice(0, 3).join(", "));
    setOsmOpen(false);
    setOsmResults([]);
  }

  function handleSelectMatch(match: OfflineLocation) {
    const distInfo = districtsData[match.district];
    const fullProvince = distInfo?.province || (match.province.includes("Province") ? match.province : `${match.province} Province`);
    setSelectedProvince(fullProvince);
    setSelectedDistrict(match.district);
    setSelectedSector(match.sector);
    setSelectedCell(match.cell);
    setLocation({
      province: fullProvince,
      district: match.district,
      sector: match.sector,
      cell: match.cell,
      lat: match.lat || distInfo?.lat || location.lat,
      lon: match.lng || distInfo?.lng || location.lon,
      elevation_m: match.altitude || distInfo?.altitude || location.elevation_m,
    });
  }

  function handleProvinceChange(province: string) {
    setSelectedProvince(province);
    const first = Object.values(districtsData).find((d) => d.province.toLowerCase() === province.toLowerCase());
    if (first) {
      setSelectedDistrict(first.name);
      setSelectedSector(first.sectors[0] || first.name);
      setSelectedCell("");
      setLocation({ province, district: first.name, sector: first.sectors[0] || first.name, cell: "", lat: first.lat, lon: first.lng, elevation_m: first.altitude });
    } else {
      setLocation({ province });
    }
  }

  function handleDistrictChange(district: string) {
    setSelectedDistrict(district);
    const info = districtsData[district];
    const firstSec = info?.sectors[0] || district;
    setSelectedSector(firstSec);
    setSelectedCell("");
    if (info) {
      setLocation({ province: info.province, district: info.name, sector: firstSec, cell: "", lat: info.lat, lon: info.lng, elevation_m: info.altitude });
    } else {
      setLocation({ district, sector: firstSec, cell: "" });
    }
  }

  function handleSectorChange(sector: string) {
    setSelectedSector(sector);
    setSelectedCell("");
    const matched = offlineLocations.find(
      (l) => l.district.toLowerCase() === selectedDistrict.toLowerCase() && l.sector.toLowerCase() === sector.toLowerCase()
    );
    setLocation({ sector, cell: "", lat: matched?.lat ?? location.lat, lon: matched?.lng ?? location.lon, elevation_m: matched?.altitude ?? location.elevation_m });
  }

  function handleCellChange(cell: string) {
    setSelectedCell(cell);
    const matched = offlineLocations.find(
      (l) => l.district.toLowerCase() === selectedDistrict.toLowerCase() &&
        l.sector.toLowerCase() === selectedSector.toLowerCase() &&
        l.cell.toLowerCase() === cell.toLowerCase()
    );
    setLocation({ cell, lat: matched?.lat ?? location.lat, lon: matched?.lng ?? location.lon, elevation_m: matched?.altitude ?? location.elevation_m });
  }

  function handleGridSearch() {
    setGridError(""); setGridSuccess("");
    const raw = gridSearchText.trim().toUpperCase().replace(/\s+/g, "");
    if (!raw) { setGridError("Please enter a grid reference (e.g., KG802ST)"); return; }
    const match = raw.match(/^([A-Z]{2})(\d{2,3})([A-Z]{2})$/);
    if (!match) { setGridError(`Invalid format: '${raw}'. Use format like KG802ST`); return; }
    const [, , eastDigits, northLetters] = match;
    const eastNum = parseInt(eastDigits, 10);
    const eastOffset = (eastNum - 500) * 0.0012;
    const northOffset = (northLetters.charCodeAt(0) - 75) * 0.015 + (northLetters.charCodeAt(1) - 75) * 0.0015;
    const newLat = parseFloat((-1.9536 + northOffset).toFixed(5));
    const newLng = parseFloat((30.0606 + eastOffset).toFixed(5));
    setLocation({ lat: newLat, lon: newLng, cell: raw });
    setGridSuccess(`Cell ${raw} located at [Lat: ${newLat}, Lng: ${newLng}]`);
  }

  const currentDistrictInfo = districtsData[selectedDistrict];

  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Header */}
      <div>
        <h2 style={{ color: "var(--primary)", fontSize: 17, fontWeight: "bold", margin: 0, display: "flex", alignItems: "center", gap: 8, letterSpacing: 0.5 }}>
          <BookOpen size={18} color="var(--primary)" /> Rwanda Location Database
        </h2>
        <p style={{ color: "var(--text-dim)", fontSize: 11, margin: "4px 0 0" }}>
          Complete geographic data from districts, provinces, sectors, and cells
        </p>
      </div>

      {/* ── Geolocation Status Banner ── */}
      {geoStatus === "requesting" && (
        <div style={{ background: "var(--primary-06)", border: "1px solid var(--border)", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "var(--primary)", display: "flex", alignItems: "center", gap: 8 }}>
          <Loader2 size={11} className="spin" />
          Requesting GPS location…
        </div>
      )}

      {geoStatus === "granted" && geoDistrict && !geoDistrict.startsWith("(") && (
        <div style={{ background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "var(--success)", display: "flex", alignItems: "center", gap: 8 }}>
          <CheckCircle size={13} /> GPS located — <strong>{geoDistrict} District</strong> auto-selected. You can refine below if needed.
        </div>
      )}

      {(geoStatus === "denied" || geoStatus === "unavailable") && (
        <div style={{ background: "rgba(245, 158, 11, 0.08)", border: "1px solid rgba(245, 158, 11, 0.35)", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "var(--warning)", display: "flex", alignItems: "flex-start", gap: 8 }}>
          <AlertTriangle size={14} />
          <span>
            {geoStatus === "denied"
              ? "Location access wasn't granted, search for your district below instead."
              : "Geolocation is not available in this browser, search for your district below instead."}
          </span>
        </div>
      )}

      {/* ── Smart Location Search (Live OSM) ── */}
      <div className="hud-box" style={{ position: "relative" }}>
        <div className="hud-box-title" style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "space-between" }}>
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}><Globe size={14} /> Smart Location Search</span>
          <span style={{ fontSize: 10, color: "var(--text-dim)", fontWeight: 500, textTransform: "none", letterSpacing: 0 }}>powered by OpenStreetMap</span>
        </div>
        <div style={{ position: "relative", marginTop: 8 }}>
          <input
            ref={osmInputRef}
            type="text"
            className="hud-input"
            value={searchText}
            placeholder="Type any place: Busogo, Kimironko, Musanze…"
            onChange={e => { setSearchText(e.target.value); setOsmOpen(true); }}
            onFocus={() => setOsmOpen(true)}
            style={{ width: "100%", fontSize: 12, paddingRight: searchText ? 28 : 10, boxSizing: "border-box" }}
          />
          {osmSearching && (
            <Loader2
              size={11}
              className="spin"
              style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", color: "var(--primary)" }}
            />
          )}
          {!osmSearching && searchText && (
            <button
              onClick={() => { setSearchText(""); setOsmResults([]); setOsmOpen(false); }}
              style={{ position: "absolute", right: 6, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--text-dim)", fontSize: 13, lineHeight: 1, padding: 0 }}
            >
              <X size={13} />
            </button>
          )}

          {/* Dropdown results */}
          {osmOpen && searchText.trim().length >= 2 && (
            <div
              ref={osmDropRef}
              style={{
                position: "absolute",
                top: "calc(100% + 3px)",
                left: 0, right: 0,
                background: "var(--bg-widget)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
                zIndex: 9000,
                overflow: "hidden",
                maxHeight: 260,
                overflowY: "auto",
              }}
            >
              {osmSearching && (
                <div style={{ padding: "10px 12px", fontSize: 11, color: "var(--text-dim)", display: "flex", alignItems: "center", gap: 8 }}>
                  <Loader2 size={13} className="spin" />
                  Searching Rwanda…
                </div>
              )}
              {!osmSearching && osmResults.map(hit => {
                const parts = hit.display_name.split(",").map((s: string) => s.trim());
                const label = parts[0];
                const sublabel = parts.slice(1, 4).join(", ");
                return (
                  <div
                    key={hit.place_id}
                    onMouseDown={e => { e.preventDefault(); handleOSMSelect(hit); }}
                    style={{ padding: "8px 12px", cursor: "pointer", borderBottom: "1px solid var(--border-subtle)", fontSize: 12 }}
                    onMouseEnter={e => (e.currentTarget.style.background = "var(--primary-06)")}
                    onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                  >
                    <div style={{ color: "var(--text-bright)", fontWeight: 600, fontSize: 13 }}>{label}</div>
                    <div style={{ color: "var(--text-dim)", fontSize: 11, marginTop: 1 }}>{sublabel}</div>
                    <span style={{ fontSize: 9, color: "var(--primary)", textTransform: "uppercase", letterSpacing: 0.5, background: "var(--primary-06)", padding: "1px 5px", borderRadius: 3, display: "inline-block", marginTop: 2 }}>{hit.type}</span>
                  </div>
                );
              })}
              {!osmSearching && osmNoResults && (
                <div style={{ padding: "10px 12px", fontSize: 11, color: "var(--text-dim)" }}>
                  No results in Rwanda for "{searchText}"
                </div>
              )}
            </div>
          )}
        </div>
        <div style={{ marginTop: 6, fontSize: 11, color: "var(--text-dim)", display: "flex", alignItems: "center", gap: 5 }}>
          <Satellite size={12} color="var(--primary)" /> Type 2+ characters — finds any sector, cell, village, hill, or landmark
        </div>
      </div>

      {/* ── Grid Cell Search ── */}
      <div className="hud-box">
        <div className="hud-box-title" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Target size={14} /> Rwanda Grid Cell Search
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
          <input
            type="text"
            className="hud-input"
            value={gridSearchText}
            placeholder="Enter grid ref: KG802ST or KG 802 ST"
            onChange={(e) => setGridSearchText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleGridSearch(); }}
            style={{ width: "100%", fontSize: 12, fontFamily: "var(--font-mono)" }}
          />
          <div style={{ display: "flex", gap: 8 }}>
            <button className="hud-btn primary" onClick={handleGridSearch} style={{ flex: 1, fontSize: 11, padding: "6px 12px", fontWeight: "bold" }}>
              <MapPin size={12} /> Locate Cell
            </button>
            <button className="hud-btn" onClick={() => { setGridSearchText(""); setGridError(""); setGridSuccess(""); }} style={{ padding: "6px 14px", fontSize: 11 }}>
              <X size={12} /> Clear
            </button>
          </div>
          <div style={{ color: "var(--text-dim)", fontSize: 10, fontStyle: "italic" }}>Enter a Rwanda national grid reference to locate the parcel</div>
          {gridError && <div style={{ color: "var(--danger)", fontSize: 11, background: "rgba(239,68,68,0.1)", padding: "4px 8px", borderRadius: 3, border: "1px solid rgba(239,68,68,0.3)", display: "flex", alignItems: "center", gap: 4 }}><AlertTriangle size={11} /> {gridError}</div>}
          {gridSuccess && <div style={{ color: "var(--success)", fontSize: 11, background: "rgba(16,185,129,0.1)", padding: "4px 8px", borderRadius: 3, border: "1px solid rgba(16,185,129,0.3)", display: "flex", alignItems: "center", gap: 4 }}><CheckCircle size={11} /> {gridSuccess}</div>}
        </div>
      </div>

      {/* ── Cascading Dropdowns ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div>
          <label className="hud-label" style={{ marginBottom: 4 }}>Province</label>
          <select className="hud-select" value={selectedProvince} onChange={(e) => handleProvinceChange(e.target.value)}>
            {PROVINCES.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="hud-label" style={{ marginBottom: 4 }}>District</label>
          <select className="hud-select" value={selectedDistrict} onChange={(e) => handleDistrictChange(e.target.value)}>
            {districtOptions.length > 0
              ? districtOptions.map((d) => <option key={d} value={d}>{d}</option>)
              : <option value={selectedDistrict}>{selectedDistrict}</option>}
          </select>
        </div>
        <div>
          <label className="hud-label" style={{ marginBottom: 4 }}>Sector</label>
          <select className="hud-select" value={selectedSector} onChange={(e) => handleSectorChange(e.target.value)}>
            {sectorOptions.length > 0
              ? sectorOptions.map((s) => <option key={s} value={s}>{s}</option>)
              : <option value={selectedSector}>{selectedSector || "-- Select Sector --"}</option>}
          </select>
        </div>
        <div>
          <label className="hud-label" style={{ marginBottom: 4 }}>Cell (Optional)</label>
          <select className="hud-select" value={selectedCell} onChange={(e) => handleCellChange(e.target.value)}>
            <option value="">-- Select Cell (Optional) --</option>
            {availableCells.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* ── Location Info ── */}
      <div className="hud-box">
        <div className="hud-box-title" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <BarChart3 size={14} /> Location Information
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8, fontSize: 11 }}>
          <div className="hud-row"><span>Location:</span><span style={{ color: "var(--primary)", fontWeight: "bold" }}>{selectedDistrict}{selectedSector ? `, ${selectedSector}` : ""}</span></div>
          <div className="hud-row"><span>Coordinates:</span><span style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{location.lat?.toFixed(4)}°, {location.lon?.toFixed(4)}°</span></div>
          <div className="hud-row"><span>Altitude:</span><span style={{ fontFamily: "var(--font-mono)" }}>{currentDistrictInfo?.altitude || location.elevation_m || 1850} m a.s.l.</span></div>
          <div className="hud-row"><span>Climate Zone:</span><span>{currentDistrictInfo?.climate_zone || "Temperate Highland"}</span></div>
          <div className="hud-row"><span>Annual Rainfall:</span><span style={{ fontFamily: "var(--font-mono)", color: "var(--primary)" }}>{currentDistrictInfo?.avg_rainfall_mm || 1100} mm/year</span></div>
          <div className="hud-row"><span>Primary Soils:</span><span>{currentDistrictInfo?.soil_types?.join(", ") || "Volcanic Loam, Clay"}</span></div>
        </div>
      </div>
    </div>
  );
}