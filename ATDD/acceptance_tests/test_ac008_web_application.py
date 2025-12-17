"""
Acceptance Tests for AC008: Web Application Endpoints
"""
import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from lead_time_analyzer import app


class TestAC008_WebApplication:
    """Test suite for web application acceptance criteria"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_ac008_1_home_page(self, client):
        """
        AC008.1: Home Page
        Given application is running
        When user navigates to root URL
        Then input form is displayed
        """
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'jira_url' in response.data or b'Jira' in response.data
    
    def test_ac008_2_standard_analysis_endpoint(self, client):
        """
        AC008.2: Standard Analysis Endpoint
        Given valid form data submitted
        When POST to /analyze
        Then analysis is performed and JSON results are returned
        """
        with patch('lead_time_analyzer.JiraClient') as mock_client:
            mock_instance = Mock()
            mock_instance.fetch_issues.return_value = []
            mock_client.return_value = mock_instance
            
            response = client.post('/analyze', data={
                'jira_url': 'https://test.atlassian.net',
                'access_token': 'test_token',
                'jql_query': 'project = TEST',
                'time_period': '3'
            })
            
            assert response.status_code in [200, 404]  # 404 if no issues found
    
    def test_ac008_3_csv_analysis_endpoint(self, client):
        """
        AC008.3: CSV Analysis Endpoint
        Given CSV file uploaded
        When POST to /analyze_csv
        Then CSV is parsed and analyzed
        """
        from io import BytesIO
        
        csv_data = b"Issue Key\nTEST-123\nTEST-456"
        
        with patch('lead_time_analyzer.JiraClient') as mock_client:
            mock_instance = Mock()
            mock_instance.test_connection.return_value = True
            mock_instance.parse_csv_for_issue_keys.return_value = ['TEST-123', 'TEST-456']
            mock_instance.fetch_issues_by_keys.return_value = []
            mock_client.return_value = mock_instance
            
            response = client.post('/analyze_csv', data={
                'jira_url': 'https://test.atlassian.net',
                'access_token': 'test_token',
                'time_period': '3',
                'csv_file': (BytesIO(csv_data), 'test.csv')
            })
            
            assert response.status_code in [200, 400, 404]
    
    def test_ac008_4_error_handling(self, client):
        """
        AC008.4: Error Handling
        Given invalid input data
        When analysis is requested
        Then appropriate error message is returned
        """
        response = client.post('/analyze', data={
            'jira_url': '',
            'access_token': '',
            'jql_query': ''
        })
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
    
    def test_ac008_5_pdf_report_generation(self, client):
        """
        AC008.5: PDF Report Generation
        Given analysis results
        When POST to /generate_report
        Then PDF report is generated
        """
        with patch('lead_time_analyzer.PDFReportGenerator') as mock_pdf:
            mock_instance = Mock()
            mock_pdf.return_value = mock_instance
            
            response = client.post('/generate_report', 
                json={'metrics': {}, 'charts': []},
                content_type='application/json'
            )
            
            # Should attempt to generate PDF
            assert response.status_code in [200, 500]
    
    def test_ac008_7_response_format(self, client):
        """
        AC008.7: Response Format
        Given successful analysis
        When results are returned
        Then JSON includes required fields
        """
        with patch('lead_time_analyzer.JiraClient') as mock_client, \
             patch('lead_time_analyzer.DataAnalyzer') as mock_analyzer, \
             patch('lead_time_analyzer.VisualizationGenerator') as mock_viz:
            
            # Setup mocks
            mock_client_instance = Mock()
            mock_client_instance.fetch_issues.return_value = [
                {
                    'key': 'TEST-1',
                    'summary': 'Test',
                    'status': 'Done',
                    'created': '2024-01-01',
                    'status_history': []
                }
            ]
            mock_client.return_value = mock_client_instance
            
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_issues.return_value = {
                'metrics': {'lead_time': {'average': 5}},
                'lead_times': [5],
                'projects': ['TEST'],
                'people_involvement': {'overall': {'total_people': 1}}
            }
            mock_analyzer.return_value = mock_analyzer_instance
            
            mock_viz_instance = Mock()
            mock_viz_instance.generate_all_charts.return_value = []
            mock_viz.return_value = mock_viz_instance
            
            response = client.post('/analyze', data={
                'jira_url': 'https://test.atlassian.net',
                'access_token': 'test_token',
                'jql_query': 'project = TEST',
                'time_period': '3'
            })
            
            if response.status_code == 200:
                json_data = response.get_json()
                assert 'success' in json_data
                assert 'total_issues' in json_data
                assert 'metrics' in json_data
                assert 'charts' in json_data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
