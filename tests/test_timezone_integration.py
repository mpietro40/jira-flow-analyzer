"""
Integration tests for timezone handling across the application
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
import pytz
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_analyzer import DataAnalyzer
from jira_client import JiraClient

class TestTimezoneIntegration:
    """Integration tests for timezone handling."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = DataAnalyzer()
    
    def test_end_to_end_timezone_handling(self):
        """Test complete workflow with timezone-aware data."""
        # Simulate Jira data with different timezones
        utc_tz = pytz.UTC
        est_tz = pytz.timezone('US/Eastern')
        pst_tz = pytz.timezone('US/Pacific')
        
        # Create realistic Jira issue data with mixed timezones
        jira_issues = [{
            'key': 'PROJ-123',
            'summary': 'Multi-timezone issue',
            'status': 'Done',
            'issue_type': 'Story',
            'priority': 'High',
            'created': datetime(2023, 1, 1, 9, 0, 0, tzinfo=utc_tz).isoformat(),
            'resolution_date': datetime(2023, 1, 10, 17, 0, 0, tzinfo=est_tz).isoformat(),
            'assignee': 'John Doe',
            'status_history': [
                {
                    'from_status': 'To Do',
                    'to_status': 'In Progress',
                    'changed': datetime(2023, 1, 2, 8, 0, 0, tzinfo=pst_tz).isoformat()
                },
                {
                    'from_status': 'In Progress',
                    'to_status': 'Testing',
                    'changed': datetime(2023, 1, 7, 12, 0, 0, tzinfo=utc_tz).isoformat()
                },
                {
                    'from_status': 'Testing',
                    'to_status': 'Done',
                    'changed': datetime(2023, 1, 10, 17, 0, 0, tzinfo=est_tz).isoformat()
                }
            ]
        }]
        
        # Run analysis
        result = self.analyzer.analyze_issues(jira_issues, 1)
        
        # Verify results
        assert result['total_issues'] == 1
        assert len(result['lead_times']) == 1
        
        # Verify lead time calculation (from In Progress to Done)
        # Should be approximately 8 days regardless of timezone differences
        lead_time = result['lead_times'][0]
        assert 7.5 <= lead_time <= 8.5  # Allow for timezone conversion tolerance
        
        # Verify metrics calculation
        assert 'lead_time' in result['metrics']
        assert result['metrics']['lead_time']['average'] == lead_time
    
    def test_jira_api_timezone_processing(self):
        """Test timezone handling in Jira API data processing."""
        # Mock Jira API response with timezone data
        mock_jira_response = {
            "key": "TEST-456",
            "fields": {
                "summary": "Timezone test",
                "status": {"name": "Done"},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Medium"},
                "created": "2023-06-15T14:30:00.000+0200",  # CEST timezone
                "resolutiondate": "2023-06-20T09:15:00.000-0700",  # PDT timezone
                "assignee": {"displayName": "Jane Smith"}
            },
            "changelog": {
                "histories": [{
                    "created": "2023-06-16T08:00:00.000+0000",  # UTC
                    "items": [{
                        "field": "status",
                        "fromString": "Open",
                        "toString": "In Progress"
                    }]
                }, {
                    "created": "2023-06-20T09:15:00.000-0700",  # PDT
                    "items": [{
                        "field": "status", 
                        "fromString": "In Progress",
                        "toString": "Done"
                    }]
                }]
            }
        }
        
        # Create JiraClient instance
        client = JiraClient("https://test.atlassian.net", "fake_token")
        
        # Process the mock response
        processed_issue = client._process_issue(mock_jira_response)
        
        # Verify processing
        assert processed_issue is not None
        assert processed_issue['key'] == 'TEST-456'
        assert len(processed_issue['status_history']) == 2
        
        # Test with analyzer
        result = self.analyzer.analyze_issues([processed_issue], 1)
        
        # Should handle timezone differences without errors
        assert result['total_issues'] == 1
        # Lead time calculation should work despite timezone complexity
        assert len(result['lead_times']) == 1
    
    def test_daylight_saving_time_transitions(self):
        """Test handling of daylight saving time transitions."""
        # Create issue that spans DST transition in US/Eastern
        est_tz = pytz.timezone('US/Eastern')
        
        # Before DST (EST)
        before_dst = est_tz.localize(datetime(2023, 3, 10, 12, 0, 0))
        # After DST (EDT) 
        after_dst = est_tz.localize(datetime(2023, 3, 15, 12, 0, 0))
        
        dst_issue = {
            'key': 'DST-TEST',
            'summary': 'DST transition test',
            'status': 'Done',
            'issue_type': 'Story',
            'priority': 'Medium',
            'created': before_dst.isoformat(),
            'resolution_date': after_dst.isoformat(),
            'assignee': 'DST Tester',
            'status_history': [{
                'from_status': 'To Do',
                'to_status': 'In Progress',
                'changed': before_dst.isoformat()
            }, {
                'from_status': 'In Progress',
                'to_status': 'Done',
                'changed': after_dst.isoformat()
            }]
        }
        
        result = self.analyzer.analyze_issues([dst_issue], 1)
        
        # Should handle DST transition correctly
        assert result['total_issues'] == 1
        assert len(result['lead_times']) == 1
        
        # Lead time should be approximately 5 days (accounting for DST)
        lead_time = result['lead_times'][0]
        assert 4.9 <= lead_time <= 5.1
    
    def test_international_timezone_handling(self):
        """Test handling of various international timezones."""
        timezones = [
            'UTC',
            'US/Eastern', 
            'US/Pacific',
            'Europe/London',
            'Europe/Berlin',
            'Asia/Tokyo',
            'Australia/Sydney',
            'America/Sao_Paulo'
        ]
        
        issues = []
        base_time = datetime(2023, 6, 1, 12, 0, 0)
        
        for i, tz_name in enumerate(timezones):
            tz = pytz.timezone(tz_name)
            start_time = tz.localize(base_time)
            end_time = tz.localize(base_time + timedelta(days=3))
            
            issue = {
                'key': f'TZ-{i}',
                'summary': f'Issue in {tz_name}',
                'status': 'Done',
                'issue_type': 'Task',
                'priority': 'Low',
                'created': start_time.isoformat(),
                'resolution_date': end_time.isoformat(),
                'assignee': f'User-{tz_name}',
                'status_history': [{
                    'from_status': 'To Do',
                    'to_status': 'In Progress',
                    'changed': start_time.isoformat()
                }, {
                    'from_status': 'In Progress',
                    'to_status': 'Done',
                    'changed': end_time.isoformat()
                }]
            }
            issues.append(issue)
        
        result = self.analyzer.analyze_issues(issues, 1)
        
        # All issues should be processed successfully
        assert result['total_issues'] == len(timezones)
        assert len(result['lead_times']) == len(timezones)
        
        # All lead times should be approximately 3 days
        for lead_time in result['lead_times']:
            assert 2.9 <= lead_time <= 3.1
    
    @patch('data_analyzer.logger')
    def test_timezone_error_logging(self, mock_logger):
        """Test that timezone-related errors are properly logged."""
        # Create issue with corrupted timezone data
        bad_issue = {
            'key': 'BAD-TZ',
            'summary': 'Bad timezone issue',
            'status': 'Done',
            'created': 'not-a-date-at-all',
            'resolution_date': '2023-01-01T12:00:00.000+9999',  # Invalid timezone
            'status_history': [{
                'from_status': 'To Do',
                'to_status': 'Done',
                'changed': 'completely-invalid'
            }]
        }
        
        result = self.analyzer.analyze_issues([bad_issue], 1)
        
        # Should handle gracefully and log warnings
        assert result['total_issues'] == 1  # Issue is included
        assert len(result['lead_times']) == 0  # But no lead time calculated
        
        # Verify warning was logged
        mock_logger.warning.assert_called()
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if 'Failed to parse' in str(call) or 'Failed to calculate' in str(call)]
        assert len(warning_calls) > 0