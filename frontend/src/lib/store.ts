import { create } from "zustand";
import {
  LocationState,
  MonthlyClimate,
  MonthlyRainfall,
  CropData,
  SoilData,
  MonthlyWaterBalance,
  ScheduleEvent,
  IrrigationDesign,
} from "./types";
import { calculateEffectiveRainfall } from "./calculations";
import { fetchNisrYield } from "./api";

const DEFAULT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const INITIAL_CLIMATE: MonthlyClimate[] = [
  { month: "Jan", tmin: 13.5, tmax: 24.2, rhmin: 52, rhmax: 82, wind_speed: 1.8, sunshine_hours: 6.2, eto: 3.8 },
  { month: "Feb", tmin: 13.8, tmax: 24.8, rhmin: 50, rhmax: 80, wind_speed: 1.9, sunshine_hours: 6.5, eto: 4.1 },
  { month: "Mar", tmin: 14.2, tmax: 24.5, rhmin: 58, rhmax: 85, wind_speed: 1.7, sunshine_hours: 5.8, eto: 3.9 },
  { month: "Apr", tmin: 14.5, tmax: 23.8, rhmin: 65, rhmax: 88, wind_speed: 1.5, sunshine_hours: 5.2, eto: 3.5 },
  { month: "May", tmin: 14.0, tmax: 23.5, rhmin: 62, rhmax: 86, wind_speed: 1.6, sunshine_hours: 5.5, eto: 3.4 },
  { month: "Jun", tmin: 12.8, tmax: 24.1, rhmin: 48, rhmax: 78, wind_speed: 1.8, sunshine_hours: 6.8, eto: 3.7 },
  { month: "Jul", tmin: 12.2, tmax: 24.6, rhmin: 44, rhmax: 75, wind_speed: 2.0, sunshine_hours: 7.2, eto: 3.9 },
  { month: "Aug", tmin: 13.1, tmax: 25.2, rhmin: 45, rhmax: 76, wind_speed: 2.1, sunshine_hours: 7.0, eto: 4.2 },
  { month: "Sep", tmin: 13.7, tmax: 24.7, rhmin: 52, rhmax: 81, wind_speed: 1.9, sunshine_hours: 6.3, eto: 4.0 },
  { month: "Oct", tmin: 14.0, tmax: 24.0, rhmin: 60, rhmax: 85, wind_speed: 1.7, sunshine_hours: 5.7, eto: 3.7 },
  { month: "Nov", tmin: 13.9, tmax: 23.6, rhmin: 64, rhmax: 87, wind_speed: 1.6, sunshine_hours: 5.3, eto: 3.5 },
  { month: "Dec", tmin: 13.6, tmax: 23.9, rhmin: 58, rhmax: 84, wind_speed: 1.7, sunshine_hours: 5.9, eto: 3.6 },
];

const INITIAL_RAINFALL: MonthlyRainfall[] = [
  { month: "Jan", rainfall_mm: 75, effective_rain_mm: calculateEffectiveRainfall(75) },
  { month: "Feb", rainfall_mm: 85, effective_rain_mm: calculateEffectiveRainfall(85) },
  { month: "Mar", rainfall_mm: 140, effective_rain_mm: calculateEffectiveRainfall(140) },
  { month: "Apr", rainfall_mm: 185, effective_rain_mm: calculateEffectiveRainfall(185) },
  { month: "May", rainfall_mm: 120, effective_rain_mm: calculateEffectiveRainfall(120) },
  { month: "Jun", rainfall_mm: 35, effective_rain_mm: calculateEffectiveRainfall(35) },
  { month: "Jul", rainfall_mm: 18, effective_rain_mm: calculateEffectiveRainfall(18) },
  { month: "Aug", rainfall_mm: 42, effective_rain_mm: calculateEffectiveRainfall(42) },
  { month: "Sep", rainfall_mm: 90, effective_rain_mm: calculateEffectiveRainfall(90) },
  { month: "Oct", rainfall_mm: 130, effective_rain_mm: calculateEffectiveRainfall(130) },
  { month: "Nov", rainfall_mm: 155, effective_rain_mm: calculateEffectiveRainfall(155) },
  { month: "Dec", rainfall_mm: 95, effective_rain_mm: calculateEffectiveRainfall(95) },
];

const INITIAL_LOCATION: LocationState = {
  polygon: [
    [-1.498, 29.628],
    [-1.498, 29.633],
    [-1.503, 29.633],
    [-1.503, 29.628],
  ],
  area_ha: 2.5,
  district: "Musanze",
  province: "Northern Province",
  sector: "Musanze",
  cell: "Musanze",
  elevation_m: 1850,
  slope_pct: 3.5,
  lat: -1.50,
  lon: 29.63,
};

