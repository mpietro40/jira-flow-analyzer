"""
Unit tests for Sprint Analyzer application.
Tests Flask routes, SprintAnalyzer class, and integration.
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
        assert data['application'] == 'sprint_analyzer'
        assert data['version'] == '2.0.0'
    
    def test_favicon_not_found(self, client):
        """Test favicon route when file doesn't exist."""
        response = client.get('/favicon.ico')
        # Should return 204 No Content or 404
        assert response.status_code in [204, 404]


class TestAnalyzeSprintRoute:
    """Test sprint analysis route."""
    
    def test_analyze_sprint_missing_credentials(self, client):
        """Test sprint analysis with missing credentials."""
        response = client.post('/analyze_sprint', data={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_sprint_missing_sprint_name(self, client):
        """Test sprint analysis with missing sprint name."""
        response = client.post('/analyze_sprint', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'sprint_name': ''  # Empty sprint name
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Sprint name is required' in data['error']
    
    @patch('apps.sprint_analyzer.app.JiraClient')
    @patch('apps.sprint_analyzer.app.SprintAnalyzer')
    def test_analyze_sprint_jira_connection_failure(
        self, mock_analyzer_class, mock_client_class, client
    ):
        """Test sprint analysis with Jira connection failure."""
        # Mock Jira client that fails connection
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        response = client.post('/analyze_sprint', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'sprint_name': 'Sprint 42'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Failed to connect to Jira' in data['error']
    
    @patch('apps.sprint_analyzer.app.JiraClient')
    @patch('apps.sprint_analyzer.app.SprintAnalyzer')
    def test_analyze_sprint_success(
        self, mock_analyzer_class, mock_client_class, 
        client, sample_sprint_analysis
    ):
        """Test successful sprint analysis."""
        # Mock Jira client
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock Sprint Analyzer
        mock_analyzer = Mock()
        mock_analyzer.configure_capacity.return_value = None
        mock_analyzer.configure_completion_statuses.return_value = None
        mock_analyzer.configure_excluded_types.return_value = None
        mock_analyzer.analyze_sprint.return_value = sample_sprint_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        response = client.post('/analyze_sprint', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'sprint_name': 'Sprint 42',
            'history_months': '6',
            'team_size': '8',
            'sprint_days': '10',
            'hours_per_day': '8',
            'completion_statuses': 'Done,Closed',
            'excluded_types': 'Epic'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'results' in data
        
        # Verify analyzer was configured correctl
        mock_analyzer.configure_capacity.assert_called_once_with(8, 10, 8)
        mock_analyzer.configure_completion_statuses.assert_called_once_with('Done,Closed')
        mock_analyzer.configure_excluded_types.assert_called_once_with('Epic')
        mock_analyzer.analyze_sprint.assert_called_once_with('Sprint 42', 6)
    
    @patch('apps.sprint_analyzer.app.JiraClient')
    @patch('apps.sprint_analyzer.app.SprintAnalyzer')
    def test_analyze_sprint_with_default_params(
        self, mock_analyzer_class, mock_client_class, 
        client, sample_sprint_analysis
    ):
        """Test sprint analysis with default parameters."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_analyzer = Mock()
        mock_analyzer.configure_capacity.return_value = None
        mock_analyzer.configure_completion_statuses.return_value = None
        mock_analyzer.configure_excluded_types.return_value = None
        mock_analyzer.analyze_sprint.return_value = sample_sprint_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Only provide required fields
        response = client.post('/analyze_sprint', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'sprint_name': 'Sprint 42'
        })
        
        assert response.status_code == 200
        # Verify defaults were used
        mock_analyzer.configure_capacity.assert_called_once_with(8, 10, 8)  # Defaults


class TestExportPDFRoute:
    """Test PDF export route."""
    
    def test_export_pdf_no_data(self, client):
        """Test PDF export with no data."""
        response = client.post(
            '/export_pdf',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'No analysis data provided' in data['error']
    
    @patch('apps.sprint_analyzer.app.SprintPDFReportGenerator')
    @patch('apps.sprint_analyzer.app.send_file')
    def test_export_pdf_success(
        self, mock_send_file, mock_pdf_class, 
        client, sample_sprint_analysis
    ):
        """Test successful PDF export."""
        # Mock PDF generator
        mock_pdf = Mock()
        mock_pdf.generate_report.return_value = None
        mock_pdf_class.return_value = mock_pdf
        
        # Mock send_file
        mock_send_file.return_value = "PDF content"
        
        response = client.post(
            '/export_pdf',
            data=json.dumps({'results': sample_sprint_analysis}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        mock_pdf.generate_report.assert_called_once()
        mock_send_file.assert_called_once()


class TestSprintAnalyzerConfiguration:
    """Test SprintAnalyzer configuration methods."""
    
    @patch('apps.sprint_analyzer.analyzer.SimpleSprintRetriever')
    @patch('apps.sprint_analyzer.analyzer.DataAnalyzer')
    def test_configure_capacity(
        self, mock_data_analyzer, mock_retriever, mock_jira_client
    ):
        """Test capacity configuration."""
        from apps.sprint_analyzer.analyzer import SprintAnalyzer
        
        analyzer = SprintAnalyzer(mock_jira_client)
        analyzer.configure_capacity(10, 12, 7)
        
        assert analyzer.team_size == 10
        assert analyzer.sprint_days == 12
        assert analyzer.hours_per_day == 7
    
    @patch('apps.sprint_analyzer.analyzer.SimpleSprintRetriever')
    @patch('apps.sprint_analyzer.analyzer.DataAnalyzer')
    def test_configure_completion_statuses(
        self, mock_data_analyzer, mock_retriever, mock_jira_client
    ):
        """Test completion statuses configuration."""
        from apps.sprint_analyzer.analyzer import SprintAnalyzer
        
        analyzer = SprintAnalyzer(mock_jira_client)
        analyzer.configure_completion_statuses('Done, Closed, Resolved ')
        
        assert 'Done' in analyzer.completion_statuses
        assert 'Closed' in analyzer.completion_statuses
        assert 'Resolved' in analyzer.completion_statuses
        assert len(analyzer.completion_statuses) == 3
    
    @patch('apps.sprint_analyzer.analyzer.SimpleSprintRetriever')
    @patch('apps.sprint_analyzer.analyzer.DataAnalyzer')
    def test_configure_excluded_types(
        self, mock_data_analyzer, mock_retriever, mock_jira_client
    ):
        """Test excluded types configuration."""
        from apps.sprint_analyzer.analyzer import SprintAnalyzer
        
        analyzer = SprintAnalyzer(mock_jira_client)
        analyzer.configure_excluded_types('Epic, Initiative ')
        
        assert 'Epic' in analyzer.excluded_types
        assert 'Initiative' in analyzer.excluded_types
        assert len(analyzer.excluded_types) == 2


class TestIntegration:
    """Integration tests."""
    
    @patch('apps.sprint_analyzer.app.JiraClient')
    @patch('apps.sprint_analyzer.app.SprintAnalyzer')
    def test_full_workflow_analysis_to_results(
        self, mock_analyzer_class, mock_client_class, 
        client, sample_sprint_analysis
    ):
        """Test complete workflow from analysis to results."""
        # Setup mocks
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_analyzer = Mock()
        mock_analyzer.configure_capacity.return_value = None
        mock_analyzer.configure_completion_statuses.return_value = None
        mock_analyzer.configure_excluded_types.return_value = None
        mock_analyzer.analyze_sprint.return_value = sample_sprint_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Execute analysis
        response = client.post('/analyze_sprint', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'sprint_name': 'Sprint 42',
            'history_months': '3',
            'team_size': '6',
            'sprint_days': '10',
            'hours_per_day': '8'
        })
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'results' in data
        
        # Verify results contain metadata
        results = data['results']
        assert 'request_params' in results
        assert results['request_params']['sprint_name'] == 'Sprint 42'
        assert results['request_params']['team_size'] == 6
        
        # Verify all components were called
        mock_client.test_connection.assert_called_once()
        mock_analyzer.configure_capacity.assert_called_once()
        mock_analyzer.analyze_sprint.assert_called_once()
    
    @patch('apps.sprint_analyzer.app.SprintPDFReportGenerator')
    @patch('apps.sprint_analyzer.app.send_file')
    @patch('apps.sprint_analyzer.app.JiraClient')
    @patch('apps.sprint_analyzer.app.SprintAnalyzer')
    def test_full_workflow_analysis_to_pdf(
        self, mock_analyzer_class, mock_client_class,
        mock_send_file, mock_pdf_class,
        client, sample_sprint_analysis
    ):
        """Test complete workflow from analysis to PDF export."""
        # Setup analysis mocks
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_analyzer = Mock()
        mock_analyzer.configure_capacity.return_value = None
        mock_analyzer.configure_completion_statuses.return_value = None
        mock_analyzer.configure_excluded_types.return_value = None
        mock_analyzer.analyze_sprint.return_value = sample_sprint_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Setup PDF mocks
        mock_pdf = Mock()
        mock_pdf.generate_report.return_value = None
        mock_pdf_class.return_value = mock_pdf
        mock_send_file.return_value = "PDF content"
        
        # Execute analysis
        analysis_response = client.post('/analyze_sprint', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'sprint_name': 'Sprint 42'
        })
        
        assert analysis_response.status_code == 200
        analysis_data = json.loads(analysis_response.data)
        
        # Export to PDF
        pdf_response = client.post(
            '/export_pdf',
            data=json.dumps({'results': analysis_data['results']}),
            content_type='application/json'
        )
        
        assert pdf_response.status_code == 200
        mock_pdf.generate_report.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('apps.sprint_analyzer.app.JiraClient')
    @patch('apps.sprint_analyzer.app.SprintAnalyzer')
    def test_analyzer_exception_handling(
        self, mock_analyzer_class, mock_client_class, client
    ):
        """Test handling of analyzer exceptions."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_analyzer = Mock()
        mock_analyzer.configure_capacity.return_value = None
        mock_analyzer.configure_completion_statuses.return_value = None
        mock_analyzer.configure_excluded_types.return_value = None
        mock_analyzer.analyze_sprint.side_effect = Exception("Analysis failed")
        mock_analyzer_class.return_value = mock_analyzer
        
        response = client.post('/analyze_sprint', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'sprint_name': 'Sprint 42'
        })
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
