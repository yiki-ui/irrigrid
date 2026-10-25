# ============= src/ai/recommender.py =============
from typing import Dict, List

class SystemRecommender:
    """Recommend drip system components"""
    
    @staticmethod
    def recommend_emitter(soil_type: str, flow_rate_range: str = "medium") -> Dict:
        """Recommend emitter specifications"""
        recommendations = {
            "Sandy Loam": {
                "type": "Pressure Compensating",
                "flow_rate": 2.0,  # L/h
                "spacing": 0.3,  # m
                "reason": "Higher infiltration rate requires closer spacing"
            },
            "Clay Loam": {
                "type": "Non-Pressure Compensating",
                "flow_rate": 1.5,  # L/h
                "spacing": 0.4,  # m
                "reason": "Lower infiltration, wider wetting pattern"
            },
            "Volcanic Soil (Andosol)": {
                "type": "Pressure Compensating",
                "spacing": 0.35,  # m
                "reason": "Good water holding capacity"
            }
        }
        
        return recommendations.get(soil_type, recommendations["Clay Loam"])
    
    @staticmethod
    def recommend_lateral_spacing(crop_type: str, soil_type: str) -> float:
        """Recommend lateral line spacing based on crop and soil"""
        crop_spacing = {
            "Tomato": 1.5,
            "Bell Pepper": 1.5,
            "Cabbage": 1.0,
            "Onion": 0.5,
            "Carrot": 0.5,
            "Avocado": 3.0,
            "Mango": 4.0,
            "Banana": 2.5
        }
        return crop_spacing.get(crop_type, 1.5)
    
    @staticmethod
    def recommend_system_design(area_ha: float, crop: str, soil: str, budget: float = None) -> Dict:
        """Complete system design recommendation"""
        emitter_rec = SystemRecommender.recommend_emitter(soil)
        lateral_spacing = SystemRecommender.recommend_lateral_spacing(crop, soil)
        
        # Calculate components
        area_m2 = area_ha * 10000
        num_laterals = area_m2 / (lateral_spacing * 100)  # Assuming 100m lateral length
        emitters_per_lateral = 100 / emitter_rec["spacing"]
        total_emitters = int(num_laterals * emitters_per_lateral)
        
        # Cost estimation (Rwanda prices in RWF)
        emitter_cost = total_emitters * 150  # 150 RWF per emitter
        pipe_cost = num_laterals * 100 * 500  # 500 RWF per meter
        pump_cost = 500000 if area_ha > 0.5 else 0
        filter_cost = 200000
        installation_cost = (emitter_cost + pipe_cost) * 0.3
        
        total_cost = emitter_cost + pipe_cost + pump_cost + filter_cost + installation_cost
        
        return {
            "emitter_type": emitter_rec["type"],
            "emitter_flow_rate": emitter_rec["flow_rate"],
            "emitter_spacing": emitter_rec["spacing"],
            "lateral_spacing": lateral_spacing,
            "total_emitters": total_emitters,
            "total_cost_rwf": total_cost,
            "cost_per_hectare": total_cost / area_ha,
            "estimated_water_savings": "40-60%",
            "roi_years": 2.5
        }