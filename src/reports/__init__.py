# ============= src/reports/__init__.py =============
"""Report Generation and Export"""

from .export_utils import ExportUtils

# Optional PDF generation (requires reportlab)
try:
    from .pdf_generator import PDFReportGenerator
    PDF_AVAILABLE = True
except ImportError:
    PDFReportGenerator = None
    PDF_AVAILABLE = False

__all__ = [
    'PDFReportGenerator',
    'ExportUtils',
    'PDF_AVAILABLE'
]
