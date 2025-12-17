"""
Acceptance Tests for AC001: Jira Connection and Authentication
"""
import pytest
from unittest.mock import Mock, patch
from jira_client import JiraClient


class TestAC001_JiraConnection:
    """Test suite for Jira connection acceptance criteria"""
    
    def test_ac001_1_successful_connection(self):
        """
        AC001.1: Successful Connection
        Given valid Jira URL and access token
        When user attempts to connect
        Then connection is established successfully
        """
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'name': 'Test User'}
            
            client = JiraClient('https://test.atlassian.net', 'valid_token')
            result = client.test_connection()
            
            assert result is True
            mock_get.assert_called_once()
    
    def test_ac001_2_invalid_token(self):
        """
        AC001.2: Invalid Token
        Given valid Jira URL but invalid access token
        When user attempts to connect
        Then authentication fails with 401 error
        """
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value.status_code = 401
            
            client = JiraClient('https://test.atlassian.net', 'invalid_token')
            result = client.test_connection()
            
            assert result is False
    
    def test_ac001_3_invalid_url(self):
        """
        AC001.3: Invalid URL
        Given invalid Jira URL
        When user attempts to connect
        Then connection fails
        """
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = Exception('Connection failed')
            
            client = JiraClient('https://invalid-url', 'token')
            result = client.test_connection()
            
            assert result is False
    
    def test_ac001_4_connection_timeout_retry(self):
        """
        AC001.4: Connection Timeout
        Given valid credentials but slow network
        When connection exceeds timeout threshold
        Then retry mechanism is triggered
        """
        import requests
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout(),
                requests.exceptions.Timeout(),
                Mock(status_code=200)
            ]
            
            client = JiraClient('https://test.atlassian.net', 'token')
            result = client.test_connection()
            
            assert result is True
            assert mock_get.call_count == 3
    
    def test_ac001_5_session_management(self):
        """
        AC001.5: Session Management
        Given established connection
        When multiple API calls are made
        Then session is reused for efficiency
        """
        client = JiraClient('https://test.atlassian.net', 'token')
        
        assert client.session is not None
        assert 'Authorization' in client.session.headers
        assert client.session.headers['Authorization'] == 'Bearer token'
        assert client.session.headers['Content-Type'] == 'application/json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
