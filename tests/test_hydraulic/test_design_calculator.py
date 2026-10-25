#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Hydraulic Design Calculator.
Validates elevation-aware head loss, pump sizing, and pressure variation.
"""
import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.hydraulic.design_calculator import HydraulicDesign, SystemDesign


class TestFlatField(unittest.TestCase):
    """Tests on a flat field (backward compatibility — no elevation)."""

    def setUp(self):
        self.design = SystemDesign(
            field_area=1.0,
            field_length=100,
            field_width=100,
            crop_name="Tomato",
            soil_type="Loam",
            emitter_flow=2.0,
            emitter_spacing=0.3,
            lateral_spacing=1.2,
            operating_pressure=1.5,
            slope_percent=0.0,
        )
        self.calc = HydraulicDesign(self.design)
        self.results = self.calc.calculate_complete_system()

    def test_elevation_components_are_zero(self):
        """Flat field → Δz contributions must be zero."""
        hl = self.results['head_loss']
        self.assertAlmostEqual(hl['elevation_lateral_m'], 0.0, places=3)
        self.assertAlmostEqual(hl['elevation_main_m'], 0.0, places=3)
        self.assertAlmostEqual(hl['elevation_total_m'], 0.0, places=3)

    def test_total_head_loss_equals_friction_plus_local(self):
        hl = self.results['head_loss']
        expected = hl['friction_total_m'] + hl['local_m']
        self.assertAlmostEqual(hl['total_m'], expected, places=5)

    def test_pump_static_head_zero_on_flat(self):
        """Flat field with no elevation data → static head = 0."""
        pump = self.results['pump']
        self.assertAlmostEqual(pump['static_head_m'], 0.0, places=3)
        self.assertEqual(pump['static_head_source'], 'estimated from slope')

    def test_emission_uniformity_positive(self):
        eu = self.results['uniformity']['emission_uniformity_percent']
        self.assertGreater(eu, 0)
        self.assertLessEqual(eu, 100)

    def test_report_generates(self):
        report = self.calc.generate_report()
        self.assertIn('HYDRAULIC DESIGN REPORT', report)
        self.assertIn('elevation-corrected', report)


class TestSlopedField(unittest.TestCase):
    """Tests on a sloped field with elevation data."""

    def setUp(self):
        self.design = SystemDesign(
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
            slope_direction='uphill',
        )
        self.calc = HydraulicDesign(self.design)
        self.results = self.calc.calculate_complete_system()

    def test_elevation_head_nonzero(self):
        hl = self.results['head_loss']
        self.assertNotAlmostEqual(hl['elevation_total_m'], 0.0, places=1)

    def test_uphill_increases_head_loss(self):
        """Uphill Δz should increase total head loss beyond friction alone."""
        hl = self.results['head_loss']
        self.assertGreater(hl['total_m'], hl['friction_total_m'] + hl['local_m'])

    def test_real_static_head_used(self):
        """When elevation data is provided, static head = max_field - source."""
        pump = self.results['pump']
        expected_static = 1535.0 - 1520.0  # = 15 m
        self.assertAlmostEqual(pump['static_head_m'], expected_static, places=1)
        self.assertEqual(pump['static_head_source'], 'measured')

    def test_report_mentions_elevation(self):
        report = self.calc.generate_report()
        self.assertIn('Elevation', report)
        self.assertIn('Δz', report)

    def test_pressure_variation_higher_on_slope(self):
        """Pressure variation on a steep slope should be higher than flat."""
        # Use a small field to avoid saturation at 100%
        sloped = SystemDesign(
            field_area=0.5, field_length=70, field_width=70,
            emitter_flow=2.0, emitter_spacing=0.3, lateral_spacing=1.8,
            operating_pressure=2.0, slope_percent=8.0,
            slope_direction='uphill',
        )
        flat_design = SystemDesign(
            field_area=0.5, field_length=70, field_width=70,
            emitter_flow=2.0, emitter_spacing=0.3, lateral_spacing=1.8,
            operating_pressure=2.0, slope_percent=0.0,
        )
        sloped_results = HydraulicDesign(sloped).calculate_complete_system()
        flat_results = HydraulicDesign(flat_design).calculate_complete_system()

        # Sloped uphill should have worse (higher) pressure variation
        self.assertGreater(
            sloped_results['pressure']['variation_percent'],
            flat_results['pressure']['variation_percent']
        )


class TestSlopeFallbackEstimation(unittest.TestCase):
    """Tests when slope is given but no elevation data (fallback path)."""

    def setUp(self):
        self.design = SystemDesign(
            field_area=1.0,
            field_length=100,
            field_width=100,
            emitter_flow=2.0,
            emitter_spacing=0.3,
            lateral_spacing=1.2,
            operating_pressure=1.5,
            slope_percent=5.0,
            # No water_source_elevation or field_max_elevation
        )
        self.calc = HydraulicDesign(self.design)
        self.results = self.calc.calculate_complete_system()

    def test_static_head_estimated_from_slope(self):
        pump = self.results['pump']
        self.assertEqual(pump['static_head_source'], 'estimated from slope')
        # 5% slope × (100 + 100) m = 10 m
        self.assertAlmostEqual(pump['static_head_m'], 10.0, places=1)


class TestDownhillField(unittest.TestCase):
    """Tests for downhill layout where gravity assists flow."""

    def setUp(self):
        self.uphill = SystemDesign(
            field_area=1.0, field_length=100, field_width=100,
            emitter_flow=2.0, emitter_spacing=0.3, lateral_spacing=1.2,
            operating_pressure=1.5, slope_percent=5.0,
            slope_direction='uphill',
        )
        self.downhill = SystemDesign(
            field_area=1.0, field_length=100, field_width=100,
            emitter_flow=2.0, emitter_spacing=0.3, lateral_spacing=1.2,
            operating_pressure=1.5, slope_percent=5.0,
            slope_direction='downhill',
        )

    def test_downhill_has_less_head_loss_than_uphill(self):
        up_calc = HydraulicDesign(self.uphill)
        up_results = up_calc.calculate_complete_system()

        down_calc = HydraulicDesign(self.downhill)
        down_results = down_calc.calculate_complete_system()

        self.assertLess(
            down_results['head_loss']['total_m'],
            up_results['head_loss']['total_m'],
            "Downhill layout should have less total head loss than uphill"
        )


class TestPumpSizingSanity(unittest.TestCase):
    """Pump sizing sanity checks."""

    def test_larger_field_needs_bigger_pump(self):
        small = SystemDesign(
            field_area=0.5, field_length=70, field_width=70,
            emitter_flow=2.0, emitter_spacing=0.3, lateral_spacing=1.2,
            operating_pressure=1.5,
        )
        large = SystemDesign(
            field_area=2.0, field_length=141, field_width=141,
            emitter_flow=2.0, emitter_spacing=0.3, lateral_spacing=1.2,
            operating_pressure=1.5,
        )
        small_r = HydraulicDesign(small).calculate_complete_system()
        large_r = HydraulicDesign(large).calculate_complete_system()

        self.assertGreater(large_r['pump']['power_hp'], small_r['pump']['power_hp'])


if __name__ == '__main__':
    unittest.main()
