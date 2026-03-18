"""
Tests for Unified Dashboard application.

Test coverage includes:
- Dashboard landing page
- Application listing API
- Health check aggregation
- Navigation routes (redirects)
- Proxy routes (backward compatibility)
- Error handlers
"""

import pytest
from unittest.mock import Mock
import json


class TestDashboardRoute:
    """Test dashboard landing page."""

    def test_dashboard_loads(self, client):
        """Test dashboard page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        
    def test_dashboard_shows_apps(self, client):
        """Test dashboard displays application cards."""
        response = client.get('/')
        assert response.status_code == 200
        # Check for key application names in HTML
        assert b'Initiative Viewer' in response.data or b'Lead Time' in response.data


class TestAppsListAPI:
    """Test /apps API endpoint."""

    def test_list_apps(self, client):
        """Test listing all applications."""
        response = client.get('/apps')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'apps' in data
        assert data['total_apps'] == 9
        
    def test_apps_have_required_fields(self, client):
        """Test each app has required metadata."""
        response = client.get('/apps')
        data = json.loads(response.data)
        
        for app in data['apps']:
            assert 'id' in app
            assert 'name' in app
            assert 'description' in app
            assert 'url' in app
            assert 'port' in app
            assert 'icon' in app
            assert 'color' in app


class TestHealthCheck:
    """Test /health endpoint."""

    def test_health_with_all_services_up(self, client, mock_successful_requests):
        """Test health check when all services are healthy."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['dashboard'] == 'healthy'
        assert data['port'] == 5000
        assert 'timestamp' in data
        assert data['apps']['total'] == 9
        
    def test_health_with_some_services_down(self, client, mocker):
        """Test health check when some services are unreachable."""
        # Mock mixed responses
        def mock_get_side_effect(url, timeout):
            if '5001' in url:
                response = Mock()
                response.status_code = 200
                response.elapsed.total_seconds.return_value = 0.05
                return response
            else:
                import requests
                raise requests.exceptions.ConnectionError()
        
        mocker.patch('requests.get', side_effect=mock_get_side_effect)
        
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] in ['degraded', 'unhealthy']
        assert data['apps']['healthy'] >= 0
        assert data['apps']['unhealthy'] >= 0
        
    def test_health_with_timeout(self, client, mock_timeout_requests):
        """Test health check when services timeout."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'details' in data
        # At least one service should have timeout status
        timeout_services = [d for d in data['details'] if 'timeout' in d.get('status', '').lower()]
        assert len(timeout_services) > 0
        
    def test_health_with_connection_error(self, client, mock_connection_error_requests):
        """Test health check when services are unreachable."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'
        assert data['apps']['healthy'] == 0
        
    def test_health_response_includes_app_details(self, client, mock_successful_requests):
        """Test health check includes details for each application."""
        response = client.get('/health')
        data = json.loads(response.data)
        
        assert 'details' in data
        assert len(data['details']) == 9
        
        for app_status in data['details']:
            assert 'id' in app_status
            assert 'name' in app_status
            assert 'status' in app_status
            assert 'port' in app_status


class TestFaviconRoute:
    """Test /favicon.ico route."""

    def test_favicon_returns_204(self, client):
        """Test favicon route returns 204 No Content."""
        response = client.get('/favicon.ico')
        assert response.status_code == 204


class TestNavigationRoutes:
    """Test navigation routes served directly by blueprints."""

    def test_initiative_viewer_accessible(self, client):
        """Test Initiative Viewer blueprint is reachable."""
        response = client.get('/initiative-viewer/', follow_redirects=True)
        assert response.status_code == 200

    def test_lead_time_analyzer_accessible(self, client):
        """Test Lead Time Analyzer blueprint is reachable."""
        response = client.get('/lead-time-analyzer/', follow_redirects=True)
        assert response.status_code == 200

    def test_epic_report_accessible(self, client):
        """Test Epic Report blueprint is reachable."""
        response = client.get('/epic-report/', follow_redirects=True)
        assert response.status_code == 200

    def test_pi_analyzer_accessible(self, client):
        """Test PI Analyzer blueprint is reachable."""
        response = client.get('/pi-analyzer/', follow_redirects=True)
        assert response.status_code == 200

    def test_sprint_analyzer_accessible(self, client):
        """Test Sprint Analyzer blueprint is reachable."""
        response = client.get('/sprint-analyzer/', follow_redirects=True)
        assert response.status_code == 200

    def test_pbc_analyzer_accessible(self, client):
        """Test PBC Analyzer blueprint is reachable."""
        response = client.get('/pbc-analyzer/', follow_redirects=True)
        assert response.status_code == 200

    def test_duplicate_detector_accessible(self, client):
        """Test Duplicate Detector blueprint is reachable."""
        response = client.get('/duplicate-detector/', follow_redirects=True)
        assert response.status_code == 200

    def test_psychological_safety_accessible(self, client):
        """Test Psychological Safety blueprint is reachable."""
        response = client.get('/psychological-safety/', follow_redirects=True)
        assert response.status_code == 200

    def test_epic_fixversion_accessible(self, client):
        """Test Epic Fix Version blueprint is reachable."""
        response = client.get('/epic-fixversion/', follow_redirects=True)
        assert response.status_code == 200


