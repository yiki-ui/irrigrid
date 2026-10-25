#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive PDF Report Generator for Irrigation DSS

Generates detailed PDF reports including:
- 2D Field Layout Visualizations
- 3D Terrain Visualizations  
- Detailed Cost Breakdown Analysis
- Water Budget and Irrigation Schedule
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        PageBreak, Image, PageTemplate, Frame, KeepTogether
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class ReportValidationState:
    """Tracks validation state for report prerequisites"""
    
    def __init__(self):
        self.project_created = False
        self.location_selected = False
        self.field_traced = False
        self.climate_data_loaded = False
        self.crop_selected = False
        self.soil_selected = False
        self.water_req_calculated = False
        self.design_calculated = False
        self.terrain_loaded = False
    
    def is_report_ready(self) -> bool:
        """Check if all prerequisites are met for comprehensive report"""
        required_checks = [
            self.project_created,
            self.field_traced,
            self.water_req_calculated,
            self.design_calculated,
        ]
        return all(required_checks)
    
    def get_missing_steps(self) -> List[str]:
        """Return list of missing steps for report generation"""
        missing = []
        if not self.project_created:
            missing.append("Create a project in Step 1")
        if not self.field_traced:
            missing.append("Trace a field on the map in Step 2 (Location)")
        if not self.water_req_calculated:
            missing.append("Calculate water requirements in Step 7")
        if not self.design_calculated:
            missing.append("Run system design in Step 10 (Design System)")
        return missing


