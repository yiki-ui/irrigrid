"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useIrriGridStore } from "@/lib/store";
import { calculateSoilMoisture, generateIrrigationSchedule } from "@/lib/calculations";
import StatCard from "@/components/common/StatCard";
import StepNav from "@/components/common/StepNav";
import { Calendar, Clock, Droplet, RefreshCw } from "lucide-react";

export default function ScheduleStep() {
  const { crop, soil, monthlyClimate, setScheduleData } = useIrriGridStore();

  const [efficiencyPct, setEfficiencyPct] = useState(90);
  const [appRateMmHr, setAppRateMmHr] = useState(4.0);

  // Calculate soil moisture threshold
  const moisture = useMemo(() => {
    return calculateSoilMoisture(
      soil.field_capacity,
      soil.wilting_point,
      crop.root_depth_m || 0.6,
      crop.depletion_fraction || 0.4
    );
  }, [soil, crop]);

  // Average peak daily ETc (typically 4.0 - 5.0 mm/day for Rwanda vegetables)
  const avgPeakEtc = useMemo(() => {
    const avgEto = monthlyClimate.reduce((s, m) => s + m.eto, 0) / monthlyClimate.length;
    return avgEto * crop.kc_mid;
  }, [monthlyClimate, crop]);

  const totalSeasonDays = (crop.stages.initial || 30) + (crop.stages.development || 40) + (crop.stages.mid || 45) + (crop.stages.late || 30);

  // Generate schedule
  const schedule = useMemo(() => {
    return generateIrrigationSchedule(
      crop.planting_date || "2026-09-15",
      totalSeasonDays,
      moisture.raw,
      avgPeakEtc,
      efficiencyPct,
      appRateMmHr
    );
  }, [crop.planting_date, totalSeasonDays, moisture.raw, avgPeakEtc, efficiencyPct, appRateMmHr]);

  useEffect(() => {
    setScheduleData(schedule.events, {
      intervalDays: schedule.intervalDays,
      appNetMm: schedule.appNetMm,
      appGrossMm: schedule.appGrossMm,
      durationHrs: schedule.durationHrs,
    });
  }, [schedule, setScheduleData]);

  return (
    <div>
      <div className="hud-card">
        <div className="hud-card-header">
          <div className="hud-card-title">
            <Calendar size={18} />
            Step 07: Irrigation Scheduling & Soil Moisture Depletion
          </div>
          <span className="badge-tag">RAW Depletion Model</span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-dim)", marginBottom: "1rem" }}>
          Irrigation events trigger when soil moisture depletes by the Readily Available Water (RAW) limit ({moisture.raw} mm).
          This prevents crop water stress and root hypoxia.
        </p>

        {/* Schedule Metric Cards */}
        <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
          <StatCard
            label="Irrigation Interval"
            value={`Every ${schedule.intervalDays}`}
            unit="days"
            subtext={`RAW (${moisture.raw}mm) / Peak ETc`}
            color="var(--primary)"
          />
          <StatCard
            label="Gross Application"
            value={schedule.appGrossMm}
            unit="mm"
            subtext={`Net: ${schedule.appNetMm} mm`}
            color="var(--accent)"
          />
          <StatCard
            label="Pump Run Duration"
            value={schedule.durationHrs}
            unit="hrs/event"
            subtext={`At ${appRateMmHr} mm/h emitter rate`}
            color="var(--warning)"
          />
          <StatCard
            label="Total Shifts"
            value={schedule.events.length}
            unit="irrigations"
            subtext={`Over ${totalSeasonDays} day cycle`}
          />
        </div>

        {/* Operating Controls */}
        <div className="grid-2" style={{ marginBottom: "1.25rem" }}>
          <div className="form-group">
            <label className="form-label">System Application Rate (mm/hour)</label>
            <input
              type="number"
              step="0.5"
              min="1"
              max="20"
              className="form-input"
              value={appRateMmHr}
              onChange={(e) => setAppRateMmHr(parseFloat(e.target.value) || 4.0)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Drip Emission Efficiency (%)</label>
            <input
              type="number"
              step="1"
              min="70"
              max="98"
              className="form-input"
              value={efficiencyPct}
              onChange={(e) => setEfficiencyPct(parseFloat(e.target.value) || 90)}
            />
          </div>
        </div>

        {/* Timetable of Events */}
        <div style={{ marginBottom: "0.75rem", fontSize: "0.75rem", color: "var(--primary)", textTransform: "uppercase" }}>
          Operational Field Timetable ({schedule.events.length} Planned Applications)
        </div>

        <div className="hud-table-container">
          <table className="hud-table">
            <thead>
              <tr>
                <th>Event #</th>
                <th>Application Date</th>
                <th>Interval</th>
                <th>Net Water (mm)</th>
                <th>Gross Water (mm)</th>
                <th style={{ color: "var(--accent)" }}>Duration (Hours)</th>
              </tr>
            </thead>
            <tbody>
              {schedule.events.slice(0, 15).map((ev) => (
                <tr key={ev.event_number}>
                  <td style={{ fontWeight: 600, color: "var(--text-bright)" }}>#{ev.event_number}</td>
                  <td>{ev.date}</td>
                  <td>{ev.interval_days} days</td>
                  <td>{ev.application_net_mm} mm</td>
                  <td>{ev.application_gross_mm} mm</td>
                  <td style={{ fontWeight: 700, color: "var(--accent)" }}>{ev.duration_hours} hrs</td>
                </tr>
              ))}
            </tbody>
          </table>
          {schedule.events.length > 15 && (
            <div style={{ padding: "0.5rem 0.75rem", fontSize: "0.72rem", color: "var(--text-dim)", textAlign: "center" }}>
              Showing first 15 events of {schedule.events.length} total season irrigations. Full schedule is included in the executive PDF report.
            </div>
          )}
        </div>
      </div>

      <StepNav />
    </div>
  );
}
