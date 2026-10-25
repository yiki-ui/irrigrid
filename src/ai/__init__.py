# ============= src/ai/__init__.py =============
"""AI and Machine Learning Modules"""

from .optimizer import IrrigationOptimizer
from .recommender import SystemRecommender
from .trainer import ModelTrainer

# Optional modules that require additional packages
try:
    from .forecaster import WeatherForecaster
    FORECASTER_AVAILABLE = True
except ImportError:
    WeatherForecaster = None
    FORECASTER_AVAILABLE = False

__all__ = [
    'IrrigationOptimizer',
    'WeatherForecaster',
    'SystemRecommender',
    'ModelTrainer',
    'FORECASTER_AVAILABLE'
]
