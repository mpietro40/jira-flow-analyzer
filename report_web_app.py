"""
Jira Report Generator Web Application
Flask web app for creating custom Jira reports with modern table display.
"""

from flask import Flask, render_template, request, jsonify, send_file
import logging
import tempfile
from datetime import datetime
from jira_client import JiraClient
from report_generator import ReportGenerator
from report_pdf_generator import ReportPDFGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ReportWebApp')

app = Flask(__name__)
app.secret_key = 'report-generator-key'

@app.route('/')
def index():
    """Main report generator page."""
    return render_template('report_generator.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate report from form data."""
    try:
        # Extract form data
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        report_title = request.form.get('report_title', 'Jira Report')
        selected_fields = request.form.getlist('display_fields')
        
        # Validate inputs
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not selected_fields:
            return jsonify({'error': 'Please select at least one field to display'}), 400
        
        # Initialize components
        jira_client = JiraClient(jira_url, access_token)
        report_generator = ReportGenerator(jira_client)
        
        # Test connection
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Check URL and token.'}), 401
        
        # Generate report
        report_data = report_generator.generate_report(jql_query, selected_fields, report_title)
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Export report as PDF."""
    try:
        data = request.get_json()
        report_data = data.get('report')
        
        if not report_data:
            return jsonify({'error': 'No report data provided'}), 400
        
        # Generate PDF
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
        # Create dummy generator to get available fields
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)