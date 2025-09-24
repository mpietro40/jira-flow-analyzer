"""
Jira Report Generator
Creates customizable reports from Jira data with modern table formatting.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from jira_client import JiraClient
from pi_cache import PICache

logger = logging.getLogger('ReportGenerator')

class ReportGenerator:
    """
    Generates customizable reports from Jira data.
    """
    
    def __init__(self, jira_client: JiraClient):
        """
        Initialize report generator.
        
        Args:
            jira_client (JiraClient): Configured Jira client
        """
        self.jira_client = jira_client
        self.cache = PICache(cache_ttl_minutes=30)
        
        # Default field mappings for display
        self.field_mappings = {
            'key': 'Issue Key',
            'summary': 'Summary',
            'status': 'Status',
            'assignee': 'Assignee',
            'priority': 'Priority',
            'issue_type': 'Type',
            'created': 'Created',
            'resolutiondate': 'Resolved',
            'project_key': 'Project'
        }
    
    def generate_report(self, jql_query: str, display_fields: List[str], 
                       report_title: str = "Jira Report", report_size: int = 1000) -> Dict:
        """
        Generate report from JQL query.
        
        Args:
            jql_query (str): JQL query string
            display_fields (List[str]): Fields to display in report
            report_title (str): Report title
            report_size (int): Maximum number of issues to include
            
        Returns:
            Dict: Report data with formatted table
        """
        logger.info(f"📊 Generating report: {report_title}")
        
        # Fetch issues with cache
        issues = self._fetch_issues_with_cache(jql_query, max_results=report_size)
        
        # Limit results to report size
        if len(issues) > report_size:
            issues = issues[:report_size]
        
        if not issues:
            return {
                'title': report_title,
                'query': jql_query,
                'total_issues': 0,
                'headers': [],
                'rows': [],
                'generated_at': datetime.now().isoformat()
            }
        
        # Process issues for display
        headers = [self.field_mappings.get(field, field.title()) for field in display_fields]
        rows = []
        
        for issue in issues:
            row = []
            for field in display_fields:
                value = self._extract_field_value(issue, field)
                row.append(value)
            rows.append(row)
        
        report_data = {
            'title': report_title,
            'query': jql_query,
            'total_issues': len(issues),
            'headers': headers,
            'rows': rows,
            'field_names': display_fields,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Report generated: {len(issues)} issues, {len(display_fields)} columns")
        return report_data
    
    def _fetch_issues_with_cache(self, jql_query: str, max_results: int = 1000) -> List[Dict]:
        """
        Fetch issues with caching.
        
        Args:
            jql_query (str): JQL query string
            max_results (int): Maximum results
            
        Returns:
            List[Dict]: Issues from cache or fresh fetch
        """
        cached_issues = self.cache.get_cached_issues(jql_query, max_results)
        if cached_issues is not None:
            return cached_issues
        
        logger.info("🔄 Fetching fresh data from Jira...")
        issues = self.jira_client.fetch_issues(jql_query, max_results)
        self.cache.cache_issues(jql_query, issues, max_results)
        
        return issues
    
    def _extract_field_value(self, issue: Dict, field: str) -> str:
        """
        Extract and format field value from issue.
        
        Args:
            issue (Dict): Issue data
            field (str): Field name
            
        Returns:
            str: Formatted field value
        """
        if field == 'assignee':
            assignee = issue.get('assignee')
            if isinstance(assignee, dict):
                return assignee.get('displayName', 'Unassigned')
            elif isinstance(assignee, str):
                return assignee if assignee else 'Unassigned'
            return 'Unassigned'
        
        elif field == 'priority':
            priority = issue.get('priority')
            if isinstance(priority, dict):
                return priority.get('name', 'None')
            elif isinstance(priority, str):
                return priority if priority else 'None'
            return 'None'
        
        elif field == 'issue_type':
            issue_type = issue.get('issue_type') or issue.get('issuetype')
            if isinstance(issue_type, dict):
                return issue_type.get('name', 'Unknown')
            return str(issue_type) if issue_type else 'Unknown'
        
        elif field == 'project_key':
            key = issue.get('key', '')
            return key.split('-')[0] if key and '-' in key else 'Unknown'
        
        elif field in ['created', 'resolutiondate']:
            date_str = issue.get(field)
            if date_str and isinstance(date_str, str):
                try:
                    if 'T' in date_str:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        return date_obj.strftime('%Y-%m-%d')
                    else:
                        return date_str[:10] if len(date_str) >= 10 else date_str
                except:
                    return date_str[:10] if len(date_str) >= 10 else date_str
            return 'N/A'
        
        else:
            value = issue.get(field, 'N/A')
            return str(value) if value is not None else 'N/A'
    
    def get_available_fields(self) -> List[str]:
        """
        Get list of available fields for reports.
        
        Returns:
            List[str]: Available field names
        """
        return list(self.field_mappings.keys())