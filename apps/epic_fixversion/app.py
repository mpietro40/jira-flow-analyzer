"""
Epic Fix Version Analyzer Flask Application

A Flask-based web application for analyzing epics by fix version across initiatives.
Provides hierarchical traversal through Jira initiatives to identify epic distributions.
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
import tempfile

from src.common.jira_client import JiraClient
from src.common.flask_utils import validate_jira_credentials, handle_errors, log_request
from apps.epic_fixversion.analyzer import EpicFixVersionAnalyzer, save_results_to_file
from apps.epic_fixversion.pdf_generator import EpicFixVersionPDFGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EpicFixVersionApp')

# Initialize Blueprint
blueprint = Blueprint('epic_fixversion', __name__,
                     template_folder='templates',
                     static_folder='static')


@blueprint.route('/')
def index():
    """Main page for epic fix version analysis."""
    return render_template('index_fixversion.html')


@blueprint.route('/analyze', methods=['POST'])
@validate_jira_credentials
@handle_errors
@log_request
def analyze():
    """Process epic fix version analysis request."""
    # Extract form data
    jira_url = request.form.get('jira_url', '').strip()
    access_token = request.form.get('access_token', '').strip()
    initiative_jql = request.form.get('initiative_jql', '').strip()
    fix_version = request.form.get('fix_version', '').strip() or None  # Optional
    excluded_statuses_str = request.form.get('excluded_statuses', '').strip()
    
    # Parse excluded statuses
    excluded_statuses = None
    if excluded_statuses_str:
        excluded_statuses = [s.strip() for s in excluded_statuses_str.split(',') if s.strip()]
    
    # Validate initiative JQL
    if not initiative_jql or not initiative_jql.strip():
        return jsonify({
            'success': False,
            'error': 'Initiative JQL query is required',
            'error_type': 'ValidationError'
        }), 400
    
    logger.info(f"📋 Initiative JQL: {initiative_jql}")
    logger.info(f"🏷️  Fix Version: {fix_version or 'All (no filter)'}")
    logger.info(f"🚫 Excluded Statuses: {excluded_statuses or 'Default'}")
    
    # Initialize Jira client
    jira_client = JiraClient(jira_url, access_token)
    
    # Test connection
    if not jira_client.test_connection():
        return jsonify({
            'success': False,
            'error': 'Failed to connect to Jira. Check URL and token.',
            'error_type': 'ConnectionError'
        }), 401
    
    # Perform analysis
    analyzer = EpicFixVersionAnalyzer(jira_client)
    results = analyzer.analyze(initiative_jql, fix_version, excluded_statuses)
    
    if 'error' in results:
        return jsonify({
            'success': False,
            'error': results['error'],
            'error_type': 'AnalysisError'
        }), 404
    
    # Save results to file
    save_results_to_file(fix_version or 'All', results)
    
    logger.info(f"✅ Analysis complete: {results['total_epics']} epics across {results['total_initiatives']} initiatives")
    
    return jsonify(results)


@blueprint.route('/export_pdf', methods=['POST'])
@handle_errors
@log_request
def export_pdf():
    """Export analysis results to PDF."""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided for PDF generation',
            'error_type': 'ValidationError'
        }), 400
    
    analysis_data = data.get('analysis_data', data)
    jira_url = data.get('jira_url', '')
    
    logger.info("📄 Generating PDF report...")
    
    # Generate PDF
    pdf_generator = EpicFixVersionPDFGenerator()
    pdf_buffer = pdf_generator.generate_report(analysis_data, jira_url=jira_url)
    
    # Create filename
    fix_version = analysis_data.get('fix_version', 'All').replace('/', '_').replace('\\', '_').replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'epic_distribution_{fix_version}_{timestamp}.pdf'
    
    logger.info(f"✅ PDF generated: {filename}")
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@blueprint.route('/favicon.ico')
def favicon():
    """Serve favicon to avoid 404 errors."""
    return '', 204


@blueprint.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'application': 'epic_fixversion',
        'version': '2.0.0',
        'port': 5008,
        'timestamp': datetime.now().isoformat(),
        'service': 'Epic Fix Version Analyzer'
    })


# Alias routes for compatibility with unified dashboard
@blueprint.route('/analyze_epic_fixversion', methods=['POST'])
def analyze_epic_fixversion_alias():
    """Alias for /analyze route (used by unified dashboard integration)."""
    return analyze()


@blueprint.route('/export_epic_fixversion_pdf', methods=['POST'])
def export_epic_fixversion_pdf_alias():
    """Alias for /export_pdf route (used by unified dashboard integration)."""
    return export_pdf()


# Blueprint is registered in unified_dashboard - no standalone execution
