import { useEffect, useRef } from "react";
import { useIrriGridStore } from "./store";
import { fetchWeather, fetchOptimize, fetchSoilProfile } from "./api";
import {
  estimateFAO56ETo,
  calculateMonthlyWaterBalance,
  calculateSoilMoisture,
  generateIrrigationSchedule,
} from "./calculations";

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

// Rwanda two-season rainfall distribution fractions
const RAIN_PATTERN = [
  0.08, 0.10, 0.13, 0.15, 0.10, 0.02,  // Jan-Jun
  0.01, 0.03, 0.08, 0.12, 0.10, 0.08,  // Jul-Dec
];

// Monthly temperature offsets relative to annual mean (Rwanda highland pattern)
const TMIN_OFFSETS = [ 0.5,  0.5,  0.2, -0.2, -0.5, -1.5, -2.0, -1.0,  0.0,  0.2,  0.3,  0.5];
const TMAX_OFFSETS = [ 1.0,  1.0,  0.5, -0.5, -1.0, -1.5, -2.0, -1.0,  0.5,  0.5,  0.5,  0.8];

// The store initialises with a 4-point square at Musanze with area_ha = 2.5.
// Skip optimisation until the user actually traces their own boundary.
function isDefaultPolygon(polygon: [number, number][] | undefined, area_ha: number | undefined) {
  if (!polygon || polygon.length < 3) return true;
  return polygon.length === 4 && area_ha === 2.5;
}

