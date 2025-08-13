"""
Tests for Flask application
"""

import pytest
import sys
import os
import json

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test main page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Jira Analytics Dashboard' in response.data

def test_analyze_missing_data(client):
    """Test analysis with missing required fields."""
    response = client.post('/analyze', data={})
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing required fields' in data['error']