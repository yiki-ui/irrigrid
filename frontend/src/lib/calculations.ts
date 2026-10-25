/**
 * Core agronomic and geometric calculations ported from IrriDSS Python core.
 */

// Earth radius in meters
const EARTH_RADIUS = 6378137;

/**
 * Calculates field area in hectares from polygon coordinates [lat, lon]
 * using spherical excess or equirectangular projection around mean latitude.
 */
export function calculatePolygonAreaHa(coords: [number, number][]): number {
  if (!coords || coords.length < 3) return 0;

  // Compute mean latitude in radians
  const meanLat = (coords.reduce((acc, c) => acc + c[0], 0) / coords.length) * (Math.PI / 180);
  const cosLat = Math.cos(meanLat);

  // Convert lat/lon degrees to meters
  const points = coords.map(([lat, lon]) => ({
    x: lon * (Math.PI / 180) * EARTH_RADIUS * cosLat,
    y: lat * (Math.PI / 180) * EARTH_RADIUS,
  }));

  // Standard Shoelace formula in meters squared
  let areaM2 = 0;
  for (let i = 0; i < points.length; i++) {
    const j = (i + 1) % points.length;
    areaM2 += points[i].x * points[j].y - points[j].x * points[i].y;
  }
  areaM2 = Math.abs(areaM2) / 2.0;

  // Convert m² to hectares (1 ha = 10,000 m²)
  const ha = areaM2 / 10000;
  return Math.round(ha * 1000) / 1000; // 3 decimal places
}

/**
 * USDA SCS method for monthly effective rainfall.
 * @param rainMm Monthly total rainfall in mm
 */
export function calculateEffectiveRainfall(rainMm: number): number {
  if (rainMm <= 0) return 0;
  if (rainMm <= 250) {
    const eff = (rainMm * (125 - 0.2 * rainMm)) / 125;
    return Math.max(0, Math.round(eff * 10) / 10);
  }
  const eff = 125 + 0.1 * rainMm;
  return Math.round(eff * 10) / 10;
}

/**
 * FAO-56 Penman-Monteith client-side ETo estimation formula.
 */
export function estimateFAO56ETo(
  tmin: number,
  tmax: number,
  rhmin: number,
  rhmax: number,
  windSpeed: number,
  sunshineHours: number,
  latitude: number = -1.5,
  elevation: number = 1500,
  dayOfYear: number = 180
): number {
  const tmean = (tmin + tmax) / 2;
  const p = 101.3 * Math.pow((293 - 0.0065 * elevation) / 293, 5.26);
  const gamma = 0.000665 * p;

  // Saturation vapor pressure
  const es_tmax = 0.6108 * Math.exp((17.27 * tmax) / (tmax + 237.3));
  const es_tmin = 0.6108 * Math.exp((17.27 * tmin) / (tmin + 237.3));
  const es = (es_tmax + es_tmin) / 2;

  // Actual vapor pressure
  const ea = (es_tmin * (rhmax / 100) + es_tmax * (rhmin / 100)) / 2;

  // Slope of vapor pressure curve
  const delta = (4098 * (0.6108 * Math.exp((17.27 * tmean) / (tmean + 237.3)))) / Math.pow(tmean + 237.3, 2);

  // Solar radiation estimation
  const phi = (Math.PI / 180) * latitude;
  const dr = 1 + 0.033 * Math.cos((2 * Math.PI * dayOfYear) / 365);
  const decl = 0.409 * Math.sin((2 * Math.PI * dayOfYear) / 365 - 1.39);
  const ws = Math.acos(Math.max(-1, Math.min(1, -Math.tan(phi) * Math.tan(decl))));
  const ra = ((24 * 60) / Math.PI) * 0.082 * dr * (ws * Math.sin(phi) * Math.sin(decl) + Math.cos(phi) * Math.cos(decl) * Math.sin(ws));

  // Max daylight hours
  const N = (24 / Math.PI) * ws;
  const rs = (0.25 + 0.5 * (Math.min(sunshineHours, N) / Math.max(1, N))) * ra;
  const rns = (1 - 0.23) * rs;

  // Net longwave radiation
  const sigma = 4.903e-9;
  const tmaxK4 = Math.pow(tmax + 273.16, 4);
  const tminK4 = Math.pow(tmin + 273.16, 4);
  const rso = (0.75 + 2e-5 * elevation) * ra;
  const rnl = sigma * ((tmaxK4 + tminK4) / 2) * (0.34 - 0.14 * Math.sqrt(Math.max(0.1, ea))) * (1.35 * Math.min(1, rs / Math.max(0.001, rso)) - 0.35);

  const rn = rns - rnl;
  const g = 0; // Daily soil heat flux

  // Penman-Monteith equation
  const num = 0.408 * delta * (rn - g) + gamma * (900 / (tmean + 273)) * windSpeed * (es - ea);
  const den = delta + gamma * (1 + 0.34 * windSpeed);
  const eto = num / den;

  return Math.max(0.5, Math.round(eto * 100) / 100);
}

