# ============= src/core/irrigation_service.py =============
"""
Main Integration Service - Ties all components together
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

from src.core.eto_calculator import ETOCalculator
from src.core.etc_calculator import ETCCalculator
from src.core.soil_water_balance import SoilWaterBalance
from src.core.irrigation_scheduler import IrrigationScheduler
from src.models.crop import CropDatabase
from src.models.soil import SoilDatabase
from src.ai.recommender import SystemRecommender
from src.weather.api_client import WeatherAPIClient


class IrrigationDesignService:
    """Complete irrigation system design service"""
    
    def __init__(self):
        self.weather_client = WeatherAPIClient()
        self.recommender = SystemRecommender()
        
    def design_complete_system(
        self,
        crop_name: str,
        soil_type: str,
        area_ha: float,
        latitude: float,
        longitude: float,
        elevation: float,
        planting_date: datetime,
        budget: Optional[float] = None
    ) -> Dict:
        """
        Complete system design workflow
        
        Returns comprehensive design with:
        - System components
        - Cost estimate
        - Irrigation schedule
        - Performance metrics
        """
        
        # 1. Get crop and soil data
        crop = CropDatabase.get_crop(crop_name)
        soil = SoilDatabase.get_soil(soil_type)
        
        if not crop or not soil:
            raise ValueError("Invalid crop or soil type")
        
        # 2. Get weather data
        weather = self.weather_client.get_current_weather(latitude, longitude)
        forecast = self.weather_client.get_forecast(latitude, longitude, days=7)
        
        # 3. Calculate ETo and ETc
        day_of_year = datetime.now().timetuple().tm_yday
        eto = ETOCalculator.calculate_eto(
            tmin=weather.get('temperature', 20) - 5,
            tmax=weather.get('temperature', 20) + 5,
            rhmin=weather.get('humidity', 65) - 10,
            rhmax=weather.get('humidity', 65) + 10,
            wind_speed=weather.get('wind_speed', 2.5),
            sunshine_hours=8,
            latitude=latitude,
            elevation=elevation,
            day_of_year=day_of_year
        )
        
        days_after_planting = (datetime.now() - planting_date).days
        kc = ETCCalculator.get_kc_value(crop, days_after_planting)
        etc = ETCCalculator.calculate_etc(eto, kc)
        
        # 4. Design system components
        system_design = self.recommender.recommend_system_design(
            area_ha=area_ha,
            crop=crop_name,
            soil=soil_type,
            budget=budget
        )
        
        # 5. Initialize water balance
        water_balance = SoilWaterBalance(soil, crop, crop.root_depth)
        
        # 6. Generate irrigation schedule
        scheduler = IrrigationScheduler(depletion_threshold=0.5)
        etc_forecast = [etc] * 7  # Simplified - use forecast in production
        schedule = scheduler.schedule_irrigation(water_balance, etc_forecast, days_ahead=7)
        
        # 7. Calculate water requirements
        daily_water_mm = etc
        daily_water_m3 = daily_water_mm * area_ha * 10  # mm to m³/ha
        seasonal_water = daily_water_m3 * sum(crop.growth_stages_days)
        
        # 8. Performance metrics
        performance = {
            "application_efficiency": 0.90,  # 90% for drip
            "uniformity_coefficient": 0.85,
            "water_savings_vs_flood": 0.50,  # 50% savings
            "expected_yield_increase": 0.25  # 25% increase
        }
        
        # 9. Compile complete design
        complete_design = {
            "project_info": {
                "crop": crop_name,
                "soil": soil_type,
                "area_ha": area_ha,
                "location": {"latitude": latitude, "longitude": longitude, "elevation": elevation},
                "planting_date": planting_date.isoformat(),
                "design_date": datetime.now().isoformat()
            },
            "climate": {
                "current_weather": weather,
                "eto_mm_day": round(eto, 2),
                "etc_mm_day": round(etc, 2),
                "kc": round(kc, 2)
            },
            "system_design": system_design,
            "water_requirements": {
                "daily_mm": round(daily_water_mm, 2),
                "daily_m3": round(daily_water_m3, 2),
                "seasonal_m3": round(seasonal_water, 2),
                "peak_demand_m3_hr": round(daily_water_m3 / 8, 2)  # 8 hours operation
            },
            "irrigation_schedule": schedule,
            "performance": performance,
            "recommendations": self._generate_recommendations(crop, soil, system_design)
        }
        
        return complete_design
    
    def _generate_recommendations(self, crop, soil, system_design: Dict) -> List[str]:
        """Generate agronomic recommendations"""
        recommendations = [
            f"Install emitters at {system_design['emitter_spacing']}m spacing",
            f"Space lateral lines at {system_design['lateral_spacing']}m",
            "Flush system weekly to prevent clogging",
            "Monitor soil moisture regularly",
            "Adjust irrigation based on rainfall",
            f"Expected ROI: {system_design['roi_years']} years",
            "Use fertigation for optimal nutrient delivery",
            "Maintain system pressure at 1.0-1.5 bar"
        ]
        
        if soil.infiltration_rate < 5:
            recommendations.append("Low infiltration rate - reduce irrigation duration, increase frequency")
        
        return recommendations
    
    def calculate_roi(self, system_cost: float, area_ha: float, crop_value_per_ha: float) -> Dict:
        """Calculate Return on Investment"""
        
        # Assumptions
        water_savings_percent = 0.50
        yield_increase_percent = 0.25
        annual_water_cost_saved = 200000 * area_ha * water_savings_percent  # RWF
        annual_yield_increase = crop_value_per_ha * area_ha * yield_increase_percent
        annual_maintenance = system_cost * 0.05  # 5% of system cost
        
        annual_benefit = annual_water_cost_saved + annual_yield_increase - annual_maintenance
        payback_years = system_cost / annual_benefit if annual_benefit > 0 else float('inf')
        
        return {
            "system_cost_rwf": system_cost,
            "annual_water_savings_rwf": annual_water_cost_saved,
            "annual_yield_increase_rwf": annual_yield_increase,
            "annual_maintenance_rwf": annual_maintenance,
            "net_annual_benefit_rwf": annual_benefit,
            "payback_period_years": round(payback_years, 1),
            "5_year_net_benefit_rwf": annual_benefit * 5 - system_cost
        }
