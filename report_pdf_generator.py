"""
Report PDF Generator
Creates modern, well-formatted PDF reports from Jira data.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger('ReportPDFGenerator')

class ReportPDFGenerator:
    """
    Generates modern PDF reports from Jira report data.
    """
    
    def __init__(self):
        """Initialize PDF generator with modern styling."""
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e'),
            alignment=TA_LEFT
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50')
        )
    
    def generate_pdf(self, report_data: Dict, output_path: str):
        """
        Generate PDF report from report data.
        
        Args:
            report_data (Dict): Report data from ReportGenerator
            output_path (str): Output PDF file path
        """
        logger.info(f"📄 Generating PDF report: {report_data.get('title', 'Report')}")
        
        # Use landscape orientation for better table display
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        # Build PDF content
        story = []
        
        # Title
        title = Paragraph(report_data.get('title', 'Jira Report'), self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Report info
        info_data = [
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Total Issues:', str(report_data.get('total_issues', 0))],
            ['JQL Query:', report_data.get('query', 'N/A')]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 6*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Data table
        if report_data.get('rows'):
            # Prepare table data
            headers = report_data.get('headers', [])
            rows = report_data.get('rows', [])
            
            # Create table data with headers
            table_data = [headers] + rows
            
            # Calculate column widths based on content
            col_widths = self._calculate_column_widths(table_data, landscape(A4)[0] - 1*inch)
            
            # Create table
            data_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Apply modern table styling
            table_style = TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data rows styling
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                
                # Grid and padding
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            
            data_table.setStyle(table_style)
            story.append(data_table)
        else:
            # No data message
            no_data = Paragraph("No data found for the specified query.", self.normal_style)
            story.append(no_data)
        
        # Build PDF
        doc.build(story)
        logger.info(f"✅ PDF report generated successfully: {output_path}")
    
    def _calculate_column_widths(self, table_data: List[List[str]], available_width: float) -> List[float]:
        """
        Calculate optimal column widths based on content.
        
        Args:
            table_data (List[List[str]]): Table data including headers
            available_width (float): Available width for table
            
        Returns:
            List[float]: Column widths
        """
        if not table_data or not table_data[0]:
            return []
        
        num_cols = len(table_data[0])
        
        # Calculate relative widths based on content length
        col_weights = []
        for col_idx in range(num_cols):
            max_length = 0
            for row in table_data:
                if col_idx < len(row):
                    content_length = len(str(row[col_idx]))
                    max_length = max(max_length, content_length)
            col_weights.append(max(max_length, 10))  # Minimum weight of 10
        
        # Convert to actual widths
        total_weight = sum(col_weights)
        col_widths = [(weight / total_weight) * available_width for weight in col_weights]
        
        return col_widths