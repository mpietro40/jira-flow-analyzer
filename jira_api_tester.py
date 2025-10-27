"""
Simple Jira API Tester Web App
Test any Jira API call with custom parameters
"""
from flask import Flask, render_template, request, jsonify
import requests
import json
# Removed HTTPBasicAuth import as we're using Bearer token

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('api_tester.html')

@app.route('/test_api', methods=['POST'])
def test_api():
    try:
        data = request.json
        
        # Get parameters from request
        base_url = data.get('base_url', '').rstrip('/')
        endpoint = data.get('endpoint', '')
        token = data.get('token', '')
        params = data.get('params', {})
        
        # Build full URL
        if endpoint.startswith('/'):
            full_url = base_url + endpoint
        else:
            full_url = f"{base_url}/{endpoint}"
        
        # Make API call using Bearer token (same as JiraClient)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'JiraApiTester/1.0'
        }
        response = requests.get(full_url, params=params, headers=headers, timeout=30)
        
        # Return results
        result = {
            'url': full_url,
            'params': params,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'response_text': response.text[:5000]  # Limit response size
        }
        
        # Try to parse JSON
        try:
            result['response_json'] = response.json()
        except:
            result['response_json'] = None
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)