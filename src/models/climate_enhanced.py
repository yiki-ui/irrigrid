#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Climate Module with Monthly/Decade/Daily Data Support
Includes country database with automatic location data
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date
from enum import Enum


class TimeScale(str, Enum):
    """Time scale for climate data input"""
    MONTHLY = "monthly"
    DECADE = "decade"  # 10-day periods
    DAILY = "daily"


class CountryData(BaseModel):
    """Country location data"""
    name: str
    capital: str
    latitude: float
    longitude: float
    altitude: float
    stations: List[str] = []


class MonthlyClimateData(BaseModel):
    """Monthly climate data for ETo calculation"""
    month: str
    min_temp: float = Field(..., description="Minimum temperature (°C)")
    max_temp: float = Field(..., description="Maximum temperature (°C)")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity (%)")
    wind_speed: float = Field(..., ge=0, description="Wind speed (km/day)")
    sunshine_hours: float = Field(..., ge=0, le=24, description="Sunshine hours")
    solar_radiation: Optional[float] = Field(None, description="Solar radiation (MJ/m²/day)")
    eto: Optional[float] = Field(None, description="Reference evapotranspiration (mm/day)")
    
    @property
    def mean_temp(self) -> float:
        """Calculate mean temperature"""
        return (self.min_temp + self.max_temp) / 2


class RainData(BaseModel):
    """Monthly rainfall data with effective rain calculation"""
    month: str
    rainfall: float = Field(..., ge=0, description="Total rainfall (mm)")
    effective_rain: Optional[float] = Field(None, description="Effective rainfall (mm)")
    method: str = Field(default="USDA S.C. Method", description="Calculation method")


class CountryDatabase:
    """Database of countries with climate station data"""
    
    COUNTRIES = {
        "Rwanda": {
            "capital": "Kigali",
            "latitude": -1.9403,
            "longitude": 30.0606,
            "altitude": 1567,
            "stations": ["Kigali", "Butare", "Gisenyi", "Ruhengeri", "Kibungo"]
        },
        "Kenya": {
            "capital": "Nairobi",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "altitude": 1795,
            "stations": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"]
        },
        "Uganda": {
            "capital": "Kampala",
            "latitude": 0.3476,
            "longitude": 32.5825,
            "altitude": 1190,
            "stations": ["Kampala", "Entebbe", "Jinja", "Mbarara", "Gulu"]
        },
        "Tanzania": {
            "capital": "Dodoma",
            "latitude": -6.1630,
            "longitude": 35.7516,
            "altitude": 1120,
            "stations": ["Dodoma", "Dar es Salaam", "Arusha", "Mwanza", "Mbeya"]
        },
        "Burundi": {
            "capital": "Gitega",
            "latitude": -3.4264,
            "longitude": 29.9306,
            "altitude": 1504,
            "stations": ["Gitega", "Bujumbura", "Ngozi", "Rutana", "Ruyigi"]
        },
        "Ethiopia": {
            "capital": "Addis Ababa",
            "latitude": 9.0320,
            "longitude": 38.7469,
            "altitude": 2355,
            "stations": ["Addis Ababa", "Dire Dawa", "Mekelle", "Gondar", "Bahir Dar"]
        },
        "South Sudan": {
            "capital": "Juba",
            "latitude": 4.8517,
            "longitude": 31.5825,
            "altitude": 550,
            "stations": ["Juba", "Wau", "Malakal", "Yei", "Bor"]
        },
        "Democratic Republic of Congo": {
            "capital": "Kinshasa",
            "latitude": -4.3276,
            "longitude": 15.3136,
            "altitude": 240,
            "stations": ["Kinshasa", "Lubumbashi", "Goma", "Bukavu", "Kisangani"]
        }
    }
    
    @classmethod
    def get_country_data(cls, country_name: str) -> Optional[CountryData]:
        """Get country data by name"""
        if country_name in cls.COUNTRIES:
            data = cls.COUNTRIES[country_name]
            return CountryData(name=country_name, **data)
        return None
    
    @classmethod
    def get_all_countries(cls) -> List[str]:
        """Get list of all available countries"""
        return list(cls.COUNTRIES.keys())


