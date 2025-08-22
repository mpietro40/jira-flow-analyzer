"""
PI (Program Increment) Analysis Application
Analyzes PI metrics for ISDOP project and related projects based on parent/child relationships.

Author: PI Analysis Tool by Pietro Maffi
Purpose: Analyze PI completion metrics across related Jira projects
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from collections import defaultdict

# Reuse existing classes
from jira_client import JiraClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PIAnalyzer')

class PIAnalyzer:
    """
    Analyzes Program Increment (PI) metrics for ISDOP and related projects.
    
    This class discovers related projects through parent/child relationships
    and analyzes completion metrics for different issue types during a PI period.
    """
    
    def __init__(self, jira_client: JiraClient):
        """
        Initialize PI analyzer with Jira client.
        
        Args:
            jira_client (JiraClient): Configured Jira client instance
        """
        self.jira_client = jira_client
        self.base_project = "ISDOP"
        self.completion_statuses = ['Done', 'Closed', 'Resolved']
        self.issue_types = ['Bug', 'Story', 'Sub-task', 'Sub-Feature', 'Feature']
    
    def analyze_pi(self, pi_start_date: str, pi_end_date: str) -> Dict:
        """
        Analyze PI metrics for ISDOP and related projects.
        
        Args:
            pi_start_date (str): PI start date (YYYY-MM-DD format)
            pi_end_date (str): PI end date (YYYY-MM-DD format)
            
        Returns:
            Dict: Complete PI analysis results
        """
        logger.info(f"📊 Starting PI analysis from {pi_start_date} to {pi_end_date}")
        
        # Step 1: Discover related projects
        related_projects = self._discover_related_projects()
        
        # Step 2: Fetch completed issues during PI period
        pi_issues = self._fetch_pi_issues(pi_start_date, pi_end_date, related_projects)
        
        # Step 3: Analyze metrics by issue type
        metrics = self._analyze_pi_metrics(pi_issues)
        
        # Step 4: Create comprehensive report
        report = self._create_pi_report(pi_start_date, pi_end_date, related_projects, metrics)
        
        logger.info("✅ PI analysis completed successfully")
        return report
    
    def _discover_related_projects(self) -> Set[str]:
        """
        For PI analysis, we focus on ISDOP initiatives and their children.
        Project discovery is handled during issue fetching.
        
        Returns:
            Set[str]: Set of related project keys
        """
        logger.info(f"🔍 PI analysis focuses on {self.base_project} initiatives")
        return {self.base_project}
    
    def _get_isdop_initiatives(self) -> List[Dict]:
        """
        Get all Business Initiatives from ISDOP project.
        
        Returns:
            List[Dict]: List of business initiative issues
        """
        logger.info(f"🎯 Fetching business initiatives from ISDOP")
        
        jql_query = 'project = ISDOP AND issuetype = "Business Initiative"'
        
        try:
            initiatives = self.jira_client.fetch_issues(jql_query, max_results=500)
            logger.info(f"📊 Found {len(initiatives)} business initiatives")
            return initiatives
            
        except Exception as e:
            logger.error(f"🚩 Failed to fetch initiatives: {str(e)}")
            return []
    

    
    def _fetch_pi_issues(self, start_date: str, end_date: str, projects: Set[str]) -> List[Dict]:
        """
        Fetch issues completed during PI period using initiative-based approach.
        
        Args:
            start_date (str): PI start date
            end_date (str): PI end date
            projects (Set[str]): Set of project keys to analyze
            
        Returns:
            List[Dict]: List of completed issues during PI
        """
        logger.info(f"📥 Fetching completed issues using initiative-based approach")
        
        all_issues = []
        
        try:
            # Get ISDOP initiatives
            initiatives = self._get_isdop_initiatives()
            
            # For each initiative, get completed child elements in PI period
            for initiative in initiatives:
                initiative_issues = self._fetch_initiative_pi_issues(
                    initiative['key'], start_date, end_date
                )
                all_issues.extend(initiative_issues)
                logger.info(f"📊 Initiative {initiative['key']}: {len(initiative_issues)} completed issues")
            
            # Also get direct ISDOP issues completed in PI period
            direct_issues = self._fetch_direct_project_issues(start_date, end_date)
            all_issues.extend(direct_issues)
            logger.info(f"📊 Direct {self.base_project} issues: {len(direct_issues)} completed")
            
            # Remove duplicates by key
            unique_issues = {issue['key']: issue for issue in all_issues}
            all_issues = list(unique_issues.values())
            
            logger.info(f"✅ Total unique completed issues: {len(all_issues)}")
            return all_issues
            
        except Exception as e:
            logger.error(f"🚩 Failed to fetch PI issues: {str(e)}")
            return []
    
    def _fetch_initiative_pi_issues(self, initiative_key: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch completed child issues for a specific initiative during PI period.
        
        Args:
            initiative_key (str): Business initiative key
            start_date (str): PI start date
            end_date (str): PI end date
            
        Returns:
            List[Dict]: List of completed child issues
        """
        status_list = ','.join(self.completion_statuses)
        
        jql_query = (f'issuekey in childIssuesOf("{initiative_key}") '
                    f'AND resolved >= "{start_date}" '
                    f'AND resolved <= "{end_date}" '
                    f'AND status IN ({status_list})')
        
        logger.debug(f"🔍 Initiative JQL: {jql_query}")
        
        try:
            issues = []
            start_at = 0
            chunk_size = 100
            
            while True:
                chunk_issues = self.jira_client.fetch_issues(
                    jql_query, 
                    max_results=chunk_size, 
                    start_at=start_at
                )
                
                if not chunk_issues:
                    break
                
                # Enhance issues with estimate data
                for issue in chunk_issues:
                    enhanced_issue = self._enhance_issue_with_estimates(issue)
                    if enhanced_issue:
                        issues.append(enhanced_issue)
                
                start_at += len(chunk_issues)
                
                if len(chunk_issues) < chunk_size:
                    break
            
            return issues
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch issues for initiative {initiative_key}: {str(e)}")
            return []
    
    def _fetch_direct_project_issues(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch completed issues directly from ISDOP project.
        
        Args:
            start_date (str): PI start date
            end_date (str): PI end date
            
        Returns:
            List[Dict]: List of completed ISDOP issues
        """
        status_list = ','.join(self.completion_statuses)
        
        jql_query = (f'project = {self.base_project} '
                    f'AND resolved >= "{start_date}" '
                    f'AND resolved <= "{end_date}" '
                    f'AND status IN ({status_list})')
        
        try:
            issues = []
            start_at = 0
            chunk_size = 100
            
            while True:
                chunk_issues = self.jira_client.fetch_issues(
                    jql_query, 
                    max_results=chunk_size, 
                    start_at=start_at
                )
                
                if not chunk_issues:
                    break
                
                # Enhance issues with estimate data
                for issue in chunk_issues:
                    enhanced_issue = self._enhance_issue_with_estimates(issue)
                    if enhanced_issue:
                        issues.append(enhanced_issue)
                
                start_at += len(chunk_issues)
                
                if len(chunk_issues) < chunk_size:
                    break
            
            return issues
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch direct {self.base_project} issues: {str(e)}")
            return []
    
    def _enhance_issue_with_estimates(self, issue: Dict) -> Optional[Dict]:
        """
        Enhance issue with estimate information.
        
        Args:
            issue (Dict): Basic issue data
            
        Returns:
            Optional[Dict]: Enhanced issue with estimate data
        """
        try:
            # Fetch detailed issue data
            response = self.jira_client.session.get(
                f"{self.jira_client.base_url}/rest/api/2/issue/{issue['key']}",
                params={'fields': 'timeoriginalestimate,issuetype,project,resolution,resolutiondate'}
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Could not fetch estimate data for {issue['key']}")
                return issue
            
            detailed_data = response.json()
            fields = detailed_data.get('fields', {})
            
            # Extract relevant data
            original_estimate_seconds = fields.get('timeoriginalestimate') or 0
            original_estimate_hours = original_estimate_seconds / 3600
            
            issue.update({
                'original_estimate_hours': original_estimate_hours,
                'has_estimate': original_estimate_seconds > 0,
                'project_key': fields.get('project', {}).get('key', ''),
                'issue_type_name': fields.get('issuetype', {}).get('name', ''),
                'resolution_date': fields.get('resolutiondate')
            })
            
            return issue
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance issue {issue.get('key', 'unknown')}: {str(e)}")
            return issue
    
    def _analyze_pi_metrics(self, issues: List[Dict]) -> Dict:
        """
        Analyze PI metrics by issue type.
        
        Args:
            issues (List[Dict]): List of completed issues
            
        Returns:
            Dict: PI metrics analysis
        """
        logger.info(f"📊 Analyzing metrics for {len(issues)} issues")
        
        # Initialize metrics structure
        metrics = {
            'total_issues': len(issues),
            'by_type': defaultdict(lambda: {
                'count': 0,
                'total_estimate_hours': 0,
                'estimated_count': 0,
                'unestimated_count': 0,
                'unestimated_percentage': 0
            }),
            'by_project': defaultdict(lambda: {
                'count': 0,
                'total_estimate_hours': 0
            }),
            'summary': {
                'total_estimate_hours': 0,
                'total_estimated_issues': 0,
                'total_unestimated_issues': 0,
                'overall_unestimated_percentage': 0
            }
        }
        
        # Analyze each issue
        for issue in issues:
            issue_type = issue.get('issue_type_name', 'Unknown')
            project_key = issue.get('project_key', 'Unknown')
            estimate_hours = issue.get('original_estimate_hours', 0)
            has_estimate = issue.get('has_estimate', False)
            
            # Update type metrics
            type_metrics = metrics['by_type'][issue_type]
            type_metrics['count'] += 1
            type_metrics['total_estimate_hours'] += estimate_hours
            
            if has_estimate:
                type_metrics['estimated_count'] += 1
                metrics['summary']['total_estimated_issues'] += 1
            else:
                type_metrics['unestimated_count'] += 1
                metrics['summary']['total_unestimated_issues'] += 1
            
            # Update project metrics
            project_metrics = metrics['by_project'][project_key]
            project_metrics['count'] += 1
            project_metrics['total_estimate_hours'] += estimate_hours
            
            # Update summary
            metrics['summary']['total_estimate_hours'] += estimate_hours
        
        # Calculate percentages
        for issue_type, type_metrics in metrics['by_type'].items():
            if type_metrics['count'] > 0:
                type_metrics['unestimated_percentage'] = (
                    type_metrics['unestimated_count'] / type_metrics['count'] * 100
                )
        
        # Calculate overall percentage
        if metrics['total_issues'] > 0:
            metrics['summary']['overall_unestimated_percentage'] = (
                metrics['summary']['total_unestimated_issues'] / metrics['total_issues'] * 100
            )
        
        # Log summary
        logger.info(f"📈 Analysis complete:")
        logger.info(f"  📊 Total issues: {metrics['total_issues']}")
        logger.info(f"  ⏱️ Total estimates: {metrics['summary']['total_estimate_hours']:.1f}h")
        logger.info(f"  📋 Estimated issues: {metrics['summary']['total_estimated_issues']}")
        logger.info(f"  ❓ Unestimated: {metrics['summary']['total_unestimated_issues']} ({metrics['summary']['overall_unestimated_percentage']:.1f}%)")
        
        return dict(metrics)
    
    def _create_pi_report(self, start_date: str, end_date: str, projects: Set[str], metrics: Dict) -> Dict:
        """
        Create comprehensive PI analysis report.
        
        Args:
            start_date (str): PI start date
            end_date (str): PI end date
            projects (Set[str]): Analyzed projects
            metrics (Dict): Analysis metrics
            
        Returns:
            Dict: Complete PI report
        """
        # Get actual projects from the metrics (where issues were found)
        actual_projects = list(metrics.get('by_project', {}).keys())
        
        return {
            'pi_period': {
                'start_date': start_date,
                'end_date': end_date,
                'duration_days': (datetime.strptime(end_date, '%Y-%m-%d') - 
                                datetime.strptime(start_date, '%Y-%m-%d')).days
            },
            'analyzed_projects': sorted(actual_projects),
            'base_project': self.base_project,
            'analysis_date': datetime.now().isoformat(),
            'metrics': metrics,
            'summary': {
                'total_projects': len(actual_projects),
                'total_issues': metrics['total_issues'],
                'total_estimate_hours': metrics['summary']['total_estimate_hours'],
                'unestimated_percentage': metrics['summary']['overall_unestimated_percentage']
            }
        }