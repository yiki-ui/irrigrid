#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Routes: Optimize
Stateless field design optimization (POST /optimize) and PDF report generation (GET /optimize/{id}/pdf).
"""

import asyncio
import time
import uuid
import base64
import logging
import traceback
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from backend.core.optimizer import optimize_irrigation_system
from backend.core.terrain import analyze_polygon_terrain, get_elevation_and_slope
from backend.core.pdf_export import generate_irrigation_pdf
from backend.core.field_layout import compute_field_layout

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/optimize", tags=["Optimization & Export"])

# Ephemeral runtime memory store for recent designs so user can fetch the generated PDF immediately
# TTL: 30 minutes (1800 seconds), max 100 entries
_RECENT_DESIGNS: Dict[str, Dict] = {}
_MAX_DESIGNS = 100
_TTL_SECONDS = 1800


def _cleanup_designs() -> None:
    """Remove expired entries and enforce max size."""
    now = time.time()
    expired = [k for k, v in _RECENT_DESIGNS.items() if now - v.get("_ts", 0) > _TTL_SECONDS]
    for k in expired:
        _RECENT_DESIGNS.pop(k, None)
    # If still over limit, remove oldest
    if len(_RECENT_DESIGNS) > _MAX_DESIGNS:
        sorted_items = sorted(_RECENT_DESIGNS.items(), key=lambda x: x[1].get("_ts", 0))
        for k, _ in sorted_items[:len(_RECENT_DESIGNS) - _MAX_DESIGNS]:
            _RECENT_DESIGNS.pop(k, None)


class OptimizeRequest(BaseModel):
    crop_name: str = "Tomato"
    soil_type: str = "Volcanic Loam"
    location_name: str = "Rwanda"
    field_area_ha: Optional[float] = Field(None, gt=0)
    polygon_coordinates: Optional[List[List[float]]] = None
    water_source_coords: Optional[List[float]] = None
    slope_percent: Optional[float] = None
    min_eu_threshold: float = 90.0
    lateral_spacing: Optional[float] = Field(None, gt=0)
    emitter_spacing: Optional[float] = Field(None, gt=0)
    layout_image_base64: Optional[str] = None
    climate_data: Optional[List[Dict]] = None
    soil_detail: Optional[Dict] = None
    water_balance: Optional[List[Dict]] = None
    schedule_summary: Optional[Dict] = None


@router.post("")
async def run_optimization(req: OptimizeRequest) -> Dict:
    """Run optimization for a smallholder field: layout first, then hydraulics on real geometry."""
    import math

    # 1. Determine terrain slope and area
    if req.polygon_coordinates and len(req.polygon_coordinates) >= 3:
        terrain = await run_in_threadpool(analyze_polygon_terrain, req.polygon_coordinates)
        slope = req.slope_percent if req.slope_percent is not None else terrain["slope_percent"]
        area_ha = req.field_area_ha if req.field_area_ha else 0.25
    else:
        slope = req.slope_percent if req.slope_percent is not None else 0.0
        area_ha = req.field_area_ha if req.field_area_ha else 0.25

    # 2. Compute layout FIRST with user-chosen spacing (or defaults)
    lat_sp = req.lateral_spacing or 1.0
    em_sp = req.emitter_spacing or 0.3

    layout_geom = await run_in_threadpool(
        compute_field_layout,
        polygon_coords=req.polygon_coordinates,
        lateral_spacing=lat_sp,
        emitter_spacing=em_sp,
        field_area_ha=area_ha,
        water_source_coords=req.water_source_coords,
    )

    # 3. Extract real geometry for the optimizer
    segments = layout_geom.get("lateral_segments", [])
    if segments:
        max_lat_m = max(
            math.hypot(s[2] - s[0], s[3] - s[1]) for s in segments
        )
    else:
        max_lat_m = layout_geom.get("field_height_m", math.sqrt(area_ha * 10000))

    layout_kwargs = {
        "layout_num_laterals": layout_geom.get("num_laterals"),
        "layout_total_emitters": layout_geom.get("total_emitters"),
        "layout_max_lateral_m": max_lat_m,
        "layout_mainline_m": layout_geom.get("mainline_length_m"),
        "layout_total_lateral_m": layout_geom.get("total_lateral_m"),
    }

    # 4. Run hydraulic optimizer on real polygon geometry
    result = await run_in_threadpool(
        optimize_irrigation_system,
        field_area_ha=area_ha,
        slope_pct=slope,
        crop_name=req.crop_name,
        min_eu_threshold=req.min_eu_threshold,
        lateral_spacing=req.lateral_spacing,
        emitter_spacing=req.emitter_spacing,
        **layout_kwargs,
    )

    # 5. Store design ephemerally for PDF download
    _cleanup_designs()
    design_id = str(uuid.uuid4())[:8]
    _RECENT_DESIGNS[design_id] = {
        "design_data": result,
        "crop_name": req.crop_name,
        "field_area_ha": area_ha,
        "location_name": req.location_name,
        "soil_type": req.soil_type,
        "polygon_coordinates": req.polygon_coordinates,
        "water_source_coords": req.water_source_coords,
        "layout_geometry": layout_geom,
        "layout_image_base64": req.layout_image_base64,
        "climate_data": req.climate_data,
        "soil_detail": req.soil_detail,
        "water_balance": req.water_balance,
        "schedule_summary": req.schedule_summary,
        "_ts": time.time(),
    }

    return {
        "design_id": design_id,
        "pdf_url": f"/api/v1/optimize/{design_id}/pdf",
        "layout_geometry": layout_geom,
        **result
    }


@router.get("/{design_id}/pdf")
async def get_design_pdf(design_id: str):
    """Generate and download executive irrigation design PDF."""
    _cleanup_designs()
    record = _RECENT_DESIGNS.get(design_id)
    if not record:
        raise HTTPException(status_code=404, detail="Design record expired or not found. Please re-run optimization.")

    # Decode client-captured layout PNG if provided
    layout_image_bytes = None
    b64 = record.get("layout_image_base64")
    if b64:
        try:
            if isinstance(b64, str):
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                b64 = b64.strip()
            decoded = base64.b64decode(b64)
            if decoded.startswith(b"\x89PNG") or decoded.startswith(b"\xff\xd8\xff"):
                layout_image_bytes = decoded
            else:
                logger.warning("Captured layout image has invalid magic header; falling back to server-generated layout.")
        except Exception as e:
            logger.warning(f"Failed to decode layout_image_base64: {e}; falling back to server-generated layout.")
            layout_image_bytes = None

    try:
        pdf_bytes = await run_in_threadpool(
            generate_irrigation_pdf,
            design_data=record.get("design_data") or {},
            crop_name=record.get("crop_name") or "Tomato",
            field_area_ha=record.get("field_area_ha") or 0.25,
            location_name=record.get("location_name") or "Rwanda",
            soil_type=record.get("soil_type") or "Loam",
            polygon_coords=record.get("polygon_coordinates"),
            water_source_coords=record.get("water_source_coords"),
            layout_image_bytes=layout_image_bytes,
            layout_geometry=record.get("layout_geometry"),
            climate_data=record.get("climate_data"),
            soil_detail=record.get("soil_detail"),
            water_balance=record.get("water_balance"),
            schedule_summary=record.get("schedule_summary"),
        )
    except Exception as e:
        logger.error(f"Failed to generate irrigation PDF: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=irrigrid_design_{design_id}.pdf"}
    )

