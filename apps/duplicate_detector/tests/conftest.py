"""
Test fixtures for Duplicate Detector application tests.
Provides mock objects and sample data for testing.
"""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def client():
    """Create Flask test client."""
    from flask import Flask
    from apps.duplicate_detector.app import blueprint

    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.register_blueprint(blueprint)
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_jira_client():
    """Create mock Jira client."""
    mock_client = Mock()
    mock_client.test_connection.return_value = True
    mock_client.fetch_issues.return_value = []
    return mock_client


@pytest.fixture
def sample_story():
    """Create sample Jira story."""
    return {
        'key': 'PROJ-123',
        'fields': {
            'summary': 'Implement user authentication system',
            'description': 'Create a robust authentication system for user login and registration',
            'issuetype': {'name': 'Story'},
            'status': {'name': 'Open'},
            'project': {
                'key': 'PROJ',
                'name': 'Sample Project'
            },
            'created': '2024-01-15T10:00:00.000+0000'
        }
    }


@pytest.fixture
def sample_duplicate_story():
    """Create sample duplicate Jira story."""
    return {
        'key': 'PROJ-456',
        'fields': {
            'summary': 'Implement authentication for users',
            'description': 'Build an authentication system for user login and signup functionality',
            'issuetype': {'name': 'Story'},
            'status': {'name': 'Open'},
            'project': {
                'key': 'PROJ',
                'name': 'Sample Project'
            },
            'created': '2024-02-20T14:00:00.000+0000'
        }
    }


@pytest.fixture
def sample_stories():
    """Create list of sample stories for duplicate detection."""
    return [
        {
            'key': 'PROJ-101',
            'fields': {
                'summary': 'Implement user authentication',
                'description': 'Create login and registration functionality',
                'issuetype': {'name': 'Story'},
                'status': {'name': 'Open'},
                'project': {'key': 'PROJ', 'name': 'Sample Project'},
                'created': '2024-01-10T10:00:00.000+0000'
            }
        },
        {
            'key': 'PROJ-102',
            'fields': {
                'summary': 'Implement authentication system',
                'description': 'Build user login and registration',
                'issuetype': {'name': 'Story'},
                'status': {'name': 'Open'},
                'project': {'key': 'PROJ', 'name': 'Sample Project'},
                'created': '2024-01-15T10:00:00.000+0000'
            }
        },
        {
            'key': 'PROJ-103',
            'fields': {
                'summary': 'Create dashboard widgets',
                'description': 'Design and implement dashboard widget system',
                'issuetype': {'name': 'Story'},
                'status': {'name': 'Open'},
                'project': {'key': 'PROJ', 'name': 'Sample Project'},
                'created': '2024-01-20T10:00:00.000+0000'
            }
        },
        {
            'key': 'PROJ-104',
            'fields': {
                'summary': 'Add dashboard components',
                'description': 'Implement widget components for dashboard',
                'issuetype': {'name': 'Story'},
                'status': {'name': 'Open'},
                'project': {'key': 'PROJ', 'name': 'Sample Project'},
                'created': '2024-01-25T10:00:00.000+0000'
            }
        }
    ]


@pytest.fixture
def sample_duplicate_analysis():
    """Create sample duplicate analysis results."""
    return {
        'total_issues': 4,
        'duplicate_count': 2,
        'duplicate_groups': [
            {
                'group_id': 1,
                'similarity_score': 0.85,
                'issues': [
                    {
                        'key': 'PROJ-101',
                        'summary': 'Implement user authentication',
                        'description': 'Create login and registration functionality',
                        'status': 'Open',
                        'created': '2024-01-10'
                    },
                    {
                        'key': 'PROJ-102',
                        'summary': 'Implement authentication system',
                        'description': 'Build user login and registration',
                        'status': 'Open',
                        'created': '2024-01-15'
                    }
                ]
            },
            {
                'group_id': 2,
                'similarity_score': 0.78,
                'issues': [
                    {
                        'key': 'PROJ-103',
                        'summary': 'Create dashboard widgets',
                        'description': 'Design and implement dashboard widget system',
                        'status': 'Open',
                        'created': '2024-01-20'
                    },
                    {
                        'key': 'PROJ-104',
                        'summary': 'Add dashboard components',
                        'description': 'Implement widget components for dashboard',
                        'status': 'Open',
                        'created': '2024-01-25'
                    }
                ]
            }
        ],
        'jira_url': 'https://test.atlassian.net',
        'jql_query': 'project = PROJ AND type = Story',
        'request_date': '2026-02-20T12:00:00',
        'analysis_timestamp': '2026-02-20T12:00:00'
    }


@pytest.fixture
def mock_duplicate_detector():
    """Create mock duplicate detector."""
    mock_detector = Mock()
    mock_detector.analyze_duplicates.return_value = {
        'total_issues': 10,
        'duplicate_count': 3,
        'duplicate_groups': []
    }
    return mock_detector


@pytest.fixture
def mock_pdf_generator():
    """Create mock PDF generator."""
    mock_generator = Mock()
    mock_generator.generate_report.return_value = None
    return mock_generator
