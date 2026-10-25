# ============================================
# FILE: src/models/climate.py
# Pydantic models for Climate data
# ============================================

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class ClimateData(BaseModel):
    """Daily climate data"""
    date: date
    temperature_min: float = Field(..., ge=-20, le=50, description="Min temp in °C")
    temperature_max: float = Field(..., ge=-20, le=50, description="Max temp in °C")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Relative humidity %")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed m/s")
    sunshine_hours: Optional[float] = Field(None, ge=0, le=24, description="Sunshine hours")
    rainfall: Optional[float] = Field(default=0, ge=0, description="Rainfall in mm")
    
    @property
    def temperature_mean(self) -> float:
        """Calculate mean temperature"""
        return (self.temperature_min + self.temperature_max) / 2


class ClimateDataBulk(BaseModel):
    """Bulk climate data import"""
    location: str
    latitude: float
    longitude: float
    data: list
