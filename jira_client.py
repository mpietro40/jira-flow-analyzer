"""
Jira API Client
Handles connection and data retrieval from Jira servers.
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class JiraClient:
    """
    Client for connecting to Jira API and retrieving issue data.
    
    This class handles authentication, API requests, and data parsing
    for Jira issue analysis.
    """
    
    def __init__(self, base_url: str, access_token: str):
        """
        Initialize Jira client with connection details.
        
        Args:
            base_url (str): Jira server URL (e.g., https://company.atlassian.net)
            access_token (str): API access token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """
        Test connection to Jira server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f'{self.base_url}/rest/api/2/myself')
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return False
    
    def fetch_issues(self, jql_query: str, max_results: int = 1000) -> List[Dict]:
        """
        Fetch issues from Jira using JQL query.
        
        Args:
            jql_query (str): JQL query string
            max_results (int): Maximum number of results to fetch
            
        Returns:
            List[Dict]: List of issue dictionaries with relevant data
        """
        issues = []
        start_at = 0
        logger.info(f"🔍 Fetching issues ",jql_query)
        
        while True:
            try:
                # Prepare request parameters
                params = {
                    'jql': jql_query,
                    'startAt': start_at,
                    'maxResults': min(50, max_results - len(issues)),
                    'expand': 'changelog',
                    'fields': 'key,summary,status,created,resolutiondate,assignee,priority,issuetype'
                }
                
                response = self.session.get(
                    f'{self.base_url}/rest/api/2/search',
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                batch_issues = data.get('issues', [])
                
                if not batch_issues:
                    break
                
                # Process each issue to extract relevant data
                for issue in batch_issues:
                    processed_issue = self._process_issue(issue)
                    if processed_issue:
                        issues.append(processed_issue)
                
                start_at += len(batch_issues)
                
                # Check if we've fetched all available issues
                if start_at >= data.get('total', 0) or len(issues) >= max_results:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {str(e)}")
                raise Exception(f"Failed to fetch issues: {str(e)}")
        
        logger.info(f"Fetched {len(issues)} issues from Jira")
        return issues
    
    def _process_issue(self, issue: Dict) -> Optional[Dict]:
        """
        Process raw issue data and extract relevant information.
        
        Args:
            issue (Dict): Raw issue data from Jira API
            
        Returns:
            Optional[Dict]: Processed issue data or None if processing fails
        """
        try:
            # Extract basic issue information
            key = issue['key']
            fields = issue['fields']
            
            processed = {
                'key': key,
                'summary': fields.get('summary', ''),
                'status': fields.get('status', {}).get('name', ''),
                'issue_type': fields.get('issuetype', {}).get('name', ''),
                'priority': fields.get('priority', {}).get('name', ''),
                'created': fields.get('created'),
                'resolution_date': fields.get('resolutiondate'),
                'assignee': fields.get('assignee', {}).get('displayName', '') if fields.get('assignee') else '',
                'status_history': []
            }
            
            # Process changelog for status transitions
            changelog = issue.get('changelog', {})
            if changelog and 'histories' in changelog:
                for history in changelog['histories']:
                    created = history.get('created')
                    for item in history.get('items', []):
                        if item.get('field') == 'status':
                            processed['status_history'].append({
                                'from_status': item.get('fromString', ''),
                                'to_status': item.get('toString', ''),
                                'changed': created
                            })
            
            return processed
            
        except Exception as e:
            logger.warning(f"Failed to process issue {issue.get('key', 'unknown')}: {str(e)}")
            return None