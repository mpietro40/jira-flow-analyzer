"""
PDF Report Generator
Creates comprehensive PDF reports for Jira analytics.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.tableofcontents import TableOfContents
from datetime import datetime
import io
import base64
import logging
from typing import Dict

# Configure logger with proper name
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JiraPDFGenerator')

class NumberedCanvas:
    """Custom canvas for adding page numbers and footer."""
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc
    
    def draw_page_number_and_footer(self):
        """Draw page number and footer on each page."""
        page_num = self.canvas.getPageNumber()
        
        # Page number (bottom right)
        page_text = f"Page {page_num}"
        page_width = A4[0]
        page_text_width = self.canvas.stringWidth(page_text)
        self.canvas.drawString(page_width - 72 - page_text_width, 30, page_text)
        
        # Footer (bottom center) - smaller font
        self.canvas.setFont("Helvetica", 8)  # Reduced font size by 2px
        footer_text = "Prepared by: Lead Time Analysis Tool - 2025 - Copyright Pietro"
        text_width = self.canvas.stringWidth(footer_text)
        x_position = (page_width - text_width) / 2
        self.canvas.drawString(x_position, 30, footer_text)
        self.canvas.setFont("Helvetica", 12)  # Reset to default font size

class PDFReportGenerator:
    """
    Generates comprehensive PDF reports for Jira analytics data.
    
    This class creates formatted PDF reports including charts, tables,
    and statistical analysis of agile metrics.
    """
    
    def __init__(self):
        """Initialize the PDF generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.blue
        )
    
    def generate_report(self, analysis_data: Dict, output_path: str):
        """
        Generate complete PDF report.
        
        Args:
            analysis_data (Dict): Analysis results and charts
            output_path (str): Path to save the PDF report
        """
        try:
            # Create PDF document with custom canvas for page numbers and footer
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=60,  # Increased for footer space
                author="Lead Time Analysis Tool by Pietro Maffi",
                title="Jira Analytics Report",
                subject="Lead Time and Cycle Time Analysis"
            )
            
            # Build report content
            story = []
            
            # Title page
            story.extend(self._create_title_page(analysis_data))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(analysis_data))
            story.append(PageBreak())
            
            # Detailed analysis
            story.extend(self._create_detailed_analysis(analysis_data))
            story.append(PageBreak())
            
            # Charts section
            story.extend(self._create_charts_section(analysis_data))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self._create_recommendations(analysis_data))
            
            # Build PDF with custom canvas function
            def add_page_elements(canvas, doc):
                numbered_canvas = NumberedCanvas(canvas, doc)
                numbered_canvas.draw_page_number_and_footer()
            
            doc.build(story, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
            logger.info(f"✅ PDF report generated successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"🚩 PDF generation failed: {str(e)}")
            raise Exception(f"Failed to generate PDF report: {str(e)}")
    
    def _create_title_page(self, data: Dict) -> list:
        """Create title page content."""
        content = []
        
        # Add logo if available
        try:
            import os
            logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path)
                logo.drawHeight = 1.5*inch
                logo.drawWidth = 2.5*inch  # Wider to preserve aspect ratio
                logo.hAlign = 'CENTER'
                content.append(logo)
                content.append(Spacer(1, 0.3*inch))
        except Exception as e:
            logger.warning(f"⚠️ Could not load logo: {str(e)}")
        
        # Title
        content.append(Paragraph("Jira Lead time Analytics Report", self.title_style))
        content.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        analysis_period = data.get('analysis_period', 'Unknown period')
        content.append(Paragraph(f"Analysis Period: {analysis_period}", self.heading_style))
        content.append(Spacer(1, 0.3*inch))
        
        # Generation info
        generation_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        content.append(Paragraph(f"Generated on: {generation_date}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Summary stats
        total_issues = data.get('total_issues', 0)
        content.append(Paragraph(f"Total Issues Analyzed: {total_issues}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Add original JQL query submitted
        # content.append(Paragraph(f"JQL Query Submitted:")
        
        # Jira server info
        jira_url = data.get('jira_url', 'Unknown server')
        content.append(Paragraph(f"Jira Server: {jira_url}", self.styles['Normal']))
        content.append(Spacer(1, 0.15*inch))
    
        # Check if this is CSV upload or standard JQL analysis
        csv_issues_found = data.get('csv_issues_found')
        if csv_issues_found is not None:
            # This is CSV upload - show CSV filename instead of JQL
            content.append(Paragraph("Data Source: CSV File Upload", self.styles['Normal']))
            content.append(Paragraph(f"Issues found in CSV: {csv_issues_found}", self.styles['Normal']))
        else:
            # This is standard JQL analysis - show JQL query
            jql_query = data.get('jql_query', 'No query specified')
            # Wrap long queries to prevent page overflow
            if len(jql_query) > 80:
                # Split long queries into multiple lines for better readability
                query_parts = []
                words = jql_query.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) > 80:
                        if current_line:
                            query_parts.append(current_line.strip())
                        current_line = word + " "
                    else:
                        current_line += word + " "
                if current_line:
                    query_parts.append(current_line.strip())
            
                content.append(Paragraph("JQL Query Submitted:", self.styles['Normal']))
                for part in query_parts:
                    content.append(Paragraph(f"<font name='Courier'>{part}</font>", self.styles['Normal']))
            else:
                content.append(Paragraph(f"JQL Query Submitted: <font name='Courier'>{jql_query}</font>", self.styles['Normal']))
    
        content.append(Spacer(1, 0.2*inch))
        
        return content
    
    def _create_executive_summary(self, data: Dict) -> list:
        """Create executive summary section."""
        content = []
        
        content.append(Paragraph("Executive Summary", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        # Key metrics summary
        metrics = data.get('metrics', {})
        
        if 'lead_time' in metrics:
            lt = metrics['lead_time']
            summary_text = f"""
            This report analyzes {data.get('total_issues', 0)} Jira issues over the past {data.get('analysis_period', 'unknown period')}.
            <br/>
            <b>Key Findings:</b><br/>
            • Average Lead Time: {lt.get('average', 0):.1f} days<br/>
            • Median Lead Time: {lt.get('median', 0):.1f} days<br/>
            • 85th Percentile: {lt.get('p85', 0):.1f} days<br/>
            • 95th Percentile: {lt.get('p95', 0):.1f} days<br/>
            """
            content.append(Paragraph(summary_text, self.styles['Normal']))
        
        # Cycle time summary
        cycle_times = {}
        for key, value in metrics.items():
            if key.startswith('cycle_time_') and isinstance(value, dict):
                status = key.replace('cycle_time_', '').replace('_', ' ').title()
                cycle_times[status] = value.get('average', 0)
        
        if cycle_times:
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph("Average Time in Each Status:", self.subheading_style))
            
            cycle_text = ""
            for status, avg_time in cycle_times.items():
                cycle_text += f"• {status}: {avg_time:.1f} days<br/>"
            
            content.append(Paragraph(cycle_text, self.styles['Normal']))
        
        return content
    
    def _create_detailed_analysis(self, data: Dict) -> list:
        """Create detailed analysis section."""
        content = []
        
        content.append(Paragraph("Detailed Analysis", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        # Lead time analysis
        content.append(Paragraph("Lead Time Analysis", self.heading_style))
        
        metrics = data.get('metrics', {})
        if 'lead_time' in metrics:
            lt = metrics['lead_time']
            
            # Create metrics table
            lead_time_data = [
                ['Metric', 'Value (Days)'],
                ['Average', f"{lt.get('average', 0):.1f}"],
                ['Median', f"{lt.get('median', 0):.1f}"],
                ['85th Percentile', f"{lt.get('p85', 0):.1f}"],
                ['95th Percentile', f"{lt.get('p95', 0):.1f}"]
            ]
            
            # Use 75% of page width for lead time table
            page_width = A4[0] - 144  # Subtract margins (72 each side)
            table_width = page_width * 0.75
            col1_width = table_width * 0.6
            col2_width = table_width * 0.4
            lead_time_table = Table(lead_time_data, colWidths=[col1_width, col2_width])
            lead_time_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(lead_time_table)
            content.append(Spacer(1, 0.3*inch))
        
        # Cycle time analysis
        content.append(Paragraph("Cycle Time Analysis", self.heading_style))
        
        cycle_data = [['Status', 'Average Time (Days)']]
        for key, value in metrics.items():
            if key.startswith('cycle_time_') and isinstance(value, dict):
                status = key.replace('cycle_time_', '').replace('_', ' ').title()
                cycle_data.append([status, f"{value.get('average', 0):.1f}"])
        
        if len(cycle_data) > 1:
            # Use 75% of page width for cycle time table
            page_width = A4[0] - 144  # Subtract margins (72 each side)
            table_width = page_width * 0.75
            col1_width = table_width * 0.6
            col2_width = table_width * 0.4
            cycle_table = Table(cycle_data, colWidths=[col1_width, col2_width])
            cycle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(cycle_table)
        
        return content
    
    def _create_charts_section(self, data: Dict) -> list:
        """Create charts section."""
        content = []
        
        content.append(Paragraph("Visualizations", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        charts = data.get('charts', {})
        
        # Add each chart
        chart_titles = {
            'lead_time_distribution': 'Lead Time Distribution',
            'cycle_time_comparison': 'Cycle Time Comparison',
            'status_duration_boxplot': 'Status Duration Analysis',
            'lead_time_trend': 'Lead Time Trend',
            'metrics_summary': 'Metrics Summary'
        }
        
        for chart_key, chart_title in chart_titles.items():
            if chart_key in charts:
                content.append(Paragraph(chart_title, self.heading_style))
                content.append(Spacer(1, 0.1*inch))
                
                # Convert base64 image to Image object
                chart_data = charts[chart_key]
                if chart_data.startswith('data:image/png;base64,'):
                    img_data = base64.b64decode(chart_data.split(',')[1])
                    img = Image(io.BytesIO(img_data))
                    img.drawHeight = 4*inch
                    img.drawWidth = 6*inch
                    content.append(img)
                    content.append(Spacer(1, 0.3*inch))
                    
                    # Add page break after Lead Time Distribution
                    if chart_key == 'lead_time_distribution':
                        content.append(PageBreak())
        
        return content
    
    def _create_recommendations(self, data: Dict) -> list:
        """Create recommendations section."""
        content = []
        
        # Add page break before recommendations
        content.append(PageBreak())
        content.append(Paragraph("Recommendations", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        metrics = data.get('metrics', {})
        
        recommendations = []
        
        # Lead time recommendations
        if 'lead_time' in metrics:
            lt = metrics['lead_time']
            avg_lead_time = lt.get('average', 0)
            p95_lead_time = lt.get('p95', 0)
            
            if avg_lead_time > 14:  # More than 2 weeks
                recommendations.append(
                    "Consider breaking down work items as the average lead time exceeds 2 weeks."
                )
            
            if p95_lead_time > avg_lead_time * 2:
                recommendations.append(
                    "High variability in lead times suggests inconsistent work sizing or process bottlenecks."
                )
        
        # Cycle time recommendations
        cycle_times = {}
        for key, value in metrics.items():
            if key.startswith('cycle_time_') and isinstance(value, dict):
                status = key.replace('cycle_time_', '')
                cycle_times[status] = value.get('average', 0)
        
        if 'testing' in cycle_times and cycle_times['testing'] > 5:
            recommendations.append(
                "Testing phase shows high average time. Consider improving test automation or increasing testing capacity."
            )
        
        if 'validation' in cycle_times and cycle_times['validation'] > 3:
            recommendations.append(
                "Validation phase may benefit from clearer acceptance criteria or increased stakeholder availability."
            )
        
        # Default recommendations if no specific issues found
        if not recommendations:
            recommendations.extend([
                "Continue monitoring lead time trends to identify improvement opportunities.",
                "Consider implementing regular retrospectives to address process bottlenecks.",
                "Maintain consistent work sizing to reduce lead time variability."
            ])
        
        # Add recommendations to content
        for i, rec in enumerate(recommendations, 1):
            content.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
            content.append(Spacer(1, 0.1*inch))
        
        return content