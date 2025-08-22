"""
Sprint PDF Report Generator
Generates comprehensive PDF reports with detailed analysis data.

Author: Pietro Maffi
Copyright: Pietro Maffi 2025
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import logging

logger = logging.getLogger('SprintPDFGenerator')

class SprintPDFReportGenerator:
    """Generate comprehensive PDF reports for sprint analysis."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles."""
        self.styles.add(ParagraphStyle(
            name='SprintTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SprintSection',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SprintCode',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Courier',
            leftIndent=20
        ))
    
    def generate_report(self, results: dict, sprint_name: str, jql_queries: list = None, 
                       detailed_logs: dict = None) -> bytes:
        """Generate PDF report."""
        from io import BytesIO
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=100,
            author="Pietro Maffi",
            title=f"Sprint Analysis Report - {sprint_name}",
            subject="Sprint Analysis Report"
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f"Sprint Analysis Report", self.styles['SprintTitle']))
        story.append(Paragraph(f"<b>Sprint analyzed: {sprint_name}</b>", self.styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Sprint Analyzer Features
        story.append(Paragraph("Sprint Analyzer Features:", self.styles['Normal']))
        story.append(Paragraph("1. Clear Risk Visualization: See exactly how many stories are at risk at different confidence levels", self.styles['Normal']))
        story.append(Paragraph("2. Actionable Recommendations: Know precisely which stories to remove for different risk tolerances", self.styles['Normal']))
        story.append(Paragraph("3. Monte Carlo Forecasting: Use statistical analysis to predict sprint outcomes", self.styles['Normal']))
        story.append(Paragraph("4. Historical Context: Leverage past sprint data to improve future planning", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        self._add_summary(story, results)
        
        # Metrics
        self._add_metrics(story, results)
        
        # Historical & Monte Carlo
        self._add_historical_data(story, results, detailed_logs)
        
        # Technical Details
        if jql_queries or detailed_logs:
            story.append(PageBreak())
            self._add_technical_details(story, jql_queries, detailed_logs)
        
        # Recommendations
        self._add_recommendations(story, results)
        
        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _add_footer(self, canvas, doc):
        """Add footer with page number and copyright."""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(72, 50, f"Page {doc.page}")
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Sprint Analyzer | © Pietro Maffi 2025"
        canvas.drawRightString(A4[0] - 72, 50, footer_text)
        canvas.restoreState()
    
    def _add_summary(self, story, results):
        """Add summary section."""
        story.append(Paragraph("Executive Summary", self.styles['SprintSection']))
        
        # Get data from main_metrics instead of summary
        main_metrics = results.get('main_metrics', {})
        
        data = [
            ['Total Issues', str(main_metrics.get('total_issues', 0))],
            ['Estimated Hours', f"{main_metrics.get('total_estimated_hours', 0):.1f}h"],
            ['Remaining Hours', f"{main_metrics.get('remaining_hours', 0):.1f}h"],
            ['Progress', f"{main_metrics.get('overall_progress', 0):.1f}%"],
            ['Risk Level', main_metrics.get('risk_level', 'UNKNOWN')],
            ['Completion Probability', f"{main_metrics.get('completion_probability', 0):.0f}%"]
        ]
        
        table = Table(data, colWidths=[2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
    
    def _add_metrics(self, story, results):
        """Add metrics section."""
        story.append(Paragraph("Main Metrics", self.styles['SprintSection']))
        
        # Get data from main_metrics
        main_metrics = results.get('main_metrics', {})
        
        story.append(Paragraph(f"Time Spent: {main_metrics.get('time_spent_hours', 0):.1f}h", self.styles['Normal']))
        story.append(Paragraph(f"Original Estimate: {main_metrics.get('total_estimated_hours', 0):.1f}h", self.styles['Normal']))
        story.append(Paragraph(f"Remaining: {main_metrics.get('remaining_hours', 0):.1f}h", self.styles['Normal']))
        
        unestimated = results.get('unestimated_issues', 0)
        if unestimated > 0:
            story.append(Paragraph(f"Unestimated Issues: {unestimated}", self.styles['Normal']))
        
        story.append(Spacer(1, 15))
    
    def _add_historical_data(self, story, results, detailed_logs):
        """Add historical context and Monte Carlo data."""
        story.append(Paragraph("Historical Context & Monte Carlo Analysis", self.styles['SprintSection']))
        
        historical = results.get('historical_context', {})
        
        story.append(Paragraph(f"Average Velocity: {historical.get('average_velocity', 0):.1f} stories/week", self.styles['Normal']))
        story.append(Paragraph(f"Completion Rate: {historical.get('completion_rate', 0):.0f}%", self.styles['Normal']))
        story.append(Paragraph(f"Historical Issues: {historical.get('total_historical_issues', 0)}", self.styles['Normal']))
        
        # Monte Carlo results from velocity_percentiles
        velocity_percentiles = historical.get('velocity_percentiles', {})
        if velocity_percentiles:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Monte Carlo Results:", self.styles['Normal']))
            story.append(Paragraph(f"P10: {velocity_percentiles.get('p10', 0):.1f}, P50: {velocity_percentiles.get('p50', 0):.1f}, P90: {velocity_percentiles.get('p90', 0):.1f}", self.styles['SprintCode']))
        
        # Weekly velocity data from detailed_logs
        if detailed_logs and 'weekly_velocities' in detailed_logs and detailed_logs['weekly_velocities'] != "[Data captured during analysis]":
            story.append(Spacer(1, 10))
            story.append(Paragraph("Weekly Story Completion Data:", self.styles['Normal']))
            story.append(Paragraph(f"{detailed_logs['weekly_velocities']}", self.styles['SprintCode']))
        
        story.append(Spacer(1, 20))
    
    def _add_technical_details(self, story, jql_queries, detailed_logs):
        """Add technical details."""
        story.append(Paragraph("Technical Details", self.styles['SprintSection']))
        
        if jql_queries:
            story.append(Paragraph("JQL Queries Executed:", self.styles['Normal']))
            for i, query in enumerate(jql_queries, 1):
                story.append(Paragraph(f"{i}. {query}", self.styles['SprintCode']))
            story.append(Spacer(1, 15))
        
        if detailed_logs and 'forecast_details' in detailed_logs:
            details = detailed_logs['forecast_details']
            story.append(Paragraph("Forecast Details:", self.styles['Normal']))
            if 'velocity_used' in details:
                story.append(Paragraph(f"Using Monte Carlo velocity: {details['velocity_used']:.1f} stories/week", self.styles['SprintCode']))
            if 'remaining_stories' in details:
                story.append(Paragraph(f"Remaining stories: {details['remaining_stories']}", self.styles['SprintCode']))
        
        story.append(Spacer(1, 20))
    
    def _add_recommendations(self, story, results):
        """Add recommendations."""
        story.append(Paragraph("Recommendations", self.styles['SprintSection']))
        
        # Get recommendations from forecast_details
        forecast_details = results.get('forecast_details', {})
        recommendations = forecast_details.get('recommendations', [])
        
        if recommendations:
            for rec in recommendations:
                clean_rec = rec.replace('📝', '•').replace('⚠️', '•').replace('📊', '•').replace('🚀', '•').replace('📈', '•').replace('✅', '•').replace('🔴', '•')
                story.append(Paragraph(clean_rec, self.styles['Normal']))
        else:
            story.append(Paragraph("No specific recommendations at this time.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))