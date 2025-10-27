"""
Jira Status Changer Web App
Changes status of issues from JQL query to "Waiting" then "PROD DEPLOYED"
"""
from flask import Flask, render_template, request, jsonify
import requests
import json
import time
import threading
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('jira_status_changer.log')
    ]
)
logger = logging.getLogger('JiraStatusChanger')

app = Flask(__name__)

# Global variable to store operation results
operation_results = {}

@app.route('/')
def index():
    return render_template('status_changer.html')

@app.route('/change_statuses', methods=['POST'])
def change_statuses():
    try:
        data = request.json
        
        # Get parameters from request
        base_url = data.get('base_url', '').rstrip('/')
        token = data.get('token', '')
        jql_query = data.get('jql_query', '')
        
        logger.info(f"🚀 Starting status change operation")
        logger.info(f"📍 Jira URL: {base_url}")
        logger.info(f"🔍 JQL Query: {jql_query}")
        
        if not all([base_url, token, jql_query]):
            logger.error("❌ Missing required fields")
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Test Jira connection first
        logger.info("🔗 Testing Jira connection...")
        if not test_jira_connection(base_url, token):
            logger.error("❌ Jira connection failed")
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 400
        
        logger.info("✅ Jira connection successful")
        
        # Start the status change operation in background
        operation_id = str(int(time.time()))
        operation_results[operation_id] = {
            'status': 'started',
            'total_issues': 0,
            'processed': 0,
            'results': [],
            'errors': [],
            'logs': []
        }
        
        logger.info(f"🆔 Operation ID: {operation_id}")
        
        # Start background thread
        thread = threading.Thread(
            target=process_status_changes,
            args=(operation_id, base_url, token, jql_query)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'operation_id': operation_id,
            'message': 'Status change operation started'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in change_statuses: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/operation_status/<operation_id>')
def operation_status(operation_id):
    """Check the status of a running operation"""
    result = operation_results.get(operation_id, {'error': 'Operation not found'})
    return jsonify(result)

def test_jira_connection(base_url, token):
    """Test connection to Jira before starting the operation"""
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'JiraStatusChanger/1.0'
        }
        
        # Test with a simple API call
        test_url = f"{base_url}/rest/api/2/myself"
        logger.info(f"🔗 Testing connection to: {test_url}")
        
        response = requests.get(test_url, headers=headers, timeout=10)
        
        logger.info(f"📡 Connection test response: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"👤 Connected as: {user_data.get('displayName', 'Unknown')} ({user_data.get('emailAddress', 'No email')})")
            return True
        else:
            logger.error(f"❌ Connection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection test failed: {str(e)}")
        return False

def add_operation_log(operation_id, message, level='info'):
    """Add a log message to the operation results"""
    if operation_id in operation_results:
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        operation_results[operation_id]['logs'].append(log_entry)
        
        # Also log to file
        if level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)
        else:
            logger.info(message)

