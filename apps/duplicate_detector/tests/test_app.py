"""
Unit tests for Duplicate Detector application.
Tests Flask routes, duplicate detection, PDF generation, and integration.
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
        assert data['application'] == 'duplicate_detector'
        assert data['version'] == '2.0.0'
        assert data['port'] == 5006
    
    def test_favicon_not_found(self, client):
        """Test favicon route."""
        response = client.get('/favicon.ico')
        assert response.status_code in [204, 404]


class TestAnalyzeDuplicatesRoute:
    """Test duplicate analysis route."""
    
    def test_analyze_duplicates_missing_credentials(self, client):
        """Test duplicate analysis with missing credentials."""
        response = client.post('/analyze_duplicates', data={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_duplicates_missing_jql(self, client):
        """Test duplicate analysis with missing JQL query."""
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': ''  # Empty JQL
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'JQL query is required' in data['error']
    
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_analyze_duplicates_jira_connection_failure(
        self, mock_detector_class, mock_client_class, client
    ):
        """Test duplicate analysis with Jira connection failure."""
        # Mock Jira client that fails connection
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Failed to connect to Jira' in data['error']
    
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_analyze_duplicates_success(
        self, mock_detector_class, mock_client_class,
        client, sample_duplicate_analysis
    ):
        """Test successful duplicate analysis."""
        # Mock Jira client
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock Duplicate Detector
        mock_detector = Mock()
        mock_detector.analyze_duplicates.return_value = {
            'total_issues': 4,
            'duplicate_count': 2,
            'duplicate_groups': sample_duplicate_analysis['duplicate_groups']
        }
        mock_detector_class.return_value = mock_detector
        
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ AND type = Story'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'analysis_results' in data
        
        # Verify results structure
        results = data['analysis_results']
        assert results['total_issues'] == 4
        assert results['duplicate_count'] == 2
        assert 'jira_url' in results
        assert 'jql_query' in results
        assert 'request_date' in results
        
        # Verify detector was called
        mock_detector.analyze_duplicates.assert_called_once_with('project = PROJ AND type = Story')
    
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_analyze_duplicates_no_issues_found(
        self, mock_detector_class, mock_client_class, client
    ):
        """Test duplicate analysis when no issues are found."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_detector = Mock()
        mock_detector.analyze_duplicates.return_value = {
            'error': 'No issues found matching the query'
        }
        mock_detector_class.return_value = mock_detector
        
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = EMPTY'
        })
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestGeneratePDFRoute:
    """Test PDF generation route."""
    
    def test_generate_pdf_no_data(self, client):
        """Test PDF generation with no data."""
        response = client.post(
            '/generate_duplicate_report',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'No analysis data provided' in data['error']
    
    @patch('apps.duplicate_detector.app.DuplicatePDFReportGenerator')
    @patch('apps.duplicate_detector.app.send_file')
    @patch('apps.duplicate_detector.app.tempfile.NamedTemporaryFile')
    def test_generate_pdf_success(
        self, mock_tempfile, mock_send_file, mock_pdf_class,
        client, sample_duplicate_analysis
    ):
        """Test successful PDF generation."""
        # Mock temporary file
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.pdf'
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp
        
        # Mock PDF generator
        mock_pdf = Mock()
        mock_pdf.generate_report.return_value = None
        mock_pdf_class.return_value = mock_pdf
        
        # Mock send_file
        mock_send_file.return_value = "PDF content"
        
        response = client.post(
            '/generate_duplicate_report',
            data=json.dumps(sample_duplicate_analysis),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        mock_pdf.generate_report.assert_called_once()
        mock_send_file.assert_called_once()


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_full_workflow_analysis_to_results(
        self, mock_detector_class, mock_client_class,
        client, sample_duplicate_analysis
    ):
        """Test complete workflow from analysis to results."""
        # Setup mocks
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_detector = Mock()
        mock_detector.analyze_duplicates.return_value = {
            'total_issues': 4,
            'duplicate_count': 2,
            'duplicate_groups': sample_duplicate_analysis['duplicate_groups']
        }
        mock_detector_class.return_value = mock_detector
        
        # Execute analysis
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ'
        })
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'analysis_results' in data
        
        # Verify results structure
        results = data['analysis_results']
        assert results['total_issues'] == 4
        assert results['duplicate_count'] == 2
        assert len(results['duplicate_groups']) == 2
        
        # Verify all components were called
        mock_client.test_connection.assert_called_once()
        mock_detector.analyze_duplicates.assert_called_once()
    
    @patch('apps.duplicate_detector.app.DuplicatePDFReportGenerator')
    @patch('apps.duplicate_detector.app.send_file')
    @patch('apps.duplicate_detector.app.tempfile.NamedTemporaryFile')
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_full_workflow_analysis_to_pdf(
        self, mock_detector_class, mock_client_class,
        mock_tempfile, mock_send_file, mock_pdf_class,
        client, sample_duplicate_analysis
    ):
        """Test complete workflow from analysis to PDF export."""
        # Setup analysis mocks
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_detector = Mock()
        mock_detector.analyze_duplicates.return_value = {
            'total_issues': 4,
            'duplicate_count': 2,
            'duplicate_groups': sample_duplicate_analysis['duplicate_groups']
        }
        mock_detector_class.return_value = mock_detector
        
        # Setup PDF mocks
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.pdf'
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp
        
        mock_pdf = Mock()
        mock_pdf.generate_report.return_value = None
        mock_pdf_class.return_value = mock_pdf
        mock_send_file.return_value = "PDF content"
        
        # Execute analysis
        analysis_response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ'
        })
        
        assert analysis_response.status_code == 200
        analysis_data = json.loads(analysis_response.data)
        
        # Export to PDF
        pdf_response = client.post(
            '/generate_duplicate_report',
            data=json.dumps(analysis_data['analysis_results']),
            content_type='application/json'
        )
        
        assert pdf_response.status_code == 200
        mock_pdf.generate_report.assert_called_once()


