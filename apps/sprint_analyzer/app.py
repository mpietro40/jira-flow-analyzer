"""
Sprint Analyzer Flask Application
Web interface for sprint capacity analysis and forecasting.

Author: Pietro Maffi
Version: 2.0.0
Port: 5004
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Blueprint, render_template, request, jsonify, send_file, send_from_directory
import logging
from datetime import datetime
import tempfile
import os
from typing import Dict

# Import shared libraries
from src.common.jira_client import JiraClient
from src.common.flask_utils import (
    validate_jira_credentials,
    handle_errors,
    log_request
)

# Import local modules
from apps.sprint_analyzer.analyzer import SprintAnalyzer
from apps.sprint_analyzer.pdf_generator import SprintPDFReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SprintAnalyzerApp')

# Initialize Blueprint
blueprint = Blueprint('sprint_analyzer', __name__,
                     template_folder='templates',
                     static_folder='static')


@blueprint.route('/')
@log_request
def index():
    """Main page with sprint analysis form."""
    return render_template('index_sprint.html')


@blueprint.route('/analyze_sprint', methods=['POST'])
@log_request
@validate_jira_credentials
@handle_errors
def analyze_sprint():
    """
    Process sprint analysis request.
    
    Returns:
        JSON response with sprint analysis results
    """
    # Extract form data
    jira_url = request.form.get('jira_url', '').strip().rstrip('/')
    access_token = request.form.get('access_token', '').strip()
    sprint_name = request.form.get('sprint_name', '').strip()
    history_months = int(request.form.get('history_months', 6))
    team_size = int(request.form.get('team_size', 8))
    sprint_days = int(request.form.get('sprint_days', 10))
    hours_per_day = int(request.form.get('hours_per_day', 8))
    completion_statuses = request.form.get('completion_statuses', 'Done,Closed').strip()
    excluded_types = request.form.get('excluded_types', 'Epic').strip()
    
    # Validate sprint name
    if not sprint_name:
        return jsonify({'error': 'Sprint name is required'}), 400
    
    logger.info(f"🚀 Starting sprint analysis: {sprint_name}")
    
    # Initialize components
    jira_client = JiraClient(jira_url, access_token)
    
    # Test connection
    if not jira_client.test_connection():
        return jsonify({
            'error': 'Failed to connect to Jira. Please check your URL and token.'
        }), 401
    
    logger.info("✅ Connected to Jira successfully")
    
    # Configure and analyze sprint
    analyzer = SprintAnalyzer(jira_client)
    analyzer.configure_capacity(team_size, sprint_days, hours_per_day)
    analyzer.configure_completion_statuses(completion_statuses)
    analyzer.configure_excluded_types(excluded_types)
    
    # Perform analysis
    results = analyzer.analyze_sprint(sprint_name, history_months)
    
    # Add metadata for PDF export
    results['request_params'] = {
        'jira_url': jira_url,
        'sprint_name': sprint_name,
        'history_months': history_months,
        'team_size': team_size,
        'sprint_days': sprint_days,
        'hours_per_day': hours_per_day,
        'completion_statuses': completion_statuses,
        'excluded_types': excluded_types,
        'analysis_date': datetime.now().isoformat()
    }
    
    logger.info(f"✅ Sprint analysis completed: {sprint_name}")
    
    return jsonify({
        'success': True,
        'results': results
    })


@blueprint.route('/export_pdf', methods=['POST'])
@log_request
@handle_errors
def export_pdf():
    """
    Generate and download sprint analysis PDF report.
    
    Returns:
        PDF file download
    """
    data = request.get_json()
    
    if not data or 'results' not in data:
        return jsonify({'error': 'No analysis data provided'}), 400
    
    results = data['results']
    sprint_name = results.get('sprint_details', {}).get('name', 'sprint')
    
    # Sanitize sprint name for filename
    safe_sprint_name = "".join(c for c in sprint_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_sprint_name = safe_sprint_name.replace(' ', '_')
    
    logger.info(f"📄 Generating PDF report for: {sprint_name}")
    
    # Generate PDF in temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_generator = SprintPDFReportGenerator()
        pdf_generator.generate_report(results, tmp_file.name)
        
        filename = f'sprint_analysis_{safe_sprint_name}_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return send_file(
            tmp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )


@blueprint.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    return send_from_directory(
        os.path.join(blueprint.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    ) if os.path.exists(os.path.join(blueprint.root_path, 'static', 'favicon.ico')) else ('', 204)


@blueprint.route('/health', methods=['GET'])
@log_request
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'application': 'sprint_analyzer',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })


# Blueprint is registered in unified_dashboard - no standalone execution
