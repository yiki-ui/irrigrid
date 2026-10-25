#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriDSS MVP PDF Report Generator
Simple, focused PDF output for farmer
"""

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  reportlab not installed. Install with: pip install reportlab")

from datetime import datetime

def generate_mvp_report(
    crop_name='Tomato',
    area_ha=0.25,
    location='Musanze, Rwanda',
    et0_seasonal_mm=282,
    cwr_m3=705,
    nir_m3=0,
    schedule=None,
    bom=None,
    total_cost_rwf=0,
    output_file='irrigation_design_report.pdf',
    layout_image_path=None
):
    """
    Generate professional PDF report for farmer
    
    Args:
        crop_name: Crop type
        area_ha: Field area (hectares)
        location: Field location
        et0_seasonal_mm: Reference ET₀ (mm)
        cwr_m3: Crop water requirement (m³)
        nir_m3: Net irrigation requirement (m³)
        schedule: List of irrigation events
        bom: Bill of materials list
        total_cost_rwf: Total system cost (RWF)
        output_file: Output PDF filename
        layout_image_path: Path to the matplotlib layout image
    
    Returns:
        Path to generated PDF
    """
    
    if not REPORTLAB_AVAILABLE:
        print("ERROR: reportlab required for PDF generation")
        return None
    
    # Create PDF document
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2e5c8a'),
        spaceAfter=10,
        spaceBefore=10,
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # HEADER / TITLE
    # ─────────────────────────────────────────────────────────────────────────
    
    title = Paragraph("IrriDSS Irrigation System Design Report", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))
    
    # Date and reference
    ref_text = f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')} | <b>Location:</b> {location}"
    story.append(Paragraph(ref_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1: PROJECT SUMMARY
    # ─────────────────────────────────────────────────────────────────────────
    
    story.append(Paragraph("1. PROJECT SUMMARY", heading2_style))
    
    summary_data = [
        ['Field Location:', location],
        ['Crop:', crop_name],
        ['Field Area:', f'{area_ha} hectares ({area_ha*10000:.0f} m²)'],
        ['Growing Season:', 'December - March (120 days)'],
        ['Soil Type:', 'Volcanic Clay Loam'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.2 * inch))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2: WATER BUDGET
    # ─────────────────────────────────────────────────────────────────────────
    
    story.append(Paragraph("2. WATER BUDGET ANALYSIS", heading2_style))
    
    water_budget_data = [
        ['Parameter', 'Amount', 'Notes'],
        ['Reference ET₀', f'{et0_seasonal_mm:.0f} mm', 'FAO-56 Penman-Monteith'],
        ['Crop Water Requirement (CWR)', f'{cwr_m3:.0f} m³', f'{(cwr_m3/(area_ha*10000))*1000:.0f} mm depth'],
        ['Seasonal Rainfall', '500 mm', 'Dec-Mar historical'],
        ['Effective Rainfall (75%)', '375 mm', f'{(375/1000)*(area_ha*10000):.0f} m³'],
        ['NET IRRIGATION REQUIRED', f'{nir_m3:.0f} m³', 'CWR - Effective RF'],
    ]
    
    water_table = Table(water_budget_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
    water_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    
    story.append(water_table)
    
    # Add interpretation
    if nir_m3 <= 0:
        interpretation = "<i>✓ Good news: Rainfall is sufficient for this season. Drip system can be used for future dry seasons or other crops.</i>"
    else:
        interpretation = f"<i>The system needs to deliver {nir_m3:.0f} m³ of water distributed over the season.</i>"
    
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(interpretation, styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3: IRRIGATION SCHEDULE
    # ─────────────────────────────────────────────────────────────────────────
    
    if schedule and len(schedule) > 0 and schedule[0].get('amount_m3', 0) > 0:
        story.append(Paragraph("3. IRRIGATION SCHEDULE", heading2_style))
        
        schedule_data = [
            ['Date', 'Amount (mm)', 'Volume (m³)', 'Hours @ 2 LPS', 'Notes']
        ]
        
        for event in schedule:
            date = event.get('date', 'TBD')
            amount_mm = event.get('amount_mm', 0)
            amount_m3 = event.get('amount_m3', 0)
            hours = amount_m3 / 0.0072 / 3600  # Rough: 6 L/s = 0.006 m³/s
            notes = event.get('reason', 'Mid-growth')
            
            schedule_data.append([
                date,
                f'{amount_mm:.0f}',
                f'{amount_m3:.0f}',
                f'{hours:.1f}',
                notes
            ])
        
        schedule_table = Table(schedule_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        schedule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        
        story.append(schedule_table)
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            "<i>Print this schedule and post on your farm. Mark dates on calendar. Check soil moisture before each date.</i>",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2 * inch))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4: BILL OF MATERIALS
    # ─────────────────────────────────────────────────────────────────────────
    
    if bom:
        story.append(Paragraph("4. BILL OF MATERIALS (What to Buy)", heading2_style))
        
        bom_data = [
            ['Item', 'Quantity', 'Unit', 'Unit Price (RWF)', 'Total (RWF)']
        ]
        
        for item in bom:
            bom_data.append([
                item['item'],
                f"{item['quantity']:.0f}" if isinstance(item['quantity'], float) else str(item['quantity']),
                item['unit'],
                f"{item['unit_price_rwf']:,.0f}",
                f"{item['total_rwf']:,.0f}",
            ])
        
        # Add total row
        bom_data.append([
            '',
            '',
            '',
            'TOTAL →',
            f'{total_cost_rwf:,.0f}'
        ])
        
        bom_table = Table(bom_data, colWidths=[2.2*inch, 1*inch, 0.8*inch, 1.5*inch, 1.5*inch])
        bom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        
        story.append(bom_table)
        story.append(Spacer(1, 0.1 * inch))
        
        cost_per_m3 = total_cost_rwf / max(nir_m3, 1) if nir_m3 > 0 else 0
        cost_note = f"<b>Total Cost: {total_cost_rwf:,.0f} RWF</b> (~${total_cost_rwf/1000:.0f} USD)<br/>"
        if nir_m3 > 0:
            cost_note += f"Cost per m³ of water: {cost_per_m3:,.0f} RWF"
        
        story.append(Paragraph(cost_note, styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5: SYSTEM SPECIFICATIONS
    # ─────────────────────────────────────────────────────────────────────────
    
    story.append(Paragraph("5. SYSTEM SPECIFICATIONS", heading2_style))
    
    specs_data = [
        ['Specification', 'Value'],
        ['Emitter Type', 'Drip irrigation (1.5 L/h)'],
        ['Emitter Spacing', '0.4 m along rows'],
        ['Total Emitters', '~8,875 units'],
        ['Mainline Diameter', 'PE 20mm'],
        ['Lateral Diameter', 'PE 13mm'],
        ['Operating Pressure', '25 kPa'],
        ['Daily Operating Hours', '6 hours'],
        ['Pump Type', 'Solar (preferred) or Diesel'],
    ]
    
    specs_table = Table(specs_data, colWidths=[2.5*inch, 4*inch])
    specs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e8f0f8')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    
    story.append(specs_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # ─────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────────────────────
    
    footer_text = (
        "<b>Next Steps:</b><br/>"
        "1. Show this report to an agricultural extension officer for verification<br/>"
        "2. Visit local agrodealers with Bill of Materials to get quotes<br/>"
        "3. Hire a technician familiar with drip irrigation installation<br/>"
        "4. Prepare water source (borehole, tank, river)<br/>"
        "5. Install system and test before planting<br/>"
        "<br/>"
        "<i>For questions: Contact your local agricultural extension office or visit an agro-dealer.</i><br/>"
        f"<i>Report generated by IrriDSS {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"
    )
    
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 6: 2D FIELD LAYOUT DRAWING
    # ─────────────────────────────────────────────────────────────────────────
    if layout_image_path:
        import os
        if os.path.exists(layout_image_path):
            story.append(PageBreak())
            story.append(Paragraph("6. TECHNICAL FIELD LAYOUT", heading2_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # Add image, keeping aspect ratio (usually 6x5 from matplotlib)
            img = Image(layout_image_path, width=7.0*inch, height=5.8*inch)
            story.append(img)
            
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(
                "<i>This diagram shows the recommended layout for the mainline and lateral pipes based on field dimensions. "
                "Emitters and laterals shown are a representative sample.</i>", 
                styles['Normal']
            ))

    # Build PDF
    try:
        doc.build(story)
        print(f"✓ PDF Report generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        return None

if __name__ == '__main__':
    # Test generation
    from core_test_data import (
        BILL_OF_MATERIALS, IRRIGATION_SCHEDULE, 
        WATER_BUDGET, TOTAL_COST_RWF
    )
    from mvp_calculation_api import run_musanze_design
    
    print("Generating test report...")
    generate_mvp_report(
        crop_name='Tomato',
        area_ha=0.25,
        location='Musanze, Northern Province, Rwanda',
        et0_seasonal_mm=282,
        cwr_m3=705,
        nir_m3=WATER_BUDGET.get('nir_m3', 0),
        schedule=IRRIGATION_SCHEDULE,
        bom=BILL_OF_MATERIALS,
        total_cost_rwf=TOTAL_COST_RWF,
        output_file='test_report.pdf'
    )
