import json
import pytest
from app import app, es

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_search_endpoint(client):
    """Test the /search endpoint with various queries"""
    # Test basic search
    response = client.post('/search', 
                         json={'query': 'Computer Science'},
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check response structure
    assert 'courses' in data
    assert 'instructors' in data
    assert 'subjects' in data
    
    # Test empty query
    response = client.post('/search', 
                         json={'query': ''},
                         content_type='application/json')
    assert response.status_code == 200
    
    # Test missing query parameter
    response = client.post('/search', 
                         json={},
                         content_type='application/json')
    assert response.status_code == 400
    
    # Test malformed JSON
    response = client.post('/search', 
                         data='not json',
                         content_type='application/json')
    assert response.status_code == 400

def test_search_results_quality(client):
    """Test the quality of search results"""
    # Test course search
    response = client.post('/search',
                         json={'query': 'COMP SCI 300'},
                         content_type='application/json')
    data = json.loads(response.data)
    assert len(data['courses']) > 0
    
    # Test instructor search
    response = client.post('/search',
                         json={'query': 'Computer Science Professor'},
                         content_type='application/json')
    data = json.loads(response.data)
    assert len(data['instructors']) > 0
    
    # Test subject search
    response = client.post('/search',
                         json={'query': 'Computer Science'},
                         content_type='application/json')
    data = json.loads(response.data)
    assert len(data['subjects']) > 0