"""
Acceptance Tests for AC003: Lead Time Calculation
"""
import pytest
from datetime import datetime, timedelta
from data_analyzer import DataAnalyzer
import pandas as pd


class TestAC003_LeadTimeCalculation:
    """Test suite for lead time calculation acceptance criteria"""
    
    def test_ac003_1_basic_lead_time(self):
        """
        AC003.1: Basic Lead Time
        Given issue with "In Progress" and "Done" transitions
        When lead time is calculated
        Then time difference in days is returned
        """
        analyzer = DataAnalyzer()
        
        start_date = datetime(2024, 1, 1, 10, 0, 0)
        end_date = datetime(2024, 1, 11, 10, 0, 0)
        
        issues = [{
            'key': 'TEST-1',
            'summary': 'Test Issue',
            'status': 'Done',
            'created': start_date.isoformat(),
            'resolution_date': end_date.isoformat(),
            'status_history': [
                {
                    'from_status': 'To Do',
                    'to_status': 'In Progress',
                    'changed': start_date.isoformat()
                },
                {
                    'from_status': 'In Progress',
                    'to_status': 'Done',
                    'changed': end_date.isoformat()
                }
            ]
        }]
        
        result = analyzer.analyze_issues(issues, months_back=12)
        lead_times = result['lead_times']
        
        assert len(lead_times) == 1
        assert lead_times[0] == 10.0
    
    def test_ac003_2_multiple_status_transitions(self):
        """
        AC003.2: Multiple Status Transitions
        Given issue with multiple status changes
        When lead time is calculated
        Then first "In Progress" date is used and last "Done" date is used
        """
        analyzer = DataAnalyzer()
        
        start_date = datetime(2024, 1, 1)
        middle_date = datetime(2024, 1, 5)
        end_date = datetime(2024, 1, 15)
        
        issues = [{
            'key': 'TEST-2',
            'summary': 'Test Issue',
            'status': 'Done',
            'created': start_date.isoformat(),
            'resolution_date': end_date.isoformat(),
            'status_history': [
                {'from_status': 'To Do', 'to_status': 'In Progress', 'changed': start_date.isoformat()},
                {'from_status': 'In Progress', 'to_status': 'Testing', 'changed': middle_date.isoformat()},
                {'from_status': 'Testing', 'to_status': 'In Progress', 'changed': datetime(2024, 1, 8).isoformat()},
                {'from_status': 'In Progress', 'to_status': 'Done', 'changed': end_date.isoformat()}
            ]
        }]
        
        result = analyzer.analyze_issues(issues, months_back=12)
        lead_times = result['lead_times']
        
        assert len(lead_times) == 1
        assert lead_times[0] == 14.0
    
    def test_ac003_3_incomplete_issues(self):
        """
        AC003.3: Incomplete Issues
        Given issue still in progress (not done)
        When lead time is calculated
        Then issue is excluded from lead time metrics
        """
        analyzer = DataAnalyzer()
        
        issues = [{
            'key': 'TEST-3',
            'summary': 'In Progress Issue',
            'status': 'In Progress',
            'created': datetime(2024, 1, 1).isoformat(),
            'resolution_date': None,
            'status_history': [
                {'from_status': 'To Do', 'to_status': 'In Progress', 'changed': datetime(2024, 1, 1).isoformat()}
            ]
        }]
        
        result = analyzer.analyze_issues(issues, months_back=12)
        lead_times = result['lead_times']
        
        assert len(lead_times) == 0
    
    def test_ac003_4_status_mapping(self):
        """
        AC003.4: Status Mapping
        Given custom status names
        When lead time is calculated
        Then statuses are mapped to standard categories
        """
        analyzer = DataAnalyzer()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 8)
        
        issues = [{
            'key': 'TEST-4',
            'summary': 'Custom Status Issue',
            'status': 'Completed',
            'created': start_date.isoformat(),
            'resolution_date': end_date.isoformat(),
            'status_history': [
                {'from_status': 'Backlog', 'to_status': 'Development', 'changed': start_date.isoformat()},
                {'from_status': 'Development', 'to_status': 'Completed', 'changed': end_date.isoformat()}
            ]
        }]
        
        result = analyzer.analyze_issues(issues, months_back=12)
        lead_times = result['lead_times']
        
        assert len(lead_times) == 1
        assert lead_times[0] == 7.0
    
    def test_ac003_6_statistical_metrics(self):
        """
        AC003.6: Statistical Metrics
        Given multiple issues with lead times
        When metrics are calculated
        Then average, median, P85, P95 are provided
        """
        analyzer = DataAnalyzer()
        
        base_date = datetime(2024, 1, 1)
        issues = []
        
        for i, days in enumerate([5, 10, 15, 20, 25]):
            end_date = base_date + timedelta(days=days)
            issues.append({
                'key': f'TEST-{i}',
                'summary': f'Issue {i}',
                'status': 'Done',
                'created': base_date.isoformat(),
                'resolution_date': end_date.isoformat(),
                'status_history': [
                    {'from_status': 'To Do', 'to_status': 'In Progress', 'changed': base_date.isoformat()},
                    {'from_status': 'In Progress', 'to_status': 'Done', 'changed': end_date.isoformat()}
                ]
            })
        
        result = analyzer.analyze_issues(issues, months_back=12)
        metrics = result['metrics']
        
        assert 'lead_time' in metrics
        assert 'average' in metrics['lead_time']
        assert 'median' in metrics['lead_time']
        assert 'p85' in metrics['lead_time']
        assert 'p95' in metrics['lead_time']
        assert metrics['lead_time']['median'] == 15.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
