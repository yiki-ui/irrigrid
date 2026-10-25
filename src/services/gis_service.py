#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GIS Service - Enhanced Geographic Data Service
Works with processed GeoJSON files and provides spatial analysis

Uses lightweight shapely + pyproj (no geopandas needed for runtime)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

try:
    from shapely.geometry import shape, Point, Polygon, LineString
    from shapely.ops import nearest_points
    import pyproj
    HAS_SPATIAL = True
except ImportError:
    HAS_SPATIAL = False
    print("⚠️  Warning: shapely/pyproj not available. Limited GIS functionality.")


@dataclass
class SpatialFeature:
    """Spatial feature with geometry and properties"""
    id: str
    geometry: any  # Shapely geometry object
    properties: Dict
    bounds: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)


@dataclass
class TerrainInfo:
    """Terrain information for a location"""
    elevation: float
    slope: float
    aspect: float
    catchment: Optional[str]
    erosion_risk: Optional[str]


@dataclass
class WaterSourceInfo:
    """Water source information"""
    source_type: str  # 'river', 'lake', 'wetland', 'borehole'
    name: str
    distance_m: float
    elevation_diff_m: float
    is_gravity_feasible: bool
    coordinates: Tuple[float, float]


class GISService:
    """
    Enhanced GIS Service for Irrigation DSS
    Works with processed GeoJSON files
    """
    
    def __init__(self, data_dir: str = None):
        """Initialize GIS service"""
        
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "processed_gis"
        else:
            self.data_dir = Path(data_dir)
        
        # Cache for loaded data
        self._cache = {}
        
        # Initialize coordinate transformer (for distance calculations)
        if HAS_SPATIAL:
            self.geodesic = pyproj.Geod(ellps='WGS84')
        
        print(f"📍 GIS Service initialized: {self.data_dir}")
    
    def _load_geojson(self, filename: str) -> List[SpatialFeature]:
        """
        Load GeoJSON file and convert to SpatialFeatures
        
        Args:
            filename: Name of GeoJSON file
            
        Returns:
            List of SpatialFeature objects
        """
        # Check cache
        if filename in self._cache:
            return self._cache[filename]
        
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  File not found: {filepath}")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            features = []
            for i, feature in enumerate(geojson_data.get('features', [])):
                if not HAS_SPATIAL:
                    continue
                
                geom = shape(feature['geometry'])
                
                spatial_feature = SpatialFeature(
                    id=feature.get('id', str(i)),
                    geometry=geom,
                    properties=feature.get('properties', {}),
                    bounds=geom.bounds
                )
                features.append(spatial_feature)
            
            # Cache the data
            self._cache[filename] = features
            
            print(f"✅ Loaded: {filename} ({len(features)} features)")
            return features
            
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return []
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points (meters)
        
        Args:
            lat1, lon1: First point
            lat2, lon2: Second point
            
        Returns:
            Distance in meters
        """
        if HAS_SPATIAL:
            # Accurate geodesic distance
            _, _, distance = self.geodesic.inv(lon1, lat1, lon2, lat2)
            return distance
        else:
            # Fallback: Haversine formula
            R = 6371000  # Earth radius in meters
            
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            return R * c
    
    def find_nearest_river(self, latitude: float, longitude: float) -> Optional[WaterSourceInfo]:
        """
        Find nearest river to a point
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            WaterSourceInfo or None
        """
        if not HAS_SPATIAL:
            return None
        
        # Load rivers
        rivers = self._load_geojson('rwanda_rivers.geojson')
        if not rivers:
            return None
        
        point = Point(longitude, latitude)
        
        nearest_river = None
        min_distance = float('inf')
        
        for river in rivers:
            # Calculate distance to river
            distance = point.distance(river.geometry)
            
            if distance < min_distance:
                min_distance = distance
                nearest_river = river
        
        if nearest_river:
            # Get nearest point on river
            nearest_pt = nearest_points(point, nearest_river.geometry)[1]
            
            # Convert distance from degrees to meters (approximate)
            distance_m = self.calculate_distance(
                latitude, longitude,
                nearest_pt.y, nearest_pt.x
            )
            
            return WaterSourceInfo(
                source_type='river',
                name=nearest_river.properties.get('NAME', 'Unknown River'),
                distance_m=distance_m,
                elevation_diff_m=0,  # Would need DEM data
                is_gravity_feasible=False,  # Would need elevation analysis
                coordinates=(nearest_pt.x, nearest_pt.y)
            )
        
        return None
    
    def get_catchment_info(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Determine which catchment a point falls in
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            Catchment name or None
        """
        if not HAS_SPATIAL:
            return None
        
        # Load catchments
        catchments = self._load_geojson('catchments_level1.geojson')
        if not catchments:
            return None
        
        point = Point(longitude, latitude)
        
        for catchment in catchments:
            if catchment.geometry.contains(point):
                return catchment.properties.get('NAME', 'Unknown Catchment')
        
        return None
    
    def get_administrative_location(self, latitude: float, longitude: float) -> Dict:
        """
        Get administrative location (province, district, sector)
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            Dict with administrative info
        """
        if not HAS_SPATIAL:
            return {}
        
        point = Point(longitude, latitude)
        location_info = {}
        
        # Check districts
        districts = self._load_geojson('rwanda_districts.geojson')
        for district in districts:
            if district.geometry.contains(point):
                location_info['district'] = district.properties.get('NAME_2', 'Unknown')
                location_info['province'] = district.properties.get('NAME_1', 'Unknown')
                break
        
        # Check sectors (if available)
        sectors = self._load_geojson('rwanda_sectors.geojson')
        for sector in sectors:
            if sector.geometry.contains(point):
                location_info['sector'] = sector.properties.get('NAME_3', 'Unknown')
                break
        
        return location_info
    
    def calculate_field_area(self, coordinates: List[Tuple[float, float]]) -> float:
        """
        Calculate area of irregular polygon (hectares)
        
        Args:
            coordinates: List of (lon, lat) tuples
            
        Returns:
            Area in hectares
        """
        if not HAS_SPATIAL or len(coordinates) < 3:
            return 0
        
        # Create polygon
        polygon = Polygon(coordinates)
        
        # Calculate geodesic area (square meters)
        # Note: For accurate area calculation, we need to project to UTM
        # This is a simplified calculation
        
        # Get centroid for local UTM zone calculation
        centroid = polygon.centroid
        lon, lat = centroid.x, centroid.y
        
        # Determine UTM zone
        utm_zone = int((lon + 180) / 6) + 1
        utm_crs = f"EPSG:{32600 + utm_zone if lat >= 0 else 32700 + utm_zone}"
        
        # Project to UTM
        transformer = pyproj.Transformer.from_crs(
            "EPSG:4326",  # WGS84
            utm_crs,
            always_xy=True
        )
        
        # Transform coordinates
        utm_coords = [transformer.transform(lon, lat) for lon, lat in coordinates]
        utm_polygon = Polygon(utm_coords)
        
        # Area in square meters
        area_m2 = utm_polygon.area
        
        # Convert to hectares
        area_ha = area_m2 / 10000
        
        return area_ha
    
    def get_rainfall_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Get rainfall data for location (from nearest station)
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            Dict with rainfall info
        """
        if not HAS_SPATIAL:
            return None
        
        # Load rainfall stations
        stations = self._load_geojson('rainfall_stations.geojson')
        if not stations:
            return None
        
        point = Point(longitude, latitude)
        
        nearest_station = None
        min_distance = float('inf')
        
        for station in stations:
            distance = point.distance(station.geometry)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        if nearest_station:
            distance_m = self.calculate_distance(
                latitude, longitude,
                nearest_station.geometry.y, nearest_station.geometry.x
            )
            
            return {
                'station_name': nearest_station.properties.get('Name', 'Unknown'),
                'distance_km': distance_m / 1000,
                'annual_rainfall_mm': nearest_station.properties.get('Rainfall', 0),
                # Add monthly data if available in properties
            }
        
        return None
    
    def assess_erosion_risk(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Assess erosion risk at location
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            Risk level: 'low', 'medium', 'high', or None
        """
        if not HAS_SPATIAL:
            return None
        
        # Load erosion data
        erosion_zones = self._load_geojson('erosion_control.geojson')
        if not erosion_zones:
            return None
        
        point = Point(longitude, latitude)
        
        for zone in erosion_zones:
            if zone.geometry.contains(point):
                # Extract risk level from properties
                # Adjust field name based on actual data
                risk = zone.properties.get('RISK', zone.properties.get('EROSION', 'unknown'))
                return str(risk).lower()
        
        return 'low'  # Default if not in high-risk zone
    
    def calculate_pipe_distance(self, 
                               field_coords: List[Tuple[float, float]],
                               water_source: Tuple[float, float]) -> float:
        """
        Calculate approximate pipe distance from water source to field
        
        Args:
            field_coords: Field polygon coordinates [(lon, lat), ...]
            water_source: Water source coordinates (lon, lat)
            
        Returns:
            Distance in meters
        """
        if not HAS_SPATIAL or len(field_coords) < 3:
            return 0
        
        # Find nearest point on field boundary to water source
        field_polygon = Polygon(field_coords)
        water_point = Point(water_source)
        
        nearest_pt = nearest_points(water_point, field_polygon)[1]
        
        # Calculate distance
        distance_m = self.calculate_distance(
            water_point.y, water_point.x,
            nearest_pt.y, nearest_pt.x
        )
        
        return distance_m
    
    def export_field_to_geojson(self, 
                                field_coords: List[Tuple[float, float]],
                                properties: Dict = None) -> str:
        """
        Export field polygon to GeoJSON string
        
        Args:
            field_coords: Field coordinates [(lon, lat), ...]
            properties: Additional properties
            
        Returns:
            GeoJSON string
        """
        if len(field_coords) < 3:
            return "{}"
        
        # Ensure polygon is closed
        if field_coords[0] != field_coords[-1]:
            field_coords = field_coords + [field_coords[0]]
        
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [field_coords]
            },
            "properties": properties or {}
        }
        
        return json.dumps(geojson, indent=2)
    
    def export_field_to_kml(self,
                           field_coords: List[Tuple[float, float]],
                           name: str = "Irrigation Field",
                           description: str = "") -> str:
        """
        Export field to KML for Google Earth
        
        Args:
            field_coords: Field coordinates [(lon, lat), ...]
            name: Field name
            description: Description
            
        Returns:
            KML string
        """
        # Ensure polygon is closed
        if field_coords[0] != field_coords[-1]:
            field_coords = field_coords + [field_coords[0]]
        
        # Generate coordinate string
        coord_string = " ".join([f"{lon},{lat},0" for lon, lat in field_coords])
        
        kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <description>{description}</description>
    <Placemark>
      <name>{name}</name>
      <description>{description}</description>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              {coord_string}
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""
        
        return kml
    
    def get_data_availability(self) -> Dict:
        """
        Check which GIS datasets are available
        
        Returns:
            Dict with availability status
        """
        datasets = {
            'rivers': 'rwanda_rivers.geojson',
            'catchments_l1': 'catchments_level1.geojson',
            'catchments_l2': 'catchments_level2.geojson',
            'districts': 'rwanda_districts.geojson',
            'sectors': 'rwanda_sectors.geojson',
            'provinces': 'rwanda_provinces.geojson',
            'rainfall': 'rainfall_stations.geojson',
            'erosion': 'erosion_control.geojson'
        }
        
        availability = {}
        for name, filename in datasets.items():
            filepath = self.data_dir / filename
            availability[name] = filepath.exists()
        
        return availability


def create_gis_service() -> GISService:
    """Create and return GIS service instance"""
    return GISService()


# Example usage
if __name__ == "__main__":
    service = GISService()
    
    # Check data availability
    print("\n📊 Data Availability:")
    availability = service.get_data_availability()
    for dataset, available in availability.items():
        status = "✅" if available else "❌"
        print(f"   {status} {dataset}")
    
    # Example: Find nearest river to Kigali
    print("\n🌊 Finding nearest river to Kigali...")
    kigali_lat, kigali_lon = -1.9536, 30.0606
    
    river_info = service.find_nearest_river(kigali_lat, kigali_lon)
    if river_info:
        print(f"   River: {river_info.name}")
        print(f"   Distance: {river_info.distance_m:.0f} meters")
    
    # Example: Calculate field area
    print("\n📐 Calculating field area...")
    field_coords = [
        (30.0, -2.0),
        (30.01, -2.0),
        (30.01, -2.01),
        (30.0, -2.01)
    ]
    area = service.calculate_field_area(field_coords)
    print(f"   Area: {area:.2f} hectares")
