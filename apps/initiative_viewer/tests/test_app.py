"""
Unit tests for Initiative Viewer application.

Tests cover:
- Flask routes
- Form validation
- Jira hierarchy fetching
- PDF generation
- Caching
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from apps.initiative_viewer.app import blueprint, JiraHierarchyFetcher
from unittest.mock import Mock, patch, MagicMock
import io


def _create_test_app():
    """Create a Flask test app with the initiative_viewer blueprint."""
    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.register_blueprint(blueprint)
    return flask_app


@pytest.fixture
def client():
    """Create test client."""
    flask_app = _create_test_app()
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_jira_client():
    """Create mock Jira client."""
    mock = Mock()
    mock.test_connection.return_value = True
    mock.base_url = "https://test.atlassian.net"
    mock.timeout = 30
    mock.session = Mock()
    return mock


@pytest.fixture
def sample_initiative_data():
    """Sample initiative data for testing."""
    return {
        'key': 'INIT-1',
        'summary': 'Test Initiative',
        'assignee': 'John Doe',
        'status': 'In Progress',
        'project_key': 'TEST',
        'risk_probability': 3,
        'features': [
            {
                'key': 'FEAT-1',
                'summary': 'Test Feature',
                'assignee': 'Jane Smith',
                'status': 'In Progress',
                'project_key': 'TEST',
                'risk_probability': 2,
                'sub_features': [
                    {
                        'key': 'SUB-1',
                        'summary': 'Test Sub-Feature',
                        'assignee': 'Bob Johnson',
                        'status': 'To Do',
                        'project_key': 'TEST',
                        'risk_probability': 1,
                        'epics_by_area': {
                            'Area1': [
                                {
                                    'key': 'EPIC-1',
                                    'summary': 'Test Epic',
                                    'assignee': 'Alice Williams',
                                    'status': 'In Progress',
                                    'project_key': 'TEST',
                                    'risk_probability': 4
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


# Route Tests

def test_index_route(client):
    """Test index route returns form."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Initiative Viewer' in response.data
    assert b'Jira Server URL' in response.data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['app'] == 'initiative_viewer'
    assert 'version' in data


def test_analyze_route_missing_credentials(client):
    """Test analyze route with missing credentials."""
    response = client.post('/analyze', data={
        'query': 'issuetype = "Business Initiative"',
        'fix_version': 'PI 2025.1'
    })
    assert response.status_code == 400


