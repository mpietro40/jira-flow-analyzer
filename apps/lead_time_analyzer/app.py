"""
Jira Analytics Web Application
A Flask-based web application for analyzing Jira issue metrics and lead times.

Author: Senior Agile Coach Assistant
Purpose: Analyze Jira data for agile coaching insights
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, render_template, request, jsonify, send_file
import logging
from datetime import datetime, timedelta
import tempfile
import base64
from io import BytesIO

# Import from src.common
from src.common.jira_client import JiraClient

# Import local specialized modules
from apps.lead_time_analyzer.data_analyzer import DataAnalyzer
from apps.lead_time_analyzer.visualization import VisualizationGenerator
from apps.lead_time_analyzer.pdf_generator import PDFReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LeadTimeAnalyzer')

# Create Blueprint instead of Flask app
blueprint = Blueprint('lead_time_analyzer', __name__, 
                     template_folder='templates', 
                     static_folder='static')

@blueprint.route('/')
def index():
    """Main page with input form for Jira connection details."""
    return render_template('index.html')

@blueprint.route('/analyze', methods=['POST'])
def analyze():
    """
    Process Jira data analysis request.
    
    Returns:
        JSON response with analysis results and visualizations
    """
    try:
        # Extract form data
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        time_period = request.form.get('time_period', '3')
        traverse_hierarchy = request.form.get('traverse_hierarchy') == 'on'
        
        # Validate inputs
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize components
        jira_client = JiraClient(jira_url, access_token)
        data_analyzer = DataAnalyzer()
        viz_generator = VisualizationGenerator()
        
        # Check for hierarchical analysis
        if traverse_hierarchy:
            from apps.lead_time_analyzer.hierarchy_analyzer import HierarchyAnalyzer
            hierarchy_analyzer = HierarchyAnalyzer(jira_client)
            
            logger.info(f"🌳 Starting hierarchical analysis with query: {jql_query}")
            analysis_results = hierarchy_analyzer.analyze_hierarchy(jql_query, int(time_period))
            
            if not analysis_results.get('lead_times'):
                return jsonify({'error': 'No issues found in hierarchy traversal'}), 404
            
            # Generate visualizations
            charts = viz_generator.generate_all_charts(analysis_results)
            
            projects = analysis_results.get('projects', [])
            logger.info(f"📤 Sending {len(projects)} projects to frontend: {projects}")
            
            # Debug: Check if comprehensive report exists
            has_report = 'comprehensive_report' in analysis_results
            logger.info(f"📊 Comprehensive report in results: {has_report}")
            if has_report:
                report_keys = list(analysis_results['comprehensive_report'].keys())
                logger.info(f"📊 Report structure: {report_keys}")
            
            return jsonify({
                'success': True,
                'total_issues': analysis_results.get('total_issues', 0),
                'analysis_period': f"{time_period} months",
                'analysis_type': 'hierarchical',
                'hierarchy_metadata': analysis_results.get('hierarchy_metadata', {}),
                'charts': charts,
                'comprehensive_report': analysis_results.get('comprehensive_report', {}),
                'jql_query': jql_query,
                'jira_url': jira_url,
                'metrics': analysis_results['metrics'],
                'projects': projects,
                'people_involvement': analysis_results.get('people_involvement', {})
            })
        else:
            # Standard flat analysis
            logger.info(f"🔗 Fetching data from Jira: {jira_url}")
            issues = jira_client.fetch_issues(jql_query)
            
            if not issues:
                return jsonify({'error': 'No issues found for the given query'}), 404
            
            # Analyze data
            analysis_results = data_analyzer.analyze_issues(issues, int(time_period))
            
            # Generate visualizations
            charts = viz_generator.generate_all_charts(analysis_results)
            
            # Generate comprehensive report
            from apps.lead_time_analyzer.analysis_reporter import AnalysisReporter
            reporter = AnalysisReporter()
            comprehensive_report = reporter.generate_comprehensive_report(analysis_results)
            
            return jsonify({
                'success': True,
                'total_issues': len(issues),
                'analysis_period': f"{time_period} months",
                'analysis_type': 'flat',
                'charts': charts,
                'comprehensive_report': comprehensive_report,
                'jql_query': jql_query,
                'jira_url': jira_url,
                'metrics': analysis_results['metrics'],
                'projects': analysis_results.get('projects', []),
                'people_involvement': analysis_results.get('people_involvement', {})
            })
        
    except Exception as e:
        logger.error(f"🚩 Analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@blueprint.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    """
    Process Jira data analysis from CSV file with issue keys.
    
    Returns:
        JSON response with analysis results and visualizations
    """
    try:
        # Extract form data
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        time_period = request.form.get('time_period', '3')
        include_subtasks = request.form.get('include_subtasks') == 'on'
        
        # Validate inputs
        if not all([jira_url, access_token]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            return jsonify({'error': 'No CSV file uploaded'}), 400
        
        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Initialize components
        jira_client = JiraClient(jira_url, access_token)
        data_analyzer = DataAnalyzer()
        viz_generator = VisualizationGenerator()
        
        # Test connection first
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        # Parse CSV and extract issue keys
        issue_keys = jira_client.parse_csv_for_issue_keys(csv_file)
        if not issue_keys:
            return jsonify({'error': 'No valid issue keys found in CSV'}), 400
        
        logger.info(f"📋 Found {len(issue_keys)} issue keys in CSV")
        
        # Fetch issues by keys
        issues = jira_client.fetch_issues_by_keys(issue_keys, include_subtasks)
        
        if not issues:
            return jsonify({'error': 'No issues found for the provided keys'}), 404
        
        # Analyze data
        analysis_results = data_analyzer.analyze_issues(issues, int(time_period))
        
        # Generate visualizations
        charts = viz_generator.generate_all_charts(analysis_results)
        
        return jsonify({
            'success': True,
            'total_issues': len(issues),
            'csv_issues_found': len(issue_keys),
            'analysis_period': f"{time_period} months",
            'jql_query': f"key in ({', '.join(issue_keys[:10])}{'...' if len(issue_keys) > 10 else ''})",
            'jira_url': jira_url,
            'charts': charts,
            'metrics': analysis_results['metrics'],
            'projects': analysis_results.get('projects', []),
            'people_involvement': analysis_results.get('people_involvement', {})
        })
        
    except Exception as e:
        logger.error(f"🚩 CSV Analysis error: {str(e)}")
        return jsonify({'error': f'CSV Analysis failed: {str(e)}'}), 500

@blueprint.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate and download PDF report."""
    try:
        data = request.get_json()
        pdf_generator = PDFReportGenerator()
        
        # Generate PDF in temporary file
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
        return jsonify({'error': f'⚠️ PDF generation failed: {str(e)}'}), 500

@blueprint.route('/analysis_status', methods=['GET'])
def analysis_status():
    """
    Get status of ongoing hierarchical analysis.
    """
    try:
        jql_query = request.args.get('jql_query')
        months_back = int(request.args.get('months_back', 3))
        
        if not jql_query:
            return jsonify({'error': 'Missing jql_query parameter'}), 400
        
        from apps.lead_time_analyzer.hierarchy_analyzer import HierarchyAnalyzer
        jira_client = JiraClient('dummy', 'dummy')  # Dummy client for status check
        hierarchy_analyzer = HierarchyAnalyzer(jira_client)
        
        status = hierarchy_analyzer.get_analysis_status(jql_query, months_back)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"🚩 Status check error: {str(e)}")
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

# Blueprint is registered in unified_dashboard - no standalone execution