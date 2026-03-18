"""
Jira API Client - Shared Module
Handles connection and data retrieval from Jira servers.

This is the consolidated, production-ready Jira client used by all applications.
"""

import requests
import requests.adapters
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import time

# Import urllib3 with fallback
try:
    from urllib3.util.retry import Retry
except ImportError:
    try:
        from requests.packages.urllib3.util.retry import Retry
    except ImportError:
        Retry = None

# Configure logger
logger = logging.getLogger('JiraClient')

# Default configuration
DEFAULT_MAX_RESULTS = 5000
DEFAULT_BATCH_SIZE = 200
DEFAULT_MIN_BATCH_SIZE = 50
DEFAULT_CONNECT_TIMEOUT = 15
DEFAULT_READ_TIMEOUT = 60


class JiraClient:
    """
    Client for connecting to Jira API and retrieving issue data.
    
    This class handles authentication, API requests, pagination, retries,
    and adaptive timeout handling for robust Jira integration.
    
    Example:
        >>> client = JiraClient("https://company.atlassian.net", "your_token")
        >>> if client.test_connection():
        ...     issues = client.fetch_issues("project = PROJ", max_results=100)
    """
    
    def __init__(self, base_url: str, access_token: str):
        """
        Initialize Jira client with connection details.
        
        Args:
            base_url: Jira server URL (e.g., https://company.atlassian.net)
            access_token: API access token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'PerseusLeadTime/2.0'
        })
        
        # Connection settings
        self.timeout = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.batch_size = DEFAULT_BATCH_SIZE
        self.min_batch_size = DEFAULT_MIN_BATCH_SIZE
        
        # Configure session with retry adapter
        if Retry:
            retry_strategy = Retry(
                total=0,  # We handle retries manually
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
            adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
            self.session.mount('https://', adapter)
            self.session.mount('http://', adapter)
        
        logger.info(f"🔧 JiraClient initialized for {self.base_url}")
    
    def configure_timeouts(self, connect_timeout: Optional[int] = None, read_timeout: Optional[int] = None, 
                          batch_size: Optional[int] = None, min_batch_size: Optional[int] = None):
        """
        Configure timeout and batch size settings.
        
        Args:
            connect_timeout: Connection timeout in seconds
            read_timeout: Read timeout in seconds
            batch_size: Default batch size for queries
            min_batch_size: Minimum batch size when reducing due to timeouts
        """
        if connect_timeout is not None:
            self.timeout = (connect_timeout, self.timeout[1])
        if read_timeout is not None:
            self.timeout = (self.timeout[0], read_timeout)
        if batch_size is not None:
            self.batch_size = batch_size
        if min_batch_size is not None:
            self.min_batch_size = min_batch_size
        
        logger.info(f"🔧 Updated timeouts: connect={self.timeout[0]}s, read={self.timeout[1]}s, batch={self.batch_size}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Jira server with timeout and retry.
        
        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    f'{self.base_url}/rest/api/2/myself',
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info(f"✅ Connected to Jira as {user_info.get('displayName', 'Unknown')}")
                    return True
                elif response.status_code == 401:
                    logger.error("🚩 Authentication failed - invalid token")
                    return False
                elif response.status_code == 403:
                    logger.error("🚩 Access forbidden - insufficient permissions")
                    return False
                else:
                    logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.warning(f"⏰ Connection issue (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"🚩 Connection test failed: {str(e)}")
                return False
                
        logger.error("🚩 Connection test failed after all retries")
        return False
    
    def fetch_issues(self, jql_query: str, max_results: int = DEFAULT_MAX_RESULTS, 
                    start_at: int = 0, fields: Optional[List[str]] = None) -> List[Dict]:
        """
        Fetch issues from Jira using JQL query with adaptive timeout handling.
        
        This method handles pagination, retries, and adaptive batch sizing to
        ensure robust data fetching even from large Jira instances.
        
        Args:
            jql_query: JQL query string
            max_results: Maximum number of results to fetch
            start_at: Starting index for pagination
            fields: Optional list of fields to fetch (uses sensible defaults if None)
            
        Returns:
            List of issue dictionaries with relevant data
        """
        if fields is None:
            fields = [
                'key', 'summary', 'status', 'created', 'resolutiondate',
                'assignee', 'reporter', 'priority', 'issuetype',
                'timeoriginalestimate', 'timeestimate', 'fixVersions',
                'project', 'customfield_10037', 'customfield_10095',
                'customfield_10096', 'customfield_10097', 'comment'
            ]
        
        issues = []
        current_start = start_at
        current_batch_size = self.batch_size
        consecutive_timeouts = 0
        
        logger.info(f"🔍 Fetching issues with JQL: {jql_query}")
        logger.info(f"📊 Target: {max_results} issues, starting at {start_at}")
        
        while len(issues) < max_results:
            batch_success = False
            timeout_occurred = False
            
            # Retry logic for each batch
            for attempt in range(self.max_retries):
                try:
                    params = {
                        'jql': jql_query,
                        'startAt': current_start,
                        'maxResults': min(current_batch_size, max_results - len(issues)),
                        'expand': 'changelog',
                        'fields': ','.join(fields)
                    }
                    
                    logger.debug(f"🔄 Fetching batch at {current_start} (size: {params['maxResults']}, attempt {attempt + 1}/{self.max_retries})")
                    
                    # Use longer timeout for retries
                    current_timeout = (self.timeout[0], self.timeout[1] * (attempt + 1))
                    
                    response = self.session.get(
                        f'{self.base_url}/rest/api/2/search',
                        params=params,
                        timeout=current_timeout
                    )
                    response.raise_for_status()
                    batch_success = True
                    consecutive_timeouts = 0
                    break
                    
                except requests.exceptions.Timeout as e:
                    timeout_occurred = True
                    logger.warning(f"⏰ Timeout on attempt {attempt + 1}/{self.max_retries} (timeout: {current_timeout[1]}s)")
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt) + (attempt * 0.5)
                        logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                        time.sleep(delay)
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"⚠️ Request failed on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
            
            # Handle batch failure with adaptive strategies
            if not batch_success:
                if timeout_occurred:
                    consecutive_timeouts += 1
                    
                    # Reduce batch size on consecutive timeouts
                    if consecutive_timeouts >= 2 and current_batch_size > self.min_batch_size:
                        old_size = current_batch_size
                        current_batch_size = max(self.min_batch_size, current_batch_size // 2)
                        logger.info(f"🔧 Reducing batch size from {old_size} to {current_batch_size}")
                        consecutive_timeouts = 0
                        continue
                    
                    # Skip batch if still failing at minimum size
                    if current_batch_size == self.min_batch_size:
                        logger.warning(f"⏭️ Skipping batch at {current_start}")
                        current_start += self.min_batch_size
                        continue
                
                logger.error(f"🚩 Failed to fetch batch after {self.max_retries} attempts")
                break
            
            # Process successful batch
            if batch_success:
                data = response.json()
                batch_issues = data.get('issues', [])
                
                if not batch_issues:
                    logger.info("📭 No more issues to fetch")
                    break
                
                # Process each issue
                for issue in batch_issues:
                    processed_issue = self._process_issue(issue)
                    if processed_issue:
                        issues.append(processed_issue)
                
                current_start += len(batch_issues)
                
                # Gradually increase batch size back to normal
                if current_batch_size < self.batch_size and consecutive_timeouts == 0:
                    current_batch_size = min(self.batch_size, current_batch_size + 25)
                    logger.debug(f"📈 Increasing batch size to {current_batch_size}")
                
                # Log progress
                total_available = data.get('total', 0)
                logger.info(f"📊 Progress: {len(issues)}/{min(max_results, total_available)} issues")
                
                # Check if we're done
                if current_start >= total_available:
                    break
        
        logger.info(f"✅ Fetched {len(issues)} issues total")
        return issues
    
    def get_issue(self, issue_key: str) -> Optional[Dict]:
        """
        Get a single issue by key.
        
        Args:
            issue_key: Jira issue key (e.g., PROJ-123)
            
        Returns:
            Issue dictionary or None if not found
        """
        try:
            response = self.session.get(
                f'{self.base_url}/rest/api/2/issue/{issue_key}',
                timeout=self.timeout
            )
            response.raise_for_status()
            return self._process_issue(response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"🚩 Failed to fetch issue {issue_key}: {str(e)}")
            return None
    
    def get_epic_children(self, epic_key: str) -> List[Dict]:
        """
        Fetch all issues linked to an epic.
        
        Args:
            epic_key: The key of the epic
            
        Returns:
            List of child issues
        """
        logger.info(f"🔍 Fetching children for epic: {epic_key}")
        jql = f"'Epic Link' = {epic_key}"
        return self.fetch_issues(jql, fields=['key', 'summary', 'status', 'timeoriginalestimate', 'timeestimate'])
    
    def _process_issue(self, issue: Dict) -> Optional[Dict]:
        """
        Process raw Jira issue into simplified format.
        
        Args:
            issue: Raw issue dictionary from Jira API
            
        Returns:
            Processed issue dictionary
        """
        try:
            fields = issue.get('fields', {})
            
            # Extract common fields
            processed = {
                'key': issue.get('key'),
                'summary': fields.get('summary', 'No Summary'),
                'status': fields.get('status', {}).get('name', 'Unknown'),
                'created': fields.get('created'),
                'updated': fields.get('updated'),
                'resolved': fields.get('resolutiondate'),
                'issue_type': fields.get('issuetype', {}).get('name', 'Unknown'),
                'priority': fields.get('priority', {}).get('name', 'Unknown'),
                'project': fields.get('project', {}).get('key', 'Unknown'),
            }
            
            # Extract assignee
            assignee = fields.get('assignee')
            processed['assignee'] = assignee.get('displayName') if assignee else 'Unassigned'
            
            # Extract reporter
            reporter = fields.get('reporter')
            processed['reporter'] = reporter.get('displayName') if reporter else 'Unknown'
            
            # Extract estimates
            processed['original_estimate'] = fields.get('timeoriginalestimate', 0)
            processed['remaining_estimate'] = fields.get('timeestimate', 0)
            
            # Extract fix versions
            fix_versions = fields.get('fixVersions', [])
            processed['fix_versions'] = [fv.get('name') for fv in fix_versions]
            
            # Store raw data for apps that need it
            processed['raw'] = issue
            
            return processed
            
        except Exception as e:
            logger.error(f"🚩 Error processing issue: {str(e)}")
            return None
    
    def search_projects(self) -> List[Dict]:
        """
        Get all projects accessible to the user.
        
        Returns:
            List of project dictionaries
        """
        try:
            response = self.session.get(
                f'{self.base_url}/rest/api/2/project',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"🚩 Failed to fetch projects: {str(e)}")
            return []
    
    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()
        logger.info("🔌 JiraClient session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