class TestDuplicateDetection:
    """Test duplicate detection logic."""
    
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_duplicate_detection_with_high_similarity(
        self, mock_detector_class, mock_client_class, client
    ):
        """Test duplicate detection with high similarity score."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_detector = Mock()
        mock_detector.analyze_duplicates.return_value = {
            'total_issues': 2,
            'duplicate_count': 1,
            'duplicate_groups': [
                {
                    'group_id': 1,
                    'similarity_score': 0.95,  # Very high similarity
                    'issues': [
                        {'key': 'PROJ-1', 'summary': 'Test story'},
                        {'key': 'PROJ-2', 'summary': 'Test story duplicate'}
                    ]
                }
            ]
        }
        mock_detector_class.return_value = mock_detector
        
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        results = data['analysis_results']
        assert results['duplicate_groups'][0]['similarity_score'] == 0.95
    
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_duplicate_detection_no_duplicates(
        self, mock_detector_class, mock_client_class, client
    ):
        """Test duplicate detection when no duplicates are found."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_detector = Mock()
        mock_detector.analyze_duplicates.return_value = {
            'total_issues': 10,
            'duplicate_count': 0,
            'duplicate_groups': []
        }
        mock_detector_class.return_value = mock_detector
        
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = PROJ'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        results = data['analysis_results']
        assert results['duplicate_count'] == 0
        assert len(results['duplicate_groups']) == 0


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('apps.duplicate_detector.app.JiraClient')
    @patch('apps.duplicate_detector.app.DuplicateDetector')
    def test_detector_exception_handling(
        self, mock_detector_class, mock_client_class, client
    ):
        """Test handling of detector exceptions."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        mock_detector = Mock()
        mock_detector.analyze_duplicates.side_effect = Exception("Detection failed")
        mock_detector_class.return_value = mock_detector
        
        response = client.post('/analyze_duplicates', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token',
            'jql_query': 'project = TEST'
        })
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('apps.duplicate_detector.app.DuplicatePDFReportGenerator')
    @patch('apps.duplicate_detector.app.tempfile.NamedTemporaryFile')
    def test_pdf_generation_exception_handling(
        self, mock_tempfile, mock_pdf_class, client, sample_duplicate_analysis
    ):
        """Test handling of PDF generation exceptions."""
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.pdf'
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp
        
        mock_pdf = Mock()
        mock_pdf.generate_report.side_effect = Exception("PDF generation error")
        mock_pdf_class.return_value = mock_pdf
        
        response = client.post(
            '/generate_duplicate_report',
            data=json.dumps(sample_duplicate_analysis),
            content_type='application/json'
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