/**
 * Computes Total Available Water (TAW, mm) and Readily Available Water (RAW, mm)
 */
export function calculateSoilMoisture(
  fieldCapacity: number,
  wiltingPoint: number,
  rootDepthM: number = 0.6,
  p: number = 0.5
) {
  // Available water capacity in mm per meter depth
  const fc = fieldCapacity > 1 ? fieldCapacity / 100 : fieldCapacity;
  const wp = wiltingPoint > 1 ? wiltingPoint / 100 : wiltingPoint;
  const tawMmPerM = 1000 * Math.max(0.05, fc - wp);
  const taw = Math.round(tawMmPerM * rootDepthM * 10) / 10;
  const raw = Math.round(taw * p * 10) / 10;
  return { tawMmPerM: Math.round(tawMmPerM), taw, raw };
}

/**
 * Computes Irrigation Schedule events for the crop cycle
 */
export function generateIrrigationSchedule(
  plantingDateStr: string,
  totalSeasonDays: number,
  rawMm: number,
  avgDailyEtcMm: number,
  irrigationEfficiencyPct: number = 90,
  applicationRateMmHr: number = 4.0
) {
  const events = [];
  const eff = irrigationEfficiencyPct / 100;
  // Interval between irrigations based on RAW depletion
  const intervalDays = Math.max(2, Math.min(10, Math.floor(rawMm / Math.max(1, avgDailyEtcMm))));
  const appNetMm = Math.round(rawMm * 10) / 10;
  const appGrossMm = Math.round((appNetMm / eff) * 10) / 10;
  const durationHrs = Math.round((appGrossMm / applicationRateMmHr) * 10) / 10;

  const startDate = plantingDateStr ? new Date(plantingDateStr) : new Date();

  let currentDay = intervalDays;
  let eventNum = 1;

  while (currentDay <= totalSeasonDays) {
    const eventDate = new Date(startDate);
    eventDate.setDate(startDate.getDate() + currentDay);

    events.push({
      event_number: eventNum++,
      date: eventDate.toISOString().split("T")[0],
      interval_days: intervalDays,
      application_net_mm: appNetMm,
      application_gross_mm: appGrossMm,
      duration_hours: durationHrs,
    });

    currentDay += intervalDays;
  }

  return {
    intervalDays,
    appNetMm,
    appGrossMm,
    durationHrs,
    events,
  };
}

/**
 * Compute monthly water balance (ETc - effective rain = net irrigation)
 */
export function calculateMonthlyWaterBalance(
  climate: Array<{ month: string; eto: number }>,
  rainfall: Array<{ month: string; rainfall_mm: number; effective_rain_mm: number }>,
  crop: { kc_mid: number; kc_init: number; kc_end: number }
) {
  return climate.map((c, i) => {
    const r = rainfall[i] || { rainfall_mm: 0, effective_rain_mm: 0 };
    let kc = crop.kc_mid;
    if (i < 2) kc = crop.kc_init;
    else if (i >= climate.length - 2) kc = crop.kc_end;
    const etc_mm = parseFloat((c.eto * kc * 30).toFixed(1));
    const net_irrigation_mm = parseFloat(Math.max(0, etc_mm - r.effective_rain_mm).toFixed(1));
    return {
      month: c.month,
      eto_mm: parseFloat((c.eto * 30).toFixed(1)),
      kc,
      etc_mm,
      rainfall_mm: r.rainfall_mm,
      effective_rain_mm: r.effective_rain_mm,
      net_irrigation_mm,
      // legacy aliases for old WaterStep
      eto_mm_day: c.eto,
      etc_mm_month: etc_mm,
      nir_mm: net_irrigation_mm,
      nir_m3: parseFloat((net_irrigation_mm * 10).toFixed(1)),
    };
  });
}
