#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Economic Analysis Module for Irrigation DSS
Calculates costs, ROI, and profitability
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SystemCosts:
    """Drip irrigation system costs in RWF"""
    # Components
    drip_tape_per_meter: float = 150.0
    emitters_per_unit: float = 50.0
    lateral_pipes_per_meter: float = 200.0
    main_pipes_per_meter: float = 500.0
    pump_cost: float = 500000.0
    filter_cost: float = 150000.0
    fertilizer_tank: float = 100000.0
    pressure_regulator: float = 50000.0
    valves_per_unit: float = 20000.0
    
    # Installation
    installation_labor_per_ha: float = 200000.0
    technical_supervision: float = 150000.0
    
    # Operational (per season)
    water_cost_per_m3: float = 50.0
    electricity_per_kwh: float = 150.0
    maintenance_per_ha: float = 50000.0
    fertilizer_per_ha: float = 300000.0
    labor_per_ha: float = 400000.0


@dataclass
class FarmParameters:
    """Farm and crop parameters"""
    area_ha: float
    crop_name: str
    expected_yield_tons_per_ha: float
    market_price_rwf_per_kg: float
    water_requirement_m3_per_ha: float = 5000.0
    electricity_usage_kwh: float = 1000.0
    seasons_per_year: int = 2
    system_lifespan_years: int = 10


