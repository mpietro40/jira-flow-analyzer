"""
Acceptance Tests for AC006: CSV Import Functionality
"""
import pytest
from io import BytesIO
from jira_client import JiraClient
from unittest.mock import patch, Mock


class TestAC006_CSVImport:
    """Test suite for CSV import acceptance criteria"""
    
    def test_ac006_1_csv_parsing(self):
        """
        AC006.1: CSV Parsing
        Given CSV file with issue keys
        When file is uploaded
        Then issue keys are extracted
        """
        csv_content = b"Issue Key,Summary\nTEST-123,Test Issue\nTEST-456,Another Issue"
        csv_file = BytesIO(csv_content)
        csv_file.filename = 'test.csv'
        
        client = JiraClient('https://test.atlassian.net', 'token')
        keys = client.parse_csv_for_issue_keys(csv_file)
        
        assert len(keys) == 2
        assert 'TEST-123' in keys
        assert 'TEST-456' in keys
    
    def test_ac006_2_column_detection(self):
        """
        AC006.2: Column Detection
        Given CSV with various column names
        When file is parsed
        Then key columns are auto-detected
        """
        csv_content = b"Ticket,Description,Status\nPROJ-100,Description 1,Open\nPROJ-200,Description 2,Done"
        csv_file = BytesIO(csv_content)
        
        client = JiraClient('https://test.atlassian.net', 'token')
        keys = client.parse_csv_for_issue_keys(csv_file)
        
        assert len(keys) == 2
        assert 'PROJ-100' in keys
        assert 'PROJ-200' in keys
    
    def test_ac006_3_key_validation(self):
        """
        AC006.3: Key Validation
        Given CSV with mixed content
        When keys are extracted
        Then only valid Jira keys are accepted
        """
        csv_content = b"Key,Value\nTEST-123,Valid\nInvalid,Not a key\n123-TEST,Wrong format\nABC-456,Valid"
        csv_file = BytesIO(csv_content)
        
        client = JiraClient('https://test.atlassian.net', 'token')
        keys = client.parse_csv_for_issue_keys(csv_file)
        
        assert len(keys) == 2
        assert 'TEST-123' in keys
        assert 'ABC-456' in keys
        assert 'Invalid' not in keys
        assert '123-TEST' not in keys
    
    def test_ac006_4_duplicate_handling(self):
        """
        AC006.4: Duplicate Handling
        Given CSV with duplicate keys
        When keys are extracted
        Then duplicates are removed
        """
        csv_content = b"Issue Key\nTEST-123\nTEST-456\nTEST-123\nTEST-789\nTEST-456"
        csv_file = BytesIO(csv_content)
        
        client = JiraClient('https://test.atlassian.net', 'token')
        keys = client.parse_csv_for_issue_keys(csv_file)
        
        assert len(keys) == 3
        assert keys.count('TEST-123') == 1
        assert keys.count('TEST-456') == 1
    
    def test_ac006_5_subtask_inclusion(self):
        """
        AC006.5: Subtask Inclusion
        Given CSV with parent issue keys
        When "include subtasks" is enabled
        Then parent issues and subtasks are fetched
        """
        with patch('requests.Session.get') as mock_get:
            # Mock parent issue response
            parent_response = Mock()
            parent_response.status_code = 200
            parent_response.json.return_value = {
                'issues': [
                    {'key': 'TEST-123', 'fields': {'summary': 'Parent', 'status': {'name': 'Done'}}}
                ],
                'total': 1
            }
            
            # Mock subtask response
            subtask_response = Mock()
            subtask_response.status_code = 200
            subtask_response.json.return_value = {
                'issues': [
                    {'key': 'TEST-124', 'fields': {'summary': 'Subtask', 'status': {'name': 'Done'}}}
                ],
                'total': 1
            }
            
            mock_get.side_effect = [parent_response, subtask_response]
            
            client = JiraClient('https://test.atlassian.net', 'token')
            issues = client.fetch_issues_by_keys(['TEST-123'], include_subtasks=True)
            
            assert len(issues) >= 1
    
    def test_ac006_6_batch_processing(self):
        """
        AC006.6: Batch Processing
        Given CSV with many issue keys
        When issues are fetched
        Then keys are processed in batches
        """
        # Create 100 issue keys
        keys = [f'TEST-{i}' for i in range(1, 101)]
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'issues': [], 'total': 0}
            mock_get.return_value = mock_response
            
            client = JiraClient('https://test.atlassian.net', 'token')
            client.fetch_issues_by_keys(keys, include_subtasks=False)
            
            # Should be called multiple times for batching
            assert mock_get.call_count >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
