"""
Test configuration for Initiative Viewer tests.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for all tests
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope='session')
def project_root_path():
    """Provide project root path to tests."""
    return project_root


@pytest.fixture
def mock_jira_response():
    """Standard mock Jira API response."""
    return {
        'startAt': 0,
        'maxResults': 50,
        'total': 1,
        'issues': [
            {
                'key': 'TEST-1',
                'fields': {
                    'summary': 'Test Issue',
                    'status': {'name': 'In Progress'},
                    'assignee': {'displayName': 'Test User'},
                    'project': {'key': 'TEST'}
                }
            }
        ]
    }