export function useAutoPopulate() {
  const {
    location,
    setMonthlyClimate,
    setSoil,
    monthlyClimate,
    monthlyRainfall,
    crop,
    soil,
    setWaterBalance,
    setScheduleData,
    setDesign,
    setIsOptimizing,
  } = useIrriGridStore();

  const autoPopulatedFor = useRef<string | null>(null);
  const lastOptimizedArea = useRef<number | null>(null);

  // ── 1. Location confirmed → fetch Climate, Rainfall & SoilGrids ────────────
  useEffect(() => {
    if (!location.district || !location.lat || !location.lon) return;
    if (autoPopulatedFor.current === location.district) return;

    const district = location.district;
    autoPopulatedFor.current = district;

    // Weather: backend returns live/cached NASA POWER climatology
    fetchWeather(location.lat, location.lon, location.elevation_m)
      .then((data) => {
        if (data?.monthly_climate && data.monthly_climate.length === 12) {
          setMonthlyClimate(data.monthly_climate);
          if (data?.monthly_rainfall && data.monthly_rainfall.length === 12) {
            useIrriGridStore.setState({ monthlyRainfall: data.monthly_rainfall });
          }
          return;
        }

        const baseTmin = data?.t_min ?? data?.tmin ?? 14;
        const baseTmax = data?.t_max ?? data?.tmax ?? 25;
        const baseHumidity = data?.humidity ?? 75;
        const baseWind = data?.wind_speed_2m ?? data?.wind_speed ?? 2.0;
        const baseSun = data?.solar_radiation_mj ? data.solar_radiation_mj * 0.45 : 6.0;

        const updated = MONTHS.map((month, idx) => {
          const tmin = +(baseTmin + TMIN_OFFSETS[idx]).toFixed(1);
          const tmax = +(baseTmax + TMAX_OFFSETS[idx]).toFixed(1);
          const rhFactor = RAIN_PATTERN[idx] > 0.07 ? 1.08 : 0.92;
          const rhmin = Math.min(85, Math.round(baseHumidity * 0.65 * rhFactor));
          const rhmax = Math.min(98, Math.round(baseHumidity * rhFactor));
          const wind = +(baseWind * (idx < 6 ? 0.9 : 1.1)).toFixed(2);
          const sun  = +(baseSun  * (RAIN_PATTERN[idx] > 0.09 ? 0.82 : 1.05)).toFixed(1);
          const dayOfYear = Math.round(((idx + 0.5) / 12) * 365);
          const eto = estimateFAO56ETo(
            tmin, tmax, rhmin, rhmax, wind, sun,
            location.lat!, location.elevation_m || 1500, dayOfYear
          );
          return { month, tmin, tmax, rhmin, rhmax, wind_speed: wind, sunshine_hours: sun, eto, isAuto: true };
        });
        setMonthlyClimate(updated);
      })
      .catch((err) => console.warn("Auto-populate Climate failed:", err));

    // District rainfall distribution
    fetch("/data/rwanda_districts_data.json")
      .then((r) => r.json())
      .then((all) => {
        const dist = Object.values(all).find(
          (d: any) => d.name.toLowerCase() === district.toLowerCase()
        ) as any;
        if (!dist) return;

        const annualRain = dist.avg_rainfall_mm || 1100;
        useIrriGridStore.setState((state) => {
          const updated = [...state.monthlyRainfall];
          RAIN_PATTERN.forEach((pct, idx) => {
            updated[idx] = {
              ...updated[idx],
              rainfall_mm: Math.round(annualRain * pct),
              effective_rain_mm: Math.round(annualRain * pct * 0.7),
              isAuto: true,
            };
          });
          return { monthlyRainfall: updated };
        });
      })
      .catch((err) => console.warn("Auto-populate Rainfall failed:", err));

    // ISRIC SoilGrids v2.0 automatic lookup with district fallback
    fetchSoilProfile(location.lat, location.lon, district)
      .then((s) => {
        if (s && s.name) {
          setSoil({
            name: s.name,
            texture: s.texture || s.name,
            description: s.description || "",
            field_capacity: s.field_capacity,
            wilting_point: s.wilting_point,
            available_water_mm_m: s.available_water_mm_m,
            max_infiltration_rate: s.max_infiltration_rate,
            source: s.source,
            sand_pct: s.sand_pct,
            silt_pct: s.silt_pct,
            clay_pct: s.clay_pct,
            isAuto: true,
          });
        }
      })
      .catch((err) => console.warn("Auto-populate SoilGrids failed:", err));

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.lat, location.lon, location.district]);

  // ── 2. Climate + Rainfall + Crop + Soil → Water Balance & Schedule ─────────
  useEffect(() => {
    if (!crop.name || !soil.name || monthlyClimate.length === 0) return;

    const waterBal = calculateMonthlyWaterBalance(monthlyClimate, monthlyRainfall, crop);
    setWaterBalance(waterBal);

    const sm = calculateSoilMoisture(
      soil.field_capacity,
      soil.wilting_point,
      crop.root_depth_m,
      crop.depletion_fraction
    );

    const peakEtc = waterBal.slice(3, 8).reduce((s, m) => s + m.etc_mm, 0) / 5;
    const avgDailyEtcMm = Math.max(1.5, peakEtc / 30);
    const totalDays =
      (crop.stages?.initial || 30) + (crop.stages?.development || 40) +
      (crop.stages?.mid || 45) + (crop.stages?.late || 30);

    const sch = generateIrrigationSchedule(
      crop.planting_date || new Date().toISOString().slice(0, 10),
      totalDays, sm.raw, avgDailyEtcMm, 90, 4.0
    );
    setScheduleData(sch.events, {
      intervalDays: sch.intervalDays,
      appNetMm: sch.appNetMm,
      appGrossMm: sch.appGrossMm,
      durationHrs: sch.durationHrs,
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monthlyClimate, monthlyRainfall, crop.name, soil.name]);

  // ── 3. User-traced field boundary → Auto-run NSGA-II Optimisation ──────────
  useEffect(() => {
    if (isDefaultPolygon(location.polygon, location.area_ha)) return;
    if (!crop.name || !location.area_ha) return;
    if (lastOptimizedArea.current === location.area_ha) return;

    lastOptimizedArea.current = location.area_ha;
    setIsOptimizing(true);

    const waterSourceCoords = location.water_source
      ? [location.water_source[0], location.water_source[1]] as [number, number]
      : undefined;

    fetchOptimize({
      crop_name: crop.name,
      soil_type: soil.name,
      location_name: location.district ? `${location.district}, Rwanda` : "Rwanda",
      field_area_ha: location.area_ha,
      polygon_coordinates: location.polygon,
      water_source_coords: waterSourceCoords,
      slope_percent: location.slope_pct || 2,
      climate_data: monthlyClimate,
      soil_detail: soil,
      water_balance: useIrriGridStore.getState().waterBalance,
      schedule_summary: useIrriGridStore.getState().scheduleSummary,
    })
      .then(setDesign)
      .catch((err) => console.error("Auto-optimize failed:", err))
      .finally(() => setIsOptimizing(false));

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.area_ha, crop.name, soil.name]);
}

