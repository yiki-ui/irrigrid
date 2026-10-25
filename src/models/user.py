# ============================================
# FILE: src/models/user.py
# Pydantic models for User data validation
# ============================================

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    full_name: Optional[str] = None
    role: str = Field(default="farmer", pattern="^(farmer|extension_officer|admin)$")
    organization: Optional[str] = None
    phone: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    sector: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
