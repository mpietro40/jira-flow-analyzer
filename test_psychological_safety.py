"""
Unit tests for Psychological Safety Analyzer
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile
from datetime import datetime, timedelta

from psychological_safety_analyzer import PsychologicalSafetyAnalyzer


class TestPsychologicalSafetyAnalyzer(unittest.TestCase):
    """Test cases for PsychologicalSafetyAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_jira_client = Mock()
        self.analyzer = PsychologicalSafetyAnalyzer(self.mock_jira_client)
        
        # Use temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer.data_dir = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_question_patterns(self):
        """Test question pattern matching."""
        test_cases = [
            ("How does this work?", True),
            ("Why did we choose this approach?", True),
            ("What if we try a different solution?", True),
            ("This is a statement.", False),
            ("Could we consider alternatives?", True),
            ("Would this be better?", True)
        ]
        
        import re
        for text, should_match in test_cases:
            has_question = any(re.search(pattern, text, re.IGNORECASE) 
                             for pattern in self.analyzer.question_patterns)
            self.assertEqual(has_question, should_match, f"Failed for: {text}")
    
    def test_disagreement_patterns(self):
        """Test disagreement pattern matching."""
        test_cases = [
            ("However, I think we should reconsider.", True),
            ("But what about the performance impact?", True),
            ("Alternatively, we could use a different approach.", True),
            ("I agree with this solution.", False),
            ("Actually, I disagree with this.", True),
            ("On the other hand, this might work.", True)
        ]
        
        import re
        for text, should_match in test_cases:
            has_disagreement = any(re.search(pattern, text, re.IGNORECASE) 
                                 for pattern in self.analyzer.disagreement_patterns)
            self.assertEqual(has_disagreement, should_match, f"Failed for: {text}")
    
    def test_help_seeking_patterns(self):
        """Test help-seeking pattern matching."""
        test_cases = [
            ("I need help with this issue.", True),
            ("Can someone provide guidance?", True),
            ("Any ideas on how to solve this?", True),
            ("This is working fine.", False),
            ("Looking for advice on implementation.", True),
            ("Need support with testing.", True)
        ]
        
        import re
        for text, should_match in test_cases:
            has_help_seeking = any(re.search(pattern, text, re.IGNORECASE) 
                                 for pattern in self.analyzer.help_seeking_patterns)
            self.assertEqual(has_help_seeking, should_match, f"Failed for: {text}")
    
    def test_get_hierarchy_issues(self):
        """Test hierarchy issue retrieval."""
        # Mock root issues
        root_issues = [
            {'key': 'PROJ-1', 'summary': 'Root Issue 1'},
            {'key': 'PROJ-2', 'summary': 'Root Issue 2'}
        ]
        
        # Mock child issues
        child_issues_1 = [
            {'key': 'PROJ-3', 'summary': 'Child Issue 1'},
            {'key': 'PROJ-4', 'summary': 'Child Issue 2'}
        ]
        child_issues_2 = [
            {'key': 'PROJ-5', 'summary': 'Child Issue 3'}
        ]
        
        self.mock_jira_client.fetch_issues.return_value = root_issues
        self.analyzer._get_all_child_issues = Mock(side_effect=[child_issues_1, child_issues_2])
        
        result = self.analyzer._get_hierarchy_issues("project = PROJ")
        
        # Should return all unique issues
        expected_keys = {'PROJ-1', 'PROJ-2', 'PROJ-3', 'PROJ-4', 'PROJ-5'}
        result_keys = {issue['key'] for issue in result}
        self.assertEqual(result_keys, expected_keys)
    
    def test_analyze_safety_indicators(self):
        """Test safety indicators analysis."""
        # Mock issues
        issues = [
            {
                'key': 'PROJ-1',
                'creator': 'user1',
                'labels': ['help-needed']
            },
            {
                'key': 'PROJ-2', 
                'creator': 'user2',
                'labels': []
            }
        ]
        
        # Mock comments
        week_start = datetime(2024, 1, 1)
        week_end = datetime(2024, 1, 7)
        
        comments_1 = [
            {
                'author': {'displayName': 'user1'},
                'body': 'How should we implement this?',
                'created': '2024-01-02T10:00:00.000Z'
            }
        ]
        comments_2 = [
            {
                'author': {'displayName': 'user2'},
                'body': 'However, I think we should consider alternatives.',
                'created': '2024-01-03T10:00:00.000Z'
            }
        ]
        
        self.analyzer._get_issue_comments = Mock(side_effect=[comments_1, comments_2])
        
        result = self.analyzer._analyze_safety_indicators(issues, "2024-01")
        
        # Verify metrics
        self.assertEqual(result['metrics']['help_seeking_issues'], 1)
        self.assertEqual(result['metrics']['idea_contributors'], 2)
        self.assertEqual(result['raw_data']['total_comments'], 2)
        self.assertEqual(result['raw_data']['question_comments'], 1)
        self.assertEqual(result['raw_data']['disagreement_comments'], 1)
    
    def test_save_and_load_weekly_data(self):
        """Test saving and loading weekly data."""
        test_data = {
            'week': '2024-01',
            'metrics': {
                'comment_participation_rate': 75.0,
                'question_frequency': 25.0
            }
        }
        
        # Save data
        self.analyzer._save_weekly_data('2024-01', test_data)
        
        # Load data
        loaded_data = self.analyzer._load_weekly_data('2024-01')
        
        self.assertEqual(loaded_data['week'], '2024-01')
        self.assertEqual(loaded_data['metrics']['comment_participation_rate'], 75.0)
    
    def test_get_historical_data(self):
        """Test historical data retrieval."""
        # Create test data files
        for i in range(3):
            week = f"2024-{i+1:02d}"
            data = {
                'week': week,
                'metrics': {
                    'comment_participation_rate': 50.0 + i * 10,
                    'question_frequency': 20.0 + i * 5
                }
            }
            self.analyzer._save_weekly_data(week, data)
        
        # Get historical data
        historical = self.analyzer.get_historical_data(weeks_back=5)
        
        # Should return data sorted by week
        self.assertEqual(len(historical), 3)
        self.assertEqual(historical[0]['week'], '2024-01')
        self.assertEqual(historical[-1]['week'], '2024-03')
    
    def test_get_safety_trends(self):
        """Test safety trends calculation."""
        # Create test data with trend
        test_data = []
        for i in range(6):
            week = f"2024-{i+1:02d}"
            data = {
                'week': week,
                'metrics': {
                    'comment_participation_rate': 40.0 + i * 5,  # Increasing trend
                    'question_frequency': 30.0 - i * 2,         # Decreasing trend
                    'disagreement_indicators': 15.0,            # Stable
                    'help_seeking_issues': i + 1                # Increasing
                }
            }
            test_data.append(data)
            self.analyzer._save_weekly_data(week, data)
        
        # Mock get_historical_data to return our test data
        self.analyzer.get_historical_data = Mock(return_value=test_data)
        
        trends = self.analyzer.get_safety_trends(weeks_back=6)
        
        # Verify trend calculations
        self.assertGreater(trends['trends']['participation_trend'], 0)  # Should be positive
        self.assertLess(trends['trends']['question_trend'], 0)          # Should be negative
        self.assertEqual(trends['trends']['disagreement_trend'], 0)     # Should be zero
        self.assertGreater(trends['trends']['help_seeking_trend'], 0)   # Should be positive
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_analyze_weekly_safety_new_week(self, mock_sleep):
        """Test weekly safety analysis for new week."""
        # Mock no existing data
        self.analyzer._load_weekly_data = Mock(return_value=None)
        
        # Mock hierarchy issues
        issues = [
            {'key': 'PROJ-1', 'creator': 'user1', 'labels': []},
            {'key': 'PROJ-2', 'creator': 'user2', 'labels': ['help-needed']}
        ]
        self.analyzer._get_hierarchy_issues = Mock(return_value=issues)
        
        # Mock comments
        self.analyzer._get_issue_comments = Mock(return_value=[
            {
                'author': {'displayName': 'user1'},
                'body': 'How does this work?',
                'created': '2024-01-02T10:00:00.000Z'
            }
        ])
        
        # Mock save method
        self.analyzer._save_weekly_data = Mock()
        
        result = self.analyzer.analyze_weekly_safety("project = PROJ", "2024-01")
        
        # Verify analysis was performed
        self.assertIn('metrics', result)
        self.assertIn('raw_data', result)
        self.analyzer._save_weekly_data.assert_called_once()
    
    def test_analyze_weekly_safety_existing_data(self):
        """Test weekly safety analysis with existing data."""
        existing_data = {
            'week': '2024-01',
            'metrics': {'comment_participation_rate': 80.0}
        }
        
        # Mock existing data
        self.analyzer._load_weekly_data = Mock(return_value=existing_data)
        
        result = self.analyzer.analyze_weekly_safety("project = PROJ", "2024-01")
        
        # Should return existing data without analysis
        self.assertEqual(result, existing_data)
        self.analyzer._load_weekly_data.assert_called_once_with("2024-01")


