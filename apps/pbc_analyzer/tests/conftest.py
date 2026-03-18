"""
Test fixtures for PBC Analyzer application tests.
Provides mock objects and sample data for testing.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime


@pytest.fixture
def client():
    """Create Flask test client."""
    from flask import Flask
    from apps.pbc_analyzer.app import blueprint

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
def sample_pbc_issue():
    """Create sample Jira issue for PBC analysis."""
    return {
        'key': 'PROJ-123',
        'fields': {
            'summary': 'Sample Story',
            'issuetype': {'name': 'Story'},
            'status': {'name': 'Done'},
            'project': {
                'key': 'PROJ',
                'name': 'Sample Project'
            },
            'created': '2024-08-01T10:00:00.000+0000',
            'resolutiondate': '2024-08-15T15:30:00.000+0000',
            'customfield_10016': 3.0,  # Story points
            'parent': None,
            'subtasks': []
        }
    }


@pytest.fixture
def sample_business_initiative():
    """Create sample Business Initiative issue."""
    return {
        'key': 'BIZ-1',
        'fields': {
            'summary': 'Strategic Initiative',
            'issuetype': {'name': 'Business Initiative'},
            'status': {'name': 'In Progress'},
            'project': {
                'key': 'BIZ',
                'name': 'Business Initiatives'
            },
            'created': '2024-01-01T10:00:00.000+0000',
            'resolutiondate': None,
            'subtasks': [
                {'key': 'FEAT-1', 'fields': {'summary': 'Feature 1'}},
                {'key': 'FEAT-2', 'fields': {'summary': 'Feature 2'}}
            ]
        }
    }


@pytest.fixture
def sample_pbc_issues():
    """Create list of sample issues for PBC analysis."""
    return [
        {
            'key': 'PROJ-101',
            'fields': {
                'summary': 'Story 1',
                'issuetype': {'name': 'Story'},
                'status': {'name': 'Done'},
                'project': {'key': 'PROJ', 'name': 'Sample Project'},
                'created': '2024-08-01T10:00:00.000+0000',
                'resolutiondate': '2024-08-05T15:30:00.000+0000',  # 4.5 days lead time
                'customfield_10016': 5.0,
                'parent': None,
                'subtasks': []
            }
        },
        {
            'key': 'PROJ-102',
            'fields': {
                'summary': 'Story 2',
                'issuetype': {'name': 'Story'},
                'status': {'name': 'Done'},
                'project': {'key': 'PROJ', 'name': 'Sample Project'},
                'created': '2024-08-05T10:00:00.000+0000',
                'resolutiondate': '2024-08-12T15:30:00.000+0000',  # 7.5 days lead time
                'customfield_10016': 8.0,
                'parent': None,
                'subtasks': []
            }
        },
        {
            'key': 'PROJ-103',
            'fields': {
                'summary': 'Bug Fix',
                'issuetype': {'name': 'Bug'},
                'status': {'name': 'Done'},
                'project': {'key': 'PROJ', 'name': 'Sample Project'},
                'created': '2024-08-10T10:00:00.000+0000',
                'resolutiondate': '2024-08-13T15:30:00.000+0000',  # 3.5 days lead time
                'customfield_10016': 2.0,
                'parent': None,
                'subtasks': []
            }
        }
    ]


@pytest.fixture
def sample_pbc_analysis():
    """Create sample PBC analysis results."""
    return {
        'analysis_id': 'pbc_20260220_120000',
        'timestamp': '2026-02-20T12:00:00',
        'start_date': '2024-08-01',
        'jql_query': 'project = PROJ AND type in (Story, Bug)',
        'summary': {
            'total_projects': 1,
            'total_issues': 15,
            'date_range': {
                'start': '2024-08-01',
                'end': '2024-08-31'
            },
            'overall_stats': {
                'mean_lead_time': 5.2,
                'median_lead_time': 4.5,
                'std_dev': 2.1,
                'upper_control_limit': 11.5,
                'lower_control_limit': 0.0
            }
        },
        'projects': {
            'PROJ': {
                'project_key': 'PROJ',
                'project_name': 'Sample Project',
                'issues_analyzed': 15,
                'lead_time_stats': {
                    'mean': 5.2,
                    'median': 4.5,
                    'std_dev': 2.1,
                    'min': 1.5,
                    'max': 10.3,
                    'ucl': 11.5,
                    'lcl': 0.0
                },
                'pbc_data': [
                    {'issue_key': 'PROJ-101', 'lead_time_days': 4.5, 'resolution_date': '2024-08-05'},
                    {'issue_key': 'PROJ-102', 'lead_time_days': 7.5, 'resolution_date': '2024-08-12'},
                    {'issue_key': 'PROJ-103', 'lead_time_days': 3.5, 'resolution_date': '2024-08-13'}
                ],
                'special_causes': [
                    {
                        'issue_key': 'PROJ-115',
                        'lead_time_days': 15.2,
                        'reason': 'Above upper control limit',
                        'deviation': 3.7
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_pbc_analyzer():
    """Create mock PBC analyzer."""
    mock_analyzer = Mock()
    mock_analyzer.analyze.return_value = {
        'analysis_id': 'pbc_test',
        'timestamp': datetime.now().isoformat(),
        'start_date': '2024-08-01',
        'summary': {
            'total_projects': 1,
            'total_issues': 10
        },
        'projects': {}
    }
    return mock_analyzer


@pytest.fixture
def mock_cache_manager():
    """Create mock cache manager."""
    mock_cache = Mock()
    mock_cache.get.return_value = None  # No cached data by default
    mock_cache.set.return_value = True
    return mock_cache


@pytest.fixture
def mock_file_storage():
    """Create mock file storage."""
    mock_storage = Mock()
    mock_storage.save_json.return_value = True
    mock_storage.load_json.return_value = None
    mock_storage.list_files.return_value = []
    return mock_storage
