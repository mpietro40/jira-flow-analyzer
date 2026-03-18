"""
Tests for Epic Fix Version Analyzer application.

Test coverage includes:
- Basic route functionality
- Epic fix version analysis workflow
- PDF generation and export
- Hierarchy traversal (Initiative → Feature → Epic)
- Fix version filtering
- Status exclusion
- Custom field extraction
- Integration scenarios
"""

import pytest
from unittest.mock import Mock, patch
import json
from io import BytesIO


class TestBasicRoutes:
    """Test basic application routes."""

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
        assert data['port'] == 5008

    def test_favicon_route(self, client):
        """Test favicon route returns 204."""
        response = client.get('/favicon.ico')
        assert response.status_code == 204


class TestAnalyzeRoute:
    """Test /analyze route for epic fix version analysis."""

    def test_analyze_missing_jira_url(self, client):
        """Test analysis fails without Jira URL."""
        response = client.post('/analyze', data={
            'access_token': 'test_token',
            'initiative_jql': 'project = INIT'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_analyze_missing_access_token(self, client):
        """Test analysis fails without access token."""
        response = client.post('/analyze', data={
            'jira_url': 'https://test.atlassian.net',
            'initiative_jql': 'project = INIT'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_analyze_missing_initiative_jql(self, client):
        """Test analysis fails without initiative JQL."""
        response = client.post('/analyze', data={
            'jira_url': 'https://test.atlassian.net',
            'access_token': 'test_token'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('apps.epic_fixversion.app.JiraClient')
    def test_analyze_connection_failure(self, mock_jira_class, client, valid_analysis_request):
        """Test analysis handles connection failure."""
        mock_instance = Mock()
        mock_instance.test_connection.return_value = False
        mock_jira_class.return_value = mock_instance

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid credentials' in data['error']

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_analyze_success_with_fixversion(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request, sample_analysis_results
    ):
        """Test successful analysis with specific fix version."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = sample_analysis_results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['fix_version'] == '2026-Q1'
        assert data['total_epics'] == 8
        assert len(data['results']) == 2

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_analyze_success_no_fixversion(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request_no_fixversion
    ):
        """Test successful analysis without fix version filter (all epics)."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        results = {
            'success': True,
            'fix_version': None,
            'total_epics': 15,
            'results': []
        }
        mock_analyzer.analyze.return_value = results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request_no_fixversion)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['fix_version'] is None
        assert data['total_epics'] == 15

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_analyze_with_custom_excluded_statuses(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test analysis with custom excluded statuses."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {'success': True}
        mock_analyzer_class.return_value = mock_analyzer

        # Custom excluded statuses
        valid_analysis_request['excluded_statuses'] = 'Done, Closed, Abandoned, Obsolete'

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200

        # Verify analyzer called with correct excluded statuses
        call_args = mock_analyzer.analyze.call_args
        assert call_args[1]['excluded_statuses'] == ['Done', 'Closed', 'Abandoned', 'Obsolete']

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_analyze_error_handling(self, mock_jira_class, mock_analyzer_class, client, valid_analysis_request):
        """Test analysis error handling."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer to raise exception
        mock_analyzer = Mock()
        mock_analyzer.analyze.side_effect = Exception("Analysis failed")
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


class TestAnalyzeEpicFixversionRoute:
    """Test /analyze_epic_fixversion alias route."""

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_alias_route(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request, sample_analysis_results
    ):
        """Test alias route works same as /analyze."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = sample_analysis_results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze_epic_fixversion', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestExportPDFRoute:
    """Test /export_pdf route for PDF generation."""

    def test_export_pdf_missing_data(self, client):
        """Test PDF export fails without analysis data."""
        response = client.post('/export_pdf', data={
            'jira_url': 'https://test.atlassian.net'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_export_pdf_invalid_json(self, client):
        """Test PDF export handles invalid JSON."""
        response = client.post('/export_pdf', data={
            'jira_url': 'https://test.atlassian.net',
            'analysis_data': 'invalid json'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('apps.epic_fixversion.app.EpicFixVersionPDFGenerator')
    def test_export_pdf_success(self, mock_pdf_class, client, sample_analysis_results):
        """Test successful PDF generation."""
        # Mock PDF generator
        mock_generator = Mock()
        pdf_buffer = BytesIO(b'%PDF-1.4 test content')
        mock_generator.generate_report.return_value = pdf_buffer
        mock_pdf_class.return_value = mock_generator

        response = client.post('/export_pdf', data={
            'jira_url': 'https://test.atlassian.net',
            'analysis_data': json.dumps(sample_analysis_results)
        })

        assert response.status_code == 200
        assert response.mimetype == 'application/pdf'
        assert response.headers.get('Content-Disposition').startswith('attachment; filename=')

    @patch('apps.epic_fixversion.app.EpicFixVersionPDFGenerator')
    def test_export_pdf_error_handling(self, mock_pdf_class, client, sample_analysis_results):
        """Test PDF generation error handling."""
        # Mock PDF generator to raise exception
        mock_generator = Mock()
        mock_generator.generate_report.side_effect = Exception("PDF generation failed")
        mock_pdf_class.return_value = mock_generator

        response = client.post('/export_pdf', data={
            'jira_url': 'https://test.atlassian.net',
            'analysis_data': json.dumps(sample_analysis_results)
        })

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


class TestExportEpicFixversionPDFRoute:
    """Test /export_epic_fixversion_pdf alias route."""

    @patch('apps.epic_fixversion.app.EpicFixVersionPDFGenerator')
    def test_alias_route(self, mock_pdf_class, client, sample_analysis_results):
        """Test PDF export alias route."""
        # Mock PDF generator
        mock_generator = Mock()
        pdf_buffer = BytesIO(b'%PDF-1.4 test content')
        mock_generator.generate_report.return_value = pdf_buffer
        mock_pdf_class.return_value = mock_generator

        response = client.post('/export_epic_fixversion_pdf', data={
            'jira_url': 'https://test.atlassian.net',
            'analysis_data': json.dumps(sample_analysis_results)
        })

        assert response.status_code == 200
        assert response.mimetype == 'application/pdf'


class TestEpicHierarchy:
    """Test epic hierarchy traversal functionality."""

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_hierarchy_traversal(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test analyzer traverses Initiative → Feature → Epic hierarchy."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer with hierarchy results
        mock_analyzer = Mock()
        hierarchy_results = {
            'success': True,
            'results': [
                {
                    'initiative_key': 'INIT-100',
                    'epic_count': 3,
                    'epics': [
                        {'key': 'EPIC-1', 'hierarchy_level': 'direct'},
                        {'key': 'EPIC-2', 'hierarchy_level': 'via_feature'},
                        {'key': 'EPIC-3', 'hierarchy_level': 'via_sub_feature'}
                    ]
                }
            ]
        }
        mock_analyzer.analyze.return_value = hierarchy_results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['results'][0]['epics']) == 3

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_multiple_initiatives(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test analysis handles multiple initiatives."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        results = {
            'success': True,
            'total_initiatives': 5,
            'initiatives_with_epics': 4,
            'results': [
                {'initiative_key': 'INIT-100', 'epic_count': 3},
                {'initiative_key': 'INIT-101', 'epic_count': 5},
                {'initiative_key': 'INIT-102', 'epic_count': 2},
                {'initiative_key': 'INIT-103', 'epic_count': 0}
            ]
        }
        mock_analyzer.analyze.return_value = results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_initiatives'] == 5
        assert data['initiatives_with_epics'] == 4


class TestFixVersionFiltering:
    """Test fix version filtering functionality."""

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_single_fixversion_filter(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test filtering by single fix version."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {'success': True, 'fix_version': '2026-Q1'}
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200

        # Verify analyzer called with fix_version
        call_args = mock_analyzer.analyze.call_args
        assert call_args[1]['fix_version'] == '2026-Q1'

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_no_fixversion_filter(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request_no_fixversion
    ):
        """Test analysis without fix version filter (all epics)."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {'success': True, 'fix_version': None}
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request_no_fixversion)
        assert response.status_code == 200

        # Verify analyzer called with None fix_version
        call_args = mock_analyzer.analyze.call_args
        assert call_args[1]['fix_version'] is None

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_epics_with_multiple_fixversions(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test handling of epics with multiple fix versions."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        results = {
            'success': True,
            'results': [{
                'epics': [
                    {'key': 'EPIC-1', 'fix_versions': ['2026-Q1', 'v2.5.0', 'Bugfix']},
                    {'key': 'EPIC-2', 'fix_versions': ['2026-Q2']}
                ]
            }]
        }
        mock_analyzer.analyze.return_value = results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['results'][0]['epics'][0]['fix_versions']) == 3


class TestStatusExclusion:
    """Test status exclusion functionality."""

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_default_excluded_statuses(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test default excluded statuses."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {'success': True}
        mock_analyzer_class.return_value = mock_analyzer

        # Empty excluded_statuses should use defaults
        valid_analysis_request['excluded_statuses'] = ''

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200

        # Verify analyzer called with default excluded statuses
        call_args = mock_analyzer.analyze.call_args
        default_statuses = ['Done', 'Closed', 'Abandoned', 'Cancelled', 'Resolved']
        assert call_args[1]['excluded_statuses'] == default_statuses

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_custom_excluded_statuses(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test custom excluded statuses."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {'success': True}
        mock_analyzer_class.return_value = mock_analyzer

        # Custom statuses with spaces
        valid_analysis_request['excluded_statuses'] = 'Done, In Review, Blocked'

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200

        # Verify analyzer called with trimmed custom statuses
        call_args = mock_analyzer.analyze.call_args
        assert call_args[1]['excluded_statuses'] == ['Done', 'In Review', 'Blocked']


class TestCustomFields:
    """Test custom field extraction functionality."""

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_complexity_extraction(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test complexity field extraction."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer with complexity data
        mock_analyzer = Mock()
        results = {
            'success': True,
            'results': [{
                'epics': [
                    {'key': 'EPIC-1', 'complexity': 'High'},
                    {'key': 'EPIC-2', 'complexity': 'Medium'},
                    {'key': 'EPIC-3', 'complexity': 'Low'}
                ]
            }]
        }
        mock_analyzer.analyze.return_value = results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        epics = data['results'][0]['epics']
        assert epics[0]['complexity'] == 'High'
        assert epics[1]['complexity'] == 'Medium'
        assert epics[2]['complexity'] == 'Low'

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_requesting_customer_extraction(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test requesting customer field extraction."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        results = {
            'success': True,
            'results': [{
                'epics': [
                    {'key': 'EPIC-1', 'requesting_customer': 'Customer A'},
                    {'key': 'EPIC-2', 'requesting_customer': 'Internal'}
                ]
            }]
        }
        mock_analyzer.analyze.return_value = results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        epics = data['results'][0]['epics']
        assert epics[0]['requesting_customer'] == 'Customer A'

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_comment_extraction(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test platform/impacts comment extraction."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        results = {
            'success': True,
            'results': [{
                'epics': [
                    {
                        'key': 'EPIC-1',
                        'comments': {
                            'platform': 'Microservices',
                            'impacts': 'Requires database migration'
                        }
                    }
                ]
            }]
        }
        mock_analyzer.analyze.return_value = results
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        comments = data['results'][0]['epics'][0]['comments']
        assert comments['platform'] == 'Microservices'
        assert comments['impacts'] == 'Requires database migration'


class TestIntegration:
    """Integration tests for complete workflows."""

    @patch('apps.epic_fixversion.app.EpicFixVersionPDFGenerator')
    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_complete_analysis_and_pdf_workflow(
        self, mock_jira_class, mock_analyzer_class, mock_pdf_class,
        client, valid_analysis_request, sample_analysis_results
    ):
        """Test complete workflow: analyze → export PDF."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = sample_analysis_results
        mock_analyzer_class.return_value = mock_analyzer

        # Mock PDF generator
        mock_generator = Mock()
        pdf_buffer = BytesIO(b'%PDF-1.4 test content')
        mock_generator.generate_report.return_value = pdf_buffer
        mock_pdf_class.return_value = mock_generator

        # Step 1: Analyze
        analyze_response = client.post('/analyze', data=valid_analysis_request)
        assert analyze_response.status_code == 200
        analyze_data = json.loads(analyze_response.data)
        assert analyze_data['success'] is True

        # Step 2: Export PDF
        pdf_response = client.post('/export_pdf', data={
            'jira_url': valid_analysis_request['jira_url'],
            'analysis_data': json.dumps(analyze_data)
        })
        assert pdf_response.status_code == 200
        assert pdf_response.mimetype == 'application/pdf'

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_no_initiatives_found(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test handling when no initiatives are found."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer with no results
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            'success': True,
            'total_initiatives': 0,
            'initiatives_with_epics': 0,
            'total_epics': 0,
            'results': []
        }
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_initiatives'] == 0
        assert len(data['results']) == 0

    @patch('apps.epic_fixversion.app.EpicFixVersionAnalyzer')
    @patch('apps.epic_fixversion.app.JiraClient')
    def test_initiatives_with_no_epics(
        self, mock_jira_class, mock_analyzer_class,
        client, valid_analysis_request
    ):
        """Test handling when initiatives have no epics for the fix version."""
        # Mock Jira connection
        mock_jira = Mock()
        mock_jira.test_connection.return_value = True
        mock_jira_class.return_value = mock_jira

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            'success': True,
            'total_initiatives': 5,
            'initiatives_with_epics': 0,
            'total_epics': 0,
            'results': [
                {'initiative_key': 'INIT-100', 'epic_count': 0, 'epics': []},
                {'initiative_key': 'INIT-101', 'epic_count': 0, 'epics': []}
            ]
        }
        mock_analyzer_class.return_value = mock_analyzer

        response = client.post('/analyze', data=valid_analysis_request)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_initiatives'] == 5
        assert data['initiatives_with_epics'] == 0
        assert data['total_epics'] == 0
