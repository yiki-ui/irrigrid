#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Routes: 2D Field Layout
  POST /api/v1/layout/compute   → geometry JSON (used by frontend Plotly)
  POST /api/v1/layout/image     → PNG bytes of the layout (used by PDF export)
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
import numpy as np

from backend.core.field_layout import compute_field_layout

router = APIRouter(prefix="/layout", tags=["2D Field Layout"])


class LayoutRequest(BaseModel):
    polygon_coords: Optional[List[List[float]]] = None   # [[lat, lon], ...]
    water_source_coords: Optional[List[float]] = None    # [lat, lon]
    lateral_spacing: float = Field(default=1.0, gt=0)
    emitter_spacing: float = Field(default=0.3, gt=0)
    field_area_ha: float = Field(default=0.5, gt=0)
    # Hydraulic parameters (for annotations in image export)
    lateral_diameter_mm: Optional[float] = None
    main_diameter_mm: Optional[float] = None
    emitter_flow_lph: Optional[float] = None
    emission_uniformity_pct: Optional[float] = None


@router.post("/compute")
def compute_layout(req: LayoutRequest) -> dict:
    """Compute 2D field layout geometry. Returns trace data for the frontend."""
    return compute_field_layout(
        polygon_coords=req.polygon_coords,
        lateral_spacing=req.lateral_spacing,
        emitter_spacing=req.emitter_spacing,
        field_area_ha=req.field_area_ha,
        water_source_coords=req.water_source_coords,
    )