def process_status_changes(operation_id, base_url, token, jql_query):
    """Process status changes for all issues matching the JQL query"""
    try:
        add_operation_log(operation_id, f"🚀 Starting status change operation")
        add_operation_log(operation_id, f"📍 Jira URL: {base_url}")
        add_operation_log(operation_id, f"🔍 JQL Query: {jql_query}")
        
        operation_results[operation_id]['status'] = 'searching_issues'
        
        # Headers for API calls
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'JiraStatusChanger/1.0'
        }
        
        # Search for issues using JQL
        search_url = f"{base_url}/rest/api/2/search"
        search_params = {
            'jql': jql_query,
            'fields': 'key,summary,status',
            'maxResults': 1000
        }
        
        add_operation_log(operation_id, f"🔍 Executing JQL search...")
        add_operation_log(operation_id, f"📡 Request URL: {search_url}")
        add_operation_log(operation_id, f"📋 Parameters: {json.dumps(search_params, indent=2)}")
        
        response = requests.get(search_url, params=search_params, headers=headers, timeout=30)
        
        add_operation_log(operation_id, f"📡 Search response status: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"Search failed: {response.status_code} - {response.text}"
            add_operation_log(operation_id, error_msg, 'error')
            operation_results[operation_id]['status'] = 'error'
            operation_results[operation_id]['errors'].append(error_msg)
            return
        
        search_data = response.json()
        add_operation_log(operation_id, f"📊 Search response: Found {search_data.get('total', 0)} total issues")
        
        issues = search_data.get('issues', [])
        total_issues = len(issues)
        
        operation_results[operation_id]['total_issues'] = total_issues
        operation_results[operation_id]['status'] = 'processing'
        
        add_operation_log(operation_id, f"📋 Processing {total_issues} issues")
        
        if total_issues == 0:
            add_operation_log(operation_id, "ℹ️ No issues found matching the JQL query")
            operation_results[operation_id]['status'] = 'completed'
            operation_results[operation_id]['results'].append("No issues found matching the JQL query")
            return
        
        # Log found issues
        for issue in issues:
            issue_key = issue['key']
            issue_summary = issue['fields']['summary']
            current_status = issue['fields']['status']['name']
            add_operation_log(operation_id, f"📝 Found: {issue_key} - {current_status} - {issue_summary[:50]}...")
        
        # Process each issue
        for i, issue in enumerate(issues):
            issue_key = issue['key']
            issue_summary = issue['fields']['summary']
            current_status = issue['fields']['status']['name']
            
            add_operation_log(operation_id, f"🔄 Processing {issue_key} ({i+1}/{total_issues})")
            add_operation_log(operation_id, f"📋 Current status: {current_status}")
            
            try:
                # Get available transitions for this issue
                transitions_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
                add_operation_log(operation_id, f"🔍 Getting transitions for {issue_key}")
                add_operation_log(operation_id, f"📡 Request URL: {transitions_url}")
                
                transitions_response = requests.get(transitions_url, headers=headers, timeout=30)
                add_operation_log(operation_id, f"📡 Transitions response: {transitions_response.status_code}")
                
                if transitions_response.status_code != 200:
                    error_msg = f"{issue_key}: Failed to get transitions - {transitions_response.text}"
                    add_operation_log(operation_id, error_msg, 'error')
                    operation_results[operation_id]['errors'].append(error_msg)
                    continue
                
                transitions_data = transitions_response.json()
                transitions = transitions_data.get('transitions', [])
                
                # Log available transitions
                transition_names = [t['to']['name'] for t in transitions]
                add_operation_log(operation_id, f"🔄 Available transitions for {issue_key}: {', '.join(transition_names)}")
                
                # Find transition to "Waiting"
                waiting_transition = None
                for transition in transitions:
                    if transition['to']['name'].upper() in ['WAITING', 'WAIT']:
                        waiting_transition = transition
                        break
                
                if not waiting_transition:
                    error_msg = f"{issue_key}: No 'Waiting' transition available from current status '{current_status}'"
                    add_operation_log(operation_id, error_msg, 'error')
                    operation_results[operation_id]['errors'].append(error_msg)
                    continue
                
                add_operation_log(operation_id, f"✅ Found 'Waiting' transition: {waiting_transition['to']['name']} (ID: {waiting_transition['id']})")
                
                # Transition to "Waiting"
                transition_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
                transition_data = {
                    'transition': {
                        'id': waiting_transition['id']
                    }
                }
                
                add_operation_log(operation_id, f"🔄 Transitioning {issue_key} to 'Waiting'")
                add_operation_log(operation_id, f"📡 Request URL: {transition_url}")
                add_operation_log(operation_id, f"📋 Request data: {json.dumps(transition_data)}")
                
                transition_response = requests.post(
                    transition_url, 
                    json=transition_data, 
                    headers=headers, 
                    timeout=30
                )
                
                add_operation_log(operation_id, f"📡 Transition to Waiting response: {transition_response.status_code}")
                
                if transition_response.status_code not in [200, 204]:
                    error_msg = f"{issue_key}: Failed to transition to Waiting - {transition_response.text}"
                    add_operation_log(operation_id, error_msg, 'error')
                    operation_results[operation_id]['errors'].append(error_msg)
                    continue
                
                success_msg = f"{issue_key}: {current_status} → Waiting"
                add_operation_log(operation_id, f"✅ {success_msg}")
                operation_results[operation_id]['results'].append(success_msg)
                
                # Wait 3 seconds
                add_operation_log(operation_id, f"⏳ Waiting 3 seconds before next transition...")
                time.sleep(3)
                
                # Get updated transitions (from Waiting status)
                add_operation_log(operation_id, f"🔍 Getting transitions from 'Waiting' status for {issue_key}")
                transitions_response = requests.get(transitions_url, headers=headers, timeout=30)
                
                add_operation_log(operation_id, f"📡 Updated transitions response: {transitions_response.status_code}")
                
                if transitions_response.status_code != 200:
                    error_msg = f"{issue_key}: Failed to get transitions from Waiting status"
                    add_operation_log(operation_id, error_msg, 'error')
                    operation_results[operation_id]['errors'].append(error_msg)
                    continue
                
                transitions_data = transitions_response.json()
                transitions = transitions_data.get('transitions', [])
                
                # Log available transitions from Waiting
                transition_names = [t['to']['name'] for t in transitions]
                add_operation_log(operation_id, f"🔄 Available transitions from Waiting: {', '.join(transition_names)}")
                
                # Find transition to "PROD DEPLOYED"
                deployed_transition = None
                for transition in transitions:
                    transition_name = transition['to']['name'].upper()
                    if ('PROD DEPLOYED' in transition_name or 
                        'PRODUCTION DEPLOYED' in transition_name or 
                        'DEPLOYED' in transition_name):
                        deployed_transition = transition
                        break
                
                if not deployed_transition:
                    error_msg = f"{issue_key}: No 'PROD DEPLOYED' transition available from Waiting status"
                    add_operation_log(operation_id, error_msg, 'error')
                    operation_results[operation_id]['errors'].append(error_msg)
                    continue
                
                add_operation_log(operation_id, f"✅ Found deployment transition: {deployed_transition['to']['name']} (ID: {deployed_transition['id']})")
                
                # Transition to "PROD DEPLOYED"
                transition_data = {
                    'transition': {
                        'id': deployed_transition['id']
                    }
                }
                
                add_operation_log(operation_id, f"🚀 Transitioning {issue_key} to '{deployed_transition['to']['name']}'")
                add_operation_log(operation_id, f"📡 Request URL: {transition_url}")
                add_operation_log(operation_id, f"📋 Request data: {json.dumps(transition_data)}")
                
                transition_response = requests.post(
                    transition_url, 
                    json=transition_data, 
                    headers=headers, 
                    timeout=30
                )
                
                add_operation_log(operation_id, f"📡 Transition to deployment response: {transition_response.status_code}")
                
                if transition_response.status_code not in [200, 204]:
                    error_msg = f"{issue_key}: Failed to transition to PROD DEPLOYED - {transition_response.text}"
                    add_operation_log(operation_id, error_msg, 'error')
                    operation_results[operation_id]['errors'].append(error_msg)
                    continue
                
                success_msg = f"{issue_key}: Waiting → {deployed_transition['to']['name']}"
                add_operation_log(operation_id, f"✅ {success_msg}")
                operation_results[operation_id]['results'].append(success_msg)
                
                operation_results[operation_id]['processed'] = i + 1
                add_operation_log(operation_id, f"✅ Completed {issue_key} ({i+1}/{total_issues})")
                
            except Exception as e:
                error_msg = f"{issue_key}: Error processing - {str(e)}"
                add_operation_log(operation_id, error_msg, 'error')
                operation_results[operation_id]['errors'].append(error_msg)
        
        operation_results[operation_id]['status'] = 'completed'
        operation_results[operation_id]['completed_at'] = datetime.now().isoformat()
        add_operation_log(operation_id, f"🎉 Operation completed! Processed {operation_results[operation_id]['processed']}/{total_issues} issues")
        
    except Exception as e:
        error_msg = f"General error: {str(e)}"
        add_operation_log(operation_id, error_msg, 'error')
        operation_results[operation_id]['status'] = 'error'
        operation_results[operation_id]['errors'].append(error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5002)