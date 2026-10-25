# ============= src/core/etc_calculator.py =============
import numpy as np
class ETCCalculator:
    """Crop Evapotranspiration Calculator"""
    
    @staticmethod
    def calculate_etc(eto: float, kc: float) -> float:
        """Calculate crop evapotranspiration (mm/day)"""
        return eto * kc
    
    @staticmethod
    def get_kc_value(crop: 'CropModel', days_after_planting: int) -> float:
        """Get crop coefficient for specific growth stage"""
        stages = crop.growth_stages_days
        cumulative = np.cumsum(stages)
        
        if days_after_planting <= cumulative[0]:
            return crop.kc_initial
        elif days_after_planting <= cumulative[1]:
            # Linear interpolation between initial and mid
            progress = (days_after_planting - cumulative[0]) / stages[1]
            return crop.kc_initial + progress * (crop.kc_mid - crop.kc_initial)
        elif days_after_planting <= cumulative[2]:
            return crop.kc_mid
        elif days_after_planting <= cumulative[3]:
            # Linear interpolation between mid and end
            progress = (days_after_planting - cumulative[2]) / stages[3]
            return crop.kc_mid + progress * (crop.kc_end - crop.kc_mid)
        else:
            return crop.kc_end
