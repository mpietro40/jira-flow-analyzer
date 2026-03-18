"""
Unit tests for PI Analyzer application.
Tests Flask routes, PIAnalyzer class, and integration.
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
        assert data['application'] == 'pi_analyzer'
        assert data['version'] == '2.0.0'
    
    def test_get_config(self, client):
        """Test get configuration endpoint."""
        response = client.get('/get_config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'base_project' in data
        assert 'completion_statuses' in data
    
    def test_list_cached_results_empty(self, client):
        """Test listing cached results when none exist."""
        response = client.get('/list_cached_results')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'cached_results' in data
        assert isinstance(data['cached_results'], list)


class TestAnalyzePIRoute:
    """Test PI analysis route."""
    
    def test_analyze_pi_missing_fields(self, client):
        """Test PI analysis with missing required fields."""
        response = client.post('/analyze_pi', data={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_pi_invalid_date_format(self, client):
        """Test PI analysis with invalid date format."""
        response = client.post('/analyze_pi', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'pi_start_date': 'invalid-date',
            'pi_end_date': '2026-02-28'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid date format' in data['error']
    
    @patch('apps.pi_analyzer.app.JiraClient')
    @patch('apps.pi_analyzer.app.PIAnalyzer')
    def test_analyze_pi_jira_connection_failure(
        self, mock_analyzer_class, mock_client_class, client
    ):
        """Test PI analysis with Jira connection failure."""
        # Mock Jira client that fails connection
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        response = client.post('/analyze_pi', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'pi_start_date': '2026-02-01',
            'pi_end_date': '2026-02-28'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Failed to connect to Jira' in data['error']
    
    @patch('apps.pi_analyzer.app.save_analysis_results')
    @patch('apps.pi_analyzer.app.JiraClient')
    @patch('apps.pi_analyzer.app.PIAnalyzer')
    def test_analyze_pi_success(
        self, mock_analyzer_class, mock_client_class, 
        mock_save, client, sample_pi_analysis
    ):
        """Test successful PI analysis."""
        # Mock Jira client
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock PI Analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_pi.return_value = sample_pi_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock save function
        mock_save.return_value = True
        
        response = client.post('/analyze_pi', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'pi_start_date': '2026-02-01',
            'pi_end_date': '2026-02-28',
            'include_full_backlog': 'on'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'analysis_results' in data
        assert 'cache_key' in data
        assert data['cache_key'] == '2026-02-01_2026-02-28'
        
        # Verify analyzer was called with correct parameters
        mock_analyzer.analyze_pi.assert_called_once_with(
            '2026-02-01',
            '2026-02-28',
            True  # include_full_backlog
        )


class TestCachedResultsRoutes:
    """Test cached results routes."""
    
    @patch('apps.pi_analyzer.app.load_analysis_results')
    def test_get_cached_results_found(self, mock_load, client, sample_pi_analysis):
        """Test retrieving cached results that exist."""
        mock_load.return_value = {
            'results': sample_pi_analysis,
            'timestamp': '2026-02-20T10:00:00'
        }
        
        response = client.get('/get_cached_results/2026-02-01_2026-02-28')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'analysis_results' in data
        assert 'cached_at' in data
    
    @patch('apps.pi_analyzer.app.load_analysis_results')
    def test_get_cached_results_not_found(self, mock_load, client):
        """Test retrieving cached results that don't exist."""
        mock_load.return_value = None
        
        response = client.get('/get_cached_results/nonexistent_key')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestPDFGenerationRoute:
    """Test PDF generation route."""
    
    @patch('apps.pi_analyzer.app.PIPDFReportGenerator')
    @patch('apps.pi_analyzer.app.send_file')
    def test_generate_pi_report_success(
        self, mock_send_file, mock_pdf_class, client, sample_pi_analysis
    ):
        """Test successful PDF report generation."""
        # Mock PDF generator
        mock_pdf = Mock()
        mock_pdf.generate_report.return_value = None
        mock_pdf_class.return_value = mock_pdf
        
        # Mock send_file
        mock_send_file.return_value = "PDF content"
        
        response = client.post(
            '/generate_pi_report',
            data=json.dumps({'analysis_results': sample_pi_analysis}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        mock_pdf.generate_report.assert_called_once()


class TestPIAnalyzerClass:
    """Test PIAnalyzer class functionality."""
    
    @patch('apps.pi_analyzer.analyzer.Path')
    def test_pianalyzer_initialization(self, mock_path, mock_jira_client, mock_cache_manager):
        """Test PIAnalyzer initialization."""
        from apps.pi_analyzer.analyzer import PIAnalyzer
        
        # Mock config file doesn't exist
        mock_path.return_value.parent.parent.parent.return_value.__truediv__.return_value.exists.return_value = False
        
        analyzer = PIAnalyzer(mock_jira_client, mock_cache_manager)
        
        assert analyzer.jira_client == mock_jira_client
        assert analyzer.cache_manager == mock_cache_manager
        assert analyzer.base_project == "ISDOP"
    
    @patch('apps.pi_analyzer.analyzer.Path')
    def test_fetch_issues_with_cache_hit(
        self, mock_path, mock_jira_client, mock_cache_manager, sample_pi_issues
    ):
        """Test fetch issues with cache hit."""
        from apps.pi_analyzer.analyzer import PIAnalyzer
        
        # Mock config file doesn't exist
        mock_path.return_value.parent.parent.parent.return_value.__truediv__.return_value.exists.return_value = False
        
        # Mock cache hit
        mock_cache_manager.get.return_value = sample_pi_issues
        
        analyzer = PIAnalyzer(mock_jira_client, mock_cache_manager)
        result = analyzer._fetch_issues_with_cache("project = TEST", 100)
        
        assert result == sample_pi_issues
        mock_cache_manager.get.assert_called_once()
        mock_jira_client.fetch_issues.assert_not_called()
    
    @patch('apps.pi_analyzer.analyzer.Path')
    def test_fetch_issues_with_cache_miss(
        self, mock_path, mock_jira_client, mock_cache_manager, sample_pi_issues
    ):
        """Test fetch issues with cache miss."""
        from apps.pi_analyzer.analyzer import PIAnalyzer
        
        # Mock config file doesn't exist
        mock_path.return_value.parent.parent.parent.return_value.__truediv__.return_value.exists.return_value = False
        
        # Mock cache miss, then fetch from Jira
        mock_cache_manager.get.return_value = None
        mock_jira_client.fetch_issues.return_value = sample_pi_issues
        
        analyzer = PIAnalyzer(mock_jira_client, mock_cache_manager)
        result = analyzer._fetch_issues_with_cache("project = TEST", 100)
        
        assert result == sample_pi_issues
        mock_cache_manager.get.assert_called_once()
        mock_jira_client.fetch_issues.assert_called_once_with("project = TEST", 100)
        mock_cache_manager.set.assert_called_once()


class TestConfigurationLoading:
    """Test configuration loading."""
    
    @patch('apps.pi_analyzer.app.Path')
    def test_load_configuration_file_not_found(self, mock_path):
        """Test loading configuration when file doesn't exist."""
        from apps.pi_analyzer.app import load_configuration
        
        # Mock config file doesn't exist
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_path.return_value.parent.parent.parent.__truediv__.return_value = mock_file
        
        config = load_configuration()
        
        assert config['base_project'] =='ISDOP'
        assert 'completion_statuses' in config
        assert 'issue_types' in config
    
    @patch('apps.pi_analyzer.app.Path')
    @patch('builtins.open')
    def test_load_configuration_success(self, mock_open, mock_path, sample_pi_config):
        """Test successful configuration loading."""
        from apps.pi_analyzer.app import load_configuration
        
        # Mock config file exists
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_path.return_value.parent.parent.parent.__truediv__.return_value = mock_file
        
        # Mock file content
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(sample_pi_config)
        
        with patch('json.load', return_value=sample_pi_config):
            config = load_configuration()
        
        assert config['base_project'] == 'ISDOP'
        assert config['excluded_projects'] == ["E2ECD", "PPB"]


class TestFileStorage:
    """Test file storage functions."""
    
    @patch('apps.pi_analyzer.app.file_storage')
    def test_save_analysis_results(self, mock_storage, sample_pi_analysis):
        """Test saving analysis results."""
        from apps.pi_analyzer.app import save_analysis_results
        
        mock_storage.save_json.return_value = True
        
        result = save_analysis_results('test_key', sample_pi_analysis)
        
        assert result is True
        mock_storage.save_json.assert_called_once()
    
    @patch('apps.pi_analyzer.app.file_storage')
    def test_load_analysis_results(self, mock_storage, sample_pi_analysis):
        """Test loading analysis results."""
        from apps.pi_analyzer.app import load_analysis_results
        
        mock_storage.load_json.return_value = {
            'results': sample_pi_analysis,
            'timestamp': '2026-02-20T10:00:00'
        }
        
        result = load_analysis_results('test_key')
        
        assert result is not None
        assert 'results' in result
        mock_storage.load_json.assert_called_once()
    
    @patch('apps.pi_analyzer.app.file_storage')
    def test_list_saved_analyses(self, mock_storage):
        """Test listing saved analyses."""
        from apps.pi_analyzer.app import list_saved_analyses
        from pathlib import Path
        
        # Mock file list
        mock_file1 = Mock(spec=Path)
        mock_file1.name = 'analysis1.json'
        mock_file1.stem = 'analysis1'
        
        mock_storage.list_files.return_value = [mock_file1]
        mock_storage.load_json.return_value = {
            'cache_key': 'analysis1',
            'results': {
                'pi_period': {'start_date': '2026-02-01', 'end_date': '2026-02-28'},
                'summary': {'total_issues': 10}
            },
            'timestamp': '2026-02-20T10:00:00'
        }
        
        result = list_saved_analyses()
        
        assert isinstance(result, list)
        if result:  # If we got results
            assert result[0]['cache_key'] == 'analysis1'


# Integration tests
class TestIntegration:
    """Integration tests."""
    
    @patch('apps.pi_analyzer.app.save_analysis_results')
    @patch('apps.pi_analyzer.app.JiraClient')
    @patch('apps.pi_analyzer.app.PIAnalyzer')
    def test_full_workflow(
        self, mock_analyzer_class, mock_client_class, 
        mock_save, client, sample_pi_analysis
    ):
        """Test complete workflow from analysis to caching."""
        # Setup mocks
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_pi.return_value = sample_pi_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_save.return_value = True
        
        # Execute analysis
        response = client.post('/analyze_pi', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'pi_start_date': '2026-02-01',
            'pi_end_date': '2026-02-28'
        })
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify components were called correctly
        mock_client.test_connection.assert_called_once()
        mock_analyzer.analyze_pi.assert_called_once()
        mock_save.assert_called_once()
