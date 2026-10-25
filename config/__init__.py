# ============= config/__init__.py =============
"""Configuration Package"""

from .settings import *
from .database import engine, SessionLocal, Base, get_db
from .rwanda_data import RWANDA_PROVINCES, CLIMATE_ZONES

# Import unified config (new)
from .app_config import (
    AppConfig,
    get_config,
    reset_config,
    DatabaseConfig,
    APIConfig,
    PathConfig,
    UIConfig,
    FeatureConfig,
    PerformanceConfig
)

__all__ = [
    # Settings (legacy - consider migrating)
    'DATABASE_URL',
    'OPENWEATHER_API_KEY',
    'NASA_POWER_API_KEY',
    'APP_NAME',
    'APP_VERSION',
    'DEFAULT_IRRIGATION_EFFICIENCY',
    'MODEL_DIR',
    'ENABLE_AI_OPTIMIZATION',
    # Database
    'engine',
    'SessionLocal',
    'Base',
    'get_db',
    # Rwanda Data
    'RWANDA_PROVINCES',
    'CLIMATE_ZONES',
    # Unified Config (new)
    'AppConfig',
    'get_config',
    'reset_config',
    'DatabaseConfig',
    'APIConfig',
    'PathConfig',
    'UIConfig',
    'FeatureConfig',
    'PerformanceConfig',
]