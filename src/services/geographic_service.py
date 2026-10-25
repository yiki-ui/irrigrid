#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rwanda Geographic Service
Complete geographic lookup and irrigation design support
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.data.rwanda_districts import RWANDA_DISTRICTS, District, get_district, get_districts_by_province
from src.data.rwanda_sectors_cells import RWANDA_SECTORS, RWANDA_CELLS, Sector, Cell, get_sector, get_sectors_by_district


@dataclass
class LocationData:
    """Complete location data for irrigation design"""
    province: str
    district: str
    sector: Optional[str]
    cell: Optional[str]
    latitude: float
    longitude: float
    altitude: float
    climate_zone: str
    avg_rainfall_mm: float
    avg_temp_c: float
    soil_types: List[str]
    water_sources: List[str]
    irrigation_potential: str
    population: int
    area_km2: float
    # ── NEW: Field-specific data (from polygon drawing) ──
    village: Optional[str] = None
    field_area_ha: Optional[float] = None
    field_perimeter_m: Optional[float] = None
    field_centroid: Optional[Tuple[float, float]] = None
    polygon_coordinates: Optional[List[Tuple[float, float]]] = None
    bounding_box: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for signal emission"""
        return {
            'province': self.province,
            'district': self.district,
            'sector': self.sector,
            'cell': self.cell,
            'village': self.village,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude_m': self.altitude,
            'climate_zone': self.climate_zone,
            'annual_rainfall_mm': self.avg_rainfall_mm,
            'field_area_ha': self.field_area_ha,
            'field_perimeter_m': self.field_perimeter_m,
            'field_centroid': self.field_centroid,
            'polygon_coordinates': self.polygon_coordinates,
            'bounding_box': self.bounding_box
        }


class RwandaGeographicService:
    """
    Rwanda Geographic Service for Irrigation Design
    Provides complete geographic data for all administrative levels
    """
    
    def __init__(self):
        """Initialize geographic service"""
        self.districts = RWANDA_DISTRICTS
        self.sectors = RWANDA_SECTORS
        self.cells = RWANDA_CELLS
    
    def get_location_data(self, 
                         district: str, 
                         sector: Optional[str] = None,
                         cell: Optional[str] = None) -> Optional[LocationData]:
        """
        Get complete location data for irrigation design
        
        Args:
            district: District name
            sector: Sector name (optional)
            cell: Cell name (optional)
            
        Returns:
            Complete location data or None if not found
        """
        # Get district data
        district_obj = self.districts.get(district)
        if not district_obj:
            return None
        
        # Start with district-level data
        location = LocationData(
            province=district_obj.province,
            district=district_obj.name,
            sector=sector,
            cell=cell,
            latitude=district_obj.latitude,
            longitude=district_obj.longitude,
            altitude=district_obj.altitude,
            climate_zone=district_obj.climate_zone,
            avg_rainfall_mm=district_obj.avg_rainfall_mm,
            avg_temp_c=district_obj.avg_temp_c,
            soil_types=district_obj.soil_types,
            water_sources=["Rivers", "Lakes", "Boreholes"],  # Default
            irrigation_potential="Medium",  # Default
            population=district_obj.population,
            area_km2=district_obj.area_km2
        )
        
        # Refine with sector data if available
        if sector:
            sector_key = f"{district}_{sector}"
            sector_obj = self.sectors.get(sector_key)
            if sector_obj:
                location.latitude = sector_obj.latitude
                location.longitude = sector_obj.longitude
                location.altitude = sector_obj.altitude
                location.soil_types = [sector_obj.soil_type_primary]
                location.water_sources = sector_obj.water_sources
                location.irrigation_potential = sector_obj.irrigation_potential
                location.population = sector_obj.population
                location.area_km2 = sector_obj.area_km2
        
        # Further refine with cell data if available
        if cell and sector:
            # Look up cell in the cells dictionary
            cell_key = f"{district}_{sector}_{cell}"
            cell_obj = self.cells.get(cell_key)
            if cell_obj:
                location.latitude = cell_obj.latitude
                location.longitude = cell_obj.longitude
                location.altitude = cell_obj.altitude
                if hasattr(cell_obj, 'population'):
                    location.population = cell_obj.population
        
        return location
    
    def update_location_with_field(self, location: LocationData, 
                                   polygon: List[Tuple[float, float]],
                                   area_ha: float,
                                   perimeter_m: float) -> LocationData:
        """
        Update location data with field polygon information
        
        Args:
            location: Existing location data
            polygon: List of (lat, lng) coordinates
            area_ha: Field area in hectares
            perimeter_m: Field perimeter in meters
            
        Returns:
            Updated location data
        """
        if not polygon or len(polygon) < 3:
            return location
        
        # Calculate centroid
        lats = [p[0] for p in polygon]
        lngs = [p[1] for p in polygon]
        centroid_lat = sum(lats) / len(lats)
        centroid_lng = sum(lngs) / len(lngs)
        
        # Calculate bounding box
        bbox = {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lng': min(lngs),
            'max_lng': max(lngs)
        }
        
        # Update location
        location.field_area_ha = area_ha
        location.field_perimeter_m = perimeter_m
        location.field_centroid = (centroid_lat, centroid_lng)
        location.polygon_coordinates = polygon
        location.bounding_box = bbox
        
        return location
    
    def get_irrigation_recommendations(self, location: LocationData) -> Dict[str, any]:
        """
        Get irrigation system recommendations based on location
        
        Args:
            location: Location data
            
        Returns:
            Dictionary of recommendations
        """
        recommendations = {
            "recommended_systems": [],
            "water_availability": "",
            "soil_suitability": "",
            "climate_considerations": "",
            "challenges": [],
            "opportunities": []
        }
        
        # System recommendations based on climate and altitude
        if location.altitude > 2000:
            recommendations["recommended_systems"] = ["Drip", "Sprinkler"]
            recommendations["climate_considerations"] = "High altitude: Cool temperatures, good for vegetables and potatoes"
        elif location.altitude > 1500:
            recommendations["recommended_systems"] = ["Drip", "Sprinkler"]
            recommendations["climate_considerations"] = "Medium altitude: Ideal for coffee, tea, and mixed crops"
        else:
            recommendations["recommended_systems"] = ["Drip", "Sprinkler", "Surface"]
            recommendations["climate_considerations"] = "Low altitude: Warm climate, suitable for rice, bananas, and tropical crops"
        
        # Water availability assessment
        if location.irrigation_potential == "Very High":
            recommendations["water_availability"] = "Excellent water availability from rivers/lakes"
            recommendations["opportunities"].append("Large-scale irrigation feasible")
        elif location.irrigation_potential == "High":
            recommendations["water_availability"] = "Good water availability"
            recommendations["opportunities"].append("Medium to large-scale irrigation possible")
        else:
            recommendations["water_availability"] = "Moderate water availability"
            recommendations["challenges"].append("Water conservation critical")
        
        # Soil suitability
        if "Volcanic" in location.soil_types:
            recommendations["soil_suitability"] = "Excellent: Volcanic soils are highly fertile"
            recommendations["opportunities"].append("High-value crops recommended")
        elif "Loam" in location.soil_types or "Clay Loam" in location.soil_types:
            recommendations["soil_suitability"] = "Good: Loam soils retain water well"
        elif "Sandy" in location.soil_types:
            recommendations["soil_suitability"] = "Fair: Sandy soils need frequent irrigation"
            recommendations["challenges"].append("High water requirement due to sandy soil")
        else:
            recommendations["soil_suitability"] = "Variable: Soil testing recommended"
        
        # Rainfall considerations
        if location.avg_rainfall_mm < 1000:
            recommendations["challenges"].append("Low rainfall area - irrigation essential")
            recommendations["recommended_systems"] = ["Drip"]  # Most efficient
        elif location.avg_rainfall_mm > 1400:
            recommendations["opportunities"].append("High rainfall - supplemental irrigation only")
        
        return recommendations
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in km (Haversine formula)
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def find_nearest_district(self, latitude: float, longitude: float) -> Tuple[str, float]:
        """
        Find nearest district to given coordinates
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Tuple of (district_name, distance_km)
        """
        min_distance = float('inf')
        nearest_district = None
        
        for name, district in self.districts.items():
            distance = self.calculate_distance(
                latitude, longitude,
                district.latitude, district.longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest_district = name
        
        return nearest_district, min_distance
    
    def get_provinces(self) -> List[str]:
        """Get list of all provinces"""
        return sorted(list(set(d.province for d in self.districts.values())))
    
    def get_districts_in_province(self, province: str) -> List[str]:
        """Get list of districts in a province"""
        return sorted([d.name for d in self.districts.values() if d.province == province])
    
    def get_sectors_in_district(self, district: str) -> List[str]:
        """Get list of sectors in a district"""
        district_obj = self.districts.get(district)
        if district_obj:
            return sorted(district_obj.sectors)
        return []
    
    def get_cells_in_sector(self, sector: str, district: str) -> List[str]:
        """Get list of cells in a sector"""
        sector_key = f"{district}_{sector}"
        sector_obj = self.sectors.get(sector_key)
        if sector_obj:
            return sorted(sector_obj.cells)
        return []
    
    def export_location_summary(self, location: LocationData) -> str:
        """
        Export location summary for reports
        
        Args:
            location: Location data
            
        Returns:
            Formatted summary string
        """
        summary = f"""
