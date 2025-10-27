"""
Jira Analytics Suite - Unified Web Application
A Flask-based web application that provides access to all Jira analytics tools.

Author: Pietro Maffi
Purpose: Unified dashboard for all Jira analytics applications
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import logging
from datetime import datetime
import os
import tempfile
import subprocess
import threading
import time
import requests

# Import all existing components
from jira_client import JiraClient
from data_analyzer import DataAnalyzer
from visualization import VisualizationGenerator
from pdf_generator import PDFReportGenerator
from pi_analyzer import PIAnalyzer
from pi_pdf_generator import PIPDFReportGenerator
from sprint_analyzer import SprintAnalyzer
from sprint_pdf_generator import SprintPDFReportGenerator
from presentation_generator import PresentationGenerator
from duplicate_detector import DuplicateDetector
from duplicate_pdf_generator import DuplicatePDFReportGenerator
from report_generator import ReportGenerator
from report_pdf_generator import ReportPDFGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JiraAnalyticsSuite')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jira-analytics-suite-key-change-in-production')

# Store running services
running_services = {}

@app.route('/')
def dashboard():
    """Main dashboard showing all available applications."""
    return render_template('dashboard.html')

@app.route('/lead-time')
def lead_time_analyzer():
    """Lead Time Analyzer application."""
    return render_template('index.html')

@app.route('/pi-analyzer')
def pi_analyzer():
    """PI Analyzer application."""
    return render_template('pi_analyzer.html')

@app.route('/sprint-analyzer')
def sprint_analyzer():
    """Sprint Analyzer application."""
    return render_template('sprint_analyzer.html')

@app.route('/epic-analyzer')
def epic_analyzer():
    """Epic Analyzer application."""
    return render_template('index_epic.html')

@app.route('/psychological-safety')
def psychological_safety():
    """Psychological Safety Analyzer application."""
    return render_template('psychological_safety.html')

@app.route('/analyze_epic_distribution', methods=['POST'])
def analyze_epic_distribution():
    """Analyze epic distribution across projects starting from initiatives."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira'}), 401
        
        from epic_obeya_analyzer import EpicObeyaAnalyzer
        analyzer = EpicObeyaAnalyzer(jira_client)
        results = analyzer.analyze_epic_distribution(jql_query)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Epic distribution analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/analyze_epic_status_validation', methods=['POST'])
