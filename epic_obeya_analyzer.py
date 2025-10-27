"""
Enhanced Epic Obeya Analyzer
Analyzes epic distribution across projects with hierarchical traversal.
"""

import logging
from datetime import datetime
from typing import List, Dict, Set
from collections import defaultdict
import matplotlib.pyplot as plt
import io
import base64

from jira_client import JiraClient

logger = logging.getLogger('EpicObeyaAnalyzer')

class EpicObeyaAnalyzer:
    """
    Enhanced Epic analyzer with hierarchical traversal and project distribution analysis.
    """
    
    def __init__(self, jira_client: JiraClient):
        """Initialize with Jira client."""
        self.jira_client = jira_client
        self.excluded_statuses = ['Done', 'Closed', 'Abandoned', 'Cancelled', 'Resolved']
    
    def analyze_epic_distribution(self, jql_query: str) -> Dict:
        """
        Analyze epic distribution across projects starting from initiatives.
        
        Args:
            jql_query (str): JQL query to find root initiatives
            
        Returns:
            Dict: Analysis results with epic distribution
        """
        logger.info(f"🔍 Starting epic distribution analysis with query: {jql_query}")
        
        try:
            # Step 1: Get ALL initiatives (not just first 25)
            all_initiatives = self._fetch_initiatives(jql_query, max_results=1000)
            if not all_initiatives:
                return {'error': 'No initiatives found with the given query'}
            
            logger.info(f"📋 Found {len(all_initiatives)} total initiatives")
            
            # Step 2: Split initiatives - first 25 vs rest
            first_25_initiatives = all_initiatives[:25]
            remaining_initiatives = all_initiatives[25:]
            
            logger.info(f"📊 Analyzing first 25 initiatives vs {len(remaining_initiatives)} remaining")
            
            # Step 3: Get all connected projects from ALL initiatives
            connected_projects = self._discover_connected_projects(all_initiatives)
            logger.info(f"🌐 Discovered {len(connected_projects)} connected projects: {sorted(connected_projects)}")
            
            # Step 4: Get epics from first 25 initiatives
            first_25_epics = self._get_epics_from_initiatives(first_25_initiatives)
            logger.info(f"🎯 Found {len(first_25_epics)} epics from first 25 initiatives")
            
            # Step 5: Get epics from remaining initiatives
            remaining_epics = self._get_epics_from_initiatives(remaining_initiatives)
            logger.info(f"📊 Found {len(remaining_epics)} epics from remaining initiatives")
            
            # Debug: Show first few epic keys from each group
            if first_25_epics:
                first_25_keys = [epic['key'] for epic in first_25_epics[:5]]
                logger.info(f"🔍 First 25 sample epics: {first_25_keys}")
            
            if remaining_epics:
                remaining_keys = [epic['key'] for epic in remaining_epics[:5]]
                logger.info(f"🔍 Remaining sample epics: {remaining_keys}")
            
            # Step 6: Create pie chart data (First 25 vs Remaining initiatives)
            chart_data = self._create_pie_chart_data(first_25_epics, remaining_epics)
            logger.info(f"📊 Chart data: {len(first_25_epics)} first 25 epics, {len(remaining_epics)} remaining epics, total: {len(first_25_epics) + len(remaining_epics)}")
            
            # Step 7: Generate pie chart
            pie_chart = self._generate_pie_chart(chart_data)
            
            # Step 8: Analyze epics by project
            project_distribution = self._analyze_epics_by_project(first_25_epics, remaining_epics)
            
            return {
                'success': True,
                'analysis_results': {
                    'total_initiatives': len(all_initiatives),
                    'first_25_initiatives': len(first_25_initiatives),
                    'remaining_initiatives': len(remaining_initiatives),
                    'connected_projects': sorted(connected_projects),
                    'first_25_epics_count': len(first_25_epics),
                    'remaining_epics_count': len(remaining_epics),
                    'total_epics_count': len(first_25_epics) + len(remaining_epics),
                    'chart_data': chart_data,
                    'pie_chart': pie_chart,
                    'project_distribution': project_distribution,
                    'excluded_statuses': self.excluded_statuses
                }
            }
            
        except Exception as e:
            logger.error(f"🚩 Epic distribution analysis failed: {str(e)}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _fetch_initiatives(self, jql_query: str, max_results: int = 25) -> List[Dict]:
        """Fetch initiatives using the provided JQL query."""
        logger.info(f"🔍 Fetching initiatives with query: {jql_query}")
        initiatives = self.jira_client.fetch_issues(jql_query, max_results=max_results)
        logger.info(f"📋 Found {len(initiatives)} initiatives")
        return initiatives
    
    def _discover_connected_projects(self, initiatives: List[Dict]) -> Set[str]:
        """Discover all projects connected to the initiatives through hierarchy."""
        connected_projects = set()
        
        for initiative in initiatives:
            try:
                # Add initiative's project
                initiative_project = self._extract_project_key(initiative)
                if initiative_project:
                    connected_projects.add(initiative_project)
                
                # Get all child epics to discover connected projects
                child_epics = self._get_all_child_epics(initiative['key'])
                
                for epic in child_epics:
                    epic_project = self._extract_project_key(epic)
                    if epic_project:
                        connected_projects.add(epic_project)
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to discover projects for initiative {initiative['key']}: {str(e)}")
                continue
        
        return connected_projects
    
    def _get_all_child_epics(self, initiative_key: str) -> List[Dict]:
        """Get all child epics for an initiative using childIssuesOf()."""
        status_exclusion = ' AND '.join([f'status != "{status}"' for status in self.excluded_statuses])
        jql_query = f'issuekey in childIssuesOf("{initiative_key}") AND type = Epic AND {status_exclusion}'
        
        try:
            child_epics = self.jira_client.fetch_issues(jql_query, max_results=2000)
            return child_epics
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch child epics for {initiative_key}: {str(e)}")
            return []
    
    def _get_epics_from_initiatives(self, initiatives: List[Dict]) -> List[Dict]:
        """Get all epics from initiative hierarchies (already filtered by status in query)."""
        all_epics = []
        
        for initiative in initiatives:
            try:
                # Get all child epics (already filtered by type and status)
                child_epics = self._get_all_child_epics(initiative['key'])
                all_epics.extend(child_epics)
                logger.info(f"📊 Initiative {initiative['key']}: {len(child_epics)} active epics")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to get epics for initiative {initiative['key']}: {str(e)}")
                continue
        
        # Remove duplicates by key
        unique_epics = {epic['key']: epic for epic in all_epics}
        return list(unique_epics.values())
    
    def _extract_project_key(self, issue: Dict) -> str:
        """Extract project key from issue data."""
        # Try direct project_key first
        if issue.get('project_key'):
            return issue['project_key']
        
        # Try fields.project.key
        fields = issue.get('fields', {})
        if fields.get('project', {}).get('key'):
            return fields['project']['key']
        
        # Try parsing from issue key (format: PROJECT-123)
        issue_key = issue.get('key', '')
        if '-' in issue_key:
            return issue_key.split('-')[0]
        
        return ''
    
    def _analyze_epics_by_project(self, first_25_epics: List[Dict], remaining_epics: List[Dict]) -> Dict:
        """Analyze epic distribution by Jira project."""
        from collections import defaultdict
        
        first_25_by_project = defaultdict(int)
        remaining_by_project = defaultdict(int)
        
        # Count first 25 epics by project
        for epic in first_25_epics:
            project_key = self._extract_project_key(epic)
            if project_key:
                first_25_by_project[project_key] += 1
        
        # Count remaining epics by project
        for epic in remaining_epics:
            project_key = self._extract_project_key(epic)
            if project_key:
                remaining_by_project[project_key] += 1
        
        # Combine all projects
        all_projects = set(first_25_by_project.keys()) | set(remaining_by_project.keys())
        
        project_summary = []
        for project in sorted(all_projects):
            first_25_count = first_25_by_project[project]
            remaining_count = remaining_by_project[project]
            total_count = first_25_count + remaining_count
            
            project_summary.append({
                'project': project,
                'first_25_epics': first_25_count,
                'remaining_epics': remaining_count,
                'total_epics': total_count
            })
        
        return {
            'by_project': project_summary,
            'total_projects': len(all_projects)
        }
    
    def _create_pie_chart_data(self, first_25_epics: List[Dict], remaining_epics: List[Dict]) -> Dict:
        """Create data for pie chart showing first 25 initiatives epics vs remaining initiatives epics."""
        first_25_count = len(first_25_epics)
        remaining_count = len(remaining_epics)
        total_count = first_25_count + remaining_count
        
        if total_count == 0:
            return {
                'first_25_epics_count': 0,
                'remaining_epics_count': 0,
                'total_epics_count': 0,
                'first_25_percentage': 0,
                'remaining_percentage': 0,
                'labels': ['First 25 Initiatives', 'Remaining Initiatives'],
                'values': [0, 0],
                'percentages': [0, 0]
            }
        
        # Calculate percentages
        first_25_percentage = (first_25_count / total_count) * 100
        remaining_percentage = (remaining_count / total_count) * 100
        
        logger.info(f"📊 Pie chart calculation: {first_25_count} + {remaining_count} = {total_count} total epics")
        logger.info(f"📊 Percentages: First 25: {first_25_percentage:.1f}%, Remaining: {remaining_percentage:.1f}%")
        
        return {
            'first_25_epics_count': first_25_count,
            'remaining_epics_count': remaining_count,
            'total_epics_count': total_count,
            'first_25_percentage': first_25_percentage,
            'remaining_percentage': remaining_percentage,
            'labels': ['First 25 Initiatives', 'Remaining Initiatives'],
            'values': [first_25_count, remaining_count],
            'percentages': [first_25_percentage, remaining_percentage]
        }
    
    def _generate_pie_chart(self, chart_data: Dict) -> str:
        """Generate pie chart showing epic distribution."""
        try:
            plt.figure(figsize=(10, 8))
            
            labels = chart_data['labels']
            values = chart_data['values']
            percentages = chart_data['percentages']
            
            # Create pie chart with custom colors
            colors = ['#FF6B6B', '#4ECDC4']  # Red for first 25, Teal for remaining
            
            wedges, texts, autotexts = plt.pie(
                values, 
                labels=labels, 
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                explode=(0.05, 0)  # Slightly separate first 25 slice
            )
            
            # Enhance text formatting
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_weight('bold')
            
            for text in texts:
                text.set_fontsize(12)
                text.set_weight('bold')
            
            plt.title(
                f'Epic Distribution: First 25 vs Remaining Initiatives\n'
                f'Total Active Epics: {chart_data["total_epics_count"]}',
                fontsize=16,
                fontweight='bold',
                pad=20
            )
            
            # Add legend with counts
            legend_labels = [
                f'First 25 Initiatives ({chart_data["first_25_epics_count"]})',
                f'Remaining Initiatives ({chart_data["remaining_epics_count"]})'
            ]
            plt.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            plt.axis('equal')
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            return chart_b64
            
        except Exception as e:
            logger.error(f"🚩 Failed to generate pie chart: {str(e)}")
            return ""
    
    def analyze_epic_status_validation(self, jql_query: str) -> Dict:
        """
        Analyze epics to find those with outdated status (To Do/Backlog but have in-progress children).
        
        Args:
            jql_query (str): JQL query to find epics
            
        Returns:
            Dict: Analysis results with outdated epics
        """
        logger.info(f"🔍 Starting epic status validation with query: {jql_query}")
        
        try:
            # Get all epics from query
            epics = self.jira_client.fetch_issues(jql_query, max_results=1000)
            logger.info(f"📋 Found {len(epics)} epics to validate")
            
            # Filter epics in To Do or Backlog status
            todo_backlog_epics = [
                epic for epic in epics
                if epic.get('status', '').lower() in ['To Do', 'Global Backlog', 'todo']
            ]
            
            logger.info(f"📊 Found {len(todo_backlog_epics)} epics in To Do/ Global Backlog status")
            
            outdated_epics = []
            
            for epic in todo_backlog_epics:
                try:
                    # Get child issues for this epic
                    child_issues = self._get_epic_children(epic['key'])
                    
                    # Check if any child is in progress
                    in_progress_children = [
                        child for child in child_issues
                        if child.get('status', '').lower() in ['Work In Progress', 'in progress', 'in-progress', 'doing', 'development']
                    ]
                    
                    if in_progress_children:
                        outdated_epics.append({
                            'key': epic['key'],
                            'summary': epic.get('summary', ''),
                            'status': epic.get('status', ''),
                            'project': self._extract_project_key(epic),
                            'in_progress_children_count': len(in_progress_children),
                            'total_children_count': len(child_issues),
                            'in_progress_children': [{
                                'key': child['key'],
                                'summary': child.get('summary', ''),
                                'status': child.get('status', '')
                            } for child in in_progress_children[:5]]  # Limit to first 5
                        })
                        
                        logger.info(f"⚠️ Epic {epic['key']} has {len(in_progress_children)} in-progress children")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to validate epic {epic['key']}: {str(e)}")
                    continue
            
            logger.info(f"🎯 Found {len(outdated_epics)} epics with outdated status")
            
            return {
                'success': True,
                'analysis_results': {
                    'total_epics_checked': len(todo_backlog_epics),
                    'outdated_epics_count': len(outdated_epics),
                    'outdated_epics': outdated_epics
                }
            }
            
        except Exception as e:
            logger.error(f"🚩 Epic status validation failed: {str(e)}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _get_epic_children(self, epic_key: str) -> List[Dict]:
        """Get all child issues for an epic."""
        jql_query = f'issuekey in childIssuesOf("{epic_key}")'
        
        try:
            child_issues = self.jira_client.fetch_issues(jql_query, max_results=1000)
            return child_issues
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch children for epic {epic_key}: {str(e)}")
            return []