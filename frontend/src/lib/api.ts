const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDistricts() {
  const res = await fetch(`${API_BASE}/api/v1/districts`);
  if (!res.ok) throw new Error("Failed to load Rwanda districts");
  return res.json();
}

export async function fetchDistrictBaseline(name: string) {
  const res = await fetch(`${API_BASE}/api/v1/districts/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`Failed to load district ${name}`);
  return res.json();
}

export async function fetchWeather(lat: number, lon: number, elevation?: number) {
  const elevParam = elevation ? `&elevation=${elevation}` : "";
  const res = await fetch(`${API_BASE}/api/v1/climate/weather?lat=${lat}&lon=${lon}${elevParam}`);
  if (!res.ok) throw new Error("Failed to load weather data");
  return res.json();
}

export async function fetchNASAClimatology(lat: number, lon: number, elevation?: number) {
  const elevParam = elevation ? `&elevation=${elevation}` : "";
  const res = await fetch(`${API_BASE}/api/v1/climate/climatology?lat=${lat}&lon=${lon}${elevParam}`);
  if (!res.ok) throw new Error("Failed to load NASA POWER climatology");
  return res.json();
}


export async function calculateETo(params: {
  tmin: number;
  tmax: number;
  rhmin: number;
  rhmax: number;
  wind_speed: number;
  sunshine_hours: number;
  latitude: number;
  elevation: number;
  day_of_year?: number;
}) {
  const res = await fetch(`${API_BASE}/api/v1/climate/eto`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Failed to calculate ETo");
  return res.json();
}

export async function fetchCrops() {
  const res = await fetch(`${API_BASE}/api/v1/vegetation/crops`);
  if (!res.ok) throw new Error("Failed to load crops catalog");
  return res.json();
}

export async function fetchSoils() {
  const res = await fetch(`${API_BASE}/api/v1/vegetation/soils`);
  if (!res.ok) throw new Error("Failed to load soils catalog");
  return res.json();
}

export async function fetchSoilProfile(lat: number, lon: number, district?: string) {
  const distParam = district ? `&district=${encodeURIComponent(district)}` : "";
  const res = await fetch(`${API_BASE}/api/v1/vegetation/soil-profile?lat=${lat}&lon=${lon}${distParam}`);
  if (!res.ok) throw new Error("Failed to load soil profile");
  return res.json();
}

export async function fetchNDVI(lat: number, lon: number) {
  const res = await fetch(`${API_BASE}/api/v1/vegetation/ndvi?lat=${lat}&lon=${lon}`);
  if (!res.ok) throw new Error("Failed to load NDVI data");
  return res.json();
}

export interface LayoutGeometryResponse {
  boundary_x: number[];
  boundary_y: number[];
  lateral_segments: [number, number, number, number][];
  emitter_x: number[];
  emitter_y: number[];
  total_emitters: number;
  mainline: [number, number, number, number];
  mainline_length_m: number;
  sub_segments: [number, number, number, number][];
  pump_x: number;
  pump_y: number;
  supply_foot_x: number;
  supply_foot_y: number;
  num_laterals: number;
  total_lateral_m: number;
  area_m2: number;
  area_ha: number;
  mainline_edge_angle_deg: number;
  lateral_spacing_m: number;
  emitter_spacing_m: number;
  field_width_m: number;
  field_height_m: number;
  is_real_polygon: boolean;
}

export async function fetchFieldLayout(payload: {
  polygon_coords?: [number, number][];
  water_source_coords?: [number, number];
  lateral_spacing?: number;
  emitter_spacing?: number;
  field_area_ha?: number;
  lateral_diameter_mm?: number;
  main_diameter_mm?: number;
  emitter_flow_lph?: number;
  emission_uniformity_pct?: number;
}): Promise<LayoutGeometryResponse> {
  const res = await fetch(`${API_BASE}/api/v1/layout/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || "Failed to compute field layout geometry");
  }
  return res.json();
}

export async function optimizeIrrigation(payload: {
  crop_name: string;
  soil_type: string;
  location_name: string;
  field_area_ha?: number;
  polygon_coordinates?: [number, number][];
  water_source_coords?: [number, number];
  slope_percent?: number;
  min_eu_threshold?: number;
  lateral_spacing?: number;
  emitter_spacing?: number;
  layout_image_base64?: string;
  climate_data?: any[];
  soil_detail?: any;
  water_balance?: any[];
  schedule_summary?: any;
}) {
  const res = await fetch(`${API_BASE}/api/v1/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || "Optimization failed");
  }
  return res.json();
}

export function getDesignPdfUrl(designId: string): string {
  if (designId.startsWith("http")) return designId;
  const cleanId = designId
    .replace(/^\/?(api\/v1\/)?optimize\//, "")
    .replace(/\/pdf$/, "");
  return `/api/v1/optimize/${cleanId}/pdf`;
}

// Full-context optimizer function used across panels
export async function fetchOptimize(payload: {
  crop_name: string;
  soil_type?: string;
  location_name?: string;
  field_area_ha?: number;
  polygon_coordinates?: [number, number][];
  water_source_coords?: [number, number];
  slope_percent?: number;
  min_eu_threshold?: number;
  lateral_spacing?: number;
  emitter_spacing?: number;
  layout_image_base64?: string;
  climate_data?: any[];
  soil_detail?: any;
  water_balance?: any[];
  schedule_summary?: any;
}) {
  return optimizeIrrigation({
    soil_type: payload.soil_type || "Loam",
    location_name: payload.location_name || "Rwanda",
    ...payload,
  });
}


export async function askAgronomist(payload: {
  prompt: string;
  crop_name: string;
  location_name: string;
  field_area_ha: number;
  soil_type: string;
}) {
  const res = await fetch(`${API_BASE}/api/v1/ai/advice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to get agronomist advice");
  return res.json();
}

export async function fetchAiStatus(): Promise<{ is_live_llm: boolean; provider: string; model: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/ai/status`);
    if (!res.ok) throw new Error("Status check failed");
    return res.json();
  } catch {
    return { is_live_llm: false, provider: "Offline Rule Engine", model: "Rwanda Agronomic Knowledge Base" };
  }
}

export async function fetchNisrYield(crop: string, district: string) {
  const res = await fetch(`${API_BASE}/api/v1/agronomy/nisr-yield/${encodeURIComponent(crop)}/${encodeURIComponent(district)}`);
  if (!res.ok) return null;
  return res.json();
}

