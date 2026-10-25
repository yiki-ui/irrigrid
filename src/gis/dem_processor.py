# ============= src/gis/dem_processor.py =============
import numpy as np
from typing import Tuple

class DEMProcessor:
    """Digital Elevation Model processing"""
    
    @staticmethod
    def calculate_slope(dem: np.ndarray, cell_size: float = 30) -> np.ndarray:
        """
        Calculate slope from DEM
        
        Args:
            dem: 2D array of elevation values
            cell_size: Grid cell size in meters
        
        Returns:
            Slope array in degrees
        """
        # Calculate gradients
        dx, dy = np.gradient(dem, cell_size)
        
        # Calculate slope
        slope = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_degrees = np.degrees(slope)
        
        return slope_degrees
    
    @staticmethod
    def calculate_aspect(dem: np.ndarray, cell_size: float = 30) -> np.ndarray:
        """Calculate aspect (direction of slope)"""
        dx, dy = np.gradient(dem, cell_size)
        aspect = np.arctan2(-dy, dx)
        aspect_degrees = np.degrees(aspect)
        aspect_degrees = (aspect_degrees + 360) % 360  # Normalize to 0-360
        
        return aspect_degrees
    
    @staticmethod
    def generate_sample_dem(size: Tuple[int, int], base_elevation: float = 1500) -> np.ndarray:
        """Generate synthetic DEM for testing"""
        rows, cols = size
        x = np.linspace(0, cols, cols)
        y = np.linspace(0, rows, rows)
        X, Y = np.meshgrid(x, y)
        
        # Create gentle slope with some variation
        dem = base_elevation + 0.5 * X + 0.3 * Y + 10 * np.sin(X/10) * np.cos(Y/10)
        
        return dem
