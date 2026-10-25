# ============= src/core/eto_calculator.py =============
"""
FAO-56 Penman-Monteith Reference Evapotranspiration Calculator

This module implements the standard FAO-56 Penman-Monteith equation
for calculating daily reference evapotranspiration (ET0).

Reference: FAO-56 Penman-Monteith method
https://www.fao.org/3/x0490e/x0490e00.htm
"""

import numpy as np
from typing import Tuple, Optional


class ETOCalculatorError(Exception):
    """Custom exception for ETo calculation errors"""
    pass


class ETOCalculator:
    """
    FAO Penman-Monteith Reference Evapotranspiration Calculator
    
    This class provides methods to calculate daily reference evapotranspiration
    using the FAO-56 Penman-Monteith equation.
    """
    
    # Valid ranges for all parameters (min, max)
    VALID_RANGES = {
        'tmin': (-50, 60),        # °C
        'tmax': (-50, 60),        # °C
        'rhmin': (0, 100),        # %
        'rhmax': (0, 100),        # %
        'wind_speed': (0, 30),     # m/s
        'sunshine_hours': (0, 24),  # hours
        'latitude': (-90, 90),    # degrees
        'elevation': (-500, 9000), # meters
        'day_of_year': (1, 366)
    }
    
    @classmethod
    def validate(cls, **params) -> None:
        """
        Validate all parameters before calculation.
        
        Args:
            **params: Parameters to validate
            
        Raises:
            ETOCalculatorError: If any parameter is out of valid range
        """
        for param, (min_val, max_val) in cls.VALID_RANGES.items():
            if param in params:
                val = params[param]
                
                # Check type
                if not isinstance(val, (int, float)):
                    raise ETOCalculatorError(
                        f"Parameter '{param}' must be numeric, got {type(val).__name__}"
                    )
                
                # Check range
                if not min_val <= val <= max_val:
                    raise ETOCalculatorError(
                        f"Parameter '{param}'={val} out of valid range [{min_val}, {max_val}]"
                    )
        
        # Additional cross-validation
        if 'tmin' in params and 'tmax' in params:
            if params['tmin'] > params['tmax']:
                raise ETOCalculatorError(
                    f"tmin ({params['tmin']}) cannot be greater than tmax ({params['tmax']})"
                )
        
        if 'rhmin' in params and 'rhmax' in params:
            if params['rhmin'] > params['rhmax']:
                raise ETOCalculatorError(
                    f"rhmin ({params['rhmin']}) cannot be greater than rhmax ({params['rhmax']})"
                )
    
    @staticmethod
    def calculate_eto(
        tmin: float, 
        tmax: float, 
        rhmin: float, 
        rhmax: float,
        wind_speed: float, 
        sunshine_hours: float, 
        latitude: float,
        elevation: float, 
        day_of_year: int
    ) -> float:
        """
        Calculate daily reference evapotranspiration (mm/day)
        
        FAO-56 Penman-Monteith equation implementation.
        
        Args:
            tmin: Minimum daily temperature (°C)
            tmax: Maximum daily temperature (°C)
            rhmin: Minimum relative humidity (%)
            rhmax: Maximum relative humidity (%)
            wind_speed: Wind speed at 2m height (m/s)
            sunshine_hours: Actual sunshine duration (hours)
            latitude: Latitude (decimal degrees, positive = north)
            elevation: Elevation above sea level (m)
            day_of_year: Day of year (1-365)
            
        Returns:
            Daily reference evapotranspiration (mm/day)
            
        Raises:
            ETOCalculatorError: If any parameter is invalid
            
        Example:
            >>> calc = ETOCalculator()
            >>> eto = calc.calculate_eto(18, 28, 50, 90, 2.0, 8.5, -1.9403, 1500, 180)
            >>> print(f"ET0 = {eto:.2f} mm/day")
        """
        # Validate inputs
        ETOCalculator.validate(
            tmin=tmin, tmax=tmax, 
            rhmin=rhmin, rhmax=rhmax,
            wind_speed=wind_speed, 
            sunshine_hours=sunshine_hours,
            latitude=latitude, 
            elevation=elevation, 
            day_of_year=day_of_year
        )
        
        # Mean temperature (°C)
        tmean = (tmax + tmin) / 2
        
        # Atmospheric pressure (kPa)
        # FAO-56 Eq. 7
        P = 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26
        
        # Psychrometric constant (kPa/°C)
        # FAO-56 Eq. 8
        gamma = 0.000665 * P
        
        # Saturation vapor pressure (kPa)
        # FAO-56 Eq. 11
        es_tmax = 0.6108 * np.exp((17.27 * tmax) / (tmax + 237.3))
        es_tmin = 0.6108 * np.exp((17.27 * tmin) / (tmin + 237.3))
        es = (es_tmax + es_tmin) / 2  # Mean saturation vapor pressure
        
        # Actual vapor pressure (kPa)
        # FAO-56 Eq. 19
        ea = (es_tmin * rhmax / 100 + es_tmax * rhmin / 100) / 2
        
        # Slope of saturation vapor pressure curve (kPa/°C)
        # FAO-56 Eq. 13
        delta = (4098 * es) / ((tmean + 237.3) ** 2)
        
        # Solar radiation calculations
        # Relative distance Earth-Sun
        lat_rad = np.deg2rad(latitude)
        dr = 1 + 0.033 * np.cos(2 * np.pi * day_of_year / 365)
        
        # Solar declination (radians)
        # FAO-56 Eq. 24
        delta_solar = 0.409 * np.sin(2 * np.pi * day_of_year / 365 - 1.39)
        
        # Sunset hour angle (radians)
        # FAO-56 Eq. 25
        ws = np.arccos(-np.tan(lat_rad) * np.tan(delta_solar))
        
        # Extraterrestrial radiation (MJ/m2/day)
        # FAO-56 Eq. 21
        Gsc = 0.0820  # Solar constant (MJ/m2/min)
        Ra = (24 * 60 / np.pi) * Gsc * dr * (
            ws * np.sin(lat_rad) * np.sin(delta_solar) +
            np.cos(lat_rad) * np.cos(delta_solar) * np.sin(ws)
        )
        
        # Daylight hours
        # FAO-56 Eq. 34
        N = (24 / np.pi) * ws
        
        # Solar radiation (MJ/m2/day)
        # FAO-56 Eq. 35 (Hargreaves-Samani method)
        Rs = (0.25 + 0.50 * sunshine_hours / N) * Ra
        
        # Clear sky radiation (MJ/m2/day)
        # FAO-56 Eq. 37
        Rso = (0.75 + 2e-5 * elevation) * Ra
        
        # Net shortwave radiation (MJ/m2/day)
        # FAO-56 Eq. 38
        albedo = 0.23  # FAO-56 default for grass
        Rns = (1 - albedo) * Rs
        
        # Net longwave radiation (MJ/m2/day)
        # FAO-56 Eq. 39
        sigma = 4.903e-9  # Stefan-Boltzmann constant (MJ/K4/m2/day)
        Rnl = sigma * (
            ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2
        ) * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * Rs / Rso - 0.35)
        
        # Net radiation (MJ/m2/day)
        # FAO-56 Eq. 40
        Rn = Rns - Rnl
        
        # Soil heat flux (MJ/m2/day)
        # FAO-56: Assumed 0 for daily calculations
        G = 0
        
        # ET0 calculation (mm/day)
        # FAO-56 Eq. 6
        if delta + gamma * (1 + 0.34 * wind_speed) == 0:
            return 0.0
            
        eto_numerator = (
            0.408 * delta * (Rn - G) + 
            gamma * (900 / (tmean + 273)) * wind_speed * (es - ea)
        )
        eto_denominator = delta + gamma * (1 + 0.34 * wind_speed)
        
        eto = eto_numerator / eto_denominator
        
        # Ensure non-negative result
        return max(0.0, round(eto, 3))
    
    @staticmethod
    def calculate_eto_monthly(
        tmin_monthly: np.ndarray,
        tmax_monthly: np.ndarray,
        rhmin_monthly: np.ndarray,
        rhmax_monthly: np.ndarray,
        wind_speed_monthly: np.ndarray,
        sunshine_hours_monthly: np.ndarray,
        latitude: float,
        elevation: float
    ) -> np.ndarray:
        """
        Calculate monthly ETo values.
        
        Args:
            tmin_monthly: Monthly min temperatures (°C), shape (12,)
            tmax_monthly: Monthly max temperatures (°C), shape (12,)
            rhmin_monthly: Monthly min humidity (%), shape (12,)
            rhmax_monthly: Monthly max humidity (%), shape (12,)
            wind_speed_monthly: Monthly wind speeds (m/s), shape (12,)
            sunshine_hours_monthly: Monthly sunshine hours, shape (12,)
            latitude: Latitude (decimal degrees)
            elevation: Elevation (m)
            
        Returns:
            Array of 12 monthly ETo values (mm/day)
        """
        eto_values = np.zeros(12)
        
        for month in range(12):
            day_of_year = 15 + month * 30  # Middle of each month
            eto_values[month] = ETOCalculator.calculate_eto(
                tmin=tmin_monthly[month],
                tmax=tmax_monthly[month],
                rhmin=rhmin_monthly[month],
                rhmax=rhmax_monthly[month],
                wind_speed=wind_speed_monthly[month],
                sunshine_hours=sunshine_hours_monthly[month],
                latitude=latitude,
                elevation=elevation,
                day_of_year=day_of_year
            )
        
        return eto_values
    
    @classmethod
    def get_valid_range(cls, param: str) -> Optional[Tuple[float, float]]:
        """
        Get the valid range for a parameter.
        
        Args:
            param: Parameter name
            
        Returns:
            Tuple of (min, max) or None if parameter not found
        """
        return cls.VALID_RANGES.get(param)


# Convenience function for simple calculations
def calculate_eto(
    tmin: float, tmax: float, rhmin: float, rhmax: float,
    wind_speed: float, sunshine_hours: float, latitude: float,
    elevation: float, day_of_year: int
) -> float:
    """
    Convenience function to calculate ETo.
    
    Args:
        See ETOCalculator.calculate_eto()
        
    Returns:
        Daily reference evapotranspiration (mm/day)
    """
    return ETOCalculator.calculate_eto(
        tmin, tmax, rhmin, rhmax, 
        wind_speed, sunshine_hours, 
        latitude, elevation, day_of_year
    )
