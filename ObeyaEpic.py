"""
Obeya Epic Analysis Web Application
A Flask-based web application for analyzing Jira Epics and their associated work

Author: Pietro Agile Coach
Purpose: Analyze Epic metrics and estimates for program management insights
"""

import matplotlib.pyplot as plt
import io

from flask import Flask, render_template, request, jsonify, send_file
import logging
from datetime import datetime, timedelta
import os
import tempfile
import base64
from io import BytesIO
import re
import time
import json
from urllib.parse import urlparse
from functools import wraps

from jira_client import JiraClient
from data_analyzer import DataAnalyzer
from visualization import VisualizationGenerator
from epic_pdf_generator import PDFReportGenerator
from reportlab.lib.units import inch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ObeyaEpic')

# Security configurations
MAX_JQL_LENGTH = 2000
MAX_RESULTS_LIMIT = 5000
RATE_LIMIT_REQUESTS = 10  # requests per minute
RATE_LIMIT_WINDOW = 60   # seconds

# Rate limiting storage
rate_limit_storage = {}

def validate_jira_url(url):
    """Validate Jira URL format and security."""
    if not url or len(url) > 500:
        return False
    
    try:
        parsed = urlparse(url)
        if not parsed.scheme in ['http', 'https']:
            return False
        if not parsed.netloc:
            return False
        # Prevent localhost/internal network access in production
        if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            logger.warning(f"🚨 Blocked localhost access attempt: {url}")
            return False
        return True
    except Exception:
        return False

def sanitize_jql(jql_query):
    """Sanitize JQL query to prevent injection attacks."""
    if not jql_query or len(jql_query) > MAX_JQL_LENGTH:
        raise ValueError("JQL query too long or empty")
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'\b(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER)\b',
        r'[;\x00-\x1f\x7f-\x9f]',  # Control characters
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',
        r'data:',
        r'vbscript:'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, jql_query, re.IGNORECASE):
            raise ValueError(f"Potentially dangerous JQL pattern detected")
    
    return jql_query.strip()

