# ============= src/weather/data_processor.py =============
import pandas as pd
from typing import List, Dict
from datetime import datetime

class WeatherDataProcessor:
    """Process and analyze weather data"""
    
    @staticmethod
    def calculate_eto_from_weather(weather_data: Dict, latitude: float, elevation: float, day_of_year: int) -> float:
        """
        Calculate ETo from weather data
        Uses simplified Hargreaves method if full data not available
        """
        from src.core.eto_calculator import ETOCalculator
        
        # Check if we have full data for Penman-Monteith
        if all(k in weather_data for k in ['temp_min', 'temp_max', 'humidity', 'wind_speed', 'sunshine_hours']):
            return ETOCalculator.calculate_eto(
                tmin=weather_data['temp_min'],
                tmax=weather_data['temp_max'],
                rhmin=weather_data.get('humidity_min', weather_data['humidity']),
                rhmax=weather_data.get('humidity_max', weather_data['humidity']),
                wind_speed=weather_data['wind_speed'],
                sunshine_hours=weather_data.get('sunshine_hours', 8),
                latitude=latitude,
                elevation=elevation,
                day_of_year=day_of_year
            )
        else:
            # Simplified Hargreaves method
            tmin = weather_data.get('temp_min', weather_data.get('temperature', 20) - 5)
            tmax = weather_data.get('temp_max', weather_data.get('temperature', 20) + 5)
            tmean = (tmin + tmax) / 2
            
            # Simplified ETo estimation
            eto = 0.0023 * (tmean + 17.8) * (tmax - tmin) ** 0.5 * 0.408
            return max(0, eto)
    
    @staticmethod
    def aggregate_daily_data(hourly_data: List[Dict]) -> Dict:
        """Aggregate hourly weather data to daily"""
        df = pd.DataFrame(hourly_data)
        
        daily = {
            'temp_min': df['temperature'].min(),
            'temp_max': df['temperature'].max(),
            'temp_mean': df['temperature'].mean(),
            'humidity': df['humidity'].mean(),
            'wind_speed': df['wind_speed'].mean(),
            'rainfall': df.get('rainfall', pd.Series([0])).sum()
        }
        
        return daily
    
    @staticmethod
    def detect_rain_probability(forecast: List[Dict]) -> float:
        """Detect probability of rain in forecast"""
        rain_days = sum(1 for day in forecast if day.get('rainfall', 0) > 0)
        return rain_days / len(forecast) if forecast else 0