class PDFReportGenerator:
    """
    Comprehensive PDF report generator integrating 2D, 3D visuals and cost analysis.
    """
    
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.temp_dir = tempfile.gettempdir()
    
    def generate_comprehensive_report(
        self,
        output_file: str = None,
        include_2d: bool = True,
        include_3d: bool = True,
        include_cost_breakdown: bool = True
    ) -> Optional[str]:
        """
        Generate comprehensive PDF report with validation gating.
        
        Returns:
            Path to generated PDF or None if prerequisites not met
        """
        validation = self._check_prerequisites()
        
        if not validation.is_report_ready():
            return None, validation.get_missing_steps()
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.temp_dir, f'irrigation_report_{timestamp}.pdf')
        
        # Collect all data for the report
        report_data = self._collect_report_data()
        
        # Generate visuals
        image_paths = {}
        if include_2d and PLOTLY_AVAILABLE:
            image_paths['layout_2d'] = self._generate_2d_layout_image(report_data)
        if include_3d:
            image_paths['terrain_3d'] = self._generate_3d_terrain_image(report_data)
        
        # Build PDF
        self._build_pdf(output_file, report_data, image_paths)
        
        # Cleanup temp images
        self._cleanup_temp_images(image_paths)
        
        return output_file, []
    
    def _check_prerequisites(self) -> ReportValidationState:
        """Check if all prerequisites are met for report generation"""
        validation = ReportValidationState()
        
        if self.main_window is None:
            return validation
        
        # Check project creation
        validation.project_created = hasattr(self.main_window, 'current_project_name')
        
        # Check field traced
        validation.field_traced = (
            hasattr(self.main_window, '_field_polygon_coords') and
            self.main_window._field_polygon_coords and
            len(self.main_window._field_polygon_coords) >= 3
        )
        
        # Check climate data
        validation.climate_data_loaded = getattr(self.main_window, 'ai_climate_data_loaded', False)
        
        # Check crop selected
        validation.crop_selected = hasattr(self.main_window, 'current_crop')
        
        # Check soil selected
        validation.soil_selected = hasattr(self.main_window, 'current_soil')
        
        # Check water requirements calculated
        # Check if calculation_done flag is set (water calculator + successful calculation)
        validation.water_req_calculated = (
            hasattr(self.main_window, 'water_req_view') and
            getattr(self.main_window.water_req_view, 'calculation_done', False)
        )
        
        # Check design calculated
        validation.design_calculated = (
            hasattr(self.main_window, 'last_design_results') and
            self.main_window.last_design_results is not None
        )
        
        # Check terrain data
        validation.terrain_loaded = (
            hasattr(self.main_window, '_terrain_mesh') and
            self.main_window._terrain_mesh is not None
        )
        
        return validation
    
    def _collect_report_data(self) -> Dict[str, Any]:
        """Collect all necessary data for the report"""
        data = {
            'project_name': getattr(self.main_window, 'current_project_name', 'Untitled'),
            'location': {},
            'field': {},
            'climate': {},
            'water_budget': {},
            'schedule': [],
            'design': {},
            'costs': {},
            'economics': {},
        }
        
        # Location data
        if hasattr(self.main_window, 'current_location_data'):
            loc = self.main_window.current_location_data
            data['location'] = {
                'district': getattr(loc, 'district', 'Unknown'),
                'province': getattr(loc, 'province', 'Unknown'),
                'latitude': getattr(loc, 'latitude', 0),
                'longitude': getattr(loc, 'longitude', 0),
                'altitude': getattr(loc, 'altitude', 0),
            }
        
        # Field data
        data['field'] = {
            'area_ha': getattr(self.main_window, '_field_area_ha', 0),
            'polygon_coords': getattr(self.main_window, '_field_polygon_coords', []),
        }
        
        # Climate data
        data['climate'] = {
            'eto_monthly': getattr(self.main_window, 'auto_generated_eto', None),
        }
        
        # Water budget from last design
        if hasattr(self.main_window, 'last_design_results'):
            design = self.main_window.last_design_results
            data['water_budget'] = {
                'nir_m3': design.get('nir_m3', 0),
                'nir_mm': design.get('nir_mm', 0),
            }
            data['design'] = design
            data['costs'] = {
                'total': design.get('total_cost_rwf', 0),
                'per_hectare': design.get('total_cost_rwf', 0) / max(design.get('area_ha', 1), 1),
            }
        
        # Economic analysis
        if hasattr(self.main_window, 'econ_results'):
            # Parse from the text view (simplified)
            data['economics'] = self._parse_economic_data()
        
        return data
    
    def _generate_2d_layout_image(self, report_data: Dict) -> Optional[str]:
        """Generate 2D field layout image from Plotly chart"""
        try:
            from gui.field_layout_2d import build_layout_from_main_window
            
            if not self.main_window:
                return None
                
            # Get the exact layout figure used in the UI
            fig = build_layout_from_main_window(self.main_window, return_fig=True)
            
            # Save as image
            image_path = os.path.join(self.temp_dir, f'layout_2d_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')
            # Increase scale for high quality rendering in the PDF
            fig.write_image(image_path, scale=3, width=1000, height=800)
            return image_path
            
        except Exception as e:
            print(f"Warning: Could not generate 2D layout image: {e}")
            return None
    
    def _generate_3d_terrain_image(self, report_data: Dict) -> Optional[str]:
        """Generate 3D terrain visualization image"""
        try:
            # If pyvista widget isn't initialized yet (user hasn't visited 3D tab), initialize it now
            if not getattr(self.main_window, 'pyvista_widget', None):
                if hasattr(self.main_window, 'showEmbeddedPyVista'):
                    self.main_window.showEmbeddedPyVista()
                    
            # Get screenshot from PyVista
            if hasattr(self.main_window, 'pyvista_widget') and self.main_window.pyvista_widget:
                image_path = os.path.join(self.temp_dir, f'terrain_3d_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')
                self.main_window.pyvista_widget.screenshot(image_path)
                return image_path
                
        except Exception as e:
            print(f"Warning: Could not generate 3D terrain image: {e}")
        return None
    
    def _parse_economic_data(self) -> Dict:
        """Parse economic data from the UI"""
        # Simplified - in practice would parse from econ_results text
        return {
            'installation_cost': 'See Analysis tab',
            'annual_revenue': 'See Analysis tab',
            'payback_period': 'See Analysis tab',
            'roi': 'See Analysis tab',
        }
    
    def _build_pdf(
        self,
        output_file: str,
        report_data: Dict,
        image_paths: Dict[str, Optional[str]]
    ):
        """Build the comprehensive PDF document"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab not installed. Run: pip install reportlab")
        
        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Title style
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        
        heading_style = ParagraphStyle(
            'ReportHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2e5c8a'),
            spaceBefore=12,
            spaceAfter=8,
        )
        
        # Title
        story.append(Paragraph("IRRIGATION DSS - COMPREHENSIVE REPORT", title_style))
        story.append(Paragraph(f"{report_data['project_name']} — {datetime.now().strftime('%B %d, %Y')}", 
                             ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER)))
        story.append(Spacer(1, 0.3 * inch))
        
        # Section 1: Project Summary
        story.append(Paragraph("1. PROJECT SUMMARY", heading_style))
        
        location = report_data['location']
        field = report_data['field']
        
        summary_data = [
            ['District:', location.get('district', 'N/A')],
            ['Province:', location.get('province', 'N/A')],
            ['Coordinates:', f"{location.get('latitude', 0):.4f}°S, {location.get('longitude', 0):.4f}°E"],
            ['Altitude:', f"{location.get('altitude', 0)} m ASL"],
            ['Field Area:', f"{field.get('area_ha', 0):.4f} ha"],
        ]
        
        summary_table = Table(summary_data, colWidths=[1.5*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f4788')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # Section 2: 2D Field Layout
        if image_paths.get('layout_2d'):
            story.append(Paragraph("2. 2D FIELD LAYOUT", heading_style))
            story.append(Spacer(1, 0.1 * inch))
            
            img = Image(image_paths['layout_2d'], width=6*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.1 * inch))
            
            caption = Paragraph(
                "Figure 1: Field boundary and irrigation layout. Mainline (orange) runs along "
                "the field edge nearest the water source, with laterals extending perpendicular.",
                ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
            )
            story.append(caption)
            story.append(Spacer(1, 0.2 * inch))
        
        # Section 3: 3D Terrain Visualization
        if image_paths.get('terrain_3d'):
            story.append(Paragraph("3. 3D TERRAIN VISUALIZATION", heading_style))
            story.append(Spacer(1, 0.1 * inch))
            
            img = Image(image_paths['terrain_3d'], width=6*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.1 * inch))
            
            caption = Paragraph(
                "Figure 2: 3D terrain view showing field topography and irrigation infrastructure. "
                "Slope analysis enables pressure-aware design.",
                ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
            )
            story.append(caption)
            story.append(Spacer(1, 0.2 * inch))
        
        # Section 4: Water Budget
        story.append(Paragraph("4. WATER BUDGET ANALYSIS", heading_style))
        
        water = report_data['water_budget']
        water_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Net Irrigation Requirement', f"{water.get('nir_m3', 0):.0f}", 'm³'],
            ['Net Irrigation Requirement', f"{water.get('nir_mm', 0):.0f}", 'mm'],
            ['Field Area', f"{field.get('area_ha', 0):.4f}", 'ha'],
        ]
        
        if water.get('nir_m3', 0) <= 0:
            water_data.append(['Note', 'Rainfall sufficient - no supplemental irrigation required', ''])
        
        water_table = Table(water_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        water_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(water_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # Section 5: DETAILED COST BREAKDOWN
        story.append(Paragraph("5. DETAILED COST BREAKDOWN", heading_style))
        
        costs = report_data['costs']
        cost_data = [
            ['Component', 'Quantity', 'Unit', 'Unit Price (RWF)', 'Total (RWF)'],
        ]
        
        # Get actual BOM from design results if available
        if self.main_window and hasattr(self.main_window, 'last_design_results'):
            design = self.main_window.last_design_results
            if design.get('costs'):
                for item, cost in design['costs'].items():
                    if item != 'total_rwf':
                        cost_data.append([
                            item.replace('_', ' ').title(),
                            '1', 'set', f'{cost:,.0f}', f'{cost:,.0f}'
                        ])
        
        # Add totals
        total = costs.get('total', 0)
        cost_data.append(['', '', '', 'TOTAL →', f'{total:,.0f}'])
        
        cost_table = Table(cost_data, colWidths=[1.8*inch, 0.8*inch, 0.6*inch, 1.5*inch, 1.5*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(cost_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Cost interpretation
        cost_note = f"<b>Total System Cost:</b> {total:,.0f} RWF (~${total/1000:.0f} USD)<br/>"
        if water.get('nir_m3', 0) > 0:
            cost_per_m3 = total / water['nir_m3']
            cost_note += f"<b>Cost per cubic meter:</b> {cost_per_m3:,.0f} RWF/m³"
        
        story.append(Paragraph(cost_note, styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Section 6: System Specifications
        story.append(Paragraph("6. SYSTEM SPECIFICATIONS", heading_style))
        
        design = report_data.get('design', {})
        specs_data = [
            ['Specification', 'Value'],
            ['System Uniformity (EU)', f"{design.get('achieved_eu', 0):.1f}%"],
            ['System Flow Rate', f"{design.get('system_flow_rate', 0):.2f} L/hr"],
            ['Operating Pressure', f"{design.get('operating_pressure', 0):.2f} bar"],
            ['Mainline Diameter', f"{design.get('pipe_diameters', {}).get('main', 0):.0f} mm"],
            ['Lateral Diameter', f"{design.get('pipe_diameters', {}).get('lateral', 0):.0f} mm"],
        ]
        
        specs_table = Table(specs_data, colWidths=[2*inch, 4*inch])
        specs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8f0f8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(specs_table)
        
        # Build PDF
        doc.build(story)
    
    def _cleanup_temp_images(self, image_paths: Dict[str, Optional[str]]):
        """Remove temporary image files"""
        for path in image_paths.values():
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass


def generate_report_from_main_window(main_window, output_file=None) -> tuple:
    """
    Convenience function to generate report from main window.
    
    Returns:
        (output_file_path, missing_steps) tuple
        output_file_path is None if prerequisites not met
    """
    generator = PDFReportGenerator(main_window)
    return generator.generate_comprehensive_report(output_file=output_file)