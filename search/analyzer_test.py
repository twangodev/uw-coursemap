import requests
import json

def test_analyze(query: str):
    url = "http://localhost:5000/analyze"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "query": query 
    }

    response = requests.post(url, headers=headers, json=data)
    
    # Pretty print the response
    print("Query:", query)
    json = response.json()
    print("Response:", [token['token'] for token in json['tokens']])
    print()

if __name__ == "__main__":
    tests = ['COMPSCI', 'comp sci', 'COMP SCI', 'cs', 'inter-ls', 'Cs&d']
    for test in tests:
        test_analyze(test)