"""
Epic Report - Flask Application (Refactored)
Find and analyze parent Epics of Jira issues with child count analysis.

Author: Pietro Maffi
Version: 2.0.0
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, render_template, request, jsonify
import logging
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict
from waitress import serve
import webbrowser
import threading
import argparse

# Import shared utilities
from src.common import (
    JiraClient,
    CacheManager,
    FileStorage,
    validate_jira_credentials,
    handle_errors,
    log_request
)
from src.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EpicReport')

# Configuration
config = get_config()

# Create Blueprint instead of Flask app
blueprint = Blueprint('epic_report', __name__,
                     template_folder='templates',
                     static_folder='static')

# Initialize utilities
cache = CacheManager(cache_dir=os.path.join(config.CACHE_DIR, 'epic_report'))
storage = FileStorage(base_path=os.path.join(config.STORAGE_DIR, 'epic_report'))

# Constants
MAX_JQL_LENGTH = 2000
MAX_RESULTS_LIMIT = 5000
EPIC_LINK_FIELDS = [
    'customfield_10014',  # Common default Epic Link field
    'customfield_10008',  # Alternative Epic Link field
    'parent',             # For next-gen projects
]


class EpicAnalyzer:
    """Analyzes issues to find parent epics and count children."""
    
    def __init__(self, jira_client: JiraClient):
        self.jira_client = jira_client
    
    def find_epic_link_field(self, issue_data: Dict) -> Optional[str]:
        """
        Dynamically find the Epic Link custom field in an issue.
        
        Args:
            issue_data: Issue data from Jira API
            
        Returns:
            Epic key if found, None otherwise
        """
        fields = issue_data.get('fields', {})
        
        # Try common Epic Link fields
        for field_id in EPIC_LINK_FIELDS:
            epic_key = fields.get(field_id)
            if epic_key:
                # Handle different field formats
                if isinstance(epic_key, dict):
                    epic_key = epic_key.get('key')
                if epic_key and isinstance(epic_key, str):
                    logger.debug(f"Found epic link in field {field_id}: {epic_key}")
                    return epic_key
        
        return None
    
    def fetch_epic_details(self, epic_key: str) -> Optional[Dict]:
        """
        Fetch detailed information about an epic.
        
        Args:
            epic_key: Epic issue key
            
        Returns:
            Epic details dictionary
        """
        try:
            response = self.jira_client.session.get(
                f"{self.jira_client.base_url}/rest/api/2/issue/{epic_key}",
                timeout=self.jira_client.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch epic {epic_key}: {response.status_code}")
                return None
            
            data = response.json()
            fields = data.get('fields', {})
            
            return {
                'key': epic_key,
                'summary': fields.get('summary', 'No summary'),
                'status': fields.get('status', {}).get('name', 'Unknown'),
                'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                'project': fields.get('project', {}).get('key', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error fetching epic {epic_key}: {str(e)}")
            return None
    
    def count_epic_children(self, epic_key: str) -> Dict[str, int]:
        """
        Count open and closed children of an epic.
        
        Args:
            epic_key: Epic issue key
            
        Returns:
            Dictionary with open_count and closed_count
        """
        try:
            # Fetch all children of the epic
            jql = f'parent = {epic_key} OR "Epic Link" = {epic_key}'
            children = self.jira_client.fetch_issues(jql, max_results=1000)
            
            open_count = 0
            closed_count = 0
            
            # Define closed statuses
            closed_statuses = ['done', 'closed', 'resolved', 'completed', 'prod deployed']
            
            for child in children:
                status = child.get('fields', {}).get('status', {}).get('name', '').lower()
                if status in closed_statuses:
                    closed_count += 1
                else:
                    open_count += 1
            
            return {
                'open_count': open_count,
                'closed_count': closed_count,
                'total_count': open_count + closed_count
            }
            
        except Exception as e:
            logger.error(f"Error counting children for epic {epic_key}: {str(e)}")
            return {'open_count': 0, 'closed_count': 0, 'total_count': 0}
    
    def analyze_parent_epics(self, issues: List[Dict]) -> Dict:
        """
        Analyze issues to find parent epics and count their children.
        
        Args:
            issues: List of issue dictionaries from Jira
            
        Returns:
            Dictionary with epic analysis results
        """
        epics_dict = {}
        issues_without_epic = []
        
        logger.info(f"Analyzing {len(issues)} issues for parent epics...")
        
        for issue in issues:
            issue_key = issue.get('key')
            epic_key = self.find_epic_link_field(issue)
            
            if epic_key:
                if epic_key not in epics_dict:
                    # First time seeing this epic, fetch details
                    epic_details = self.fetch_epic_details(epic_key)
                    if epic_details:
                        # Count children
                        child_counts = self.count_epic_children(epic_key)
                        epic_details.update(child_counts)
                        epics_dict[epic_key] = epic_details
                        logger.info(f"Found new epic: {epic_key} with {child_counts['total_count']} children")
            else:
                issues_without_epic.append({
                    'key': issue_key,
                    'summary': issue.get('fields', {}).get('summary', 'No summary')
                })
        
        # Convert dict to list and sort by key
        epics_list = sorted(epics_dict.values(), key=lambda x: x['key'])
        
        # Generate CSV of epic keys
        epic_keys_csv = ','.join([epic['key'] for epic in epics_list])
        
        return {
            'epics': epics_list,
            'epic_keys_csv': epic_keys_csv,
            'issues_without_epic': issues_without_epic
        }


# Flask Routes

@blueprint.route('/')
@log_request
def index():
    """Display the main form."""
    return render_template('index_epic.html')


@blueprint.route('/analyze_epics', methods=['POST'])
@log_request
@validate_jira_credentials
@handle_errors
def analyze_epics():
    """
    Analyze issues and find their parent epics.
    
    Retrieves issues from JQL query, finds parent epic for each,
    and returns a report with epic details and child counts.
    """
    # Get form data
    jira_url = request.form['jira_url']
    access_token = request.form['access_token']
    jql_query = request.form.get('jql_query', '').strip()
    
    # Validate JQL length
    if len(jql_query) > MAX_JQL_LENGTH:
        return jsonify({
            'error': 'JQL query too long',
            'error_type': 'ValidationError',
            'error_details': {'suggestion': f'JQL query must be less than {MAX_JQL_LENGTH} characters'}
        }), 400
    
    if not jql_query:
        return jsonify({
            'error': 'JQL query is required',
            'error_type': 'ValidationError',
            'error_details': {'suggestion': 'Please provide a JQL query'}
        }), 400
    
    # Create cache key
    cache_key = f"{jira_url}_{jql_query}"
    
    # Check cache (5 min TTL for this data)
    if cache.is_valid(cache_key, max_age=300):
        logger.info("Using cached epic analysis results")
        cached_data = cache.get(cache_key)
        if cached_data:
            cached_data['cached'] = True
            return jsonify(cached_data)
    
    # Create Jira client
    logger.info(f"Connecting to Jira: {jira_url}")
    client = JiraClient(jira_url, access_token)
    
    if not client.test_connection():
        return jsonify({
            'error': 'Failed to connect to Jira. Please check your URL and access token.',
            'error_type': 'ConnectionError',
            'error_details': {'suggestion': 'Verify your credentials and network connectivity'}
        }), 401
    
    # Fetch issues
    logger.info(f"Fetching issues with JQL: {jql_query}")
    issues = client.fetch_issues(jql_query, max_results=MAX_RESULTS_LIMIT)
    
    if not issues:
        return jsonify({
            'error': 'No issues found for the given JQL query',
            'error_type': 'NotFoundError',
            'error_details': {'suggestion': 'Check your JQL query and permissions'}
        }), 404
    
    logger.info(f"Found {len(issues)} issues, analyzing parent epics...")
    
    # Analyze epics
    analyzer = EpicAnalyzer(client)
    epic_report = analyzer.analyze_parent_epics(issues)
    
    if not epic_report['epics']:
        return jsonify({
            'error': 'No parent epics found for the issues in the query',
            'error_type': 'NotFoundError',
            'error_details': {'suggestion': 'The issues may not have epic links or the epics are not accessible'}
        }), 404
    
    logger.info(f"Analysis complete: {len(epic_report['epics'])} epics found, {len(epic_report['issues_without_epic'])} issues without epics")
    
    # Prepare response
    response_data = {
        'success': True,
        'analysis_date': datetime.now().isoformat(),
        'total_issues_analyzed': len(issues),
        'epic_keys_csv': epic_report['epic_keys_csv'],
        'epics': epic_report['epics'],
        'issues_without_epic': epic_report['issues_without_epic'],
        'summary': {
            'total_epics': len(epic_report['epics']),
            'total_open_children': sum(e['open_count'] for e in epic_report['epics']),
            'issues_without_epic': len(epic_report['issues_without_epic'])
        },
        'cached': False
    }
    
    # Cache the results
    cache.save(cache_key, response_data, metadata={
        'jira_url': jira_url,
        'jql_query': jql_query
    })
    
    return jsonify(response_data)


@blueprint.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'app': 'epic_report',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })


# Blueprint is registered in unified_dashboard - no standalone execution
