"""
Test fixtures for Epic Fix Version Analyzer application.
"""

import pytest
from datetime import datetime
from apps.epic_fixversion.app import app


@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_jira_client(mocker):
    """Mock Jira client."""
    mock_client = mocker.Mock()
    mock_client.test_connection.return_value = True
    mock_client.jira_url = 'https://test.atlassian.net'
    return mock_client


@pytest.fixture
def sample_initiative():
    """Sample initiative issue."""
    return {
        'key': 'INIT-100',
        'summary': 'Q1 2026 Strategic Initiative',
        'fields': {
            'issuetype': {'name': 'Initiative'},
            'status': {'name': 'In Progress'},
            'project': {'key': 'INIT'}
        }
    }


@pytest.fixture
def sample_epic():
    """Sample epic with fix version."""
    return {
        'key': 'PROJ-500',
        'summary': 'Implement new authentication system',
        'fields': {
            'issuetype': {'name': 'Epic'},
            'status': {'name': 'In Progress'},
            'project': {'key': 'PROJ'},
            'fixVersions': [
                {'name': '2026-Q1'},
                {'name': 'v2.5.0'}
            ],
            'assignee': {'displayName': 'John Doe'},
            'customfield_41340': {'value': 'High'},  # complexity
            'customfield_114641': 'Customer A',  # requesting customer
            'customfield_42640': '2026-03-01',  # target start
            'customfield_116072': 'OAuth 2.0 implementation',  # solution
            'comment': {
                'comments': [
                    {
                        'author': {'displayName': 'Dev Lead'},
                        'body': 'Platform: microservices architecture'
                    }
                ]
            }
        }
    }


@pytest.fixture
def sample_epic_no_fixversion():
    """Sample epic without fix version."""
    return {
        'key': 'PROJ-501',
        'summary': 'Refactor legacy code',
        'fields': {
            'issuetype': {'name': 'Epic'},
            'status': {'name': 'To Do'},
            'project': {'key': 'PROJ'},
            'fixVersions': [],
            'assignee': {'displayName': 'Jane Smith'}
        }
    }


@pytest.fixture
def sample_analysis_results():
    """Sample epic fix version analysis results."""
    return {
        'success': True,
        'fix_version': '2026-Q1',
        'excluded_statuses': ['Done', 'Closed'],
        'total_initiatives': 3,
        'initiatives_with_epics': 2,
        'total_epics': 8,
        'results': [
            {
                'initiative_key': 'INIT-100',
                'initiative_summary': 'Q1 2026 Strategic Initiative',
                'epic_count': 5,
                'epics': [
                    {
                        'key': 'PROJ-500',
                        'summary': 'Implement authentication',
                        'status': 'In Progress',
                        'project': 'PROJ',
                        'fix_versions': ['2026-Q1'],
                        'complexity': 'High',
                        'requesting_customer': 'Customer A',
                        'assignee': 'John Doe',
                        'target_start': '2026-03-01',
                        'solution': 'OAuth 2.0',
                        'comments': {'platform': 'Microservices', 'impacts': ''}
                    },
                    {
                        'key': 'PROJ-501',
                        'summary': 'Update database schema',
                        'status': 'In Progress',
                        'project': 'PROJ',
                        'fix_versions': ['2026-Q1'],
                        'complexity': 'Medium',
                        'requesting_customer': 'Customer B',
                        'assignee': 'Jane Smith',
                        'target_start': '2026-03-15',
                        'solution': 'PostgreSQL migration',
                        'comments': {'platform': '', 'impacts': 'Minor delay expected'}
                    }
                ]
            },
            {
                'initiative_key': 'INIT-101',
                'initiative_summary': 'Infrastructure Modernization',
                'epic_count': 3,
                'epics': [
                    {
                        'key': 'INFRA-200',
                        'summary': 'Migrate to Kubernetes',
                        'status': 'In Progress',
                        'project': 'INFRA',
                        'fix_versions': ['2026-Q1'],
                        'complexity': 'High',
                        'requesting_customer': 'Internal',
                        'assignee': 'DevOps Team',
                        'target_start': '2026-02-01',
                        'solution': 'EKS deployment',
                        'comments': {'platform': 'AWS', 'impacts': ''}
                    }
                ]
            }
        ],
        'timestamp': datetime.now().isoformat()
    }


@pytest.fixture
def mock_analyzer(mocker, sample_analysis_results):
    """Mock EpicFixVersionAnalyzer."""
    mock = mocker.Mock()
    mock.analyze.return_value = sample_analysis_results
    return mock


@pytest.fixture
def mock_pdf_generator(mocker):
    """Mock EpicFixVersionPDFGenerator."""
    import io
    mock = mocker.Mock()
    mock_buffer = io.BytesIO(b'PDF content')
    mock.generate_report.return_value = mock_buffer
    return mock


@pytest.fixture
def valid_analysis_request():
    """Valid epic fix version analysis request data."""
    return {
        'jira_url': 'https://test-company.atlassian.net',
        'access_token': 'test_token_123',
        'initiative_jql': 'project = INIT AND type = Initiative',
        'fix_version': '2026-Q1',
        'excluded_statuses': 'Done, Closed'
    }


@pytest.fixture
def valid_analysis_request_no_fixversion():
    """Valid analysis request without fix version filter."""
    return {
        'jira_url': 'https://test-company.atlassian.net',
        'access_token': 'test_token_123',
        'initiative_jql': 'project = INIT AND type = Initiative',
        'fix_version': '',  # No fix version filter
        'excluded_statuses': ''  # Use defaults
    }


@pytest.fixture
def sample_pdf_request(sample_analysis_results):
    """Sample PDF export request."""
    return {
        'analysis_data': sample_analysis_results,
        'jira_url': 'https://test-company.atlassian.net'
    }