def analyze_epic_status_validation():
    """Analyze epics to find those with outdated status."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira'}), 401
        
        from epic_obeya_analyzer import EpicObeyaAnalyzer
        analyzer = EpicObeyaAnalyzer(jira_client)
        results = analyzer.analyze_epic_status_validation(jql_query)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Epic status validation error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/analyze_epics', methods=['POST'])
def analyze_epics():
    """Process Epic analysis request."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira'}), 401
        
        # Import Epic analyzer from standalone app
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from ObeyaEpic import EpicAnalyzer
        
        epics = jira_client.fetch_issues(jql_query, max_results=1000)
        if not epics:
            return jsonify({'error': 'No epics found with the given query'}), 404
        
        epic_analyzer = EpicAnalyzer(jira_client)
        epic_analysis = epic_analyzer.analyze_epics(epics)
        
        # Generate visualizations
        viz_gen = VisualizationGenerator()
        
        # Generate pie chart for epic size distribution
        epic_pie_chart = viz_gen.create_pie_chart(epic_analysis, 'Epic Size Distribution')
        
        # Generate estimate comparison charts
        filtered_epics = [epic for epic in epic_analysis if epic['original_estimate'] > 0 or epic['remaining_estimate'] > 0]
        estimate_charts = []
        
        if filtered_epics:
            chunk_size = 50
            for i in range(0, len(filtered_epics), chunk_size):
                chunk = filtered_epics[i:i + chunk_size]
                epic_names = [epic['key'] for epic in chunk]
                original_estimates = [epic['original_estimate'] for epic in chunk]
                remaining_estimates = [epic['remaining_estimate'] for epic in chunk]
                
                chart_title = f'Epic Progress Comparison ({i+1}-{min(i+chunk_size, len(filtered_epics))})'
                estimate_chart = viz_gen.create_bar_chart(
                    epic_names,
                    [original_estimates, remaining_estimates],
                    chart_title,
                    'Hours',
                    ['Original Estimate', 'Remaining Estimate']
                )
                estimate_charts.append(estimate_chart)
        
        # Convert charts to base64
        import base64
        estimate_charts_b64 = [base64.b64encode(chart.getvalue()).decode('utf-8') for chart in estimate_charts]
        epic_pie_chart_b64 = base64.b64encode(epic_pie_chart.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'epic_analysis': epic_analysis,
            'visualizations': {
                'estimate_charts': estimate_charts_b64,
                'epic_pie_chart': epic_pie_chart_b64
            }
        })
        
    except Exception as e:
        logger.error(f"Epic analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/analyze_safety', methods=['POST'])
def analyze_safety():
    """Process psychological safety analysis request."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        week_year = request.form.get('week_year')
        
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira'}), 401
        
        from psychological_safety_analyzer import PsychologicalSafetyAnalyzer
        analyzer = PsychologicalSafetyAnalyzer(jira_client)
        results = analyzer.analyze_weekly_safety(jql_query, week_year or None)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        return jsonify({
            'success': True,
            'analysis_results': results
        })
        
    except Exception as e:
        logger.error(f"Safety analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/get_trends', methods=['POST'])
def get_trends():
    """Get historical trends for psychological safety indicators."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        weeks_back = int(request.form.get('weeks_back', 12))
        
        if not all([jira_url, access_token]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        from psychological_safety_analyzer import PsychologicalSafetyAnalyzer
        analyzer = PsychologicalSafetyAnalyzer(jira_client)
        
        trends = analyzer.get_safety_trends(weeks_back)
        
        if 'error' in trends:
            return jsonify({'error': trends['error']}), 404
        
        return jsonify({
            'success': True,
            'trends': trends
        })
        
    except Exception as e:
        logger.error(f"Trends analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/duplicate-detector')
def duplicate_detector():
    """Duplicate Story Detector application."""
    return render_template('duplicate_detector.html')

@app.route('/reports')
def reports():
    """Report Generator application."""
    return render_template('report_generator.html')

@app.route('/presentation')
def presentation():
    """Generate presentation."""
    try:
        generator = PresentationGenerator()
        pdf_buffer = generator.generate_presentation()
        
        # Save to doc folder
        doc_dir = os.path.join(os.path.dirname(__file__), 'doc')
        os.makedirs(doc_dir, exist_ok=True)
        output_path = os.path.join(doc_dir, "Jira_Analytics_Suite_Presentation.pdf")
        
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'Jira_Analytics_Suite_Presentation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"🚩 Presentation generation error: {str(e)}")
        return jsonify({'error': f'Presentation generation failed: {str(e)}'}), 500

@app.route('/custom-presentation')
def custom_presentation():
    """Generate custom presentation from JSON config."""
    try:
        from custom_slide_generator import CustomSlideGenerator
        
        generator = CustomSlideGenerator()
        output_path = generator.save_presentation()
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'Custom_Presentation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"🚩 Custom presentation generation error: {str(e)}")
        return jsonify({'error': f'Custom presentation generation failed: {str(e)}'}), 500

# Lead Time Analyzer endpoints
@app.route('/analyze', methods=['POST'])
def analyze():
    """Process Jira data analysis request."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        time_period = request.form.get('time_period', '3')
        traverse_hierarchy = request.form.get('traverse_hierarchy') == 'on'
        
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        data_analyzer = DataAnalyzer()
        viz_generator = VisualizationGenerator()
        
        if traverse_hierarchy:
            from hierarchy_analyzer import HierarchyAnalyzer
            hierarchy_analyzer = HierarchyAnalyzer(jira_client)
            
            logger.info(f"🌳 Starting hierarchical analysis with query: {jql_query}")
            analysis_results = hierarchy_analyzer.analyze_hierarchy(jql_query, int(time_period))
            
            if not analysis_results.get('lead_times'):
                return jsonify({'error': 'No issues found in hierarchy traversal'}), 404
            
            charts = viz_generator.generate_all_charts(analysis_results)
            
            return jsonify({
                'success': True,
                'total_issues': analysis_results.get('total_issues', 0),
                'analysis_period': f"{time_period} months",
                'analysis_type': 'hierarchical',
                'hierarchy_metadata': analysis_results.get('hierarchy_metadata', {}),
                'charts': charts,
                'jql_query': jql_query,
                'jira_url': jira_url,
                'metrics': analysis_results['metrics']
            })
        else:
            logger.info(f"🔗 Fetching data from Jira: {jira_url}")
            issues = jira_client.fetch_issues(jql_query)
            
            if not issues:
                return jsonify({'error': 'No issues found for the given query'}), 404
            
            analysis_results = data_analyzer.analyze_issues(issues, int(time_period))
            charts = viz_generator.generate_all_charts(analysis_results)
            
            return jsonify({
                'success': True,
                'total_issues': len(issues),
                'analysis_period': f"{time_period} months",
                'analysis_type': 'flat',
                'charts': charts,
                'jql_query': jql_query,
                'jira_url': jira_url,
                'metrics': analysis_results['metrics']
            })
        
    except Exception as e:
        logger.error(f"🚩 Analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    """Process CSV analysis request."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        time_period = request.form.get('time_period', '3')
        include_subtasks = request.form.get('include_subtasks') == 'on'
        
        if not all([jira_url, access_token]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if 'csv_file' not in request.files:
            return jsonify({'error': 'No CSV file uploaded'}), 400
        
        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        data_analyzer = DataAnalyzer()
        viz_generator = VisualizationGenerator()
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        issue_keys = jira_client.parse_csv_for_issue_keys(csv_file)
        if not issue_keys:
            return jsonify({'error': 'No valid issue keys found in CSV'}), 400
        
        logger.info(f"📋 Found {len(issue_keys)} issue keys in CSV")
        issues = jira_client.fetch_issues_by_keys(issue_keys, include_subtasks)
        
        if not issues:
            return jsonify({'error': 'No issues found for the provided keys'}), 404
        
        analysis_results = data_analyzer.analyze_issues(issues, int(time_period))
        charts = viz_generator.generate_all_charts(analysis_results)
        
        return jsonify({
            'success': True,
            'total_issues': len(issues),
            'csv_issues_found': len(issue_keys),
            'analysis_period': f"{time_period} months",
            'jql_query': f"key in ({', '.join(issue_keys[:10])}{'...' if len(issue_keys) > 10 else ''})",
            'jira_url': jira_url,
            'charts': charts,
            'metrics': analysis_results['metrics']
        })
        
    except Exception as e:
        logger.error(f"🚩 CSV Analysis error: {str(e)}")
        return jsonify({'error': f'CSV Analysis failed: {str(e)}'}), 500

# PI Analyzer endpoints
@app.route('/analyze_pi', methods=['POST'])
def analyze_pi():
    """Process PI analysis request."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        pi_start_date = request.form.get('pi_start_date')
        pi_end_date = request.form.get('pi_end_date')
        include_full_backlog = request.form.get('include_full_backlog') == 'on'
        
        if not all([jira_url, access_token, pi_start_date, pi_end_date]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            datetime.strptime(pi_start_date, '%Y-%m-%d')
            datetime.strptime(pi_end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        pi_analyzer = PIAnalyzer(jira_client)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        logger.info(f"🔗 Starting PI analysis from {pi_start_date} to {pi_end_date}")
        analysis_results = pi_analyzer.analyze_pi(pi_start_date, pi_end_date, include_full_backlog)
        
        analysis_results.update({
            'jira_url': jira_url,
            'request_date': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'analysis_results': analysis_results
        })
        
    except Exception as e:
        logger.error(f"🚩 PI Analysis error: {str(e)}")
        return jsonify({'error': f'PI Analysis failed: {str(e)}'}), 500

# Sprint Analyzer endpoints
@app.route('/analyze_sprint', methods=['POST'])
def analyze_sprint():
    """Process sprint analysis request."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        sprint_name = request.form.get('sprint_name')
        history_months = int(request.form.get('history_months', 6))
        team_size = int(request.form.get('team_size', 8))
        sprint_days = int(request.form.get('sprint_days', 10))
        hours_per_day = int(request.form.get('hours_per_day', 8))
        completion_statuses = request.form.get('completion_statuses', 'Done,Closed').strip()
        
        if not all([jira_url, access_token, sprint_name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        logger.info(f"🚀 Starting sprint analysis for: {sprint_name}")
        
        jira_client = JiraClient(jira_url, access_token)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        analyzer = SprintAnalyzer(jira_client)
        analyzer.configure_capacity(team_size, sprint_days, hours_per_day)
        analyzer.configure_completion_statuses(completion_statuses)
        
        results = analyzer.analyze_sprint(sprint_name, history_months)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        # Format results for web display (reuse existing function)
        from sprint_web_app import format_results_for_web
        web_results = format_results_for_web(results)
        
        return jsonify({
            'success': True,
            'sprint_name': sprint_name,
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'results': web_results
        })
        
    except Exception as e:
        logger.error(f"🚩 Sprint analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

# PDF Generation endpoints
@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate and download PDF report."""
    try:
        data = request.get_json()
        pdf_generator = PDFReportGenerator()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_generator.generate_report(data, tmp_file.name)
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'jira_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                mimetype='application/pdf'
            )
    except Exception as e:
        logger.error(f"🚩 PDF generation error: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/generate_pi_report', methods=['POST'])
def generate_pi_report():
    """Generate and download PI analysis PDF report."""
    try:
        data = request.get_json()
        pdf_generator = PIPDFReportGenerator()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_generator.generate_report(data, tmp_file.name)
            
            pi_period = data.get('analysis_results', {}).get('pi_period', {})
            start_date = pi_period.get('start_date', 'unknown')
            end_date = pi_period.get('end_date', 'unknown')
            filename = f'pi_analysis_{start_date}_to_{end_date}.pdf'
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
    except Exception as e:
        logger.error(f"🚩 PDF generation error: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Export sprint analysis as PDF report."""
    try:
        data = request.get_json()
        
        if not data or 'results' not in data:
            return jsonify({'error': 'No analysis data provided'}), 400
        
        results = data['results']
        sprint_name = data.get('sprint_name', 'Unknown Sprint')
        jql_queries = data.get('jql_queries', [])
        detailed_logs = data.get('detailed_logs', {})
        
        logger.info(f"📄 Generating PDF report for: {sprint_name}")
        
        pdf_generator = SprintPDFReportGenerator()
        pdf_content = pdf_generator.generate_report(
            results=results,
            sprint_name=sprint_name,
            jql_queries=jql_queries,
            detailed_logs=detailed_logs
        )
        
        filename = f"sprint_analysis_{sprint_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        from flask import Response
        response = Response(
            pdf_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf'
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"🚩 PDF export error: {str(e)}")
        return jsonify({'error': f'PDF export failed: {str(e)}'}), 500

# Duplicate Detector endpoints
@app.route('/analyze_duplicates', methods=['POST'])
def analyze_duplicates():
    """Process duplicate detection request."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        detector = DuplicateDetector(jira_client)
        results = detector.analyze_duplicates(jql_query)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        results.update({
            'jira_url': jira_url,
            'request_date': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'analysis_results': results
        })
        
    except Exception as e:
        logger.error(f"🚩 Duplicate analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/generate_duplicate_report', methods=['POST'])
def generate_duplicate_report():
    """Generate and download duplicate analysis PDF report."""
    try:
        data = request.get_json()
        pdf_generator = DuplicatePDFReportGenerator()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_generator.generate_report(data, tmp_file.name)
            
            filename = f'duplicate_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
    except Exception as e:
        logger.error(f"🚩 PDF generation error: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

# Report Generator endpoints
@app.route('/generate_custom_report', methods=['POST'])
def generate_custom_report():
    """Generate custom report from form data."""
    try:
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        report_title = request.form.get('report_title', 'Jira Report')
        report_size = int(request.form.get('report_size', 100))
        selected_fields = request.form.getlist('display_fields')
        
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not selected_fields:
            return jsonify({'error': 'Please select at least one field to display'}), 400
        
        jira_client = JiraClient(jira_url, access_token)
        report_generator = ReportGenerator(jira_client)
        
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Check URL and token.'}), 401
        
        report_data = report_generator.generate_report(jql_query, selected_fields, report_title, report_size)
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500

@app.route('/export_custom_report', methods=['POST'])
def export_custom_report():
    """Export custom report as PDF."""
    try:
        data = request.get_json()
        report_data = data.get('report')
        
        if not report_data:
            return jsonify({'error': 'No report data provided'}), 400
        
        pdf_generator = ReportPDFGenerator()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_generator.generate_pdf(report_data, tmp_file.name)
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'jira_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                mimetype='application/pdf'
            )
    
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return jsonify({'error': f'PDF export failed: {str(e)}'}), 500

@app.route('/get_available_fields')
def get_available_fields():
    """Get available fields for report generation."""
    try:
        dummy_client = JiraClient('dummy', 'dummy')
        report_generator = ReportGenerator(dummy_client)
        
        fields = report_generator.get_available_fields()
        field_mappings = report_generator.field_mappings
        
        return jsonify({
            'fields': [{'name': field, 'label': field_mappings[field]} for field in fields]
        })
    
    except Exception as e:
        logger.error(f"Error getting fields: {str(e)}")
        return jsonify({'error': 'Failed to get available fields'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Jira Analytics Suite',
        'applications': [
            'Lead Time Analyzer',
            'PI Analyzer', 
            'Sprint Analyzer',
            'Epic Analyzer',
            'Duplicate Detector',
            'Report Generator',
            'Presentation Generator'
        ]
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Jira Analytics Suite - Unified Web Application...")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)