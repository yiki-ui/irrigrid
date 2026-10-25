# ============= tests/test_core/test_water_balance.py =============
import pytest
from src.core.soil_water_balance import SoilWaterBalance
from src.models.soil import SoilDatabase
from src.models.crop import CropDatabase

def test_water_balance_initialization():
    """Test water balance initialization"""
    soil = SoilDatabase.get_soil("Clay Loam")
    crop = CropDatabase.get_crop("Tomato")
    
    wb = SoilWaterBalance(soil, crop, root_depth=0.5)
    
    assert wb.taw > 0
    assert wb.raw > 0
    assert wb.current_depletion == 0

def test_water_balance_update():
    """Test water balance daily update"""
    soil = SoilDatabase.get_soil("Sandy Loam")
    crop = CropDatabase.get_crop("Tomato")
    
    wb = SoilWaterBalance(soil, crop, root_depth=0.5)
    
    # Simulate one day with ETc=5mm, no rain, no irrigation
    result = wb.update(etc=5.0, rainfall=0, irrigation=0)
    
    assert result['depletion'] == 5.0
    assert result['stress_coefficient'] <= 1.0
    assert result['stress_coefficient'] >= 0.0

def test_irrigation_need():
    """Test irrigation need calculation"""
    soil = SoilDatabase.get_soil("Clay Loam")
    crop = CropDatabase.get_crop("Onion")
    
    wb = SoilWaterBalance(soil, crop, root_depth=0.4)
    wb.current_depletion = 30  # 30mm depleted
    
    need = wb.get_irrigation_need()
    
    assert need == 30