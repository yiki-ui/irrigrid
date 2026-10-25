# ============= src/utils/converters.py =============
class UnitConverter:
    """Unit conversion utilities"""
    
    @staticmethod
    def mm_to_m3_per_ha(mm: float) -> float:
        """Convert mm of water to m³ per hectare"""
        return mm * 10  # 1 mm over 1 ha = 10 m³
    
    @staticmethod
    def m3_per_ha_to_mm(m3: float) -> float:
        """Convert m³ per hectare to mm"""
        return m3 / 10
    
    @staticmethod
    def liters_per_hour_to_m3_per_day(lph: float) -> float:
        """Convert L/h to m³/day"""
        return lph * 24 / 1000
    
    @staticmethod
    def celsius_to_fahrenheit(c: float) -> float:
        """Convert Celsius to Fahrenheit"""
        return (c * 9/5) + 32