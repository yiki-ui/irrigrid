# ============= tests/test_core/test_eto.py =============
import pytest
from src.core.eto_calculator import ETOCalculator

def test_eto_calculation():
    """Test ETo calculation"""
    calc = ETOCalculator()
    
    eto = calc.calculate_eto(
        tmin=15.0,
        tmax=25.0,
        rhmin=50.0,
        rhmax=85.0,
        wind_speed=2.0,
        sunshine_hours=8.0,
        latitude=-1.9,
        elevation=1500,
        day_of_year=180
    )
    
    assert eto > 0
    assert eto < 15  # Reasonable range
    assert isinstance(eto, float)

def test_eto_boundary_conditions():
    """Test ETo with boundary conditions"""
    calc = ETOCalculator()
    
    # Very hot day
    eto_hot = calc.calculate_eto(
        tmin=20.0, tmax=35.0, rhmin=30.0, rhmax=60.0,
        wind_speed=3.0, sunshine_hours=10.0,
        latitude=-1.9, elevation=1500, day_of_year=180
    )
    
    # Cloudy cool day
    eto_cool = calc.calculate_eto(
        tmin=12.0, tmax=18.0, rhmin=70.0, rhmax=95.0,
        wind_speed=1.0, sunshine_hours=2.0,
        latitude=-1.9, elevation=1500, day_of_year=180
    )
    
    assert eto_hot > eto_cool