const INITIAL_CROP: CropData = {
  name: "Tomato",
  category: "Vegetables",
  kc_init: 0.6,
  kc_mid: 1.15,
  kc_end: 0.8,
  root_depth_m: 0.6,
  depletion_fraction: 0.4,
  stages: {
    initial: 30,
    development: 40,
    mid: 45,
    late: 30,
  },
  planting_date: "2026-09-15",
  harvest_date: "2027-02-07",
  ndvi: 0.68,
  ndvi_status: "Healthy / Vigorous",
};

const INITIAL_SOIL: SoilData = {
  name: "Volcanic Loam",
  description: "Fertile volcanic soil typical of Northern Rwanda with high water retention",
  field_capacity: 34,
  wilting_point: 16,
  available_water_mm_m: 180,
  max_infiltration_rate: 25,
};

interface IrriGridStore {
  currentStep: number;
  completedSteps: number[];
  setCurrentStep: (step: number) => void;
  markStepComplete: (step: number) => void;

  sidebarStep: number;
  setSidebarStep: (step: number) => void;

  // Step 1: Location
  location: LocationState;
  setLocation: (loc: Partial<LocationState>) => void;

  // Step 2: Climate
  monthlyClimate: MonthlyClimate[];
  updateClimateMonth: (index: number, updates: Partial<MonthlyClimate>) => void;
  setMonthlyClimate: (data: MonthlyClimate[]) => void;

  // Step 3: Rainfall
  monthlyRainfall: MonthlyRainfall[];
  updateRainfallMonth: (index: number, rainMm: number) => void;
  setMonthlyRainfall: (data: MonthlyRainfall[]) => void;

  // 2D Layout Options
  layout2DOptions: {
    showEmitters: boolean;
    showLaterals: boolean;
    showMainline: boolean;
    showPump: boolean;
    showPressureShading: boolean;
    showDimensions: boolean;
  };
  setLayout2DOption: (key: string, val: boolean) => void;

  // Step 4: Crop
  crop: CropData;
  setCrop: (crop: Partial<CropData>) => void;

  // Step 5: Soil
  soil: SoilData;
  setSoil: (soil: Partial<SoilData>) => void;

  // Step 6: Water Req
  waterBalance: MonthlyWaterBalance[];
  setWaterBalance: (wb: MonthlyWaterBalance[]) => void;

  // Step 7: Schedule
  scheduleEvents: ScheduleEvent[];
  scheduleSummary: {
    intervalDays: number;
    appNetMm: number;
    appGrossMm: number;
    durationHrs: number;
  };
  setScheduleData: (events: ScheduleEvent[], summary: any) => void;

  // Step 8: Design
  design: IrrigationDesign | null;
  setDesign: (design: IrrigationDesign | null) => void;
  isOptimizing: boolean;
  setIsOptimizing: (v: boolean) => void;

  // Health checks (for bottom status bar)
  health: {
    db: "unknown" | "healthy" | "unhealthy";
    ai: "unknown" | "healthy" | "unhealthy";
    gis: "unknown" | "healthy" | "unhealthy";
  };
  setHealth: (key: "db" | "ai" | "gis", status: "healthy" | "unhealthy") => void;
  runHealthChecks: () => Promise<void>;

  // Crop yield (for bottom status bar)
  cropExpectedYield: number | null; // tons/ha
  setCropExpectedYield: (yieldval: number | null) => void;
  fetchCropYield: (cropName: string, district?: string) => Promise<void>;

  // 2D Layout PNG capture (client-side Plotly.toImage for PDF export)
  layoutPngBase64: string | null;
  setLayoutPngBase64: (png: string | null) => void;

  // Reset
  resetAll: () => void;
}


