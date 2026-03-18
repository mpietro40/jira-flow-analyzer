"""
Test configuration and fixtures for PI Analyzer tests.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock


@pytest.fixture
def client():
    """Create Flask test client."""
    from flask import Flask
    from apps.pi_analyzer.app import blueprint

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
def sample_pi_config():
    """Sample PI configuration."""
    return {
        "base_project": "ISDOP",
        "excluded_projects": ["E2ECD", "PPB"],
        "completion_statuses": ["Done", "Closed"],
        "in_progress_statuses": ["In Progress", "Doing"],
        "issue_types": ["Story", "Bug", "Task"]
    }


@pytest.fixture
def sample_initiative():
    """Sample business initiative issue."""
    return {
        "key": "ISDOP-1000",
        "fields": {
            "summary": "Test Business Initiative",
            "issuetype": {"name": "Business Initiative"},
            "project": {"key": "ISDOP"}
        }
    }


@pytest.fixture
def sample_pi_issues():
    """Sample PI period issues."""
    return [
        {
            "key": "PROJ-100",
            "fields": {
                "summary": "Completed Story",
                "issuetype": {"name": "Story"},
                "project": {"key": "PROJ1"},
                "status": {"name": "Done"},
                "resolution": {"name": "Done"},
                "resolutiondate": "2026-02-15T10:00:00.000Z",
                "timeoriginalestimate": 28800  # 8 hours in seconds
            }
        },
        {
            "key": "PROJ-101",
            "fields": {
                "summary": "Completed Bug",
                "issuetype": {"name": "Bug"},
                "project": {"key": "PROJ1"},
                "status": {"name": "Closed"},
                "resolution": {"name": "Fixed"},
                "resolutiondate": "2026-02-16T14:00:00.000Z",
                "timeoriginalestimate": None
            }
        },
        {
            "key": "PROJ-102",
            "fields": {
                "summary": "Completed Task",
                "issuetype": {"name": "Task"},
                "project": {"key": "PROJ2"},
                "status": {"name": "Done"},
                "resolution": {"name": "Done"},
                "resolutiondate": "2026-02-18T09:00:00.000Z",
                "timeoriginalestimate": 14400  # 4 hours
            }
        }
    ]


@pytest.fixture
def sample_pi_analysis():
    """Sample PI analysis results."""
    return {
        "pi_period": {
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "duration_days": 27
        },
        "analyzed_projects": ["PROJ1", "PROJ2"],
        "base_project": "ISDOP",
        "metrics": {
            "total_issues": 3,
            "by_type": {
                "Story": {
                    "count": 1,
                    "total_estimate_hours": 8.0,
                    "estimated_count": 1,
                    "unestimated_count": 0
                },
                "Bug": {
                    "count": 1,
                    "total_estimate_hours": 0.0,
                    "estimated_count": 0,
                    "unestimated_count": 1
                },
                "Task": {
                    "count": 1,
                    "total_estimate_hours": 4.0,
                    "estimated_count": 1,
                    "unestimated_count": 0
                }
            },
            "by_project": {
                "PROJ1": {"count": 2, "total_estimate_hours": 8.0},
                "PROJ2": {"count": 1, "total_estimate_hours": 4.0}
            },
            "summary": {
                "total_estimate_hours": 12.0,
                "overall_estimated_count": 2,
                "overall_unestimated_count": 1,
                "overall_unestimated_percentage": 33.33
            }
        },
        "has_flow_metrics": False
    }


@pytest.fixture
def mock_cache_manager():
    """Create mock cache manager."""
    cache = Mock()
    cache.get.return_value = None
    cache.set.return_value = None
    return cache


@pytest.fixture
def mock_file_storage():
    """Create mock file storage."""
    storage = Mock()
    storage.save_json.return_value = True
    storage.load_json.return_value = None
    storage.list_files.return_value = []
    return storage
