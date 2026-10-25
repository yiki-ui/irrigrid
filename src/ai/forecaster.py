# ============= src/ai/forecaster.py =============
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    # Avoid Unicode errors on Windows console
    try:
        print("[WARNING] Prophet not installed - Weather forecasting disabled. Run: pip install prophet")
    except:
        pass  # Silently ignore if even this fails

import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta

class WeatherForecaster:
    """Time series weather forecasting using Prophet"""
    
    def __init__(self):
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet is not installed. Install with: pip install prophet")
        
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False
        )
        self.is_trained = False
    
    def train(self, historical_data: List[Dict]):
        """
        Train forecasting model
        
        Args:
            historical_data: List of dicts with 'date' and 'value' keys
        """
        df = pd.DataFrame(historical_data)
        df.columns = ['ds', 'y']
        self.model.fit(df)
        self.is_trained = True
    
    def forecast(self, days_ahead: int = 7) -> List[float]:
        """Generate forecast for next N days"""
        if not self.is_trained:
            # Return dummy forecast
            return [5.0] * days_ahead
        
        future = self.model.make_future_dataframe(periods=days_ahead)
        forecast = self.model.predict(future)
        return forecast['yhat'].tail(days_ahead).tolist()
