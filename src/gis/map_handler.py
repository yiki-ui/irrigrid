# ============= src/gis/map_handler.py =============
# Lightweight GIS - folium removed (too heavy for desktop)
from typing import Tuple, List, Optional

# Optional folium import
try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    folium = None

class MapHandler:
    """GIS mapping functionality - Lightweight implementation"""
    
    def __init__(self, center: Tuple[float, float] = (-1.9403, 29.8739)):
        self.center = center  # Kigali coordinates
        self.zoom = 12
        
    def create_map(self):
        """Create interactive map (requires folium)"""
        if not FOLIUM_AVAILABLE:
            raise ImportError("Folium not installed. Install with: pip install folium")
        
        m = folium.Map(
            location=self.center,
            zoom_start=self.zoom,
            tiles='OpenStreetMap'
        )
        return m
    
    def add_farm_boundary(self, map_obj, coordinates: List[Tuple]):
        """Add farm boundary polygon (requires folium)"""
        if not FOLIUM_AVAILABLE:
            raise ImportError("Folium not installed")
            
        folium.Polygon(
            locations=coordinates,
            color='green',
            fill=True,
            fillColor='lightgreen',
            fillOpacity=0.4,
            popup='Farm Boundary'
        ).add_to(map_obj)
        
    def calculate_area(self, coordinates: List[Tuple]) -> float:
        """Calculate area in hectares using Shoelace formula"""
        from shapely.geometry import Polygon
        from pyproj import Geod
        
        poly = Polygon(coordinates)
        geod = Geod(ellps="WGS84")
        area, _ = geod.geometry_area_perimeter(poly)
        return abs(area) / 10000  # Convert to hectares
