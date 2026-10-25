# ============= src/gis/spatial_utils.py =============
from pyproj import Transformer
from typing import Tuple

class SpatialUtils:
    """Spatial utility functions"""
    
    @staticmethod
    def latlon_to_utm(lat: float, lon: float) -> Tuple[float, float]:
        """Convert lat/lon to UTM coordinates"""
        # Rwanda is in UTM Zone 35S
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32735", always_xy=True)
        x, y = transformer.transform(lon, lat)
        return x, y
    
    @staticmethod
    def utm_to_latlon(x: float, y: float) -> Tuple[float, float]:
        """Convert UTM to lat/lon"""
        transformer = Transformer.from_crs("EPSG:32735", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(x, y)
        return lat, lon
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points (meters) using Haversine"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c