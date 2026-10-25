# ============= src/core/irrigation_scheduler.py =============
from datetime import datetime, timedelta
from typing import List, Dict
from .soil_water_balance import SoilWaterBalance

class IrrigationScheduler:
    """AI-powered irrigation scheduling"""
    
    def __init__(self, depletion_threshold: float = 0.5):
        self.depletion_threshold = depletion_threshold  # Fraction of RAW
        
    def schedule_irrigation(
        self, water_balance: SoilWaterBalance, etc_forecast: List[float],
        days_ahead: int = 7
    ) -> List[Dict]:
        """
        Generate irrigation schedule
        
        Returns list of irrigation events with date and amount
        """
        schedule = []
        current_depletion = water_balance.current_depletion
        threshold = water_balance.raw * self.depletion_threshold
        
        for day in range(days_ahead):
            etc = etc_forecast[day] if day < len(etc_forecast) else etc_forecast[-1]
            current_depletion += etc
            
            if current_depletion >= threshold:
                irrigation_amount = current_depletion
                schedule.append({
                    "day": day,
                    "date": datetime.now() + timedelta(days=day),
                    "amount_mm": round(irrigation_amount, 2),
                    "duration_hours": self._calculate_duration(irrigation_amount)
                })
                current_depletion = 0
        
        return schedule
    
    def _calculate_duration(self, amount_mm: float, emitter_flow_rate: float = 2.0) -> float:
        """
        Calculate irrigation duration in hours
        emitter_flow_rate: liters/hour per emitter
        """
        # Simplified calculation - needs system-specific parameters
        return round(amount_mm / 10, 2)  # Rough estimate