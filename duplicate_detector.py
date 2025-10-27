"""
Duplicate Story Detector
Analyzes Jira issues to identify potential duplicates based on summary and description similarity.

Author: Pietro Maffi
Purpose: Detect duplicate stories to improve backlog quality
"""

import logging
from datetime import datetime
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
import re
from collections import defaultdict

from jira_client import JiraClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DuplicateDetector')

class DuplicateDetector:
    """
    Detects potential duplicate stories in Jira based on text similarity.
    """
    
    def __init__(self, jira_client: JiraClient):
        """
        Initialize duplicate detector with Jira client.
        
        Args:
            jira_client (JiraClient): Configured Jira client instance
        """
        self.jira_client = jira_client
        self.similarity_threshold = 0.6  # Minimum similarity to consider as potential duplicate
        
    def analyze_duplicates(self, jql_query: str) -> Dict:
        """
        Analyze issues for potential duplicates.
        
        Args:
            jql_query (str): JQL query to fetch issues
            
        Returns:
            Dict: Analysis results with duplicate groups
        """
        logger.info(f"🔍 Starting duplicate analysis with JQL: {jql_query}")
        
        # Fetch issues
        issues = self.jira_client.fetch_issues(jql_query, max_results=1000)
        
        if not issues:
            return {'error': 'No issues found for the given query'}
        
        logger.info(f"📊 Analyzing {len(issues)} issues for duplicates")
        
        # Find duplicate groups
        duplicate_groups = self._find_duplicate_groups(issues)
        
        # Create analysis report
        report = self._create_analysis_report(issues, duplicate_groups, jql_query)
        
        logger.info(f"✅ Found {len(duplicate_groups)} potential duplicate groups")
        return report
    
    def _find_duplicate_groups(self, issues: List[Dict]) -> List[Dict]:
        """
        Find groups of potentially duplicate issues.
        
        Args:
            issues (List[Dict]): List of issues to analyze
            
        Returns:
            List[Dict]: List of duplicate groups
        """
        duplicate_groups = []
        processed_issues = set()
        
        for i, issue1 in enumerate(issues):
            if issue1['key'] in processed_issues:
                continue
                
            # Find similar issues
            similar_issues = []
            
            for j, issue2 in enumerate(issues):
                if i != j and issue2['key'] not in processed_issues:
                    similarity = self._calculate_similarity(issue1, issue2)
                    
                    if similarity >= self.similarity_threshold:
                        similar_issues.append({
                            'issue': issue2,
                            'similarity': similarity
                        })
            
            # If we found similar issues, create a group
            if similar_issues:
                # Sort by creation date (oldest first)
                all_issues = [issue1] + [item['issue'] for item in similar_issues]
                all_issues.sort(key=lambda x: x.get('created', ''))
                
                # Mark all issues as processed
                for issue in all_issues:
                    processed_issues.add(issue['key'])
                
                # Create group with oldest as primary
                primary_issue = all_issues[0]
                duplicates = []
                
                for issue in all_issues[1:]:
                    # Recalculate similarity with primary issue
                    similarity = self._calculate_similarity(primary_issue, issue)
                    duplicates.append({
                        'issue': issue,
                        'similarity': similarity
                    })
                
                # Sort duplicates by similarity (highest first)
                duplicates.sort(key=lambda x: x['similarity'], reverse=True)
                
                duplicate_groups.append({
                    'primary_issue': primary_issue,
                    'duplicates': duplicates,
                    'group_size': len(all_issues)
                })
        
        # Sort groups by group size (largest first)
        duplicate_groups.sort(key=lambda x: x['group_size'], reverse=True)
        
        return duplicate_groups
    
    def _calculate_similarity(self, issue1: Dict, issue2: Dict) -> float:
        """
        Calculate similarity between two issues based on summary and description.
        
        Args:
            issue1 (Dict): First issue
            issue2 (Dict): Second issue
            
        Returns:
            float: Similarity score between 0 and 1
        """
        # Get text content
        text1 = self._extract_text_content(issue1)
        text2 = self._extract_text_content(issue2)
        
        # Calculate similarity using SequenceMatcher
        similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
        return similarity
    
    def _extract_text_content(self, issue: Dict) -> str:
        """
        Extract text content from issue for comparison.
        
        Args:
            issue (Dict): Issue data
            
        Returns:
            str: Combined text content
        """
        # Get summary
        summary = issue.get('summary', '')
        
        # Get description from fields
        description = ''
        fields = issue.get('fields', {})
        if fields and 'description' in fields and fields['description']:
            description = fields['description']
        
        # Combine and clean text
        combined_text = f"{summary} {description}"
        
        # Remove common Jira markup and normalize
        combined_text = re.sub(r'\{[^}]*\}', '', combined_text)  # Remove {code}, {quote}, etc.
        combined_text = re.sub(r'\[[^\]]*\]', '', combined_text)  # Remove [links]
        combined_text = re.sub(r'\s+', ' ', combined_text)  # Normalize whitespace
        
        return combined_text.strip()
    
    def _create_analysis_report(self, issues: List[Dict], duplicate_groups: List[Dict], jql_query: str) -> Dict:
        """
        Create comprehensive analysis report.
        
        Args:
            issues (List[Dict]): All analyzed issues
            duplicate_groups (List[Dict]): Found duplicate groups
            jql_query (str): Original JQL query
            
        Returns:
            Dict: Complete analysis report
        """
        # Calculate statistics
        total_issues = len(issues)
        issues_in_groups = sum(group['group_size'] for group in duplicate_groups)
        potential_duplicates = issues_in_groups - len(duplicate_groups)  # Exclude primary issues
        
        # Group statistics
        group_stats = {
            'total_groups': len(duplicate_groups),
            'largest_group_size': max([group['group_size'] for group in duplicate_groups]) if duplicate_groups else 0,
            'average_group_size': sum([group['group_size'] for group in duplicate_groups]) / len(duplicate_groups) if duplicate_groups else 0
        }
        
        # Similarity statistics
        all_similarities = []
        for group in duplicate_groups:
            for duplicate in group['duplicates']:
                all_similarities.append(duplicate['similarity'])
        
        similarity_stats = {}
        if all_similarities:
            similarity_stats = {
                'average_similarity': sum(all_similarities) / len(all_similarities),
                'max_similarity': max(all_similarities),
                'min_similarity': min(all_similarities)
            }
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'jql_query': jql_query,
            'total_issues_analyzed': total_issues,
            'duplicate_groups': duplicate_groups,
            'statistics': {
                'total_groups': group_stats['total_groups'],
                'issues_in_groups': issues_in_groups,
                'potential_duplicates': potential_duplicates,
                'duplicate_percentage': (potential_duplicates / total_issues * 100) if total_issues > 0 else 0,
                'largest_group_size': group_stats['largest_group_size'],
                'average_group_size': group_stats['average_group_size'],
                'similarity_stats': similarity_stats
            },
            'settings': {
                'similarity_threshold': self.similarity_threshold
            }
        }