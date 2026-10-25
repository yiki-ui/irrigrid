# ============= config/app_config.py =============
"""
Unified Application Configuration

This module provides a centralized configuration system that:
- Loads from environment variables
- Loads from JSON config files
- Provides sensible defaults
- Validates configuration values
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from functools import lru_cache

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///drip_irrigation.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class APIConfig:
    """API keys and endpoints"""
    groq_api_key: Optional[str] = None
    openweather_api_key: Optional[str] = None
    nasa_power_api_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"


@dataclass
class PathConfig:
    """File system paths"""
    base_dir: Path = field(default_factory=lambda: BASE_DIR)
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    assets_dir: Path = field(default_factory=lambda: BASE_DIR / "assets")
    cache_dir: Path = field(default_factory=lambda: BASE_DIR / "cache")
    gis_data_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "processed_gis")
    models_dir: Path = field(default_factory=lambda: BASE_DIR / "models")
    output_dir: Path = field(default_factory=lambda: BASE_DIR / "output")


@dataclass
class UIConfig:
    """User interface configuration"""
    theme: str = "dark"
    window_width: int = 1400
    window_height: int = 900
    font_size: int = 10
    show_splash: bool = True


@dataclass
class FeatureConfig:
    """Feature toggles"""
    enable_ml_optimization: bool = True
    enable_weather_forecasting: bool = True
    enable_3d_visualization: bool = True
    enable_ai_expert: bool = True
    enable_gis: bool = True


@dataclass
class PerformanceConfig:
    """Performance settings"""
    max_workers: int = 4
    cache_size_mb: int = 50
    log_level: str = "INFO"


@dataclass
class AppConfig:
    """
    Unified Application Configuration
    
    This is the main configuration class that aggregates all settings.
    Load configuration using AppConfig.load() or AppConfig.from_env()
    """
    # Subsections
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # App metadata
    name: str = "AI Drip Irrigation Design System"
    version: str = "1.0.0"
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables"""
        # Database
        database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///drip_irrigation.db"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
        )
        
        # API
        api = APIConfig(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
            nasa_power_api_url=os.getenv(
                "NASA_POWER_API_URL",
                "https://power.larc.nasa.gov/api/temporal/daily/point"
            )
        )
        
        # UI
        ui = UIConfig(
            theme=os.getenv("THEME", "dark"),
            window_width=int(os.getenv("WINDOW_WIDTH", "1400")),
            window_height=int(os.getenv("WINDOW_HEIGHT", "900"))
        )
        
        # Features
        features = FeatureConfig(
            enable_ml_optimization=os.getenv("ENABLE_ML_OPTIMIZATION", "true").lower() == "true",
            enable_weather_forecasting=os.getenv("ENABLE_WEATHER_FORECASTING", "true").lower() == "true",
            enable_3d_visualization=os.getenv("ENABLE_3D_VISUALIZATION", "true").lower() == "true",
            enable_ai_expert=os.getenv("ENABLE_AI_EXPERT", "true").lower() == "true",
            enable_gis=os.getenv("ENABLE_GIS", "true").lower() == "true"
        )
        
        # Performance
        performance = PerformanceConfig(
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            cache_size_mb=int(os.getenv("CACHE_SIZE_MB", "50")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
        
        return cls(
            database=database,
            api=api,
            ui=ui,
            features=features,
            performance=performance,
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'AppConfig':
        """
        Load configuration from JSON file, with environment variable overrides.
        
        Args:
            config_path: Path to JSON config file. Defaults to config/app_config.json
            
        Returns:
            AppConfig instance
        """
        if config_path is None:
            config_path = BASE_DIR / "config" / "app_config.json"
        
        # Start with environment-based config
        config = cls.from_env()
        
        # Override with JSON file if it exists
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                
                # Update config from JSON (only provided fields)
                if 'database' in data:
                    config.database = DatabaseConfig(**data['database'])
                if 'api' in data:
                    config.api = APIConfig(**data['api'])
                if 'paths' in data:
                    # Convert string paths to Path objects
                    paths_data = data['paths']
                    for key in paths_data:
                        if isinstance(paths_data[key], str):
                            paths_data[key] = Path(paths_data[key])
                    config.paths = PathConfig(**paths_data)
                if 'ui' in data:
                    config.ui = UIConfig(**data['ui'])
                if 'features' in data:
                    config.features = FeatureConfig(**data['features'])
                if 'performance' in data:
                    config.performance = PerformanceConfig(**data['performance'])
                if 'name' in data:
                    config.name = data['name']
                if 'version' in data:
                    config.version = data['version']
                    
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Failed to load config from {config_path}: {e}")
                print("Using environment variables and defaults instead.")
        
        return config
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to JSON file"""
        if config_path is None:
            config_path = BASE_DIR / "config" / "app_config.json"
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict (handle Path objects)
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif hasattr(obj, '__dict__'):
                return convert_paths(asdict(obj))
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            return obj
        
        data = convert_paths(asdict(self))
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of warnings.
        
        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []
        
        # Check required paths exist
        if not self.paths.base_dir.exists():
            warnings.append(f"Base directory does not exist: {self.paths.base_dir}")
        
        # Check API keys
        if not self.api.groq_api_key:
            warnings.append("GROQ_API_KEY not set - AI Expert will be disabled")
        
        if not self.api.openweather_api_key:
            warnings.append("OPENWEATHER_API_KEY not set - Weather features limited")
        
        # Validate theme
        if self.ui.theme not in ['light', 'dark']:
            warnings.append(f"Invalid theme '{self.ui.theme}', defaulting to 'dark'")
            self.ui.theme = "dark"
        
        # Validate window size
        if self.ui.window_width < 800 or self.ui.window_height < 600:
            warnings.append("Window size too small, minimum 800x600")
            self.ui.window_width = max(800, self.ui.window_width)
            self.ui.window_height = max(600, self.ui.window_height)
        
        return warnings
    
    def get_database_url(self) -> str:
        """Get the database URL for SQLAlchemy"""
        return self.database.url
    
    def get_groq_key(self) -> Optional[str]:
        """Get Groq API key (alias for compatibility)"""
        return self.api.groq_api_key
    
    def get_nasa_url(self) -> str:
        """Get NASA POWER API URL"""
        return self.api.nasa_power_api_url


# Global config instance (lazy loaded)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the global application configuration instance.
    
    This function caches the config to avoid repeated loading.
    Use reset_config() to clear the cache.
    
    Returns:
        AppConfig instance
    """
    global _config
    if _config is None:
        _config = AppConfig.load()
        warnings = _config.validate()
        for warning in warnings:
            print(f"Config Warning: {warning}")
    return _config


def reset_config() -> None:
    """Reset the global config cache (useful for testing)"""
    global _config
    _config = None


# Backward compatibility - expose common settings as module-level variables
# These are deprecated but maintained for backward compatibility
def __getattr__(name: str) -> Any:
    """Lazy-load legacy settings for backward compatibility"""
    config = get_config()
    
    legacy_map = {
        'DATABASE_URL': config.database.url,
        'OPENWEATHER_API_KEY': config.api.openweather_api_key,
        'NASA_POWER_API_KEY': config.api.nasa_power_api_url,  # Note: this is URL not key
        'APP_NAME': config.name,
        'APP_VERSION': config.version,
        'DEFAULT_IRRIGATION_EFFICIENCY': 0.90,  # Hardcoded for drip
        'MODEL_DIR': config.paths.models_dir,
        'ENABLE_AI_OPTIMIZATION': config.features.enable_ml_optimization,
    }
    
    if name in legacy_map:
        return legacy_map[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'AppConfig',
    'DatabaseConfig', 
    'APIConfig',
    'PathConfig',
    'UIConfig',
    'FeatureConfig',
    'PerformanceConfig',
    'get_config',
    'reset_config',
]
