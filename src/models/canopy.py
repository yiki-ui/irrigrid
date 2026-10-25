#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crop Canopy Coverage Module
Calculates canopy development and its impact on water requirements
Based on FAO-56 methodology
"""

import numpy as np
from typing import Tuple, List
from dataclasses import dataclass


@dataclass
class CanopyStage:
    """Canopy development stage"""
    name: str
    days: int
    coverage_start: float  # 0-1
    coverage_end: float    # 0-1
    kc: float              # Crop coefficient


class CanopyModel:
    """
    Crop canopy development model
    
    Canopy coverage affects:
    1. Evapotranspiration (via Kc)
    2. Solar radiation interception
    3. Soil water evaporation
    4. Irrigation efficiency
    """
    
    def __init__(self, crop_name: str, crop_data: dict):
        """
        Initialize canopy model for a crop
        
        Args:
            crop_name: Name of the crop
            crop_data: Dictionary with crop parameters (kc values, growth stages)
        """
        self.crop_name = crop_name
        self.kc_initial = crop_data.get('kc_initial', 0.6)
        self.kc_mid = crop_data.get('kc_mid', 1.15)
        self.kc_end = crop_data.get('kc_end', 0.8)
        self.growth_stages = crop_data.get('growth_stages_days', [30, 40, 50, 30])
        
        # Calculate canopy coverage progression
        self.canopy_stages = self._calculate_canopy_stages()
    
    def _calculate_canopy_stages(self) -> List[CanopyStage]:
        """
        Calculate canopy coverage for each growth stage
        
        FAO-56 approach:
        - Initial stage: 0-20% coverage (establishment)
        - Development: 20-90% coverage (rapid growth)
        - Mid-season: 90-100% coverage (full canopy)
        - Late season: 100-40% coverage (senescence)
        """
        stages = []
        
        # Stage 1: Initial (planting to ~10% ground cover)
        stages.append(CanopyStage(
            name="Initial",
            days=self.growth_stages[0],
            coverage_start=0.05,  # 5% (seedling)
            coverage_end=0.20,    # 20%
            kc=self.kc_initial
        ))
        
        # Stage 2: Development (rapid vegetative growth)
        stages.append(CanopyStage(
            name="Development",
            days=self.growth_stages[1],
            coverage_start=0.20,  # 20%
            coverage_end=0.90,    # 90%
            kc=(self.kc_initial + self.kc_mid) / 2  # Transition
        ))
        
        # Stage 3: Mid-season (full canopy, flowering/fruiting)
        stages.append(CanopyStage(
            name="Mid-Season",
            days=self.growth_stages[2],
            coverage_start=0.90,  # 90%
            coverage_end=0.98,    # 98% (full cover)
            kc=self.kc_mid
        ))
        
        # Stage 4: Late season (maturation, senescence)
        stages.append(CanopyStage(
            name="Late Season",
            days=self.growth_stages[3],
            coverage_start=0.98,  # 98%
            coverage_end=0.40,    # 40% (leaf drop)
            kc=self.kc_end
        ))
        
        return stages
    
    def get_canopy_coverage(self, days_after_planting: int) -> float:
        """
        Get canopy coverage fraction at a given day
        
        Args:
            days_after_planting: Days since planting
            
        Returns:
            Canopy coverage (0-1)
        """
        cumulative_days = 0
        
        for stage in self.canopy_stages:
            if days_after_planting <= cumulative_days + stage.days:
                # Within this stage
                days_into_stage = days_after_planting - cumulative_days
                fraction = days_into_stage / stage.days
                
                # Linear interpolation between start and end coverage
                coverage = stage.coverage_start + (
                    stage.coverage_end - stage.coverage_start
                ) * fraction
                
                return min(1.0, max(0.0, coverage))
            
            cumulative_days += stage.days
        
        # After all stages (harvest or beyond)
        return self.canopy_stages[-1].coverage_end
    
    def get_kc_adjusted(self, days_after_planting: int) -> float:
        """
        Get Kc value adjusted for current canopy stage
        
        Args:
            days_after_planting: Days since planting
            
        Returns:
            Crop coefficient (Kc)
        """
        cumulative_days = 0
        
        for i, stage in enumerate(self.canopy_stages):
            if days_after_planting <= cumulative_days + stage.days:
                # Within this stage
                if i == 0:
                    return self.kc_initial
                elif i == 1:
                    # Development: interpolate between initial and mid
                    days_into_stage = days_after_planting - cumulative_days
                    fraction = days_into_stage / stage.days
                    return self.kc_initial + (
                        self.kc_mid - self.kc_initial
                    ) * fraction
                elif i == 2:
                    return self.kc_mid
                else:  # i == 3
                    # Late season: interpolate between mid and end
                    days_into_stage = days_after_planting - cumulative_days
                    fraction = days_into_stage / stage.days
                    return self.kc_mid + (
                        self.kc_end - self.kc_mid
                    ) * fraction
            
            cumulative_days += stage.days
        
        # After all stages
        return self.kc_end
    
    def get_solar_interception(self, days_after_planting: int) -> float:
        """
        Calculate fraction of solar radiation intercepted by canopy
        
        Args:
            days_after_planting: Days since planting
            
        Returns:
            Solar interception fraction (0-1)
        """
        coverage = self.get_canopy_coverage(days_after_planting)
        
        # Beer-Lambert law for radiation interception
        # I = I0 * exp(-k * LAI)
        # Simplified: Use coverage as proxy for LAI
        k = 0.5  # Extinction coefficient (typical for many crops)
        LAI_approx = coverage * 4.0  # Approximate LAI from coverage
        
        interception = 1 - np.exp(-k * LAI_approx)
        return min(1.0, interception)
    
    def get_soil_evaporation_factor(self, days_after_planting: int) -> float:
        """
        Calculate soil evaporation reduction factor based on canopy
        
        Full canopy = less soil evaporation
        
        Args:
            days_after_planting: Days since planting
            
        Returns:
            Soil evaporation factor (0-1, where 1 = full evaporation)
        """
        coverage = self.get_canopy_coverage(days_after_planting)
        
        # Exponential reduction with canopy coverage
        # At 100% coverage, soil evaporation is ~10% of bare soil
        return np.exp(-2.5 * coverage)
    
    def get_irrigation_efficiency_multiplier(self, days_after_planting: int,
                                            irrigation_method: str = "drip") -> float:
        """
        Calculate irrigation efficiency adjustment based on canopy
        
        Args:
            days_after_planting: Days since planting
            irrigation_method: "drip", "sprinkler", or "surface"
            
        Returns:
            Efficiency multiplier (0.5-1.2)
        """
        coverage = self.get_canopy_coverage(days_after_planting)
        
        if irrigation_method.lower() == "drip":
            # Drip is efficient regardless of canopy
            return 0.95 + 0.05 * coverage  # 0.95 - 1.0
        
        elif irrigation_method.lower() == "sprinkler":
            # Sprinkler efficiency improves with canopy (less wind drift)
            # But decreases slightly with very dense canopy (interception loss)
            if coverage < 0.7:
                return 0.75 + 0.20 * coverage  # 0.75 - 0.89
            else:
                return 0.95 - 0.05 * (coverage - 0.7)  # 0.95 - 0.93
        
        elif irrigation_method.lower() == "surface":
            # Surface irrigation: canopy helps reduce evaporation during application
            return 0.60 + 0.15 * coverage  # 0.60 - 0.75
        
        else:
            return 1.0
    
    def get_growth_stage_name(self, days_after_planting: int) -> str:
        """
        Get current growth stage name
        
        Args:
            days_after_planting: Days since planting
            
        Returns:
            Stage name
        """
        cumulative_days = 0
        
        for stage in self.canopy_stages:
            if days_after_planting <= cumulative_days + stage.days:
                return stage.name
            cumulative_days += stage.days
        
        return "Post-Harvest"
    
    def calculate_etc_with_canopy(self, eto: float, days_after_planting: int) -> float:
        """
        Calculate crop evapotranspiration considering canopy coverage
        
        ETc = ETo * Kc (adjusted)
        
        Args:
            eto: Reference evapotranspiration (mm/day)
            days_after_planting: Days since planting
            
        Returns:
            Crop evapotranspiration (mm/day)
        """
        kc = self.get_kc_adjusted(days_after_planting)
        return eto * kc
    
    def get_full_season_profile(self) -> dict:
        """
        Get complete canopy profile for the entire growing season
        
        Returns:
            Dictionary with daily values
        """
        total_days = sum(stage.days for stage in self.canopy_stages)
        
        profile = {
            'days': list(range(total_days + 1)),
            'coverage': [],
            'kc': [],
            'solar_interception': [],
            'soil_evap_factor': [],
            'stage': []
        }
        
        for day in range(total_days + 1):
            profile['coverage'].append(self.get_canopy_coverage(day))
            profile['kc'].append(self.get_kc_adjusted(day))
            profile['solar_interception'].append(self.get_solar_interception(day))
            profile['soil_evap_factor'].append(self.get_soil_evaporation_factor(day))
            profile['stage'].append(self.get_growth_stage_name(day))
        
        return profile


# Example usage and testing
if __name__ == "__main__":
    # Test with tomato crop
    tomato_data = {
        'kc_initial': 0.6,
        'kc_mid': 1.15,
        'kc_end': 0.8,
        'growth_stages_days': [25, 40, 45, 25]  # Total 135 days
    }
    
    canopy = CanopyModel("Tomato", tomato_data)
    
    print("=" * 60)
    print("CANOPY DEVELOPMENT PROFILE - TOMATO")
    print("=" * 60)
    print()
    
    test_days = [0, 10, 25, 50, 90, 110, 135]
    
    for day in test_days:
        coverage = canopy.get_canopy_coverage(day)
        kc = canopy.get_kc_adjusted(day)
        stage = canopy.get_growth_stage_name(day)
        solar = canopy.get_solar_interception(day)
        soil_evap = canopy.get_soil_evaporation_factor(day)
        
        print(f"Day {day:3d} ({stage:12s}):")
        print(f"  Coverage: {coverage*100:5.1f}%")
        print(f"  Kc:       {kc:.3f}")
        print(f"  Solar Interception: {solar*100:5.1f}%")
        print(f"  Soil Evaporation:   {soil_evap*100:5.1f}%")
        print()
    
    # Test ETc calculation
    eto_test = 5.0  # mm/day
    print(f"With ETo = {eto_test} mm/day:")
    for day in [25, 65, 110]:
        etc = canopy.calculate_etc_with_canopy(eto_test, day)
        print(f"  Day {day}: ETc = {etc:.2f} mm/day")
