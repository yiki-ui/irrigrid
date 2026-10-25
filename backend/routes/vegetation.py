#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Routes: Vegetation
Endpoints for crop catalogs, soil profiles, and NDVI vegetation index.
"""

from fastapi import APIRouter, Query
from typing import Dict, List, Optional
from backend.ingestion.ndvi import get_ndvi_data
from src.models.crop import CropDatabase
from src.models.soil import SoilDatabase

router = APIRouter(prefix="/vegetation", tags=["Vegetation"])


@router.get("/crops")
def list_crops() -> List[Dict]:
    """Retrieve catalog of supported crops with FAO Kc growth stages."""
    return [
        {"name": name, **data}
        for name, data in CropDatabase.CROPS.items()
    ]


@router.get("/soils")
def list_soils() -> List[Dict]:
    """Retrieve soil texture classes with water-holding capacity."""
    return [
        {"name": name, **data}
        for name, data in SoilDatabase.SOILS.items()
    ]


@router.get("/ndvi")
def get_ndvi(
    lat: float = Query(-1.50, description="Latitude"),
    lon: float = Query(29.63, description="Longitude")
) -> Dict:
    """Retrieve Normalized Difference Vegetation Index (NDVI) and vigor status."""
    return get_ndvi_data(lat, lon)


@router.get("/soil-profile")
def get_soil_profile(
    lat: float = Query(-1.50, description="Latitude"),
    lon: float = Query(29.63, description="Longitude"),
    district: Optional[str] = Query(None, description="District name for fallback")
) -> Dict:
    """
    Retrieve pedological soil properties from ISRIC SoilGrids v2.0
    with fallback to district baseline and standard agronomic default.
    """
    from backend.ingestion.soilgrids import get_soil_properties
    return get_soil_properties(lat=lat, lon=lon, district=district)

