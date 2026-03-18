"""
Epic Fix Version Distribution Analyzer
Analyzes epics by fix version across initiatives

Author: Epic Analysis Tool - Pietro Maffi
Purpose: Analyze which epics are assigned to specific fix versions across initiatives
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
import json
from pathlib import Path

from src.common.jira_client import JiraClient

# Configure logging
logger = logging.getLogger('EpicFixVersionAnalyzer')

# Results directory for persistence
RESULTS_DIR = Path(__file__).parent / 'epic_fixversion_results'
RESULTS_DIR.mkdir(exist_ok=True)

class EpicFixVersionAnalyzer:
    """Analyzes epics by fix version across initiatives"""
    
    def __init__(self, jira_client: JiraClient):
        self.jira_client = jira_client
    
    def analyze(self, initiative_jql: str, fix_version: Optional[str] = None, excluded_statuses: Optional[List[str]] = None) -> Dict:
        """
        Analyze epics across initiatives using hierarchy traversal
        
        Args:
            initiative_jql: JQL to find initiatives
            fix_version: Optional fix version to filter epics
            excluded_statuses: Optional list of statuses to exclude
            
        Returns:
            Analysis results with epics grouped by initiative
        """
        if excluded_statuses is None:
            excluded_statuses = ['Done', 'Closed', 'Abandoned', 'Cancelled', 'Resolved']
        
        logger.info(f"🚀 Starting analysis")
        if fix_version:
            logger.info(f"🏷️ Fix version filter: {fix_version}")
        else:
            logger.info(f"🏷️ No fix version filter (all epics)")
        logger.info(f"🚫 Excluded statuses: {', '.join(excluded_statuses)}")
        logger.info(f"📋 Initiative JQL: {initiative_jql}")
        
        try:
            # Step 1: Fetch initiatives
            initiatives = self._fetch_initiatives(initiative_jql)
            if not initiatives:
                logger.warning("⚠️ No initiatives found")
                return {'error': 'No initiatives found with the given JQL query'}
            
            logger.info(f"✅ Found {len(initiatives)} initiatives")
            
            # Step 2: For each initiative, get epics through hierarchy
            results = []
            total_epics = 0
            
            for initiative in initiatives:
                initiative_key = initiative['key']
                initiative_summary = initiative.get('summary', 'No summary')
                
                logger.info(f"🔍 Analyzing initiative: {initiative_key}")
                
                # Get all child epics through hierarchy
                epics = self._get_initiative_epics_via_hierarchy(initiative_key, fix_version, excluded_statuses)
                
                if epics:
                    logger.info(f"  ✅ Found {len(epics)} epics")
                    total_epics += len(epics)
                    
                    results.append({
                        'initiative_key': initiative_key,
                        'initiative_summary': initiative_summary,
                        'epic_count': len(epics),
                        'epics': epics
                    })
                else:
                    logger.info(f"  ℹ️ No epics found")
            
            logger.info(f"✅ Analysis complete: {total_epics} total epics across {len(results)} initiatives")
            
            return {
                'success': True,
                'fix_version': fix_version or 'All',
                'excluded_statuses': excluded_statuses,
                'total_initiatives': len(initiatives),
                'initiatives_with_epics': len(results),
                'total_epics': total_epics,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}", exc_info=True)
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _fetch_initiatives(self, jql_query: str) -> List[Dict]:
        """Fetch initiatives using JQL"""
        try:
            logger.info(f"📥 Fetching initiatives...")
            initiatives = self.jira_client.fetch_issues(jql_query, max_results=1000)
            logger.info(f"📊 Fetched {len(initiatives)} initiatives")
            return initiatives
        except Exception as e:
            logger.error(f"❌ Failed to fetch initiatives: {str(e)}")
            raise
    
    def _get_initiative_epics_via_hierarchy(self, initiative_key: str, fix_version: str = None, excluded_statuses: List[str] = None) -> List[Dict]:
        """Get all epics for an initiative through hierarchy traversal"""
        try:
            # Build status exclusion clause
            status_exclusion = ''
            if excluded_statuses:
                status_list = ' AND '.join([f'status != "{status}"' for status in excluded_statuses])
                status_exclusion = f' AND {status_list}'
            
            # Use childIssuesOf to get all descendants including epics
            # This traverses: Initiative -> Feature -> Sub-Feature -> Epic
            if fix_version:
                jql = (f'issuekey in childIssuesOf("{initiative_key}") '
                       f'AND type = Epic '
                       f'AND fixVersion = "{fix_version}"'
                       f'{status_exclusion}')
            else:
                jql = (f'issuekey in childIssuesOf("{initiative_key}") '
                       f'AND type = Epic'
                       f'{status_exclusion}')
            
            logger.debug(f"  🔍 JQL: {jql}")
            
            # Fetch epics - note: fetch_issues includes fixVersions in fields
            epics = self.jira_client.fetch_issues(jql, max_results=2000)
            
            # Extract relevant epic information including fix version
            epic_list = []
            for epic in epics:
                # Get fix versions from epic
                fix_versions = self._extract_fix_versions(epic)
                fields = epic.get('fields', {})
                
                epic_data = {
                    'key': epic['key'],
                    'summary': epic.get('summary', 'No summary'),
                    'status': epic.get('status', 'Unknown'),
                    'project': self._extract_project_key(epic),
                    'fix_versions': fix_versions,
                    'complexity': self._extract_custom_field(fields, 'customfield_41340'),
                    'requesting_customer': self._extract_custom_field(fields, 'customfield_114641'),
                    'assignee': epic.get('assignee', 'Unassigned'),
                    'target_start': self._extract_custom_field(fields, 'customfield_42640'),
                    'solution': self._extract_custom_field(fields, 'customfield_116072'),
                    'comments': self._extract_comments(fields)
                }
                epic_list.append(epic_data)
                logger.debug(f"    📌 {epic_data['key']}: {epic_data['summary'][:50]}...")
            
            return epic_list
            
        except Exception as e:
            logger.warning(f"  ⚠️ Failed to get epics for {initiative_key}: {str(e)}")
            return []
    
    def _extract_project_key(self, issue: Dict) -> str:
        """Extract project key from issue"""
        if issue.get('project_key'):
            return issue['project_key']
        
        fields = issue.get('fields', {})
        if fields.get('project', {}).get('key'):
            return fields['project']['key']
        
        issue_key = issue.get('key', '')
        if '-' in issue_key:
            return issue_key.split('-')[0]
        
        return 'Unknown'
    
    def _extract_fix_versions(self, issue: Dict) -> List[str]:
        """Extract fix version names from issue"""
        # Try to get from fields first (raw API response)
        fields = issue.get('fields', {})
        fix_versions = fields.get('fixVersions', [])
        
        # If not found, try alternative field names
        if not fix_versions:
            fix_versions = fields.get('fixversions', [])
        
        if not fix_versions:
            return []
        
        # Extract names from version objects
        version_names = []
        for v in fix_versions:
            if isinstance(v, dict):
                name = v.get('name', '')
                if name:
                    version_names.append(name)
            elif isinstance(v, str):
                # In case it's already a string
                version_names.append(v)
        
        return version_names
    
    def _extract_custom_field(self, fields: Dict, field_id: str) -> str:
        """Extract custom field value from issue fields"""
        value = fields.get(field_id)
        if not value:
            return ''
        
        # Handle different field types
        if isinstance(value, dict):
            return value.get('value', value.get('name', str(value)))
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                return ', '.join([v.get('value', v.get('name', str(v))) for v in value])
            return ', '.join([str(v) for v in value])
        return str(value)
    
    def _extract_comments(self, fields: Dict) -> Dict:
        """Extract platform and impacts comments from issue"""
        comments = fields.get('comment', {})
        comment_list = comments.get('comments', [])
        
        result = {'platform': '', 'impacts': ''}
        
        for comment in comment_list:
            body = comment.get('body', '').lower()
            comment_text = comment.get('body', '')
            
            # Look for platform mentions
            if 'platform' in body and not result['platform']:
                result['platform'] = comment_text[:200]
            
            # Look for impact/delay mentions
            if any(word in body for word in ['impact', 'delay', 'risk']) and not result['impacts']:
                result['impacts'] = comment_text[:200]
        
        return result

def save_results_to_file(fix_version: str, results: Dict) -> bool:
    """Save analysis results to JSON file"""
    try:
        # Sanitize fix version for filename
        safe_version = (fix_version or 'All').replace('/', '_').replace('\\', '_').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_version}_{timestamp}.json"
        filepath = RESULTS_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to {filepath}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save results: {str(e)}")
        return False

