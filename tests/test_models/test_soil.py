# ============= tests/test_models/test_soil.py =============
import pytest
from src.models.soil import SoilDatabase, SoilModel

def test_soil_database():
    """Test soil database"""
    clay = SoilDatabase.get_soil("Clay Loam")
    
    assert clay is not None
    assert clay.name == "Clay Loam"
    assert clay.field_capacity > clay.wilting_point
    assert clay.total_available_water > 0

def test_soil_taw_calculation():
    """Test TAW calculation"""
    soil = SoilDatabase.get_soil("Sandy Loam")
    taw = soil.total_available_water
    
    assert taw == soil.field_capacity - soil.wilting_point
    assert taw > 0

def test_soil_raw_calculation():
    """Test RAW calculation"""
    soil = SoilDatabase.get_soil("Volcanic Soil (Andosol)")
    raw = soil.readily_available_water
    
    assert raw == 0.5 * soil.total_available_water
