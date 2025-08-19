"""
Jira API Client
Handles connection and data retrieval from Jira servers.
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Configure logger with proper name
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JiraClient')

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
            logger.error(f"🚩 Connection test failed: {str(e)}")
            return False
        
    ## Fetch issues based on JQL query
    ## This method retrieves issues from Jira using a JQL query.
    ## It handles pagination and processes each issue to extract relevant data.
    ## max rows is set to 5000 by default, but can be adjusted.
    ## fetching is done in chunks of 200 to avoid hitting API limits.
    def fetch_issues(self, jql_query: str, max_results: int = 5000) -> List[Dict]:
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
        logger.info(f"🔍 Fetching issues with JQL: {jql_query}")
        
        while True:
            try:
                # Prepare request parameters
                params = {
                    'jql': jql_query,
                    'startAt': start_at,
                    'maxResults': min(200, max_results - len(issues)),
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
                logger.error(f"🚩 API request failed: {str(e)}")
                raise Exception(f"Failed to fetch issues: {str(e)}")
        
        logger.info(f"✅ Fetched {len(issues)} issues from Jira")
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
            logger.warning(f"⚠️ Failed to process issue {issue.get('key', 'unknown')}: {str(e)}")
            return None
        
    # Parse CSV file for issue keys
    def parse_csv_for_issue_keys(self, csv_file) -> List[str]:
        """
        Parse CSV file to extract Jira issue keys.
    
        Args:
            csv_file: Uploaded CSV file object
        
        Returns:
            List[str]: List of valid Jira issue keys
        """
        import csv
        import re
    
        issue_keys = []
        jira_key_pattern = re.compile(r'^[A-Z][A-Z0-9]*-\d+$')
    
        try:
            # Read CSV content
            csv_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(csv_content.splitlines())
        
            # Look for columns that might contain issue keys
            key_columns = []
            if csv_reader.fieldnames:
                for field in csv_reader.fieldnames:
                    if any(keyword in field.lower() for keyword in ['key', 'issue', 'ticket', 'id']):
                        key_columns.append(field)
        
            if not key_columns:
                logger.warning(f"⚠️ No key columns found, using first column")
                key_columns = [csv_reader.fieldnames[0]] if csv_reader.fieldnames else []
        
            logger.info(f"📋 Using columns for issue keys: {key_columns}")
        
            # Extract issue keys
            for row in csv_reader:
                for column in key_columns:
                    value = row.get(column, '').strip().upper()
                    if value and jira_key_pattern.match(value):
                        if value not in issue_keys:  # Avoid duplicates
                            issue_keys.append(value)
                        break  # Found valid key in this row
        
            logger.info(f"✅ Extracted {len(issue_keys)} unique issue keys from CSV")
            return issue_keys
        
        except Exception as e:
            logger.error(f"🚩 Failed to parse CSV: {str(e)}")
            raise Exception(f"CSV parsing failed: {str(e)}")

    def fetch_issues_by_keys(self, issue_keys: List[str], include_subtasks: bool = False) -> List[Dict]:
        """
        Fetch specific issues by their keys.
    
        Args:
            issue_keys (List[str]): List of Jira issue keys
            include_subtasks (bool): Whether to include subtasks and linked issues
        
        Returns:
            List[Dict]: List of issue dictionaries with relevant data
        """
        all_issues = []
    
        logger.info(f"🔍 Attempting to fetch {len(issue_keys)} issue keys")
    
        # Process in batches to avoid URL length limits
        batch_size = 50  # Conservative batch size for key-based queries
    
        for i in range(0, len(issue_keys), batch_size):
            batch_keys = issue_keys[i:i + batch_size]
        
            try:
                # Create JQL for this batch
                keys_str = ','.join(batch_keys)
                jql = f"key in ({keys_str})"
            
                logger.info(f"📦 Fetching batch {i//batch_size + 1}: {len(batch_keys)} keys")
                logger.info(f"🔍 JQL query: {jql}")
            
                # Test the JQL query first with a simple search
                test_response = self.session.get(
                    f'{self.base_url}/rest/api/2/search',
                    params={
                        'jql': jql,
                        'startAt': 0,
                        'maxResults': 1,
                        'fields': 'key'
                    }
                )
                test_response.raise_for_status()
                test_data = test_response.json()
            
                logger.info(f"📊 JQL test result: found {test_data.get('total', 0)} issues")
                if test_data.get('total', 0) == 0:
                    logger.warning(f"⚠️ No issues found for batch: {batch_keys}")
                
                    # Try individual key lookups for debugging
                    for key in batch_keys[:3]:  # Test first 3 keys
                        individual_jql = f"key = {key}"
                        logger.info(f"🔍 Testing individual key: {individual_jql}")
                        individual_response = self.session.get(
                            f'{self.base_url}/rest/api/2/search',
                            params={'jql': individual_jql, 'maxResults': 1, 'fields': 'key'}
                        )
                        if individual_response.status_code == 200:
                            individual_data = individual_response.json()
                            logger.info(f"📊 Individual key {key} result: {individual_data.get('total', 0)} issues")
                        else:
                            logger.warning(f"⚠️ Individual key {key} failed: {individual_response.status_code}")
                    continue
            
                # Fetch this batch using the existing fetch_issues method with correct signature
                batch_issues = self.fetch_issues(jql, max_results=len(batch_keys))
                logger.info(f"✅ Fetched {len(batch_issues)} issues from batch")
                all_issues.extend(batch_issues)
            
                # If including subtasks, fetch related issues
                if include_subtasks:
                    related_issues = self._fetch_related_issues(batch_keys)
                    logger.info(f"🔗 Fetched {len(related_issues)} related issues")
                    all_issues.extend(related_issues)
                
            except Exception as e:
                logger.error(f"🚩 Failed to fetch batch starting at {i}: {str(e)}")
                continue
    
        # Remove duplicates based on key
        seen_keys = set()
        unique_issues = []
        for issue in all_issues:
            if issue['key'] not in seen_keys:
                seen_keys.add(issue['key'])
                unique_issues.append(issue)
    
        logger.info(f"✅ Final result: {len(unique_issues)} unique issues for {len(issue_keys)} requested keys")
        if len(unique_issues) == 0 and len(issue_keys) > 0:
            logger.error("🚩 No issues found! Possible causes:")
            logger.error("🚩 1. Issue keys don't exist in this Jira instance")
            logger.error("🚩 2. User doesn't have permission to view these issues")
            logger.error("🚩 3. Issues are in different projects not accessible with current token")
        
        return unique_issues

    def _fetch_related_issues(self, parent_keys: List[str]) -> List[Dict]:
        """
        Fetch subtasks and linked issues for given parent keys.
    
        Args:
            parent_keys (List[str]): List of parent issue keys
        
        Returns:
            List[Dict]: List of related issues
        """
        related_issues = []
    
        try:
            # Fetch subtasks
            keys_str = ','.join(parent_keys)
            subtask_jql = f"parent in ({keys_str})"
        
            subtasks = self.fetch_issues(subtask_jql, months_back=24, max_results=1000)
            related_issues.extend(subtasks)
        
            logger.info(f"🔗 Found {len(subtasks)} subtasks for parent issues")
        
            # Could also fetch linked issues here if needed
            # linked_jql = f"issue in linkedIssues({keys_str})"
        
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch related issues: {str(e)}")
    
        return related_issues