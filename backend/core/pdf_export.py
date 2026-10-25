#!/usr/bin/env python3
# MUST be set before importing pyplot -- safe on Render (no display)
import matplotlib
matplotlib.use("Agg")

import logging
import traceback
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
)

from backend.core.field_layout import compute_field_layout

logger = logging.getLogger("pdf_export")


def _flt(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _int(val, default=0):
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _generate_layout_image_bytes(
    polygon_coords, water_source_coords, field_area_ha,
    lateral_spacing, emitter_spacing, rec_design, layout_geom=None
):
    """
    Generate print-quality PNG of the 2D irrigation layout using matplotlib Agg.
    Uses object-oriented Figure API and cleans up in a finally block to eliminate memory leaks.
    Adapts DPI and dot density to stay safely within Render's 512 MB RAM limit.
    """
    fig = None
    try:
        import gc
        import resource
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        field_area_ha = _flt(field_area_ha, 0.25)
        lateral_spacing = _flt(lateral_spacing, 1.0)
        emitter_spacing = _flt(emitter_spacing, 0.3)

        # Memory & scale guard: reduce detail for huge fields or tight memory
        peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        if peak_mb > 350.0 or field_area_ha > 30.0:
            dpi = 85
            dot_cap = 1000
        elif field_area_ha > 10.0:
            dpi = 95
            dot_cap = 1500
        else:
            dpi = 110
            dot_cap = 2500

        if layout_geom is not None:
            geom = layout_geom
        else:
            geom = compute_field_layout(
                polygon_coords=polygon_coords,
                lateral_spacing=lateral_spacing,
                emitter_spacing=emitter_spacing,
                field_area_ha=field_area_ha,
                water_source_coords=water_source_coords,
            )

        fig = Figure(figsize=(9, 5.5), dpi=dpi)
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f8fafc")

        # Field boundary
        bx = geom["boundary_x"] + [geom["boundary_x"][0]]
        by = geom["boundary_y"] + [geom["boundary_y"][0]]
        ax.fill(bx, by, color="#e8f5e9", alpha=0.7, zorder=1)
        ax.plot(bx, by, color="#1b5e20", linewidth=2.5, label="Field Boundary", zorder=2)

        # Laterals -- batch draw via single plot call
        lat_xs, lat_ys = [], []
        # If there are excessive laterals on huge fields, sample every Nth line
        segments = geom["lateral_segments"]
        stride = max(1, len(segments) // 300)
        for s in segments[::stride]:
            lat_xs += [s[0], s[2], None]
            lat_ys += [s[1], s[3], None]
        if lat_xs:
            ax.plot(lat_xs, lat_ys, color="#0288d1", linewidth=0.7, alpha=0.6, zorder=3,
                    label=f"Laterals ({lateral_spacing:.1f}m)")

        # Sub-mains
        sub_xs, sub_ys = [], []
        for s in geom["sub_segments"]:
            sub_xs += [s[0], s[2], None]
            sub_ys += [s[1], s[3], None]
        if sub_xs:
            ax.plot(sub_xs, sub_ys, color="#f57c00", linewidth=1.2, linestyle=":", zorder=3,
                    label="Sub-mains")

        # Mainline
        ml = geom["mainline"]
        ml_len = geom.get("mainline_length_m", 0)
        ax.plot([ml[0], ml[2]], [ml[1], ml[3]], color="#e65100", linewidth=4,
                label=f"Mainline ({ml_len}m)", zorder=4)

        # Emitters -- capped to avoid high memory allocation
        if geom["emitter_x"]:
            n = len(geom["emitter_x"])
            step = max(1, n // dot_cap)
            ex = geom["emitter_x"][::step]
            ey = geom["emitter_y"][::step]
            total_em = _int(geom.get("total_emitters"), 0)
            ax.scatter(ex, ey, s=3, color="#01579b", alpha=0.5, zorder=4,
                       label=f"Emitters ({total_em:,})")

        # Pump & Supply line
        ax.plot([geom["pump_x"], geom["supply_foot_x"]],
                [geom["pump_y"], geom["supply_foot_y"]],
                color="#d32f2f", linestyle="--", linewidth=1.5, zorder=5)
        ax.scatter([geom["pump_x"]], [geom["pump_y"]],
                   marker="*", s=280, color="#d32f2f", edgecolor="white",
                   linewidth=0.8, zorder=6, label="Pump / Water Source")

        area_ha = _flt(geom.get("area_ha"), field_area_ha)
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, linestyle="--", alpha=0.35, linewidth=0.5)
        ax.set_xlabel("East-West (metres)", fontsize=9, color="#475569")
        ax.set_ylabel("North-South (metres)", fontsize=9, color="#475569")
        ax.set_title(
            f"2D Field Engineering Layout  --  {area_ha:.3f} ha  |  Mainline snapped to nearest edge",
            fontsize=10, fontweight="bold", color="#1f2937", pad=8
        )
        ax.legend(loc="upper right", fontsize=7.5, framealpha=0.9,
                  edgecolor="#cbd5e1", fancybox=False)
        ax.tick_params(labelsize=8, colors="#475569")
        for spine in ax.spines.values():
            spine.set_edgecolor("#e2e8f0")

        fig.tight_layout(pad=1.0)

        buf = BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf.getvalue()

    except Exception:
        logger.error("Failed to generate 2D layout image for PDF:\n%s", traceback.format_exc())
        return None
    finally:
        if fig is not None:
            fig.clf()
            del fig
        import matplotlib.pyplot as plt
        plt.close("all")
        import gc
        gc.collect()



def generate_irrigation_pdf(
    design_data,
    crop_name="Tomato",
    field_area_ha=0.25,
    location_name="Rwanda",
    soil_type="Loam",
    polygon_coords=None,
    water_source_coords=None,
    layout_image_bytes=None,
    layout_geometry=None,
    climate_data=None,
    soil_detail=None,
    water_balance=None,
    schedule_summary=None,
    output_path=None
):
    """
    Generate complete engineering PDF with all 11 sections.
    Falls back gracefully if 2D layout fails -- never silently skips.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        output_path if output_path else buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "MainTitle", parent=styles["Heading1"], fontSize=18, leading=22,
        textColor=colors.HexColor("#0F5132"), spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "SubTitle", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#495057"), spaceAfter=10
    )
    section_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], fontSize=11, leading=15,
        textColor=colors.HexColor("#0F5132"), spaceBefore=10, spaceAfter=4
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=8.5, leading=12,
        textColor=colors.HexColor("#374151"), spaceAfter=6
    )
    caption_style = ParagraphStyle(
        "FigCaption", parent=styles["Normal"], fontSize=8,
        textColor=colors.HexColor("#6c757d"), alignment=1, spaceBefore=3, spaceAfter=8
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=7.5,
        textColor=colors.HexColor("#94a3b8"), leading=11
    )

    crop_name = crop_name or "Tomato"
    field_area_ha = _flt(field_area_ha, 0.25)
    location_name = location_name or "Rwanda"
    soil_type = soil_type or "Loam"
    design_data = design_data if isinstance(design_data, dict) else {}
    rec = design_data.get("recommended_design") or design_data.get("optimal_design") or design_data
    if not isinstance(rec, dict):
        rec = {}

    lat_spacing = _flt(rec.get("lateral_spacing_m"), 1.0)
    em_spacing = _flt(rec.get("emitter_spacing_m"), 0.3)
    now_str = datetime.now().strftime("%B %d, %Y")

    # Cover
    story.append(Paragraph("<b>Irrigrid -- Drip Irrigation System Design Report</b>", title_style))
    story.append(Paragraph(
        f"Generated: <b>{now_str}</b> &nbsp;|&nbsp; "
        f"Location: <b>{location_name}</b> &nbsp;|&nbsp; "
        f"Field Area: <b>{field_area_ha:.3f} ha ({_int(field_area_ha * 10000):,} m2)</b>",
        subtitle_style
    ))
    story.append(Paragraph(
        "Built for NISR Big Data Hackathon 2026 - Track 1: Agricultural Productivity",
        ParagraphStyle("Tag", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#0F5132"), spaceAfter=4)
    ))
    story.append(Spacer(1, 4))

    # 1. Field & Location
    slope_val = _flt(design_data.get('slope_percent', rec.get('slope_percent')), 2.0)
    story.append(Paragraph("1. Field &amp; Location Parameters", section_style))
    loc_rows = [
        ["Crop Selected:", crop_name, "Soil Type:", soil_type],
        ["Field Area:", f"{field_area_ha:.3f} ha ({_int(field_area_ha * 10000):,} m2)",
         "Terrain Slope:", f"{slope_val:.1f}%"],
        ["Location:", location_name, "Report Date:", now_str],
    ]
    t = Table(loc_rows, colWidths=[120, 150, 110, 160])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # 2. Climate
    story.append(Paragraph("2. Climate -- ETo, Rainfall &amp; Temperature", section_style))
    if climate_data:
        clim_rows = [["Month", "Tmin (C)", "Tmax (C)", "RH (%)", "Wind (m/s)", "ETo (mm/d)"]]
        for m in climate_data:
            if not isinstance(m, dict):
                continue
            clim_rows.append([
                str(m.get("month", "")),
                f"{_flt(m.get('tmin')):.1f}",
                f"{_flt(m.get('tmax')):.1f}",
                f"{_flt(m.get('rhmax')):.0f}",
                f"{_flt(m.get('wind_speed')):.1f}",
                f"{_flt(m.get('eto')):.2f}"
            ])
        tc = Table(clim_rows, colWidths=[50, 70, 70, 55, 75, 80])
        tc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F5132")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ]))
        story.append(tc)
    else:
        story.append(Paragraph("Climate data not available in this report.", body_style))
    story.append(Spacer(1, 6))

    # 3. Crop
    story.append(Paragraph("3. Crop -- Growth Stages &amp; Kc Values", section_style))
    kc_init = _flt(rec.get('kc_init'), 0.6)
    kc_mid = _flt(rec.get('kc_mid'), 1.15)
    kc_end = _flt(rec.get('kc_end'), 0.8)
    crop_root_depth = _flt(rec.get('root_depth_m'), 0.6)
    total_days = _int(rec.get('total_days'), 145)
    depletion_fraction = _flt(rec.get('depletion_fraction'), 0.4)

    crop_rows = [
        ["Crop:", crop_name, "Kc Initial:", f"{kc_init:.2f}"],
        ["Root Depth:", f"{crop_root_depth:.2f} m", "Kc Mid:", f"{kc_mid:.2f}"],
        ["Season Length:", f"{total_days} days", "Kc End:", f"{kc_end:.2f}"],
        ["Depletion (p):", f"{depletion_fraction * 100:.0f}% of FC",
         "Lateral Spacing:", f"{lat_spacing:.2f} m"],
    ]
    tc2 = Table(crop_rows, colWidths=[120, 150, 110, 160])
    tc2.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
    ]))
    story.append(tc2)
    story.append(Spacer(1, 6))

    # 4. Soil
    story.append(Paragraph("4. Soil -- Texture, Water-Holding &amp; Infiltration", section_style))
    sd = soil_detail if isinstance(soil_detail, dict) else {}
    soil_source = sd.get("source", "District default")
    fc_val = _flt(sd.get("field_capacity"), 30.0)
    wp_val = _flt(sd.get("wilting_point"), 15.0)
    inf_rate = _flt(sd.get("max_infiltration_rate"), 13.0)
    root_depth = _flt(sd.get("root_depth_m"), crop_root_depth)

    # Unit normalisation: backend presets are in % (30.0); the frontend may
    # occasionally store m3/m3 (0.30). Detect by magnitude and convert.
    if fc_val <= 1.0:
        fc_val = fc_val * 100.0
    if wp_val <= 1.0:
        wp_val = wp_val * 100.0
    # Infiltration: presets are mm/h. If the value exceeds 100 it was stored
    # in mm/day (e.g. 312 mm/day / 24 = 13 mm/h).
    if inf_rate > 100:
        inf_rate = inf_rate / 24.0

    # Compute TAW and RAW from first principles
    fc_frac = fc_val / 100.0
    wp_frac = wp_val / 100.0
    taw_mm = 1000.0 * max(0.05, fc_frac - wp_frac) * root_depth
    depletion_p = depletion_fraction
    raw_mm = taw_mm * depletion_p

    sand_pct = sd.get("sand_pct")
    silt_pct = sd.get("silt_pct")
    clay_pct = sd.get("clay_pct")
    if sand_pct is not None and silt_pct is not None and clay_pct is not None:
        composition_str = f"Sand {_flt(sand_pct):.0f}% / Silt {_flt(silt_pct):.0f}% / Clay {_flt(clay_pct):.0f}%"
    else:
        composition_str = "Not measured"

    soil_rows = [
        ["Soil Texture:", soil_type, "Source:", soil_source],
        ["Grain composition:", composition_str, "", ""],
        ["Field Capacity (FC):", f"{fc_val:.1f}% ({fc_frac:.3f} m3/m3)", "Wilting Point (WP):", f"{wp_val:.1f}% ({wp_frac:.3f} m3/m3)"],
        ["Max Infiltration:", f"{inf_rate:.1f} mm/h", "Root Depth:", f"{root_depth:.2f} m"],
        ["TAW = 1000*(FC-WP)*Zr:", f"{taw_mm:.1f} mm", "RAW = p*TAW:", f"{raw_mm:.1f} mm (p={depletion_p:.2f})"],
    ]
    ts = Table(soil_rows, colWidths=[130, 130, 130, 150])
    ts.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
    ]))
    story.append(ts)
    story.append(Spacer(1, 6))

    # 5. Water Balance & Schedule
    story.append(Paragraph("5. Crop Water Requirement &amp; Irrigation Schedule", section_style))
    if water_balance:
        wb_rows = [["Month", "ETo (mm/d)", "Kc", "ETc (mm/mo)", "Rain (mm)", "Peff (mm)", "Net Irr (mm)"]]
        for m in water_balance:
            if not isinstance(m, dict):
                continue
            rain = _flt(m.get("rainfall_mm"))
            peff = _flt(m.get("effective_rain_mm"))
            if peff == 0 and rain > 0:
                if rain <= 250:
                    peff = rain * (125 - 0.2 * rain) / 125
                else:
                    peff = 125 + 0.1 * rain
            eto_val = _flt(m.get('eto_mm', m.get('eto_mm_day')))
            kc_val = _flt(m.get('kc'))
            etc_val = _flt(m.get('etc_mm', m.get('etc_mm_month')))
            nir_val = _flt(m.get('net_irrigation_mm', m.get('nir_mm')))
            wb_rows.append([
                str(m.get("month", "")),
                f"{eto_val:.2f}",
                f"{kc_val:.2f}",
                f"{etc_val:.1f}",
                f"{rain:.0f}",
                f"{peff:.0f}",
                f"{nir_val:.1f}",
            ])
        twb = Table(wb_rows, colWidths=[42, 60, 40, 68, 55, 55, 68])
        twb.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F5132")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ]))
        story.append(twb)
    if schedule_summary and isinstance(schedule_summary, dict):
        story.append(Spacer(1, 4))
        interval = schedule_summary.get("intervalDays", "?")
        net_mm = _flt(schedule_summary.get("appNetMm"))
        gross_mm = _flt(schedule_summary.get("appGrossMm"))
        dur_h = _flt(schedule_summary.get("durationHrs"))
        sched_rows = [
            ["Irrigation Interval:", f"{interval} days (floor of RAW/ETc_peak)", "Application (net):", f"{net_mm:.1f} mm"],
            ["Application (gross):", f"{gross_mm:.1f} mm", "Run Time per Zone:", f"{dur_h:.2f} h"],
        ]
        tsch = Table(sched_rows, colWidths=[130, 130, 130, 150])
        tsch.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ]))
        story.append(tsch)
    story.append(Spacer(1, 6))

    # 6. Hydraulic Design — pipes, emitters, zones, pump, TDH
    story.append(Paragraph("6. Hydraulic Design -- Pipes, Emitters, Zones &amp; Pump", section_style))

    n_zones = _int(rec.get("num_zones"), 1)
    q_zone = _flt(rec.get("flow_per_zone_m3h", rec.get("flow_rate_m3h")), 0.0)
    app_rate = _flt(rec.get("application_rate_mmh"), 0.0)
    run_time = _flt(rec.get("run_time_per_zone_h"), 0.0)
    if schedule_summary and isinstance(schedule_summary, dict) and schedule_summary.get("durationHrs") is not None:
        run_time = _flt(schedule_summary.get("durationHrs"), run_time)
    main_vel = _flt(rec.get("mainline_velocity_ms"), 0.0)
    max_lat_len = _flt(rec.get("max_lateral_length_m"), 0.0)
    lat_diam = _int(rec.get('lateral_diameter_mm'), 16)
    main_diam = _int(rec.get('main_diameter_mm'), 50)
    em_flow = _flt(rec.get('emitter_flow_lph'), 2.0)
    tot_lat = _int(rec.get('num_laterals'), 0)
    tot_emitters = _int(rec.get('total_emitters'), 0)
    tot_flow = _flt(rec.get('flow_rate_m3h'), 0.0)
    pumping_window = _flt(rec.get('daily_pumping_window_h'), 12.0)
    tdh_dict = rec.get('tdh_breakdown') if isinstance(rec.get('tdh_breakdown'), dict) else {}
    op_m = _flt(tdh_dict.get('operating_pressure_m'), 10.2)
    pump_kw = _flt(rec.get('pump_power_kw'), 0.75)
    pump_eff = _flt(rec.get('pump_efficiency'), 0.65)

    hydraulic_rows = [
        ["Lateral Diameter:", f"{lat_diam} mm LDPE",
         "Mainline Diameter:", f"{main_diam} mm HDPE/PVC"],
        ["Emitter Spacing:", f"{em_spacing:.2f} m",
         "Lateral Row Spacing:", f"{lat_spacing:.2f} m"],
        ["Emitter Flow Rate:", f"{em_flow:.1f} L/hr",
         "Application Rate:", f"{app_rate:.2f} mm/h"],
        ["Total Laterals:", f"{tot_lat} lines",
         "Max Lateral Length:", f"{max_lat_len:.1f} m"],
        ["Total System Flow:", f"{tot_flow:.2f} m3/hr",
         "Total Field Emitters:", f"{tot_emitters:,} units"],
        ["Number of Zones:", f"{n_zones}",
         "Flow per Zone:", f"{q_zone:.2f} m3/hr"],
        ["Run Time per Zone:", f"{run_time:.2f} h",
         "Daily Pumping Window:", f"{pumping_window:.0f} h"],
        ["Mainline Velocity:", f"{main_vel:.2f} m/s (max 1.5)",
         "Operating Pressure:", f"{op_m / 10.2:.1f} bar"],
        ["Pump Power Required:", f"{pump_kw:.2f} kW (η={pump_eff:.2f})",
         "Filter Required:", "120-mesh disc filter"],
    ]
    th = Table(hydraulic_rows, colWidths=[120, 150, 120, 150])
    th.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CED4DA")),
    ]))
    story.append(th)

    # TDH breakdown sub-table
    tdh = rec.get("tdh_breakdown")
    if tdh and isinstance(tdh, dict):
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Total Dynamic Head (TDH) Breakdown:</b>", body_style))
        tdh_rows = [
            ["Component", "Head (m)"],
            ["Operating Pressure", f"{_flt(tdh.get('operating_pressure_m')):.2f}"],
            ["Lateral Friction Loss", f"{_flt(tdh.get('lateral_friction_m')):.2f}"],
            ["Mainline Friction Loss", f"{_flt(tdh.get('mainline_friction_m')):.2f}"],
            ["Filter Head Loss", f"{_flt(tdh.get('filter_loss_m')):.2f}"],
            ["Elevation Head", f"{_flt(tdh.get('elevation_head_m')):.2f}"],
            ["TOTAL TDH", f"{_flt(tdh.get('total_dynamic_head_m')):.2f}"],
        ]
        ttdh = Table(tdh_rows, colWidths=[200, 100])
        ttdh.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F5132")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E9ECEF")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ]))
        story.append(ttdh)
    story.append(Spacer(1, 6))

    # 7. Hydraulic Analysis — EU and UC as distinct values
    story.append(Paragraph("7. Hydraulic Analysis Results", section_style))
    eu = _flt(rec.get("emission_uniformity_percent"), 90.0)
    uc = _flt(rec.get("uniformity_coefficient_percent"), 95.0)
    eu_thresh = _flt(design_data.get('eu_threshold_used'), 90.0)
    candidates_count = _int(design_data.get('total_candidates_passing'), 0)
    analysis_rows = [
        ["Emission Uniformity (EU):", f"{eu:.1f}%  (Keller-Karmeli: q_min/q_avg)",
         "Uniformity Coefficient (UC):", f"{uc:.1f}%  (Christiansen)"],
        ["EU Threshold Used:", f"{eu_thresh:.0f}%",
         "Configs Evaluated:", f"{candidates_count}"],
        ["Relationship:", "EU ≤ UC always holds",
         "Optimization Method:", "Exhaustive grid search"],
    ]
    ta = Table(analysis_rows, colWidths=[130, 140, 130, 140])
    ta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FFF4")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBF7D0")),
    ]))
    story.append(ta)
    story.append(Spacer(1, 6))

    # 8. 2D Layout
    story.append(PageBreak())
    story.append(Paragraph("8. 2D Field Engineering Layout", section_style))

    if layout_image_bytes is None:
        layout_image_bytes = _generate_layout_image_bytes(
            polygon_coords=polygon_coords,
            water_source_coords=water_source_coords,
            field_area_ha=field_area_ha,
            lateral_spacing=lat_spacing,
            emitter_spacing=em_spacing,
            rec_design=rec,
            layout_geom=layout_geometry
        )

    layout_rendered = False
    if layout_image_bytes:
        try:
            from reportlab.lib.utils import ImageReader
            ir = ImageReader(BytesIO(layout_image_bytes))
            ir.getSize()  # Validates image format and dimensions
            img = Image(BytesIO(layout_image_bytes), width=6.8 * inch, height=4.1 * inch)
            story.append(img)
            story.append(Paragraph(
                f"<b>Figure 1:</b> 2D engineering layout generated server-side. "
                f"Mainline (orange) {rec.get('mainline_length_m', '')}m snapped to nearest field edge. "
                f"{rec.get('num_laterals', '')} laterals (blue) at {lat_spacing:.2f}m spacing, "
                f"{tot_emitters:,} emitters at {em_spacing:.2f}m. "
                f"Pump sized for zone flow {q_zone:.1f} m3/h.",
                caption_style
            ))
            layout_rendered = True
        except Exception as e:
            logger.warning("Could not embed layout image into PDF: %s", e)
            layout_rendered = False

    if not layout_rendered:
        # Plain text for farmers — real traceback is already in the server log.
        story.append(Paragraph(
            "<b>Notice:</b> The 2D layout could not be drawn. "
            "The engineering calculations, water requirements, and bill of materials "
            "in this report are complete and accurate.",
            ParagraphStyle("Warn", parent=styles["Normal"], fontSize=9,
                           textColor=colors.HexColor("#b91c1c"), spaceAfter=8)
        ))
    story.append(Spacer(1, 6))

    # 9. BOM
    story.append(Paragraph("9. Bill of Materials &amp; Estimated Cost (RWF)", section_style))
    bom_data = [["Equipment Item", "Quantity", "Estimated Cost (RWF)"]]
    bom_total_check = 0
    for item in rec.get("bom", []):
        if not isinstance(item, dict):
            continue
        cost = _int(item.get('cost_rwf', 0))
        bom_total_check += cost
        bom_data.append([str(item.get("item", "")), str(item.get("quantity", "")), f"{cost:,} RWF"])
    total_cost = _int(rec.get("total_cost_rwf", bom_total_check), bom_total_check)
    bom_data.append(["TOTAL ESTIMATED INVESTMENT", "", f"{total_cost:,} RWF"])
    tbom = Table(bom_data, colWidths=[250, 120, 170])
    tbom.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F5132")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E9ECEF")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(tbom)
    story.append(Spacer(1, 8))

    # 10. O&M
    story.append(Paragraph("10. Operation &amp; Maintenance Protocols", section_style))
    notes = (
        "- Filtration: Clean disc filter cartridge at least twice weekly during peak pumping season.<br/>"
        "- Flushing: Open submain and lateral end-caps for 2 minutes every two weeks to flush silt.<br/>"
        "- Pressure check: Verify lateral end pressure stays above 0.8 bar with a portable gauge.<br/>"
        "- Emitter inspection: Walk laterals monthly; replace clogged emitters immediately.<br/>"
        "- Seasonal shutdown: Drain all pipes at end of dry season to prevent algal buildup."
    )
    story.append(Paragraph(
        notes,
        ParagraphStyle("Notes", parent=styles["Normal"],
                       fontSize=8.5, leading=13, textColor=colors.HexColor("#374151"))
    ))
    story.append(Spacer(1, 10))

    # 11. Footer / Data Sources
    story.append(Paragraph(
        "Data sources &amp; credits",
        ParagraphStyle("FootHead", parent=styles["Normal"], fontSize=8,
                       fontName="Helvetica-Bold",
                       textColor=colors.HexColor("#6b7280"), spaceAfter=3)
    ))
    story.append(Paragraph(
        "- Climate &amp; ETo: NASA POWER (Prediction of Worldwide Energy Resources), FAO-56 Penman-Monteith.<br/>"
        "- Soil data: ISRIC SoilGrids v2.0 (rest.isric.org) or district defaults where unavailable.<br/>"
        "- Agricultural baselines: <b>National Institute of Statistics of Rwanda (NISR)</b> -- "
        "Seasonal Agricultural Survey (SAS) 2024/2025.<br/>"
        "- Hydraulic optimisation: NSGA-II multi-objective algorithm (pymoo).<br/>"
        "- Disclaimer: All values are design estimates. Site verification by a licensed irrigation engineer is recommended.",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue() if not output_path else b""


if __name__ == "__main__":
    from backend.core.optimizer import optimize_irrigation_system
    opt = optimize_irrigation_system(0.25, 2.0, "Tomato",
                                      field_length_m=50.0, field_width_m=50.0)
    pdf_bytes = generate_irrigation_pdf(opt, "Tomato", 0.25, "Musanze, Rwanda",
                                        output_path="test_report.pdf")
    print(f"Generated test_report.pdf. Size: {len(pdf_bytes)} bytes")

