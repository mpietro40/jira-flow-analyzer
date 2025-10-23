"""
Sprint Analyzer Web Application
A Flask-based web interface for sprint analysis and forecasting.

Author: Sprint Analysis Web Tool
Purpose: Provide user-friendly web interface for sprint capacity analysis
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import logging
from datetime import datetime
import os
import traceback

# Reuse existing classes
from jira_client import JiraClient
from sprint_analyzer import SprintAnalyzer
from sprint_pdf_generator import SprintPDFReportGenerator

# Configure logging with same style
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SprintWebApp')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sprint-analyzer-key-change-in-production')

@app.route('/')
def index():
    """Main page with sprint analysis form."""
    return render_template('sprint_analyzer.html')

@app.route('/analyze_sprint', methods=['POST'])
def analyze_sprint():
    """
    Process sprint analysis request.
    
    Returns:
        JSON response with sprint analysis results
    """
    try:
        # Extract form data
        jira_url = request.form.get('jira_url')
        access_token = request.form.get('access_token')
        sprint_name = request.form.get('sprint_name')
        history_months = int(request.form.get('history_months', 6))
        team_size = int(request.form.get('team_size', 8))
        sprint_days = int(request.form.get('sprint_days', 10))
        hours_per_day = int(request.form.get('hours_per_day', 8))
        completion_statuses = request.form.get('completion_statuses', 'Done,Closed').strip()
        excluded_types = request.form.get('excluded_types', 'Epic').strip()
        
        # Validate inputs
        if not all([jira_url, access_token, sprint_name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        logger.info(f"🚀 Starting sprint analysis for: {sprint_name}")
        
        # Initialize components
        jira_client = JiraClient(jira_url, access_token)
        
        # Test connection
        if not jira_client.test_connection():
            return jsonify({'error': 'Failed to connect to Jira. Please check your URL and token.'}), 401
        
        logger.info("✅ Connected to Jira successfully")
        
        # Analyze sprint with capacity and status configuration
        analyzer = SprintAnalyzer(jira_client)
        analyzer.configure_capacity(team_size, sprint_days, hours_per_day)
        analyzer.configure_completion_statuses(completion_statuses)
        analyzer.configure_excluded_types(excluded_types)
        
        # Capture detailed logs for PDF export
        detailed_logs = {}
        jql_queries = []
        
        results = analyzer.analyze_sprint(sprint_name, history_months)
        
        # Extract detailed information for PDF
        if 'historical_context' in results:
            historical = results['historical_context']
            if 'monte_carlo_forecast' in historical:
                mc_data = historical['monte_carlo_forecast']
                if 'percentiles' in mc_data:
                    detailed_logs['monte_carlo'] = mc_data['percentiles']
        
        # Add JQL queries (sprint + historical)
        if sprint_name.isdigit():
            jql_queries.append(f'sprint = {sprint_name}')
        else:
            jql_queries.append(f'sprint = "{sprint_name}"')
        
        # Add historical data JQL query with actual pattern used
        if 'historical_context' in results:
            historical = results['historical_context']
            pattern_used = historical.get('sprint_pattern_used', '')
            if pattern_used:
                jql_queries.append(f'Historical data filtered by sprint pattern: {pattern_used}')
            else:
                jql_queries.append('Historical data: All completed issues in date range')
        
        # Add forecast details
        if 'forecast' in results:
            forecast = results['forecast']
            historical = results.get('historical_context', {})
            detailed_logs['forecast_details'] = {
                'remaining_stories': forecast.get('remaining_stories', 0),
                'velocity_used': historical.get('average_velocity', 0),
                'similar_sprints_analyzed': historical.get('similar_sprints_count', 0),
                'sprint_pattern_used': historical.get('sprint_pattern_used', 'None')
            }
        
        # Add weekly velocities from historical context if available
        if 'historical_context' in results and results['historical_context'].get('total_historical_issues', 0) > 0:
            detailed_logs['weekly_velocities'] = "[Historical velocity data used for Monte Carlo simulation]"
        else:
            detailed_logs['weekly_velocities'] = "[No historical data available]"
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 404
        
        # Format results for web display
        web_results = format_results_for_web(results)
        
        logger.info("✅ Sprint analysis completed successfully")
        return jsonify({
            'success': True,
            'sprint_name': sprint_name,
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'results': web_results,
            'jql_queries': jql_queries,
            'detailed_logs': detailed_logs
        })
        
    except Exception as e:
        logger.error(f"🚩 Sprint analysis error: {str(e)}")
        logger.error(f"🚩 Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

def format_results_for_web(results: dict) -> dict:
    """
    Format analysis results for web display.
    
    Args:
        results (dict): Raw analysis results
        
    Returns:
        dict: Formatted results for web UI
    """
    workload = results.get('workload_analysis', {})
    forecast = results.get('forecast', {})
    summary = results.get('summary', {})
    
    # Format main metrics
    main_metrics = {
        'total_issues': summary.get('total_issues', 0),
        'total_estimated_hours': round(summary.get('total_estimated_hours', 0), 1),
        'remaining_hours': round(summary.get('remaining_hours', 0), 1),
        'time_spent_hours': round(workload.get('total_time_spent', 0), 1),
        'overall_progress': round(workload.get('overall_progress', 0), 1),
        'completion_probability': round(summary.get('completion_probability', 0), 0),
        'risk_level': summary.get('risk_level', 'UNKNOWN')
    }
    
    # Format status breakdown
    status_breakdown = []
    for status, data in workload.get('status_breakdown', {}).items():
        status_breakdown.append({
            'status': status,
            'count': data.get('count', 0),
            'remaining_hours': round(data.get('remaining_estimate', 0), 1),
            'time_spent': round(data.get('time_spent', 0), 1)
        })
    
    # Format forecast details
    date_forecast = forecast.get('date_forecast', {})
    forecast_details = {
        'estimated_weeks_needed': round(forecast.get('estimated_weeks_needed', 0), 1),
        'estimated_days_needed': round(forecast.get('estimated_days_needed', 0), 1),
        'remaining_days': round(forecast.get('remaining_days', 0), 1),
        'adjusted_hours_estimate': round(forecast.get('adjusted_hours_estimate', 0), 1),
        'probability_of_completion': round(forecast.get('probability_of_completion', 0), 0),
        'risk_level': forecast.get('risk_level', 'UNKNOWN'),
        'recommendations': forecast.get('recommendations', []),
        'monte_carlo_scenarios': forecast.get('monte_carlo_scenarios', {}),
        'remaining_stories': forecast.get('remaining_stories', 0),
        'date_forecast': {
            'planned_end_date': date_forecast.get('planned_end_date'),
            'estimated_completion_date': date_forecast.get('estimated_completion_date'),
            'days_difference': date_forecast.get('days_difference', 0),
            'will_finish_on_time': date_forecast.get('will_finish_on_time', True),
            'missing_days': date_forecast.get('missing_days', 0),
            'date_risk_level': date_forecast.get('date_risk_level', 'LOW')
        }
    }
    
    # Format historical context
    historical = results.get('historical_context', {})
    monte_carlo_data = historical.get('monte_carlo_forecast', {})
    historical_context = {
        'average_velocity': round(historical.get('average_velocity', 0), 1),
        'estimate_accuracy': round(historical.get('estimate_accuracy', 1), 2),
        'completion_rate': round(historical.get('completion_rate', 0) * 100, 0),
        'total_historical_issues': historical.get('total_historical_issues', 0),
        'monte_carlo_enabled': bool(monte_carlo_data),
        'velocity_percentiles': monte_carlo_data.get('percentiles', {}),
        'sprint_pattern_used': historical.get('sprint_pattern_used', ''),
        'similar_sprints_count': historical.get('similar_sprints_count', 0),
        'velocity_variance': historical.get('velocity_variance', 0),
        'weekly_story_counts': historical.get('weekly_story_counts', [])
    }
    
    # Get risk level color
    risk_colors = {
        'LOW': 'success',
        'MEDIUM': 'warning', 
        'HIGH': 'danger',
        'UNKNOWN': 'secondary'
    }
    
    return {
        'main_metrics': main_metrics,
        'status_breakdown': status_breakdown,
        'forecast_details': forecast_details,
        'historical_context': historical_context,
        'risk_color': risk_colors.get(main_metrics['risk_level'], 'secondary'),
        'unestimated_issues': workload.get('unestimated_issues', 0)
    }

@app.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """
    Export sprint analysis as PDF report.
    
    Returns:
        PDF file response
    """
    try:
        # Get the analysis data from the request
        data = request.get_json()
        
        if not data or 'results' not in data:
            return jsonify({'error': 'No analysis data provided'}), 400
        
        results = data['results']
        sprint_name = data.get('sprint_name', 'Unknown Sprint')
        jql_queries = data.get('jql_queries', [])
        detailed_logs = data.get('detailed_logs', {})
        
        logger.info(f"📄 Generating PDF report for: {sprint_name}")
        
        # Generate PDF
        pdf_generator = SprintPDFReportGenerator()
        pdf_content = pdf_generator.generate_report(
            results=results,
            sprint_name=sprint_name,
            jql_queries=jql_queries,
            detailed_logs=detailed_logs
        )
        
        # Create response
        filename = f"sprint_analysis_{sprint_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        response = Response(
            pdf_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf'
            }
        )
        
        logger.info(f"✅ PDF report generated successfully: {filename}")
        return response
        
    except Exception as e:
        logger.error(f"🚩 PDF export error: {str(e)}")
        logger.error(f"🚩 Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'PDF export failed: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Sprint Analyzer Web App'
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Sprint Analyzer Web Application...")
    app.run(debug=True, host='0.0.0.0', port=5200)