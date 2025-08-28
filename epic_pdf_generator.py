"""
Epic PDF Report Generator
Creates comprehensive PDF reports for Epic analysis.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from io import BytesIO
from datetime import datetime
import logging

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('EpicPDFGenerator')

class PDFReportGenerator:
    """Generates PDF reports for Epic analysis."""
    
    def __init__(self, jira_url=''):
        """Initialize the PDF generator with styles."""
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.jira_url = jira_url.rstrip('/')
        
    def add_title(self, title):
        """Add a title to the report."""
        self.elements.append(Spacer(1, 12))
        self.elements.append(Paragraph(title, self.styles['Title']))
        self.elements.append(Spacer(1, 12))
        
    def add_timestamp(self):
        """Add timestamp to the report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.elements.append(Paragraph(f"Generated on: {timestamp}", self.styles['Normal']))
        self.elements.append(Spacer(1, 12))
        
    def add_heading(self, text):
        """Add a heading to the report."""
        self.elements.append(Spacer(1, 12))
        self.elements.append(Paragraph(text, self.styles['Heading1']))
        self.elements.append(Spacer(1, 6))
        
    def add_image(self, image_data, caption=None, height=4*inch):
        """Add an image to the report."""
        img = Image(image_data, width=6*inch, height=height)
        self.elements.append(img)
        if caption:
            self.elements.append(Paragraph(caption, self.styles['Italic']))
        self.elements.append(Spacer(1, 12))
        
    def add_epic_details(self, epic):
        """Add compact epic details with child info inline."""
        # Create epic link if jira_url available
        epic_key = epic['key']
        if self.jira_url:
            epic_link = f'<a href="{self.jira_url}/browse/{epic_key}">{epic_key}</a>'
        else:
            epic_link = epic_key
            
        # Truncate summary
        summary = epic['summary'][:40] + '...' if len(epic['summary']) > 40 else epic['summary']
        
        # Create child summary (first 3 children)
        child_summary = ''
        if epic['children']:
            child_keys = []
            for child in epic['children'][:3]:
                if self.jira_url:
                    child_link = f'<a href="{self.jira_url}/browse/{child["key"]}">{child["key"]}</a>'
                else:
                    child_link = child['key']
                child_keys.append(child_link)
            
            child_summary = ', '.join(child_keys)
            if len(epic['children']) > 3:
                child_summary += f' (+{len(epic["children"]) - 3} more)'
        
        # Compact table with epic and child info
        data = [
            [Paragraph(f'<b>{epic_link}</b>', self.styles['Normal']), 
             summary, 
             epic['status'],
             f"{epic['original_estimate']:.0f}h",
             f"{epic['remaining_estimate']:.0f}h",
             f"{epic['progress']:.0f}%"],
            [Paragraph('<i>Children:</i>', self.styles['Normal']), 
             Paragraph(child_summary, self.styles['Normal']) if child_summary else 'None',
             f"{epic['num_children']} items",
             '', '', '']
        ]
        
        t = Table(data, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 0.6*inch, 0.6*inch, 0.5*inch])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightyellow),
            ('PADDING', (0, 0), (-1, -1), 3),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        self.elements.append(t)
        self.elements.append(Spacer(1, 6))
        
    def _add_banner(self):
        """Add banner to the report."""
        banner_style = ParagraphStyle(
            'Banner',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=colors.white,
            alignment=1,  # Center
            spaceAfter=15
        )
        
        # Create banner table
        banner_data = [[Paragraph('Jira Obeya Epic Analysis', banner_style)]]
        banner_table = Table(banner_data, colWidths=[6.5*inch], rowHeights=[0.8*inch])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.28, 0.74, 0.54)),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        self.elements.insert(0, banner_table)
        self.elements.insert(1, Spacer(1, 20))
    
    def generate_pdf(self):
        """
        Generate the PDF report with custom page template.
        
        Returns:
            BytesIO: PDF file buffer
        """
        buffer = BytesIO()
        
        # Add banner
        self._add_banner()
        
        # Create custom document with footer and metadata
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=90,
            author="Pietro Maffi",
            title="Jira Obeya Epic Analysis Report"
        )
        
        # Create frame and page template
        frame = Frame(
            doc.leftMargin, doc.bottomMargin + 20,
            doc.width, doc.height - 20,
            id='normal'
        )
        
        template = PageTemplate(id='main', frames=frame, onPage=self._add_footer)
        doc.addPageTemplates([template])
        
        # Build the PDF
        doc.build(self.elements)
        
        # Reset the buffer position
        buffer.seek(0)
        return buffer
    
    def _add_footer(self, canvas, doc):
        """Add footer with app name, copyright, and page number."""
        canvas.saveState()
        
        # Footer text
        footer_text = "Obeya Epic Analysis - Copyright Pietro Maffi 2025"
        canvas.setFont('Helvetica', 9)
        canvas.drawString(doc.leftMargin, 30, footer_text)
        
        # Page number
        page_num = f"Page {canvas.getPageNumber()}"
        canvas.drawRightString(doc.width + doc.leftMargin, 30, page_num)
        
        canvas.restoreState()
