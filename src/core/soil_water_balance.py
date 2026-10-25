# ============= src/core/soil_water_balance.py =============
class SoilWaterBalance:
    """Daily soil water balance model"""
    
    def __init__(self, soil, crop, root_depth: float):
        self.soil = soil
        self.crop = crop
        self.root_depth = root_depth
        self.taw = soil.available_water * root_depth * 1000  # mm (Total Available Water)
        self.raw = self.taw * 0.5  # mm (Readily Available Water - 50% of TAW)
        self.current_depletion = 0  # mm
        
    def update(self, etc: float, rainfall: float, irrigation: float) -> dict:
        """
        Update daily water balance
        Returns dict with: depletion, drainage, runoff
        """
        # Water input
        water_input = rainfall + irrigation
        
        # Update depletion
        self.current_depletion = self.current_depletion + etc - water_input
        
        # Calculate drainage (deep percolation)
        drainage = 0
        if self.current_depletion < 0:
            drainage = abs(self.current_depletion)
            self.current_depletion = 0
        
        # Check if exceeds TAW (should not happen normally)
        if self.current_depletion > self.taw:
            self.current_depletion = self.taw
        
        # Calculate water stress
        if self.current_depletion > self.raw:
            stress_coefficient = 1 - (self.current_depletion - self.raw) / (self.taw - self.raw)
        else:
            stress_coefficient = 1.0
        
        return {
            "depletion": self.current_depletion,
            "drainage": drainage,
            "stress_coefficient": max(0, min(1, stress_coefficient)),
            "soil_moisture_deficit": self.current_depletion / self.taw
        }
    
    def get_irrigation_need(self) -> float:
        """Calculate irrigation requirement to refill to field capacity"""
        return max(0, self.current_depletion)