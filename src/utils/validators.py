# ============= src/utils/validators.py =============
from typing import Tuple, Dict
import re

class DataValidator:
    """Validation utilities"""
    
    @staticmethod
    def calculate_lateral_length(area_ha: float, row_spacing: float) -> float:
        """Calculate recommended lateral length"""
        # Avoid excessive pressure loss - max 50-60m for PE laterals
        area_m2 = area_ha * 10000
        width = (area_m2 / 100) ** 0.5  # Assume squarish plot
        return min(60, width)
    
    @staticmethod
    def estimate_pump_requirements(
        total_flow: float, elevation_diff: float, pipe_length: float
    ) -> Dict:
        """
        Estimate pump specifications
        
        Args:
            total_flow: Total system flow (m³/h)
            elevation_diff: Elevation difference (m)
            pipe_length: Total pipe length (m)
        
        Returns:
            Dict with pump power and head requirements
        """
        # Friction loss estimation (simplified)
        friction_loss = pipe_length * 0.05  # 5% per 100m approximation
        
        # Required pressure head (m)
        system_pressure = 10  # 1 bar = 10m for drip
        total_head = elevation_diff + friction_loss + system_pressure
        
        # Power calculation (kW)
        efficiency = 0.7  # Pump efficiency
        power = (total_flow * total_head * 9.81) / (3600 * efficiency * 1000)
        
        return {
            "total_head_m": round(total_head, 2),
            "flow_rate_m3h": round(total_flow, 2),
            "power_kw": round(power, 2),
            "recommended_pump_type": "Centrifugal" if power < 5 else "Multi-stage"
        }