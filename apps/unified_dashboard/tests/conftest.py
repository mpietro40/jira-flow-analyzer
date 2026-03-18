"""
Test fixtures for Unified Dashboard application.
"""

import pytest
from apps.unified_dashboard.app import app
from apps.unified_dashboard.config import APPS


@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def apps_config():
    """Application configuration."""
    return APPS


@pytest.fixture
def mock_health_response():
    """Mock successful health check response from an application."""
    return {
        'status': 'healthy',
        'port': 5001,
        'timestamp': '2026-02-20T10:00:00'
    }


@pytest.fixture
def mock_health_response_unhealthy():
    """Mock unhealthy response from an application."""
    return {
        'status': 'unhealthy',
        'port': 5001,
        'error': 'Service degraded'
    }


@pytest.fixture
def sample_app_list():
    """Sample application list for testing."""
    return [
        {
            'id': 'initiative_viewer',
            'name': 'Initiative Viewer',
            'description': '4-level hierarchical initiative visualization',
            'url': 'http://localhost:5001',
            'port': 5001,
            'icon': 'fa-sitemap',
            'color': '#667eea'
        },
        {
            'id': 'epic_report',
            'name': 'Epic Report',
            'description': 'Parent epic discovery and child count analysis',
            'url': 'http://localhost:5002',
            'port': 5002,
            'icon': 'fa-scroll',
            'color': '#764ba2'
        }
    ]


@pytest.fixture
def mock_successful_requests(mocker):
    """Mock requests library for successful health checks."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.elapsed.total_seconds.return_value = 0.05
    
    mock_get = mocker.patch('requests.get')
    mock_get.return_value = mock_response
    
    return mock_get


@pytest.fixture
def mock_timeout_requests(mocker):
    """Mock requests library for timeout scenarios."""
    import requests
    
    mock_get = mocker.patch('requests.get')
    mock_get.side_effect = requests.exceptions.Timeout()
    
    return mock_get


@pytest.fixture
def mock_connection_error_requests(mocker):
    """Mock requests library for connection error scenarios."""
    import requests
    
    mock_get = mocker.patch('requests.get')
    mock_get.side_effect = requests.exceptions.ConnectionError()
    
    return mock_get


@pytest.fixture
def mock_proxy_response(mocker):
    """Mock requests.post for proxy route testing."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = b'{"success": true}'
    mock_response.headers.items.return_value = [('Content-Type', 'application/json')]
    
    mock_post = mocker.patch('requests.post')
    mock_post.return_value = mock_response
    
    return mock_post
