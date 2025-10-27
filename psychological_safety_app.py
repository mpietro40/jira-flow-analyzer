"""
Jira-Based Psychological Safety Indicators Web Application
Flask-based web application for analyzing team psychological safety.
"""

from flask import Flask, render_template, request, jsonify
import logging
from datetime import datetime
import os
from urllib.parse import urlparse

from jira_client import JiraClient
from psychological_safety_analyzer import PsychologicalSafetyAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PsychologicalSafetyApp')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'psychological-safety-key')

def validate_jira_url(url):
    """Validate Jira URL format."""
    if not url or len(url) > 500:
        return False
    
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https'] and parsed.netloc
    except Exception:
        return False

@app.route('/')
def index():
    """Main page for psychological safety analysis."""
    return render_template('psychological_safety.html')

@app.route('/analyze_safety', methods=['POST'])
def analyze_safety():
    """Process psychological safety analysis request."""
    try:
        # Extract form data
        jira_url = request.form.get('jira_url', '').strip()
        access_token = request.form.get('access_token', '').strip()
        jql_query = request.form.get('jql_query', '').strip()
        week_year = request.form.get('week_year', '').strip()
        
        # Input validation
        if not all([jira_url, access_token, jql_query]):
            return jsonify({
                'error': 'Missing required fields',
                'error_type': 'ValidationError'
            }), 400
        
        if not validate_jira_url(jira_url):
            return jsonify({
                'error': 'Invalid Jira URL format',
                'error_type': 'ValidationError'
            }), 400
        
        # Initialize clients
        jira_client = JiraClient(jira_url, access_token)
        
        if not jira_client.test_connection():
            return jsonify({
                'error': 'Failed to connect to Jira. Check URL and token.',
                'error_type': 'ConnectionError'
            }), 401
        
        # Perform analysis
        analyzer = PsychologicalSafetyAnalyzer(jira_client)
        results = analyzer.analyze_weekly_safety(jql_query, week_year or None)
        
        if 'error' in results:
            return jsonify({
                'error': results['error'],
                'error_type': 'AnalysisError'
            }), 404
        
        logger.info(f"✅ Safety analysis completed for {urlparse(jira_url).netloc}")
        return jsonify({
            'success': True,
            'analysis_results': results
        })
        
    except Exception as e:
        logger.error(f"Safety analysis error: {str(e)}")
        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'error_type': 'ServerError'
        }), 500

@app.route('/get_trends', methods=['POST'])
def get_trends():
    """Get historical trends for psychological safety indicators."""
    try:
        # Extract form data
        jira_url = request.form.get('jira_url', '').strip()
        access_token = request.form.get('access_token', '').strip()
        weeks_back = int(request.form.get('weeks_back', 12))
        
        if not all([jira_url, access_token]):
            return jsonify({
                'error': 'Missing required fields',
                'error_type': 'ValidationError'
            }), 400
        
        # Initialize clients (just for validation)
        jira_client = JiraClient(jira_url, access_token)
        analyzer = PsychologicalSafetyAnalyzer(jira_client)
        
        # Get trends
        trends = analyzer.get_safety_trends(weeks_back)
        
        if 'error' in trends:
            return jsonify({
                'error': trends['error'],
                'error_type': 'DataError'
            }), 404
        
        return jsonify({
            'success': True,
            'trends': trends
        })
        
    except Exception as e:
        logger.error(f"Trends analysis error: {str(e)}")
        return jsonify({
            'error': f'Trends analysis failed: {str(e)}',
            'error_type': 'ServerError'
        }), 500

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    """Clear cached Jira data."""
    try:
        jira_url = request.form.get('jira_url', '').strip()
        access_token = request.form.get('access_token', '').strip()
        
        if not all([jira_url, access_token]):
            return jsonify({
                'error': 'Missing required fields',
                'error_type': 'ValidationError'
            }), 400
        
        jira_client = JiraClient(jira_url, access_token)
        analyzer = PsychologicalSafetyAnalyzer(jira_client)
        analyzer.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        return jsonify({
            'error': f'Failed to clear cache: {str(e)}',
            'error_type': 'ServerError'
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Psychological Safety Analyzer'
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Psychological Safety Analyzer...")
    app.run(debug=True, host='0.0.0.0', port=5300)