class TestPsychologicalSafetyIntegration(unittest.TestCase):
    """Integration tests for psychological safety analysis."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.mock_jira_client = Mock()
        
        # Create realistic mock data
        self.mock_issues = [
            {
                'key': 'PROJ-1',
                'summary': 'Implement new feature',
                'creator': 'alice',
                'labels': []
            },
            {
                'key': 'PROJ-2', 
                'summary': 'Fix critical bug',
                'creator': 'bob',
                'labels': ['help-needed']
            }
        ]
        
        self.mock_comments = {
            'PROJ-1': [
                {
                    'author': {'displayName': 'alice'},
                    'body': 'How should we approach this implementation?',
                    'created': '2024-01-02T10:00:00.000Z'
                },
                {
                    'author': {'displayName': 'bob'},
                    'body': 'However, I think we should consider performance implications.',
                    'created': '2024-01-02T14:00:00.000Z'
                }
            ],
            'PROJ-2': [
                {
                    'author': {'displayName': 'charlie'},
                    'body': 'I need help understanding this error.',
                    'created': '2024-01-03T09:00:00.000Z'
                }
            ]
        }
    
    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        # Setup mocks
        self.mock_jira_client.fetch_issues.return_value = self.mock_issues
        
        def mock_get_child_issues(issue_key):
            return []  # No child issues for simplicity
        
        def mock_get_comments(issue_key, week_start, week_end):
            comments = self.mock_comments.get(issue_key, [])
            # Filter by date range (simplified)
            return [
                {
                    'author': comment['author']['displayName'],
                    'body': comment['body'],
                    'created': comment['created']
                }
                for comment in comments
            ]
        
        analyzer = PsychologicalSafetyAnalyzer(self.mock_jira_client)
        analyzer._get_all_child_issues = mock_get_child_issues
        analyzer._get_issue_comments = mock_get_comments
        
        # Use temporary directory
        temp_dir = tempfile.mkdtemp()
        analyzer.data_dir = temp_dir
        
        try:
            result = analyzer.analyze_weekly_safety("project = PROJ", "2024-01")
            
            # Verify results
            self.assertIn('metrics', result)
            self.assertIn('raw_data', result)
            
            metrics = result['metrics']
            raw_data = result['raw_data']
            
            # Check basic counts
            self.assertEqual(raw_data['total_issues'], 2)
            self.assertEqual(raw_data['total_comments'], 3)
            self.assertEqual(metrics['help_seeking_issues'], 1)
            self.assertEqual(metrics['idea_contributors'], 2)
            
            # Check pattern detection
            self.assertGreater(metrics['question_frequency'], 0)
            self.assertGreater(metrics['disagreement_indicators'], 0)
            
            # Verify data was saved
            saved_data = analyzer._load_weekly_data("2024-01")
            self.assertIsNotNone(saved_data)
            self.assertEqual(saved_data['week'], "2024-01")
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()