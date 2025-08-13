"""
Jira Analytics Web Application
A Flask-based web application for analyzing Jira issue metrics and lead times.

Author: Senior Agile Coach Assistant
Purpose: Analyze Jira data for agile coaching insights
"""

from flask import Flask, render_template, request, jsonify, send_file
import logging
from datetime import datetime, timedelta
import os
import tempfile
import base64
from io import BytesIO

from jira_client import JiraClient
from data_analyzer import DataAnalyzer
from visualization import VisualizationGenerator
from pdf_generator import PDFReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

@app.route('/')
def index():
    """Main page with input form for Jira connection details."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
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
        time_period = request.form.get('time_period', '3')  # Default to 3 months
        
        # Validate inputs
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize components
        jira_client = JiraClient(jira_url, access_token)
        data_analyzer = DataAnalyzer()
        viz_generator = VisualizationGenerator()
        
        # Fetch and analyze data
        logger.info(f"📊 Fetching data from Jira: {jira_url}")
        issues = jira_client.fetch_issues(jql_query)
        
        if not issues:
            return jsonify({'error': 'No issues found for the given query'}), 404
        
        # Analyze data
        analysis_results = data_analyzer.analyze_issues(issues, int(time_period))
        
        # Generate visualizations
        charts = viz_generator.generate_all_charts(analysis_results)
        
        return jsonify({
            'success': True,
            'total_issues': len(issues),
            'analysis_period': f"{time_period} months",
            'charts': charts,
            'metrics': analysis_results['metrics']
        })
        
    except Exception as e:
        logger.error(f"⚠️ Analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/generate_report', methods=['POST'])
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
        logger.error(f"⚠️ PDF generation error: {str(e)}")
        return jsonify({'error': f'⚠️ PDF generation failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5100)