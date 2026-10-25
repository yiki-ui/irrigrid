# ============= config/settings.py =============
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///drip_irrigation.db")

# API Keys
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
NASA_POWER_API_KEY = os.getenv("NASA_POWER_API_KEY", "")

# App Settings
APP_NAME = "AI Drip Irrigation Design System"
APP_VERSION = "1.0.0"
DEFAULT_IRRIGATION_EFFICIENCY = 0.90  # 90% for drip

# AI Model Settings
MODEL_DIR = BASE_DIR / "models"
ENABLE_AI_OPTIMIZATION = True