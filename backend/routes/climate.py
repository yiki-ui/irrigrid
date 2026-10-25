#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Routes: Climate
Endpoints for weather parameter retrieval and FAO-56 Penman-Monteith ETo calculation.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Dict
from backend.ingestion.nasa_power import get_weather_data, get_nasa_climatology
from src.core.eto_calculator import ETOCalculator

router = APIRouter(prefix="/climate", tags=["Climate"])
_eto_calc = ETOCalculator()


class EToRequest(BaseModel):
    tmin: float = 14.5
    tmax: float = 25.0
    rhmin: float = 50.0
    rhmax: float = 85.0
    wind_speed: float = 2.0
    sunshine_hours: float = 6.5
    latitude: float = -1.50
    elevation: float = 1800.0
    day_of_year: int = 180


@router.get("/weather")
def get_weather(
    lat: float = Query(-1.50, description="Latitude"),
    lon: float = Query(29.63, description="Longitude"),
    elevation: float = Query(1500.0, description="Elevation in meters")
) -> Dict:
    """Fetch agrometeorological parameters with full monthly climatology."""
    data = get_weather_data(lat, lon)
    # Also attach monthly climatology
    clim = get_nasa_climatology(lat, lon, elevation=elevation)
    if "monthly_climate" in clim:
        data["monthly_climate"] = clim["monthly_climate"]
    if "monthly_rainfall" in clim:
        data["monthly_rainfall"] = clim["monthly_rainfall"]
    data["climatology_source"] = clim.get("source", "nasa_power_live")
    return data


@router.get("/climatology")
def get_climatology(
    lat: float = Query(-1.50, description="Latitude"),
    lon: float = Query(29.63, description="Longitude"),
    elevation: float = Query(1500.0, description="Elevation in meters")
) -> Dict:
    """Fetch full 30-year monthly climatology (Temperature, Rain, Wind, ETo) from NASA POWER."""
    return get_nasa_climatology(lat, lon, elevation=elevation)


@router.post("/eto")
def calculate_eto(req: EToRequest) -> Dict:
    """Compute daily reference evapotranspiration (ETo mm/day) via FAO-56 PM."""
    eto = _eto_calc.calculate_eto(
        tmin=req.tmin,
        tmax=req.tmax,
        rhmin=req.rhmin,
        rhmax=req.rhmax,
        wind_speed=req.wind_speed,
        sunshine_hours=req.sunshine_hours,
        latitude=req.latitude,
        elevation=req.elevation,
        day_of_year=req.day_of_year
    )
    return {
        "eto_mm_day": round(float(eto), 2),
        "method": "FAO-56 Penman-Monteith"
    }
