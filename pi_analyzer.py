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
import json
import os

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
        self._load_configuration()
    
    def _load_configuration(self):
        """
        Load configuration from pi_config.json file.
        """
        config_path = os.path.join(os.path.dirname(__file__), 'pi_config.json')
        
        # Default configuration
        default_config = {
            "base_project": "ISDOP",
            "excluded_projects": ["E2ECD"],
            "test_mode": {"enabled": False, "test_initiative_id": "ISDOP-2000"},
            "completion_statuses": ["Done", "Closed", "Resolved"],
            "in_progress_statuses": ["In Progress", "Doing", "Working", "Development"],
            "issue_types": ["Bug", "Story", "Sub-task", "Sub-Feature", "Feature"]
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"📋 Loaded configuration from {config_path}")
            else:
                config = default_config
                logger.info("📋 Using default configuration")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load config, using defaults: {str(e)}")
            config = default_config
        
        # Set configuration values
        self.base_project = config.get("base_project", "ISDOP")
        self.excluded_projects = set(config.get("excluded_projects", ["E2ECD"]))
        self.test_mode = config.get("test_mode", {"enabled": False, "test_initiative_id": "ISDOP-2000"})
        self.completion_statuses = config.get("completion_statuses", ["Done", "Closed", "Resolved"])
        self.in_progress_statuses = config.get("in_progress_statuses", ["In Progress", "Doing", "Working", "Development"])
        self.issue_types = config.get("issue_types", ["Bug", "Story", "Sub-task", "Sub-Feature", "Feature"])
        self.flow_recommendations = config.get("flow_metrics_recommendations", {})
        
        logger.info(f"🎯 Base project: {self.base_project}")
        logger.info(f"🚫 Excluded projects: {list(self.excluded_projects)}")
        if self.test_mode.get("enabled", False):
            logger.info(f"🧪 Test mode enabled: {self.test_mode.get('test_initiative_id')}")
    
    def analyze_pi(self, pi_start_date: str, pi_end_date: str, include_full_backlog: bool = False) -> Dict:
        """
        Analyze PI metrics for ISDOP and related projects.
        
        Args:
            pi_start_date (str): PI start date (YYYY-MM-DD format)
            pi_end_date (str): PI end date (YYYY-MM-DD format)
            include_full_backlog (bool): Include full area backlog analysis with flow metrics
            
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
        
        # Step 4: Full backlog analysis if requested
        flow_metrics = None
        if include_full_backlog:
            # Get actual projects from completed issues for flow analysis
            actual_projects = set(metrics.get('by_project', {}).keys())
            # Filter out excluded projects
            actual_projects = actual_projects - self.excluded_projects
            flow_metrics = self._analyze_flow_metrics(pi_start_date, pi_end_date, actual_projects)
        
        # Step 5: Create comprehensive report
        report = self._create_pi_report(pi_start_date, pi_end_date, related_projects, metrics, flow_metrics)
        
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
        Get Business Initiatives from ISDOP project.
        In test mode, returns only the specified test initiative.
        
        Returns:
            List[Dict]: List of business initiative issues
        """
        if self.test_mode.get("enabled", False):
            test_id = self.test_mode.get("test_initiative_id", "ISDOP-2000")
            logger.info(f"🧪 Test mode: Fetching single initiative {test_id}")
            
            jql_query = f'key = "{test_id}"'
            
            try:
                initiatives = self.jira_client.fetch_issues(jql_query, max_results=1)
                logger.info(f"📊 Test mode: Found {len(initiatives)} initiative(s)")
                return initiatives
            except Exception as e:
                logger.error(f"🚩 Failed to fetch test initiative: {str(e)}")
                return []
        else:
            logger.info(f"🎯 Fetching all business initiatives from ISDOP")
            
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
        status_list = ','.join([f'"{status}"' for status in self.completion_statuses])
        
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
        status_list = ','.join([f'"{status}"' for status in self.completion_statuses])
        
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
    
    def _analyze_flow_metrics(self, start_date: str, end_date: str, projects: Set[str]) -> Dict:
        """
        Analyze flow metrics for each area backlog.
        
        Args:
            start_date (str): PI start date
            end_date (str): PI end date
            projects (Set[str]): Related projects
            
        Returns:
            Dict: Flow metrics by project
        """
        logger.info(f"🔄 Analyzing flow metrics for {len(projects)} areas")
        
        flow_metrics = {}
        
        for project in projects:
            logger.info(f"📊 Analyzing flow metrics for {project}")
            
            # Get all issues in project during PI period
            all_issues = self._fetch_project_flow_issues(project, start_date, end_date)
            
            if all_issues:
                project_metrics = self._calculate_project_flow_metrics(project, all_issues, start_date, end_date)
                flow_metrics[project] = project_metrics
        
        return flow_metrics
    
    def _fetch_project_flow_issues(self, project: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch all issues for flow metrics analysis.
        
        Args:
            project (str): Project key
            start_date (str): PI start date
            end_date (str): PI end date
            
        Returns:
            List[Dict]: All relevant issues
        """
        # Get completed issues
        completed_jql = (f'project = {project} '
                        f'AND resolved >= "{start_date}" '
                        f'AND resolved <= "{end_date}"')
        
        # Get in-progress issues
        in_progress_statuses = ','.join([f'"{status}"' for status in self.in_progress_statuses])
        wip_jql = (f'project = {project} '
                  f'AND status IN ({in_progress_statuses}) '
                  f'AND created <= "{end_date}"')
        
        all_issues = []
        
        try:
            # Fetch completed issues
            completed_issues = self.jira_client.fetch_issues(completed_jql, max_results=1000)
            all_issues.extend(completed_issues)
            
            # Fetch WIP issues
            wip_issues = self.jira_client.fetch_issues(wip_jql, max_results=1000)
            all_issues.extend(wip_issues)
            
            # Enhance with detailed data
            enhanced_issues = []
            for issue in all_issues:
                enhanced = self._enhance_issue_with_flow_data(issue)
                if enhanced:
                    enhanced_issues.append(enhanced)
            
            return enhanced_issues
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch flow issues for {project}: {str(e)}")
            return []
    
    def _enhance_issue_with_flow_data(self, issue: Dict) -> Optional[Dict]:
        """
        Enhance issue with flow metrics data.
        
        Args:
            issue (Dict): Basic issue data
            
        Returns:
            Optional[Dict]: Enhanced issue with flow data
        """
        try:
            response = self.jira_client.session.get(
                f"{self.jira_client.base_url}/rest/api/2/issue/{issue['key']}",
                params={'fields': 'created,resolutiondate,status,changelog', 'expand': 'changelog'}
            )
            
            if response.status_code != 200:
                return issue
            
            detailed_data = response.json()
            fields = detailed_data.get('fields', {})
            
            # Calculate flow metrics
            created_date = fields.get('created')
            resolved_date = fields.get('resolutiondate')
            current_status = fields.get('status', {}).get('name', '')
            
            # Find first in-progress date from changelog
            in_progress_date = self._find_in_progress_date(detailed_data.get('changelog', {}))
            
            issue.update({
                'created_date': created_date,
                'resolved_date': resolved_date,
                'current_status': current_status,
                'in_progress_date': in_progress_date,
                'is_completed': resolved_date is not None,
                'is_wip': current_status in self.in_progress_statuses
            })
            
            return issue
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance flow data for {issue.get('key', 'unknown')}: {str(e)}")
            return issue
    
    def _find_in_progress_date(self, changelog: Dict) -> Optional[str]:
        """
        Find the first date when issue moved to in-progress status.
        
        Args:
            changelog (Dict): Issue changelog
            
        Returns:
            Optional[str]: First in-progress date
        """
        histories = changelog.get('histories', [])
        
        for history in histories:
            for item in history.get('items', []):
                if (item.get('field') == 'status' and 
                    item.get('toString') in self.in_progress_statuses):
                    return history.get('created')
        
        return None
    
    def _calculate_project_flow_metrics(self, project: str, issues: List[Dict], start_date: str, end_date: str) -> Dict:
        """
        Calculate flow metrics for a project.
        
        Args:
            project (str): Project key
            issues (List[Dict]): Project issues
            start_date (str): PI start date
            end_date (str): PI end date
            
        Returns:
            Dict: Flow metrics
        """
        from datetime import datetime, timedelta
        import statistics
        
        completed_issues = [i for i in issues if i.get('is_completed', False)]
        wip_issues = [i for i in issues if i.get('is_wip', False)]
        
        # 1. Work in Progress
        wip_count = len(wip_issues)
        
        # 2. Throughput (items per week)
        pi_start = datetime.strptime(start_date, '%Y-%m-%d')
        pi_end = datetime.strptime(end_date, '%Y-%m-%d')
        pi_weeks = (pi_end - pi_start).days / 7
        throughput = len(completed_issues) / max(pi_weeks, 1)
        
        # 3. Work Item Age (for WIP items)
        ages = []
        for issue in wip_issues:
            if issue.get('in_progress_date'):
                try:
                    start_dt = datetime.fromisoformat(issue['in_progress_date'].replace('Z', '+00:00')).replace(tzinfo=None)
                    age_days = (pi_end - start_dt).days
                    ages.append(max(age_days, 0))
                except Exception:
                    continue
        
        avg_age = statistics.mean(ages) if ages else 0
        
        # 4. Cycle Time (for completed items)
        cycle_times = []
        for issue in completed_issues:
            if issue.get('in_progress_date') and issue.get('resolved_date'):
                try:
                    start_dt = datetime.fromisoformat(issue['in_progress_date'].replace('Z', '+00:00')).replace(tzinfo=None)
                    end_dt = datetime.fromisoformat(issue['resolved_date'].replace('Z', '+00:00')).replace(tzinfo=None)
                    cycle_days = (end_dt - start_dt).days
                    cycle_times.append(max(cycle_days, 0))
                except Exception:
                    continue
        
        avg_cycle_time = statistics.mean(cycle_times) if cycle_times else 0
        
        metrics = {
            'work_in_progress': wip_count,
            'throughput_per_week': round(throughput, 2),
            'avg_work_item_age_days': round(avg_age, 1),
            'avg_cycle_time_days': round(avg_cycle_time, 1),
            'total_completed': len(completed_issues),
            'total_issues': len(issues)
        }
        
        # Add coaching recommendations
        metrics['coaching_recommendations'] = self._generate_coaching_recommendations(metrics)
        
        return metrics
    
    def _create_pi_report(self, start_date: str, end_date: str, projects: Set[str], metrics: Dict, flow_metrics: Optional[Dict] = None) -> Dict:
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
        actual_projects = [p for p in metrics.get('by_project', {}).keys() if p not in self.excluded_projects]
        
        report = {
            'pi_period': {
                'start_date': start_date,
                'end_date': end_date,
                'duration_days': (datetime.strptime(end_date, '%Y-%m-%d') - 
                                datetime.strptime(start_date, '%Y-%m-%d')).days
            },
            'analyzed_projects': sorted(actual_projects),
            'base_project': self.base_project,
            'excluded_projects': list(self.excluded_projects),
            'analysis_date': datetime.now().isoformat(),
            'metrics': metrics,
            'summary': {
                'total_projects': len(actual_projects),
                'total_issues': metrics['total_issues'],
                'total_estimate_hours': metrics['summary']['total_estimate_hours'],
                'unestimated_percentage': metrics['summary']['overall_unestimated_percentage']
            }
        }
        
        # Add flow metrics if available
        if flow_metrics:
            report['flow_metrics'] = flow_metrics
            report['has_flow_metrics'] = True
            # Add overall coaching summary
            report['coaching_summary'] = self._generate_overall_coaching_summary(flow_metrics)
        else:
            report['has_flow_metrics'] = False
        
        return report
    def _generate_coaching_recommendations(self, metrics: Dict) -> List[Dict]:
        """
        Generate coaching recommendations based on flow metrics.
        
        Args:
            metrics (Dict): Project flow metrics
            
        Returns:
            List[Dict]: List of coaching recommendations
        """
        recommendations = []
        
        if not self.flow_recommendations:
            return recommendations
        
        # WIP Analysis
        wip = metrics.get('work_in_progress', 0)
        wip_config = self.flow_recommendations.get('wip_limits', {})
        if wip > wip_config.get('critical_threshold', 15):
            recommendations.append({
                'metric': 'Work in Progress',
                'severity': 'Critical',
                'current_value': wip,
                'threshold': wip_config.get('critical_threshold', 15),
                'advice': wip_config.get('coaching_advice', 'Implement WIP limits')
            })
        elif wip > wip_config.get('warning_threshold', 10):
            recommendations.append({
                'metric': 'Work in Progress',
                'severity': 'Warning',
                'current_value': wip,
                'threshold': wip_config.get('warning_threshold', 10),
                'advice': wip_config.get('coaching_advice', 'Consider WIP limits')
            })
        
        # Cycle Time Analysis
        cycle_time = metrics.get('avg_cycle_time_days', 0)
        cycle_config = self.flow_recommendations.get('cycle_time', {})
        if cycle_time > cycle_config.get('critical_threshold', 30):
            recommendations.append({
                'metric': 'Cycle Time',
                'severity': 'Critical',
                'current_value': f"{cycle_time:.1f} days",
                'threshold': f"{cycle_config.get('critical_threshold', 30)} days",
                'advice': cycle_config.get('coaching_advice', 'Break down work items')
            })
        elif cycle_time > cycle_config.get('warning_threshold', 21):
            recommendations.append({
                'metric': 'Cycle Time',
                'severity': 'Warning',
                'current_value': f"{cycle_time:.1f} days",
                'threshold': f"{cycle_config.get('warning_threshold', 21)} days",
                'advice': cycle_config.get('coaching_advice', 'Review work sizing')
            })
        
        # Work Item Age Analysis
        age = metrics.get('avg_work_item_age_days', 0)
        age_config = self.flow_recommendations.get('work_item_age', {})
        if age > age_config.get('critical_threshold', 21):
            recommendations.append({
                'metric': 'Work Item Age',
                'severity': 'Critical',
                'current_value': f"{age:.1f} days",
                'threshold': f"{age_config.get('critical_threshold', 21)} days",
                'advice': age_config.get('coaching_advice', 'Address blocked items')
            })
        elif age > age_config.get('warning_threshold', 14):
            recommendations.append({
                'metric': 'Work Item Age',
                'severity': 'Warning',
                'current_value': f"{age:.1f} days",
                'threshold': f"{age_config.get('warning_threshold', 14)} days",
                'advice': age_config.get('coaching_advice', 'Review aging items')
            })
        
        return recommendations
    
    def _generate_overall_coaching_summary(self, flow_metrics: Dict) -> Dict:
        """
        Generate overall coaching summary across all projects.
        
        Args:
            flow_metrics (Dict): Flow metrics for all projects
            
        Returns:
            Dict: Overall coaching summary
        """
        all_recommendations = []
        critical_count = 0
        warning_count = 0
        
        for project, metrics in flow_metrics.items():
            project_recommendations = metrics.get('coaching_recommendations', [])
            for rec in project_recommendations:
                rec['project'] = project
                all_recommendations.append(rec)
                if rec['severity'] == 'Critical':
                    critical_count += 1
                elif rec['severity'] == 'Warning':
                    warning_count += 1
        
        # Get general recommendations from config
        general_advice = self.flow_recommendations.get('general_recommendations', [])
        
        return {
            'total_recommendations': len(all_recommendations),
            'critical_issues': critical_count,
            'warning_issues': warning_count,
            'all_recommendations': all_recommendations,
            'general_recommendations': general_advice,
            'overall_health': 'Critical' if critical_count > 0 else 'Warning' if warning_count > 0 else 'Healthy'
        }