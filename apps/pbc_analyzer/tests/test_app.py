"""
Unit tests for PBC Analyzer application.
Tests Flask routes, PBC analysis, caching, and integration.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestRoutes:
    """Test Flask routes."""
    
    def test_index_route(self, client):
        """Test index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['application'] == 'pbc_analyzer'
        assert data['version'] == '2.0.0'
        assert data['port'] == 5005
    
    def test_favicon_not_found(self, client):
        """Test favicon route."""
        response = client.get('/favicon.ico')
        assert response.status_code in [204, 404]


class TestAnalyzePBCRoute:
    """Test PBC analysis route."""
    
    def test_analyze_pbc_missing_credentials(self, client):
        """Test PBC analysis with missing credentials."""
        response = client.post('/analyze_pbc', data={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_pbc_missing_jql(self, client):
        """Test PBC analysis with missing JQL query."""
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': ''  # Empty JQL
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'JQL query is required' in data['error']
    
    def test_analyze_pbc_invalid_date_format(self, client):
        """Test PBC analysis with invalid date format."""
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST',
            'start_date': 'invalid-date'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid date format' in data['error']
    
    @patch('apps.pbc_analyzer.app.JiraClient')
    @patch('apps.pbc_analyzer.app.PBCAnalyzer')
    @patch('apps.pbc_analyzer.app.cache_manager')
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_analyze_pbc_jira_connection_failure(
        self, mock_storage, mock_cache, mock_analyzer_class, mock_client_class, client
    ):
        """Test PBC analysis with Jira connection failure."""
        # Mock Jira client that fails connection
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        # Mock cache (no cached data)
        mock_cache.get.return_value = None
        
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST',
            'start_date': '2024-08-01'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Failed to connect to Jira' in data['error']
    
    @patch('apps.pbc_analyzer.app.JiraClient')
    @patch('apps.pbc_analyzer.app.PBCAnalyzer')
    @patch('apps.pbc_analyzer.app.cache_manager')
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_analyze_pbc_success(
        self, mock_storage, mock_cache, mock_analyzer_class,
        mock_client_class, client, sample_pbc_analysis
    ):
        """Test successful PBC analysis."""
        # Mock Jira client
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock cache (no cached data initially)
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        # Mock storage
        mock_storage.save_json.return_value = True
        
        # Mock PBC Analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = sample_pbc_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ AND type in (Story, Bug)',
            'start_date': '2024-08-01'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'analysis_results' in data
        assert data['cached'] is False
        
        # Verify analyzer was called
        mock_analyzer.analyze.assert_called_once()
        
        # Verify results were cached
        mock_cache.set.assert_called_once()
        
        # Verify results were saved to storage
        mock_storage.save_json.assert_called_once()
    
    @patch('apps.pbc_analyzer.app.JiraClient')
    @patch('apps.pbc_analyzer.app.cache_manager')
    def test_analyze_pbc_returns_cached_data(
        self, mock_cache, mock_client_class, client, sample_pbc_analysis
    ):
        """Test PBC analysis returns cached data when available."""
        # Mock Jira client
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock cache with existing data
        mock_cache.get.return_value = sample_pbc_analysis
        
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ',
            'start_date': '2024-08-01'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['cached'] is True
        assert 'analysis_results' in data
    
    @patch('apps.pbc_analyzer.app.JiraClient')
    @patch('apps.pbc_analyzer.app.PBCAnalyzer')
    @patch('apps.pbc_analyzer.app.cache_manager')
    def test_analyze_pbc_with_debug_mode(
        self, mock_cache, mock_analyzer_class, mock_client_class, client
    ):
        """Test PBC analysis with debug mode enabled."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_cache.get.return_value = None
        
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {'summary': {'total_issues': 5}}
        mock_analyzer_class.return_value = mock_analyzer
        
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST',
            'start_date': '2024-08-01',
            'debug': 'on'
        })
        
        assert response.status_code == 200
        # Verify analyzer was created with debug=True
        mock_analyzer_class.assert_called_with(mock_client, debug=True)


class TestCachedResultsRoutes:
    """Test cached results routes."""
    
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_get_cached_results_not_found(self, mock_storage, client):
        """Test getting cached results with invalid ID."""
        mock_storage.load_json.return_value = None
        
        response = client.get('/get_cached_results/invalid_id')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_get_cached_results_success(self, mock_storage, client, sample_pbc_analysis):
        """Test successfully getting cached results."""
        mock_storage.load_json.return_value = sample_pbc_analysis
        
        response = client.get('/get_cached_results/pbc_20260220_120000')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'analysis_results' in data
        assert data['analysis_results']['analysis_id'] == 'pbc_20260220_120000'
    
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_list_cached_results_empty(self, mock_storage, client):
        """Test listing cached results when none exist."""
        mock_storage.list_files.return_value = []
        
        response = client.get('/list_cached_results')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['cached_results']) == 0
    
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_list_cached_results_success(self, mock_storage, client, sample_pbc_analysis):
        """Test listing cached results with existing analyses."""
        # Mock file list
        mock_storage.list_files.return_value = ['pbc_20260220_120000.json', 'pbc_20260219_100000.json']
        
        # Mock loading each file
        def mock_load(filename):
            if filename == 'pbc_20260220_120000.json':
                return sample_pbc_analysis
            elif filename == 'pbc_20260219_100000.json':
                return {
                    'analysis_id': 'pbc_20260219_100000',
                    'timestamp': '2026-02-19T10:00:00',
                    'start_date': '2024-07-01',
                    'summary': {
                        'total_projects': 2,
                        'total_issues': 25
                    }
                }
            return None
        
        mock_storage.load_json.side_effect = mock_load
        
        response = client.get('/list_cached_results')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['cached_results']) == 2
        
        # Verify sorting (newest first)
        assert data['cached_results'][0]['analysis_id'] == 'pbc_20260220_120000'
        assert data['cached_results'][1]['analysis_id'] == 'pbc_20260219_100000'


class TestPBCConfiguration:
    """Test PBC configuration loading."""
    
    @patch('apps.pbc_analyzer.app.load_pbc_config')
    def test_load_pbc_config_default(self, mock_config, client):
        """Test loading default PBC configuration."""
        mock_config.return_value = {
            'start_date': '2024-08-01',
            'default_jql': 'project = TEST',
            'analysis_description': 'Test description'
        }
        
        response = client.get('/')
        assert response.status_code == 200


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @patch('apps.pbc_analyzer.app.JiraClient')
    @patch('apps.pbc_analyzer.app.PBCAnalyzer')
    @patch('apps.pbc_analyzer.app.cache_manager')
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_full_workflow_analysis_to_retrieval(
        self, mock_storage, mock_cache, mock_analyzer_class,
        mock_client_class, client, sample_pbc_analysis
    ):
        """Test complete workflow from analysis to retrieval."""
        # Setup mocks
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_cache.get.return_value = None  # No cache initially
        mock_cache.set.return_value = True
        
        mock_storage.save_json.return_value = True
        mock_storage.load_json.return_value = sample_pbc_analysis
        
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = sample_pbc_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Execute analysis
        analysis_response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ',
            'start_date': '2024-08-01'
        })
        
        assert analysis_response.status_code == 200
        analysis_data = json.loads(analysis_response.data)
        assert analysis_data['success'] is True
        
        # Retrieve saved results
        analysis_id = analysis_data['analysis_results'].get('analysis_id')
        retrieval_response = client.get(f'/get_cached_results/{analysis_id}')
        
        assert retrieval_response.status_code == 200
        retrieval_data = json.loads(retrieval_response.data)
        assert retrieval_data['success'] is True
        
        # Verify all components were called
        mock_client.test_connection.assert_called_once()
        mock_analyzer.analyze.assert_called_once()
        mock_cache.set.assert_called_once()
        mock_storage.save_json.assert_called_once()
    
    @patch('apps.pbc_analyzer.app.JiraClient')
    @patch('apps.pbc_analyzer.app.cache_manager')
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_list_multiple_analyses(
        self, mock_storage, mock_cache, mock_client_class, client
    ):
        """Test listing multiple saved analyses."""
        # Mock storage with multiple files
        mock_storage.list_files.return_value = [
            'pbc_20260220_120000.json',
            'pbc_20260219_100000.json',
            'pbc_20260218_140000.json'
        ]
        
        def mock_load(filename):
            timestamp = filename.replace('pbc_', '').replace('.json', '')
            return {
                'analysis_id': f'pbc_{timestamp}',
                'timestamp': f'2026-02-{timestamp[6:8]}T{timestamp[9:11]}:00:00',
                'start_date': '2024-08-01',
                'summary': {'total_projects': 1, 'total_issues': 10}
            }
        
        mock_storage.load_json.side_effect = mock_load
        
        response = client.get('/list_cached_results')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['cached_results']) == 3


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('apps.pbc_analyzer.app.JiraClient')
    @patch('apps.pbc_analyzer.app.PBCAnalyzer')
    @patch('apps.pbc_analyzer.app.cache_manager')
    def test_analyzer_exception_handling(
        self, mock_cache, mock_analyzer_class, mock_client_class, client
    ):
        """Test handling of analyzer exceptions."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_cache.get.return_value = None
        
        mock_analyzer = Mock()
        mock_analyzer.analyze.side_effect = Exception("Analysis failed")
        mock_analyzer_class.return_value = mock_analyzer
        
        response = client.post('/analyze_pbc', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST',
            'start_date': '2024-08-01'
        })
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('apps.pbc_analyzer.app.file_storage')
    def test_storage_exception_handling(self, mock_storage, client):
        """Test handling of storage exceptions."""
        mock_storage.load_json.side_effect = Exception("Storage error")
        
        response = client.get('/get_cached_results/test_id')
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
