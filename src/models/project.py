# ============================================
# FILE: src/models/project.py
# Pydantic models for Project data validation
# ============================================

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    province: str
    district: str
    sector: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    farm_area: float = Field(..., gt=0, description="Farm area in hectares")
    irrigated_area: Optional[float] = Field(None, gt=0, description="Irrigated area in hectares")
    
    @validator('irrigated_area')
    def validate_irrigated_area(cls, v, values):
        if v and 'farm_area' in values and v > values['farm_area']:
            raise ValueError('Irrigated area cannot exceed farm area')
        return v


class ProjectCreate(ProjectBase):
    crop_id: Optional[int] = None
    planting_date: Optional[datetime] = None
    soil_type: Optional[str] = None
    water_source_type: Optional[str] = None
    budget: Optional[float] = Field(None, gt=0)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|completed|archived)$")
    planting_date: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    soil_type: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    status: str
    crop_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectDetail(ProjectResponse):
    """Detailed project info with all fields"""
    elevation: Optional[float] = None
    slope: Optional[float] = None
    soil_texture: Optional[str] = None
    field_capacity: Optional[float] = None
    wilting_point: Optional[float] = None
    water_flow_rate: Optional[float] = None
    system_design: Optional[Dict[str, Any]] = None
    installation_cost: Optional[float] = None
    roi: Optional[float] = None