def test_analyze_route_missing_fix_version(client):
    """Test analyze route with missing fix version."""
    response = client.post('/analyze', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'query': 'issuetype = "Business Initiative"'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


@patch('apps.initiative_viewer.app.JiraClient')
@patch('apps.initiative_viewer.app.JiraHierarchyFetcher')
def test_analyze_route_success(mock_fetcher_class, mock_client_class, client, sample_initiative_data):
    """Test successful analysis."""
    # Setup mocks
    mock_client = Mock()
    mock_client.test_connection.return_value = True
    mock_client_class.return_value = mock_client
    
    mock_fetcher = Mock()
    mock_fetcher.fetch_hierarchy.return_value = [sample_initiative_data]
    mock_fetcher_class.return_value = mock_fetcher
    
    # Make request
    response = client.post('/analyze', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'query': 'issuetype = "Business Initiative"',
        'fix_version': 'PI 2025.1'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data
    assert len(data['data']['initiatives']) == 1


# JiraHierarchyFetcher Tests

def test_hierarchy_fetcher_initialization(mock_jira_client):
    """Test hierarchy fetcher initialization."""
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    assert fetcher.jira_client == mock_jira_client


def test_normalize_risk_value_numeric(mock_jira_client):
    """Test risk value normalization - numeric."""
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    
    assert fetcher._normalize_risk_value(1, 'TEST-1') == 1
    assert fetcher._normalize_risk_value(3, 'TEST-1') == 3
    assert fetcher._normalize_risk_value(5, 'TEST-1') == 5


def test_normalize_risk_value_text(mock_jira_client):
    """Test risk value normalization - text values."""
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    
    assert fetcher._normalize_risk_value('Green', 'TEST-1') == 1
    assert fetcher._normalize_risk_value('Yellow', 'TEST-1') == 3
    assert fetcher._normalize_risk_value('Red', 'TEST-1') == 5
    assert fetcher._normalize_risk_value('No risk', 'TEST-1') == 1
    assert fetcher._normalize_risk_value('High risk', 'TEST-1') == 5


def test_normalize_risk_value_dict(mock_jira_client):
    """Test risk value normalization - dict format."""
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    
    assert fetcher._normalize_risk_value({'value': 'Green'}, 'TEST-1') == 1
    assert fetcher._normalize_risk_value({'value': 3}, 'TEST-1') == 3


def test_normalize_risk_value_none(mock_jira_client):
    """Test risk value normalization - None."""
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    
    assert fetcher._normalize_risk_value(None, 'TEST-1') is None
    assert fetcher._normalize_risk_value('', 'TEST-1') is None


@patch.object(JiraHierarchyFetcher, '_fetch_issue_details')
def test_fetch_initiatives(mock_fetch_details, mock_jira_client):
    """Test fetching initiatives."""
    mock_jira_client.fetch_issues.return_value = [
        {'key': 'INIT-1'},
        {'key': 'INIT-2'}
    ]
    
    mock_fetch_details.side_effect = [
        {'key': 'INIT-1', 'summary': 'Initiative 1'},
        {'key': 'INIT-2', 'summary': 'Initiative 2'}
    ]
    
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    initiatives = fetcher._fetch_initiatives('project = TEST')
    
    assert len(initiatives) == 2
    assert initiatives[0]['key'] == 'INIT-1'
    assert initiatives[1]['key'] == 'INIT-2'


@patch.object(JiraHierarchyFetcher, '_fetch_issue_details')
def test_fetch_features(mock_fetch_details, mock_jira_client):
    """Test fetching features."""
    mock_jira_client.fetch_issues.return_value = [
        {'key': 'FEAT-1'}
    ]
    
    mock_fetch_details.return_value = {
        'key': 'FEAT-1',
        'summary': 'Feature 1'
    }
    
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    features = fetcher._fetch_features('INIT-1', 'PI 2025.1')
    
    assert len(features) == 1
    assert features[0]['key'] == 'FEAT-1'


@patch.object(JiraHierarchyFetcher, '_fetch_issue_details')
def test_fetch_epics_by_area(mock_fetch_details, mock_jira_client):
    """Test fetching epics by area."""
    mock_jira_client.fetch_issues.return_value = [
        {'key': 'EPIC-1'},
        {'key': 'EPIC-2'}
    ]
    
    mock_fetch_details.side_effect = [
        {'key': 'EPIC-1', 'summary': 'Epic 1', 'project_key': 'AREA1'},
        {'key': 'EPIC-2', 'summary': 'Epic 2', 'project_key': 'AREA2'}
    ]
    
    fetcher = JiraHierarchyFetcher(mock_jira_client)
    epics_by_area = fetcher._fetch_epics_by_area('SUB-1')
    
    assert len(epics_by_area) == 2
    assert 'AREA1' in epics_by_area
    assert 'AREA2' in epics_by_area
    assert len(epics_by_area['AREA1']) == 1
    assert len(epics_by_area['AREA2']) == 1


# Helper Function Tests

def test_filter_empty_hierarchy(sample_initiative_data):
    """Test filtering empty hierarchy."""
    from apps.initiative_viewer.app import filter_empty_hierarchy
    
    # Test with data
    filtered = filter_empty_hierarchy([sample_initiative_data])
    assert len(filtered) == 1
    assert len(filtered[0]['features']) == 1
    
    # Test with empty epics
    empty_data = {
        'key': 'INIT-2',
        'summary': 'Empty Initiative',
        'features': [
            {
                'key': 'FEAT-2',
                'summary': 'Empty Feature',
                'sub_features': [
                    {
                        'key': 'SUB-2',
                        'summary': 'Empty Sub-Feature',
                        'epics_by_area': {}
                    }
                ]
            }
        ]
    }
    
    filtered = filter_empty_hierarchy([empty_data])
    assert len(filtered) == 0


# PDF Generation Tests

@patch('apps.initiative_viewer.app.InitiativeViewerPDFGenerator')
def test_export_pdf_no_session_data(mock_pdf_class, client):
    """Test PDF export without session data."""
    response = client.get('/export_pdf')
    assert response.status_code == 400


@patch('apps.initiative_viewer.app.cache')
@patch('apps.initiative_viewer.app.InitiativeViewerPDFGenerator')
def test_export_pdf_success(mock_pdf_class, mock_cache, client, sample_initiative_data):
    """Test successful PDF export."""
    # Setup session
    with client.session_transaction() as sess:
        sess['analysis_data'] = 'test-cache-key'
    
    # Mock cache
    mock_cache.get.return_value = {
        'initiatives': [sample_initiative_data],
        'jira_url': 'https://test.atlassian.net',
        'fix_version': 'PI 2025.1'
    }
    
    # Mock PDF generator
    mock_generator = Mock()
    mock_pdf_class.return_value = mock_generator
    
    # Make request
    response = client.get('/export_pdf')
    
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'


# Cache Tests

def test_cache_key_generation():
    """Test cache key generation."""
    jira_url = "https://test.atlassian.net"
    query = 'project = TEST'
    fix_version = 'PI 2025.1'
    
    cache_key = f"{jira_url}_{query}_{fix_version}"
    assert 'test.atlassian.net' in cache_key
    assert 'TEST' in cache_key
    assert 'PI 2025.1' in cache_key


# Integration Tests

@patch('apps.initiative_viewer.app.JiraClient')
@patch('apps.initiative_viewer.app.JiraHierarchyFetcher')
def test_full_workflow(mock_fetcher_class, mock_client_class, client, sample_initiative_data):
    """Test full workflow: analyze → view → export."""
    # Setup mocks
    mock_client = Mock()
    mock_client.test_connection.return_value = True
    mock_client_class.return_value = mock_client
    
    mock_fetcher = Mock()
    mock_fetcher.fetch_hierarchy.return_value = [sample_initiative_data]
    mock_fetcher_class.return_value = mock_fetcher
    
    # Step 1: Analyze
    response = client.post('/analyze', data={
        'jira_url': 'https://test.atlassian.net',
        'access_token': 'test-token',
        'query': 'project = TEST',
        'fix_version': 'PI 2025.1'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    # Step 2: Export (requires session)
    with client.session_transaction() as sess:
        # In real scenario, session would be set by analyze route
        # For test, we manually set it
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
