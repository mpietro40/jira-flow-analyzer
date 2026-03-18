"""
Hierarchical Lead Time Analyzer
Extends lead time analysis with hierarchical traversal capabilities.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import defaultdict
import hashlib

from src.common.jira_client import JiraClient

logger = logging.getLogger('HierarchyAnalyzer')

class HierarchyAnalyzer:
    """
    Analyzes lead times using hierarchical traversal from initiatives to child issues.
    Includes persistent state management for large dataset processing.
    """
    max_results = 2000  # Max results per JIRA API call
    
    def __init__(self, jira_client: JiraClient):
        """Initialize hierarchy analyzer with Jira client."""
        self.jira_client = jira_client
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'analysis_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Default issue types for hierarchy traversal
        self.hierarchy_issue_types = [
            "Business Initiative", "Initiative", "Epic", "Feature", 
            "Sub-Feature", "Story", "Bug", "Task", "Sub-task",
            "Technical Task", "Defect", "Improvement","incident",
            "Incident (Sub-Task)","Evolution","Documentation"
        ]
    
    def analyze_hierarchy(self, jql_query: str, months_back: int = 3) -> Dict:
        """
        Analyze lead times using hierarchical traversal.
        
        Args:
            jql_query (str): JQL query to find root initiatives
            months_back (int): Number of months to analyze
            
        Returns:
            Dict: Analysis results with hierarchy information
        """
        analysis_id = self._generate_analysis_id(jql_query, months_back)
        logger.info(f"🔍 Starting hierarchical analysis: {analysis_id}")
        
        # Check for existing analysis state
        state = self._load_analysis_state(analysis_id)
        
        if state and state.get('status') == 'completed':
            logger.info("✅ Found completed analysis, returning cached results")
            cached_results = state.get('results', {})
            
            # Validate cached results structure
            if self._validate_results_structure(cached_results):
                logger.info("✅ Cached results validated successfully")
                
                # Generate comprehensive report if missing
                if 'comprehensive_report' not in cached_results:
                    logger.info("📊 Generating missing comprehensive report for cached results")
                    from apps.lead_time_analyzer.analysis_reporter import AnalysisReporter
                    reporter = AnalysisReporter()
                    cached_results['comprehensive_report'] = reporter.generate_comprehensive_report(cached_results)
                
                return cached_results
            else:
                logger.warning("⚠️ Cached results invalid, forcing re-analysis")
                state = None  # Force re-analysis
        
        try:
            # Step 1: Find root initiatives
            if not state or state.get('step', 0) < 1:
                logger.info("📋 Step 1: Finding root initiatives...")
                initiatives = self._fetch_initiatives(jql_query)
                self._save_analysis_state(analysis_id, {
                    'step': 1,
                    'status': 'in_progress',
                    'initiatives': initiatives,
                    'total_initiatives': len(initiatives),
                    'processed_initiatives': 0,
                    'all_issues': [],
                    'start_time': datetime.now().isoformat()
                })
                state = self._load_analysis_state(analysis_id)
            
            # Step 2: Traverse hierarchy for each initiative
            if state.get('step', 0) < 2:
                logger.info("🌳 Step 2: Traversing hierarchy...")
                all_issues = self._traverse_hierarchy(analysis_id, state)
                
                # Update state with all collected issues
                state['step'] = 2
                state['all_issues'] = all_issues
                state['total_issues'] = len(all_issues)
                self._save_analysis_state(analysis_id, state)
            
            # Step 3: Analyze lead times
            if state.get('step', 0) < 3:
                logger.info("📊 Step 3: Analyzing lead times...")
                from apps.lead_time_analyzer.data_analyzer import DataAnalyzer
                
                analyzer = DataAnalyzer()
                results = analyzer.analyze_issues(state['all_issues'], months_back)
                
                # Add hierarchy metadata
                results['hierarchy_metadata'] = {
                    'analysis_id': analysis_id,
                    'total_initiatives': state.get('total_initiatives', 0),
                    'total_issues': state.get('total_issues', 0),
                    'analysis_type': 'hierarchical',
                    'root_query': jql_query
                }
                
                # Ensure projects are included in results
                if 'projects' not in results:
                    results['projects'] = []
                
                # Ensure people involvement is included in results
                if 'people_involvement' not in results:
                    results['people_involvement'] = {'overall': {'total_people': 0, 'reporters': 0, 'assignees': 0, 'commenters': 0}, 'by_project': {}}
                
                # Log the final results structure for debugging
                logger.info(f"📊 Final results structure: {list(results.keys())}")
                logger.info(f"👥 People involvement data: {results.get('people_involvement', {})}")
                logger.info(f"🏢 Projects data: {results.get('projects', [])}")
                
                # Generate comprehensive report
                logger.info("📊 Generating comprehensive report...")
                logger.info(f"📊 Lead times available: {len(results.get('lead_times', []))}")
                try:
                    from apps.lead_time_analyzer.analysis_reporter import AnalysisReporter
                    reporter = AnalysisReporter()
                    comprehensive_report = reporter.generate_comprehensive_report(results)
                    results['comprehensive_report'] = comprehensive_report
                    logger.info(f"✅ Comprehensive report generated successfully: {list(comprehensive_report.keys())}")
                except Exception as e:
                    import traceback
                    logger.error(f"🚩 Failed to generate comprehensive report: {str(e)}")
                    logger.error(f"🚩 Full traceback: {traceback.format_exc()}")
                    results['comprehensive_report'] = {'error': f'Report generation failed: {str(e)}'}
                
                # Mark as completed
                state['step'] = 3
                state['status'] = 'completed'
                state['results'] = results
                state['completion_time'] = datetime.now().isoformat()
                self._save_analysis_state(analysis_id, state)
                
                logger.info("✅ Hierarchical analysis completed successfully")
                return results
            
        except Exception as e:
            logger.error(f"🚩 Hierarchical analysis failed: {str(e)}")
            # Save error state
            if state:
                state['status'] = 'error'
                state['error'] = str(e)
                state['error_time'] = datetime.now().isoformat()
                self._save_analysis_state(analysis_id, state)
            raise
        
        return state.get('results', {})
    
    def _validate_results_structure(self, results: Dict) -> bool:
        """
        Validate that cached results have the required structure.
        
        Args:
            results (Dict): Results to validate
            
        Returns:
            bool: True if structure is valid
        """
        required_keys = ['metrics', 'charts', 'projects', 'people_involvement']
        
        for key in required_keys:
            if key not in results:
                logger.warning(f"⚠️ Missing required key: {key}")
                return False
        
        # Validate people_involvement structure
        people = results.get('people_involvement', {})
        if not isinstance(people.get('overall'), dict):
            logger.warning("⚠️ Invalid people_involvement.overall structure")
            return False
        
        # Validate projects is a list
        if not isinstance(results.get('projects'), list):
            logger.warning("⚠️ Invalid projects structure")
            return False
        
        return True
    
    def _fetch_initiatives(self, jql_query: str) -> List[Dict]:
        """Fetch root initiatives using the provided JQL query."""
        logger.info(f"🔍 Fetching initiatives with query: {jql_query}")
        initiatives = self.jira_client.fetch_issues(jql_query, max_results=self.max_results)
        logger.info(f"📋 Found {len(initiatives)} initiatives")
        return initiatives
    
    def _traverse_hierarchy(self, analysis_id: str, state: Dict) -> List[Dict]:
        """Traverse hierarchy for all initiatives with progress tracking."""
        initiatives = state.get('initiatives', [])
        processed_count = state.get('processed_initiatives', 0)
        all_issues = state.get('all_issues', [])
        
        logger.info(f"🌳 Resuming hierarchy traversal from initiative {processed_count + 1}/{len(initiatives)}")
        
        for i, initiative in enumerate(initiatives[processed_count:], processed_count):
            try:
                logger.info(f"🔍 Processing initiative {i + 1}/{len(initiatives)}: {initiative['key']}")
                
                # Get all child issues for this initiative
                child_issues = self._get_all_child_issues(initiative['key'])
                all_issues.extend(child_issues)
                
                logger.info(f"📊 Initiative {initiative['key']}: {len(child_issues)} child issues")
                
                # Update progress
                state['processed_initiatives'] = i + 1
                state['all_issues'] = all_issues
                self._save_analysis_state(analysis_id, state)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process initiative {initiative['key']}: {str(e)}")
                continue
        
        # Remove duplicates by key
        unique_issues = {issue['key']: issue for issue in all_issues}
        final_issues = list(unique_issues.values())
        
        logger.info(f"✅ Hierarchy traversal complete: {len(final_issues)} unique issues")
        
        # Log sample of issues for debugging
        if final_issues:
            sample_issue = final_issues[0]
            logger.info(f"📋 Sample issue structure: {list(sample_issue.keys())}")
            if 'reporter' in sample_issue:
                logger.info(f"👤 Sample reporter: {sample_issue.get('reporter', 'N/A')}")
            if 'assignee' in sample_issue:
                logger.info(f"👤 Sample assignee: {sample_issue.get('assignee', 'N/A')}")
            if 'comments' in sample_issue:
                logger.info(f"💬 Sample comments count: {len(sample_issue.get('comments', []))}")
        
        return final_issues
    
    def _get_all_child_issues(self, initiative_key: str) -> List[Dict]:
        """Get all child issues for an initiative using childIssuesOf()."""
        issue_type_list = ','.join([f'"{issue_type}"' for issue_type in self.hierarchy_issue_types])
        
        jql_query = (f'issuekey in childIssuesOf("{initiative_key}") '
                    f'AND issuetype IN ({issue_type_list})')
        
        try:
            child_issues = self.jira_client.fetch_issues(jql_query, max_results=self.max_results)
            return child_issues
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch child issues for {initiative_key}: {str(e)}")
            return []
    
    def _generate_analysis_id(self, jql_query: str, months_back: int) -> str:
        """Generate unique analysis ID based on query and parameters."""
        content = f"{jql_query}_{months_back}_{datetime.now().strftime('%Y-%m-%d')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _save_analysis_state(self, analysis_id: str, state: Dict):
        """Save analysis state to disk."""
        state_file = os.path.join(self.cache_dir, f"analysis_{analysis_id}.json")
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"⚠️ Failed to save analysis state: {str(e)}")
    
    def _load_analysis_state(self, analysis_id: str) -> Optional[Dict]:
        """Load analysis state from disk."""
        state_file = os.path.join(self.cache_dir, f"analysis_{analysis_id}.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Failed to load analysis state: {str(e)}")
        return None
    
    def get_analysis_status(self, jql_query: str, months_back: int = 3) -> Dict:
        """Get current status of an analysis."""
        analysis_id = self._generate_analysis_id(jql_query, months_back)
        state = self._load_analysis_state(analysis_id)
        
        if not state:
            return {'status': 'not_started', 'analysis_id': analysis_id}
        
        status_info = {
            'analysis_id': analysis_id,
            'status': state.get('status', 'unknown'),
            'step': state.get('step', 0),
            'start_time': state.get('start_time'),
            'completion_time': state.get('completion_time'),
            'error': state.get('error')
        }
        
        if state.get('status') == 'in_progress':
            status_info.update({
                'total_initiatives': state.get('total_initiatives', 0),
                'processed_initiatives': state.get('processed_initiatives', 0),
                'total_issues': state.get('total_issues', 0),
                'progress_percentage': (state.get('processed_initiatives', 0) / 
                                      max(state.get('total_initiatives', 1), 1)) * 100
            })
        
        return status_info
    
    def cleanup_old_analyses(self, days_old: int = 7):
        """Clean up analysis files older than specified days."""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        cleaned_count = 0
        for filename in os.listdir(self.cache_dir):
            if filename.startswith('analysis_') and filename.endswith('.json'):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to remove old analysis file {filename}: {str(e)}")
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} old analysis files")