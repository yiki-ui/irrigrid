#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crop Water Requirement Calculator
Calculates ETc, irrigation requirements, and water balance
"""

from typing import List, Dict, Optional
from datetime import date, timedelta
import numpy as np


class CropWaterRequirement:
    """Calculate crop water requirements"""
    
    def __init__(self, eto_data: List[float], kc_values: List[float], 
                 rainfall: List[float], effective_rain: List[float]):
        """
        Initialize crop water requirement calculator
        
        Args:
            eto_data: List of ETo values (mm/day or mm/month)
            kc_values: List of Kc values for each period
            rainfall: List of rainfall values (mm)
            effective_rain: List of effective rainfall values (mm)
        """
        self.eto_data = eto_data
        self.kc_values = kc_values
        self.rainfall = rainfall
        self.effective_rain = effective_rain
    
    def calculate_etc(self) -> List[float]:
        """
        Calculate crop evapotranspiration (ETc)
        ETc = Kc × ETo
        
        Returns:
            List of ETc values
        """
        return [kc * eto for kc, eto in zip(self.kc_values, self.eto_data)]
    
    def calculate_irrigation_requirement(self) -> List[float]:
        """
        Calculate irrigation requirement
        IR = ETc - Effective Rainfall
        
        Returns:
            List of irrigation requirements (mm)
        """
        etc = self.calculate_etc()
        return [max(0, etc_val - eff_rain) 
                for etc_val, eff_rain in zip(etc, self.effective_rain)]
    
    def calculate_total_water_requirement(self) -> Dict[str, float]:
        """
        Calculate total water requirements
        
        Returns:
            Dictionary with total ETc, rainfall, effective rain, and irrigation requirement
        """
        etc = self.calculate_etc()
        ir = self.calculate_irrigation_requirement()
        
        return {
            "total_etc": sum(etc),
            "total_rainfall": sum(self.rainfall),
            "total_effective_rain": sum(self.effective_rain),
            "total_irrigation_requirement": sum(ir),
            "irrigation_efficiency": (sum(self.effective_rain) / sum(self.rainfall) * 100) if sum(self.rainfall) > 0 else 0
        }
    
    def get_monthly_summary(self, months: List[str]) -> List[Dict]:
        """
        Get monthly water requirement summary
        
        Args:
            months: List of month names
            
        Returns:
            List of dictionaries with monthly data
        """
        etc = self.calculate_etc()
        ir = self.calculate_irrigation_requirement()
        
        summary = []
        for i, month in enumerate(months):
            if i < len(etc):
                summary.append({
                    "month": month,
                    "eto": round(self.eto_data[i], 2),
                    "kc": round(self.kc_values[i], 2),
                    "etc": round(etc[i], 2),
                    "rainfall": round(self.rainfall[i], 2),
                    "effective_rain": round(self.effective_rain[i], 2),
                    "irrigation_req": round(ir[i], 2)
                })
        
        return summary


class IrrigationScheduleGenerator:
    """Generate detailed irrigation schedules"""
    
    def __init__(self, etc_daily: List[float], effective_rain_daily: List[float],
                 soil_tam: float, critical_depletion: float, application_efficiency: float = 0.85):
        """
        Initialize irrigation schedule generator
        
        Args:
            etc_daily: Daily ETc values (mm/day)
            effective_rain_daily: Daily effective rainfall (mm/day)
            soil_tam: Total available moisture (mm)
            critical_depletion: Critical depletion fraction (p)
            application_efficiency: Irrigation application efficiency (0-1)
        """
        self.etc_daily = etc_daily
        self.effective_rain_daily = effective_rain_daily
        self.soil_tam = soil_tam
        self.critical_depletion = critical_depletion
        self.application_efficiency = application_efficiency
        self.raw = soil_tam * critical_depletion  # Readily available water
    
    def generate_schedule(self, start_date: date, initial_depletion: float = 0) -> List[Dict]:
        """
        Generate irrigation schedule
        
        Args:
            start_date: Start date for schedule
            initial_depletion: Initial soil moisture depletion (mm)
            
        Returns:
            List of irrigation events with dates and amounts
        """
        schedule = []
        current_depletion = initial_depletion
        
        for day, (etc, eff_rain) in enumerate(zip(self.etc_daily, self.effective_rain_daily)):
            current_date = start_date + timedelta(days=day)
            
            # Update depletion
            net_depletion = etc - eff_rain
            current_depletion += net_depletion
            
            # Check if irrigation is needed
            if current_depletion >= self.raw:
                # Calculate irrigation amount
                gross_irrigation = current_depletion / self.application_efficiency
                
                schedule.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "day": day + 1,
                    "depletion_before": round(current_depletion, 2),
                    "net_irrigation": round(current_depletion, 2),
                    "gross_irrigation": round(gross_irrigation, 2),
                    "etc": round(etc, 2),
                    "effective_rain": round(eff_rain, 2)
                })
                
                # Reset depletion after irrigation
                current_depletion = 0
        
        return schedule
    
    def calculate_irrigation_interval(self) -> float:
        """
        Calculate average irrigation interval in days
        
        Returns:
            Average days between irrigations
        """
        avg_etc = np.mean(self.etc_daily)
        avg_eff_rain = np.mean(self.effective_rain_daily)
        net_water_use = avg_etc - avg_eff_rain
        
        if net_water_use <= 0:
            return float('inf')  # No irrigation needed
        
        return self.raw / net_water_use
    
    def get_schedule_summary(self, schedule: List[Dict]) -> Dict:
        """
        Get summary statistics for irrigation schedule
        
        Args:
            schedule: List of irrigation events
            
        Returns:
            Dictionary with summary statistics
        """
        if not schedule:
            return {
                "total_events": 0,
                "total_net_irrigation": 0,
                "total_gross_irrigation": 0,
                "average_interval": 0,
                "average_depth": 0
            }
        
        total_net = sum(event["net_irrigation"] for event in schedule)
        total_gross = sum(event["gross_irrigation"] for event in schedule)
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(schedule)):
            intervals.append(schedule[i]["day"] - schedule[i-1]["day"])
        
        return {
            "total_events": len(schedule),
            "total_net_irrigation": round(total_net, 2),
            "total_gross_irrigation": round(total_gross, 2),
            "average_interval": round(np.mean(intervals), 1) if intervals else 0,
            "average_depth": round(total_net / len(schedule), 2)
        }


class WaterBalanceCalculator:
    """Calculate daily water balance"""
    
    def __init__(self, soil_tam: float, initial_moisture: float):
        """
        Initialize water balance calculator
        
        Args:
            soil_tam: Total available moisture (mm)
            initial_moisture: Initial soil moisture (mm)
        """
        self.soil_tam = soil_tam
        self.initial_moisture = initial_moisture
    
    def calculate_daily_balance(self, etc_daily: List[float], 
                               rain_daily: List[float],
                               irrigation_events: Dict[int, float]) -> List[Dict]:
        """
        Calculate daily water balance
        
        Args:
            etc_daily: Daily ETc values (mm)
            rain_daily: Daily rainfall (mm)
            irrigation_events: Dictionary mapping day number to irrigation amount
            
        Returns:
            List of daily water balance data
        """
        balance = []
        current_moisture = self.initial_moisture
        
        for day, (etc, rain) in enumerate(zip(etc_daily, rain_daily)):
            # Get irrigation for this day
            irrigation = irrigation_events.get(day, 0)
            
            # Calculate water inputs and outputs
            water_in = rain + irrigation
            water_out = etc
            
            # Update moisture
            current_moisture = min(self.soil_tam, current_moisture + water_in - water_out)
            current_moisture = max(0, current_moisture)
            
            # Calculate depletion
            depletion = self.soil_tam - current_moisture
            depletion_percent = (depletion / self.soil_tam) * 100
            
            balance.append({
                "day": day + 1,
                "etc": round(etc, 2),
                "rain": round(rain, 2),
                "irrigation": round(irrigation, 2),
                "moisture": round(current_moisture, 2),
                "depletion": round(depletion, 2),
                "depletion_percent": round(depletion_percent, 1)
            })
        
        return balance
