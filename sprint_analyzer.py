"""
Sprint Analysis Application
Analyzes sprint capacity, estimates, and forecasts feasibility based on historical data.

Author: Sprint Analysis Tool - Pietro Maffi
Purpose: Analyze sprint workload and predict feasibility using historical velocity
"""

import argparse
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

# Reuse existing classes
from jira_client import JiraClient
from data_analyzer import DataAnalyzer
from simple_sprint_retriever import SimpleSprintRetriever

# Configure logging with same style
# to enable debug change INFO to DEBUG in the next line
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SprintAnalyzer')

class SprintAnalyzer:
    """
    Analyzes sprint capacity and forecasts feasibility based on historical data.
    
    This class extends the existing analytics capabilities to focus on sprint planning
    and capacity analysis using time estimates and historical velocity.
    """
    
    def __init__(self, jira_client: JiraClient):
        """
        Initialize sprint analyzer with Jira client.
        
        Args:
            jira_client (JiraClient): Configured Jira client instance
        """
        self.jira_client = jira_client
        self.data_analyzer = DataAnalyzer()
        self.sprint_retriever = SimpleSprintRetriever(jira_client)
        # Cache for sprint data to avoid duplicate calls
        self._sprint_cache = {}
        # Default capacity configuration
        self.team_size = 8
        self.sprint_days = 10
        self.hours_per_day = 8
        self.completion_statuses = ['Done', 'Closed']
        self.excluded_types = ['Epic']
        # Configurable limits
        self.max_results_limit = 2000
    
    def configure_capacity(self, team_size: int, sprint_days: int, hours_per_day: int):
        """
        Configure sprint capacity parameters.
        
        Args:
            team_size (int): Number of team members
            sprint_days (int): Working days in sprint
            hours_per_day (int): Working hours per day
        """
        self.team_size = team_size
        self.sprint_days = sprint_days
        self.hours_per_day = hours_per_day
        logger.info(f"📊 Configured capacity: {team_size} people × {sprint_days} days × {hours_per_day}h = {team_size * sprint_days * hours_per_day}h total")
    
    def configure_completion_statuses(self, statuses_str: str):
        """
        Configure completion status names.
        
        Args:
            statuses_str (str): Comma-separated status names
        """
        self.completion_statuses = [s.strip() for s in statuses_str.split(',') if s.strip()]
        logger.info(f"✅ Configured completion statuses: {self.completion_statuses}")
    
    def configure_excluded_types(self, types_str: str):
        """
        Configure excluded issue types.
        
        Args:
            types_str (str): Comma-separated issue type names
        """
        self.excluded_types = [s.strip() for s in types_str.split(',') if s.strip()]
        logger.info(f"🚫 Configured excluded types: {self.excluded_types}")
        
    def analyze_sprint(self, sprint_name: str, historical_months: int = 6) -> Dict:
        """
        Analyze sprint workload and forecast feasibility.
        
        Args:
            sprint_name (str): Name or ID of the sprint to analyze
            historical_months (int): Months of historical data for forecasting
            
        Returns:
            Dict: Complete sprint analysis with forecasting
        """
        logger.info(f"📊 Starting sprint analysis for: {sprint_name}")
        
        # Fetch sprint issues and details
        sprint_issues, sprint_details = self._fetch_sprint_issues_with_details(sprint_name, historical_months)
        if not sprint_issues:
            logger.error(f"🚩 No issues found for sprint: {sprint_name}")
            return self._empty_result()
        
        logger.info(f"✅ Found {len(sprint_issues)} issues in sprint")
        
        # Analyze sprint workload
        workload_analysis = self._analyze_sprint_workload(sprint_issues)
        
        # Get historical data for forecasting (filtered by similar sprint names)
        historical_data = self._fetch_historical_data_by_sprint_pattern(historical_months, sprint_name, sprint_issues)
        
        # Generate forecast with date comparison
        forecast = self._generate_forecast_with_dates(workload_analysis, historical_data, sprint_details)
        
        # Create comprehensive report
        report = self._create_sprint_report(sprint_name, workload_analysis, forecast, historical_data)
        
        logger.info("✅ Sprint analysis completed successfully")
        return report
    
    def _fetch_sprint_issues_with_details(self, sprint_name: str, historical_months: int = 6) -> Tuple[List[Dict], Dict]:
        """
        Fetch all issues in the specified sprint along with sprint details.
        
        Args:
            sprint_name (str): Sprint name or ID
            
        Returns:
            Tuple[List[Dict], Dict]: List of issues and sprint details
        """
        logger.info(f"🔍 Fetching Jira issues for sprint: {sprint_name}")
        
        # Build JQL query for sprint - try different formats
        if sprint_name.isdigit():
            # If sprint_name is numeric, use sprint ID format
            jql_query = f'sprint = {sprint_name}'
        else:
            # If sprint_name contains text, use quoted format
            jql_query = f'sprint = "{sprint_name}"'
        
        # Add excluded types filter
        if self.excluded_types:
            excluded_types_str = ','.join([f'"{t}"' for t in self.excluded_types])
            jql_query += f' AND type NOT IN ({excluded_types_str})'
            logger.info(f"🚫 Excluding issue types: {self.excluded_types}")
        
        logger.debug(f"🔍 Using JQL query: {jql_query}")
        
        try:
            issues = self.jira_client.fetch_issues(jql_query, max_results=self.max_results_limit)
            
            # Enhance issues with time tracking data
            enhanced_issues = []
            logger.info(f"🔄 Enhancing {len(issues)} issues with time tracking data...")
            for i, issue in enumerate(issues):
                if i % 10 == 0 and i > 0:
                    logger.info(f"📊 Enhanced {i}/{len(issues)} issues ({i/len(issues)*100:.1f}%)")
                enhanced_issue = self._enhance_issue_with_time_data(issue, sprint_name)
                if enhanced_issue:
                    enhanced_issues.append(enhanced_issue)
            logger.info(f"✅ Completed enhancing {len(enhanced_issues)} issues")
            
            # Get sprint details
            sprint_details = self._get_sprint_details(sprint_name, historical_months)
            
            return enhanced_issues, sprint_details
            
        except Exception as e:
            logger.error(f"🚩 Failed to fetch sprint issues: {str(e)}")
            return [], {}
    
    def _enhance_issue_with_time_data(self, issue: Dict, sprint_name: str = None) -> Optional[Dict]:
        """
        Enhance issue with time tracking information, including sprint-specific time spent.
        
        Args:
            issue (Dict): Basic issue data
            sprint_name (str): Sprint name to filter worklog entries
            
        Returns:
            Optional[Dict]: Enhanced issue with time data
        """
        try:
            # Fetch detailed issue data including time tracking and worklog
            response = self.jira_client.session.get(
                f"{self.jira_client.base_url}/rest/api/2/issue/{issue['key']}",
                params={'fields': 'timeoriginalestimate,timeestimate,timespent,status,summary,assignee,worklog', 'expand': 'changelog'}
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Could not fetch time data for {issue['key']}")
                return issue
            
            detailed_data = response.json()
            fields = detailed_data.get('fields', {})
            
            # Convert seconds to hours and log raw values
            raw_original = fields.get('timeoriginalestimate') or 0
            raw_remaining = fields.get('timeestimate') or 0
            raw_spent_total = fields.get('timespent') or 0
            
            original_estimate = raw_original / 3600
            remaining_estimate = raw_remaining / 3600
            time_spent_total = raw_spent_total / 3600
            
            # Calculate sprint-specific time spent from worklog
            sprint_time_spent = self._calculate_sprint_time_spent(detailed_data, sprint_name)
            
            logger.debug(f"🔍 {issue['key']} raw time data: Original={raw_original}s, Remaining={raw_remaining}s, Total_Spent={raw_spent_total}s")
            logger.debug(f"⏱️ {issue['key']} converted: Original={original_estimate:.1f}h, Remaining={remaining_estimate:.1f}h, Total_Spent={time_spent_total:.1f}h, Sprint_Spent={sprint_time_spent:.1f}h")
            
            # Enhance the issue
            issue.update({
                'original_estimate_hours': original_estimate,
                'remaining_estimate_hours': remaining_estimate,
                'time_spent_hours': sprint_time_spent,  # Use sprint-specific time
                'time_spent_total_hours': time_spent_total,  # Keep total for reference
                'completion_percentage': (sprint_time_spent / original_estimate * 100) if original_estimate > 0 else 0
            })
            
            return issue
            
        except Exception as e:
            logger.debug(f"⚠️ Failed to enhance issue {issue.get('key', 'unknown')}: {str(e)}")
            return issue
    
    def _calculate_sprint_time_spent(self, issue_data: Dict, sprint_name: str) -> float:
        """
        Calculate time spent specifically within the current sprint timeframe.
        
        Args:
            issue_data (Dict): Full issue data from Jira API
            sprint_name (str): Sprint name to match against
            
        Returns:
            float: Hours spent in current sprint
        """
        issue_key = issue_data.get('key', 'Unknown')
        
        if not sprint_name:
            # Fallback to total time if no sprint specified
            total_time = (issue_data.get('fields', {}).get('timespent') or 0) / 3600
            logger.debug(f"  🔄 {issue_key}: No sprint specified, using total time: {total_time:.1f}h")
            return total_time
        
        # Get sprint start/end dates from changelog
        sprint_start_date, sprint_end_date = self._get_sprint_dates_from_changelog(issue_data, sprint_name)
        
        # Get worklog entries
        worklog_data = issue_data.get('fields', {}).get('worklog', {})
        worklogs = worklog_data.get('worklogs', [])
        
        logger.debug(f" 📅 {issue_key}: Sprint dates - Start: {sprint_start_date}, End: {sprint_end_date}")
        logger.debug(f" 📋 {issue_key}: Found {len(worklogs)} worklog entries")
        
        sprint_time_seconds = 0
        total_worklog_time = 0
        
        for worklog in worklogs:
            worklog_date_str = worklog.get('started', '')
            worklog_seconds = worklog.get('timeSpentSeconds', 0)
            total_worklog_time += worklog_seconds
            
            if not worklog_date_str:
                continue
            
            try:
                from dateutil import parser as date_parser
                worklog_date = date_parser.parse(worklog_date_str).date()
                
                logger.debug(f" 📝 {issue_key} worklog on {worklog_date}: {worklog_seconds/3600:.1f}h")
                
                # Check if worklog falls within sprint timeframe
                if sprint_start_date and sprint_end_date:
                    if sprint_start_date <= worklog_date <= sprint_end_date:
                        sprint_time_seconds += worklog_seconds
                        logger.debug(f" ✅ Included in sprint (within range)")
                    else:
                        logger.debug(f" ❌ Excluded (outside sprint range)")
                elif sprint_start_date and worklog_date >= sprint_start_date:
                    # If no end date, include all work after sprint start
                    sprint_time_seconds += worklog_seconds
                    logger.debug(f" ✅ Included in sprint (after start date)")
                # else:
                #    logger.debug(f" ❌ Excluded (no sprint dates found)")
                    
            except Exception as e:
                logger.debug(f"⚠️ Failed to parse worklog date {worklog_date_str}: {e}")
        
        sprint_hours = sprint_time_seconds / 3600
        total_hours = total_worklog_time / 3600
        
        # Fallback: if no sprint dates found or no time in sprint, use total time
        if not sprint_start_date and not sprint_end_date:
            logger.debug(f"  ⚠️ {issue_key}: No sprint dates found in changelog, using total time: {total_hours:.1f}h")
            return total_hours
        elif sprint_hours == 0 and total_hours > 0:
            logger.debug(f"  ⚠️ {issue_key}: No time logged during sprint period, using total time: {total_hours:.1f}h")
            return total_hours
        
        logger.debug(f"  ✅ {issue_key}: Sprint time calculated: {sprint_hours:.1f}h (of {total_hours:.1f}h total)")
        return sprint_hours
    
    def _get_sprint_dates_from_changelog(self, issue_data: Dict, sprint_name: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Extract sprint start and end dates from issue changelog.
        
        Args:
            issue_data (Dict): Full issue data from Jira API
            sprint_name (str): Sprint name to look for
            
        Returns:
            Tuple[Optional[datetime], Optional[datetime]]: Sprint start and end dates
        """
        changelog = issue_data.get('changelog', {})
        histories = changelog.get('histories', [])
        
        sprint_start_date = None
        sprint_end_date = None
        
        for history in histories:
            for item in history.get('items', []):
                if item.get('field') == 'Sprint':
                    to_string = item.get('toString', '')
                    if sprint_name in to_string:
                        # Found when issue was added to sprint
                        try:
                            from dateutil import parser as date_parser
                            sprint_start_date = date_parser.parse(history.get('created', '')).date()
                            logger.debug(f"  📅 {issue_data.get('key', 'Unknown')} added to sprint {sprint_name} on {sprint_start_date}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to parse sprint start date: {e}")
                            
                # Debug: log all sprint changes
                if item.get('field') == 'Sprint':
                    logger.debug(f"  🔍 {issue_data.get('key', 'Unknown')} sprint change: '{item.get('fromString', '')}' -> '{item.get('toString', '')}'")
                    
                    from_string = item.get('fromString', '')
                    if sprint_name in from_string and sprint_name not in to_string:
                        # Found when issue was removed from sprint
                        try:
                            from dateutil import parser as date_parser
                            sprint_end_date = date_parser.parse(history.get('created', '')).date()
                            logger.debug(f"  📅 {issue_data.get('key', 'Unknown')} removed from sprint {sprint_name} on {sprint_end_date}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to parse sprint end date: {e}")
        
        return sprint_start_date, sprint_end_date
    
    def _analyze_sprint_workload(self, issues: List[Dict]) -> Dict:
        """
        Analyze sprint workload and capacity.
        
        Args:
            issues (List[Dict]): Sprint issues with time data
            
        Returns:
            Dict: Workload analysis results
        """
        logger.info("📊 Analyzing sprint workload...")
        
        # Calculate totals with detailed logging
        total_original_estimate = 0
        total_remaining_estimate = 0
        total_time_spent = 0
        
        logger.debug("📋 Individual issue time tracking details:")
        for issue in issues:
            key = issue.get('key', 'Unknown')
            original = issue.get('original_estimate_hours', 0)
            remaining = issue.get('remaining_estimate_hours', 0)
            spent = issue.get('time_spent_hours', 0)
            status = issue.get('status', 'Unknown')
            
            total_original_estimate += original
            total_remaining_estimate += remaining
            total_time_spent += spent
            
            logger.debug(f"  📝 {key} [{status}]: Original={original:.1f}h, Remaining={remaining:.1f}h, Spent={spent:.1f}h")
        
        
        # Analyze by status
        status_breakdown = {}
        for issue in issues:
            status = issue.get('status', 'Unknown')
            if status not in status_breakdown:
                status_breakdown[status] = {
                    'count': 0,
                    'original_estimate': 0,
                    'remaining_estimate': 0,
                    'time_spent': 0
                }
            
            status_breakdown[status]['count'] += 1
            status_breakdown[status]['original_estimate'] += issue.get('original_estimate_hours', 0)
            status_breakdown[status]['remaining_estimate'] += issue.get('remaining_estimate_hours', 0)
            status_breakdown[status]['time_spent'] += issue.get('time_spent_hours', 0)
        
        # Calculate progress metrics
        overall_progress = (total_time_spent / total_original_estimate * 100) if total_original_estimate > 0 else 0
        
        # Identify issues without estimates
        unestimated_issues = [issue for issue in issues if issue.get('original_estimate_hours', 0) == 0]
        
        logger.info(f"📊 Total estimated hours: {total_original_estimate:.1f}")
        logger.info(f"⏳ Remaining hours: {total_remaining_estimate:.1f}")
        logger.info(f"✅ Hours spent: {total_time_spent:.1f}")
        logger.info(f"📈 Overall progress: {overall_progress:.1f}%")
        
        return {
            'total_issues': len(issues),
            'total_original_estimate': total_original_estimate,
            'total_remaining_estimate': total_remaining_estimate,
            'total_time_spent': total_time_spent,
            'overall_progress': overall_progress,
            'status_breakdown': status_breakdown,
            'unestimated_issues': len(unestimated_issues),
            'issues_detail': issues
        }
    
    def _fetch_historical_data_by_sprint_pattern(self, months_back: int, current_sprint_name: str, sprint_issues: List[Dict] = None) -> Dict:
        """
        Fetch historical data filtered by similar sprint names.
        
        Args:
            months_back (int): Number of months of historical data
            current_sprint_name (str): Current sprint name to extract pattern
            sprint_issues (List[Dict]): Current sprint issues
            
        Returns:
            Dict: Historical velocity and completion data
        """
        logger.info(f"📈 Fetching {months_back} months of historical data...")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # Extract project from sprint issues
        project_filter = ""
        if sprint_issues:
            projects = set()
            for issue in sprint_issues:
                key = issue.get('key', '')
                if '-' in key:
                    project = key.split('-')[0]
                    projects.add(project)
            
            if projects:
                project_list = ','.join(projects)
                project_filter = f' AND project IN ({project_list})'
                logger.info(f"🏢 Filtering historical data to projects: {project_list}")
        
        # Get similar sprints using proper JQL
        similar_sprints = self._get_similar_sprints(current_sprint_name, sprint_issues, months_back)
        sprint_filter = f' AND sprint IN ({similar_sprints})' if similar_sprints else ''
        
        # Enhanced JQL for completed issues filtered by similar sprints
        status_list = ','.join(self.completion_statuses)
        
        # Build excluded types filter
        excluded_types_list = ['"XTest"', '"XTest Execution"', '"XTest Plan"']
        if self.excluded_types:
            excluded_types_list.extend([f'"{t}"' for t in self.excluded_types])
        excluded_types_str = ','.join(excluded_types_list)
        
        jql_query = f'resolved >= "{start_date.strftime("%Y-%m-%d")}" AND resolved <= "{end_date.strftime("%Y-%m-%d")}" AND type NOT IN ({excluded_types_str}) AND status IN ({status_list}){project_filter}{sprint_filter}'
        
        logger.info(f"🔍 Similar sprints filter: {similar_sprints[:100]}...")  # Truncate for readability
        
        logger.info(f"🔍 Using JQL: {jql_query}")
        
        try:
            # Fetch in chunks to handle large datasets
            all_historical_issues = []
            start_at = 0
            chunk_size = 100
            
            while True:
                logger.info(f"📥 Fetching chunk {start_at//chunk_size + 1} (issues {start_at}-{start_at + chunk_size})")
                
                chunk_issues = self.jira_client.fetch_issues(jql_query, max_results=chunk_size, start_at=start_at)
                
                if not chunk_issues:
                    break
                    
                all_historical_issues.extend(chunk_issues)
                logger.info(f"📊 Retrieved {len(chunk_issues)} issues in this chunk, total: {len(all_historical_issues)}")
                
                # Stop if we got less than requested (last page)
                if len(chunk_issues) < chunk_size:
                    break
                    
                start_at += chunk_size
                
                # Safety limit to prevent infinite loops
                if len(all_historical_issues) >= self.max_results_limit:
                    logger.info(f"⚠️ Reached safety limit of {self.max_results_limit} issues, stopping fetch")
                    break
            
            logger.info(f"📈 Total historical issues fetched: {len(all_historical_issues)}")
            
            # Enhance with time data in chunks
            enhanced_historical = []
            max_to_process = min(len(all_historical_issues), 500)
            logger.info(f"🔄 Enhancing {max_to_process} historical issues with time data...")
            
            for i, issue in enumerate(all_historical_issues[:500]):  # Process max 500 for performance
                if i % 25 == 0:
                    logger.info(f"📊 Processing historical issue {i+1}/{max_to_process} ({(i+1)/max_to_process*100:.1f}%)")
                    
                enhanced = self._enhance_issue_with_time_data(issue)
                if enhanced:
                    enhanced_historical.append(enhanced)
            
            logger.info(f"✅ Completed enhancing {len(enhanced_historical)} historical issues")
            
            # Calculate historical velocity
            velocity_data = self._calculate_historical_velocity(enhanced_historical)
            
            # Add sprint pattern and count information
            velocity_data['sprint_pattern_used'] = getattr(self, '_current_sprint_pattern', '')
            velocity_data['similar_sprints_count'] = len(similar_sprints.split(',')) if similar_sprints else 0
            
            logger.info(f"✅ Analyzed {len(enhanced_historical)} enhanced historical issues")
            logger.info(f"📊 Used {velocity_data['similar_sprints_count']} similar sprints with pattern: {velocity_data['sprint_pattern_used']}")
            return velocity_data
            
        except Exception as e:
            logger.error(f"🚩 Failed to fetch historical data: {str(e)}")
            return {'average_velocity': 0, 'velocity_variance': 0, 'completion_rate': 0, 'sprint_pattern_used': ''}
    
    def _calculate_historical_velocity(self, historical_issues: List[Dict]) -> Dict:
        """
        Calculate team velocity using Monte Carlo simulation based on story count completion.
        
        Args:
            historical_issues (List[Dict]): Historical completed issues
            
        Returns:
            Dict: Velocity metrics with Monte Carlo forecasting
        """
        logger.info(f"📊 Calculating velocity from {len(historical_issues)} historical issues")
        
        if not historical_issues:
            logger.warning("⚠️ No historical issues available for velocity calculation")
            return {'average_velocity': 0, 'velocity_variance': 0, 'completion_rate': 0, 'total_historical_issues': 0, 'monte_carlo_forecast': {}}
        
        # Group issues by resolution week for story-based velocity
        weekly_story_counts = self._group_issues_by_week(historical_issues)
        
        if not weekly_story_counts:
            logger.warning("⚠️ No weekly velocity data available")
            return {'average_velocity': 0, 'velocity_variance': 0, 'completion_rate': 0, 'total_historical_issues': len(historical_issues), 'monte_carlo_forecast': {}}
        
        logger.info(f"📈 Weekly story completion data: {weekly_story_counts}")
        
        # Calculate basic velocity metrics
        avg_stories_per_week = np.mean(weekly_story_counts)
        velocity_variance = np.var(weekly_story_counts)
        
        # Monte Carlo simulation for forecasting
        monte_carlo_results = self._run_monte_carlo_simulation(weekly_story_counts)
        
        # Completion rate
        completed_statuses = [s.lower() for s in self.completion_statuses]
        completed_issues = [i for i in historical_issues if i.get('status', '').lower() in completed_statuses]
        completion_rate = len(completed_issues) / len(historical_issues) if historical_issues else 0
        
        logger.info(f"📈 Average velocity: {avg_stories_per_week:.1f} stories/week")
        logger.info(f"📊 Velocity variance: {velocity_variance:.2f}")
        logger.info(f"✅ Completion rate: {completion_rate:.1%}")
        logger.info(f"🎲 Monte Carlo P50: {monte_carlo_results.get('p50', 0):.1f} stories/week")
        
        return {
            'average_velocity': avg_stories_per_week,
            'velocity_variance': velocity_variance,
            'completion_rate': completion_rate,
            'total_historical_issues': len(historical_issues),
            'monte_carlo_forecast': monte_carlo_results,
            'sprint_pattern_used': getattr(self, '_current_sprint_pattern', ''),
            'estimate_accuracy': 1.0,  # Default accuracy multiplier
            'weekly_story_counts': weekly_story_counts
        }
    
    def _group_issues_by_week(self, issues: List[Dict]) -> List[int]:
        """
        Group completed issues by resolution week.
        
        Args:
            issues (List[Dict]): Historical issues
            
        Returns:
            List[int]: Story counts per week
        """
        from collections import defaultdict
        from dateutil import parser
        
        weekly_counts = defaultdict(int)
        
        for issue in issues:
            resolution_date = issue.get('resolution_date')
            if resolution_date:
                try:
                    # Parse resolution date and get week number
                    date_obj = parser.parse(resolution_date)
                    week_key = f"{date_obj.year}-W{date_obj.isocalendar()[1]:02d}"
                    weekly_counts[week_key] += 1
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse date {resolution_date}: {e}")
        
        # Return list of weekly story counts
        story_counts = list(weekly_counts.values())
        logger.info(f"📅 Found {len(story_counts)} weeks of velocity data")
        logger.info(f"📊 Weekly story completion data: {story_counts}")
        
        return story_counts
    
    def _run_monte_carlo_simulation(self, weekly_velocities: List[int], simulations: int = 10000) -> Dict:
        """
        Run Monte Carlo simulation for velocity forecasting.
        
        Args:
            weekly_velocities (List[int]): Historical weekly story counts
            simulations (int): Number of Monte Carlo simulations
            
        Returns:
            Dict: Monte Carlo forecast results
        """
        if not weekly_velocities:
            return {}
        
        logger.info(f"🎲 Running Monte Carlo simulation with {simulations} iterations")
        
        # Run simulations
        simulation_results = []
        for _ in range(simulations):
            # Randomly sample from historical velocities
            simulated_velocity = np.random.choice(weekly_velocities)
            simulation_results.append(simulated_velocity)
        
        # Calculate percentiles
        percentiles = {
            'p10': np.percentile(simulation_results, 10),
            'p25': np.percentile(simulation_results, 25),
            'p50': np.percentile(simulation_results, 50),  # Median
            'p75': np.percentile(simulation_results, 75),
            'p90': np.percentile(simulation_results, 90)
        }
        
        logger.info(f"🎲 Monte Carlo results - P10: {percentiles['p10']:.1f}, P50: {percentiles['p50']:.1f}, P90: {percentiles['p90']:.1f}")
        
        return {
            'percentiles': percentiles,
            'mean': np.mean(simulation_results),
            'std': np.std(simulation_results),
            'confidence_intervals': {
                '50%': (percentiles['p25'], percentiles['p75']),
                '80%': (percentiles['p10'], percentiles['p90'])
            }
        }
    
    def _generate_forecast_with_dates(self, workload: Dict, historical: Dict, sprint_details: Dict) -> Dict:
        """
        Generate sprint feasibility forecast with date comparison.
        
        Args:
            workload (Dict): Current sprint workload analysis
            historical (Dict): Historical velocity data
            sprint_details (Dict): Sprint details including dates
            
        Returns:
            Dict: Forecast results with date comparison
        """
        logger.info("🔮 Generating sprint feasibility forecast...")
        
        remaining_hours = workload['total_remaining_estimate']
        average_velocity = historical.get('average_velocity', 0)
        estimate_accuracy = historical.get('estimate_accuracy', 1)
        completion_rate = historical.get('completion_rate', 0.8)
        
        # Calculate days (hours/8)
        remaining_days = remaining_hours / 8
        
        # Get remaining story count for forecast
        remaining_stories = workload['total_issues'] - len([i for i in workload.get('issues_detail', []) if i.get('status', '').lower() in [s.lower() for s in self.completion_statuses]])
        
        # Forecast calculations using Monte Carlo results
        monte_carlo_data = historical.get('monte_carlo_forecast', {})
        if average_velocity > 0 and monte_carlo_data:
            # Use Monte Carlo P50 (median) multiplied by 3 for conservative estimate
            mc_velocity_base = monte_carlo_data.get('percentiles', {}).get('p50', average_velocity)
            mc_velocity = mc_velocity_base * 3  # Apply 3x multiplier
            
            estimated_weeks_needed = remaining_stories / mc_velocity if mc_velocity > 0 else remaining_hours / average_velocity
            estimated_days_needed = estimated_weeks_needed * 5  # 5 working days per week
            adjusted_hours = remaining_hours * estimate_accuracy
            
            # Calculate probability based on Monte Carlo confidence intervals with same multiplier
            probability_of_completion = self._calculate_monte_carlo_probability(remaining_stories, monte_carlo_data, multiplier=2)
            
            logger.info(f"🎲 Using Monte Carlo velocity: {mc_velocity_base:.1f} x 3 = {mc_velocity:.1f} stories/week for {remaining_stories} remaining stories")
        else:
            # Use configured team capacity
            team_capacity_per_day = self.team_size * self.hours_per_day
            team_capacity_per_week = team_capacity_per_day * 5  # Assume 5 working days per week
            
            # When no historical data, use team capacity
            estimated_weeks_needed = remaining_hours / team_capacity_per_week
            estimated_days_needed = remaining_hours / team_capacity_per_day
            adjusted_hours = remaining_hours
            probability_of_completion = 70  # More optimistic with known team capacity
            logger.info(f"📊 No historical velocity data - using configured capacity: {team_capacity_per_week}h/week, {team_capacity_per_day}h/day")
        
        # Enhanced risk assessment based on multiple factors
        risk_level = self._calculate_risk_level(remaining_hours, remaining_days, probability_of_completion, workload)
        
        # Recommendations
        recommendations = self._generate_recommendations(workload, historical, estimated_weeks_needed)
        
        # Generate scenario analysis
        scenario_analysis = self._generate_scenario_analysis(remaining_stories, monte_carlo_data, workload)
        
        # Calculate date-based forecast
        date_forecast = self._calculate_date_forecast(estimated_days_needed, sprint_details)
        
        forecast_result = {
            'estimated_weeks_needed': estimated_weeks_needed,
            'estimated_days_needed': estimated_days_needed,
            'remaining_days': remaining_days,
            'adjusted_hours_estimate': adjusted_hours,
            'probability_of_completion': probability_of_completion,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'monte_carlo_scenarios': scenario_analysis,
            'remaining_stories': remaining_stories,
            'date_forecast': date_forecast
        }
        
        logger.info(f"🔮 Forecast: {estimated_days_needed:.1f} days ({estimated_weeks_needed:.1f} weeks) needed, {probability_of_completion:.0f}% completion probability")
        
        return forecast_result
    
    def _calculate_monte_carlo_probability(self, remaining_stories: int, monte_carlo_data: Dict, multiplier: float = 1.0) -> float:
        """
        Calculate completion probability using Monte Carlo confidence intervals.
        
        Args:
            remaining_stories (int): Number of stories remaining
            monte_carlo_data (Dict): Monte Carlo simulation results
            multiplier (float): Velocity multiplier to apply (same as forecast)
            
        Returns:
            float: Probability of completion (0-100)
        """
        percentiles = monte_carlo_data.get('percentiles', {})
        if not percentiles:
            return 50.0  # Default probability
        
        # Apply the same multiplier used in forecast calculation
        p90_velocity = percentiles.get('p90', 0) * multiplier
        p50_velocity = percentiles.get('p50', 0) * multiplier
        p10_velocity = percentiles.get('p10', 0) * multiplier
        
        logger.info(f"🎲 Probability calculation: P90={p90_velocity:.1f}, P50={p50_velocity:.1f}, P10={p10_velocity:.1f} stories/week (multiplier={multiplier}x)")
        
        if remaining_stories == 0:
            return 100.0
        
        # Simple probability model based on velocity distribution
        if p90_velocity >= remaining_stories:
            return 90.0  # High confidence
        elif p50_velocity >= remaining_stories:
            return 70.0  # Medium confidence
        elif p10_velocity >= remaining_stories:
            return 30.0  # Low confidence
        else:
            return 10.0  # Very low confidence
    
    def _generate_scenario_analysis(self, remaining_stories: int, monte_carlo_data: Dict, workload: Dict) -> Dict:
        """
        Generate scenario analysis for different confidence levels.
        
        Args:
            remaining_stories (int): Number of stories remaining
            monte_carlo_data (Dict): Monte Carlo simulation results
            workload (Dict): Workload analysis data
            
        Returns:
            Dict: Scenario analysis with recommendations
        """
        if not monte_carlo_data or remaining_stories == 0:
            return {}
        
        percentiles = monte_carlo_data.get('percentiles', {})
        scenarios = {}
        
        # P90 Scenario (Optimistic)
        p90_velocity = percentiles.get('p90', 0)
        if p90_velocity > 0:
            stories_at_risk_p90 = max(0, remaining_stories - int(p90_velocity))
            scenarios['p90'] = {
                'velocity': p90_velocity,
                'confidence': '90%',
                'stories_at_risk': stories_at_risk_p90,
                'description': f'Best case: Team completes {int(p90_velocity)} stories/week',
                'recommendation': f'Remove {stories_at_risk_p90} lowest priority stories for 90% confidence' if stories_at_risk_p90 > 0 else 'All stories likely to be completed'
            }
        
        # P50 Scenario (Realistic)
        p50_velocity = percentiles.get('p50', 0)
        if p50_velocity > 0:
            stories_at_risk_p50 = max(0, remaining_stories - int(p50_velocity))
            scenarios['p50'] = {
                'velocity': p50_velocity,
                'confidence': '50%',
                'stories_at_risk': stories_at_risk_p50,
                'description': f'Typical case: Team completes {int(p50_velocity)} stories/week',
                'recommendation': f'Remove {stories_at_risk_p50} lowest priority stories for 50% confidence' if stories_at_risk_p50 > 0 else 'All stories likely to be completed'
            }
        
        # P10 Scenario (Pessimistic)
        p10_velocity = percentiles.get('p10', 0)
        if p10_velocity > 0:
            stories_at_risk_p10 = max(0, remaining_stories - int(p10_velocity))
            scenarios['p10'] = {
                'velocity': p10_velocity,
                'confidence': '10%',
                'stories_at_risk': stories_at_risk_p10,
                'description': f'Worst case: Team completes {int(p10_velocity)} stories/week',
                'recommendation': f'Remove {stories_at_risk_p10} lowest priority stories for conservative planning' if stories_at_risk_p10 > 0 else 'All stories likely to be completed'
            }
        
        return scenarios
    
    def _calculate_risk_level(self, remaining_hours: float, remaining_days: float, completion_probability: float, workload: Dict) -> str:
        """
        Calculate risk level based on multiple factors.
        
        Args:
            remaining_hours (float): Hours remaining
            remaining_days (float): Days remaining (hours/8)
            completion_probability (float): Probability of completion
            workload (Dict): Workload analysis data
            
        Returns:
            str: Risk level (LOW, MEDIUM, HIGH)
        """
        risk_factors = 0
        
        # Factor 1: High remaining workload (>10 days)
        if remaining_days > 10:
            risk_factors += 2
        elif remaining_days > 5:
            risk_factors += 1
        
        # Factor 2: Low completion probability
        if completion_probability < 60:
            risk_factors += 2
        elif completion_probability < 80:
            risk_factors += 1
        
        # Factor 3: Low progress if sprint is ongoing
        progress = workload.get('overall_progress', 0)
        if progress < 30 and remaining_hours > 100:  # Low progress with high remaining work
            risk_factors += 1
        
        # Factor 4: Many unestimated issues
        unestimated_ratio = workload.get('unestimated_issues', 0) / max(workload.get('total_issues', 1), 1)
        if unestimated_ratio > 0.3:
            risk_factors += 1
        
        # Determine risk level
        if risk_factors >= 3:
            return "HIGH"
        elif risk_factors >= 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, workload: Dict, historical: Dict, weeks_needed: float) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        remaining_days = workload['total_remaining_estimate'] / 8
        time_spent = workload.get('total_time_spent', 0)
        total_estimated = workload.get('total_original_estimate', 0)
        
        # Check for overtime situation
        if time_spent > total_estimated and total_estimated > 0:
            recommendations.append("🔴 Spent time exceeds planned estimates - discuss in next retrospective why estimates were exceeded")
        
        if workload['unestimated_issues'] > 0:
            recommendations.append(f"📝 {workload['unestimated_issues']} issues lack time estimates - prioritize estimation")
        
        if remaining_days > 10:
            recommendations.append(f"⚠️ High workload remaining ({remaining_days:.1f} days) - consider scope reduction")
        elif weeks_needed > 2:
            recommendations.append("⚠️ Sprint appears overcommitted - consider scope reduction")
        
        if historical.get('estimate_accuracy', 1) < 0.8:
            recommendations.append("📊 Historical estimates tend to be optimistic - add buffer time")
        
        if workload['overall_progress'] < 20 and remaining_days > 5:
            recommendations.append("🚀 Sprint just started with high workload - monitor progress closely")
        
        if workload['overall_progress'] < 50 and remaining_days > 8:
            recommendations.append("📈 Consider daily standups to track progress more closely")
        
        if not recommendations:
            recommendations.append("✅ Sprint appears well-balanced based on current analysis")
        
        return recommendations
    
    def _create_sprint_report(self, sprint_name: str, workload: Dict, forecast: Dict, historical: Dict) -> Dict:
        """Create comprehensive sprint analysis report."""
        return {
            'sprint_name': sprint_name,
            'analysis_date': datetime.now().isoformat(),
            'workload_analysis': workload,
            'forecast': forecast,
            'historical_context': historical,
            'summary': {
                'total_issues': workload['total_issues'],
                'total_estimated_hours': workload['total_original_estimate'],
                'remaining_hours': workload['total_remaining_estimate'],
                'completion_probability': forecast['probability_of_completion'],
                'risk_level': forecast['risk_level']
            }
        }
    
    def _get_similar_sprints(self, current_sprint_name: str, sprint_issues: List[Dict] = None, months_back: int = 6) -> str:
        """
        Get list of similar sprint names using SprintRetriever with fallback.
        
        Args:
            current_sprint_name (str): Current sprint name
            sprint_issues (List[Dict]): Current sprint issues to extract project info
            months_back (int): Months of historical data
            
        Returns:
            str: Comma-separated list of sprint names for JQL IN clause
        """
        try:
            # Use cached sprints if available
            cache_key = f"{current_sprint_name}_{months_back}"
            if cache_key not in self._sprint_cache:
                logger.info(f"💾 Caching sprints for {current_sprint_name}")
                # Set current sprint info for the retriever
                self.sprint_retriever.current_sprint_name = current_sprint_name
                if current_sprint_name.isdigit():
                    self.sprint_retriever.current_sprint_id = int(current_sprint_name)
                self._sprint_cache[cache_key] = self.sprint_retriever.get_sprints_from_same_board(current_sprint_name, months_back * 30)
            
            sprints = self._sprint_cache[cache_key]
            if sprints:
                similar_sprints = self._extract_similar_sprint_names(current_sprint_name, sprints)
                logger.info(f"✅ Using cached sprints: {len(similar_sprints)} similar sprints from same board")
                return similar_sprints
            else:
                logger.warning("⚠️ No sprints found from same board")
                return ''
            
        except Exception as e:
            logger.error(f"⚠️ Failed to get similar sprints: {str(e)}")
            return ''
    
    def _extract_similar_sprint_names(self, current_sprint_name: str, sprints: List[Dict]) -> str:
        """
        Extract similar sprint names from sprint list using pattern matching.
        
        Args:
            current_sprint_name (str): Current sprint name
            sprints (List[Dict]): List of sprint dictionaries
            
        Returns:
            str: Comma-separated list of sprint names for JQL IN clause
        """
        if not current_sprint_name or current_sprint_name.isdigit():
            return ''
        
        similar_sprints = []
        
        # Extract pattern from current sprint name
        import re
        pattern_match = re.match(r'^(.+?\s+Sprint)\s+\d+', current_sprint_name)
        if pattern_match:
            base_pattern = pattern_match.group(1)
            self._current_sprint_pattern = base_pattern + ' *'
            
            # Find sprints matching the pattern
            for sprint in sprints:
                sprint_name = sprint.get('name', '')
                if sprint_name.startswith(base_pattern) and sprint_name != current_sprint_name:
                    similar_sprints.append(f'"{sprint_name}"')
            
            logger.info(f"🔍 Found {len(similar_sprints)} similar sprints for pattern '{base_pattern}'")
            return ','.join(similar_sprints[:20])  # Limit to 20 sprints
        
        # Fallback: use first part before numbers
        fallback_match = re.match(r'^(.+?)\s+\d+', current_sprint_name)
        if fallback_match:
            base_pattern = fallback_match.group(1)
            self._current_sprint_pattern = base_pattern + ' *'
            
            for sprint in sprints:
                sprint_name = sprint.get('name', '')
                if sprint_name.startswith(base_pattern) and sprint_name != current_sprint_name:
                    similar_sprints.append(f'"{sprint_name}"')
            
            logger.info(f"🔍 Found {len(similar_sprints)} similar sprints for fallback pattern '{base_pattern}'")
            return ','.join(similar_sprints[:20])  # Limit to 20 sprints
        
        logger.warning(f"⚠️ Could not extract pattern from: '{current_sprint_name}'")
        return ''
    

    
    def _get_sprint_details(self, sprint_name: str, months_back: int = 6) -> Dict:
        """
        Get sprint details including planned end date using direct API call.
        
        Args:
            sprint_name (str): Sprint name or ID
            months_back (int): Not used but kept for compatibility
            
        Returns:
            Dict: Sprint details with dates
        """
        try:
            if not sprint_name:
                logger.warning("⚠️ Empty sprint name provided")
                return {}
            
            logger.info(f"🔍 Getting sprint details for: '{sprint_name}'")
            
            # Try direct API call if sprint is numeric (ID)
            if sprint_name.isdigit():
                url = f"{self.jira_client.base_url}/rest/agile/1.0/sprint/{sprint_name}"
                logger.info(f"🔍 Direct API call: {url}")
                response = self.jira_client.session.get(url)
                
                if response.status_code == 200:
                    sprint_data = response.json()
                    logger.info(f"📅 Direct sprint data: {sprint_data}")
                    return {
                        'id': sprint_data.get('id'),
                        'name': sprint_data.get('name'),
                        'state': sprint_data.get('state'),
                        'start_date': sprint_data.get('startDate'),
                        'end_date': sprint_data.get('endDate'),
                        'complete_date': sprint_data.get('completeDate')
                    }
            
            # Fallback to cached sprints
            cache_key = f"{sprint_name}_6"
            if cache_key in self._sprint_cache:
                logger.info(f"💾 Using cached sprints for sprint details")
                sprints = self._sprint_cache[cache_key]
                for sprint in sprints:
                    if sprint.get('name') == sprint_name or str(sprint.get('id')) == sprint_name:
                        logger.info(f"📅 Found sprint details from cache: {sprint}")
                        return sprint
            
            logger.warning(f"⚠️ Sprint details not found for: {sprint_name}")
            return {}
                
        except Exception as e:
            logger.error(f"⚠️ Failed to get sprint details for '{sprint_name}': {str(e)}")
            return {}
    
    def _calculate_date_forecast(self, estimated_days_needed: float, sprint_details: Dict) -> Dict:
        """
        Calculate date-based forecast comparing planned end date vs estimated completion.
        
        Args:
            estimated_days_needed (float): Estimated days needed to complete
            sprint_details (Dict): Sprint details including end date
            
        Returns:
            Dict: Date forecast with comparison
        """
        from dateutil import parser
        
        result = {
            'planned_end_date': None,
            'estimated_completion_date': None,
            'days_difference': 0,
            'will_finish_on_time': True,
            'missing_days': 0,
            'date_risk_level': 'LOW'
        }
        
        try:
            from datetime import date, timedelta
            today = date.today()
            estimated_completion = today + timedelta(days=int(estimated_days_needed))
            result['estimated_completion_date'] = estimated_completion.isoformat()
            
            planned_end_str = sprint_details.get('end_date')
            logger.info(f"📅 Sprint details received: {sprint_details}")
            logger.info(f"📅 Planned end date string: {planned_end_str}")
            
            if planned_end_str:
                # Parse planned end date
                planned_end = parser.parse(planned_end_str).date()
                result['planned_end_date'] = planned_end.isoformat()
                logger.info(f"📅 Parsed planned end date: {planned_end}")
                
                # Calculate difference
                days_diff = (estimated_completion - planned_end).days
                result['days_difference'] = days_diff
                result['will_finish_on_time'] = days_diff <= 0
                result['missing_days'] = max(0, days_diff)
                
                # Determine risk level based on date difference
                if days_diff <= 0:
                    result['date_risk_level'] = 'LOW'
                elif days_diff <= 3:
                    result['date_risk_level'] = 'MEDIUM'
                else:
                    result['date_risk_level'] = 'HIGH'
                
                logger.info(f"📅 Date forecast: Planned={planned_end}, Estimated={estimated_completion}, Diff={days_diff} days")
            else:
                # Fallback: No planned end date available
                logger.warning("⚠️ No planned end date found - using forecast-only timeline")
                result['planned_end_date'] = None
                result['days_difference'] = 0
                result['will_finish_on_time'] = True
                result['missing_days'] = 0
                result['date_risk_level'] = 'MEDIUM'  # Unknown timeline = medium risk
                
                logger.info(f"📅 Fallback forecast: Estimated completion={estimated_completion} (no planned date available)")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate date forecast: {str(e)}")
            # Ensure estimated completion date is always set
            from datetime import date, timedelta
            today = date.today()
            estimated_completion = today + timedelta(days=int(estimated_days_needed))
            result['estimated_completion_date'] = estimated_completion.isoformat()
            logger.info(f"📅 Fallback: Estimated completion={estimated_completion}")
        
        return result
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'sprint_name': '',
            'analysis_date': datetime.now().isoformat(),
            'workload_analysis': {},
            'forecast': {},
            'historical_context': {},
            'summary': {},
            'error': 'No data available for analysis'
        }

def print_sprint_report(analysis_result: Dict):
    """
    Print a formatted sprint analysis report to console.
    
    Args:
        analysis_result (Dict): Sprint analysis results
    """
    if 'error' in analysis_result:
        print(f"❌ Error: {analysis_result['error']}")
        return
    
    sprint_name = analysis_result['sprint_name']
    summary = analysis_result['summary']
    workload = analysis_result['workload_analysis']
    forecast = analysis_result['forecast']
    
    print("\n" + "="*60)
    print(f"📊 SPRINT ANALYSIS REPORT: {sprint_name}")
    print("="*60)
    
    print(f"\n📈 SUMMARY:")
    print(f"  • Total Issues: {summary['total_issues']}")
    print(f"  • Estimated Hours: {summary['total_estimated_hours']:.1f}h")
    print(f"  • Remaining Hours: {summary['remaining_hours']:.1f}h")
    print(f"  • Progress: {workload['overall_progress']:.1f}%")
    print(f"  • Risk Level: {summary['risk_level']}")
    
    print(f"\n🔮 FORECAST:")
    print(f"  • Completion Probability: {summary['completion_probability']:.0f}%")
    print(f"  • Estimated Weeks Needed: {forecast['estimated_weeks_needed']:.1f}")
    
    print(f"\n📋 STATUS BREAKDOWN:")
    for status, data in workload['status_breakdown'].items():
        print(f"  • {status}: {data['count']} issues, {data['remaining_estimate']:.1f}h remaining")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in forecast['recommendations']:
        print(f"  {rec}")
    
    print("\n" + "="*60)

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Analyze Jira sprint capacity and feasibility')
    parser.add_argument('--jira-url', required=True, help='Jira server URL')
    parser.add_argument('--token', required=True, help='Jira API token')
    parser.add_argument('--sprint', required=True, help='Sprint name or ID')
    parser.add_argument('--history-months', type=int, default=6, help='Months of historical data (default: 6)')
    
    args = parser.parse_args()
    
    try:
        # Initialize components
        logger.info("🚀 Starting Sprint Analyzer...")
        jira_client = JiraClient(args.jira_url, args.token)
        
        # Test connection
        if not jira_client.test_connection():
            logger.error("🚩 Failed to connect to Jira")
            sys.exit(1)
        
        logger.info("✅ Connected to Jira successfully")
        
        # Analyze sprint
        analyzer = SprintAnalyzer(jira_client)
        results = analyzer.analyze_sprint(args.sprint, args.history_months)
        
        # Print report
        print_sprint_report(results)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"🚩 Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()