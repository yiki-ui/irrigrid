# ============= src/reports/pdf_generator.py =============
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from datetime import datetime
from typing import List

class PDFReportGenerator:
    """Generate comprehensive PDF reports"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.doc = SimpleDocTemplate(filename, pagesize=A4)
        self.styles = getSampleStyleSheet()
        self.elements = []
        
    def add_title(self, text: str):
        """Add report title"""
        title = Paragraph(text, self.styles['Title'])
        self.elements.append(title)
        self.elements.append(Spacer(1, 20))
        
    def add_section(self, heading: str, content: str):
        """Add section with heading and content"""
        h = Paragraph(heading, self.styles['Heading2'])
        p = Paragraph(content, self.styles['Normal'])
        self.elements.append(h)
        self.elements.append(Spacer(1, 10))
        self.elements.append(p)
        self.elements.append(Spacer(1, 15))
        
    def add_table(self, data: List[List], col_widths: List = None):
        """Add table to report"""
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        self.elements.append(table)
        self.elements.append(Spacer(1, 15))
        
    def build(self):
        """Generate PDF file"""
        self.doc.build(self.elements)
