#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Water Requirement Calculator with Optional Canopy Integration
Provides backward-compatible water calculations with optional canopy model support
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class WaterCalculationResult:
    """Result of water requirement calculation"""
    etc: float  # Crop evapotranspiration (mm)
    kc: float  # Crop coefficient used
    irrigation_requirement: float  # mm
    effective_rainfall: float  # mm
    canopy_coverage: Optional[float] = None  # 0-1, only if canopy model used
    growth_stage: Optional[str] = None  # only if canopy model used


class WaterCalculator:
    """
    Water requirement calculator with optional canopy integration
    
    Features:
    - Backward compatible (defaults to static Kc)
    - Optional canopy-adjusted Kc
    - Works with or without canopy model
    """
    
    def __init__(self, use_canopy: bool = False):
        """
        Initialize calculator
        
        Args:
            use_canopy: If True, use canopy model for dynamic Kc adjustment
        """
        self.use_canopy = use_canopy
        self.canopy_model = None
    
    def set_crop(self, crop_name: str, crop_data: dict):
        """
        Set crop for calculations
        
        Args:
            crop_name: Name of the crop
            crop_data: Dictionary with crop parameters (kc_initial, kc_mid, kc_end, growth_stages_days)
        """
        self.crop_name = crop_name
        self.crop_data = crop_data
        
        # Initialize canopy model if enabled
        if self.use_canopy:
            try:
                from src.models.canopy import CanopyModel
                self.canopy_model = CanopyModel(crop_name, crop_data)
            except Exception as e:
                print(f"Warning: Could not initialize canopy model: {e}")
                print("Falling back to static Kc values")
                self.use_canopy = False
                self.canopy_model = None
    
    def get_kc_for_day(self, days_after_planting: int, fallback_kc: float = 1.0) -> Tuple[float, Optional[float], Optional[str]]:
        """
        Get Kc value for a specific day
        
        Args:
            days_after_planting: Days since planting
            fallback_kc: Static Kc to use if canopy model not available
            
        Returns:
            Tuple of (kc_value, canopy_coverage, growth_stage)
        """
        if self.use_canopy and self.canopy_model:
            # Use dynamic canopy-adjusted Kc
            kc = self.canopy_model.get_kc_adjusted(days_after_planting)
            coverage = self.canopy_model.get_canopy_coverage(days_after_planting)
            stage = self.canopy_model.get_growth_stage_name(days_after_planting)
            return (kc, coverage, stage)
        else:
            # Use static fallback Kc
            return (fallback_kc, None, None)
    
    def calculate_daily_etc(self, eto_daily: float, days_after_planting: int, 
                           fallback_kc: float = 1.0) -> Tuple[float, float, Optional[float], Optional[str]]:
        """
        Calculate daily crop evapotranspiration
        
        Args:
            eto_daily: Reference evapotranspiration (mm/day)
            days_after_planting: Days since planting
            fallback_kc: Static Kc to use if canopy model not available
            
        Returns:
            Tuple of (etc, kc_used, canopy_coverage, growth_stage)
        """
        kc, coverage, stage = self.get_kc_for_day(days_after_planting, fallback_kc)
        etc = eto_daily * kc
        return (etc, kc, coverage, stage)
    
    def calculate_monthly_requirements(
        self, 
        eto_daily_values: List[float],
        days_in_months: List[int],
        rainfall_monthly: List[float],
        kc_monthly_fallback: List[float],
        planting_day_of_year: int = 1
    ) -> List[WaterCalculationResult]:
        """
        Calculate monthly water requirements for entire season
        
        Args:
            eto_daily_values: List of 12 daily ETo values (mm/day) for each month
            days_in_months: List of days in each month [31, 28, 31, ...]
            rainfall_monthly: List of 12 monthly rainfall values (mm)
            kc_monthly_fallback: List of 12 static Kc values to use if canopy disabled
            planting_day_of_year: Day of year when crop was planted (1-365)
            
        Returns:
            List of WaterCalculationResult objects (one per month)
        """
        results = []
        
        # Import effective rainfall calculator
        try:
            from src.models.climate_enhanced import EffectiveRainCalculator
            eff_rain_calculator = EffectiveRainCalculator
        except:
            # Fallback to simple 75% efficiency
            class SimpleEffRain:
                @staticmethod
                def usda_sc_method(rainfall):
                    return rainfall * 0.75
            eff_rain_calculator = SimpleEffRain
        
        cumulative_days = 0
        
        for month_idx in range(12):
            # Get monthly ETo (convert daily to monthly)
            eto_monthly = eto_daily_values[month_idx] * days_in_months[month_idx]
            
            # Calculate average Kc for this month
            if self.use_canopy and self.canopy_model:
                # Use canopy model - average Kc across all days in month
                kc_sum = 0.0
                coverage_sum = 0.0
                for day_in_month in range(days_in_months[month_idx]):
                    days_after_planting = cumulative_days + day_in_month
                    kc_sum += self.canopy_model.get_kc_adjusted(days_after_planting)
                    coverage_sum += self.canopy_model.get_canopy_coverage(days_after_planting)
                
                kc_avg = kc_sum / days_in_months[month_idx]
                coverage_avg = coverage_sum / days_in_months[month_idx]
                stage = self.canopy_model.get_growth_stage_name(cumulative_days + days_in_months[month_idx] // 2)
            else:
                # Use static fallback Kc
                kc_avg = kc_monthly_fallback[month_idx]
                coverage_avg = None
                stage = None
            
            # Calculate ETc
            etc = eto_monthly * kc_avg
            
            # Calculate effective rainfall
            eff_rain = eff_rain_calculator.usda_sc_method(rainfall_monthly[month_idx])
            
            # Calculate irrigation requirement
            irrig_req = max(0, etc - eff_rain)
            
            # Store result
            results.append(WaterCalculationResult(
                etc=etc,
                kc=kc_avg,
                irrigation_requirement=irrig_req,
                effective_rainfall=eff_rain,
                canopy_coverage=coverage_avg,
                growth_stage=stage
            ))
            
            cumulative_days += days_in_months[month_idx]
        
        return results
    
    def get_irrigation_efficiency_multiplier(self, days_after_planting: int, 
                                            irrigation_method: str = "drip") -> float:
        """
        Get irrigation efficiency multiplier based on canopy (if enabled)
        
        Args:
            days_after_planting: Days since planting
            irrigation_method: "drip", "sprinkler", or "surface"
            
        Returns:
            Efficiency multiplier (0.5-1.2)
        """
        if self.use_canopy and self.canopy_model:
            return self.canopy_model.get_irrigation_efficiency_multiplier(
                days_after_planting, irrigation_method
            )
        else:
            # Return neutral multiplier
            return 1.0
    
    def get_soil_evaporation_factor(self, days_after_planting: int) -> float:
        """
        Get soil evaporation reduction factor based on canopy (if enabled)
        
        Args:
            days_after_planting: Days since planting
            
        Returns:
            Soil evaporation factor (0-1, where 1 = full evaporation)
        """
        if self.use_canopy and self.canopy_model:
            return self.canopy_model.get_soil_evaporation_factor(days_after_planting)
        else:
            # Return full evaporation (no canopy reduction)
            return 1.0


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("WATER CALCULATOR TEST - WITH AND WITHOUT CANOPY")
    print("=" * 70)
    print()
    
    # Test crop data (Tomato)
    tomato_data = {
        'kc_initial': 0.6,
        'kc_mid': 1.15,
        'kc_end': 0.8,
        'growth_stages_days': [25, 40, 45, 25]
    }
    
    # Sample data
    eto_daily = [4.5, 5.0, 5.2, 5.0, 4.8, 5.5, 6.0, 6.2, 5.8, 5.2, 4.8, 4.5]
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    rainfall = [75, 90, 115, 150, 85, 15, 10, 25, 70, 95, 110, 85]
    kc_static = [0.6, 0.7, 0.9, 1.1, 1.15, 1.15, 1.1, 0.9, 0.8, 0.7, 0.6, 0.6]
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    print("TEST 1: WITHOUT CANOPY (Static Kc)")
    print("-" * 70)
    calc_static = WaterCalculator(use_canopy=False)
    calc_static.set_crop("Tomato", tomato_data)
    
    results_static = calc_static.calculate_monthly_requirements(
        eto_daily, days_in_month, rainfall, kc_static
    )
    
    total_etc_static = sum(r.etc for r in results_static)
    total_irrig_static = sum(r.irrigation_requirement for r in results_static)
    
    print(f"Total ETc: {total_etc_static:.0f} mm")
    print(f"Total Irrigation: {total_irrig_static:.0f} mm")
    print()
    
    print("TEST 2: WITH CANOPY (Dynamic Kc)")
    print("-" * 70)
    calc_canopy = WaterCalculator(use_canopy=True)
    calc_canopy.set_crop("Tomato", tomato_data)
    
    results_canopy = calc_canopy.calculate_monthly_requirements(
        eto_daily, days_in_month, rainfall, kc_static
    )
    
    total_etc_canopy = sum(r.etc for r in results_canopy)
    total_irrig_canopy = sum(r.irrigation_requirement for r in results_canopy)
    
    print(f"Total ETc: {total_etc_canopy:.0f} mm")
    print(f"Total Irrigation: {total_irrig_canopy:.0f} mm")
    print()
    
    print("COMPARISON BY MONTH:")
    print("-" * 70)
    print(f"{'Month':<8} {'Static Kc':<10} {'Canopy Kc':<10} {'Coverage':<10} {'Stage':<15}")
    print("-" * 70)
    
    for i in range(12):
        static = results_static[i]
        canopy = results_canopy[i]
        coverage = f"{canopy.canopy_coverage*100:.0f}%" if canopy.canopy_coverage else "N/A"
        stage = canopy.growth_stage or "N/A"
        
        print(f"{months[i]:<8} {static.kc:<10.3f} {canopy.kc:<10.3f} {coverage:<10} {stage:<15}")
    
    print()
    print("=" * 70)
    print(f"WATER SAVINGS: {total_irrig_static - total_irrig_canopy:.0f} mm")
    print(f"EFFICIENCY GAIN: {((total_irrig_static - total_irrig_canopy) / total_irrig_static * 100):.1f}%")
    print("=" * 70)
