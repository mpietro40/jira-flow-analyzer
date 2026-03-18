"""
Duplicate Detector Flask Application
Identifies potential duplicate Jira stories using text similarity analysis

Port: 5006
Author: Pietro Maffi
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Blueprint, render_template, request, jsonify, send_file
import logging
from datetime import datetime
import os
import tempfile

# Import shared libraries
from src.common.jira_client import JiraClient
from src.common.flask_utils import validate_jira_credentials, handle_errors, log_request

# Import application modules
from apps.duplicate_detector.detector import DuplicateDetector
from apps.duplicate_detector.pdf_generator import DuplicatePDFReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DuplicateApp')

# Initialize Blueprint
blueprint = Blueprint('duplicate_detector', __name__,
                     template_folder='templates',
                     static_folder='static')

# Configuration
PORT = 5006


@blueprint.route('/')
@handle_errors
@log_request
def index():
    """
    Main page with duplicate detection form.
    
    Returns:
        HTML page with detection form
    """
    return render_template('index_duplicate.html')


@blueprint.route('/analyze_duplicates', methods=['POST'])
@validate_jira_credentials
@handle_errors
@log_request
def analyze_duplicates():
    """
    Process duplicate detection request.
    Analyzes Jira issues for potential duplicates based on text similarity.
    
    Form Parameters:
        jira_url (str): Jira instance URL
        access_token (str): Jira API token
        jql_query (str): JQL query to fetch issues
    
    Returns:
        JSON response with duplicate analysis results
    """
    try:
        # Extract form data
        jira_url = request.form.get('jira_url', '').strip()
        access_token = request.form.get('access_token', '').strip()
        jql_query = request.form.get('jql_query', '').strip()
        
        # Validate inputs
        if not jql_query:
            return jsonify({'error': 'JQL query is required'}), 400
        
        logger.info(f"🔍 Starting duplicate analysis for: {jql_query}")
        
        # Initialize Jira client
        jira_client = JiraClient(jira_url, access_token)
        
        # Test connection
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Check URL and token.'}), 401
        
        logger.info("✅ Connected to Jira successfully")
        
        # Analyze duplicates
        detector = DuplicateDetector(jira_client)
        results = detector.analyze_duplicates(jql_query)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        # Add request metadata
        results.update({
            'jira_url': jira_url,
            'jql_query': jql_query,
            'request_date': datetime.now().isoformat(),
            'analysis_timestamp': datetime.now().isoformat()
        })
        
        # Summary logging
        duplicate_count = results.get('duplicate_count', 0)
        total_issues = results.get('total_issues', 0)
        logger.info(
            f"✅ Duplicate analysis complete: "
            f"{duplicate_count} potential duplicates found in {total_issues} issues"
        )
        
        return jsonify({
            'success': True,
            'analysis_results': results
        })
        
    except Exception as e:
        logger.error(f"🚩 Duplicate analysis error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@blueprint.route('/generate_duplicate_report', methods=['POST'])
@handle_errors
@log_request
def generate_duplicate_report():
    """
    Generate and download duplicate analysis PDF report.
    
    Request Body (JSON):
        analysis_results (dict): Results from duplicate analysis
    
    Returns:
        PDF file download
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No analysis data provided'}), 400
        
        logger.info("📄 Generating duplicate analysis PDF report")
        
        # Initialize PDF generator
        pdf_generator = DuplicatePDFReportGenerator()
        
        # Generate PDF in temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_generator.generate_report(data, tmp_file.name)
            
            # Create filename with timestamp
            filename = f'duplicate_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            
            logger.info(f"✅ PDF report generated: {filename}")
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
    except Exception as e:
        logger.error(f"🚩 PDF generation error: {str(e)}", exc_info=True)
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500


@blueprint.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'application': 'duplicate_detector',
        'version': '2.0.0',
        'port': PORT,
        'timestamp': datetime.now().isoformat()
    })


@blueprint.route('/favicon.ico')
def favicon():
    """Favicon handler."""
    return '', 204


# Blueprint is registered in unified_dashboard - no standalone execution