class ClimateStationData(BaseModel):
    """Complete climate station data"""
    country: str
    station: str
    latitude: float
    longitude: float
    altitude: float
    time_scale: TimeScale = TimeScale.MONTHLY
    monthly_data: List[MonthlyClimateData] = []
    rain_data: List[RainData] = []
    
    def calculate_annual_eto(self) -> float:
        """Calculate total annual ETo"""
        return sum(month.eto for month in self.monthly_data if month.eto)
    
    def calculate_annual_rainfall(self) -> float:
        """Calculate total annual rainfall"""
        return sum(rain.rainfall for rain in self.rain_data)
    
    def calculate_annual_effective_rain(self) -> float:
        """Calculate total annual effective rainfall"""
        return sum(rain.effective_rain for rain in self.rain_data if rain.effective_rain)


class EffectiveRainCalculator:
    """Calculate effective rainfall using various methods"""
    
    @staticmethod
    def usda_sc_method(rainfall: float) -> float:
        """
        USDA Soil Conservation Method for effective rainfall
        
        Args:
            rainfall: Monthly rainfall in mm
            
        Returns:
            Effective rainfall in mm
        """
        if rainfall <= 0:
            return 0.0
        elif rainfall <= 250:
            # Peff = (125 - 0.2 * P) / 125 * P
            return ((125 - 0.2 * rainfall) / 125) * rainfall
        else:
            # Peff = 125 + 0.1 * P
            return 125 + 0.1 * rainfall
    
    @staticmethod
    def fao_method(rainfall: float, etc: float) -> float:
        """
        FAO method for effective rainfall
        
        Args:
            rainfall: Monthly rainfall in mm
            etc: Crop evapotranspiration in mm
            
        Returns:
            Effective rainfall in mm
        """
        if rainfall <= 0:
            return 0.0
        
        # Dependable rain (80% probability)
        dependable_rain = 0.8 * rainfall
        
        # Effective rain is minimum of dependable rain and ETc
        return min(dependable_rain, etc)
    
    @staticmethod
    def fixed_percentage_method(rainfall: float, percentage: float = 0.8) -> float:
        """
        Fixed percentage method
        
        Args:
            rainfall: Monthly rainfall in mm
            percentage: Percentage of rainfall that is effective (default 80%)
            
        Returns:
            Effective rainfall in mm
        """
        return rainfall * percentage


def get_default_monthly_climate() -> List[Dict]:
    """Get default monthly climate data template for Rwanda"""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Default Rwanda climate data (Kigali)
    default_data = [
        {"min_temp": 15.5, "max_temp": 27.0, "humidity": 75, "wind_speed": 150, "sunshine_hours": 6.5},
        {"min_temp": 15.8, "max_temp": 27.5, "humidity": 73, "wind_speed": 155, "sunshine_hours": 6.8},
        {"min_temp": 16.0, "max_temp": 27.2, "humidity": 76, "wind_speed": 145, "sunshine_hours": 6.2},
        {"min_temp": 16.2, "max_temp": 26.8, "humidity": 78, "wind_speed": 140, "sunshine_hours": 5.8},
        {"min_temp": 16.0, "max_temp": 26.5, "humidity": 77, "wind_speed": 135, "sunshine_hours": 6.0},
        {"min_temp": 15.2, "max_temp": 27.8, "humidity": 65, "wind_speed": 160, "sunshine_hours": 7.5},
        {"min_temp": 14.8, "max_temp": 28.5, "humidity": 62, "wind_speed": 165, "sunshine_hours": 8.0},
        {"min_temp": 15.0, "max_temp": 28.8, "humidity": 63, "wind_speed": 168, "sunshine_hours": 8.2},
        {"min_temp": 15.5, "max_temp": 28.2, "humidity": 68, "wind_speed": 158, "sunshine_hours": 7.5},
        {"min_temp": 15.8, "max_temp": 27.5, "humidity": 72, "wind_speed": 150, "sunshine_hours": 6.8},
        {"min_temp": 15.6, "max_temp": 26.8, "humidity": 77, "wind_speed": 142, "sunshine_hours": 6.0},
        {"min_temp": 15.4, "max_temp": 26.5, "humidity": 76, "wind_speed": 145, "sunshine_hours": 6.2},
    ]
    
    return [{"month": month, **data} for month, data in zip(months, default_data)]