export const useIrriGridStore = create<IrriGridStore>((set) => ({
  currentStep: 1,
  completedSteps: [1],
  setCurrentStep: (step) => set({ currentStep: Math.max(1, Math.min(13, step)) }),
  markStepComplete: (step) =>
    set((state) => ({
      completedSteps: Array.from(new Set([...state.completedSteps, step])),
    })),

  sidebarStep: 1,
  setSidebarStep: (step) => set({ sidebarStep: Math.max(1, Math.min(13, step)) }),

  location: INITIAL_LOCATION,
  setLocation: (loc) =>
    set((state) => ({
      location: { ...state.location, ...loc },
    })),

  monthlyClimate: INITIAL_CLIMATE,
  updateClimateMonth: (index, updates) =>
    set((state) => {
      const updated = [...state.monthlyClimate];
      updated[index] = { ...updated[index], ...updates };
      return { monthlyClimate: updated };
    }),
  setMonthlyClimate: (data) => set({ monthlyClimate: data }),

  monthlyRainfall: INITIAL_RAINFALL,
  updateRainfallMonth: (index, rainMm) =>
    set((state) => {
      const updated = [...state.monthlyRainfall];
      updated[index] = {
        ...updated[index],
        rainfall_mm: rainMm,
        effective_rain_mm: calculateEffectiveRainfall(rainMm),
      };
      return { monthlyRainfall: updated };
    }),
  setMonthlyRainfall: (data) => set({ monthlyRainfall: data }),

  layout2DOptions: {
    showEmitters: true,
    showLaterals: true,
    showMainline: true,
    showPump: true,
    showPressureShading: true,
    showDimensions: true,
  },
  setLayout2DOption: (key, val) =>
    set((state) => ({
      layout2DOptions: { ...state.layout2DOptions, [key]: val },
    })),


  crop: INITIAL_CROP,
  setCrop: (crop) =>
    set((state) => ({
      crop: { ...state.crop, ...crop },
    })),

  soil: INITIAL_SOIL,
  setSoil: (soil) =>
    set((state) => ({
      soil: { ...state.soil, ...soil },
    })),

  waterBalance: [],
  setWaterBalance: (wb) => set({ waterBalance: wb }),

  scheduleEvents: [],
  scheduleSummary: {
    intervalDays: 4,
    appNetMm: 16.2,
    appGrossMm: 18.0,
    durationHrs: 4.5,
  },
  setScheduleData: (events, summary) =>
    set({
      scheduleEvents: events,
      scheduleSummary: summary,
    }),

  design: null,
  setDesign: (design) => set({ design }),
  isOptimizing: false,
  setIsOptimizing: (isOptimizing) => set({ isOptimizing }),

  health: {
    db: "unknown",
    ai: "unknown",
    gis: "unknown",
  },
  setHealth: (key, status) =>
    set((state) => ({
      health: { ...state.health, [key]: status },
    })),
  runHealthChecks: async () => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    // DB health
    try {
      const res = await fetch(`${API_BASE}/health`);
      set((state) => ({
        health: { ...state.health, db: res.ok ? "healthy" : "unhealthy" },
      }));
    } catch {
      set((state) => ({
        health: { ...state.health, db: "unhealthy" },
      }));
    }
    // AI health (lightweight check - just verify endpoint reachable)
    try {
      const res = await fetch(`${API_BASE}/api/v1/ai/advice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: "health", crop_name: "Test", location_name: "Test", field_area_ha: 1, soil_type: "Test" }),
      });
      set((state) => ({
        health: { ...state.health, ai: res.ok ? "healthy" : "unhealthy" },
      }));
    } catch {
      set((state) => ({
        health: { ...state.health, ai: "unhealthy" },
      }));
    }
    // GIS health (check if boundary data loaded - location polygon exists)
    set((state) => ({
      health: {
        ...state.health,
        gis: state.location.polygon && state.location.polygon.length >= 3 ? "healthy" : "unhealthy",
      },
    }));
  },

   cropExpectedYield: null,
   setCropExpectedYield: (yieldVal) => set({ cropExpectedYield: yieldVal }),
   layoutPngBase64: null,
   setLayoutPngBase64: (png) => set({ layoutPngBase64: png }),
   fetchCropYield: async (cropName: string, district?: string) => {
    // First try NISR district-adjusted yield
    if (district) {
      try {
        const data = await fetchNisrYield(cropName, district);
        if (data?.yield_kg_ha) {
          set({ cropExpectedYield: data.yield_kg_ha / 1000 }); // Convert kg/ha to tons/ha
          return;
        }
      } catch {
        // Fall through to generic yield
      }
    }
    // Fallback: fetch crop catalog and get generic expected_yield
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/v1/vegetation/crops`);
      if (res.ok) {
        const crops = await res.json();
        const crop = crops.find((c: any) => c.name.toLowerCase() === cropName.toLowerCase());
        if (crop?.expected_yield) {
          set({ cropExpectedYield: crop.expected_yield });
          return;
        }
      }
    } catch {
      // Ignore
    }
    set({ cropExpectedYield: null });
  },

  resetAll: () =>
    set({
      currentStep: 1,
      completedSteps: [1],
      sidebarStep: 1,
      location: INITIAL_LOCATION,
      monthlyClimate: INITIAL_CLIMATE,
      monthlyRainfall: INITIAL_RAINFALL,
      crop: INITIAL_CROP,
      soil: INITIAL_SOIL,
      waterBalance: [],
      scheduleEvents: [],
      design: null,
      health: { db: "unknown", ai: "unhealthy", gis: "unknown" },
      cropExpectedYield: null,
      layoutPngBase64: null,
    }),
}));
