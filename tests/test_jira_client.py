"""
Tests for Jira Client module
"""

import pytest
import responses
import sys
import os
from datetime import datetime
import pytz

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jira_client import JiraClient
import json

class TestJiraClient:
    """Test suite for JiraClient class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.base_url = "https://test.atlassian.net"
        self.access_token = "test_token"
        self.client = JiraClient(self.base_url, self.access_token)
    
    @responses.activate
    def test_connection_success(self):
        """Test successful connection to Jira."""
        responses.add(
            responses.GET,
            f"{self.base_url}/rest/api/2/myself",
            json={"key": "testuser"},
            status=200
        )
        
        assert self.client.test_connection() == True
    
    @responses.activate
    def test_connection_failure(self):
        """Test failed connection to Jira."""
        responses.add(
            responses.GET,
            f"{self.base_url}/rest/api/2/myself",
            status=401
        )
        
        assert self.client.test_connection() == False
    
    @responses.activate
    def test_fetch_issues_success(self):
        """Test successful issue fetching."""
        mock_response = {
            "total": 1,
            "issues": [{
                "key": "TEST-1",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "priority": {"name": "High"},
                    "created": "2023-01-01T00:00:00.000+0000",
                    "resolutiondate": "2023-01-02T00:00:00.000+0000",
                    "assignee": {"displayName": "Test User"}
                },
                "changelog": {
                    "histories": [{
                        "created": "2023-01-01T12:00:00.000+0000",
                        "items": [{
                            "field": "status",
                            "fromString": "To Do",
                            "toString": "In Progress"
                        }]
                    }]
                }
            }]
        }
        
        responses.add(
            responses.GET,
            f"{self.base_url}/rest/api/2/search",
            json=mock_response,
            status=200
        )
        
        issues = self.client.fetch_issues("project = TEST")
        
        assert len(issues) == 1
        assert issues[0]["key"] == "TEST-1"
        assert issues[0]["summary"] == "Test issue"
        assert len(issues[0]["status_history"]) == 1

    # NEW TIMEZONE-SPECIFIC TESTS
    
    def test_process_issue_with_multiple_timezones(self):
        """Test processing issue with different timezones in changelog."""
        mock_issue = {
            "key": "TZ-TEST",
            "fields": {
                "summary": "Timezone test issue",
                "status": {"name": "Done"},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High"},
                "created": "2023-01-01T09:00:00.000+0100",  # CET
                "resolutiondate": "2023-01-05T17:00:00.000-0800",  # PST
                "assignee": {"displayName": "Global User"}
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2023-01-02T14:30:00.000+0000",  # UTC
                        "items": [{
                            "field": "status",
                            "fromString": "Open",
                            "toString": "In Progress"
                        }]
                    },
                    {
                        "created": "2023-01-04T22:15:00.000+0900",  # JST
                        "items": [{
                            "field": "status",
                            "fromString": "In Progress", 
                            "toString": "Testing"
                        }]
                    },
                    {
                        "created": "2023-01-05T17:00:00.000-0800",  # PST
                        "items": [{
                            "field": "status",
                            "fromString": "Testing",
                            "toString": "Done"
                        }]
                    }
                ]
            }
        }
        
        processed = self.client._process_issue(mock_issue)
        
        assert processed is not None
        assert processed['key'] == 'TZ-TEST'
        assert len(processed['status_history']) == 3
        
        # Verify all status transitions are captured
        status_changes = [t['to_status'] for t in processed['status_history']]
        assert 'In Progress' in status_changes
        assert 'Testing' in status_changes  
        assert 'Done' in status_changes
    
    def test_process_issue_with_malformed_timezone(self):
        """Test processing issue with malformed timezone data."""
        mock_issue = {
            "key": "BAD-TZ",
            "fields": {
                "summary": "Bad timezone issue",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Low"},
                "created": "not-a-date",  # Invalid date
                "resolutiondate": None,
                "assignee": None
            },
            "changelog": {
                "histories": [{
                    "created": "2023-01-01T12:00:00.000+9999",  # Invalid timezone
                    "items": [{
                        "field": "status",
                        "fromString": "To Do",
                        "toString": "In Progress"
                    }]
                }]
            }
        }
        
        processed = self.client._process_issue(mock_issue)
        
        # Should handle gracefully
        assert processed is not None
        assert processed['key'] == 'BAD-TZ'
        assert processed['created'] == "not-a-date"  # Preserved as-is
        # Status history should still be included (raw data preserved)
        assert len(processed['status_history']) == 1
    
    def test_process_issue_missing_changelog(self):
        """Test processing issue without changelog."""
        mock_issue = {
            "key": "NO-CHANGELOG",
            "fields": {
                "summary": "Issue without changelog",
                "status": {"name": "Open"},
                "issuetype": {"name": "Task"},
                "priority": {"name": "Medium"},
                "created": "2023-01-01T12:00:00.000+0000",
                "resolutiondate": None,
                "assignee": {"displayName": "Test User"}
            }
            # No changelog field
        }
        
        processed = self.client._process_issue(mock_issue)
        
        assert processed is not None
        assert processed['key'] == 'NO-CHANGELOG'
        assert processed['status_history'] == []
    
    def test_process_issue_empty_changelog_histories(self):
        """Test processing issue with empty changelog histories."""
        mock_issue = {
            "key": "EMPTY-CHANGELOG", 
            "fields": {
                "summary": "Issue with empty changelog",
                "status": {"name": "Open"},
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
                "created": "2023-01-01T12:00:00.000+0000",
                "resolutiondate": None,
                "assignee": {"displayName": "Test User"}
            },
            "changelog": {
                "histories": []  # Empty histories
            }
        }
        
        processed = self.client._process_issue(mock_issue)
        
        assert processed is not None
        assert processed['key'] == 'EMPTY-CHANGELOG'
        assert processed['status_history'] == []