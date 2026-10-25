# ============= src/__init__.py =============
"""Main Irrigation DSS Package"""

from .core import IrrigationDesignService
from .models import CropDatabase, SoilDatabase
from .ai import SystemRecommender
from .visualization import DripSystem2DVisualizer
from .gis import MapHandler, DEMProcessor, SpatialUtils
from .reports import PDFReportGenerator, ExportUtils

__version__ = "1.0.0"
__author__ = "AI-Based Drip Irrigation DSS Team"

__all__ = [
    'IrrigationDesignService',
    'CropDatabase',
    'SoilDatabase',
    'SystemRecommender',
    'DripSystem2DVisualizer',
    'MapHandler',
    'DEMProcessor',
    'SpatialUtils',
    'PDFReportGenerator',
    'ExportUtils',
    '__version__',
    '__author__'
]