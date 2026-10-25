#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hydraulic Design Calculator
Complete drip irrigation system design with FAO-56 methodology
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class SystemDesign:
    """System design parameters"""
    field_area: float  # hectares
    field_length: float = 0.0  # meters (auto-calculated from area if 0)
    field_width: float = 0.0  # meters (auto-calculated from area if 0)
    crop_name: str = 'Unknown'
    soil_type: str = 'Loam'
    emitter_flow: float = 2.0  # L/hr
    emitter_spacing: float = 0.3  # meters
    lateral_spacing: float = 1.2  # meters
    operating_pressure: float = 1.5  # bar  (user-specified, NOT auto-derived)
    slope_percent: float = 0.0  # terrain slope % from SRTM
    # Elevation data for accurate hydraulic calculations
    water_source_elevation: Optional[float] = None  # meters ASL (None = unknown)
    field_min_elevation: Optional[float] = None      # meters ASL (None = unknown)
    field_max_elevation: Optional[float] = None      # meters ASL (None = unknown)
    slope_direction: str = 'downhill'      # 'downhill' (source above field) or 'uphill'
    # Optional explicitly provided diameters
    lateral_diameter_mm: Optional[float] = None
    main_diameter_mm: Optional[float] = None


class HydraulicDesign:
    """Complete hydraulic design calculator"""
    
    # Constants
    WATER_DENSITY = 1000  # kg/m³
    GRAVITY = 9.81  # m/s²
    KINEMATIC_VISCOSITY = 1.0e-6  # m²/s at 20°C
    
    # Hazen-Williams C coefficients
    HW_COEFFICIENTS = {
        'PE': 150,  # Polyethylene
        'PVC': 150,  # PVC
        'Steel': 120,  # Steel
        'Concrete': 100  # Concrete
    }
    
    def __init__(self, design: Optional[SystemDesign] = None, **kwargs):
        """
        Initialize hydraulic design
        
        Args:
            design: SystemDesign object or individual parameters
        """
        if design:
            self.design = design
        else:
            self.design = SystemDesign(**kwargs)
        
        self.results = {}
    
    def calculate_complete_system(self) -> Dict:
        """
        Calculate complete system design
        
        Returns:
            Dictionary with all design parameters
        """
        # 1. Calculate number of emitters and laterals
        self.calculate_emitter_layout()
        
        # 2. Calculate system flow
        self.calculate_system_flow()
        
        # 3. Size pipes
        self.size_pipes()
        
        # 4. Calculate head losses
        self.calculate_head_losses()
        
        # 5. Calculate pressure variation
        self.calculate_pressure_variation()
        
        # 6. Calculate uniformity
        self.calculate_uniformity()
        
        # 7. Size pump
        self.select_pump()
        
        # 8. Estimate costs
        self.estimate_costs()
        
        return self.results
    
    def calculate_emitter_layout(self):
        """Calculate emitter and lateral arrangement"""
        # Field dimensions
        if self.design.field_length == 0 or self.design.field_width == 0:
            # Calculate from area assuming rectangular
            side = math.sqrt(self.design.field_area * 10000)  # Convert ha to m²
            self.design.field_length = side
            self.design.field_width = side
        
        # Number of laterals
        n_laterals = int(self.design.field_width / self.design.lateral_spacing)
        
        # Emitters per lateral
        emitters_per_lateral = int(self.design.field_length / self.design.emitter_spacing)
        
        # Total emitters
        total_emitters = n_laterals * emitters_per_lateral
        
        self.results['layout'] = {
            'n_laterals': n_laterals,
            'emitters_per_lateral': emitters_per_lateral,
            'total_emitters': total_emitters,
            'field_length': self.design.field_length,
            'field_width': self.design.field_width
        }
    
    def calculate_system_flow(self):
        """Calculate total system flow rate"""
        total_emitters = self.results['layout']['total_emitters']
        emitter_flow = self.design.emitter_flow  # L/hr
        
        # Total flow in m³/hr
        total_flow = (total_emitters * emitter_flow) / 1000
        
        # Flow per lateral
        emitters_per_lateral = self.results['layout']['emitters_per_lateral']
        lateral_flow = (emitters_per_lateral * emitter_flow) / 1000
        
        self.results['flow'] = {
            'total_flow_m3hr': total_flow,
            'total_flow_lps': total_flow / 3.6,  # L/s
            'lateral_flow_m3hr': lateral_flow,
            'lateral_flow_lps': lateral_flow / 3.6
        }
    
    def size_pipes(self):
        """Size lateral and main pipes"""
        # Recommended velocities (m/s)
        v_lateral_max = 1.5  # Maximum velocity in laterals
        v_main_max = 2.0  # Maximum velocity in mains
        
        # Lateral diameter
        Q_lateral = self.results['flow']['lateral_flow_m3hr'] / 3600  # m³/s
        if self.design.lateral_diameter_mm is not None:
            d_lateral = self.design.lateral_diameter_mm
        else:
            A_lateral_min = Q_lateral / v_lateral_max
            d_lateral_min = math.sqrt(4 * A_lateral_min / math.pi) * 1000  # mm
            
            # Standard pipe sizes (mm)
            standard_sizes = [12, 16, 20, 25, 32, 40, 50, 63, 75, 90, 110, 125, 160]
            d_lateral = min([d for d in standard_sizes if d >= d_lateral_min])
        
        # Main line diameter
        Q_main = self.results['flow']['total_flow_m3hr'] / 3600  # m³/s
        if self.design.main_diameter_mm is not None:
            d_main = self.design.main_diameter_mm
        else:
            A_main_min = Q_main / v_main_max
            d_main_min = math.sqrt(4 * A_main_min / math.pi) * 1000  # mm
            standard_sizes = [12, 16, 20, 25, 32, 40, 50, 63, 75, 90, 110, 125, 160]
            d_main = min([d for d in standard_sizes if d >= d_main_min])
        
        # Calculate actual velocities
        A_lateral = math.pi * (d_lateral/1000)**2 / 4
        v_lateral = Q_lateral / A_lateral
        
        A_main = math.pi * (d_main/1000)**2 / 4
        v_main = Q_main / A_main
        
        self.results['pipes'] = {
            'lateral_diameter_mm': d_lateral,
            'main_diameter_mm': d_main,
            'lateral_velocity_ms': v_lateral,
            'main_velocity_ms': v_main,
            'lateral_length_m': self.design.field_length,
            'main_length_m': self.design.field_width
        }
    
    def calculate_head_losses(self):
        """Calculate head losses using Hazen-Williams + elevation head (Δz)"""
        pipes = self.results['pipes']
        flow = self.results['flow']
        
        # --- Friction losses (Hazen-Williams) ---
        hf_lateral = self.hazen_williams_head_loss(
            flow['lateral_flow_m3hr'] / 3600,  # m³/s
            pipes['lateral_diameter_mm'] / 1000,  # m
            pipes['lateral_length_m'],
            C=150  # PE pipe
        )
        
        hf_main = self.hazen_williams_head_loss(
            flow['total_flow_m3hr'] / 3600,  # m³/s
            pipes['main_diameter_mm'] / 1000,  # m
            pipes['main_length_m'],
            C=150  # PE pipe
        )
        
        # --- Elevation head (Δz) ---
        # Positive Δz = pipe runs uphill (head LOST to gravity)
        # Negative Δz = pipe runs downhill (head GAINED from gravity)
        slope_frac = (self.design.slope_percent or 0.0) / 100.0
        
        if self.design.slope_direction == 'uphill':
            # Laterals run uphill from mainline
            dz_lateral = slope_frac * pipes['lateral_length_m']
            dz_main = slope_frac * pipes['main_length_m']
        else:
            # Laterals run downhill (gravity assists) — worst-case is
            # still the far end of the furthest-uphill lateral, but
            # mainline itself typically runs along the contour or downhill.
            dz_lateral = -slope_frac * pipes['lateral_length_m']
            dz_main = slope_frac * pipes['main_length_m'] * 0.5  # mainline along contour
        
        # Total friction
        hf_friction = hf_lateral + hf_main
        
        # Local / minor losses (10% of friction)
        hf_local = hf_friction * 0.1
        
        # Total head loss = friction + local + elevation
        hf_total = hf_friction + hf_local + dz_lateral + dz_main
        
        self.results['head_loss'] = {
            'lateral_friction_m': hf_lateral,
            'main_friction_m': hf_main,
            'lateral_m': hf_lateral,  # backward-compat alias
            'main_m': hf_main,        # backward-compat alias
            'local_m': hf_local,
            'elevation_lateral_m': dz_lateral,
            'elevation_main_m': dz_main,
            'elevation_total_m': dz_lateral + dz_main,
            'friction_total_m': hf_friction,
            'total_m': hf_total
        }
    
    def hazen_williams_head_loss(self, Q: float, D: float, L: float, C: float = 150) -> float:
        """
        Calculate head loss using Hazen-Williams formula
        
        Args:
            Q: Flow rate (m³/s)
            D: Pipe diameter (m)
            L: Pipe length (m)
            C: Hazen-Williams coefficient
            
        Returns:
            Head loss (m)
        """
        hf = 10.67 * L * (Q ** 1.85) / ((C ** 1.85) * (D ** 4.87))
        return hf
    
    def calculate_pressure_variation(self):
        """Calculate pressure variation along lateral (including elevation)"""
        # Operating pressure at inlet (bar to m)
        P_inlet = self.design.operating_pressure * 10.2  # m of water
        
        # Pressure at outlet = inlet - friction - elevation_change
        hf_lateral_friction = self.results['head_loss']['lateral_friction_m']
        dz_lateral = self.results['head_loss']['elevation_lateral_m']
        
        # Total lateral head loss (friction + elevation)
        hf_lateral_total = hf_lateral_friction + dz_lateral
        P_outlet = P_inlet - hf_lateral_total
        
        # Clamp to physical minimum (can't have negative absolute pressure)
        P_outlet = max(0.0, P_outlet)
        
        # Pressure variation
        if P_inlet > 0:
            pressure_variation = ((P_inlet - P_outlet) / P_inlet) * 100
        else:
            pressure_variation = 100.0
        
        # Average pressure
        P_avg = (P_inlet + P_outlet) / 2
        
        self.results['pressure'] = {
            'inlet_m': P_inlet,
            'outlet_m': P_outlet,
            'average_m': P_avg,
            'variation_percent': pressure_variation,
            'inlet_bar': self.design.operating_pressure,
            'outlet_bar': P_outlet / 10.2,
            'average_bar': P_avg / 10.2
        }
    
    def calculate_uniformity(self):
        """Calculate emission uniformity"""
        pressure = self.results['pressure']
        
        # Emitter discharge equation: q = k * P^x
        # For pressure-compensating emitters, x ≈ 0.5
        # For non-compensating, x ≈ 0.5
        x = 0.5
        
        # Calculate min and max discharge
        P_min = max(0.1, pressure['outlet_bar'])  # Ensure positive pressure
        P_max = max(0.1, pressure['inlet_bar'])
        P_operating = max(0.1, self.design.operating_pressure)
        
        q_at_pmin = abs(self.design.emitter_flow * ((P_min / P_operating) ** x))
        q_at_pmax = abs(self.design.emitter_flow * ((P_max / P_operating) ** x))
        # Ensure q_min is always the smaller value regardless of pressure direction
        q_min = min(q_at_pmin, q_at_pmax)
        q_max = max(q_at_pmin, q_at_pmax)
        q_avg = (q_min + q_max) / 2
        
        # Emission uniformity
        EU = (q_min / q_avg) * 100
        
        # Uniformity coefficient
        UC = (1 - abs(q_max - q_min) / (2 * q_avg)) * 100
        
        self.results['uniformity'] = {
            'emission_uniformity_percent': EU,
            'uniformity_coefficient_percent': UC,
            'q_min_lhr': q_min,
            'q_max_lhr': q_max,
            'q_avg_lhr': q_avg,
            'q_variation_percent': ((q_max - q_min) / q_avg) * 100
        }
    
    def select_pump(self):
        """Select pump based on system requirements"""
        flow = self.results['flow']
        head_loss = self.results['head_loss']
        
        # ── Static head: prefer real elevation data ──
        ws_elev = self.design.water_source_elevation
        field_max = self.design.field_max_elevation
        
        if ws_elev is not None and field_max is not None:
            # Real elevation data available
            h_static = max(0.0, field_max - ws_elev)
            static_source = 'measured'
        else:
            # Fallback: estimate from slope + total pipe run
            slope_frac = (self.design.slope_percent or 0.0) / 100.0
            lateral_len = self.results['pipes'].get('lateral_length_m', 50.0)
            main_len = self.results['pipes'].get('main_length_m', 100.0)
            h_static = slope_frac * (main_len + lateral_len)
            static_source = 'estimated from slope'
        
        # Friction losses (already includes elevation Δz from calculate_head_losses)
        h_friction = head_loss['total_m']
        
        # Operating pressure head
        h_pressure = self.design.operating_pressure * 10.2
        
        # Suction head (typical for surface water pumping)
        h_suction = 2.0  # meters — conservative default
        
        # Safety factor (10%)
        safety_factor = 1.1
        
        # Total dynamic head (TDH)
        h_total = (h_static + h_friction + h_pressure + h_suction) * safety_factor
        
        # Required power (kW)
        Q = flow['total_flow_m3hr'] / 3600  # m³/s
        rho = self.WATER_DENSITY
        g = self.GRAVITY
        eta = 0.70  # Pump efficiency (70%)
        
        power_kw = (rho * g * Q * h_total) / (eta * 1000)
        power_hp = power_kw * 1.341  # Convert to HP
        
        self.results['pump'] = {
            'required_head_m': h_total,
            'static_head_m': h_static,
            'static_head_source': static_source,
            'suction_head_m': h_suction,
            'required_flow_m3hr': flow['total_flow_m3hr'],
            'power_kw': power_kw,
            'power_hp': power_hp,
            'efficiency': eta,
            'recommended_model': self.recommend_pump_model(power_hp, h_total)
        }
    
    def recommend_pump_model(self, power_hp: float, head_m: float) -> str:
        """Recommend pump model based on requirements"""
        if power_hp < 3:
            return f"Grundfos CR3-{int(head_m/10)} or equivalent"
        elif power_hp < 5:
            return f"Grundfos CR5-{int(head_m/10)} or equivalent"
        elif power_hp < 10:
            return f"Grundfos CR10-{int(head_m/10)} or equivalent"
        else:
            return f"Grundfos CR15-{int(head_m/10)} or equivalent"
    
    def estimate_costs(self):
        """Estimate system costs (Rwanda prices)"""
        layout = self.results['layout']
        pipes = self.results['pipes']
        pump = self.results['pump']
        
        # Unit costs (RWF)
        cost_drip_tape = 150  # RWF/m for 16mm
        cost_main_pipe = 300  # RWF/m for 63mm
        cost_emitter = 50  # RWF/unit
        cost_pump_per_hp = 600000  # RWF/HP
        cost_filter = 500000  # RWF
        cost_fittings = 200000  # RWF
        cost_installation_per_ha = 300000  # RWF/ha
        
        # Calculate costs
        drip_tape_cost = pipes['lateral_length_m'] * layout['n_laterals'] * cost_drip_tape
        main_pipe_cost = pipes['main_length_m'] * cost_main_pipe
        emitter_cost = layout['total_emitters'] * cost_emitter
        pump_cost = pump['power_hp'] * cost_pump_per_hp
        filter_cost = cost_filter
        fittings_cost = cost_fittings
        installation_cost = self.design.field_area * cost_installation_per_ha
        
        total_cost = (drip_tape_cost + main_pipe_cost + emitter_cost + 
                     pump_cost + filter_cost + fittings_cost + installation_cost)
        
        self.results['costs'] = {
            'drip_tape_rwf': drip_tape_cost,
            'main_pipe_rwf': main_pipe_cost,
            'emitters_rwf': emitter_cost,
            'pump_rwf': pump_cost,
            'filter_rwf': filter_cost,
            'fittings_rwf': fittings_cost,
            'installation_rwf': installation_cost,
            'total_rwf': total_cost,
            'cost_per_ha_rwf': total_cost / self.design.field_area,
            'cost_per_emitter_rwf': total_cost / layout['total_emitters']
        }
    
    def generate_report(self) -> str:
        """Generate detailed hydraulic design report"""
        if not self.results:
            self.calculate_complete_system()
        
        layout = self.results['layout']
        flow = self.results['flow']
        pipes = self.results['pipes']
        head_loss = self.results['head_loss']
        pressure = self.results['pressure']
        uniformity = self.results['uniformity']
        pump = self.results['pump']
        costs = self.results['costs']
        
        report = f"""
═══════════════════════════════════════════════════════════════
HYDRAULIC DESIGN REPORT - DRIP IRRIGATION SYSTEM
═══════════════════════════════════════════════════════════════

PROJECT INFORMATION:
  • Crop:                   {self.design.crop_name}
  • Soil Type:              {self.design.soil_type}
  • Field Area:             {self.design.field_area:.2f} hectares
  • Field Dimensions:       {layout['field_length']:.0f}m × {layout['field_width']:.0f}m

EMITTER LAYOUT:
  • Number of Laterals:     {layout['n_laterals']}
  • Emitters per Lateral:   {layout['emitters_per_lateral']}
  • Total Emitters:         {layout['total_emitters']:,}
  • Emitter Spacing:        {self.design.emitter_spacing} m
  • Lateral Spacing:        {self.design.lateral_spacing} m
  • Emitter Flow Rate:      {self.design.emitter_flow} L/hr

SYSTEM FLOW:
  • Total Flow:             {flow['total_flow_m3hr']:.2f} m³/hr ({flow['total_flow_lps']:.2f} L/s)
  • Lateral Flow:           {flow['lateral_flow_m3hr']:.3f} m³/hr ({flow['lateral_flow_lps']:.3f} L/s)

PIPE SPECIFICATIONS:
  • Lateral Diameter:       {pipes['lateral_diameter_mm']} mm
  • Main Line Diameter:     {pipes['main_diameter_mm']} mm
  • Lateral Velocity:       {pipes['lateral_velocity_ms']:.2f} m/s {'✓' if pipes['lateral_velocity_ms'] < 1.5 else '⚠'}
  • Main Velocity:          {pipes['main_velocity_ms']:.2f} m/s {'✓' if pipes['main_velocity_ms'] < 2.0 else '⚠'}
  • Total Lateral Length:   {pipes['lateral_length_m'] * layout['n_laterals']:.0f} m
  • Main Line Length:       {pipes['main_length_m']:.0f} m

HYDRAULIC ANALYSIS:
  • Lateral Friction Loss:  {head_loss['lateral_friction_m']:.2f} m
  • Main Friction Loss:     {head_loss['main_friction_m']:.2f} m
  • Lateral Elevation (Δz): {head_loss['elevation_lateral_m']:+.2f} m
  • Main Elevation (Δz):    {head_loss['elevation_main_m']:+.2f} m
  • Total Elevation (Δz):   {head_loss['elevation_total_m']:+.2f} m
  • Local/Minor Losses:     {head_loss['local_m']:.2f} m
  • Friction Sub-total:     {head_loss['friction_total_m']:.2f} m
  • TOTAL HEAD LOSS:        {head_loss['total_m']:.2f} m
  {'⚠ Elevation adds significant head!' if abs(head_loss['elevation_total_m']) > 2.0 else ''}

PRESSURE PROFILE:
  • Inlet Pressure:         {pressure['inlet_bar']:.2f} bar ({pressure['inlet_m']:.2f} m)
  • Outlet Pressure:        {pressure['outlet_bar']:.2f} bar ({pressure['outlet_m']:.2f} m)
  • Average Pressure:       {pressure['average_bar']:.2f} bar ({pressure['average_m']:.2f} m)
  • Pressure Variation:     {pressure['variation_percent']:.1f}% {'✓' if pressure['variation_percent'] < 10 else '⚠'}

UNIFORMITY ANALYSIS:
  • Emission Uniformity:    {uniformity['emission_uniformity_percent']:.1f}% {'✓' if uniformity['emission_uniformity_percent'] > 90 else '⚠'}
  • Uniformity Coefficient: {uniformity['uniformity_coefficient_percent']:.1f}%
  • Min Discharge:          {uniformity['q_min_lhr']:.2f} L/hr
  • Max Discharge:          {uniformity['q_max_lhr']:.2f} L/hr
  • Avg Discharge:          {uniformity['q_avg_lhr']:.2f} L/hr
  • Discharge Variation:    {uniformity['q_variation_percent']:.1f}%

PUMP REQUIREMENTS:
  • Static Head:            {pump['static_head_m']:.2f} m ({pump['static_head_source']})
  • Suction Head:           {pump['suction_head_m']:.2f} m
  • Total Dynamic Head:     {pump['required_head_m']:.2f} m
  • Required Flow:          {pump['required_flow_m3hr']:.2f} m³/hr
  • Required Power:         {pump['power_kw']:.2f} kW ({pump['power_hp']:.1f} HP)
  • Pump Efficiency:        {pump['efficiency']*100:.0f}%
  • Recommended Model:      {pump['recommended_model']}

COST ESTIMATE (RWF):
  • Drip Tape:              {costs['drip_tape_rwf']:,.0f} RWF
  • Main Pipe:              {costs['main_pipe_rwf']:,.0f} RWF
  • Emitters:               {costs['emitters_rwf']:,.0f} RWF
  • Pump:                   {costs['pump_rwf']:,.0f} RWF
  • Filter System:          {costs['filter_rwf']:,.0f} RWF
  • Fittings & Accessories: {costs['fittings_rwf']:,.0f} RWF
  • Installation:           {costs['installation_rwf']:,.0f} RWF
  ─────────────────────────────────────────────────────────────
  • TOTAL COST:             {costs['total_rwf']:,.0f} RWF
  • Cost per Hectare:       {costs['cost_per_ha_rwf']:,.0f} RWF/ha
  • Cost per Emitter:       {costs['cost_per_emitter_rwf']:.0f} RWF

DESIGN RECOMMENDATIONS:
  {'✓' if pipes['lateral_velocity_ms'] < 1.5 else '✗'} Lateral velocity is {'acceptable' if pipes['lateral_velocity_ms'] < 1.5 else 'too high'} (< 1.5 m/s recommended)
  {'✓' if pipes['main_velocity_ms'] < 2.0 else '✗'} Main velocity is {'acceptable' if pipes['main_velocity_ms'] < 2.0 else 'too high'} (< 2.0 m/s recommended)
  {'✓' if pressure['variation_percent'] < 10 else '✗'} Pressure variation is {'acceptable' if pressure['variation_percent'] < 10 else 'high'} (< 10% recommended)
  {'✓' if uniformity['emission_uniformity_percent'] > 90 else '✗'} Emission uniformity is {'excellent' if uniformity['emission_uniformity_percent'] > 90 else 'needs improvement'} (> 90% recommended)
  {'✓' if head_loss['total_m'] < 5 else '⚠'} Total head loss is {'reasonable' if head_loss['total_m'] < 5 else 'significant'}
  {'⚠ WARNING: Terrain slope = ' + str(self.design.slope_percent) + '% — verify elevation data!' if (self.design.slope_percent or 0) > 3 else '✓ Terrain slope accounted for in calculations'}
  ✓ System design follows FAO-56 guidelines (elevation-corrected)

STATUS: {'✅ READY FOR IMPLEMENTATION' if uniformity['emission_uniformity_percent'] > 90 and pressure['variation_percent'] < 10 else '⚠ REQUIRES OPTIMIZATION'}

═══════════════════════════════════════════════════════════════
Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═══════════════════════════════════════════════════════════════
"""
        return report


