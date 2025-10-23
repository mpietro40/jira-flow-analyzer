"""
Duplicate Story Detector Web Application
A Flask-based web interface for detecting duplicate Jira stories.

Author: Pietro Maffi
Purpose: Web interface for duplicate story detection
"""

from flask import Flask, render_template, request, jsonify, send_file
import logging
from datetime import datetime
import os
import tempfile

from jira_client import JiraClient
from duplicate_detector import DuplicateDetector
from duplicate_pdf_generator import DuplicatePDFReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DuplicateWebApp')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'duplicate-detector-key-change-in-production')

@app.route('/')
def index():
    """Main page with duplicate detection form."""
    return render_template('duplicate_detector.html')

@app.route('/analyze_duplicates', methods=['POST'])
def analyze_duplicates():
    """
    Process duplicate detection request.
    
    Returns:
        JSON response with duplicate analysis results
    """
    try:
        # Extract form data
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        jql_query = request.form.get('jql_query')
        
        # Validate inputs
        if not all([jira_url, access_token, jql_query]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        logger.info(f"🚀 Starting duplicate analysis for: {jql_query}")
        
        # Initialize components
        jira_client = JiraClient(jira_url, access_token)
        
        # Test connection
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        logger.info("✅ Connected to Jira successfully")
        
        # Analyze duplicates
        detector = DuplicateDetector(jira_client)
        results = detector.analyze_duplicates(jql_query)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        # Add request parameters for PDF generation
        results.update({
            'jira_url': jira_url,
            'request_date': datetime.now().isoformat()
        })
        
        logger.info("✅ Duplicate analysis completed successfully")
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
        
        # Generate PDF in temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_generator.generate_report(data, tmp_file.name)
            
            # Create filename with timestamp
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

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Duplicate Story Detector'
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Duplicate Story Detector Web Application...")
    app.run(debug=True, host='0.0.0.0', port=5400)