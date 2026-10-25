#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Crop Module with Planting/Harvest Dates and Detailed Growth Stages
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date, timedelta
from enum import Enum


class GrowthStage(str, Enum):
    """Crop growth stages"""
    INITIAL = "Initial"
    DEVELOPMENT = "Development"
    MID_SEASON = "Mid-Season"
    LATE_SEASON = "Late-Season"


class CropType(str, Enum):
    """Crop type classification"""
    DRY = "Dry Crop"
    PADDY_RICE = "Paddy Rice"
    UPLAND_RICE = "Upland Rice"


class CropStageData(BaseModel):
    """Detailed crop stage information"""
    stage: GrowthStage
    duration_days: int = Field(..., gt=0, description="Stage duration in days")
    kc_value: float = Field(..., ge=0, le=2, description="Crop coefficient for this stage")
    rooting_depth_start: float = Field(..., ge=0, description="Root depth at stage start (m)")
    rooting_depth_end: float = Field(..., ge=0, description="Root depth at stage end (m)")


class EnhancedCropModel(BaseModel):
    """Enhanced crop model with detailed growth information"""
    name: str
    scientific_name: str
    crop_type: CropType = CropType.DRY
    
    # Kc values for each stage
    kc_initial: float = Field(..., ge=0, le=2)
    kc_development: float = Field(..., ge=0, le=2)
    kc_mid: float = Field(..., ge=0, le=2)
    kc_late: float = Field(..., ge=0, le=2)
    
    # Growth stage durations (days)
    stage_initial: int = Field(..., gt=0, description="Initial stage duration")
    stage_development: int = Field(..., gt=0, description="Development stage duration")
    stage_mid: int = Field(..., gt=0, description="Mid-season stage duration")
    stage_late: int = Field(..., gt=0, description="Late-season stage duration")
    
    # Rooting depth
    max_rooting_depth: float = Field(..., gt=0, description="Maximum rooting depth (m)")
    initial_rooting_depth: float = Field(default=0.3, description="Initial rooting depth (m)")
    
    # Water stress factors
    critical_depletion: float = Field(default=0.5, ge=0, le=1, description="Critical depletion fraction")
    yield_response_factor: float = Field(default=1.0, ge=0, description="Yield response factor (Ky)")
    
    # Economic data
    planting_density: int = Field(default=25000, description="Plants per hectare")
    expected_yield: float = Field(default=30.0, description="Expected yield (tons/ha)")
    market_price: float = Field(default=500.0, description="Market price (RWF/kg)")
    water_productivity: float = Field(default=15.0, description="Water productivity (kg/m³)")
    
    # Varieties
    varieties: List[str] = Field(default=[], description="Common varieties")
    
    @property
    def total_growing_days(self) -> int:
        """Calculate total growing period"""
        return self.stage_initial + self.stage_development + self.stage_mid + self.stage_late
    
    def get_harvest_date(self, planting_date: date) -> date:
        """Calculate harvest date from planting date"""
        return planting_date + timedelta(days=self.total_growing_days)
    
    def get_stage_info(self) -> List[Dict]:
        """Get detailed information for each growth stage"""
        return [
            {
                "stage": "Initial",
                "days": self.stage_initial,
                "kc": self.kc_initial,
                "root_depth": f"{self.initial_rooting_depth:.2f} m"
            },
            {
                "stage": "Development",
                "days": self.stage_development,
                "kc": self.kc_development,
                "root_depth": f"{self.initial_rooting_depth:.2f} - {self.max_rooting_depth:.2f} m"
            },
            {
                "stage": "Mid-Season",
                "days": self.stage_mid,
                "kc": self.kc_mid,
                "root_depth": f"{self.max_rooting_depth:.2f} m"
            },
            {
                "stage": "Late-Season",
                "days": self.stage_late,
                "kc": self.kc_late,
                "root_depth": f"{self.max_rooting_depth:.2f} m"
            }
        ]
    
    def get_kc_at_day(self, day_after_planting: int) -> float:
        """Get Kc value at specific day after planting"""
        if day_after_planting < 0:
            return 0.0
        elif day_after_planting <= self.stage_initial:
            return self.kc_initial
        elif day_after_planting <= self.stage_initial + self.stage_development:
            # Linear interpolation during development
            days_in_dev = day_after_planting - self.stage_initial
            return self.kc_initial + (self.kc_mid - self.kc_initial) * (days_in_dev / self.stage_development)
        elif day_after_planting <= self.stage_initial + self.stage_development + self.stage_mid:
            return self.kc_mid
        elif day_after_planting <= self.total_growing_days:
            # Linear interpolation during late season
            days_in_late = day_after_planting - (self.stage_initial + self.stage_development + self.stage_mid)
            return self.kc_mid + (self.kc_late - self.kc_mid) * (days_in_late / self.stage_late)
        else:
            return self.kc_late