class TestProxyRoutes:
    """Test proxy routes for backward compatibility."""

    def test_proxy_epic_fixversion_analysis(self, client, mock_proxy_response):
        """Test proxy route for epic fix version analysis."""
        response = client.post('/analyze_epic_fixversion', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'initiative_jql': 'project = TEST'
        })
        
        assert response.status_code == 200
        assert mock_proxy_response.called
        
    def test_proxy_epic_fixversion_pdf(self, client, mock_proxy_response):
        """Test proxy route for epic fix version PDF export."""
        response = client.post('/export_epic_fixversion_pdf', json={
            'analysis_data': {'test': 'data'},
            'jira_url': 'https://test.atlassian.net'
        })
        
        assert response.status_code == 200
        assert mock_proxy_response.called
        
    def test_proxy_psychological_safety_analysis(self, client, mock_proxy_response):
        """Test proxy route for psychological safety analysis."""
        response = client.post('/analyze_safety', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST'
        })
        
        assert response.status_code == 200
        assert mock_proxy_response.called
        
    def test_proxy_safety_trends(self, client, mock_proxy_response):
        """Test proxy route for psychological safety trends."""
        response = client.post('/get_trends', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST',
            'weeks': '4'
        })
        
        assert response.status_code == 200
        assert mock_proxy_response.called
        
    def test_proxy_pbc_analysis(self, client, mock_proxy_response):
        """Test proxy route for PBC analysis."""
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST'
        })
        
        assert response.status_code == 200
        assert mock_proxy_response.called
        
    def test_proxy_handles_network_errors(self, client, mocker):
        """Test proxy handles network errors gracefully."""
        import requests
        
        mock_post = mocker.patch('requests.post')
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        response = client.post('/analyze_epic_fixversion', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'initiative_jql': 'project = TEST'
        })
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data
        
    def test_proxy_handles_timeout(self, client, mocker):
        """Test proxy handles timeout errors."""
        import requests
        
        mock_post = mocker.patch('requests.post')
        mock_post.side_effect = requests.exceptions.Timeout()
        
        response = client.post('/analyze_safety', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST'
        })
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data


class TestErrorHandlers:
    """Test error handler routes."""

    def test_404_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Page not found'
        assert 'available_routes' in data
        
    def test_404_includes_available_routes(self, client):
        """Test 404 response includes list of available routes."""
        response = client.get('/invalid-path')
        data = json.loads(response.data)
        
        assert 'available_routes' in data
        assert '/' in data['available_routes']
        assert '/health' in data['available_routes']
        assert '/apps' in data['available_routes']


class TestConfiguration:
    """Test application configuration."""

    def test_apps_config_structure(self, apps_config):
        """Test APPS configuration has correct structure."""
        assert len(apps_config) == 9
        
        for app_id, app_info in apps_config.items():
            assert 'name' in app_info
            assert 'description' in app_info
            assert 'url' in app_info
            assert 'port' in app_info
            assert 'icon' in app_info
            assert 'color' in app_info
            
    def test_apps_ports_are_unique(self, apps_config):
        """Test each application has a unique port."""
        ports = [app['port'] for app in apps_config.values()]
        assert len(ports) == len(set(ports))  # All ports unique
        
    def test_apps_urls_are_valid(self, apps_config):
        """Test application URLs are valid."""
        for app_id, app_info in apps_config.items():
            assert app_info['url'].startswith('http://') or app_info['url'].startswith('https://')
            assert f":{app_info['port']}" in app_info['url']


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_dashboard_to_app_navigation_flow(self, client):
        """Test complete navigation flow from dashboard to app."""
        # Step 1: Load dashboard
        dashboard_response = client.get('/')
        assert dashboard_response.status_code == 200
        
        # Step 2: Navigate to an app (e.g., initiative viewer) - served by blueprint
        nav_response = client.get('/initiative-viewer/', follow_redirects=True)
        assert nav_response.status_code == 200
        
    def test_health_check_and_apps_list_consistency(self, client, mock_successful_requests):
        """Test health check and apps list report same number of apps."""
        # Get apps list
        apps_response = client.get('/apps')
        apps_data = json.loads(apps_response.data)
        
        # Get health check
        health_response = client.get('/health')
        health_data = json.loads(health_response.data)
        
        # Should have same number of apps
        assert apps_data['total_apps'] == health_data['apps']['total']
        assert len(apps_data['apps']) == len(health_data['details'])
