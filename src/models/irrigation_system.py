# ============= src/models/irrigation_system.py =============
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum

class EmitterType(str, Enum):
    INLINE = "inline"
    ONLINE = "online"
    BUTTON = "button"
    MICRO_SPRINKLER = "micro_sprinkler"

class SystemType(str, Enum):
    DRIP = "drip"
    MICRO_SPRINKLER = "micro_sprinkler"
    SUBSURFACE = "subsurface"

class IrrigationSystemDesign(BaseModel):
    """Complete irrigation system design"""
    system_type: SystemType = SystemType.DRIP
    emitter_type: EmitterType = EmitterType.INLINE
    emitter_flow_rate: float = Field(..., gt=0, description="Liters/hour")
    emitter_spacing: float = Field(..., gt=0, description="meters")
    lateral_spacing: float = Field(..., gt=0, description="meters")
    lateral_diameter: float = Field(default=16, description="mm")
    mainline_diameter: float = Field(default=50, description="mm")
    submain_diameter: float = Field(default=32, description="mm")
    operating_pressure: float = Field(default=1.5, description="bar")
    filtration_type: str = Field(default="screen")
    pump_required: bool = True
    pump_power: Optional[float] = Field(None, description="kW")
    tank_capacity: Optional[float] = Field(None, description="m³")
    
class SystemComponents(BaseModel):
    """Bill of materials for irrigation system"""
    emitters: int
    lateral_pipes_m: float
    submain_pipes_m: float
    mainline_pipes_m: float
    filters: int
    fertilizer_tank: int
    valves: int
    fittings: Dict[str, int]
    pump_hp: Optional[float] = None
    
class CostEstimate(BaseModel):
    """Cost breakdown"""
    emitters_cost: float
    pipes_cost: float
    fittings_cost: float
    pump_cost: float
    filtration_cost: float
    installation_cost: float
    total_cost: float
    cost_per_hectare: float
    
class SystemPerformance(BaseModel):
    """System performance metrics"""
    application_efficiency: float = Field(ge=0, le=1)
    uniformity_coefficient: float = Field(ge=0, le=1)
    distribution_uniformity: float = Field(ge=0, le=1)
    application_rate: float = Field(description="mm/hour")
    wetted_area_percentage: float = Field(ge=0, le=100)
