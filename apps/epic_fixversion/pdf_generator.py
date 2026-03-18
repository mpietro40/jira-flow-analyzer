"""
Epic Distribution Analysis PDF Report Generator
Generates professional PDF reports for epic distribution analysis
"""

from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, PageTemplate, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
import logging
import html

logger = logging.getLogger('EpicFixVersionPDFGenerator')

class EpicFixVersionPDFGenerator:
    """Generates PDF reports for epic distribution analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.page_num = 0
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='InitiativeHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=10,
            spaceBefore=10,
            leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='TOCEntry',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=6
        ))
    
    def generate_report(self, analysis_data: dict, output_path: str = None, jira_url: str = None) -> io.BytesIO:
        """
        Generate PDF report from analysis data
        
        Args:
            analysis_data: Analysis results dictionary
            output_path: Optional file path to save PDF
            jira_url: Jira base URL for creating links
            
        Returns:
            BytesIO buffer containing PDF
        """
        self.jira_url = jira_url
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer if not output_path else output_path,
            pagesize=landscape(letter),
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Add page number footer
        doc.build = self._build_with_page_numbers(doc)
        
        story = []
        
        # Title
        title = Paragraph("Epic Distribution Analysis Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Metadata - access data directly
        timestamp = analysis_data.get('timestamp', datetime.now().isoformat())
        fix_version = analysis_data.get('fix_version', 'All')
        excluded_statuses = analysis_data.get('excluded_statuses', [])
        
        metadata = [
            ['Report Generated:', datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')],
            ['Fix Version Filter:', fix_version],
            ['Excluded Statuses:', ', '.join(excluded_statuses) if excluded_statuses else 'None'],
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary Statistics
        story.append(Paragraph("Summary Statistics", self.styles['SectionHeader']))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Initiatives Scanned', str(analysis_data.get('total_initiatives', 0))],
            ['Initiatives with Epics', str(analysis_data.get('initiatives_with_epics', 0))],
            ['Total Epics Found', str(analysis_data.get('total_epics', 0))],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.4*inch))
        
        # Table of Contents
        story.append(Paragraph("Table of Contents", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        initiative_results = analysis_data.get('results', [])
        
        if initiative_results:
            for idx, initiative in enumerate(initiative_results, 1):
                toc_entry = f"{idx}. {initiative['initiative_key']}: {initiative['initiative_summary'][:80]}"
                story.append(Paragraph(toc_entry, self.styles['TOCEntry']))
        
        story.append(PageBreak())
        
        # Epic Details by Initiative
        story.append(Paragraph("Epic Details by Initiative", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        if not initiative_results:
            story.append(Paragraph("No epics found.", self.styles['Normal']))
        else:
            for initiative in initiative_results:
                # Initiative header with styling
                init_header = f"{initiative['initiative_key']}: {initiative['initiative_summary']}"
                story.append(Paragraph(init_header, self.styles['InitiativeHeader']))
                story.append(Spacer(1, 0.1*inch))
                
                # Create table for all epics in this initiative
                story.append(self._create_epics_table(initiative['epics']))
                story.append(Spacer(1, 0.3*inch))
        
        # Build PDF with page numbers
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        if not output_path:
            buffer.seek(0)
            return buffer
        
        return None
    
    def _build_with_page_numbers(self, doc):
        """Wrapper to add page numbers to build method"""
        original_build = doc.build
        def build_wrapper(story, **kwargs):
            kwargs['onFirstPage'] = self._add_page_number
            kwargs['onLaterPages'] = self._add_page_number
            return original_build(story, **kwargs)
        return build_wrapper
    
    def _add_page_number(self, canvas, doc):
        """Add page number to bottom right of each page"""
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(10.5*inch, 0.5*inch, text)
        canvas.restoreState()
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text for PDF by escaping HTML/XML characters"""
        if not text:
            return 'N/A'
        return html.escape(str(text))
    
    def _create_epics_table(self, epics: list) -> Table:
        """Create table with all epics (one row per epic)"""
        # Table header
        data = [[
            Paragraph('<b>Epic Key</b>', self.styles['Normal']),
            Paragraph('<b>Summary</b>', self.styles['Normal']),
            Paragraph('<b>Status</b>', self.styles['Normal']),
            Paragraph('<b>Magnitude</b>', self.styles['Normal']),
            Paragraph('<b>Who asked</b>', self.styles['Normal']),
            Paragraph('<b>CPO-APO</b>', self.styles['Normal']),
            Paragraph('<b>Start date</b>', self.styles['Normal']),
            Paragraph('<b>Fix Ver</b>', self.styles['Normal']),
            Paragraph('<b>What to deliver</b>', self.styles['Normal']),
            Paragraph('<b>Comments</b>', self.styles['Normal'])
        ]]
        
        # Add epic rows
        for epic in epics:
            # Create clickable link
            epic_key = epic['key']
            if self.jira_url:
                epic_link = f'<link href="{self.jira_url}/browse/{epic_key}" color="blue"><u>{epic_key}</u></link>'
            else:
                epic_link = self._sanitize_text(epic_key)
            
            # Combine comments
            comments = epic.get('comments', {})
            combined_comments = []
            if comments.get('platform'):
                combined_comments.append(f"Platform: {self._sanitize_text(comments['platform'][:100])}")
            if comments.get('impacts'):
                combined_comments.append(f"Impacts: {self._sanitize_text(comments['impacts'][:100])}")
            comments_text = ' | '.join(combined_comments) if combined_comments else 'N/A'
            
            row = [
                Paragraph(epic_link, self.styles['Normal']),
                Paragraph(self._sanitize_text(epic.get('summary', 'N/A')), self.styles['Normal']),
                Paragraph(self._sanitize_text(epic.get('status', 'N/A')), self.styles['Normal']),
                Paragraph(self._sanitize_text(epic.get('complexity', 'N/A')), self.styles['Normal']),
                Paragraph(self._sanitize_text(epic.get('requesting_customer', 'N/A')), self.styles['Normal']),
                Paragraph(self._sanitize_text(epic.get('assignee', 'Unassigned')), self.styles['Normal']),
                Paragraph(self._sanitize_text(epic.get('target_start', 'N/A')), self.styles['Normal']),
                Paragraph(self._sanitize_text(', '.join(epic.get('fix_versions', [])) or 'None'), self.styles['Normal']),
                Paragraph(self._sanitize_text(epic.get('solution', 'N/A')), self.styles['Normal']),
                Paragraph(comments_text, self.styles['Normal'])
            ]
            data.append(row)
        
        # Column widths for landscape letter (11 inches - margins) - Project column removed
        table = Table(data, colWidths=[0.7*inch, 1.3*inch, 0.6*inch, 0.7*inch, 1.0*inch, 0.9*inch, 0.7*inch, 0.7*inch, 1.3*inch, 1.6*inch], repeatRows=1)
        
        # Build style with alternating row colors
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d4c5f9')),  # Light purple header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]
        
        # Add alternating row colors (light yellow and white)
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fffacd')))  # Light yellow
            else:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
        
        table.setStyle(TableStyle(style))
        
        return table
