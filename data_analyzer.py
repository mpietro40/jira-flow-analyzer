"""
Data Analysis Module
Analyzes Jira issue data to calculate metrics and generate insights.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from dateutil import parser
from scipy import stats
import pytz

# Configure logger with proper name
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JiraAnalyzer')

class DataAnalyzer:
    """
    Analyzes Jira issue data to calculate agile metrics.
    
    This class processes issue data to calculate lead times, cycle times,
    and time spent in various statuses.
    """
    
    def __init__(self):
        """Initialize the data analyzer."""
        self.status_mappings = {
            'in_progress': ['In Progress', 'In Development', 'Development', 'Doing','Work In Progress','Active','In analysis',
                            'Analysis in progress','Implementation in progress', 'Planning', 'realization', 'Executing'],
            'testing': ['Testing','To Test', 'In Testing', 'Test', 'QA', 'Quality Assurance', 'Fixed'],
            'validation': ['Validation', 'To Validate', 'In Review', 'Review', 'Validation', 'Acceptance', 'verify'],
            'done': ['Done', 'Closed', 'Resolved', 'Complete', 'Finished', 'Completed', 'Delivered', 'Released', 'Close', 'PRD Deployed'
                     ],
            'waiting': ['Waiting', 'New', 'Open', 'Accepted', 'Information needed', 'On Hold', 'Blocked', 'Pending',
                        'Deployment requested','Estimation', 'To Deploy', 'Waiting for Deployment', 'Waiting for Release', 
                        'Waiting for Approval', 'Waiting for Feedback', 'Waiting for Review', 'Waiting for Test', 
                        'Waiting for Validation', 'Analysis - Wait Customer','Need info', 'Authorization', 'GLOBAL BACKLOG', 'ToDo']
        }
        # Store discovered statuses for debugging
        self.discovered_statuses = set()
    
    def _discover_and_map_statuses(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Discover actual status names in the data and create enhanced mappings.
        Uses fuzzy matching against existing status_mappings.
        
        Args:
            df (pd.DataFrame): DataFrame with issue data
            
        Returns:
            Dict[str, List[str]]: Enhanced status mappings
        """
        # Collect all unique status names from the data
        all_statuses = set()
        
        for _, issue in df.iterrows():
            if issue['current_status']:
                all_statuses.add(issue['current_status'])
            
            for transition in issue['status_transitions']:
                if transition.get('from_status'):
                    all_statuses.add(transition['from_status'])
                if transition.get('to_status'):
                    all_statuses.add(transition['to_status'])
        
        self.discovered_statuses = all_statuses
        logger.info(f"🔍 Discovered statuses in data: {sorted(all_statuses)}")
        
        # Create enhanced mappings with fuzzy matching
        enhanced_mappings = {k: list(v) for k, v in self.status_mappings.items()}
        
        # Auto-map unmapped statuses using fuzzy matching against existing mappings
        for status in all_statuses:
            already_mapped = any(status in mapping for mapping in enhanced_mappings.values())
            
            if not already_mapped:
                best_match = self._find_best_status_match(status, enhanced_mappings)
                if best_match:
                    enhanced_mappings[best_match].append(status)
                    logger.info(f"🔗 Auto-mapped '{status}' to '{best_match}'")
        
        return enhanced_mappings
    
    def _find_best_status_match(self, status: str, mappings: Dict[str, List[str]]) -> str:
        """
        Find the best matching status category using fuzzy matching.
        
        Args:
            status (str): Status to match
            mappings (Dict[str, List[str]]): Current status mappings
            
        Returns:
            str: Best matching category or None
        """
        status_lower = status.lower()
        best_score = 0
        best_category = None
        
        for category, known_statuses in mappings.items():
            for known_status in known_statuses:
                known_lower = known_status.lower()
                
                # Exact match
                if status_lower == known_lower:
                    return category
                
                # Substring match
                if status_lower in known_lower or known_lower in status_lower:
                    score = min(len(status_lower), len(known_lower)) / max(len(status_lower), len(known_lower))
                    if score > best_score:
                        best_score = score
                        best_category = category
                
                # Word overlap
                status_words = set(status_lower.split())
                known_words = set(known_lower.split())
                overlap = len(status_words & known_words)
                if overlap > 0:
                    score = overlap / max(len(status_words), len(known_words))
                    if score > best_score:
                        best_score = score
                        best_category = category
        
        return best_category if best_score > 0.3 else None
    
    def analyze_issues(self, issues: List[Dict], months_back: int = 3) -> Dict:
        """
        Analyze issues to calculate metrics and generate insights.
        
        Args:
            issues (List[Dict]): List of processed Jira issues
            months_back (int): Number of months to analyze
            
        Returns:
            Dict: Analysis results including metrics and distributions
        """
        logger.info(f"📊 Analyzing {len(issues)} issues for {months_back} months")
        
        # Convert to DataFrame for easier analysis
        df = self._create_dataframe(issues)
        
        # Discover and map statuses from actual data
        if not df.empty:
            self.status_mappings = self._discover_and_map_statuses(df)
        
        if df.empty:
            return self._empty_analysis_result()
        
        # Filter by date range - make sure we use timezone-aware comparison
        cutoff_date = self._get_timezone_aware_cutoff_date(df, months_back)
        df_filtered = df[df['created'] >= cutoff_date].copy()
        
        logger.info(f"📅 Filtered to {len(df_filtered)} issues within date range")
        
        if df_filtered.empty:
            return self._empty_analysis_result()
        
        # Calculate metrics
        lead_times = self._calculate_lead_times(df_filtered)
        cycle_times = self._calculate_cycle_times(df_filtered)
        status_durations = self._calculate_status_durations(df_filtered)
        
        # Generate distributions
        distributions = self._calculate_distributions(lead_times, cycle_times, status_durations)
        
        # Calculate summary metrics
        metrics = self._calculate_summary_metrics(lead_times, cycle_times, status_durations)
        
        # Log discovered statuses for debugging
        logger.info(f"🗺️ Final status mappings: {self.status_mappings}")
        for status_type, durations in status_durations.items():
            logger.info(f"📏 {status_type}: {len(durations)} measurements")
        
        # Enhanced logging for debugging
        logger.info("📈 === ANALYSIS RESULTS ===")
        logger.info(f"📊 Total issues analyzed: {len(df_filtered)}")
        logger.info(f"⏱️ Lead times calculated: {len(lead_times)}")

        logger.info("⏳ Cycle time measurements by status:")
        for status_type, durations in status_durations.items():
            count = len(durations)
            avg_duration = np.mean(durations) if durations else 0
            logger.info(f"  📊 {status_type}: {count} measurements, avg {avg_duration:.1f} days")

        # Check for Done transitions
        done_transitions = 0
        for _, issue in df_filtered.iterrows():
            for transition in issue['status_transitions']:
                if self._is_status_type(transition.get('to_status', ''), 'done'):
                    done_transitions += 1

        logger.info(f"✅ Issues with transitions to Done status: {done_transitions}")

        # Log unmapped statuses
        mapped_statuses = set()
        for status_list in self.status_mappings.values():
            mapped_statuses.update(status_list)

        unmapped = self.discovered_statuses - mapped_statuses
        if unmapped:
            logger.warning(f"⚠️ Unmapped statuses found: {sorted(list(unmapped))}")
        else:
            logger.info(f"✅ All discovered statuses were successfully mapped")
        
        return {
            'metrics': metrics,
            'distributions': distributions,
            'lead_times': lead_times,
            'cycle_times': cycle_times,
            'status_durations': status_durations,
            'analysis_period': f"{months_back} months",
            'total_issues': len(df_filtered)
        }
    
    
    def _get_timezone_aware_cutoff_date(self, df: pd.DataFrame, months_back: int) -> pd.Timestamp:
        """
        Get a timezone-aware cutoff date that matches the data's timezone.
        
        Args:
            df (pd.DataFrame): DataFrame with created dates
            months_back (int): Number of months to go back
            
        Returns:
            pd.Timestamp: Timezone-aware cutoff date
        """
        if df.empty or 'created' not in df.columns:
            # Fallback to UTC timezone
            return pd.Timestamp.now(tz=pytz.UTC) - pd.DateOffset(months=months_back)
        
        # Get the timezone from the first valid created date
        first_date = df['created'].dropna().iloc[0] if not df['created'].dropna().empty else None
        
        if first_date is None or first_date.tz is None:
            # No timezone info, use naive datetime
            return pd.Timestamp.now() - pd.DateOffset(months=months_back)
        
        # Use the same timezone as the data
        tz = first_date.tz
        return pd.Timestamp.now(tz=tz) - pd.DateOffset(months=months_back)
    
    def _create_dataframe(self, issues: List[Dict]) -> pd.DataFrame:
        """
        Convert issues list to pandas DataFrame.
        
        Args:
            issues (List[Dict]): List of issue dictionaries
            
        Returns:
            pd.DataFrame: DataFrame with parsed dates and status transitions
        """
        data = []
        
        for issue in issues:
            try:
                # Parse dates with timezone handling
                created = self._parse_date_safe(issue.get('created'))
                resolution_date = self._parse_date_safe(issue.get('resolution_date'))
                
                # Process status history
                status_transitions = []
                for transition in issue.get('status_history', []):
                    try:
                        changed_date = self._parse_date_safe(transition.get('changed'))
                        if changed_date:
                            status_transitions.append({
                                'from_status': transition.get('from_status', ''),
                                'to_status': transition.get('to_status', ''),
                                'changed': changed_date
                            })
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to parse transition date for {issue.get('key', 'unknown')}: {str(e)}")
                        continue
                
                data.append({
                    'key': issue.get('key', ''),
                    'summary': issue.get('summary', ''),
                    'current_status': issue.get('status', ''),
                    'issue_type': issue.get('issue_type', ''),
                    'priority': issue.get('priority', ''),
                    'created': created,
                    'resolution_date': resolution_date,
                    'assignee': issue.get('assignee', ''),
                    'status_transitions': status_transitions
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process issue {issue.get('key', 'unknown')}: {str(e)}")
                continue
        
        return pd.DataFrame(data)
    
    def _parse_date_safe(self, date_str: str) -> pd.Timestamp:
        """
        Safely parse a date string, handling timezone issues.
        
        Args:
            date_str (str): Date string to parse
            
        Returns:
            pd.Timestamp: Parsed date or None if parsing fails
        """
        if not date_str:
            return None
        
        try:
            # Parse the date string
            parsed_date = parser.parse(date_str)
            
            # Convert to pandas Timestamp
            return pd.Timestamp(parsed_date)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse date '{date_str}': {str(e)}")
            return None
    
    def _calculate_lead_times(self, df: pd.DataFrame) -> List[float]:
        """
        Calculate lead times from first 'In Progress' to 'Done'.
        
        Args:
            df (pd.DataFrame): DataFrame with issue data
            
        Returns:
            List[float]: List of lead times in days
        """
        lead_times = []
        
        for _, issue in df.iterrows():
            try:
                in_progress_date = None
                done_date = None
                
                # Find first 'In Progress' transition
                for transition in issue['status_transitions']:
                    if self._is_status_type(transition['to_status'], 'in_progress'):
                        in_progress_date = transition['changed']
                        break
                
                # Find last 'Done' transition
                for transition in reversed(issue['status_transitions']):
                    if self._is_status_type(transition['to_status'], 'done'):
                        done_date = transition['changed']
                        break
                
                # Calculate lead time if both dates found
                if in_progress_date and done_date and pd.notna(in_progress_date) and pd.notna(done_date):
                    # Convert to timezone-naive for calculation if needed
                    if hasattr(in_progress_date, 'tz') and hasattr(done_date, 'tz'):
                        if in_progress_date.tz != done_date.tz:
                            # Convert both to UTC for comparison
                            in_progress_date = in_progress_date.tz_convert('UTC') if in_progress_date.tz else in_progress_date.tz_localize('UTC')
                            done_date = done_date.tz_convert('UTC') if done_date.tz else done_date.tz_localize('UTC')
                    
                    lead_time_delta = done_date - in_progress_date
                    lead_time = lead_time_delta.total_seconds() / (24 * 3600)
                    
                    if lead_time > 0:  # Only positive lead times
                        lead_times.append(lead_time)
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to calculate lead time for {issue['key']}: {str(e)}")
                continue
        
        logger.info(f"✅ Calculated {len(lead_times)} lead times")
        return lead_times
    
    def _calculate_cycle_times(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """
        Calculate time spent in each status category.
        
        Args:
            df (pd.DataFrame): DataFrame with issue data
            
        Returns:
            Dict[str, List[float]]: Dictionary with cycle times for each status
        """
        cycle_times = {
            'in_progress': [],
            'testing': [],
            'validation': [],
            'waiting': [],
            'total': []
        }
        
        for _, issue in df.iterrows():
            try:
                status_durations = self._calculate_issue_status_durations(issue)
                
                for status_type, duration in status_durations.items():
                    if duration > 0:
                        cycle_times[status_type].append(duration)
                
                # Calculate total cycle time
                total_cycle = sum(status_durations.values())
                if total_cycle > 0:
                    cycle_times['total'].append(total_cycle)
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to calculate cycle times for {issue['key']}: {str(e)}")
                continue
        
        return cycle_times
    
    def _calculate_issue_status_durations(self, issue: pd.Series) -> Dict[str, float]:
        """
        Calculate time spent in each status for a single issue.
        
        Args:
            issue (pd.Series): Single issue row
            
        Returns:
            Dict[str, float]: Duration in days for each status type
        """
        durations = {
            'in_progress': 0.0,
            'testing': 0.0,
            'waiting': 0.0,
            'validation': 0.0
        }
        
        transitions = issue['status_transitions']
        if not transitions:
            return durations
        
        # Sort transitions by date
        try:
            transitions = sorted(transitions, key=lambda x: x['changed'])
        except Exception as e:
            logger.warning(f"⚠️ Failed to sort transitions for {issue['key']}: {str(e)}")
            return durations
        
        current_status = None
        current_start = None
        
        for transition in transitions:
            try:
                # End previous status
                if current_status and current_start and pd.notna(current_start):
                    transition_date = transition['changed']
                    if pd.notna(transition_date):
                        # Handle timezone differences
                        if hasattr(current_start, 'tz') and hasattr(transition_date, 'tz'):
                            if current_start.tz != transition_date.tz:
                                current_start = current_start.tz_convert('UTC') if current_start.tz else current_start.tz_localize('UTC')
                                transition_date = transition_date.tz_convert('UTC') if transition_date.tz else transition_date.tz_localize('UTC')
                        
                        duration_delta = transition_date - current_start
                        duration = duration_delta.total_seconds() / (24 * 3600)
                        
                        for status_type, status_names in self.status_mappings.items():
                            if status_type in durations and current_status in status_names:
                                durations[status_type] += duration
                                break
                
                # Start new status
                current_status = transition['to_status']
                current_start = transition['changed']
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process transition for {issue['key']}: {str(e)}")
                continue
        
        # Handle final status if issue is still in progress
        try:
            if current_status and current_start and pd.notna(current_start):
                end_time = issue['resolution_date'] if pd.notna(issue['resolution_date']) else pd.Timestamp.now(tz=current_start.tz if hasattr(current_start, 'tz') else None)
                
                if pd.notna(end_time):
                    # Handle timezone differences
                    if hasattr(current_start, 'tz') and hasattr(end_time, 'tz'):
                        if current_start.tz != end_time.tz:
                            current_start = current_start.tz_convert('UTC') if current_start.tz else current_start.tz_localize('UTC')
                            end_time = end_time.tz_convert('UTC') if end_time.tz else end_time.tz_localize('UTC')
                    
                    duration_delta = end_time - current_start
                    duration = duration_delta.total_seconds() / (24 * 3600)
                    
                    for status_type, status_names in self.status_mappings.items():
                        if status_type in durations and current_status in status_names:
                            durations[status_type] += duration
                            break
        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate final status duration for {issue['key']}: {str(e)}")
        
        return durations
    
    def _calculate_status_durations(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """
        Calculate status durations for all issues.
        
        Args:
            df (pd.DataFrame): DataFrame with issue data
            
        Returns:
            Dict[str, List[float]]: Status durations for each category
        """
        all_durations = {
            'in_progress': [],
            'testing': [],
            'waiting': [],
            'validation': []
        }
        
        for _, issue in df.iterrows():
            durations = self._calculate_issue_status_durations(issue)
            for status_type, duration in durations.items():
                if duration > 0:
                    all_durations[status_type].append(duration)
        
        return all_durations
    
    def _calculate_distributions(self, lead_times: List[float], 
                               cycle_times: Dict[str, List[float]], 
                               status_durations: Dict[str, List[float]]) -> Dict:
        """
        Calculate statistical distributions for all metrics.
        
        Args:
            lead_times (List[float]): Lead time data
            cycle_times (Dict[str, List[float]]): Cycle time data
            status_durations (Dict[str, List[float]]): Status duration data
            
        Returns:
            Dict: Statistical distributions and parameters
        """
        distributions = {}
        
        # Lead time distribution
        if lead_times:
            distributions['lead_time'] = self._fit_gaussian_distribution(lead_times)
        
        # Cycle time distributions
        for status, times in cycle_times.items():
            if times:
                distributions[f'cycle_time_{status}'] = self._fit_gaussian_distribution(times)
        
        # Status duration distributions
        for status, durations in status_durations.items():
            if durations:
                distributions[f'status_{status}'] = self._fit_gaussian_distribution(durations)
        
        return distributions
    
    def _fit_gaussian_distribution(self, data: List[float]) -> Dict:
        """
        Fit Gaussian distribution to data.
        
        Args:
            data (List[float]): Data points
            
        Returns:
            Dict: Distribution parameters and statistics
        """
        if not data:
            return {}
        
        data_array = np.array(data)
        
        # Calculate basic statistics
        mean = np.mean(data_array)
        std = np.std(data_array)
        median = np.median(data_array)
        
        # Fit normal distribution
        params = stats.norm.fit(data_array)
        
        # Perform normality test
        if len(data_array) > 3:
            try:
                _, p_value = stats.shapiro(data_array)
            except Exception:
                p_value = None
        else:
            p_value = None
        
        return {
            'mean': mean,
            'std': std,
            'median': median,
            'count': len(data_array),
            'min': np.min(data_array),
            'max': np.max(data_array),
            'distribution_params': {
                'loc': params[0],  # mean
                'scale': params[1]  # std
            },
            'normality_test_p_value': p_value,
            'is_normal': p_value > 0.05 if p_value else None
        }
    
    def _calculate_summary_metrics(self, lead_times: List[float], 
                                 cycle_times: Dict[str, List[float]], 
                                 status_durations: Dict[str, List[float]]) -> Dict:
        """
        Calculate summary metrics for dashboard display.
        
        Args:
            lead_times (List[float]): Lead time data
            cycle_times (Dict[str, List[float]]): Cycle time data
            status_durations (Dict[str, List[float]]): Status duration data
            
        Returns:
            Dict: Summary metrics
        """
        metrics = {}
        
        # Lead time metrics
        if lead_times:
            metrics['lead_time'] = {
                'average': np.mean(lead_times),
                'median': np.median(lead_times),
                'p85': np.percentile(lead_times, 85),
                'p95': np.percentile(lead_times, 95)
            }
        
        # Cycle time metrics
        for status, times in cycle_times.items():
            if times:
                metrics[f'cycle_time_{status}'] = {
                    'average': np.mean(times),
                    'median': np.median(times),
                    'p85': np.percentile(times, 85),
                    'p95': np.percentile(times, 95)
                }
        
        return metrics
    
    def _is_status_type(self, status_name: str, status_type: str) -> bool:
        """
        Check if a status name belongs to a specific status type.
        
        Args:
            status_name (str): Status name to check
            status_type (str): Status type category
            
        Returns:
            bool: True if status belongs to type
        """
        if status_type not in self.status_mappings:
            return False
        
        return status_name in self.status_mappings[status_type]
    
    def _empty_analysis_result(self) -> Dict:
        """
        Return empty analysis result structure.
        
        Returns:
            Dict: Empty result structure
        """
        return {
            'metrics': {},
            'distributions': {},
            'lead_times': [],
            'cycle_times': {},
            'status_durations': {},
            'analysis_period': '0 months',
            'total_issues': 0
        }