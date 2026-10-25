# ============= src/ai/trainer.py =============
import numpy as np
from typing import Tuple, List
import joblib
from pathlib import Path

class ModelTrainer:
    """Train and manage AI models"""
    
    @staticmethod
    def generate_training_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for irrigation optimization
        
        Features: [soil_moisture, etc, crop_stage, avg_forecast_temp, forecast_variability]
        Target: optimal_irrigation_amount
        """
        np.random.seed(42)
        
        # Generate features
        soil_moisture = np.random.uniform(0.2, 0.8, n_samples)
        etc = np.random.uniform(3, 8, n_samples)
        crop_stage = np.random.randint(1, 5, n_samples)
        avg_forecast = np.random.uniform(18, 28, n_samples)
        forecast_var = np.random.uniform(0, 5, n_samples)
        
        X = np.column_stack([soil_moisture, etc, crop_stage, avg_forecast, forecast_var])
        
        # Generate target (simplified logic)
        y = np.zeros(n_samples)
        for i in range(n_samples):
            if soil_moisture[i] < 0.3:
                y[i] = etc[i] * 1.5  # High irrigation need
            elif soil_moisture[i] < 0.5:
                y[i] = etc[i] * 1.0  # Normal irrigation
            elif soil_moisture[i] < 0.7:
                y[i] = etc[i] * 0.5  # Low irrigation
            else:
                y[i] = 0  # No irrigation needed
            
            # Adjust for weather forecast
            if forecast_var[i] > 3:  # High variability (possible rain)
                y[i] *= 0.8
        
        return X, y
    
    @staticmethod
    def train_and_save_model(model, X, y, save_path: str):
        """Train model and save to disk"""
        model.fit(X, y)
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, save_path)
        print(f"Model saved to {save_path}")
        return model
