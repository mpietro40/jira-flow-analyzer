"""
Unit tests for Epic Report application.

Tests cover:
- Flask routes
- Epic analysis logic
- Form validation
- Error handling
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.epic_report.app import blueprint, EpicAnalyzer


# Route Tests

def test_index_route(client):
    """Test index route returns form."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Epic Report' in response.data or b'epic' in response.data.lower()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['app'] == 'epic_report'
    assert 'version' in data


def test_analyze_epics_missing_credentials(client):
    """Test analyze route with missing credentials."""
    response = client.post('/analyze_epics', data={
        'jql_query': 'project = TEST'
    })
    assert response.status_code == 400


def test_analyze_epics_missing_jql(client):
    """Test analyze route with missing JQL."""
    response = client.post('/analyze_epics', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'jql_query': ''
    })
    assert response.status_code == 400


def test_analyze_epics_jql_too_long(client):
    """Test analyze route with JQL too long."""
    long_jql = 'a' * 2001
    response = client.post('/analyze_epics', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'jql_query': long_jql
    })
    assert response.status_code == 400


@patch('apps.epic_report.app.JiraClient')
@patch('apps.epic_report.app.EpicAnalyzer')
def test_analyze_epics_success(mock_analyzer_class, mock_client_class, client, sample_issues):
    """Test successful epic analysis."""
    # Setup mocks
    mock_client = Mock()
    mock_client.test_connection.return_value = True
    mock_client.fetch_issues.return_value = sample_issues
    mock_client_class.return_value = mock_client
    
    mock_analyzer = Mock()
    mock_analyzer.analyze_parent_epics.return_value = {
        'epics': [
            {
                'key': 'EPIC-1',
                'summary': 'Test Epic',
                'status': 'In Progress',
                'assignee': 'John Doe',
                'project': 'PROJ',
                'open_count': 2,
                'closed_count': 1,
                'total_count': 3
            }
        ],
        'epic_keys_csv': 'EPIC-1',
        'issues_without_epic': []
    }
    mock_analyzer_class.return_value = mock_analyzer
    
    # Make request
    response = client.post('/analyze_epics', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'jql_query': 'project = TEST'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'epics' in data
    assert len(data['epics']) == 1


@patch('apps.epic_report.app.cache')
@patch('apps.epic_report.app.JiraClient')
def test_analyze_epics_connection_failure(mock_client_class, mock_cache, client):
    """Test epic analysis with connection failure."""
    mock_cache.is_valid.return_value = False  # No cached data
    mock_client = Mock()
    mock_client.test_connection.return_value = False
    mock_client_class.return_value = mock_client

    response = client.post('/analyze_epics', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'jql_query': 'project = TEST'
    })

    assert response.status_code == 401


@patch('apps.epic_report.app.JiraClient')
def test_analyze_epics_no_issues_found(mock_client_class, client):
    """Test epic analysis with no issues found."""
    mock_client = Mock()
    mock_client.test_connection.return_value = True
    mock_client.fetch_issues.return_value = []
    mock_client_class.return_value = mock_client
    
    response = client.post('/analyze_epics', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'jql_query': 'project = NONEXISTENT'
    })
    
    assert response.status_code == 404


# EpicAnalyzer Tests

def test_epic_analyzer_initialization():
    """Test EpicAnalyzer initialization."""
    mock_client = Mock()
    analyzer = EpicAnalyzer(mock_client)
    assert analyzer.jira_client == mock_client


def test_find_epic_link_field_customfield(sample_issues):
    """Test finding epic link in customfield."""
    mock_client = Mock()
    analyzer = EpicAnalyzer(mock_client)
    
    issue = sample_issues[0]
    epic_key = analyzer.find_epic_link_field(issue)
    assert epic_key == 'EPIC-1'


def test_find_epic_link_field_none(sample_issues):
    """Test finding epic link when none exists."""
    mock_client = Mock()
    analyzer = EpicAnalyzer(mock_client)
    
    issue = sample_issues[3]  # Issue without epic
    epic_key = analyzer.find_epic_link_field(issue)
    assert epic_key is None