@router.post("/image")
def layout_image(req: LayoutRequest) -> Response:
    """
    Generate a static PNG of the 2D field layout using Plotly + Kaleido.
    Returns image/png bytes — embedded directly into the PDF report.
    """
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
    except ImportError:
        raise HTTPException(500, "plotly not installed")

    geom = compute_field_layout(
        polygon_coords=req.polygon_coords,
        lateral_spacing=req.lateral_spacing,
        emitter_spacing=req.emitter_spacing,
        field_area_ha=req.field_area_ha,
        water_source_coords=req.water_source_coords,
    )

    fig = go.Figure()

    # ── Field boundary ────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=geom["boundary_x"], y=geom["boundary_y"],
        mode="lines",
        line=dict(color="#00ffc8", width=2.5),
        fill="toself",
        fillcolor="rgba(0,255,200,0.07)",
        name="Field Boundary",
        hoverinfo="skip",
    ))

    # ── Drip Laterals ─────────────────────────────────────────────────────────
    lat_x, lat_y = [], []
    for s in geom["lateral_segments"]:
        lat_x += [s[0], s[2], None]
        lat_y += [s[1], s[3], None]

    if lat_x:
        fig.add_trace(go.Scatter(
            x=lat_x, y=lat_y,
            mode="lines",
            line=dict(color="#00e5ff", width=1.3),
            name=f"Laterals ({req.lateral_spacing} m spacing)",
            hoverinfo="skip",
        ))

    # ── Sub-main connectors ────────────────────────────────────────────────────
    sub_x, sub_y = [], []
    for s in geom["sub_segments"]:
        sub_x += [s[0], s[2], None]
        sub_y += [s[1], s[3], None]

    if sub_x:
        fig.add_trace(go.Scatter(
            x=sub_x, y=sub_y,
            mode="lines",
            line=dict(color="#ffb74d", width=1.2, dash="dot"),
            name="Sub-mains",
            hoverinfo="skip",
        ))

    # ── Mainline (snapped to nearest edge) ────────────────────────────────────
    ml = geom["mainline"]
    fig.add_trace(go.Scatter(
        x=[ml[0], ml[2]], y=[ml[1], ml[3]],
        mode="lines",
        line=dict(color="#ffa726", width=4.5),
        name=f"Mainline — snapped ({geom['mainline_length_m']:.0f} m)",
        hoverinfo="skip",
    ))

    # ── Emitters ──────────────────────────────────────────────────────────────
    if geom["emitter_x"]:
        fig.add_trace(go.Scatter(
            x=geom["emitter_x"], y=geom["emitter_y"],
            mode="markers",
            marker=dict(size=3, color="#00e5ff", opacity=0.7, symbol="circle"),
            name=f"Emitters ({geom['total_emitters']:,} @ {req.emitter_spacing} m)",
            hoverinfo="skip",
        ))

    # ── Pump / Water source ────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[geom["pump_x"]], y=[geom["pump_y"]],
        mode="markers+text",
        marker=dict(symbol="star", size=16, color="#29b6f6", line=dict(color="#fff", width=1.5)),
        text=["Pump / Source"],
        textposition="top center",
        textfont=dict(color="#29b6f6", size=10),
        name="Pump & Filtration Head",
        hoverinfo="skip",
    ))

    # Supply line: pump → mainline foot
    fig.add_trace(go.Scatter(
        x=[geom["pump_x"], geom["supply_foot_x"]],
        y=[geom["pump_y"], geom["supply_foot_y"]],
        mode="lines",
        line=dict(color="#29b6f6", width=2, dash="dash"),
        showlegend=False,
        hoverinfo="skip",
    ))

    # ── Annotations: Field Summary box ────────────────────────────────────────
    eu = req.emission_uniformity_pct or 91.5
    em_flow = req.emitter_flow_lph or 2.0
    design_flow = (geom["total_emitters"] * em_flow) / 1000.0

    fig.add_annotation(
        x=0.01, y=0.99, xref="paper", yref="paper",
        text=(
            f"<b style='color:#00ffc8'>FIELD SUMMARY</b><br><br>"
            f"Area:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<b>{geom['area_ha']:.3f} ha ({geom['area_m2']:,} m²)</b><br>"
            f"Laterals:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<b>{geom['num_laterals']}</b><br>"
            f"Emitters:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<b>{geom['total_emitters']:,}</b><br>"
            f"Lateral spacing:&nbsp;&nbsp;<b>{req.lateral_spacing} m</b><br>"
            f"Emitter spacing:&nbsp;&nbsp;<b>{req.emitter_spacing} m</b><br>"
            f"Mainline length:&nbsp;&nbsp;<b>{geom['mainline_length_m']:.0f} m</b><br>"
            f"Edge angle:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<b>{geom['mainline_edge_angle_deg']:.1f}°</b><br>"
            f"Snapped:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<span style='color:#00ffc8'><b>YES</b></span>"
        ),
        showarrow=False, align="left",
        bgcolor="rgba(10,17,30,0.88)",
        bordercolor="rgba(0,255,200,0.35)", borderwidth=1, borderpad=12,
        font=dict(size=10, color="#e0e0e0", family="monospace"),
        xanchor="left", yanchor="top",
    )

    # ── Design parameters box ─────────────────────────────────────────────────
    fig.add_annotation(
        x=0.99, y=0.99, xref="paper", yref="paper",
        text=(
            f"<b style='color:#00ffc8'>DESIGN PARAMETERS</b><br><br>"
            f"Lateral pipe:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>{req.lateral_diameter_mm or 16:.0f} mm LDPE</b><br>"
            f"Mainline pipe:&nbsp;&nbsp;&nbsp;<b>{req.main_diameter_mm or 50:.0f} mm PVC</b><br>"
            f"Emitter flow:&nbsp;&nbsp;&nbsp;&nbsp;<b>{em_flow:.1f} L/h</b><br>"
            f"Design flow:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>{design_flow:.2f} m³/h</b><br>"
            f"Op. pressure:&nbsp;&nbsp;&nbsp;&nbsp;<b>1.0 bar</b><br>"
            f"Filter:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>120 mesh</b><br>"
            f"EU:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<span style='color:#00ffc8'><b>{eu:.1f}%</b></span>"
        ),
        showarrow=False, align="left",
        bgcolor="rgba(10,17,30,0.88)",
        bordercolor="rgba(0,255,200,0.35)", borderwidth=1, borderpad=12,
        font=dict(size=10, color="#e0e0e0", family="monospace"),
        xanchor="right", yanchor="top",
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=(
                "<b>2D DRIP IRRIGATION ENGINEERING LAYOUT</b>"
                f"<br><span style='font-size:11px;color:#00ffc8'>"
                f"Mainline snapped to nearest field edge · {geom['area_ha']:.3f} ha"
                "</span>"
            ),
            font=dict(size=14, color="#e0e0e0", family="monospace"),
            x=0.5, y=0.99, xanchor="center", yanchor="top",
        ),
        paper_bgcolor="#030712",
        plot_bgcolor="#070e1c",
        xaxis=dict(
            title="East–West (Metres)",
            color="#7a8fa0",
            gridcolor="rgba(255,255,255,0.05)",
            zeroline=False,
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            title="North–South (Metres)",
            color="#7a8fa0",
            gridcolor="rgba(255,255,255,0.05)",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            x=0.02, y=-0.12,
            font=dict(color="#8a9aaa", size=9),
            bgcolor="rgba(10,17,30,0.7)",
            bordercolor="rgba(0,229,255,0.2)",
            borderwidth=1,
        ),
        showlegend=True,
        hovermode="closest",
        margin=dict(l=70, r=70, t=90, b=90),
        width=1100,
        height=780,
    )

    # Export to PNG via kaleido
    try:
        png_bytes = pio.to_image(fig, format="png", width=1100, height=780, scale=1.5)
    except Exception as e:
        raise HTTPException(500, f"Kaleido image export failed: {e}")

    return Response(content=png_bytes, media_type="image/png")
