"""
PBC Analyzer Flask Application
Process Behavior Charts for Lead Time Analysis using Statistical Process Control

Port: 5005
Author: Pietro Maffi
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Blueprint, render_template, request, jsonify
import logging
from datetime import datetime
import os
from pathlib import Path
import json

# Import shared libraries
from src.common.jira_client import JiraClient
from src.common.cache_manager import CacheManager
from src.common.file_storage import FileStorage
from src.common.flask_utils import validate_jira_credentials, handle_errors, log_request

# Import application modules
from apps.pbc_analyzer.analyzer import PBCAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PBCApp')

# Initialize Blueprint
blueprint = Blueprint('pbc_analyzer', __name__,
                     template_folder='templates',
                     static_folder='static')

# Configuration
PORT = 5005
CACHE_TTL = 60  # 1 hour cache TTL for PBC analyses (in minutes)

# Initialize shared services
cache_manager = CacheManager(cache_dir='cache/pbc_analyzer', ttl_minutes=CACHE_TTL)
file_storage = FileStorage(base_path='data/pbc_results')


def load_pbc_config():
    """
    Load PBC analyzer configuration from config file.
    
    Returns:
        dict: Configuration with defaults
    """
    try:
        config_path = Path(__file__).parent.parent.parent / 'pbc_config.json'
        
        # Default configuration
        default_config = {
            "start_date": "2024-08-01",
            "default_jql": "project = ISDOP AND type in (Story, Bug, Task) AND resolved is not EMPTY",
            "analysis_description": "Process Behavior Charts help identify trends and special causes in lead time metrics"
        }
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"📋 Loaded PBC configuration from {config_path}")
            return config
        else:
            logger.info(f"📋 Using default PBC configuration")
            return default_config
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse PBC config JSON: {str(e)}")
        return default_config
    except Exception as e:
        logger.error(f"❌ Failed to load PBC configuration: {str(e)}")
        return default_config


@blueprint.route('/')
@handle_errors
@log_request
def index():
    """
    Main page with input form for PBC analysis.
    
    Returns:
        HTML page with analysis form
    """
    config = load_pbc_config()
    return render_template('index_pbc.html', config=config)


@blueprint.route('/analyze_pbc', methods=['POST'])
@validate_jira_credentials
@handle_errors
@log_request
def analyze_pbc():
    """
    Process PBC analysis request.
    Performs statistical process control analysis on lead time metrics.
    
    Form Parameters:
        jira_url (str): Jira instance URL
        access_token (str): Jira API token
        jql_query (str): JQL query to fetch issues
        start_date (str): Start date for analysis (YYYY-MM-DD)
        debug (bool): Enable debug logging
    
    Returns:
        JSON response with PBC analysis results
    """
    try:
        # Extract form data
        jira_url = request.form.get('jira_url', '').strip()
        access_token = request.form.get('access_token', '').strip()
        jql_query = request.form.get('jql_query', '').strip()
        start_date = request.form.get('start_date', '2024-08-01').strip()
        debug = request.form.get('debug') == 'on'
        
        # Validate inputs
        if not jql_query:
            return jsonify({'error': 'JQL query is required'}), 400
        
        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if debug:
            logger.info("🐛 Debug mode enabled")
        
        logger.info(f"🔗 Connecting to Jira: {jira_url}")
        
        # Initialize Jira client
        jira_client = JiraClient(jira_url, access_token)
        
        # Test connection
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Check URL and token.'}), 401
        
        # Check cache first
        cache_key = f"pbc_{hash(jql_query + start_date)}"
        cached_result = cache_manager.get(cache_key)
        
        if cached_result:
            logger.info("✅ Returning cached PBC analysis results")
            return jsonify({
                'success': True,
                'analysis_results': cached_result,
                'cached': True
            })
        
        # Perform analysis
        logger.info(f"🔍 Starting PBC analysis with JQL: {jql_query}")
        pbc_analyzer = PBCAnalyzer(jira_client, debug=debug)
        results = pbc_analyzer.analyze(jql_query, start_date)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        # Generate analysis ID
        analysis_id = f"pbc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results['analysis_id'] = analysis_id
        results['timestamp'] = datetime.now().isoformat()
        
        # Save to cache
        cache_manager.set(cache_key, results)
        
        # Save to persistent storage
        try:
            file_storage.save_json(f"{analysis_id}.json", results)
            logger.info(f"💾 Saved analysis to persistent storage: {analysis_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save to persistent storage: {str(e)}")
        
        # Add metadata to response
        results_summary = results.get('summary', {})
        logger.info(
            f"✅ Analysis complete: "
            f"{results_summary.get('total_projects', 0)} projects, "
            f"{results_summary.get('total_issues', 0)} issues analyzed"
        )
        
        return jsonify({
            'success': True,
            'analysis_results': results,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"🚩 PBC Analysis error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@blueprint.route('/get_cached_results/<analysis_id>', methods=['GET'])
@handle_errors
@log_request
def get_cached_results(analysis_id):
    """
    Load previously saved analysis results by ID.
    
    Args:
        analysis_id (str): Analysis identifier
    
    Returns:
        JSON response with analysis results or error
    """
    try:
        # Try to load from file storage
        data = file_storage.load_json(f"{analysis_id}.json")
        
        if data:
            logger.info(f"✅ Retrieved analysis: {analysis_id}")
            return jsonify({
                'success': True,
                'analysis_results': data
            })
        else:
            return jsonify({'error': 'No saved results found for this ID'}), 404
            
    except Exception as e:
        logger.error(f"❌ Failed to load cached results: {str(e)}")
        return jsonify({'error': str(e)}), 500


@blueprint.route('/list_cached_results', methods=['GET'])
@handle_errors
@log_request
def list_cached_results():
    """
    List all available saved analysis results.
    
    Returns:
        JSON response with list of cached analyses
    """
    try:
        # Get all JSON files from storage
        all_files = file_storage.list_files(pattern='*.json')
        
        analyses = []
        for filename in all_files:
            try:
                data = file_storage.load_json(filename)
                if data:
                    summary = data.get('summary', {})
                    analyses.append({
                        'analysis_id': data.get('analysis_id', filename.replace('.json', '')),
                        'start_date': data.get('start_date'),
                        'timestamp': data.get('timestamp'),
                        'total_projects': summary.get('total_projects', 0),
                        'total_issues': summary.get('total_issues', 0),
                        'filename': filename
                    })
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid file {filename}: {str(e)}")
        
        # Sort by timestamp (newest first)
        analyses.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
        
        logger.info(f"📋 Listed {len(analyses)} cached analyses")
        return jsonify({
            'success': True,
            'cached_results': analyses
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to list analyses: {str(e)}")
        return jsonify({'error': str(e)}), 500


@blueprint.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'application': 'pbc_analyzer',
        'version': '2.0.0',
        'port': PORT
    })


@blueprint.route('/favicon.ico')
def favicon():
    """Favicon handler."""
    return '', 204


# Blueprint is registered in unified_dashboard - no standalone execution
