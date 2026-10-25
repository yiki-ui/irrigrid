"use client";

import React, { useEffect, useRef, useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import "leaflet/dist/leaflet.css";
import * as turf from "@turf/turf";
import {
  Map as MapIcon,
  Layers,
  MapPin,
  Check,
  Pencil,
  X,
  Crosshair,
  Trash2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Navigation,
  Droplets,
  Ruler
} from "lucide-react";


const SATELLITE_URL =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
const OSM_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

function calcMetrics(coords: [number, number][]) {
  if (coords.length < 3) return { area_m2: 0, area_ha: 0, perimeter_m: 0 };
  // turf needs [lng, lat] ring closed
  const ring = coords.map((c) => [c[1], c[0]] as [number, number]);
  ring.push(ring[0]);
  const poly = turf.polygon([ring]);
  const area_m2 = turf.area(poly);
  const perimeter_m = turf.length(poly, { units: "meters" });
  return {
    area_m2: Math.round(area_m2),
    area_ha: parseFloat((area_m2 / 10000).toFixed(3)),
    perimeter_m: Math.round(perimeter_m),
  };
}

export default function FarmMap() {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<any>(null);
  const tileLayerRef = useRef<any>(null);
  const districtLayerRef = useRef<any>(null);
  const locationMarkerRef = useRef<any>(null);
  const drawnPolygonRef = useRef<any>(null);
  const tempDrawPointsRef = useRef<any[]>([]);
  const tempDrawLineRef = useRef<any>(null);
  const pumpMarkerRef = useRef<any>(null);
  const geojsonCacheRef = useRef<any>(null);

  // Refs that the map click handler reads — avoids stale closures
  const isDrawingRef = useRef(false);
  const isPlacingPumpRef = useRef(false);
  const drawPointsRef = useRef<[number, number][]>([]);
  const clickHandlerRef = useRef<((e: any) => void) | null>(null);

  const { location, setLocation } = useIrriGridStore();

  const [mouseCoords, setMouseCoords] = useState({ lat: -1.5, lng: 29.63 });
  const [basemap, setBasemap] = useState<"satellite" | "osm">("satellite");
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawPoints, setDrawPoints] = useState<[number, number][]>([]);
  const [isPlacingPump, setIsPlacingPump] = useState(false);
  const [fieldBadge, setFieldBadge] = useState("");
  // True once Leaflet has finished initialising the map instance
  const [mapReady, setMapReady] = useState(false);

  // Keep refs in sync with state
  useEffect(() => { isDrawingRef.current = isDrawing; }, [isDrawing]);
  useEffect(() => { isPlacingPumpRef.current = isPlacingPump; }, [isPlacingPump]);
  useEffect(() => { drawPointsRef.current = drawPoints; }, [drawPoints]);

  // ── Helper: highlight district boundary + label marker ──────────────────
  function highlightDistrict(geojson: any, districtName: string, sectorName?: string, flyLat?: number, flyLon?: number) {
    const map = mapInstance.current;
    if (!map) return;

    import("leaflet").then((L) => {
      if (districtLayerRef.current) {
        map.removeLayer(districtLayerRef.current);
        districtLayerRef.current = null;
      }
      if (locationMarkerRef.current) {
        map.removeLayer(locationMarkerRef.current);
        locationMarkerRef.current = null;
      }

      const cleanDistrict = (districtName || "").replace(/\s*district\s*$/i, "").trim();
      const normDist = cleanDistrict.toLowerCase();

      const matches = geojson?.features?.filter((f: any) => {
        const n = (f.properties?.NAME_2 || f.properties?.name || "").toLowerCase().replace(/\s*district\s*$/i, "").trim();
        return n === normDist;
      }) || [];

      let actualPt: any = null;
      const pinLat = flyLat ?? location.lat;
      const pinLon = flyLon ?? location.lon;

      if (matches.length > 0) {
        // Cyan boundary outline
        districtLayerRef.current = L.geoJSON(
          { type: "FeatureCollection", features: matches } as any,
          {
            style: {
              color: "#00e5ff",
              weight: 3,
              fillColor: "#00e5ff",
              fillOpacity: 0.18,
              dashArray: "6, 4",
            },
          }
        ).addTo(map);

        const bounds = districtLayerRef.current.getBounds();
        actualPt = (pinLat && pinLon) ? L.latLng(pinLat, pinLon) : bounds.getCenter();
      } else if (pinLat && pinLon) {
        actualPt = L.latLng(pinLat, pinLon);
      }

      if (!actualPt) return;

      map.flyTo(actualPt, 14, { duration: 0.8 });

      const label = sectorName && sectorName.toLowerCase() !== normDist
        ? `${sectorName}, ${cleanDistrict}`
        : cleanDistrict || sectorName || "Selected Location";

      locationMarkerRef.current = L.marker(actualPt, {
        icon: L.divIcon({
          className: "",
          html: `
            <div style="
              background: #0a1628;
              color: #ffffff;
              padding: 5px 12px;
              border-radius: 16px;
              font-weight: 600;
              font-size: 12px;
              border: 1.5px solid #00e5ff;
              box-shadow: 0 4px 14px rgba(0, 229, 255, 0.4), 0 2px 6px rgba(0,0,0,0.8);
              white-space: nowrap;
              display: inline-flex;
              align-items: center;
              gap: 6px;
              transform: translate(-50%, -100%);
              pointer-events: auto;
            ">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#00e5ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
                <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              <span style="color: #00e5ff; font-weight: 700;">${label}</span>
            </div>
          `,
          iconSize: [0, 0],
          iconAnchor: [0, 0],
        }),
      }).addTo(map);
    });
  }

  // ── Initialize Leaflet map (once) ────────────────────────────────────────
  useEffect(() => {
    if (typeof window === "undefined" || !mapRef.current || mapInstance.current) return;
    let isMounted = true;

    import("leaflet").then((L) => {
      if (!isMounted || !mapRef.current || mapInstance.current) return;

      const map = L.map(mapRef.current, {
        center: [location.lat || -1.5, location.lon || 29.63],
        zoom: 12,
        zoomControl: false,
      });

      tileLayerRef.current = L.tileLayer(SATELLITE_URL, {
        attribution: "Tiles © Esri",
        maxZoom: 19,
      }).addTo(map);

      map.on("mousemove", (e: any) => {
        setMouseCoords({
          lat: parseFloat(e.latlng.lat.toFixed(5)),
          lng: parseFloat(e.latlng.lng.toFixed(5)),
        });
      });

      // Store click handler ref for cleanup
      const clickHandler = (e: any) => {
        const pt: [number, number] = [e.latlng.lat, e.latlng.lng];

        if (isPlacingPumpRef.current) {
          if (pumpMarkerRef.current) map.removeLayer(pumpMarkerRef.current);
          pumpMarkerRef.current = L.marker(pt, {
            icon: L.divIcon({
              className: "",
              html: `
                <div style="
                  background:#081426;color:#00e5ff;
                  border:2px solid #00e5ff;padding:4px 8px;
                  border-radius:4px;font-weight:bold;font-size:11px;
                  box-shadow:0 0 10px rgba(0,229,255,0.6);
                  white-space:nowrap;display:flex;align-items:center;gap:4px;">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#00e5ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
                    <path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z" />
                  </svg> Pump
                </div>`,
              iconSize: [75, 28],
              iconAnchor: [37, 14],
            }),
          }).addTo(map);
          pumpMarkerRef.current.bindPopup("<b>Pump / Water Source</b>").openPopup();
          setLocation({ water_source: pt });
          setIsPlacingPump(false);
          map.getContainer().style.cursor = "";
          return;
        }

        if (isDrawingRef.current) {
          const newPts = [...drawPointsRef.current, pt];
          drawPointsRef.current = newPts; // update ref immediately
          setDrawPoints([...newPts]);

          const dot = L.circleMarker(pt, {
            radius: 5,
            color: "#00e5ff",
            fillColor: "#ffffff",
            fillOpacity: 1,
            weight: 2,
          }).addTo(map);
          tempDrawPointsRef.current.push(dot);

          if (tempDrawLineRef.current) map.removeLayer(tempDrawLineRef.current);
          tempDrawLineRef.current = L.polyline(newPts, {
            color: "#00e5ff",
            weight: 3,
            dashArray: "4, 4",
          }).addTo(map);
        }
      };
      clickHandlerRef.current = clickHandler;
      map.on("click", clickHandler);

      mapInstance.current = map;
      setMapReady(true);

      // Load district GeoJSON and highlight initial district
      fetch("/data/rwanda_districts.geojson")
        .then((r) => r.json())
        .then((geojson) => {
          geojsonCacheRef.current = geojson;
          highlightDistrict(geojson, location.district || "Musanze", location.sector || "Musanze", location.lat, location.lon);
        })
        .catch((err) => console.error("Error loading district GeoJSON:", err));
    });

    return () => {
      isMounted = false;
      if (mapInstance.current) {
        mapInstance.current.off("mousemove");
        if (clickHandlerRef.current) {
          mapInstance.current.off("click", clickHandlerRef.current);
        }
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Re-highlight when district/sector changes (from location search) ─────
  useEffect(() => {
    if (geojsonCacheRef.current && location.district) {
      highlightDistrict(
        geojsonCacheRef.current,
        location.district,
        location.sector,
        location.lat,
        location.lon
      );
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.district, location.sector, location.lat, location.lon]);

  // ── Restore drawn polygon from store when map re-mounts after a tab switch ─
  // Only fires once (when mapReady flips true). Skips the 4-point default.
  useEffect(() => {
    if (!mapReady) return;
    const poly = location.polygon;
    // 4-point default placeholder at Musanze — don't restore it
    if (!poly || poly.length < 3) return;
    if (poly.length === 4 && location.area_ha === 2.5) return;

    import("leaflet").then((L) => {
      const map = mapInstance.current;
      if (!map) return;
      if (drawnPolygonRef.current) map.removeLayer(drawnPolygonRef.current);
      drawnPolygonRef.current = L.polygon(poly, {
        color: "#00e5ff", weight: 3,
        fillColor: "#00e5ff", fillOpacity: 0.2,
      }).addTo(map);
      const metrics = calcMetrics(poly);
      setFieldBadge(`${metrics.area_ha.toFixed(3)} ha (${metrics.area_m2} m²) | Perimeter: ${metrics.perimeter_m} m`);
      map.flyToBounds(drawnPolygonRef.current.getBounds(), { padding: [40, 40] });
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapReady]);

  // ── Basemap toggle ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapInstance.current || !tileLayerRef.current) return;
    import("leaflet").then((L) => {
      tileLayerRef.current.remove();
      const url = basemap === "satellite" ? SATELLITE_URL : OSM_URL;
      const attr = basemap === "satellite" ? "Tiles © Esri" : "© OpenStreetMap contributors";
      tileLayerRef.current = L.tileLayer(url, { attribution: attr, maxZoom: 19 })
        .addTo(mapInstance.current);
    });
  }, [basemap]);

  // ── Finish Polygon Drawing ────────────────────────────────────────────────
  const finishDrawing = () => {
    const map = mapInstance.current;
    const pts = drawPointsRef.current;
    if (!map || pts.length < 3) { cancelDrawing(); return; }

    import("leaflet").then((L) => {
      tempDrawPointsRef.current.forEach((d) => map.removeLayer(d));
      tempDrawPointsRef.current = [];
      if (tempDrawLineRef.current) { map.removeLayer(tempDrawLineRef.current); tempDrawLineRef.current = null; }
      if (drawnPolygonRef.current) map.removeLayer(drawnPolygonRef.current);

      drawnPolygonRef.current = L.polygon(pts, {
        color: "#00e5ff",
        weight: 3,
        fillColor: "#00e5ff",
        fillOpacity: 0.2,
      }).addTo(map);

      const metrics = calcMetrics(pts);
      setFieldBadge(`${metrics.area_ha.toFixed(3)} ha (${metrics.area_m2} m²) | Perimeter: ${metrics.perimeter_m} m`);
      setLocation({ polygon: pts, area_ha: metrics.area_ha });
      setIsDrawing(false);
      setDrawPoints([]);
      drawPointsRef.current = [];
      map.getContainer().style.cursor = "";
    });
  };

  // ── Cancel in-progress drawing only (does NOT touch the stored polygon) ───
  const cancelDrawing = () => {
    const map = mapInstance.current;
    if (map) {
      tempDrawPointsRef.current.forEach((d) => map.removeLayer(d));
      tempDrawPointsRef.current = [];
      if (tempDrawLineRef.current) { map.removeLayer(tempDrawLineRef.current); tempDrawLineRef.current = null; }
      map.getContainer().style.cursor = "";
    }
    setIsDrawing(false);
    setDrawPoints([]);
    drawPointsRef.current = [];
    // Only clear the badge if no finished polygon is in the store
    if (!location.polygon || location.polygon.length < 3) setFieldBadge("");
  };

  // ── Delete finished field (explicit clear of store + map layer) ───────────
  const deleteField = () => {
    cancelDrawing();
    const map = mapInstance.current;
    if (map && drawnPolygonRef.current) {
      map.removeLayer(drawnPolygonRef.current);
      drawnPolygonRef.current = null;
    }
    setFieldBadge("");
    setLocation({ polygon: undefined, area_ha: location.area_ha });
  };

  // ── Fly to & re-draw stored field ("Go to Field") ─────────────────────────
  const handleGoToField = () => {
    const poly = location.polygon;
    const map = mapInstance.current;
    if (!map || !poly || poly.length < 3) return;
    import("leaflet").then((L) => {
      if (!drawnPolygonRef.current) {
        drawnPolygonRef.current = L.polygon(poly, {
          color: "#00e5ff", weight: 3,
          fillColor: "#00e5ff", fillOpacity: 0.2,
        }).addTo(map);
      }
      map.flyToBounds(drawnPolygonRef.current.getBounds(), { padding: [40, 40] });
      const metrics = calcMetrics(poly);
      setFieldBadge(`${metrics.area_ha.toFixed(3)} ha (${metrics.area_m2} m²) | Perimeter: ${metrics.perimeter_m} m`);
    });
  };

  // ── Start Drawing Mode ────────────────────────────────────────────────────
  const startDrawing = () => {
    // Remove finished polygon from map so user draws fresh, but keep store until finish
    const map = mapInstance.current;
    if (map && drawnPolygonRef.current) {
      map.removeLayer(drawnPolygonRef.current);
      drawnPolygonRef.current = null;
    }
    cancelDrawing();
    setIsDrawing(true);
    isDrawingRef.current = true;
    if (map) map.getContainer().style.cursor = "crosshair";
  };

  // ── Pump placement ────────────────────────────────────────────────────────
  const startPumpPlacement = () => {
    setIsDrawing(false);
    isDrawingRef.current = false;
    setIsPlacingPump(true);
    if (mapInstance.current) mapInstance.current.getContainer().style.cursor = "crosshair";
  };

  // ── Zoom / Fit Controls ───────────────────────────────────────────────────
  const handleZoom = (delta: number) => {
    if (mapInstance.current) mapInstance.current.setZoom(mapInstance.current.getZoom() + delta);
  };

  const handleFit = () => {
    const map = mapInstance.current;
    if (!map) return;
    if (drawnPolygonRef.current) map.flyToBounds(drawnPolygonRef.current.getBounds(), { padding: [40, 40] });
    else if (districtLayerRef.current) map.flyToBounds(districtLayerRef.current.getBounds(), { padding: [40, 40] });
    else map.flyTo([-1.9536, 30.0606], 9);
  };

  const handleMyLocation = () => {
    const map = mapInstance.current;
    if (!map) return;
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => map.flyTo([pos.coords.latitude, pos.coords.longitude], 14),
        () => map.flyTo([-1.5, 29.63], 13)
      );
    } else {
      map.flyTo([-1.5, 29.63], 13);
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100%", position: "relative", overflow: "hidden" }}>
      {/* ── Top Bar ── */}
      <div style={{ height: 38, background: "var(--bg-widget)", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 14px", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <MapIcon size={14} color="var(--primary)" />
          <span style={{ color: "var(--text)", fontWeight: "bold", fontSize: 13, letterSpacing: 0.5 }}>
            Rwanda — Farm Location Map
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          {/* Basemap Toggle */}
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ color: "var(--text-dim)", fontSize: 11 }}>Basemap:</span>
            <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 3, overflow: "hidden" }}>
              <button onClick={() => setBasemap("satellite")} style={{ background: basemap === "satellite" ? "var(--primary)" : "transparent", color: basemap === "satellite" ? "#000" : "var(--text-dim)", border: "none", padding: "3px 9px", fontSize: 10, fontWeight: "bold", cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}>
                <Layers size={11} /> Satellite
              </button>
              <button onClick={() => setBasemap("osm")} style={{ background: basemap === "osm" ? "var(--primary)" : "transparent", color: basemap === "osm" ? "#000" : "var(--text-dim)", border: "none", borderLeft: "1px solid var(--border)", padding: "3px 9px", fontSize: 10, fontWeight: "bold", cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}>
                <MapPin size={11} /> OSM
              </button>
            </div>
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)" }}>
            Lat: <span style={{ color: "var(--primary)" }}>{mouseCoords.lat.toFixed(4)}</span>&nbsp;
            Lng: <span style={{ color: "var(--primary)" }}>{mouseCoords.lng.toFixed(4)}</span>
          </div>
        </div>
      </div>

      {/* ── Draw Controls Toolbar ── */}
      <div style={{ height: 36, background: "rgba(5,10,20,0.95)", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 14px", flexShrink: 0 }}>
        <div style={{ color: "var(--text-dim)", fontSize: 11, fontStyle: "italic" }}>
          {isDrawing
            ? `Click map to add boundary points — ${drawPoints.length} pts added. Click 'Finish' when done.`
            : isPlacingPump
            ? "Click on the map to place the water source / pump station."
            : "— Draw your field boundary on the map"}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {isDrawing ? (
            <button className="hud-btn" onClick={finishDrawing} style={{ padding: "3px 12px", fontSize: 11, fontWeight: "bold", background: "var(--accent)", color: "#000", borderColor: "var(--accent)", display: "flex", alignItems: "center", gap: 4 }}>
              <Check size={12} /> Finish Field ({drawPoints.length} pts)
            </button>
          ) : (
            <button className="hud-btn" onClick={startDrawing} style={{ padding: "3px 12px", fontSize: 11, fontWeight: "bold", background: "rgba(0,229,255,0.12)", color: "var(--primary)", borderColor: "var(--primary)", display: "flex", alignItems: "center", gap: 4 }}>
              <Pencil size={12} /> Draw Field
            </button>
          )}
          {/* Cancel in-progress drawing only (shown while drawing) */}
          {isDrawing && (
            <button className="hud-btn" onClick={cancelDrawing} title="Cancel drawing" style={{ padding: "3px 8px", fontSize: 11, background: "#5e1a1a", borderColor: "#aa0000", color: "#fff", display: "flex", alignItems: "center", gap: 4 }}>
              <X size={12} /> Cancel
            </button>
          )}
          {/* Go to Field — shown when a finished polygon is stored */}
          {!isDrawing && location.polygon && location.polygon.length >= 3 && !(location.polygon.length === 4 && location.area_ha === 2.5) && (
            <button className="hud-btn" onClick={handleGoToField} title="Fly to stored field" style={{ padding: "3px 10px", fontSize: 11, background: "rgba(0,229,255,0.18)", color: "var(--primary)", borderColor: "var(--primary)", fontWeight: "bold", display: "flex", alignItems: "center", gap: 4 }}>
              <Crosshair size={12} /> Go to Field
            </button>
          )}
          {/* Delete field — shown when a finished polygon is stored and not currently drawing */}
          {!isDrawing && location.polygon && location.polygon.length >= 3 && !(location.polygon.length === 4 && location.area_ha === 2.5) && (
            <button className="hud-btn" onClick={deleteField} title="Delete field boundary" style={{ padding: "3px 8px", fontSize: 11, background: "#5e1a1a", borderColor: "#aa0000", color: "#fff", display: "flex", alignItems: "center", gap: 4 }}>
              <Trash2 size={12} /> Delete Field
            </button>
          )}
          <button className="hud-btn" onClick={() => handleZoom(1)} title="Zoom In" style={{ padding: "3px 9px", fontSize: 11 }}>
            <ZoomIn size={12} />
          </button>
          <button className="hud-btn" onClick={() => handleZoom(-1)} title="Zoom Out" style={{ padding: "3px 9px", fontSize: 11 }}>
            <ZoomOut size={12} />
          </button>
          <button className="hud-btn" onClick={handleFit} title="Fit View" style={{ padding: "3px 9px", fontSize: 11 }}>
            <Maximize2 size={12} />
          </button>
          <button className="hud-btn" onClick={handleMyLocation} title="My Location" style={{ padding: "3px 10px", fontSize: 11, background: "rgba(0,255,136,0.15)", borderColor: "#00b850", color: "#00ff88", fontWeight: "bold", display: "flex", alignItems: "center", gap: 4 }}>
            <Navigation size={12} /> My Location
          </button>
          <button className="hud-btn" onClick={startPumpPlacement} title="Place pump on map" style={{ padding: "3px 10px", fontSize: 11, background: isPlacingPump ? "var(--primary)" : "rgba(0,229,255,0.1)", color: isPlacingPump ? "#000" : "var(--primary)", borderColor: "var(--primary)", fontWeight: "bold", display: "flex", alignItems: "center", gap: 4 }}>
            <Droplets size={12} /> Pump
          </button>
        </div>
      </div>

      {/* ── Map Canvas ── */}
      <div style={{ flex: 1, position: "relative", minHeight: 0 }}>
        <div ref={mapRef} style={{ width: "100%", height: "100%" }} />

        {/* Field Area Badge */}
        {fieldBadge && (
          <div style={{ position: "absolute", top: 14, left: "50%", transform: "translateX(-50%)", zIndex: 1000, background: "rgba(0,229,255,0.92)", color: "#040711", padding: "6px 18px", borderRadius: 20, fontSize: 12, fontWeight: "bold", fontFamily: "var(--font-mono)", boxShadow: "0 4px 15px rgba(0,229,255,0.4)", pointerEvents: "none", display: "flex", alignItems: "center", gap: 6 }}>
            <Ruler size={13} /> {fieldBadge}
          </div>
        )}


        {/* Pump placement hint */}
        {isPlacingPump && (
          <div style={{ position: "absolute", bottom: 30, left: "50%", transform: "translateX(-50%)", zIndex: 1000, background: "rgba(8,16,32,0.9)", color: "var(--primary)", border: "1px solid var(--primary)", padding: "6px 16px", borderRadius: 4, fontSize: 12, fontWeight: "bold", boxShadow: "0 4px 12px rgba(0,0,0,0.6)", pointerEvents: "none" }}>
            Click anywhere on the map to place the water source / pump
          </div>
        )}

        {/* Bottom-right coords */}
        <div style={{ position: "absolute", bottom: 0, right: 0, zIndex: 1000, background: "rgba(5,10,20,0.85)", borderTop: "1px solid var(--border)", borderLeft: "1px solid var(--border)", padding: "3px 10px", fontSize: 10, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
          Lat: <span style={{ color: "var(--primary)" }}>{mouseCoords.lat.toFixed(4)}</span>&nbsp;
          Lng: <span style={{ color: "var(--primary)" }}>{mouseCoords.lng.toFixed(4)}</span>&nbsp;| Leaflet | Tiles © Esri
        </div>
      </div>
    </div>
  );
}
