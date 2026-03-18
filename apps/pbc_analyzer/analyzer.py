"""
Process Behavior Charts (PBC) Analyzer
Analyzes lead time trends and variations using statistical process control.

Based on: https://www.infoq.com/articles/DORA-metrics-PBCs/
Author: Pietro Maffi
Purpose: Identify trends, spikes, and process stability in lead time metrics
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import statistics

from src.common.jira_client import JiraClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PBCAnalyzer')


class PBCAnalyzer:
    """
    Analyzes lead time data to create Process Behavior Charts.
    Calculates control limits and identifies special cause variations.
    """
    
    def __init__(self, jira_client: JiraClient, debug: bool = False):
        """
        Initialize PBC analyzer with Jira client.
        
        Args:
            jira_client (JiraClient): Configured Jira client instance
            debug (bool): Enable debug logging for queries
        """
        self.jira_client = jira_client
        self.debug = debug
        
        # Issue types to include in hierarchy traversal (like hierarchy_analyzer)
        self.hierarchy_issue_types = [
            "Business Initiative", "Feature", "Sub-Feature", "Epic",
            "Story", "Bug", "Task", "Sub-task", "Technical task",
            "Improvement", "Technical Improvement"
        ]
        
        if self.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("🐛 Debug mode enabled for PBC Analyzer")
    
    def analyze(self, jql_query: str, start_date: str = "2024-08-01") -> Dict:
        """
        Perform Process Behavior Chart analysis on issues from JQL query.
        Discovers related projects through parent/child relationships.
        
        Args:
            jql_query (str): JQL query to fetch issues
            start_date (str): Start date for analysis (default: August 2024)
            
        Returns:
            Dict: Analysis results with PBC data per project
        """
        logger.info(f"🔍 Starting PBC analysis from {start_date}")
        logger.info(f"📋 Initial JQL Query: {jql_query}")
        
        if self.debug:
            logger.debug(f"🐛 Executing initial query: {jql_query}")
        
        # Fetch initial issues (Business Initiatives)
        initial_issues = self.jira_client.fetch_issues(jql_query, max_results=1000)
        
        if not initial_issues:
            return {'error': 'No issues found for the given query'}
        
        logger.info(f"📊 Found {len(initial_issues)} initial issues (Business Initiatives)")
        
        # Traverse full hierarchy for each initiative to get all child issues
        all_issues = self._traverse_full_hierarchy(initial_issues)
        
        if not all_issues:
            return {'error': 'No issues found in hierarchy traversal'}
        
        logger.info(f"📊 Total issues after hierarchy traversal: {len(all_issues)}")
        
        # Discover all projects from the issues
        projects = set()
        for issue in all_issues:
            project = issue['fields'].get('project', {}).get('key')
            if project:
                projects.add(project)
        
        logger.info(f"🔗 Discovered {len(projects)} projects from hierarchy: {sorted(projects)}")
        
        # Filter issues resolved after start_date
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        filtered_issues = []
        
        for issue in all_issues:
            resolved = issue['fields'].get('resolutiondate')
            if resolved:
                try:
                    resolved_dt = datetime.fromisoformat(resolved.replace('Z', '+00:00')).replace(tzinfo=None)
                    if resolved_dt >= start_dt:
                        filtered_issues.append(issue)
                except Exception:
                    continue
        
        logger.info(f"📊 {len(filtered_issues)} issues resolved after {start_date}")
        
        if not filtered_issues:
            return {'error': f'No issues found with resolution date >= {start_date}'}
        
        logger.info(f"📊 Analyzing {len(filtered_issues)} total issues from all related projects")
        
        # Calculate lead times and group by project and month
        project_data = self._calculate_lead_times_by_project(filtered_issues, start_date)
        
        # Calculate PBC metrics for each project
        pbc_results = {}
        for project, monthly_data in project_data.items():
            pbc_results[project] = self._calculate_pbc_metrics(project, monthly_data)
        
        # Generate overall summary
        summary = self._generate_summary(pbc_results, start_date)
        
        return {
            'success': True,
            'start_date': start_date,
            'analysis_date': datetime.now().isoformat(),
            'total_issues': len(filtered_issues),
            'projects': list(project_data.keys()),
            'pbc_results': pbc_results,
            'summary': summary,
            'jql_query': jql_query
        }
    
    def _traverse_full_hierarchy(self, initiatives: List[Dict]) -> List[Dict]:
        """
        Traverse the full Jira hierarchy starting from Business Initiatives.
        Gets all child issues: Features → Sub-Features → Epics → Stories/Tasks/Bugs
        
        Args:
            initiatives (List[Dict]): List of Business Initiative issues
            
        Returns:
            List[Dict]: All issues in the hierarchy
        """
        all_issues = []
        
        logger.info(f"🌳 Starting hierarchy traversal for {len(initiatives)} initiatives")
        
        for i, initiative in enumerate(initiatives, 1):
            initiative_key = initiative['key']
            logger.info(f"🔍 [{i}/{len(initiatives)}] Processing initiative: {initiative_key}")
            
            try:
                # Get all child issues using childIssuesOf() - this recursively gets everything
                child_issues = self._get_all_child_issues(initiative_key)
                
                # Add the initiative itself
                all_issues.append(initiative)
                
                # Add all child issues
                all_issues.extend(child_issues)
                
                logger.info(f"  ✓ Found {len(child_issues)} child issues under {initiative_key}")
                
            except Exception as e:
                logger.error(f"  ✗ Failed to process {initiative_key}: {str(e)}")
                continue
        
        # Remove duplicates by issue key
        unique_issues = {issue['key']: issue for issue in all_issues}
        final_issues = list(unique_issues.values())
        
        logger.info(f"✅ Hierarchy traversal complete: {len(final_issues)} unique issues")
        
        return final_issues
    
    def _get_all_child_issues(self, initiative_key: str) -> List[Dict]:
        """
        Get all child issues for an initiative using childIssuesOf() JQL function.
        This recursively gets Features, Sub-Features, Epics, Stories, Tasks, etc.
        
        Args:
            initiative_key (str): Parent issue key
            
        Returns:
            List[Dict]: All child issues
        """
        issue_type_list = ','.join([f'"{issue_type}"' for issue_type in self.hierarchy_issue_types])
        
        jql_query = (f'issuekey in childIssuesOf("{initiative_key}") '
                    f'AND issuetype IN ({issue_type_list})')
        
        if self.debug:
            logger.debug(f"🐛 Fetching children with JQL: {jql_query}")
        
        try:
            child_issues = self.jira_client.fetch_issues(jql_query, max_results=5000)
            return child_issues
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch child issues for {initiative_key}: {str(e)}")
            return []
    
    def _discover_related_projects(self, initial_issues: List[Dict]) -> set:
        """
        Discover all related projects through parent/child issue relationships.
        
        Args:
            initial_issues (List[Dict]): Initial issues from query
            
        Returns:
            set: Set of related project keys
        """
        projects = set()
        issue_keys_to_explore = set()
        
        # Extract projects and parent keys from initial issues
        for issue in initial_issues:
            project = issue['fields'].get('project', {}).get('key')
            if project:
                projects.add(project)
            
            # Check for parent (epic link, parent issue)
            parent = issue['fields'].get('parent', {}).get('key')
            if parent:
                issue_keys_to_explore.add(parent)
            
            # Check for epic link
            epic_link = issue['fields'].get('customfield_10014')  # Epic Link field
            if epic_link:
                issue_keys_to_explore.add(epic_link)
            
            # Check for issue links (blocks, relates, etc.)
            issue_links = issue['fields'].get('issuelinks', [])
            for link in issue_links:
                if 'outwardIssue' in link:
                    issue_keys_to_explore.add(link['outwardIssue']['key'])
                if 'inwardIssue' in link:
                    issue_keys_to_explore.add(link['inwardIssue']['key'])
        
        # Fetch parent/related issues to discover their projects
        if issue_keys_to_explore:
            logger.info(f"🔗 Exploring {len(issue_keys_to_explore)} related issues for additional projects")
            
            if self.debug:
                logger.debug(f"🐛 Related issue keys to explore: {list(issue_keys_to_explore)[:10]}...")
            
            try:
                related_issues = self.jira_client.fetch_issues_by_keys(list(issue_keys_to_explore))
                for issue in related_issues:
                    project = issue['fields'].get('project', {}).get('key')
                    if project:
                        projects.add(project)
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch related issues: {str(e)}")
        
        return projects
    
    def _fetch_project_issues(self, projects: set, start_date: str) -> List[Dict]:
        """
        Fetch all issues from given projects resolved after start_date.
        
        Args:
            projects (set): Set of project keys
            start_date (str): Start date (YYYY-MM-DD)
            
        Returns:
            List[Dict]: All issues from projects
        """
        all_issues = []
        
        for project in sorted(projects):
            jql = f'project = {project} AND resolved >= "{start_date}" ORDER BY resolved ASC'
            
            logger.info(f"📥 Fetching issues from project {project}")
            if self.debug:
                logger.debug(f"🐛 Executing query: {jql}")
            
            try:
                project_issues = self.jira_client.fetch_issues(jql, max_results=5000)
                logger.info(f"  ✓ Retrieved {len(project_issues)} issues from {project}")
                all_issues.extend(project_issues)
            except Exception as e:
                logger.error(f"  ✗ Failed to fetch issues from {project}: {str(e)}")
                continue
        
        return all_issues
    
    def _calculate_lead_times_by_project(self, issues: List[Dict], start_date: str) -> Dict:
        """
        Calculate lead times for each issue, grouped by project and month.
        
        Args:
            issues (List[Dict]): List of Jira issues
            start_date (str): Start date filter
            
        Returns:
            Dict: {project: {month: [lead_times]}}
        """
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        project_monthly_data = defaultdict(lambda: defaultdict(list))
        
        for issue in issues:
            try:
                # Get project
                project = issue['fields'].get('project', {}).get('key', 'UNKNOWN')
                
                # Calculate lead time (from created to resolved)
                created = issue['fields'].get('created')
                resolved = issue['fields'].get('resolutiondate')
                
                if not created or not resolved:
                    continue
                
                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00')).replace(tzinfo=None)
                resolved_dt = datetime.fromisoformat(resolved.replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Filter by start date
                if resolved_dt < start_dt:
                    continue
                
                # Calculate lead time in days
                lead_time_days = (resolved_dt - created_dt).days
                
                if lead_time_days < 0:
                    continue
                
                # Group by month (YYYY-MM)
                month_key = resolved_dt.strftime('%Y-%m')
                
                project_monthly_data[project][month_key].append({
                    'lead_time': lead_time_days,
                    'issue_key': issue['key'],
                    'resolved_date': resolved_dt.isoformat()
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process issue {issue.get('key')}: {str(e)}")
                continue
        
        return dict(project_monthly_data)
    
    def _calculate_pbc_metrics(self, project: str, monthly_data: Dict) -> Dict:
        """
        Calculate Process Behavior Chart metrics for a project.
        
        Args:
            project (str): Project key
            monthly_data (Dict): {month: [lead_time_data]}
            
        Returns:
            Dict: PBC metrics including median, 85th percentile, monthly averages
        """
        logger.info(f"📊 Calculating PBC metrics for {project}")
        
        # Flatten all lead times
        all_lead_times = []
        for month_data in monthly_data.values():
            all_lead_times.extend([item['lead_time'] for item in month_data])
        
        if not all_lead_times:
            return {
                'project': project,
                'error': 'No valid lead times found'
            }
        
        # Calculate baseline metrics (overall)
        median_lead_time = statistics.median(all_lead_times)
        percentile_85 = self._calculate_percentile(all_lead_times, 85)
        mean_lead_time = statistics.mean(all_lead_times)
        
        # Calculate moving range for control limits
        moving_ranges = self._calculate_moving_ranges(all_lead_times)
        mean_moving_range = statistics.mean(moving_ranges) if moving_ranges else 0
        
        # Calculate control limits (Natural Process Limits)
        # Using ±3σ (where σ is estimated from moving range)
        # σ ≈ MR̄ / 1.128 (for individuals chart)
        sigma_estimate = mean_moving_range / 1.128 if mean_moving_range > 0 else 0
        
        upper_control_limit = mean_lead_time + (3 * sigma_estimate)
        lower_control_limit = max(0, mean_lead_time - (3 * sigma_estimate))
        
        # Calculate monthly aggregates
        monthly_metrics = []
        sorted_months = sorted(monthly_data.keys())
        
        for month in sorted_months:
            month_lead_times = [item['lead_time'] for item in monthly_data[month]]
            
            if month_lead_times:
                monthly_metrics.append({
                    'month': month,
                    'median': statistics.median(month_lead_times),
                    'mean': statistics.mean(month_lead_times),
                    'p85': self._calculate_percentile(month_lead_times, 85),
                    'count': len(month_lead_times),
                    'min': min(month_lead_times),
                    'max': max(month_lead_times)
                })
        
        # Detect special causes (points outside control limits)
        special_causes = self._detect_special_causes(monthly_metrics, upper_control_limit, lower_control_limit)
        
        # Detect trends (7+ consecutive points increasing or decreasing)
        trends = self._detect_trends(monthly_metrics)
        
        return {
            'project': project,
            'baseline_metrics': {
                'median': round(median_lead_time, 2),
                'mean': round(mean_lead_time, 2),
                'p85': round(percentile_85, 2),
                'total_issues': len(all_lead_times),
                'min': min(all_lead_times),
                'max': max(all_lead_times)
            },
            'control_limits': {
                'upper': round(upper_control_limit, 2),
                'lower': round(lower_control_limit, 2),
                'sigma': round(sigma_estimate, 2)
            },
            'monthly_metrics': monthly_metrics,
            'special_causes': special_causes,
            'trends': trends,
            'process_stability': self._assess_stability(special_causes, trends)
        }
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate the nth percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_data):
            return sorted_data[-1]
        
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
    
    def _calculate_moving_ranges(self, data: List[float]) -> List[float]:
        """Calculate moving ranges between consecutive values."""
        if len(data) < 2:
            return []
        
        return [abs(data[i] - data[i-1]) for i in range(1, len(data))]
    
    def _detect_special_causes(self, monthly_metrics: List[Dict], ucl: float, lcl: float) -> List[Dict]:
        """
        Detect special cause variations (points outside control limits).
        
        Args:
            monthly_metrics (List[Dict]): Monthly data points
            ucl (float): Upper control limit
            lcl (float): Lower control limit
            
        Returns:
            List[Dict]: Special cause events
        """
        special_causes = []
        
        for metric in monthly_metrics:
            mean = metric['mean']
            month = metric['month']
            
            if mean > ucl:
                special_causes.append({
                    'month': month,
                    'type': 'above_ucl',
                    'value': mean,
                    'limit': ucl,
                    'severity': 'high',
                    'message': f'Lead time significantly above upper control limit ({mean:.1f} > {ucl:.1f})'
                })
            elif mean < lcl and lcl > 0:
                special_causes.append({
                    'month': month,
                    'type': 'below_lcl',
                    'value': mean,
                    'limit': lcl,
                    'severity': 'low',
                    'message': f'Lead time significantly below lower control limit ({mean:.1f} < {lcl:.1f})'
                })
        
        return special_causes
    
    def _detect_trends(self, monthly_metrics: List[Dict]) -> List[Dict]:
        """
        Detect trends (7+ consecutive increasing or decreasing points).
        
        Args:
            monthly_metrics (List[Dict]): Monthly data points
            
        Returns:
            List[Dict]: Trend detections
        """
        trends = []
        
        if len(monthly_metrics) < 7:
            return trends
        
        # Check for increasing trend
        increasing_count = 0
        decreasing_count = 0
        
        for i in range(1, len(monthly_metrics)):
            current_mean = monthly_metrics[i]['mean']
            previous_mean = monthly_metrics[i-1]['mean']
            
            if current_mean > previous_mean:
                increasing_count += 1
                decreasing_count = 0
            elif current_mean < previous_mean:
                decreasing_count += 1
                increasing_count = 0
            else:
                increasing_count = 0
                decreasing_count = 0
            
            if increasing_count >= 6:
                trends.append({
                    'type': 'increasing',
                    'end_month': monthly_metrics[i]['month'],
                    'duration': increasing_count + 1,
                    'severity': 'warning',
                    'message': f'Increasing trend detected over {increasing_count + 1} months'
                })
                increasing_count = 0
            
            if decreasing_count >= 6:
                trends.append({
                    'type': 'decreasing',
                    'end_month': monthly_metrics[i]['month'],
                    'duration': decreasing_count + 1,
                    'severity': 'positive',
                    'message': f'Decreasing trend detected over {decreasing_count + 1} months (improvement)'
                })
                decreasing_count = 0
        
        return trends
    
    def _assess_stability(self, special_causes: List[Dict], trends: List[Dict]) -> Dict:
        """
        Assess overall process stability.
        
        Args:
            special_causes (List[Dict]): Detected special causes
            trends (List[Dict]): Detected trends
            
        Returns:
            Dict: Stability assessment
        """
        total_signals = len(special_causes) + len(trends)
        high_severity_count = len([s for s in special_causes if s.get('severity') == 'high'])
        
        if total_signals == 0:
            status = 'stable'
            message = 'Process is stable with no special causes detected'
            color = 'green'
        elif high_severity_count > 0:
            status = 'unstable'
            message = f'Process is unstable with {high_severity_count} high severity signal(s)'
            color = 'red'
        elif total_signals <= 2:
            status = 'mostly_stable'
            message = f'Process is mostly stable with {total_signals} signal(s)'
            color = 'yellow'
        else:
            status = 'needs_attention'
            message = f'Process needs attention with {total_signals} signal(s)'
            color = 'orange'
        
        return {
            'status': status,
            'message': message,
            'color': color,
            'total_signals': total_signals,
            'special_causes_count': len(special_causes),
            'trends_count': len(trends)
        }
    
    def _generate_summary(self, pbc_results: Dict, start_date: str) -> Dict:
        """
        Generate overall summary across all projects.
        
        Args:
            pbc_results (Dict): PBC results for all projects
            start_date (str): Analysis start date
            
        Returns:
            Dict: Summary statistics
        """
        total_projects = len(pbc_results)
        stable_projects = 0
        unstable_projects = 0
        total_issues = 0
        
        for project_result in pbc_results.values():
            if 'error' in project_result:
                continue
            
            total_issues += project_result['baseline_metrics']['total_issues']
            stability = project_result['process_stability']['status']
            
            if stability == 'stable':
                stable_projects += 1
            elif stability == 'unstable':
                unstable_projects += 1
        
        return {
            'total_projects': total_projects,
            'stable_projects': stable_projects,
            'unstable_projects': unstable_projects,
            'total_issues_analyzed': total_issues,
            'analysis_period': f"{start_date} to {datetime.now().strftime('%Y-%m-%d')}",
            'stability_percentage': round((stable_projects / total_projects * 100) if total_projects > 0 else 0, 1)
        }
