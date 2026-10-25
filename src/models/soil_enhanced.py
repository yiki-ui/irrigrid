#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Soil Module with TAM, Infiltration Rate, and Rooting Depth
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class EnhancedSoilModel(BaseModel):
    """Enhanced soil model with comprehensive parameters"""
    name: str
    texture: str
    
    # Water content parameters (volumetric)
    field_capacity: float = Field(..., ge=0, le=1, description="Field capacity (FC) - volumetric")
    wilting_point: float = Field(..., ge=0, le=1, description="Wilting point (WP) - volumetric")
    saturation: float = Field(..., ge=0, le=1, description="Saturation point - volumetric")
    
    # Calculated parameters
    total_available_moisture: float = Field(..., ge=0, description="TAM = FC - WP (mm/meter)")
    
    # Physical properties
    bulk_density: float = Field(..., gt=0, description="Bulk density (g/cm³)")
    infiltration_rate: float = Field(..., gt=0, description="Maximum infiltration rate (mm/day)")
    max_rooting_depth: float = Field(..., gt=0, description="Maximum rooting depth (cm)")
    
    # Initial conditions
    initial_soil_moisture_depletion: float = Field(
        default=50.0, ge=0, le=100, 
        description="Initial soil moisture depletion (% of TAM)"
    )
    initial_available_soil_moisture: Optional[float] = Field(
        None, description="Initial available soil moisture (mm/meter)"
    )
    
    # Hydraulic properties
    hydraulic_conductivity: float = Field(default=10.0, description="Saturated hydraulic conductivity (mm/hr)")
    
    @property
    def available_water_mm_per_meter(self) -> float:
        """Calculate available water in mm per meter of soil"""
        return (self.field_capacity - self.wilting_point) * 1000
    
    @property
    def initial_moisture_mm_per_meter(self) -> float:
        """Calculate initial available moisture"""
        if self.initial_available_soil_moisture:
            return self.initial_available_soil_moisture
        # Calculate from depletion percentage
        return self.total_available_moisture * (1 - self.initial_soil_moisture_depletion / 100)
    
    def get_raw(self, critical_depletion: float = 0.5) -> float:
        """
        Calculate Readily Available Water (RAW)
        
        Args:
            critical_depletion: Critical depletion fraction (p)
            
        Returns:
            RAW in mm/meter
        """
        return self.total_available_moisture * critical_depletion
    
    def get_total_available_water(self, root_depth_m: float) -> float:
        """
        Calculate total available water for given root depth
        
        Args:
            root_depth_m: Root depth in meters
            
        Returns:
            Total available water in mm
        """
        return self.total_available_moisture * root_depth_m


class EnhancedSoilDatabase:
    """Enhanced soil database with comprehensive parameters"""
    
    SOILS = {
        "Sandy Loam": {
            "texture": "Sandy Loam",
            "field_capacity": 0.22,
            "wilting_point": 0.10,
            "saturation": 0.43,
            "total_available_moisture": 120.0,  # mm/meter
            "bulk_density": 1.55,
            "infiltration_rate": 600.0,  # mm/day (25 mm/hr)
            "max_rooting_depth": 200.0,  # cm
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 25.0
        },
        "Loam": {
            "texture": "Loam",
            "field_capacity": 0.30,
            "wilting_point": 0.13,
            "saturation": 0.47,
            "total_available_moisture": 170.0,
            "bulk_density": 1.45,
            "infiltration_rate": 312.0,  # mm/day (13 mm/hr)
            "max_rooting_depth": 180.0,
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 13.0
        },
        "Clay Loam": {
            "texture": "Clay Loam",
            "field_capacity": 0.35,
            "wilting_point": 0.18,
            "saturation": 0.49,
            "total_available_moisture": 170.0,
            "bulk_density": 1.40,
            "infiltration_rate": 192.0,  # mm/day (8 mm/hr)
            "max_rooting_depth": 170.0,
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 8.0
        },
        "Silty Loam": {
            "texture": "Silty Loam",
            "field_capacity": 0.33,
            "wilting_point": 0.13,
            "saturation": 0.50,
            "total_available_moisture": 200.0,
            "bulk_density": 1.40,
            "infiltration_rate": 240.0,  # mm/day (10 mm/hr)
            "max_rooting_depth": 180.0,
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 10.0
        },
        "Sandy Clay Loam": {
            "texture": "Sandy Clay Loam",
            "field_capacity": 0.28,
            "wilting_point": 0.15,
            "saturation": 0.45,
            "total_available_moisture": 130.0,
            "bulk_density": 1.50,
            "infiltration_rate": 360.0,  # mm/day (15 mm/hr)
            "max_rooting_depth": 190.0,
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 15.0
        },
        "Clay": {
            "texture": "Clay",
            "field_capacity": 0.40,
            "wilting_point": 0.25,
            "saturation": 0.52,
            "total_available_moisture": 150.0,
            "bulk_density": 1.30,
            "infiltration_rate": 48.0,  # mm/day (2 mm/hr)
            "max_rooting_depth": 150.0,
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 2.0
        },
        "Sand": {
            "texture": "Sand",
            "field_capacity": 0.12,
            "wilting_point": 0.05,
            "saturation": 0.40,
            "total_available_moisture": 70.0,
            "bulk_density": 1.60,
            "infiltration_rate": 1200.0,  # mm/day (50 mm/hr)
            "max_rooting_depth": 150.0,
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 50.0
        },
        "Silty Clay": {
            "texture": "Silty Clay",
            "field_capacity": 0.38,
            "wilting_point": 0.22,
            "saturation": 0.51,
            "total_available_moisture": 160.0,
            "bulk_density": 1.35,
            "infiltration_rate": 120.0,  # mm/day (5 mm/hr)
            "max_rooting_depth": 160.0,
            "initial_soil_moisture_depletion": 50.0,
            "hydraulic_conductivity": 5.0
        }
    }
    
    @classmethod
    def get_soil(cls, name: str) -> Optional[EnhancedSoilModel]:
        """Get enhanced soil data by name"""
        if name in cls.SOILS:
            data = cls.SOILS[name]
            return EnhancedSoilModel(name=name, **data)
        return None
    
    @classmethod
    def get_all_soils(cls) -> List[str]:
        """Get list of all available soil types"""
        return list(cls.SOILS.keys())
    
    @classmethod
    def get_soil_properties_table(cls) -> List[Dict]:
        """Get soil properties as a table for display"""
        table = []
        for name, data in cls.SOILS.items():
            table.append({
                "Soil Type": name,
                "Texture": data["texture"],
                "FC": f"{data['field_capacity']:.2f}",
                "WP": f"{data['wilting_point']:.2f}",
                "TAM (mm/m)": f"{data['total_available_moisture']:.0f}",
                "Infiltration (mm/day)": f"{data['infiltration_rate']:.0f}",
                "Max Root Depth (cm)": f"{data['max_rooting_depth']:.0f}"
            })
        return table