def get_default_monthly_rainfall() -> List[Dict]:
    """Get default monthly rainfall data for Rwanda"""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Default Rwanda rainfall data (Kigali) in mm
    rainfall_data = [75, 90, 115, 150, 85, 15, 10, 25, 70, 95, 110, 85]
    
    return [{"month": month, "rainfall": rain} for month, rain in zip(months, rainfall_data)]


# ═══════════════════════════════════════════════════════════════════════════════
# RWANDA STATION DATABASE
# Monthly climate data sourced from:
#  - FAO CLIMWAT 2.0 for Rwanda stations
#  - core_test_data.py (30-year Musanze normals)
#  - Meteo Rwanda / World Bank CCKP historical 1991-2020
# ═══════════════════════════════════════════════════════════════════════════════

RWANDA_STATIONS = {
    "Kigali": {
        "latitude": -1.9403, "longitude": 30.0606, "altitude": 1567,
        # tmin, tmax, rh, wind_km_day, sunshine_h, eto_mm_day, rainfall_mm
        "monthly": [
            # Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
            {"tmin": 15.5, "tmax": 27.0, "rh": 75, "wind": 150, "sun": 6.5, "eto": 4.5, "rain": 85},
            {"tmin": 15.8, "tmax": 27.5, "rh": 73, "wind": 155, "sun": 6.8, "eto": 4.7, "rain": 95},
            {"tmin": 16.0, "tmax": 27.2, "rh": 76, "wind": 145, "sun": 6.2, "eto": 4.6, "rain": 115},
            {"tmin": 16.2, "tmax": 26.8, "rh": 78, "wind": 140, "sun": 5.8, "eto": 4.3, "rain": 160},
            {"tmin": 16.0, "tmax": 26.5, "rh": 77, "wind": 135, "sun": 6.0, "eto": 4.4, "rain": 105},
            {"tmin": 15.2, "tmax": 27.8, "rh": 65, "wind": 160, "sun": 7.5, "eto": 5.0, "rain": 25},
            {"tmin": 14.8, "tmax": 28.5, "rh": 62, "wind": 165, "sun": 8.0, "eto": 5.3, "rain": 10},
            {"tmin": 15.0, "tmax": 28.8, "rh": 63, "wind": 168, "sun": 8.2, "eto": 5.5, "rain": 15},
            {"tmin": 15.5, "tmax": 28.2, "rh": 68, "wind": 158, "sun": 7.5, "eto": 5.2, "rain": 55},
            {"tmin": 15.8, "tmax": 27.5, "rh": 72, "wind": 150, "sun": 6.8, "eto": 4.8, "rain": 95},
            {"tmin": 15.6, "tmax": 26.8, "rh": 77, "wind": 142, "sun": 6.0, "eto": 4.4, "rain": 110},
            {"tmin": 15.4, "tmax": 26.5, "rh": 76, "wind": 145, "sun": 6.2, "eto": 4.4, "rain": 90},
        ]
    },
    "Ruhengeri": {
        # Ruhengeri = Musanze, Northern Province, ~1,850m ASL
        # Source: core_test_data.py MUSANZE_CLIMATE_MONTHLY (30-year normals)
        "latitude": -1.5000, "longitude": 29.6330, "altitude": 1850,
        "monthly": [
            {"tmin": 14, "tmax": 23, "rh": 81, "wind": 120, "sun": 6.0, "eto": 3.2, "rain": 150},
            {"tmin": 14, "tmax": 23, "rh": 80, "wind": 130, "sun": 6.0, "eto": 3.5, "rain": 140},
            {"tmin": 13, "tmax": 22, "rh": 79, "wind": 138, "sun": 5.5, "eto": 3.3, "rain": 90},
            {"tmin": 12, "tmax": 21, "rh": 80, "wind": 130, "sun": 5.0, "eto": 3.0, "rain": 180},
            {"tmin": 11, "tmax": 20, "rh": 78, "wind": 138, "sun": 5.0, "eto": 3.1, "rain": 70},
            {"tmin": 9,  "tmax": 19, "rh": 75, "wind": 155, "sun": 5.5, "eto": 3.6, "rain": 30},
            {"tmin": 8,  "tmax": 19, "rh": 74, "wind": 164, "sun": 6.0, "eto": 3.8, "rain": 50},
            {"tmin": 9,  "tmax": 20, "rh": 75, "wind": 155, "sun": 6.0, "eto": 3.9, "rain": 80},
            {"tmin": 11, "tmax": 21, "rh": 78, "wind": 138, "sun": 5.5, "eto": 3.7, "rain": 150},
            {"tmin": 13, "tmax": 22, "rh": 80, "wind": 130, "sun": 5.0, "eto": 3.4, "rain": 200},
            {"tmin": 14, "tmax": 23, "rh": 82, "wind": 121, "sun": 5.0, "eto": 3.2, "rain": 180},
            {"tmin": 13, "tmax": 22, "rh": 80, "wind": 130, "sun": 5.5, "eto": 3.2, "rain": 120},
        ]
    },
    "Butare": {
        # Butare = Huye, Southern Province, ~1,768m ASL
        # Source: FAO CLIMWAT Southern Rwanda records
        "latitude": -2.5967, "longitude": 29.7400, "altitude": 1768,
        "monthly": [
            {"tmin": 14.5, "tmax": 26.5, "rh": 78, "wind": 130, "sun": 6.2, "eto": 4.0, "rain": 90},
            {"tmin": 14.8, "tmax": 27.0, "rh": 76, "wind": 135, "sun": 6.5, "eto": 4.2, "rain": 100},
            {"tmin": 15.0, "tmax": 26.8, "rh": 79, "wind": 128, "sun": 5.8, "eto": 4.0, "rain": 140},
            {"tmin": 15.2, "tmax": 26.2, "rh": 82, "wind": 122, "sun": 5.2, "eto": 3.8, "rain": 185},
            {"tmin": 15.0, "tmax": 25.8, "rh": 81, "wind": 118, "sun": 5.5, "eto": 3.9, "rain": 120},
            {"tmin": 14.0, "tmax": 27.0, "rh": 68, "wind": 145, "sun": 7.0, "eto": 4.5, "rain": 20},
            {"tmin": 13.5, "tmax": 27.8, "rh": 65, "wind": 150, "sun": 7.5, "eto": 4.8, "rain": 12},
            {"tmin": 14.0, "tmax": 28.0, "rh": 66, "wind": 152, "sun": 7.8, "eto": 4.9, "rain": 20},
            {"tmin": 14.5, "tmax": 27.5, "rh": 70, "wind": 143, "sun": 7.0, "eto": 4.6, "rain": 65},
            {"tmin": 14.8, "tmax": 26.8, "rh": 75, "wind": 135, "sun": 6.2, "eto": 4.2, "rain": 110},
            {"tmin": 14.6, "tmax": 26.0, "rh": 80, "wind": 125, "sun": 5.5, "eto": 3.9, "rain": 135},
            {"tmin": 14.4, "tmax": 25.8, "rh": 79, "wind": 128, "sun": 5.8, "eto": 3.9, "rain": 95},
        ]
    },
    "Gisenyi": {
        # Gisenyi = Rubavu, Western Province, ~1,540m ASL, Lake Kivu shore
        "latitude": -1.7034, "longitude": 29.2564, "altitude": 1540,
        "monthly": [
            {"tmin": 17.0, "tmax": 28.5, "rh": 74, "wind": 160, "sun": 6.8, "eto": 4.8, "rain": 120},
            {"tmin": 17.2, "tmax": 29.0, "rh": 72, "wind": 165, "sun": 7.0, "eto": 5.0, "rain": 130},
            {"tmin": 17.5, "tmax": 28.8, "rh": 75, "wind": 155, "sun": 6.5, "eto": 4.8, "rain": 160},
            {"tmin": 17.8, "tmax": 28.2, "rh": 78, "wind": 148, "sun": 6.0, "eto": 4.5, "rain": 195},
            {"tmin": 17.5, "tmax": 27.8, "rh": 77, "wind": 142, "sun": 6.2, "eto": 4.6, "rain": 145},
            {"tmin": 16.5, "tmax": 29.0, "rh": 65, "wind": 170, "sun": 7.8, "eto": 5.3, "rain": 35},
            {"tmin": 16.0, "tmax": 29.8, "rh": 62, "wind": 175, "sun": 8.2, "eto": 5.6, "rain": 20},
            {"tmin": 16.2, "tmax": 30.0, "rh": 63, "wind": 178, "sun": 8.5, "eto": 5.7, "rain": 30},
            {"tmin": 16.8, "tmax": 29.5, "rh": 68, "wind": 165, "sun": 7.8, "eto": 5.4, "rain": 80},
            {"tmin": 17.2, "tmax": 28.8, "rh": 73, "wind": 158, "sun": 7.0, "eto": 5.0, "rain": 120},
            {"tmin": 17.0, "tmax": 28.0, "rh": 77, "wind": 150, "sun": 6.2, "eto": 4.7, "rain": 150},
            {"tmin": 16.8, "tmax": 27.8, "rh": 75, "wind": 153, "sun": 6.5, "eto": 4.7, "rain": 110},
        ]
    },
    "Kibungo": {
        # Kibungo = Ngoma, Eastern Province, ~1,490m ASL — drier savanna zone
        "latitude": -2.1601, "longitude": 30.5430, "altitude": 1490,
        "monthly": [
            {"tmin": 16.5, "tmax": 29.5, "rh": 70, "wind": 170, "sun": 7.2, "eto": 5.0, "rain": 65},
            {"tmin": 16.8, "tmax": 30.0, "rh": 68, "wind": 175, "sun": 7.5, "eto": 5.2, "rain": 75},
            {"tmin": 17.0, "tmax": 29.8, "rh": 71, "wind": 165, "sun": 7.0, "eto": 5.0, "rain": 95},
            {"tmin": 17.2, "tmax": 29.2, "rh": 74, "wind": 158, "sun": 6.5, "eto": 4.7, "rain": 130},
            {"tmin": 17.0, "tmax": 28.8, "rh": 73, "wind": 152, "sun": 6.8, "eto": 4.8, "rain": 80},
            {"tmin": 16.0, "tmax": 30.5, "rh": 60, "wind": 185, "sun": 8.5, "eto": 5.6, "rain": 15},
            {"tmin": 15.5, "tmax": 31.2, "rh": 57, "wind": 190, "sun": 9.0, "eto": 5.9, "rain": 8},
            {"tmin": 15.8, "tmax": 31.5, "rh": 58, "wind": 192, "sun": 9.2, "eto": 6.0, "rain": 12},
            {"tmin": 16.5, "tmax": 30.8, "rh": 63, "wind": 180, "sun": 8.5, "eto": 5.7, "rain": 45},
            {"tmin": 16.8, "tmax": 30.0, "rh": 68, "wind": 172, "sun": 7.8, "eto": 5.3, "rain": 80},
            {"tmin": 16.5, "tmax": 29.2, "rh": 72, "wind": 162, "sun": 7.0, "eto": 4.9, "rain": 90},
            {"tmin": 16.3, "tmax": 29.0, "rh": 71, "wind": 165, "sun": 7.2, "eto": 4.9, "rain": 70},
        ]
    },
}


def get_station_climate(station_name: str) -> Optional[Dict]:
    """Return full monthly climate + rainfall for a Rwanda station, or None."""
    return RWANDA_STATIONS.get(station_name)


def get_station_eto_daily(station_name: str) -> List[float]:
    """Return list of 12 monthly ETo values (mm/day) for a Rwanda station."""
    station = RWANDA_STATIONS.get(station_name)
    if station:
        return [m["eto"] for m in station["monthly"]]
    return [4.5] * 12  # generic fallback


def get_station_rainfall(station_name: str) -> List[float]:
    """Return list of 12 monthly rainfall values (mm) for a Rwanda station."""
    station = RWANDA_STATIONS.get(station_name)
    if station:
        return [m["rain"] for m in station["monthly"]]
    return [85, 95, 115, 160, 105, 25, 10, 15, 55, 95, 110, 90]  # Kigali fallback
