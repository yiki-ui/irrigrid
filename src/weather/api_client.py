# ============= src/weather/api_client.py =============
import requests
from datetime import datetime, timedelta
from typing import Dict, List

class WeatherAPIClient:
    """Fetch weather data from APIs"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """Get current weather data"""
        if not self.api_key:
            return self._get_dummy_weather()
        
        url = f"{self.base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"]
            }
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_dummy_weather()
    
    def get_forecast(self, lat: float, lon: float, days: int = 7) -> List[Dict]:
        """Get weather forecast"""
        if not self.api_key:
            return self._get_dummy_forecast(days)
        
        url = f"{self.base_url}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "cnt": days * 8  # 3-hour intervals
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecast = []
            for item in data["list"][::8]:  # Daily data
                forecast.append({
                    "date": datetime.fromtimestamp(item["dt"]),
                    "temp_min": item["main"]["temp_min"],
                    "temp_max": item["main"]["temp_max"],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item["wind"]["speed"],
                    "rainfall": item.get("rain", {}).get("3h", 0)
                })
            
            return forecast[:days]
        except Exception as e:
            print(f"Forecast API error: {e}")
            return self._get_dummy_forecast(days)
    
    def _get_dummy_weather(self) -> Dict:
        """Return dummy weather for testing"""
        return {
            "temperature": 22,
            "humidity": 65,
            "wind_speed": 2.5,
            "description": "partly cloudy"
        }
    
    def _get_dummy_forecast(self, days: int) -> List[Dict]:
        """Return dummy forecast for testing"""
        forecast = []
        base_date = datetime.now()
        for i in range(days):
            forecast.append({
                "date": base_date + timedelta(days=i),
                "temp_min": 18 + i * 0.5,
                "temp_max": 25 + i * 0.3,
                "humidity": 65,
                "wind_speed": 2.5,
                "rainfall": 0 if i % 3 != 0 else 5
            })
        return forecast
