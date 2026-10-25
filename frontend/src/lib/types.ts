export interface MonthlyClimate {
  month: string;
  tmin: number;
  tmax: number;
  rhmin: number;
  rhmax: number;
  wind_speed: number;
  sunshine_hours: number;
  eto: number;
  isAuto?: boolean;
}

export interface MonthlyRainfall {
  month: string;
  rainfall_mm: number;
  effective_rain_mm: number;
  isAuto?: boolean;
}

export interface CropStageData {
  initial: number;
  development: number;
  mid: number;
  late: number;
}

export interface CropData {
  name: string;
  category?: string;
  kc_init: number;
  kc_mid: number;
  kc_end: number;
  root_depth_m: number;
  depletion_fraction: number;
  stages: CropStageData;
  planting_date: string;
  harvest_date: string;
  ndvi?: number;
  ndvi_status?: string;
}

export interface SoilData {
  name: string;
  texture?: string;
  description?: string;
  field_capacity: number; // m3/m3 or %
  wilting_point: number;
  available_water_mm_m: number;
  max_infiltration_rate: number; // mm/h
  source?: string;
  sand_pct?: number;
  silt_pct?: number;
  clay_pct?: number;
  isAuto?: boolean;
}


export interface MonthlyWaterBalance {
  month: string;
  // New field names (used by WaterPanel & calculateMonthlyWaterBalance)
  eto_mm: number;
  kc: number;
  etc_mm: number;
  rainfall_mm: number;
  effective_rain_mm: number;
  net_irrigation_mm: number;
  // Legacy field names (used by WaterStep)
  eto_mm_day: number;
  etc_mm_month: number;
  nir_mm: number;
  nir_m3: number;
}

export interface ScheduleEvent {
  event_number: number;
  date: string;
  interval_days: number;
  application_net_mm: number;
  application_gross_mm: number;
  duration_hours: number;
}

export interface BOMItem {
  category: string;
  item: string;
  specification: string;
  quantity: number;
  unit: string;
  unit_price_rwf: number;
  total_rwf: number;
}

export interface IrrigationDesign {
  design_id?: string;
  pdf_url?: string;
  status?: string;
  crop?: string;
  field_area_ha?: number;
  slope_percent?: number;
  total_candidates_passing?: number;
  eu_threshold_used?: number;
  recommended_design?: {
    lateral_diameter_mm: number;
    main_diameter_mm: number;
    emitter_spacing_m: number;
    lateral_spacing_m: number;
    emitter_flow_lph: number;
    emission_uniformity_percent: number;
    uniformity_coefficient_percent: number;
    total_dynamic_head_m: number;
    pump_power_kw: number;
    flow_rate_m3h: number;
    total_cost_rwf: number;
    num_laterals: number;
    emitters_per_lateral: number;
    total_emitters: number;
    bom: Array<{ item: string; quantity: string; cost_rwf: number }>;
  };
  layout_geometry?: any;
  // Legacy shape kept for backward compat
  optimal_design?: any;
  bom?: BOMItem[];
  pareto_frontier?: Array<{ cost_rwf: number; eu_pct: number; pump_kw: number }>;
}

export interface LocationState {
  polygon: [number, number][]; // [lat, lon]
  area_ha: number;
  district: string;
  province: string;
  sector?: string;
  cell?: string;
  elevation_m: number;
  slope_pct: number;
  lat: number;
  lon: number;
  water_source?: [number, number];
}