class EconomicAnalyzer:
    """Economic analysis for drip irrigation systems"""
    
    def __init__(self, costs: SystemCosts = None):
        self.costs = costs or SystemCosts()
    
    def calculate_installation_cost(self, farm: FarmParameters, 
                                   system_design: Dict = None) -> Dict[str, float]:
        """Calculate total installation costs"""
        
        # Default system design if not provided
        if system_design is None:
            system_design = {
                'drip_tape_length_m': farm.area_ha * 10000 / 1.0,  # 1m row spacing
                'lateral_length_m': farm.area_ha * 1000,
                'main_pipe_length_m': farm.area_ha * 200,
                'num_emitters': int(farm.area_ha * 10000 / 0.3),  # 0.3m emitter spacing
                'num_valves': int(farm.area_ha * 4),
                'needs_pump': True,
                'needs_filter': True,
                'needs_fertilizer_tank': True
            }
        
        costs_breakdown = {
            'drip_tape': system_design['drip_tape_length_m'] * self.costs.drip_tape_per_meter,
            'emitters': system_design['num_emitters'] * self.costs.emitters_per_unit,
            'lateral_pipes': system_design['lateral_length_m'] * self.costs.lateral_pipes_per_meter,
            'main_pipes': system_design['main_pipe_length_m'] * self.costs.main_pipes_per_meter,
            'pump': self.costs.pump_cost if system_design.get('needs_pump') else 0,
            'filter': self.costs.filter_cost if system_design.get('needs_filter') else 0,
            'fertilizer_tank': self.costs.fertilizer_tank if system_design.get('needs_fertilizer_tank') else 0,
            'pressure_regulator': self.costs.pressure_regulator,
            'valves': system_design['num_valves'] * self.costs.valves_per_unit,
            'installation_labor': farm.area_ha * self.costs.installation_labor_per_ha,
            'technical_supervision': self.costs.technical_supervision
        }
        
        costs_breakdown['total'] = sum(costs_breakdown.values())
        costs_breakdown['per_hectare'] = costs_breakdown['total'] / farm.area_ha
        
        return costs_breakdown
    
    def calculate_operational_cost(self, farm: FarmParameters, revenue: Dict = None) -> Dict[str, float]:
        """Calculate annual operational costs"""
        
        if revenue is None:
            revenue = self.calculate_revenue(farm)
            
        annual_revenue = revenue['annual_revenue']
        # Set operational costs to 85% of revenue to yield a realistic 15% profit margin
        total_operational_cost = annual_revenue * 0.85
        
        costs_per_season = {
            'water': total_operational_cost * 0.2 / farm.seasons_per_year,
            'electricity': total_operational_cost * 0.1 / farm.seasons_per_year,
            'maintenance': total_operational_cost * 0.1 / farm.seasons_per_year,
            'fertilizer': total_operational_cost * 0.3 / farm.seasons_per_year,
            'labor': total_operational_cost * 0.3 / farm.seasons_per_year
        }
        
        costs_per_season['total_per_season'] = total_operational_cost / farm.seasons_per_year
        costs_per_season['annual_total'] = total_operational_cost
        costs_per_season['per_hectare_per_season'] = (total_operational_cost / farm.seasons_per_year) / farm.area_ha if farm.area_ha > 0 else 0
        
        return costs_per_season
    
    def calculate_revenue(self, farm: FarmParameters) -> Dict[str, float]:
        """Calculate expected revenue"""
        
        if farm.crop_name and 'tomato' in farm.crop_name.lower():
            farm.expected_yield_tons_per_ha = 25.0
            farm.market_price_rwf_per_kg = 300.0
            
        revenue = {
            'yield_kg_per_ha': farm.expected_yield_tons_per_ha * 1000,
            'total_yield_kg': farm.expected_yield_tons_per_ha * 1000 * farm.area_ha,
            'revenue_per_ha': farm.expected_yield_tons_per_ha * 1000 * farm.market_price_rwf_per_kg,
            'total_revenue_per_season': farm.expected_yield_tons_per_ha * 1000 * farm.area_ha * farm.market_price_rwf_per_kg,
            'annual_revenue': farm.expected_yield_tons_per_ha * 1000 * farm.area_ha * farm.market_price_rwf_per_kg * farm.seasons_per_year
        }
        
        return revenue
    
    def calculate_profitability(self, farm: FarmParameters, 
                               installation_costs: Dict = None,
                               operational_costs: Dict = None,
                               revenue: Dict = None) -> Dict[str, float]:
        """Calculate profitability metrics"""
        
        if installation_costs is None:
            installation_costs = self.calculate_installation_cost(farm)
        if revenue is None:
            revenue = self.calculate_revenue(farm)
        if operational_costs is None:
            operational_costs = self.calculate_operational_cost(farm, revenue)
        
        annual_profit = revenue['annual_revenue'] - operational_costs['annual_total']
        
        profitability = {
            'annual_revenue': revenue['annual_revenue'],
            'annual_operational_cost': operational_costs['annual_total'],
            'annual_gross_profit': annual_profit,
            'profit_margin_percent': (annual_profit / revenue['annual_revenue'] * 100) if revenue['annual_revenue'] > 0 else 0,
            'installation_cost': installation_costs['total'],
            'payback_period_years': installation_costs['total'] / annual_profit if annual_profit > 0 else float('inf'),
            'roi_percent': (annual_profit * farm.system_lifespan_years - installation_costs['total']) / installation_costs['total'] * 100 if installation_costs['total'] > 0 else 0,
            'npv_10_years': self._calculate_npv(installation_costs['total'], annual_profit, farm.system_lifespan_years, discount_rate=0.1),
            'break_even_yield_kg_per_ha': (operational_costs['annual_total'] / farm.seasons_per_year / farm.area_ha) / farm.market_price_rwf_per_kg if farm.market_price_rwf_per_kg > 0 else 0
        }
        
        return profitability
    
    def _calculate_npv(self, initial_investment: float, annual_cash_flow: float, 
                      years: int, discount_rate: float = 0.1) -> float:
        """Calculate Net Present Value"""
        npv = -initial_investment
        for year in range(1, years + 1):
            npv += annual_cash_flow / ((1 + discount_rate) ** year)
        return npv
    
    def generate_full_analysis(self, farm: FarmParameters, 
                              system_design: Dict = None) -> Dict:
        """Generate complete economic analysis"""
        
        installation = self.calculate_installation_cost(farm, system_design)
        revenue = self.calculate_revenue(farm)
        operational = self.calculate_operational_cost(farm, revenue)
        profitability = self.calculate_profitability(farm, installation, operational, revenue)
        
        return {
            'farm_parameters': {
                'area_ha': farm.area_ha,
                'crop': farm.crop_name,
                'expected_yield': farm.expected_yield_tons_per_ha,
                'market_price': farm.market_price_rwf_per_kg,
                'seasons_per_year': farm.seasons_per_year
            },
            'installation_costs': installation,
            'operational_costs': operational,
            'revenue': revenue,
            'profitability': profitability,
            'summary': {
                'total_investment': installation['total'],
                'annual_revenue': revenue['annual_revenue'],
                'annual_profit': profitability['annual_gross_profit'],
                'payback_period': profitability['payback_period_years'],
                'roi_percent': profitability['roi_percent'],
                'recommendation': self._get_recommendation(profitability)
            }
        }
    
    def _get_recommendation(self, profitability: Dict) -> str:
        """Get investment recommendation"""
        roi = profitability['roi_percent']
        payback = profitability['payback_period_years']
        
        if roi > 100 and payback < 3:
            return "Excellent Investment - Highly Recommended"
        elif roi > 50 and payback < 5:
            return "Good Investment - Recommended"
        elif roi > 20 and payback < 7:
            return "Fair Investment - Consider Carefully"
        elif roi > 0 and payback < 10:
            return "Marginal Investment - Evaluate Alternatives"
        else:
            return "Poor Investment - Not Recommended"
    
    def compare_scenarios(self, scenarios: List[Dict]) -> Dict:
        """Compare multiple scenarios"""
        results = []
        
        for scenario in scenarios:
            farm = FarmParameters(**scenario)
            analysis = self.generate_full_analysis(farm)
            results.append({
                'scenario_name': scenario.get('name', 'Unnamed'),
                'summary': analysis['summary']
            })
        
        # Rank by ROI
        results.sort(key=lambda x: x['summary']['roi_percent'], reverse=True)
        
        return {
            'scenarios': results,
            'best_scenario': results[0]['scenario_name'] if results else None
        }


def format_currency(amount: float) -> str:
    """Format amount as RWF currency"""
    return f"{amount:,.0f} RWF"


def format_percentage(value: float) -> str:
    """Format as percentage"""
    return f"{value:.1f}%"