def test_find_epic_link_field_dict_format():
    """Test finding epic link in dict format."""
    mock_client = Mock()
    analyzer = EpicAnalyzer(mock_client)
    
    issue = {
        'key': 'TEST-1',
        'fields': {
            'customfield_10014': {'key': 'EPIC-X'}
        }
    }
    
    epic_key = analyzer.find_epic_link_field(issue)
    assert epic_key == 'EPIC-X'


def test_fetch_epic_details(sample_epic_data):
    """Test fetching epic details."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_epic_data
    mock_client.session.get.return_value = mock_response
    mock_client.base_url = 'https://test.atlassian.net'
    mock_client.timeout = 30
    
    analyzer = EpicAnalyzer(mock_client)
    epic_details = analyzer.fetch_epic_details('EPIC-1')
    
    assert epic_details is not None
    assert epic_details['key'] == 'EPIC-1'
    assert epic_details['summary'] == 'Test Epic 1'
    assert epic_details['status'] == 'In Progress'
    assert epic_details['assignee'] == 'John Doe'


def test_fetch_epic_details_failure():
    """Test fetching epic details with failure."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 404
    mock_client.session.get.return_value = mock_response
    mock_client.base_url = 'https://test.atlassian.net'
    mock_client.timeout = 30
    
    analyzer = EpicAnalyzer(mock_client)
    epic_details = analyzer.fetch_epic_details('EPIC-X')
    
    assert epic_details is None


def test_count_epic_children():
    """Test counting epic children."""
    mock_client = Mock()
    mock_client.fetch_issues.return_value = [
        {'fields': {'status': {'name': 'Done'}}},
        {'fields': {'status': {'name': 'In Progress'}}},
        {'fields': {'status': {'name': 'Closed'}}},
        {'fields': {'status': {'name': 'Open'}}}
    ]
    
    analyzer = EpicAnalyzer(mock_client)
    counts = analyzer.count_epic_children('EPIC-1')
    
    assert counts['open_count'] == 2  # In Progress, Open
    assert counts['closed_count'] == 2  # Done, Closed
    assert counts['total_count'] == 4


def test_analyze_parent_epics(sample_issues, sample_epic_data):
    """Test analyzing parent epics."""
    mock_client = Mock()
    
    # Mock fetch_epic_details
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_epic_data
    mock_client.session.get.return_value = mock_response
    mock_client.base_url = 'https://test.atlassian.net'
    mock_client.timeout = 30
    
    # Mock count children
    mock_client.fetch_issues.return_value = [
        {'fields': {'status': {'name': 'Done'}}},
        {'fields': {'status': {'name': 'Open'}}}
    ]
    
    analyzer = EpicAnalyzer(mock_client)
    result = analyzer.analyze_parent_epics(sample_issues)
    
    assert 'epics' in result
    assert 'epic_keys_csv' in result
    assert 'issues_without_epic' in result
    assert len(result['issues_without_epic']) == 1  # PROJ-4 has no epic


# Integration Tests

@patch('apps.epic_report.app.JiraClient')
@patch('apps.epic_report.app.EpicAnalyzer')
def test_full_workflow(mock_analyzer_class, mock_client_class, client):
    """Test full workflow: submit form → analyze → get results."""
    # Setup complete mocks
    mock_client = Mock()
    mock_client.test_connection.return_value = True
    mock_client.fetch_issues.return_value = [
        {'key': 'TEST-1', 'fields': {'customfield_10014': 'EPIC-1'}}
    ]
    mock_client_class.return_value = mock_client
    
    mock_analyzer = Mock()
    mock_analyzer.analyze_parent_epics.return_value = {
        'epics': [
            {
                'key': 'EPIC-1',
                'summary': 'Test',
                'open_count': 1,
                'closed_count': 0,
                'total_count': 1
            }
        ],
        'epic_keys_csv': 'EPIC-1',
        'issues_without_epic': []
    }
    mock_analyzer_class.return_value = mock_analyzer
    
    # Submit analysis
    response = client.post('/analyze_epics', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'jql_query': 'project = TEST'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['summary']['total_epics'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
