"""
PI Analysis Web Application
Flask-based web application for analyzing Program Increment metrics.

Author: PI Analysis Tool by Pietro Maffi
Purpose: Web interface for PI analysis with PDF export
"""

from flask import Flask, render_template, request, jsonify, send_file
import logging
from datetime import datetime
import os
import tempfile

from jira_client import JiraClient
from pi_analyzer import PIAnalyzer
from pi_pdf_generator import PIPDFReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PIWebApp')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pi-analysis-key-change-in-production')

@app.route('/')
def index():
    """Main page with input form for PI analysis."""
    return render_template('pi_analyzer.html')

@app.route('/analyze_pi', methods=['POST'])
def analyze_pi():
    """
    Process PI analysis request.
    
    Returns:
        JSON response with PI analysis results
    """
    try:
        # Extract form data
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        pi_start_date = request.form.get('pi_start_date')
        pi_end_date = request.form.get('pi_end_date')
        include_full_backlog = request.form.get('include_full_backlog') == 'on'
        
        # Validate inputs
        if not all([jira_url, access_token, pi_start_date, pi_end_date]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate date format
        try:
            datetime.strptime(pi_start_date, '%Y-%m-%d')
            datetime.strptime(pi_end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Initialize components
        jira_client = JiraClient(jira_url, access_token)
        pi_analyzer = PIAnalyzer(jira_client)
        
        # Test connection
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        logger.info(f"🔗 Starting PI analysis from {pi_start_date} to {pi_end_date}")
        
        # Perform PI analysis
        analysis_results = pi_analyzer.analyze_pi(pi_start_date, pi_end_date, include_full_backlog)
        
        # Add request parameters for PDF generation
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

@app.route('/generate_pi_report', methods=['POST'])
def generate_pi_report():
    """Generate and download PI analysis PDF report."""
    try:
        data = request.get_json()
        pdf_generator = PIPDFReportGenerator()
        
        # Generate PDF in temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_generator.generate_report(data, tmp_file.name)
            
            # Create filename with PI dates
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5300)