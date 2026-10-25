# ============= src/database/models.py =============
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    role = Column(String(20), default="farmer")  # farmer, extension_officer, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Location
    province = Column(String(50))
    district = Column(String(50))
    sector = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    elevation = Column(Float)
    
    # Farm details
    area_hectares = Column(Float)
    crop_name = Column(String(50))
    soil_type = Column(String(50))
    planting_date = Column(DateTime)
    
    # System design
    emitter_spacing = Column(Float)
    lateral_spacing = Column(Float)
    emitter_flow_rate = Column(Float)
    
    # Status
    status = Column(String(20), default="draft")  # draft, active, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="projects")
    irrigation_events = relationship("IrrigationEvent", back_populates="project")
    chat_sessions = relationship("ChatSession", back_populates="project")

class IrrigationEvent(Base):
    __tablename__ = "irrigation_events"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    date = Column(DateTime)
    amount_mm = Column(Float)
    duration_hours = Column(Float)
    status = Column(String(20), default="scheduled")  # scheduled, completed, skipped
    notes = Column(Text)
    
    project = relationship("Project", back_populates="irrigation_events")