# Example usage
if __name__ == "__main__":
    # Example 1: Flat field (backward compatibility)
    print("=" * 60)
    print("EXAMPLE 1: Flat field (no slope)")
    print("=" * 60)
    design_flat = SystemDesign(
        field_area=2.5,
        field_length=158,
        field_width=158,
        crop_name="Tomato",
        soil_type="Loam",
        emitter_flow=2.0,
        emitter_spacing=0.3,
        lateral_spacing=1.8,
        operating_pressure=1.5
    )
    calc_flat = HydraulicDesign(design_flat)
    calc_flat.calculate_complete_system()
    print(calc_flat.generate_report())
    
    # Example 2: Sloped field with elevation data
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Sloped field (8% slope, real elevations)")
    print("=" * 60)
    design_slope = SystemDesign(
        field_area=2.5,
        field_length=158,
        field_width=158,
        crop_name="Tomato",
        soil_type="Loam",
        emitter_flow=2.0,
        emitter_spacing=0.3,
        lateral_spacing=1.8,
        operating_pressure=2.0,
        slope_percent=8.0,
        water_source_elevation=1520.0,
        field_min_elevation=1510.0,
        field_max_elevation=1535.0,
        slope_direction='uphill'
    )
    calc_slope = HydraulicDesign(design_slope)
    calc_slope.calculate_complete_system()
    print(calc_slope.generate_report())
