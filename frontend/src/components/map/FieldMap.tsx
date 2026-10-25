"use client";

import React, { useEffect, useRef, useState } from "react";
import { useIrriGridStore } from "@/lib/store";
import { calculatePolygonAreaHa } from "@/lib/calculations";
import { MapPin, Trash2, CheckCircle2, Layers } from "lucide-react";

export default function FieldMap() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layerGroupRef = useRef<any>(null);
  const polygonLayerRef = useRef<any>(null);
  const baseTileLayerRef = useRef<any>(null);

  const { location, setLocation } = useIrriGridStore();
  const [isDrawing, setIsDrawing] = useState(false);
  const [points, setPoints] = useState<[number, number][]>(location.polygon || []);
  const [mapType, setMapType] = useState<"satellite" | "streets">("satellite");

  useEffect(() => {
    let isMounted = true;
    let clickHandler: any = null;

    async function initMap() {
      if (typeof window === "undefined" || !mapContainerRef.current) return;

      const L = await import("leaflet");
      await import("leaflet/dist/leaflet.css");

      // Fix leaflet marker default icons
      // @ts-ignore
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      if (mapInstanceRef.current) return;

      const map = L.map(mapContainerRef.current, {
        center: [location.lat || -1.50, location.lon || 29.63],
        zoom: 16,
        maxZoom: 19,
      });
      mapInstanceRef.current = map;

      // Base tile layers
      const satelliteTiles = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { attribution: "Esri World Imagery" }
      );

      const streetTiles = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        { attribution: "© OpenStreetMap contributors" }
      );

      if (mapType === "satellite") {
        satelliteTiles.addTo(map);
        baseTileLayerRef.current = satelliteTiles;
      } else {
        streetTiles.addTo(map);
        baseTileLayerRef.current = streetTiles;
      }

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;

      // Click handler for drawing polygon vertices
      clickHandler = (e: any) => {
        const { lat, lng } = e.latlng;
        setPoints((prev) => {
          const updated = [...prev, [lat, lng] as [number, number]];
          return updated;
        });
      };
      map.on("click", clickHandler);
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        if (clickHandler) {
          mapInstanceRef.current.off("click", clickHandler);
        }
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update polygon and markers when points change
  useEffect(() => {
    if (!mapInstanceRef.current || typeof window === "undefined") return;

    import("leaflet").then((L) => {
      if (!layerGroupRef.current) return;
      layerGroupRef.current.clearLayers();

      // Draw markers on vertices
      points.forEach(([lat, lng], idx) => {
        const circle = L.circleMarker([lat, lng], {
          radius: 6,
          fillColor: "#00e5ff",
          color: "#ffffff",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        });
        circle.bindTooltip(`Point ${idx + 1}`, { permanent: false });
        circle.addTo(layerGroupRef.current);
      });

      // Draw polygon if 3 or more points
      if (points.length >= 3) {
        const polygon = L.polygon(points, {
          color: "#00e5ff",
          weight: 3,
          fillColor: "#00e5ff",
          fillOpacity: 0.25,
          dashArray: isDrawing ? "6, 6" : undefined,
        });
        polygon.addTo(layerGroupRef.current);
        polygonLayerRef.current = polygon;

        // Auto-compute area
        const computedHa = calculatePolygonAreaHa(points);
        if (computedHa > 0) {
          setLocation({
            polygon: points,
            area_ha: computedHa,
            lat: points[0][0],
            lon: points[0][1],
          });
        }
      }
    });
  }, [points, isDrawing]);

  // Map layer toggle
  const toggleMapLayer = async () => {
    if (!mapInstanceRef.current) return;
    const L = await import("leaflet");

    if (baseTileLayerRef.current) {
      mapInstanceRef.current.removeLayer(baseTileLayerRef.current);
    }

    if (mapType === "satellite") {
      const streetTiles = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        { attribution: "© OpenStreetMap contributors" }
      );
      streetTiles.addTo(mapInstanceRef.current);
      baseTileLayerRef.current = streetTiles;
      setMapType("streets");
    } else {
      const satelliteTiles = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { attribution: "Esri World Imagery" }
      );
      satelliteTiles.addTo(mapInstanceRef.current);
      baseTileLayerRef.current = satelliteTiles;
      setMapType("satellite");
    }
  };

  const clearPoints = () => {
    setPoints([]);
    setLocation({ polygon: [] });
    if (layerGroupRef.current) {
      layerGroupRef.current.clearLayers();
    }
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "460px", borderRadius: "6px", overflow: "hidden", border: "1px solid var(--border)" }}>
      <div ref={mapContainerRef} style={{ width: "100%", height: "100%" }} />

      {/* Map Floating Controls */}
      <div
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          zIndex: 1000,
          display: "flex",
          gap: "8px",
          background: "rgba(5, 5, 16, 0.85)",
          padding: "6px 10px",
          borderRadius: "6px",
          border: "1px solid var(--border)",
          backdropFilter: "blur(4px)",
        }}
      >
        <button
          onClick={toggleMapLayer}
          className="btn btn-secondary"
          style={{ padding: "4px 8px", fontSize: "0.75rem" }}
          title="Toggle Satellite / Street Basemap"
        >
          <Layers size={14} />
          {mapType === "satellite" ? "Satellite" : "Street"}
        </button>

        <button
          onClick={clearPoints}
          className="btn btn-secondary"
          style={{ padding: "4px 8px", fontSize: "0.75rem", color: "var(--danger)" }}
          title="Clear polygon points"
        >
          <Trash2 size={14} />
          Clear
        </button>
      </div>

      {/* Map Hint Footer */}
      <div
        style={{
          position: "absolute",
          bottom: 8,
          left: 12,
          zIndex: 1000,
          background: "rgba(5, 5, 16, 0.9)",
          padding: "4px 10px",
          borderRadius: "4px",
          border: "1px solid var(--border)",
          fontSize: "0.75rem",
          fontFamily: "var(--font-mono)",
          color: "var(--text-bright)",
        }}
      >
        {points.length === 0 && "Click anywhere on map to trace boundary vertices"}
        {points.length > 0 && points.length < 3 && `Placed ${points.length} vertices (need at least 3 for area)`}
        {points.length >= 3 && `Traced ${points.length} vertices • Area: ${location.area_ha} ha (${Math.round(location.area_ha * 10000)} m²)`}
      </div>
    </div>
  );
}
