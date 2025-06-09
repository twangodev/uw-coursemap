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
    assert response.status_code == 200    

    # Test malformed JSON
    response = client.post('/search', 
                         data='not json',
                         content_type='application/json')
    assert response.status_code == 400

def test_department_search(client):
    """Test department search functionality"""
    # Test 1: Initials should match department
    response = client.post('/search', 
                         json={'query': 'cs'},
                         content_type='application/json')
    data = response.json
    subjects = data['subjects']
    assert any('Computer Science' in subject['name'] for subject in subjects)
    
    # Test 2: Known abbreviations
    response = client.post('/search', 
                         json={'query': 'COMPSCI'},
                         content_type='application/json')
    data = response.json
    subjects = data['subjects']
    assert any('Computer Science' in subject['name'] for subject in subjects)

    # Test 3: Full department name
    response = client.post('/search', 
                         json={'query': 'Computer Science'},
                         content_type='application/json')
    data = response.json
    subjects = data['subjects']
    assert any('Computer Science' in subject['name'] for subject in subjects)

    # Test 4: Partial department name
    response = client.post('/search', 
                         json={'query': 'Comp sci'},
                         content_type='application/json')
    data = response.json
    subjects = data['subjects']
    assert any('Computer Science' in subject['name'] for subject in subjects)

def test_course_search(client):
    """Test course search functionality"""
    # Test 1: Course codes with and without spaces
    test_cases = ['cs577', 'cs 577']
    for query in test_cases:
        response = client.post('/search', 
                            json={'query': query},
                            content_type='application/json')
        data = response.json
        courses = data['courses']
        assert any('COMPSCI_577' in course['course_id'] 
                  for course in courses), f"Failed for query: {query}"
    
    # Test 2: Full text department name with number
    response = client.post('/search', 
                         json={'query': 'computer science 577'},
                         content_type='application/json')
    data = response.json
    courses = data['courses']
    assert any('COMPSCI_577' in course['course_id'] for course in courses)
    
    # Test 3: Contextual course title matches
    title_tests = [
        ('artificial intelligence', 'COMPSCI_540'),
        ('matrix methods', 'COMPSCI_ECE_ME_532')
    ]
    for query, expected in title_tests:
        response = client.post('/search', 
                            json={'query': query},
                            content_type='application/json')
        data = response.json
        courses = data['courses']
        assert any(expected in course['course_id'] 
                  for course in courses), f"Failed for query: {query}"

def test_instructor_search(client):
    """Test instructor search functionality"""
    response = client.post('/search', 
                         json={'query': 'Hobbes'},
                         content_type='application/json')
    data = response.json
    instructors = data['instructors']
    assert any('Hobbes Legault' in instructor['name'] for instructor in instructors)