def rate_limit(f):
    """Rate limiting decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        current_time = time.time()
        
        # Clean old entries
        rate_limit_storage[client_ip] = [
            timestamp for timestamp in rate_limit_storage.get(client_ip, [])
            if current_time - timestamp < RATE_LIMIT_WINDOW
        ]
        
        # Check rate limit
        if len(rate_limit_storage.get(client_ip, [])) >= RATE_LIMIT_REQUESTS:
            logger.warning(f"🚨 Rate limit exceeded for IP: {client_ip}")
            return jsonify({
                'error': 'Rate limit exceeded',
                'error_type': 'RateLimitError',
                'error_details': {
                    'suggestion': f'Please wait before making another request. Limit: {RATE_LIMIT_REQUESTS} requests per minute'
                }
            }), 429
        
        # Add current request
        if client_ip not in rate_limit_storage:
            rate_limit_storage[client_ip] = []
        rate_limit_storage[client_ip].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

class EpicAnalyzer:
    """Analyzes Epics and their associated work items."""
    
    def __init__(self, jira_client):
        """Initialize with a JiraClient instance."""
        self.jira_client = jira_client
    
    def analyze_epics(self, epics):
        """
        Analyze epics and their child items.
        
        Args:
            epics: List of Epic issues from Jira
            
        Returns:
            List of dictionaries containing epic analysis
        """
        epic_analysis = []
        
        for epic in epics:
            # Get all linked issues for the epic
            linked_issues = self.jira_client.get_epic_children(epic['key'])
            
            # Debug: Log raw linked issues
            # logger.info(f"📋 Epic {epic['key']} has {len(linked_issues)} linked issues")
            
            # Calculate estimates from raw epic data
            epic_fields = epic.get('fields', {})
            epic_original = epic_fields.get('timeoriginalestimate', 0) or 0
            epic_remaining = epic_fields.get('timeestimate', 0) or 0
            
            # Debug logging for epic estimates
            # logger.info(f"🔍 Epic {epic['key']}: original={epic_original}, remaining={epic_remaining}")
            
            # Add estimates from linked issues
            linked_original = 0
            linked_remaining = 0
            
            for issue in linked_issues:
                issue_fields = issue.get('fields', {})
                orig_est = issue_fields.get('timeoriginalestimate', 0) or 0
                rem_est = issue_fields.get('timeestimate', 0) or 0
                
                # Debug logging for child estimates
                if orig_est > 0 or rem_est > 0:
                    logger.info(f"  📋 Child {issue.get('key', 'Unknown')}: original={orig_est}, remaining={rem_est}")
                
                linked_original += orig_est
                linked_remaining += rem_est
            
            total_original = epic_original + linked_original
            total_remaining = epic_remaining + linked_remaining
            
            epic_data = {
                'key': epic['key'],
                'summary': epic['summary'],
                'status': epic['status'],
                'original_estimate': total_original / 3600,  # Convert to hours
                'remaining_estimate': total_remaining / 3600,  # Convert to hours
                'progress': ((total_original - total_remaining) / total_original * 100) if total_original > 0 else 0,
                'num_children': len(linked_issues),
                'jira_epic_has_zero_estimates': (epic_original == 0 and epic_remaining == 0),  # Flag for update logic
                'children': [
                    {
                        'key': issue.get('key', ''),
                        'summary': issue.get('fields', {}).get('summary', ''),
                        'status': issue.get('fields', {}).get('status', {}).get('name', ''),
                        'original_estimate': (issue.get('fields', {}).get('timeoriginalestimate', 0) or 0) / 3600,
                        'remaining_estimate': (issue.get('fields', {}).get('timeestimate', 0) or 0) / 3600
                    }
                    for issue in linked_issues
                ]
            }
            epic_analysis.append(epic_data)
        
        return epic_analysis

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; img-src 'self' data:; font-src 'self' cdnjs.cloudflare.com"
    return response

@app.route('/')
def index():
    """Main page with input form for Jira connection details."""
    return render_template('index_epic.html')

@app.route('/analyze_epics', methods=['POST'])
@rate_limit
def analyze_epics():
    """
    Process Epic analysis request.
    
    Returns:
        JSON response with analysis results
    """
    try:
        # Extract and validate form data
        jira_url = request.form.get('jira_url', '').strip()
        access_token = request.form.get('access_token', '').strip()
        jql_query = request.form.get('jql_query', '').strip()
        
        # Input validation
        if not all([jira_url, access_token, jql_query]):
            return jsonify({
                'error': 'Missing required fields',
                'error_type': 'ValidationError',
                'error_details': {'suggestion': 'Please provide Jira URL, access token, and JQL query'}
            }), 400
        
        # Validate Jira URL
        if not validate_jira_url(jira_url):
            return jsonify({
                'error': 'Invalid Jira URL format',
                'error_type': 'ValidationError',
                'error_details': {'suggestion': 'Please provide a valid HTTPS Jira URL'}
            }), 400
        
        # Validate access token
        if len(access_token) < 10 or len(access_token) > 500:
            return jsonify({
                'error': 'Invalid access token format',
                'error_type': 'ValidationError',
                'error_details': {'suggestion': 'Access token appears to be invalid'}
            }), 400
        
        # Sanitize JQL query
        try:
            jql_query = sanitize_jql(jql_query)
        except ValueError as e:
            return jsonify({
                'error': f'Invalid JQL query: {str(e)}',
                'error_type': 'ValidationError',
                'error_details': {'suggestion': 'Please check your JQL syntax and avoid dangerous patterns'}
            }), 400
        
        # Initialize Jira client
        jira_client = JiraClient(jira_url, access_token)
        
        # Test connection first
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and access token.'}), 401
        
        # Get epics with result limit
        epics = jira_client.fetch_issues(jql_query, max_results=MAX_RESULTS_LIMIT)
        if not epics:
            return jsonify({
                'error': 'No epics found with the given query',
                'error_type': 'NoDataError',
                'error_details': {'suggestion': 'Please check your JQL query and permissions'}
            }), 404
        
        # Log successful analysis
        logger.info(f"✅ Analysis completed: {len(epics)} epics processed for {urlparse(jira_url).netloc}")
        
        # Analyze epics
        epic_analyzer = EpicAnalyzer(jira_client)
        epic_analysis = epic_analyzer.analyze_epics(epics)
        
        # Generate visualizations
        viz_gen = VisualizationGenerator()
        
        # Generate charts
        viz_gen = VisualizationGenerator()
        
        # Generate pie chart for epic size distribution
        epic_pie_chart = viz_gen.create_pie_chart(
            epic_analysis,
            'Epic Size Distribution'
        )
        
        # Generate estimate comparison charts for non-zero epics (split every 50 epics)
        filtered_epics = [epic for epic in epic_analysis if epic['original_estimate'] > 0 or epic['remaining_estimate'] > 0]
        estimate_charts = []
        
        if filtered_epics:
            # Split epics into chunks of 50
            chunk_size = 50
            for i in range(0, len(filtered_epics), chunk_size):
                chunk = filtered_epics[i:i + chunk_size]
                epic_names = [epic['key'] for epic in chunk]
                original_estimates = [epic['original_estimate'] for epic in chunk]
                remaining_estimates = [epic['remaining_estimate'] for epic in chunk]
                
                chart_title = f'Epic Progress Comparison ({i+1}-{min(i+chunk_size, len(filtered_epics))})'
                estimate_chart = viz_gen.create_bar_chart(
                    epic_names,
                    [original_estimates, remaining_estimates],
                    chart_title,
                    'Hours',
                    ['Original Estimate', 'Remaining Estimate']
                )
                estimate_charts.append(estimate_chart)
        else:
            # Create an empty chart if no epics with estimates
            plt.figure(figsize=(12, 8))
            plt.text(0.5, 0.5, "No epics with estimates found", ha='center', va='center')
            plt.axis('off')
            estimate_chart = io.BytesIO()
            plt.savefig(estimate_chart, format='png')
            estimate_chart.seek(0)
            plt.close()
            estimate_charts.append(estimate_chart)
        
        # Convert charts to base64 for embedding
        estimate_charts_b64 = [base64.b64encode(chart.getvalue()).decode('utf-8') for chart in estimate_charts]
        epic_pie_chart_b64 = base64.b64encode(epic_pie_chart.getvalue()).decode('utf-8')
        
        # Prepare response data
        response_data = {
            'success': True,
            'epic_analysis': epic_analysis,
            'visualizations': {
                'estimate_charts': estimate_charts_b64,
                'epic_pie_chart': epic_pie_chart_b64
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        error_type = type(e).__name__
        status_code = 400  # Default to 400 for client errors
        
        if isinstance(e, (AttributeError, ValueError, TypeError)):
            # Client-side errors (invalid data format or missing fields)
            status_code = 400
        elif isinstance(e, ConnectionError):
            # Connection issues
            status_code = 503
        elif isinstance(e, TimeoutError):
            # Timeout issues
            status_code = 504
        elif isinstance(e, PermissionError):
            # Authorization issues
            status_code = 403
        elif isinstance(e, (KeyError, IndexError)):
            # Data structure issues
            status_code = 422
        else:
            # Unknown server errors
            status_code = 500
        
        error_details = {
            'error': str(e),
            'error_type': error_type,
            'error_details': {
                'location': 'epic_analysis',
                'suggestion': 'Please check input data format and try again'
            }
        }
        
        logger.error(f"Error in epic analysis: {error_type} - {str(e)}", exc_info=True)
        
        return jsonify(error_details), status_code

@app.route('/export_pdf', methods=['POST'])
@rate_limit
def export_pdf():
    """
    Export the epic analysis results as a PDF report.
    
    Returns:
        PDF file for download
    """
    try:
        data = request.get_json()
        epic_analysis = data.get('epic_analysis', [])
        visualizations = data.get('visualizations', {})
        jira_url = data.get('jira_url', '')
        
        # Create PDF generator
        pdf_gen = PDFReportGenerator(jira_url)
        
        # Add title and timestamp
        pdf_gen.add_title("Epic Analysis Report")
        pdf_gen.add_timestamp()
        
        # Add visualizations
        if visualizations.get('epic_pie_chart'):
            pie_chart_data = base64.b64decode(visualizations['epic_pie_chart'])
            pdf_gen.add_image(io.BytesIO(pie_chart_data), caption="Epic Size Distribution", height=5*inch)
            
        if visualizations.get('estimate_charts'):
            pdf_gen.add_heading("Epic Progress Comparison")
            for i, chart_b64 in enumerate(visualizations['estimate_charts']):
                chart_data = base64.b64decode(chart_b64)
                pdf_gen.add_image(io.BytesIO(chart_data), caption="")
        
        # Filter out unestimated epics for PDF
        estimated_epics = [epic for epic in epic_analysis if 
                          epic['original_estimate'] > 0 or 
                          epic['remaining_estimate'] > 0 or 
                          epic['num_children'] > 0]
        
        unestimated_count = len(epic_analysis) - len(estimated_epics)
        
        # Add summary with unestimated count
        pdf_gen.add_heading("Analysis Summary")
        summary_data = [
            ['Total Epics Analyzed:', str(len(epic_analysis))],
            ['Epics with Estimates/Children:', str(len(estimated_epics))],
            ['Epics without Estimates or Children:', str(unestimated_count)]
        ]
        
        from reportlab.platypus import Table, TableStyle, Spacer
        from reportlab.lib import colors
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        pdf_gen.elements.append(summary_table)
        
        pdf_gen.elements.append(Spacer(1, 0.2*inch))
        
        # Add epic details only for estimated epics (continuous table)
        from reportlab.platypus import PageBreak
        pdf_gen.elements.append(PageBreak())
        pdf_gen.add_heading("Epic Details (Estimated Only)")
        
        # Add all epics continuously without pagination
        for epic in estimated_epics:
            pdf_gen.add_epic_details(epic)
        
        # Generate and return PDF
        pdf_buffer = pdf_gen.generate_pdf()
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'epic_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        error_type = type(e).__name__
        
        error_response = {
            'error': str(e),
            'error_type': error_type,
            'error_details': {
                'location': 'pdf_generation',
                'suggestion': 'Please check if the data is complete and properly formatted'
            }
        }
        
        logger.error(f"Error in PDF generation: {error_type} - {str(e)}", exc_info=True)
        return jsonify(error_response), 422  # Unprocessable Entity

@app.route('/export_csv', methods=['POST'])
@rate_limit
def export_csv():
    """
    Export epic estimates as CSV for updating Jira.
    
    Returns:
        CSV file with epics that need estimate updates
    """
    try:
        data = request.get_json()
        epic_analysis = data.get('epic_analysis', [])
        
        # Filter epics with 0 estimates but have children with estimates
        epics_to_update = []
        for epic in epic_analysis:
            if (epic['original_estimate'] == 0 and epic['remaining_estimate'] == 0 and 
                epic['num_children'] > 0 and len(epic['children']) > 0):
                
                # Calculate totals from children
                child_original_total = sum(child['original_estimate'] for child in epic['children'])
                child_remaining_total = sum(child['remaining_estimate'] for child in epic['children'])
                
                if child_original_total > 0 or child_remaining_total > 0:
                    epics_to_update.append({
                        'jira_id': epic['key'],
                        'original_estimate_hours': child_original_total,
                        'remaining_estimate_hours': child_remaining_total
                    })
        
        # Create CSV content
        csv_content = "Jira ID,Original Estimate (hours),Remaining Estimate (hours)\n"
        for epic in epics_to_update:
            csv_content += f"{epic['jira_id']},{epic['original_estimate_hours']:.2f},{epic['remaining_estimate_hours']:.2f}\n"
        
        # Create response
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=epic_estimates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        error_type = type(e).__name__
        
        error_response = {
            'error': str(e),
            'error_type': error_type,
            'error_details': {
                'location': 'csv_generation',
                'suggestion': 'Please check if the data is complete and properly formatted'
            }
        }
        
        logger.error(f"Error in CSV generation: {error_type} - {str(e)}", exc_info=True)
        return jsonify(error_response), 422  # Unprocessable Entity

@app.route('/update_estimates', methods=['POST'])
@rate_limit
def update_estimates():
    """
    Update epic estimates directly in Jira via API.
    
    Returns:
        JSON response with update results
    """
    try:
        data = request.get_json()
        jira_url = data.get('jira_url')
        access_token = data.get('access_token')
        epic_analysis = data.get('epic_analysis', [])
        
        if not jira_url or not access_token:
            return jsonify({
                'success': False,
                'error_type': 'Update Error',
                'error': 'Missing Jira URL or access token'
            })
        
        # Initialize Jira client for updates
        jira_client = JiraClient(jira_url, access_token)
        
        # Filter epics that need updates with detailed logging
        epics_to_update = []
        logger.info(f"🔍 Analyzing {len(epic_analysis)} epics for estimate updates...")
        
        for epic in epic_analysis:
            epic_key = epic['key']
            epic_orig = epic['original_estimate']
            epic_rem = epic['remaining_estimate']
            num_children = epic['num_children']
            children_count = len(epic['children'])
            jira_has_zero = epic.get('jira_epic_has_zero_estimates', False)
            
            logger.info(f"📋 Epic {epic_key}: display={epic_orig}h/{epic_rem}h, jira_zero={jira_has_zero}, children={num_children}/{children_count}")
            
            # Check if epic has zero estimates in Jira (not calculated display values)
            if not jira_has_zero:
                logger.info(f"  ❌ Skipped {epic_key}: Epic already has estimates in Jira")
                continue
                
            if num_children == 0 or children_count == 0:
                logger.info(f"  ❌ Skipped {epic_key}: No children (num_children={num_children}, children_count={children_count})")
                continue
            
            # Calculate child totals
            child_original_total = sum(child['original_estimate'] for child in epic['children'])
            child_remaining_total = sum(child['remaining_estimate'] for child in epic['children'])
            
            logger.info(f"  📊 {epic_key} children totals: orig={child_original_total}h, rem={child_remaining_total}h")
            
            # Log each child's estimates
            for child in epic['children']:
                logger.info(f"    🔸 {child['key']}: {child['original_estimate']}h / {child['remaining_estimate']}h")
            
            if child_original_total > 0 or child_remaining_total > 0:
                logger.info(f"  ✅ {epic_key} qualifies for update: will set Jira to {child_original_total}h/{child_remaining_total}h")
                epics_to_update.append({
                    'key': epic['key'],
                    'original_estimate': child_original_total,
                    'remaining_estimate': child_remaining_total
                })
            else:
                logger.info(f"  ❌ Skipped {epic_key}: Children have no estimates")
        
        logger.info(f"📈 Found {len(epics_to_update)} epics that need estimate updates")
        
        if not epics_to_update:
            logger.warning("⚠️ No epics found that need estimate updates")
            return jsonify({
                'success': False,
                'error_type': 'Update Error',
                'error': 'No epics found that need estimate updates',
                'error_details': {
                    'suggestion': 'Check logs for detailed analysis of why epics were skipped'
                }
            })
        
        # Update estimates via API using JiraClient method
        updated_count = 0
        
        for epic in epics_to_update:
            try:
                # Format estimates as Jira time strings
                original_estimate_str = f"{epic['original_estimate']:.0f}h"
                remaining_estimate_str = f"{epic['remaining_estimate']:.0f}h"
                
                # Use JiraClient's update method
                success = jira_client.update_issue_estimates(
                    epic['key'], 
                    original_estimate_str, 
                    remaining_estimate_str
                )
                
                if success:
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error updating {epic['key']}: {str(e)}")
        
        if updated_count > 0:
            return jsonify({
                'success': True,
                'updated_count': updated_count,
                'total_epics': len(epics_to_update),
                'message': f'Successfully updated {updated_count} out of {len(epics_to_update)} epics'
            })
        else:
            return jsonify({
                'success': False,
                'error_type': 'Update Error',
                'error': 'No epics could be updated',
                'error_details': {
                    'suggestion': 'Time tracking may not be enabled or you may lack permissions. Check Jira configuration or use CSV export instead.'
                }
            })
        
    except Exception as e:
        error_type = type(e).__name__
        
        error_response = {
            'success': False,
            'error_type': 'Update Error',
            'error': str(e),
            'error_details': {
                'location': 'estimate_update',
                'suggestion': 'Please check your Jira credentials and try again'
            }
        }
        
        logger.error(f"Error in estimate update: {error_type} - {str(e)}", exc_info=True)
        return jsonify(error_response), 422

if __name__ == '__main__':
    app.run(debug=True)