LOCATION SUMMARY
================

Administrative Division:
- Province: {location.province}
- District: {location.district}
{f"- Sector: {location.sector}" if location.sector else ""}
{f"- Cell: {location.cell}" if location.cell else ""}

Geographic Coordinates:
- Latitude: {location.latitude:.4f}°
- Longitude: {location.longitude:.4f}°
- Altitude: {location.altitude}m above sea level

Climate Data:
- Climate Zone: {location.climate_zone}
- Average Rainfall: {location.avg_rainfall_mm}mm/year
- Average Temperature: {location.avg_temp_c}°C

Soil & Water:
- Soil Types: {', '.join(location.soil_types)}
- Water Sources: {', '.join(location.water_sources)}
- Irrigation Potential: {location.irrigation_potential}

Demographics:
- Population: {location.population:,}
- Area: {location.area_km2:.1f} km²
"""
        return summary
    
    def get_climate_adjusted_eto(self, location: LocationData, month: int) -> float:
        """
        Get climate-adjusted ETo estimate for location
        
        Args:
            location: Location data
            month: Month (1-12)
            
        Returns:
            Estimated ETo in mm/day
        """
        # Base ETo adjusted for altitude and temperature
        base_eto = 4.0  # mm/day baseline
        
        # Altitude adjustment (higher altitude = lower ETo)
        if location.altitude > 2000:
            altitude_factor = 0.85
        elif location.altitude > 1500:
            altitude_factor = 0.95
        else:
            altitude_factor = 1.05
        
        # Temperature adjustment
        temp_factor = location.avg_temp_c / 20.0
        
        # Seasonal adjustment (Rwanda has two rainy seasons)
        if month in [3, 4, 5, 10, 11]:  # Rainy seasons
            seasonal_factor = 0.9
        else:  # Dry seasons
            seasonal_factor = 1.1
        
        eto = base_eto * altitude_factor * temp_factor * seasonal_factor
        
        return round(eto, 2)


# Convenience function
def create_geographic_service() -> RwandaGeographicService:
    """Create and return geographic service instance"""
    return RwandaGeographicService()
