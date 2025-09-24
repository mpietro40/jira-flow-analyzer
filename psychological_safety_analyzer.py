"""
Jira-Based Psychological Safety Indicators Analyzer
Analyzes team psychological safety through Jira comments and interactions.
"""

import json
import os
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from collections import defaultdict
import time
import hashlib

from jira_client import JiraClient

logger = logging.getLogger('PsychologicalSafetyAnalyzer')

class PsychologicalSafetyAnalyzer:
    """
    Analyzes psychological safety indicators from Jira comments and interactions.
    """
    
    def __init__(self, jira_client: JiraClient):
        """Initialize with Jira client."""
        self.jira_client = jira_client
        self.data_dir = os.path.join(os.path.dirname(__file__), 'safety_data')
        self.cache_dir = os.path.join(self.data_dir, 'cache')
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_ttl = 1800  # 30 minutes cache
        
        # Psychological safety indicators patterns
        self.question_patterns = [
            r'\?', r'\bhow\b', r'\bwhy\b', r'\bwhat if\b', r'\bwould\b', r'\bcould\b'
        ]
        
        self.disagreement_patterns = [
            r'\bhowever\b', r'\bbut\b', r'\balternatively\b', r'\bon the other hand\b',
            r'\bactually\b', r'\bdisagree\b', r'\bdifferent view\b'
        ]
        
        self.help_seeking_patterns = [
            r'\bhelp\b', r'\bguidance\b', r'\badvice\b', r'\bsupport\b',
            r'\bneed help\b', r'\bcan someone\b', r'\bany ideas\b'
        ]
        
        self.help_labels = ['help-needed', 'guidance', 'support', 'blocked']
    
    def analyze_weekly_safety(self, jql_query: str, week_year: Optional[str] = None) -> Dict:
        """
        Analyze psychological safety indicators for a specific week.
        
        Args:
            jql_query (str): JQL query to find root issues
            week_year (str): Week in format "YYYY-WW" (e.g., "2024-15")
            
        Returns:
            Dict: Analysis results with safety indicators
        """
        if not week_year:
            week_year = datetime.now().strftime("%Y-%W")
        
        logger.info(f"🔍 Starting psychological safety analysis for week {week_year}")
        
        # Check if data already exists for this week
        existing_data = self._load_weekly_data(week_year)
        if existing_data:
            logger.info(f"✅ Found existing data for week {week_year}")
            return existing_data
        
        try:
            # Get all issues from hierarchy
            all_issues = self._get_hierarchy_issues(jql_query)
            logger.info(f"📋 Found {len(all_issues)} issues in hierarchy")
            
            # Analyze safety indicators
            safety_data = self._analyze_safety_indicators(all_issues, week_year)
            
            # Save weekly data
            self._save_weekly_data(week_year, safety_data)
            
            logger.info(f"✅ Psychological safety analysis completed for week {week_year}")
            return safety_data
            
        except Exception as e:
            logger.error(f"🚩 Psychological safety analysis failed: {str(e)}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _get_hierarchy_issues(self, jql_query: str) -> List[Dict]:
        """Get all issues from hierarchy traversal with caching."""
        # Create cache key from JQL query
        cache_key = hashlib.md5(jql_query.encode()).hexdigest()
        cached_issues = self._load_cached_issues(cache_key)
        
        if cached_issues:
            logger.info(f"✅ Using cached hierarchy data ({len(cached_issues)} issues)")
            return cached_issues
        
        # Add filter to exclude issues without comments
        filtered_jql = f"({jql_query}) AND issueFunction not in hasComments(0)"
        logger.info(f"🔍 Using filtered JQL: {filtered_jql}")
        
        # Get root issues
        root_issues = self.jira_client.fetch_issues(filtered_jql, max_results=1000)
        all_issues = list(root_issues)
        
        # Traverse hierarchy for each root issue
        for root_issue in root_issues:
            try:
                child_issues = self._get_all_child_issues(root_issue['key'])
                all_issues.extend(child_issues)
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.warning(f"⚠️ Failed to get children for {root_issue['key']}: {str(e)}")
                continue
        
        # Remove duplicates
        unique_issues = {issue['key']: issue for issue in all_issues}
        final_issues = list(unique_issues.values())
        
        # Cache the results
        self._save_cached_issues(cache_key, final_issues)
        
        return final_issues
    
    def _get_all_child_issues(self, issue_key: str) -> List[Dict]:
        """Get all child issues recursively, filtering out those without comments."""
        jql_query = f'issuekey in childIssuesOf("{issue_key}") AND issueFunction not in hasComments(0)'
        
        try:
            child_issues = self.jira_client.fetch_issues(jql_query, max_results=2000)
            return child_issues
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch child issues for {issue_key}: {str(e)}")
            return []
    
    def _analyze_safety_indicators(self, issues: List[Dict], week_year: str) -> Dict:
        """Analyze psychological safety indicators from issues."""
        # Get week date range
        year, week = map(int, week_year.split('-'))
        week_start = datetime.strptime(f'{year}-W{week:02d}-1', "%Y-W%W-%w")
        week_end = week_start + timedelta(days=6)
        
        logger.info(f"📅 Analyzing week {week_year}: {week_start.date()} to {week_end.date()}")
        
        # Initialize counters
        team_members = set()
        commenting_members = set()
        total_comments = 0
        question_comments = 0
        disagreement_comments = 0
        help_seeking_issues = 0
        idea_contributors = set()
        
        # Analyze each issue
        for issue in issues:
            try:
                issue_key = issue['key']
                
                # Track issue creators for idea contribution
                creator = issue.get('creator', '')
                if creator:
                    idea_contributors.add(creator)
                    team_members.add(creator)
                
                # Check for help-seeking labels
                labels = issue.get('labels', [])
                if any(label.lower() in self.help_labels for label in labels):
                    help_seeking_issues += 1
                
                # Get and analyze comments
                comments = self._get_issue_comments(issue_key, week_start, week_end)
                
                for comment in comments:
                    total_comments += 1
                    author = comment.get('author', '')
                    body = comment.get('body', '').lower()
                    
                    if author:
                        team_members.add(author)
                        commenting_members.add(author)
                    
                    # Check for questions
                    if any(re.search(pattern, body, re.IGNORECASE) for pattern in self.question_patterns):
                        question_comments += 1
                    
                    # Check for disagreement indicators
                    if any(re.search(pattern, body, re.IGNORECASE) for pattern in self.disagreement_patterns):
                        disagreement_comments += 1
                
                time.sleep(0.05)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to analyze issue {issue.get('key', 'unknown')}: {str(e)}")
                continue
        
        # Calculate metrics
        total_team_members = len(team_members)
        participation_rate = (len(commenting_members) / max(total_team_members, 1)) * 100
        question_rate = (question_comments / max(total_comments, 1)) * 100
        disagreement_rate = (disagreement_comments / max(total_comments, 1)) * 100
        
        safety_data = {
            'week': week_year,
            'analysis_date': datetime.now().isoformat(),
            'metrics': {
                'comment_participation_rate': round(participation_rate, 1),
                'question_frequency': round(question_rate, 1),
                'disagreement_indicators': round(disagreement_rate, 1),
                'help_seeking_issues': help_seeking_issues,
                'idea_contributors': len(idea_contributors)
            },
            'raw_data': {
                'total_team_members': total_team_members,
                'commenting_members': len(commenting_members),
                'total_comments': total_comments,
                'question_comments': question_comments,
                'disagreement_comments': disagreement_comments,
                'total_issues': len(issues)
            },
            'team_members': list(team_members),
            'commenting_members': list(commenting_members)
        }
        
        logger.info(f"📊 Safety metrics: Participation {participation_rate:.1f}%, Questions {question_rate:.1f}%, Disagreements {disagreement_rate:.1f}%")
        
        return safety_data
    
    def _get_issue_comments(self, issue_key: str, week_start: datetime, week_end: datetime) -> List[Dict]:
        """Get comments for an issue within the week range."""
        try:
            comments = self.jira_client.get_issue_comments(issue_key)
            
            # Filter comments by date range
            week_comments = []
            for comment in comments:
                try:
                    # Parse comment date
                    created_str = comment.get('created', '')
                    if created_str:
                        # Handle Jira datetime format
                        created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        created_date = created_date.replace(tzinfo=None)  # Remove timezone for comparison
                        
                        if week_start <= created_date <= week_end:
                            week_comments.append({
                                'author': comment.get('author', {}).get('displayName', ''),
                                'body': comment.get('body', ''),
                                'created': created_str
                            })
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse comment date: {str(e)}")
                    continue
            
            return week_comments
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get comments for {issue_key}: {str(e)}")
            return []
    
    def _save_weekly_data(self, week_year: str, data: Dict):
        """Save weekly analysis data to local storage."""
        filename = f"safety_data_{week_year}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"💾 Saved weekly data to {filepath}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save weekly data: {str(e)}")
    
    def _load_weekly_data(self, week_year: str) -> Optional[Dict]:
        """Load existing weekly analysis data."""
        filename = f"safety_data_{week_year}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Failed to load weekly data: {str(e)}")
        
        return None
    
    def get_historical_data(self, weeks_back: int = 12) -> List[Dict]:
        """Get historical safety data for the last N weeks."""
        historical_data = []
        current_date = datetime.now()
        
        for i in range(weeks_back):
            week_date = current_date - timedelta(weeks=i)
            week_year = week_date.strftime("%Y-%W")
            
            data = self._load_weekly_data(week_year)
            if data:
                historical_data.append(data)
        
        return sorted(historical_data, key=lambda x: x['week'])
    
    def get_safety_trends(self, weeks_back: int = 12) -> Dict:
        """Analyze trends in psychological safety indicators."""
        historical_data = self.get_historical_data(weeks_back)
        
        if not historical_data:
            return {'error': 'No historical data available'}
        
        # Extract metrics for trend analysis
        weeks = [data['week'] for data in historical_data]
        participation_rates = [data['metrics']['comment_participation_rate'] for data in historical_data]
        question_frequencies = [data['metrics']['question_frequency'] for data in historical_data]
        disagreement_rates = [data['metrics']['disagreement_indicators'] for data in historical_data]
        help_seeking = [data['metrics']['help_seeking_issues'] for data in historical_data]
        
        # Calculate trends (simple average of last 3 vs first 3 weeks)
        def calculate_trend(values):
            if len(values) < 6:
                return 0
            recent_avg = sum(values[-3:]) / 3
            early_avg = sum(values[:3]) / 3
            return recent_avg - early_avg
        
        trends = {
            'participation_trend': round(calculate_trend(participation_rates), 1),
            'question_trend': round(calculate_trend(question_frequencies), 1),
            'disagreement_trend': round(calculate_trend(disagreement_rates), 1),
            'help_seeking_trend': round(calculate_trend(help_seeking), 1)
        }
        
        return {
            'weeks': weeks,
            'participation_rates': participation_rates,
            'question_frequencies': question_frequencies,
            'disagreement_rates': disagreement_rates,
            'help_seeking': help_seeking,
            'trends': trends,
            'total_weeks': len(historical_data)
        }
    
    def _load_cached_issues(self, cache_key: str) -> Optional[List[Dict]]:
        """Load cached issues if still valid."""
        cache_file = os.path.join(self.cache_dir, f"issues_{cache_key}.json")
        
        try:
            if os.path.exists(cache_file):
                # Check if cache is still valid
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < self.cache_ttl:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                else:
                    # Remove expired cache
                    os.remove(cache_file)
        except Exception as e:
            logger.warning(f"⚠️ Failed to load cached issues: {str(e)}")
        
        return None
    
    def _save_cached_issues(self, cache_key: str, issues: List[Dict]):
        """Save issues to cache."""
        cache_file = os.path.join(self.cache_dir, f"issues_{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(issues, f, indent=2, default=str)
            logger.info(f"💾 Cached {len(issues)} issues with key {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save cached issues: {str(e)}")
    
    def clear_cache(self):
        """Clear all cached data."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.startswith('issues_'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logger.info("🗑️ Cache cleared successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clear cache: {str(e)}")