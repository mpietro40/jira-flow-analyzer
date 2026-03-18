"""
Test configuration and fixtures for Sprint Analyzer tests.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock


@pytest.fixture
def client():
    """Create Flask test client."""
    from flask import Flask
    from apps.sprint_analyzer.app import blueprint

    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.register_blueprint(blueprint)

    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_jira_client():
    """Create mock Jira client."""
    client = Mock()
    client.test_connection.return_value = True
    client.fetch_issues.return_value = []
    return client


@pytest.fixture
def sample_sprint_details():
    """Sample sprint details."""
    return {
        'id': 123,
        'name': 'Sprint 42',
        'state': 'active',
        'startDate': '2026-02-10T09:00:00.000Z',
        'endDate': '2026-02-21T17:00:00.000Z',
        'completeDate': None,
        'originBoardId': 456
    }


@pytest.fixture
def sample_sprint_issues():
    """Sample sprint issues."""
    return [
        {
            'key': 'PROJ-100',
            'fields': {
                'summary': 'Implement feature A',
                'issuetype': {'name': 'Story'},
                'status': {'name': 'Done'},
                'timeoriginalestimate': 28800,  # 8 hours
                'timespent': 25200,  # 7 hours
                'project': {'key': 'PROJ'},
                'sprint': {'name': 'Sprint 42'}
            }
        },
        {
            'key': 'PROJ-101',
            'fields': {
                'summary': 'Fix bug B',
                'issuetype': {'name': 'Bug'},
                'status': {'name': 'Done'},
                'timeoriginalestimate': 14400,  # 4 hours
                'timespent': 18000,  # 5 hours
                'project': {'key': 'PROJ'},
                'sprint': {'name': 'Sprint 42'}
            }
        },
        {
            'key': 'PROJ-102',
            'fields': {
                'summary': 'Task C',
                'issuetype': {'name': 'Task'},
                'status': {'name': 'In Progress'},
                'timeoriginalestimate': 7200,  # 2 hours
                'timespent': None,
                'project': {'key': 'PROJ'},
                'sprint': {'name': 'Sprint 42'}
            }
        }
    ]


@pytest.fixture
def sample_historical_sprints():
    """Sample historical sprint data."""
    return [
        {
            'id': 120,
            'name': 'Sprint 39',
            'state': 'closed',
            'velocity_hours': 180.0,
            'completed_issues': 15
        },
        {
            'id': 121,
            'name': 'Sprint 40',
            'state': 'closed',
            'velocity_hours': 200.0,
            'completed_issues': 18
        },
        {
            'id': 122,
            'name': 'Sprint 41',
            'state': 'closed',
            'velocity_hours': 190.0,
            'completed_issues': 16
        }
    ]


@pytest.fixture
def sample_sprint_analysis():
    """Sample complete sprint analysis results."""
    return {
        'sprint_details': {
            'id': 123,
            'name': 'Sprint 42',
            'state': 'active',
            'start_date': '2026-02-10',
            'end_date': '2026-02-21',
            'duration_days': 11
        },
        'capacity': {
            'team_size': 8,
            'sprint_days': 10,
            'hours_per_day': 8,
            'total_capacity_hours': 640,
            'available_capacity_days': 80
        },
        'workload': {
            'total_planned_hours': 150.0,
            'total_planned_days': 18.75,
            'completed_hours': 132.0,
            'remaining_hours': 18.0,
            'completion_percentage': 88.0
        },
        'forecast': {
           'feasibility': 'feasible',
            'confidence': 'high',
            'risk_level': 'low',
            'recommendation': 'Sprint load within capacity'
        },
        'historical_context': {
            'sprints_analyzed': 3,
            'avg_velocity_hours': 190.0,
            'velocity_trend': 'stable'
        },
        'issues': []
    }


@pytest.fixture
def mock_sprint_analyzer():
    """Create mock Sprint Analyzer."""
    analyzer = Mock()
    analyzer.configure_capacity.return_value = None
    analyzer.configure_completion_statuses.return_value = None
    analyzer.configure_excluded_types.return_value = None
    analyzer.analyze_sprint.return_value = {}
    return analyzer


@pytest.fixture
def mock_pdf_generator():
    """Create mock PDF generator."""
    generator = Mock()
    generator.generate_report.return_value = None
    return generator
