"""
Hydraulic Design Module
Professional hydraulic calculations for drip irrigation systems
Based on FAO-56 and industry standards
"""

from .design_calculator import HydraulicDesign, SystemDesign

__all__ = [
    'HydraulicDesign',
    'SystemDesign'
]
