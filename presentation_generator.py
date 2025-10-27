"""
Professional Presentation Generator
Creates a modern PDF slide deck about the Jira Analytics applications.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable
from io import BytesIO
from datetime import datetime
import logging
import os

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PresentationGenerator')

class PresentationGenerator:
    """Generates professional PDF presentations for Jira Analytics applications."""
    
    def __init__(self):
        """Initialize the presentation generator."""
        self.styles = getSampleStyleSheet()
        self.elements = []
        
        # Define color scheme and font first
        self.primary_blue = colors.Color(0.1, 0.3, 0.7)
        self.secondary_blue = colors.Color(0.2, 0.5, 0.9)
        self.accent_orange = colors.Color(0.9, 0.5, 0.1)
        self.light_gray = colors.Color(0.95, 0.95, 0.95)
        self.dark_gray = colors.Color(0.3, 0.3, 0.3)
        
        # Font configuration - change here to update all fonts
        self.main_font = 'Helvetica-Bold'  # Change this to update all fonts
        self.table_font = 'Helvetica'  # Standard table font
        self.table_font_size = 14  # Standard table font size
        self.table_padding = 12  # Standard table padding
        
        # Setup styles after colors are defined
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom styles for the presentation."""
        # Title style - bigger and more prominent
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=46,
            textColor=self.primary_blue,
            alignment=1,  # Center
            spaceAfter=40,
            fontName=self.main_font
        )
        
        # Slide title style - bigger and more prominent
        self.slide_title_style = ParagraphStyle(
            'SlideTitle',
            parent=self.styles['Heading1'],
            fontSize=36,
            textColor=self.primary_blue,
            alignment=1,  # Center
            spaceAfter=30,
            spaceBefore=20,
            fontName=self.main_font
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=self.dark_gray,
            alignment=1,
            spaceAfter=20,
            fontName=self.main_font
        )
        
        # Large text style
        self.large_text_style = ParagraphStyle(
            'LargeText',
            parent=self.styles['Normal'],
            fontSize=18,
            spaceAfter=15,
            leading=24
        )
    
    def add_background_image(self, slide_number=1):
        """Add background image - always uses slide_1.png for consistency."""
        image_dir = os.path.join(os.path.dirname(__file__), 'doc', 'images')
        image_path = os.path.join(image_dir, 'slide_1.png')  # Always use slide_1.png
        
        if os.path.exists(image_path):
            try:
                img = Image(image_path, width=10*inch, height=6*inch)
                self.elements.append(img)
                self.elements.append(Spacer(1, -6*inch))  # Overlap
                return True
            except Exception as e:
                logger.warning(f"Could not load background image {image_path}: {e}")
        return False
    
    def add_title_slide(self):
        """Add the title slide with professional background."""
        # Try to add background image
        if not self.add_background_image(1):
            # Add colored background if no image
            bg_data = [[""]]
            bg_table = Table(bg_data, colWidths=[10*inch], rowHeights=[7.5*inch])
            bg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.95, 0.98, 1.0)),
                ('GRID', (0, 0), (-1, -1), 0, colors.white)
            ]))
            self.elements.append(bg_table)
            self.elements.append(Spacer(1, -6*inch))
        
        self.elements.append(Spacer(1, 1*inch))
        
        # Main title
        title = Paragraph("Jira Analytics Suite", self.title_style)
        self.elements.append(title)
        
        # Subtitle
        subtitle = Paragraph("Advanced Flow Metrics & Product Analysis Tools", self.subtitle_style)
        self.elements.append(subtitle)
        
        self.elements.append(Spacer(1, 0.5*inch))
        
        # Value proposition
        value_data = [[
            "► Empowering Agile Teams with Data-Driven Insights\n\n"
            "► Analytics for Product Increments, Sprints, and Epic management\n\n"
            "► Real-time metrics and professional reporting\n\n"
            "► Evidence-based decision making for agile transformation"
        ]]
        
        value_table = Table(value_data, colWidths=[8*inch], rowHeights=[1.8*inch])
        value_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.99, 1.0)),
            ('PADDING', (0, 0), (-1, -1), 22),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, self.secondary_blue)
        ]))
        self.elements.append(value_table)
        
        self.elements.append(Spacer(1, 0.5*inch))
        

        
        self.elements.append(PageBreak())
    
    def add_flow_metrics_intro_slide(self):
        """Add introduction slide about flow metrics value."""
        # Try to add background image
        if not self.add_background_image(2):
            # Add simple background
            self.elements.append(Spacer(1, 0.5*inch))
        
        self.elements.append(Paragraph("Why Flow Metrics Matter", self.slide_title_style))
        self.elements.append(Spacer(1, 0.3*inch))
        
        # Key concepts
        data = [
            ["● Predictability", "Forecast delivery dates with statistical confidence"],
            ["● Visibility", "Real-time insights into team performance and issue"],
            ["● Efficiency", "Identify and eliminate workflow inefficiencies"],
            ["● Continuous Improvement", "Data-driven retrospectives and sprint planning"]
        ]
        
        table = Table(data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*4)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.primary_blue),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 0.97, 1.0)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, self.secondary_blue)
        ]))
        self.elements.append(table)
        #page break added by Pietro to fix issue with table splitting
        self.elements.append(PageBreak())
        
        # Add background to new page
        if not self.add_background_image():
            self.elements.append(Spacer(1, 0.5*inch))
                
        self.elements.append(Paragraph("Flow Metrics", self.slide_title_style))
        self.elements.append(Spacer(1, 0.3*inch))
        
        # Core metrics table
        metrics_data = [
            ["● WIP (Work in Progress)", "Items currently being worked on - measures team capacity"],
            ["● Throughput", "Items completed per time period - measures delivery rate"],
            ["● Work Item Age", "Time items spend in progress - identifies stalled work"],
            ["● Cycle Time", "Total time from start to completion - measures efficiency"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*4)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.1, 0.5, 0.3)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 0.99, 0.97)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.6, 0.8, 0.7))
        ]))
        self.elements.append(metrics_table)
        
        self.elements.append(PageBreak())
    
    def add_pi_analyzer_slide(self):
        """Add PI Analyzer application slide."""
        if not self.add_background_image(3):
            self.elements.append(Spacer(1, 0.5*inch))
        
        self.elements.append(Paragraph("PI (Product Increment) Analyzer", self.slide_title_style))
        
        # Purpose table
        purpose_data = [
            ["● Purpose", "Analyze Product Increment completion metrics and flow patterns"],
            ["● Scope", "ISDOP Business Initiatives and all related child projects"],
            ["● Discovery", "Automatic project discovery through parent/child relationships"],
            ["● Analysis", "Completion metrics + optional comprehensive flow metrics"]
        ]
        
        purpose_table = Table(purpose_data, colWidths=[1.5*inch, 6*inch], rowHeights=[0.7*inch]*4)
        purpose_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.2, 0.4, 0.8)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 0.97, 1.0)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.7, 0.8, 0.9))
        ]))
        self.elements.append(purpose_table)
        
        self.elements.append(Spacer(1, 0.2*inch))
        #page break added by Pietro to fix issue with table splitting
        self.elements.append(PageBreak())
        
        # Add background to new page
        if not self.add_background_image():
            self.elements.append(Spacer(1, 0.5*inch))

        self.elements.append(Paragraph("PI Analyzer feature", self.slide_title_style))
                
        # Key features table
        features_data = [
            ["● Cross-project Analysis", "Completion analysis with automatic discovery"],
            ["● Issue Type Breakdown", "Bug, Story, Feature, Sub-task categorization"],
            ["● Estimation Analysis", "Unestimated work tracking and validation"],
            ["● Flow Metrics", "WIP, Throughput, Cycle Time, Work Item Age"],
            ["● Professional Reports", "PDF reports with coaching recommendations"],
            ["● Configurable Scope", "Basic vs. full area backlog analysis"]
        ]
        
        features_table = Table(features_data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*6)
        features_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.2, 0.4, 0.8)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 0.97, 1.0)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.7, 0.8, 0.9))
        ]))
        self.elements.append(features_table)
        
        self.elements.append(PageBreak())
    
    def add_sprint_analyzer_slide(self):
        """Add Sprint Analyzer application slide."""
        if not self.add_background_image(4):
            self.elements.append(Spacer(1, 0.5*inch))
        
        self.elements.append(Paragraph("Sprint Analyzer", self.slide_title_style))
        
        # Purpose table
        purpose_data = [
            ["● Purpose", "Forecast sprint feasibility using historical velocity data"],
            ["● Analysis", "Workload analysis with time tracking integration"],
            ["● Forecasting", "Completion probability based on historical performance"],
            ["● Insights", "Risk assessment and actionable recommendations"]
        ]
        
        purpose_table = Table(purpose_data, colWidths=[1.5*inch, 6*inch], rowHeights=[0.7*inch]*4)
        purpose_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.8, 0.4, 0.2)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(1.0, 0.97, 0.95)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.9, 0.8, 0.7))
        ]))
        self.elements.append(purpose_table)
        
        self.elements.append(Spacer(1, 0.2*inch))
        
        #page break added by Pietro to fix issue with table splitting
        self.elements.append(PageBreak())
        
        # Add background to new page
        if not self.add_background_image():
            self.elements.append(Spacer(1, 0.5*inch))   

        self.elements.append(Paragraph("Sprint Analyzer key feature", self.slide_title_style))
                
        # Key features table
        features_data = [
            ["● Velocity Analysis", "Historical analysis for accurate forecasting"],
            ["● Progress Tracking", "Real-time sprint progress with time estimates"],
            ["● Risk Assessment", "Automatic risk level assessment (LOW/MEDIUM/HIGH)"],
            ["● Status Breakdown", "Analysis of To Do, In Progress, Done items"],
            ["● Smart Recommendations", "Based on historical patterns and data"],
            ["● Time Integration", "Integration with existing Jira time tracking"]
        ]
        
        features_table = Table(features_data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*6)
        features_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.8, 0.4, 0.2)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(1.0, 0.97, 0.95)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.9, 0.8, 0.7))
        ]))
        self.elements.append(features_table)
        
        self.elements.append(PageBreak())
    
    def add_epic_analyzer_slide(self):
        """Add Epic Analyzer application slide."""
        if not self.add_background_image(5):
            self.elements.append(Spacer(1, 0.5*inch))
        
        self.elements.append(Paragraph("Epic Analyzer & Estimate Manager", self.slide_title_style))
        
        # Purpose table
        purpose_data = [
            ["● Purpose", "Analyze Epic progress and manage estimate synchronization"],
            ["● Analysis", "Epic vs. child issue estimate comparison and progress tracking"],
            ["● Updates", "Direct API integration for estimate updates in Jira"],
            ["● Export", "CSV export for bulk estimate management"]
        ]
        
        purpose_table = Table(purpose_data, colWidths=[1.5*inch, 6*inch], rowHeights=[0.7*inch]*4)
        purpose_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.2, 0.8, 0.4)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 1.0, 0.97)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.7, 0.9, 0.8))
        ]))
        self.elements.append(purpose_table)
        
        self.elements.append(Spacer(1, 0.2*inch))

        #page break added by Pietro to fix issue with table splitting
        self.elements.append(PageBreak())
        
        # Add background to new page
        if not self.add_background_image():
            self.elements.append(Spacer(1, 0.5*inch))
                                
        self.elements.append(Paragraph("Epic Analyzer key feature", self.slide_title_style))
        # Key features table
        features_data = [
            ["● Estimate Comparison", "Epic-to-child estimate comparison and validation"],
            ["● Progress Tracking", "Visual indicators and progress monitoring"],
            ["● Discrepancy Detection", "Automatic identification of estimate discrepancies"],
            ["● API Integration", "Direct Jira API updates for time tracking fields"],
            ["● Security Measures", "Comprehensive security and rate limiting"],
            ["● Compact Reporting", "Pagination for large datasets management"]
        ]
        
        features_table = Table(features_data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*6)
        features_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.2, 0.8, 0.4)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 1.0, 0.97)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.7, 0.9, 0.8))
        ]))
        self.elements.append(features_table)
        
        self.elements.append(PageBreak())
    
    def add_technical_overview_slide(self):
        """Add technical architecture overview slide."""
        if not self.add_background_image(6):
            self.elements.append(Spacer(1, 0.5*inch))
        
        self.elements.append(Paragraph("Technical Architecture & Integration", self.slide_title_style))
        
        # Architecture table
        arch_data = [
            ["● Framework", "Modular Python architecture with reusable components"],
            ["● Integration", "Jira REST API with comprehensive error handling"],
            ["● Analytics", "Statistical analysis with pandas and numpy"],
            ["● Visualization", "Professional charts and PDF generation"],
            ["● Security", "Rate limiting, input validation, JQL injection prevention"],
            ["● Quality", "Test-driven development with comprehensive test coverage"]
        ]
        
        arch_table = Table(arch_data, colWidths=[1.5*inch, 6*inch], rowHeights=[0.7*inch]*6)
        arch_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.6, 0.2, 0.8)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.98, 0.95, 1.0)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.8, 0.7, 0.9))
        ]))
        self.elements.append(arch_table)
        
        self.elements.append(Spacer(1, 0.2*inch))
        #page break added by Pietro to fix issue with table splitting
        self.elements.append(PageBreak())
        
        # Add background to new page
        if not self.add_background_image():
            self.elements.append(Spacer(1, 0.5*inch))
                
        self.elements.append(Paragraph("Technical Architecture key feature", self.slide_title_style))
        
        # Shared components table
        components_data = [
            ["● JiraClient", "Unified API connectivity with retry logic and timeouts"],
            ["● DataAnalyzer", "Core analytics engine for statistical calculations"],
            ["● VisualizationGenerator", "Professional charts and graphs creation"],
            ["● PDFGenerator", "Consistent report formatting across applications"],
            ["● Security Layer", "Input validation, rate limiting, safe API handling"]
        ]
        
        components_table = Table(components_data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*5)
        components_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.6, 0.2, 0.8)),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.98, 0.95, 1.0)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.8, 0.7, 0.9))
        ]))
        self.elements.append(components_table)
        
        self.elements.append(PageBreak())
    
    def add_business_value_slide(self):
        """Add business value slide."""
        if not self.add_background_image(7):
            self.elements.append(Spacer(1, 0.5*inch))
        
        self.elements.append(Paragraph("Business Value & Impact", self.slide_title_style))
        self.elements.append(Spacer(1, 0.3*inch))
        
        # Value propositions
        value_data = [
            ["● Cost Reduction", "Eliminate manual reporting and reduce analysis time"],
            ["● Improved Delivery", "Increase predictability through data-driven planning"],
            ["● Better Decisions", "Evidence-based insights for resource allocation"],
            ["● Faster Feedback", "Real-time metrics enable rapid course correction"],
            ["● Process Improvement", "Identify bottlenecks and optimization opportunities"],
            ["● Stakeholder Confidence", "Professional reports increase management trust"]
        ]
        
        value_table = Table(value_data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*6)
        value_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.accent_orange),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(1.0, 0.98, 0.95)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.9, 0.6, 0.2))
        ]))
        self.elements.append(value_table)
        
        self.elements.append(PageBreak())
    
    def add_roi_slide(self):
        """Add dedicated ROI slide with detailed analysis."""
        if not self.add_background_image(8):
            self.elements.append(Spacer(1, 0.5*inch))
        
        # ROI Title
        roi_title = Paragraph("Return on Investment Analysis", self.slide_title_style)
        self.elements.append(roi_title)
        
        self.elements.append(Spacer(1, 0.3*inch))
        
        # ROI metrics with better column sizing
        roi_data = [
            ["● Time Savings", "Significant reduction in manual reporting"],
            ["● Accuracy Improvement", "Increase in planning precision"],
            ["● Decision Speed", "Real-time insights and immediate identification"],
            ["● Team Productivity", "Improvement in delivery efficiency"]
        ]
        
        roi_table = Table(roi_data, colWidths=[2.5*inch, 5*inch], rowHeights=[0.7*inch]*4)
        roi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.primary_blue),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 0.97, 1.0)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.1, 0.3, 0.7))
        ]))
        self.elements.append(roi_table)
        
        self.elements.append(Spacer(1, 0.3*inch))
        #page break added by Pietro to fix issue with table splitting
        self.elements.append(PageBreak())
        
        # Add background to new page
        if not self.add_background_image():
            self.elements.append(Spacer(1, 0.5*inch))

        self.elements.append(Paragraph("ROI advantage", self.slide_title_style))
                
        # Financial impact table
        financial_data = [
            ["● Annual Cost Savings", "Substantial reduction in manual effort"],
            ["● Delivery Predictability", "Reduces project overruns and delays"],
            ["● Team Efficiency", "Focus on value delivery vs. reporting"],
            ["● Risk Mitigation", "Early identification prevents costly delays"],
            ["● Stakeholder Confidence", "Professional reporting increases project support"]
        ]
        
        financial_table = Table(financial_data, colWidths=[2.5*inch, 5.5*inch], rowHeights=[0.7*inch]*5)
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.primary_blue),
            ('BACKGROUND', (1, 0), (1, -1), colors.Color(0.95, 0.97, 1.0)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), self.table_padding),
            ('FONTSIZE', (0, 0), (-1, -1), self.table_font_size),
            ('FONTNAME', (0, 0), (0, -1), self.main_font),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.1, 0.3, 0.7))
        ]))
        self.elements.append(financial_table)
        
        self.elements.append(PageBreak())
    
    def add_thank_you_slide(self):
        """Add thank you slide."""
        if not self.add_background_image(9):
            self.elements.append(Spacer(1, 1*inch))
        
        # Thank you title
        thank_you_title = Paragraph("Thank You!", self.title_style)
        self.elements.append(thank_you_title)
        
        self.elements.append(Spacer(1, 0.5*inch))
        
        # Thank you message
        message_data = [[
            "Questions & Discussion\n\n"
            "Let's discuss how these tools can benefit your team!"
        ]]
        
        message_table = Table(message_data, colWidths=[8*inch]*3, rowHeights=[2.5*inch])
        message_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.99, 1.0)),
            ('PADDING', (0, 0), (-1, -1), 30),
            ('FONTSIZE', (0, 0), (-1, -1), 20),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, self.secondary_blue)
        ]))
        self.elements.append(message_table)
        
        self.elements.append(PageBreak())
    
    def add_footer(self, canvas, doc):
        """Add footer with page numbers and author."""
        canvas.saveState()
        
        # Footer text with presented by
        footer_text = f"Presented by: Pietro Maffi | {datetime.now().strftime('%B %Y')} | Jira Analytics Suite"
        canvas.setFont('Helvetica', 9)
        canvas.drawString(doc.leftMargin, 30, footer_text)
        
        # Page number
        page_num = f"Page {canvas.getPageNumber()}"
        canvas.drawRightString(doc.width + doc.leftMargin, 30, page_num)
        
        canvas.restoreState()
    
    def generate_presentation(self):
        """Generate the complete presentation PDF."""
        buffer = BytesIO()
        
        # Use landscape orientation for better slide layout
        doc = BaseDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=70,
            author="Pietro Maffi",
            title="Jira Analytics Suite Presentation"
        )
        
        # Create frame and page template
        frame = Frame(
            doc.leftMargin, doc.bottomMargin + 20,
            doc.width, doc.height - 20,
            id='normal'
        )
        
        template = PageTemplate(id='main', frames=frame, onPage=self.add_footer)
        doc.addPageTemplates([template])
        
        # Add all slides
        logger.info("🎨 Generating presentation slides...")
        self.add_title_slide()
        self.add_flow_metrics_intro_slide()
        self.add_pi_analyzer_slide()
        self.add_sprint_analyzer_slide()
        self.add_epic_analyzer_slide()
        self.add_technical_overview_slide()
        self.add_business_value_slide()
        self.add_roi_slide()  # Separate ROI slide
        self.add_thank_you_slide()  # Thank you slide
        
        # Build the PDF
        doc.build(self.elements)
        
        buffer.seek(0)
        return buffer

def main():
    """Main function to generate the presentation."""
    try:
        logger.info("🚀 Starting presentation generation...")
        
        # Create generator
        generator = PresentationGenerator()
        
        # Generate presentation
        pdf_buffer = generator.generate_presentation()
        
        # Ensure doc directory exists
        doc_dir = os.path.join(os.path.dirname(__file__), 'doc')
        os.makedirs(doc_dir, exist_ok=True)
        
        # Save to doc folder
        output_path = os.path.join(doc_dir, "Jira_Analytics_Suite_Presentation.pdf")
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        logger.info(f"✅ Presentation generated successfully: {output_path}")
        print(f"\n🎉 Presentation created: {output_path}")
        print("📊 Ready to present your Jira Analytics Suite to management!")
        
    except Exception as e:
        logger.error(f"🚩 Error generating presentation: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()