# ============= src/models/soil.py =============
from pydantic import BaseModel, Field
from typing import Optional

class SoilModel(BaseModel):
    name: str
    texture: str
    field_capacity: float = Field(ge=0, le=1, description="Volumetric water content at field capacity")
    wilting_point: float = Field(ge=0, le=1, description="Volumetric water content at wilting point")
    bulk_density: float = Field(gt=0, description="g/cm³")
    infiltration_rate: float = Field(gt=0, description="mm/hr")
    available_water: float = Field(ge=0, le=1, description="Field capacity - wilting point")

class SoilDatabase:
    SOILS = {
        "Sandy Loam": {
            "texture": "Sandy Loam",
            "field_capacity": 0.22,
            "wilting_point": 0.10,
            "bulk_density": 1.55,
            "infiltration_rate": 25.0,
            "available_water": 0.12
        },
        "Loam": {
            "texture": "Loam",
            "field_capacity": 0.30,
            "wilting_point": 0.13,
            "bulk_density": 1.45,
            "infiltration_rate": 13.0,
            "available_water": 0.17
        },
        "Clay Loam": {
            "texture": "Clay Loam",
            "field_capacity": 0.35,
            "wilting_point": 0.18,
            "bulk_density": 1.40,
            "infiltration_rate": 8.0,
            "available_water": 0.17
        },
        "Silty Loam": {
            "texture": "Silty Loam",
            "field_capacity": 0.33,
            "wilting_point": 0.13,
            "bulk_density": 1.40,
            "infiltration_rate": 10.0,
            "available_water": 0.20
        },
        "Sandy Clay Loam": {
            "texture": "Sandy Clay Loam",
            "field_capacity": 0.28,
            "wilting_point": 0.15,
            "bulk_density": 1.50,
            "infiltration_rate": 15.0,
            "available_water": 0.13
        },
        "Clay": {
            "texture": "Clay",
            "field_capacity": 0.40,
            "wilting_point": 0.25,
            "bulk_density": 1.30,
            "infiltration_rate": 2.0,
            "available_water": 0.15
        }
    }
    
    @classmethod
    def get_soil(cls, name: str) -> Optional[SoilModel]:
        if name in cls.SOILS:
            data = cls.SOILS[name]
            return SoilModel(name=name, **data)
        return None