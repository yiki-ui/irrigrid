#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rwanda Administrative and Geographic Data
Provinces, Districts, Sectors, and Climate Zones
"""

from typing import Dict, List, Optional


class RwandaAdministrative:
    """Rwanda administrative boundaries and data"""
    
    # 5 Provinces with their districts
    PROVINCES = {
        "Kigali": {
            "districts": ["Gasabo", "Kicukiro", "Nyarugenge"],
            "capital": "Kigali",
            "area_km2": 730,
            "climate_zone": "Temperate Highland"
        },
        "Eastern": {
            "districts": ["Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana"],
            "capital": "Rwamagana",
            "area_km2": 9458,
            "climate_zone": "Tropical Savanna"
        },
        "Northern": {
            "districts": ["Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo"],
            "capital": "Musanze",
            "area_km2": 3276,
            "climate_zone": "Temperate Highland"
        },
        "Southern": {
            "districts": ["Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango"],
            "capital": "Huye",
            "area_km2": 5963,
            "climate_zone": "Temperate Highland"
        },
        "Western": {
            "districts": ["Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro"],
            "capital": "Rubavu",
            "area_km2": 5883,
            "climate_zone": "Tropical Highland"
        }
    }
    
    # Key sectors for major districts
    SECTORS = {
        "Gasabo": ["Bumbogo", "Gatsata", "Gikomero", "Gisozi", "Jabana", "Jali", "Kacyiru", 
                   "Kimihurura", "Kimironko", "Kinyinya", "Ndera", "Nduba", "Remera", "Rusororo", "Rutunga"],
        "Kicukiro": ["Gahanga", "Gatenga", "Gikondo", "Kagarama", "Kanombe", "Kicukiro", 
                     "Kigarama", "Masaka", "Niboye", "Nyarugunga"],
        "Nyarugenge": ["Gitega", "Kanyinya", "Kigali", "Kimisagara", "Mageragere", "Muhima", 
                       "Nyakabanda", "Nyamirambo", "Nyarugenge", "Rwezamenyo"],
        "Bugesera": ["Gashora", "Juru", "Kamabuye", "Mareba", "Mayange", "Musenyi", 
                     "Mwogo", "Ngeruka", "Ntarama", "Nyamata", "Nyarugenge", "Rilima", 
                     "Ruhuha", "Rweru", "Shyara"],
        "Musanze": ["Busogo", "Cyuve", "Gacaca", "Gashaki", "Gataraga", "Kimonyi", 
                    "Kinigi", "Muhoza", "Muko", "Musanze", "Nkotsi", "Nyange", 
                    "Remera", "Rwaza", "Shingiro"],
        "Huye": ["Gishamvu", "Karama", "Kigoma", "Kinazi", "Maraba", "Mbazi", 
                 "Mukura", "Ngoma", "Ruhashya", "Rusatira", "Rwaniro", "Simbi", 
                 "Tumba", "Huye"],
    }
    
    # Climate data by province (averages)
    CLIMATE_DATA = {
        "Kigali": {
            "avg_temp_min": 15.0,
            "avg_temp_max": 27.0,
            "annual_rainfall_mm": 1000,
            "altitude_m": 1500,
            "humidity_percent": 70,
            "eto_mm_per_day": 4.5
        },
        "Eastern": {
            "avg_temp_min": 16.0,
            "avg_temp_max": 29.0,
            "annual_rainfall_mm": 800,
            "altitude_m": 1300,
            "humidity_percent": 65,
            "eto_mm_per_day": 5.0
        },
        "Northern": {
            "avg_temp_min": 12.0,
            "avg_temp_max": 24.0,
            "annual_rainfall_mm": 1400,
            "altitude_m": 1900,
            "humidity_percent": 75,
            "eto_mm_per_day": 3.8
        },
        "Southern": {
            "avg_temp_min": 14.0,
            "avg_temp_max": 26.0,
            "annual_rainfall_mm": 1200,
            "altitude_m": 1600,
            "humidity_percent": 72,
            "eto_mm_per_day": 4.2
        },
        "Western": {
            "avg_temp_min": 15.0,
            "avg_temp_max": 27.0,
            "annual_rainfall_mm": 1300,
            "altitude_m": 1500,
            "humidity_percent": 73,
            "eto_mm_per_day": 4.3
        }
    }
    
    # Soil types by region
    SOIL_TYPES = {
        "Kigali": ["Nitisols", "Ferralsols", "Urban soils"],
        "Eastern": ["Ferralsols", "Acrisols", "Lixisols", "Gleysols (wetlands)"],
        "Northern": ["Andosols (volcanic)", "Nitisols", "Histosols"],
        "Southern": ["Ferralsols", "Acrisols", "Nitisols"],
        "Western": ["Andosols (volcanic)", "Nitisols", "Ferralsols"]
    }
    
    @classmethod
    def get_districts(cls, province: str) -> List[str]:
        """Get districts for a province"""
        return cls.PROVINCES.get(province, {}).get("districts", [])
    
    @classmethod
    def get_sectors(cls, district: str) -> List[str]:
        """Get sectors for a district"""
        return cls.SECTORS.get(district, [])
    
    @classmethod
    def get_climate_data(cls, province: str) -> Dict:
        """Get climate data for a province"""
        return cls.CLIMATE_DATA.get(province, {})
    
    @classmethod
    def get_soil_types(cls, province: str) -> List[str]:
        """Get common soil types for a province"""
        return cls.SOIL_TYPES.get(province, [])
    
    @classmethod
    def get_all_provinces(cls) -> List[str]:
        """Get list of all provinces"""
        return list(cls.PROVINCES.keys())
    
    @classmethod
    def get_all_districts(cls) -> List[str]:
        """Get list of all districts"""
        districts = []
        for province_data in cls.PROVINCES.values():
            districts.extend(province_data["districts"])
        return sorted(districts)
    
    @classmethod
    def find_province_for_district(cls, district: str) -> Optional[str]:
        """Find which province a district belongs to"""
        for province, data in cls.PROVINCES.items():
            if district in data["districts"]:
                return province
        return None


class SoilDatabase:
    """Soil properties database"""
    
    SOIL_PROPERTIES = {
        "Andosols (Volcanic)": {
            "texture": "Loam to Clay Loam",
            "field_capacity": 0.40,
            "wilting_point": 0.20,
            "bulk_density": 0.85,
            "infiltration_rate_mm_hr": 25,
            "hydraulic_conductivity": 15,
            "description": "Volcanic soils, high water retention, fertile"
        },
        "Nitisols": {
            "texture": "Clay",
            "field_capacity": 0.38,
            "wilting_point": 0.22,
            "bulk_density": 1.20,
            "infiltration_rate_mm_hr": 15,
            "hydraulic_conductivity": 8,
            "description": "Deep red clay soils, good structure"
        },
        "Ferralsols": {
            "texture": "Clay to Sandy Clay",
            "field_capacity": 0.32,
            "wilting_point": 0.18,
            "bulk_density": 1.30,
            "infiltration_rate_mm_hr": 20,
            "hydraulic_conductivity": 10,
            "description": "Weathered tropical soils, moderate fertility"
        },
        "Acrisols": {
            "texture": "Sandy Clay Loam",
            "field_capacity": 0.28,
            "wilting_point": 0.15,
            "bulk_density": 1.40,
            "infiltration_rate_mm_hr": 25,
            "hydraulic_conductivity": 12,
            "description": "Acidic soils, require lime amendment"
        },
        "Lixisols": {
            "texture": "Sandy Loam to Clay Loam",
            "field_capacity": 0.30,
            "wilting_point": 0.16,
            "bulk_density": 1.35,
            "infiltration_rate_mm_hr": 22,
            "hydraulic_conductivity": 11,
            "description": "Moderate fertility, good drainage"
        },
        "Gleysols (Wetlands)": {
            "texture": "Clay to Silty Clay",
            "field_capacity": 0.45,
            "wilting_point": 0.25,
            "bulk_density": 1.10,
            "infiltration_rate_mm_hr": 5,
            "hydraulic_conductivity": 3,
            "description": "Waterlogged soils, high organic matter"
        },
        "Histosols": {
            "texture": "Organic",
            "field_capacity": 0.60,
            "wilting_point": 0.30,
            "bulk_density": 0.50,
            "infiltration_rate_mm_hr": 30,
            "hydraulic_conductivity": 20,
            "description": "Peat soils, very high water retention"
        }
    }
    
    @classmethod
    def get_soil_properties(cls, soil_type: str) -> Dict:
        """Get properties for a soil type"""
        return cls.SOIL_PROPERTIES.get(soil_type, {})
    
    @classmethod
    def get_all_soil_types(cls) -> List[str]:
        """Get list of all soil types"""
        return list(cls.SOIL_PROPERTIES.keys())
    
    @classmethod
    def calculate_taw(cls, soil_type: str, root_depth_m: float = 0.6) -> float:
        """Calculate Total Available Water (mm)"""
        props = cls.get_soil_properties(soil_type)
        if not props:
            return 0.0
        
        fc = props.get("field_capacity", 0.30)
        wp = props.get("wilting_point", 0.15)
        
        # TAW = (FC - WP) * root_depth * 1000 (convert to mm)
        taw = (fc - wp) * root_depth_m * 1000
        return taw
    
    @classmethod
    def calculate_raw(cls, soil_type: str, root_depth_m: float = 0.6, 
                     depletion_fraction: float = 0.5) -> float:
        """Calculate Readily Available Water (mm)"""
        taw = cls.calculate_taw(soil_type, root_depth_m)
        raw = taw * depletion_fraction
        return raw