class CropPattern(BaseModel):
    """Crop pattern for multiple crops in rotation"""
    pattern_name: str
    crops: List[Dict] = Field(default=[], description="List of crops in pattern")
    total_area: float = Field(..., gt=0, description="Total area (ha)")
    
    def add_crop(self, crop_name: str, crop_number: int, planting_date: date, 
                 harvest_date: date, area_percentage: float):
        """Add a crop to the pattern"""
        self.crops.append({
            "name": crop_name,
            "number": crop_number,
            "planting_date": planting_date.strftime("%Y-%m-%d"),
            "harvest_date": harvest_date.strftime("%Y-%m-%d"),
            "area_percent": area_percentage,
            "area_ha": self.total_area * (area_percentage / 100)
        })
    
    def get_total_area_percentage(self) -> float:
        """Get total area percentage allocated"""
        return sum(crop["area_percent"] for crop in self.crops)


class EnhancedCropDatabase:
    """Enhanced crop database with detailed stage information"""
    
    CROPS = {
        "Tomato": {
            "scientific_name": "Solanum lycopersicum",
            "crop_type": CropType.DRY,
            "kc_initial": 0.6, "kc_development": 0.88, "kc_mid": 1.15, "kc_late": 0.8,
            "stage_initial": 25, "stage_development": 40, "stage_mid": 45, "stage_late": 25,
            "max_rooting_depth": 0.7, "initial_rooting_depth": 0.3,
            "critical_depletion": 0.4, "yield_response_factor": 1.05,
            "planting_density": 25000, "expected_yield": 35.0, 
            "market_price": 600.0, "water_productivity": 15.0,
            "varieties": ["Tycoon", "Onyx", "Anna F1", "Saim", "Komeza"]
        },
        "Bell Pepper": {
            "scientific_name": "Capsicum annuum",
            "crop_type": CropType.DRY,
            "kc_initial": 0.6, "kc_development": 0.83, "kc_mid": 1.05, "kc_late": 0.9,
            "stage_initial": 25, "stage_development": 35, "stage_mid": 40, "stage_late": 20,
            "max_rooting_depth": 0.5, "initial_rooting_depth": 0.25,
            "critical_depletion": 0.3, "yield_response_factor": 1.1,
            "planting_density": 30000, "expected_yield": 25.0,
            "market_price": 800.0, "water_productivity": 12.0,
            "varieties": ["California Wonder", "Yolo Wonder"]
        },
        "Cabbage": {
            "scientific_name": "Brassica oleracea var. capitata",
            "crop_type": CropType.DRY,
            "kc_initial": 0.7, "kc_development": 0.88, "kc_mid": 1.05, "kc_late": 0.95,
            "stage_initial": 20, "stage_development": 30, "stage_mid": 50, "stage_late": 15,
            "max_rooting_depth": 0.5, "initial_rooting_depth": 0.3,
            "critical_depletion": 0.45, "yield_response_factor": 0.95,
            "planting_density": 40000, "expected_yield": 40.0,
            "market_price": 300.0, "water_productivity": 18.0,
            "varieties": ["Copenhagen Market", "Gloria F1"]
        },
        "Maize": {
            "scientific_name": "Zea mays",
            "crop_type": CropType.DRY,
            "kc_initial": 0.3, "kc_development": 0.75, "kc_mid": 1.2, "kc_late": 0.6,
            "stage_initial": 20, "stage_development": 35, "stage_mid": 40, "stage_late": 30,
            "max_rooting_depth": 1.0, "initial_rooting_depth": 0.3,
            "critical_depletion": 0.55, "yield_response_factor": 1.25,
            "planting_density": 53000, "expected_yield": 6.0,
            "market_price": 400.0, "water_productivity": 18.0,
            "varieties": ["MH14", "WH505", "Hybrid"]
        },
        "Irish Potato": {
            "scientific_name": "Solanum tuberosum",
            "crop_type": CropType.DRY,
            "kc_initial": 0.5, "kc_development": 0.83, "kc_mid": 1.15, "kc_late": 0.75,
            "stage_initial": 25, "stage_development": 30, "stage_mid": 45, "stage_late": 30,
            "max_rooting_depth": 0.4, "initial_rooting_depth": 0.2,
            "critical_depletion": 0.35, "yield_response_factor": 1.1,
            "planting_density": 40000, "expected_yield": 30.0,
            "market_price": 250.0, "water_productivity": 20.0,
            "varieties": ["Victoria", "Kinigi", "Cruza"]
        },
        "Beans": {
            "scientific_name": "Phaseolus vulgaris",
            "crop_type": CropType.DRY,
            "kc_initial": 0.4, "kc_development": 0.78, "kc_mid": 1.15, "kc_late": 0.35,
            "stage_initial": 20, "stage_development": 30, "stage_mid": 40, "stage_late": 20,
            "max_rooting_depth": 0.5, "initial_rooting_depth": 0.3,
            "critical_depletion": 0.45, "yield_response_factor": 1.15,
            "planting_density": 200000, "expected_yield": 2.5,
            "market_price": 800.0, "water_productivity": 12.0,
            "varieties": ["Climbing beans", "Bush beans"]
        },
        "Onion": {
            "scientific_name": "Allium cepa",
            "crop_type": CropType.DRY,
            "kc_initial": 0.7, "kc_development": 0.88, "kc_mid": 1.05, "kc_late": 0.75,
            "stage_initial": 15, "stage_development": 25, "stage_mid": 70, "stage_late": 40,
            "max_rooting_depth": 0.4, "initial_rooting_depth": 0.2,
            "critical_depletion": 0.3, "yield_response_factor": 1.1,
            "planting_density": 500000, "expected_yield": 30.0,
            "market_price": 400.0, "water_productivity": 14.0,
            "varieties": ["Red Creole", "Bombay Red"]
        },
        "Banana": {
            "scientific_name": "Musa acuminata × balbisiana",
            "crop_type": CropType.DRY,
            "kc_initial": 0.5, "kc_development": 0.8, "kc_mid": 1.1, "kc_late": 1.0,
            "stage_initial": 120, "stage_development": 90, "stage_mid": 120, "stage_late": 60,
            "max_rooting_depth": 0.6, "initial_rooting_depth": 0.3,
            "critical_depletion": 0.35, "yield_response_factor": 1.35,
            "planting_density": 2000, "expected_yield": 40.0,
            "market_price": 300.0, "water_productivity": 20.0,
            "varieties": ["Cavendish", "Gros Michel", "Local cooking"]
        },
        "Coffee Arabica": {
            "scientific_name": "Coffea arabica",
            "crop_type": CropType.DRY,
            "kc_initial": 0.9, "kc_development": 0.93, "kc_mid": 0.95, "kc_late": 0.95,
            "stage_initial": 90, "stage_development": 90, "stage_mid": 120, "stage_late": 60,
            "max_rooting_depth": 1.5, "initial_rooting_depth": 0.5,
            "critical_depletion": 0.4, "yield_response_factor": 0.8,
            "planting_density": 2000, "expected_yield": 2.0,
            "market_price": 3000.0, "water_productivity": 0.5,
            "varieties": ["Bourbon", "Mayaguez 139"]
        }
    }
    
    @classmethod
    def get_crop(cls, name: str) -> Optional[EnhancedCropModel]:
        """Get enhanced crop data by name"""
        if name in cls.CROPS:
            data = cls.CROPS[name]
            return EnhancedCropModel(name=name, **data)
        return None
    
    @classmethod
    def get_all_crops(cls) -> List[str]:
        """Get list of all available crops"""
        return list(cls.CROPS.keys())
