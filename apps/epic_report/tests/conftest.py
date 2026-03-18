"""Test configuration for Epic Report tests."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def client():
    """Create test client."""
    from flask import Flask
    from apps.epic_report.app import blueprint
    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.register_blueprint(blueprint)
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def sample_issues():
    """Sample Jira issues for testing."""
    return [
        {
            'key': 'PROJ-1',
            'fields': {
                'summary': 'Test Issue 1',
                'customfield_10014': 'EPIC-1',
                'status': {'name': 'In Progress'}
            }
        },
        {
            'key': 'PROJ-2',
            'fields': {
                'summary': 'Test Issue 2',
                'customfield_10014': 'EPIC-1',
                'status': {'name': 'Done'}
            }
        },
        {
            'key': 'PROJ-3',
            'fields': {
                'summary': 'Test Issue 3',
                'customfield_10014': 'EPIC-2',
                'status': {'name': 'To Do'}
            }
        },
        {
            'key': 'PROJ-4',
            'fields': {
                'summary': 'Test Issue 4 - No Epic',
                'status': {'name': 'Open'}
            }
        }
    ]


@pytest.fixture
def sample_epic_data():
    """Sample epic data."""
    return {
        'key': 'EPIC-1',
        'fields': {
            'summary': 'Test Epic 1',
            'status': {'name': 'In Progress'},
            'assignee': {'displayName': 'John Doe'},
            'project': {'key': 'PROJ'}
        }
    }
