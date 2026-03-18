"""
PI Analyzer Flask Application
Web interface for Program Increment analysis.

Author: Pietro Maffi
Version: 2.0.0
Port: 5003
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
import json
from pathlib import Path
from typing import Dict, Optional

# Import shared libraries
from src.common.jira_client import JiraClient
from src.common.cache_manager import CacheManager
from src.common.file_storage import FileStorage
from src.common.flask_utils import (
    validate_jira_credentials,
    handle_errors,
    log_request
)

# Import local modules
from apps.pi_analyzer.analyzer import PIAnalyzer
from apps.pi_analyzer.pdf_generator import PIPDFReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PIAnalyzerApp')

# Initialize Blueprint
blueprint = Blueprint('pi_analyzer', __name__,
                     template_folder='templates',
                     static_folder='static')

# Initialize shared components
cache_manager = CacheManager(cache_dir='data/cache/pi_analyzer', ttl_minutes=30)
file_storage = FileStorage(base_path='data/storage/pi_analyzer')

# Default configuration
DEFAULT_CONFIG = {
    "base_project": "ISDOP",
    "excluded_projects": ["E2ECD", "PPB", "KCCS", "TAISS"],
    "completion_statuses": [
        "Done", "Closed", "Resolved", "PRD Deployed", "Deployed",
        "Released", "Completed", "Cancelled", "Abandonned", "To Validate"
    ],
    "in_progress_statuses": [
        "In Progress", "Doing", "Working", "Development", "Estimation",
        "Work In Progress", "To Test", "Testing", "Code Review",
        "Ready for Development"
    ],
    "issue_types": [
        "Bug", "Analysis", "Configuration", "Defect (Sub-Task)",
        "Documentation", "Epic", "Evolution", "Feature", "Improvement",
        "Incident (Sub-Task)", "Info", "Information", "InvoiceTask",
        "Story", "Sub-Feature", "Sub-task", "Task",
        "Technical Improvement", "Technical subtask", "Technical task"
    ]
}


def load_configuration() -> Dict:
    """
    Load PI analyzer configuration from file or use defaults.
    
    Returns:
        Dict: Configuration dictionary
    """
    try:
        config_path = Path(__file__).parent.parent.parent / 'pi_config.json'
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"📋 Loaded configuration from {config_path}")
            return config
        else:
            logger.warning("⚠️  Config file not found, using defaults")
            return DEFAULT_CONFIG
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse config JSON: {e}")
        return DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        return DEFAULT_CONFIG


def save_analysis_results(cache_key: str, analysis_results: Dict) -> bool:
    """
    Save analysis results to file.
    
    Args:
        cache_key: Unique identifier for the analysis
        analysis_results: Analysis data to save
        
    Returns:
        bool: True if saved successfully
    """
    try:
        data = {
            'results': analysis_results,
            'timestamp': datetime.now().isoformat(),
            'cache_key': cache_key
        }
        file_storage.save_json(f"{cache_key}.json", data)
        logger.info(f"💾 Saved analysis to storage with key: {cache_key}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save analysis: {e}")
        return False


def load_analysis_results(cache_key: str) -> Optional[Dict]:
    """
    Load analysis results from file.
    
    Args:
        cache_key: Unique identifier for the analysis
        
    Returns:
        Optional[Dict]: Analysis data or None if not found
    """
    try:
        data = file_storage.load_json(f"{cache_key}.json")
        if data:
            logger.info(f"📂 Loaded analysis from storage: {cache_key}")
        return data
    except Exception as e:
        logger.error(f"❌ Failed to load analysis: {e}")
        return None


def list_saved_analyses() -> list:
    """
    List all saved analysis files.
    
    Returns:
        list: List of saved analysis summaries
    """
    try:
        analyses = []
        for file_name in file_storage.list_files(pattern='*.json'):
            try:
                data = file_storage.load_json(file_name)
                if data and 'results' in data:
                    results = data['results']
                    pi_period = results.get('pi_period', {})
                    analyses.append({
                        'cache_key': data.get('cache_key', file_name.replace('.json', '')),
                        'start_date': pi_period.get('start_date'),
                        'end_date': pi_period.get('end_date'),
                        'timestamp': data.get('timestamp'),
                        'total_issues': results.get('summary', {}).get('total_issues', 0),
                        'filename': file_name
                    })
            except Exception as e:
                logger.warning(f"⚠️  Skipping invalid file {file_name}: {e}")
        
        return sorted(analyses, key=lambda x: x.get('timestamp', ''), reverse=True)
    except Exception as e:
        logger.error(f"❌ Failed to list analyses: {e}")
        return []


@blueprint.route('/')
@log_request
def index():
    """Main page with input form for PI analysis."""
    config = load_configuration()
    return render_template('index_pi.html', config=config)


@blueprint.route('/analyze_pi', methods=['POST'])
@log_request
@validate_jira_credentials
@handle_errors
def analyze_pi():
    """
    Process PI analysis request.
    
    Returns:
        JSON response with PI analysis results
    """
    # Extract form data
    jira_url = request.form.get('jira_url', '').strip().rstrip('/')
    access_token = request.form.get('access_token', '').strip()
    pi_start_date = request.form.get('pi_start_date', '').strip()
    pi_end_date = request.form.get('pi_end_date', '').strip()
    include_full_backlog = request.form.get('include_full_backlog') == 'on'
    
    # Validate dates
    try:
        datetime.strptime(pi_start_date, '%Y-%m-%d')
        datetime.strptime(pi_end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    logger.info(f"🔗 Starting PI analysis: {pi_start_date} to {pi_end_date}")
    
    # Initialize components
    jira_client = JiraClient(jira_url, access_token)
    pi_analyzer = PIAnalyzer(jira_client, cache_manager)
    
    # Test connection
    if not jira_client.test_connection():
        return jsonify({
            'error': 'Failed to connect to Jira. Please check your URL and token.'
        }), 401
    
    # Perform PI analysis
    analysis_results = pi_analyzer.analyze_pi(
        pi_start_date,
        pi_end_date,
        include_full_backlog
    )
    
    # Add request parameters for PDF generation
    analysis_results.update({
        'jira_url': jira_url,
        'request_date': datetime.now().isoformat()
    })
    
    # Save results to file
    cache_key = f"{pi_start_date}_{pi_end_date}"
    save_analysis_results(cache_key, analysis_results)
    
    logger.info(f"✅ PI analysis completed: {cache_key}")
    
    return jsonify({
        'success': True,
        'analysis_results': analysis_results,
        'cache_key': cache_key
    })


@blueprint.route('/get_cached_results/<cache_key>', methods=['GET'])
@log_request
@handle_errors
def get_cached_results(cache_key: str):
    """
    Retrieve saved analysis results.
    
    Args:
        cache_key: Unique identifier for the analysis
        
    Returns:
        JSON response with cached results
    """
    cached_data = load_analysis_results(cache_key)
    if cached_data:
        return jsonify({
            'success': True,
            'analysis_results': cached_data['results'],
            'cached_at': cached_data['timestamp']
        })
    else:
        return jsonify({'error': 'No saved results found for this key'}), 404


@blueprint.route('/list_cached_results', methods=['GET'])
@log_request
@handle_errors
def list_cached_results():
    """List all available saved results."""
    cached_list = list_saved_analyses()
    return jsonify({'cached_results': cached_list})


@blueprint.route('/get_config', methods=['GET'])
@log_request
@handle_errors
def get_config():
    """Get current PI analyzer configuration."""
    config = load_configuration()
    return jsonify(config)


@blueprint.route('/generate_pi_report', methods=['POST'])
@log_request
@handle_errors
def generate_pi_report():
    """Generate and download PI analysis PDF report."""
    data = request.get_json()
    pdf_generator = PIPDFReportGenerator()
    
    # Generate PDF in temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_generator.generate_report(data, tmp_file.name)
        
        # Create filename with PI dates
        analysis_results = data.get('analysis_results', {})
        pi_period = analysis_results.get('pi_period', {})
        start_date = pi_period.get('start_date', 'unknown')
        end_date = pi_period.get('end_date', 'unknown')
        filename = f'pi_analysis_{start_date}_to_{end_date}.pdf'
        
        return send_file(
            tmp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )


@blueprint.route('/health', methods=['GET'])
@log_request
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'application': 'pi_analyzer',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })


# Blueprint is registered in unified_dashboard - no standalone execution
