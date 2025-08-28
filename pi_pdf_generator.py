"""
PI PDF Report Generator
Creates comprehensive PDF reports for Product Increment analysis.

Author: PI Analysis Tool by Pietro Maffi
Purpose: Generate professional PDF reports for PI metrics
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
import logging
from typing import Dict

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PIPDFGenerator')

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
        self.canvas.setFont("Helvetica", 8)
        footer_text = "Prepared by: PI Analysis Tool - 2025 - Copyright Pietro Maffi"
        text_width = self.canvas.stringWidth(footer_text)
        x_position = (page_width - text_width) / 2
        self.canvas.drawString(x_position, 30, footer_text)
        self.canvas.setFont("Helvetica", 12)  # Reset to default font size

class PIPDFReportGenerator:
    """
    Generates comprehensive PDF reports for PI analysis data.
    
    This class creates formatted PDF reports including metrics, tables,
    and statistical analysis of PI completion data.
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
        Generate complete PI analysis PDF report.
        
        Args:
            analysis_data (Dict): PI analysis results
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
                author="PI Analysis Tool by Pietro Maffi",
                title="Product Increment Analysis Report",
                subject="PI Completion Metrics and Analysis"
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
            
            # Coaching Recommendations (if available)
            results = analysis_data.get('analysis_results', {})
            if results.get('has_flow_metrics') and results.get('coaching_summary'):
                story.extend(self._create_coaching_recommendations(analysis_data))
            
            # General Recommendations
            story.extend(self._create_recommendations(analysis_data))
            
            # Build PDF with custom canvas function
            def add_page_elements(canvas, doc):
                numbered_canvas = NumberedCanvas(canvas, doc)
                numbered_canvas.draw_page_number_and_footer()
            
            doc.build(story, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
            logger.info(f"✅ PI PDF report generated successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"🚩 PDF generation failed: {str(e)}")
            raise Exception(f"Failed to generate PDF report: {str(e)}")
    
    def _create_title_page(self, data: Dict) -> list:
        """Create title page content."""
        content = []
        
        # Add logo if available
        try:
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
        content.append(Paragraph("Product Increment Analysis Report", self.title_style))
        content.append(Spacer(1, 0.5*inch))
        
        # Get analysis results
        results = data.get('analysis_results', {})
        pi_period = results.get('pi_period', {})
        summary = results.get('summary', {})
        
        # PI Period info
        start_date = pi_period.get('start_date', 'Unknown')
        end_date = pi_period.get('end_date', 'Unknown')
        duration = pi_period.get('duration_days', 0)
        
        content.append(Paragraph(f"PI Period: {start_date} to {end_date}", self.heading_style))
        content.append(Paragraph(f"Duration: {duration} days", self.styles['Normal']))
        content.append(Spacer(1, 0.3*inch))
        
        # Generation info
        generation_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        content.append(Paragraph(f"Generated on: {generation_date}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Summary stats
        total_hours = summary.get('total_estimate_hours', 0)
        total_days = total_hours / 8
        content.append(Paragraph(f"Total Issues Analyzed: {summary.get('total_issues', 0)}", self.styles['Normal']))
        content.append(Paragraph(f"Total Projects: {summary.get('total_projects', 0)}", self.styles['Normal']))
        content.append(Paragraph(f"Total Estimates: {total_days:.1f} days", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Configuration info
        base_project = results.get('base_project', 'ISDOP')
        excluded_projects = results.get('excluded_projects', [])
        content.append(Paragraph(f"Base Project: {base_project}", self.styles['Normal']))
        if excluded_projects:
            content.append(Paragraph(f"Excluded Projects: {', '.join(excluded_projects)}", self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        return content
    
    def _create_executive_summary(self, data: Dict) -> list:
        """Create executive summary section."""
        content = []
        
        content.append(Paragraph("Executive Summary", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        results = data.get('analysis_results', {})
        summary = results.get('summary', {})
        pi_period = results.get('pi_period', {})
        projects = results.get('analyzed_projects', [])
        
        # Key findings summary
        total_days = summary.get('total_estimate_hours', 0) / 8
        summary_text = f"""
        This report analyzes {summary.get('total_issues', 0)} completed issues across {summary.get('total_projects', 0)} projects 
        during the Program Increment from {pi_period.get('start_date', 'unknown')} to {pi_period.get('end_date', 'unknown')}.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • Total Completed Issues: {summary.get('total_issues', 0)}<br/>
        • Total Estimated Days: {total_days:.1f}d<br/>
        • Unestimated Issues: {summary.get('unestimated_percentage', 0):.1f}%<br/>
        • Projects Analyzed: {', '.join(projects[:5])}{'...' if len(projects) > 5 else ''}<br/>
        """
        content.append(Paragraph(summary_text, self.styles['Normal']))
        
        return content
    
    def _create_detailed_analysis(self, data: Dict) -> list:
        """Create detailed analysis section."""
        content = []
        
        content.append(Paragraph("Detailed Analysis", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        results = data.get('analysis_results', {})
        metrics = results.get('metrics', {})
        
        # Issue Type Analysis
        content.append(Paragraph("Issue Type Analysis", self.heading_style))
        
        type_metrics = metrics.get('by_type', {})
        if type_metrics:
            # Create issue type table with shorter headers
            type_data = [['Issue Type', 'Count', 'Est. (d)', 'With Est.', 'No Est.', '% No Est.']]
            
            for issue_type, data in type_metrics.items():
                estimate_days = data['total_estimate_hours'] / 8
                type_data.append([
                    issue_type,
                    str(data['count']),
                    f"{estimate_days:.1f}",
                    str(data['estimated_count']),
                    str(data['unestimated_count']),
                    f"{data['unestimated_percentage']:.1f}%"
                ])
            
            # Use 95% of page width for table
            page_width = A4[0] - 144  # Subtract margins
            table_width = page_width * 0.95
            col_widths = [table_width * 0.25, table_width * 0.12, table_width * 0.15, 
                         table_width * 0.16, table_width * 0.16, table_width * 0.16]
            
            type_table = Table(type_data, colWidths=col_widths)
            
            # Create alternating row colors
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]
            
            # Add alternating row colors
            for i in range(1, len(type_data)):
                if i % 2 == 1:  # Odd rows (1, 3, 5...)
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgreen))
                else:  # Even rows (2, 4, 6...)
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
            
            type_table.setStyle(TableStyle(table_style))
            
            content.append(type_table)
            content.append(Spacer(1, 0.3*inch))
        
        # Project Analysis
        content.append(PageBreak())
        content.append(Paragraph("Project Analysis", self.heading_style))
        
        project_metrics = metrics.get('by_project', {})
        if project_metrics:
            # Create project table
            project_data = [['Project', 'Issues Count', 'Total Estimates (d)']]
            
            for project, data in project_metrics.items():
                estimate_days = data['total_estimate_hours'] / 8
                project_data.append([
                    project,
                    str(data['count']),
                    f"{estimate_days:.1f}"
                ])
            
            # Use 85% of page width for table
            table_width = page_width * 0.85
            col1_width = table_width * 0.4
            col2_width = table_width * 0.3
            col3_width = table_width * 0.3
            
            project_table = Table(project_data, colWidths=[col1_width, col2_width, col3_width])
            
            # Create alternating row colors
            project_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]
            
            # Add alternating row colors
            for i in range(1, len(project_data)):
                if i % 2 == 1:  # Odd rows (1, 3, 5...)
                    project_style.append(('BACKGROUND', (0, i), (-1, i), colors.peachpuff))
                else:  # Even rows (2, 4, 6...)
                    project_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
            
            project_table.setStyle(TableStyle(project_style))
            
            content.append(project_table)
        
        # Flow Metrics Analysis (if available)
        if results.get('has_flow_metrics') and results.get('flow_metrics'):
            content.append(PageBreak())
            content.append(Paragraph("Flow Metrics Analysis", self.heading_style))
            
            flow_metrics = results.get('flow_metrics', {})
            if flow_metrics:
                # Create flow metrics table with shorter headers
                flow_data = [['Project', 'WIP', 'Items/Week', 'Age (d)', 'Cycle (d)', 'Done', 'Total']]
                
                for project, metrics in flow_metrics.items():
                    flow_data.append([
                        project,
                        str(metrics.get('work_in_progress', 0)),
                        str(metrics.get('throughput_per_week', 0)),
                        str(metrics.get('avg_work_item_age_days', 0)),
                        str(metrics.get('avg_cycle_time_days', 0)),
                        str(metrics.get('total_completed', 0)),
                        str(metrics.get('total_issues', 0))
                    ])
                
                # Use 95% of page width for flow metrics table
                flow_table_width = page_width * 0.95
                flow_col_widths = [
                    flow_table_width * 0.25,  # Project
                    flow_table_width * 0.1,   # WIP
                    flow_table_width * 0.15,  # Items/Week
                    flow_table_width * 0.12,  # Age
                    flow_table_width * 0.12,  # Cycle
                    flow_table_width * 0.13,  # Done
                    flow_table_width * 0.13   # Total
                ]
                
                flow_table = Table(flow_data, colWidths=flow_col_widths)
                
                # Create alternating row colors for flow table
                flow_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]
                
                # Add alternating row colors
                for i in range(1, len(flow_data)):
                    if i % 2 == 1:  # Odd rows
                        flow_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightblue))
                    else:  # Even rows
                        flow_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
                
                flow_table.setStyle(TableStyle(flow_style))
                content.append(flow_table)
                
                # Add flow metrics explanation
                content.append(Spacer(1, 0.2*inch))
                flow_explanation = """
                <b>Flow Metrics Explanation:</b><br/>
                • <b>WIP</b>: Work in Progress - Items started but not finished during PI<br/>
                • <b>Throughput/Week</b>: Average number of items completed per week<br/>
                • <b>Avg Age</b>: Average time from start to PI end for WIP items<br/>
                • <b>Avg Cycle Time</b>: Average time from start to completion for finished items<br/>
                • <b>Completed</b>: Number of items completed during PI period<br/>
                • <b>Total Issues</b>: Total items analyzed (completed + WIP)
                """
                content.append(Paragraph(flow_explanation, self.styles['Normal']))
        
        return content
    
    def _create_recommendations(self, data: Dict) -> list:
        """Create recommendations section."""
        content = []
        
        # Add page break before recommendations
        content.append(PageBreak())
        content.append(Paragraph("Recommendations", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        results = data.get('analysis_results', {})
        summary = results.get('summary', {})
        metrics = results.get('metrics', {})
        
        recommendations = []
        
        # Estimation recommendations
        unestimated_pct = summary.get('unestimated_percentage', 0)
        if unestimated_pct > 30:
            recommendations.append(
                f"High percentage of unestimated issues ({unestimated_pct:.1f}%). "
                "Improve estimation practices for better capacity planning."
            )
        elif unestimated_pct > 15:
            recommendations.append(
                f"Moderate percentage of unestimated issues ({unestimated_pct:.1f}%). "
                "Consider estimation workshops for teams."
            )
        
        # Issue type recommendations
        type_metrics = metrics.get('by_type', {})
        bug_count = type_metrics.get('Bug', {}).get('count', 0)
        total_issues = summary.get('total_issues', 1)
        
        if bug_count / total_issues > 0.3:
            recommendations.append(
                f"High bug ratio ({bug_count}/{total_issues} = {bug_count/total_issues*100:.1f}%). "
                "Focus on quality improvement and preventive measures."
            )
        
        # Project distribution recommendations
        project_metrics = metrics.get('by_project', {})
        if len(project_metrics) > 5:
            recommendations.append(
                f"Work distributed across {len(project_metrics)} projects. "
                "Consider consolidation opportunities for better focus."
            )
        
        # Default recommendations if no specific issues found
        if not recommendations:
            recommendations.extend([
                "PI completion metrics appear balanced across issue types and projects.",
                "Continue monitoring estimation accuracy to improve future planning.",
                "Consider implementing regular PI retrospectives to identify improvement opportunities."
            ])
        
        # Add recommendations to content
        for i, rec in enumerate(recommendations, 1):
            content.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
            content.append(Spacer(1, 0.1*inch))
        
        return content
    def _create_coaching_recommendations(self, data: Dict) -> list:
        """Create coaching recommendations section."""
        content = []
        
        content.append(PageBreak())
        content.append(Paragraph("Coaching Recommendations", self.title_style))
        content.append(Spacer(1, 0.2*inch))
        
        results = data.get('analysis_results', {})
        coaching_summary = results.get('coaching_summary', {})
        
        if not coaching_summary:
            return content
        
        # Overall health status
        health = coaching_summary.get('overall_health', 'Unknown')
        critical_count = coaching_summary.get('critical_issues', 0)
        warning_count = coaching_summary.get('warning_issues', 0)
        
        health_color = colors.green if health == 'Healthy' else colors.orange if health == 'Warning' else colors.red
        
        health_text = f"""
        <b>Overall Flow Health: <font color="{health_color.hexval()}">{health}</font></b><br/>
        Total Recommendations: {coaching_summary.get('total_recommendations', 0)} 
        ({critical_count} critical, {warning_count} warnings)
        """
        content.append(Paragraph(health_text, self.styles['Normal']))
        content.append(Spacer(1, 0.3*inch))
        
        # Project-specific recommendations
        all_recommendations = coaching_summary.get('all_recommendations', [])
        if all_recommendations:
            # Group recommendations by project
            project_recs = {}
            for rec in all_recommendations:
                project = rec.get('project', 'Unknown')
                if project not in project_recs:
                    project_recs[project] = []
                project_recs[project].append(rec)
            
            # Create separate section for each project
            for project, recs in project_recs.items():
                content.append(Paragraph(f"{project} Project Issues", self.heading_style))
                
                for rec in recs:
                    severity_color = colors.red if rec['severity'] == 'Critical' else colors.orange
                    severity_icon = "⚠️" if rec['severity'] == 'Critical' else "⚡"
                    
                    rec_text = f"""
                    <b>{severity_icon} {rec.get('metric', '')} - <font color="{severity_color.hexval()}">{rec.get('severity', '')}</font></b><br/>
                    Current Value: {rec.get('current_value', '')} | Recommended Threshold: {rec.get('threshold', '')}<br/>
                    <i>{rec.get('advice', '')}</i>
                    """
                    content.append(Paragraph(rec_text, self.styles['Normal']))
                    content.append(Spacer(1, 0.15*inch))
                
                content.append(Spacer(1, 0.2*inch))
        
        # General flow principles
        general_recs = coaching_summary.get('general_recommendations', [])
        if general_recs:
            content.append(Paragraph("General Flow Principles", self.heading_style))
            
            for rec in general_recs:
                content.append(Paragraph(f"• {rec}", self.styles['Normal']))
                content.append(Spacer(1, 0.05*inch))
        
        return content