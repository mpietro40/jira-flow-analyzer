"""
Unified Dashboard - Jira Analytics Suite

Central navigation dashboard providing access to all Jira analytics applications.
This is a lightweight gateway that routes requests to individual microservices.

Features:
- Dashboard landing page with application links
- Health check aggregation across all services
- Backward-compatible proxy routes (optional)
- Minimal business logic - pure routing layer

Port: 5000
Author: Pietro Maffi
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, render_template, jsonify, redirect, request
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List

from apps.unified_dashboard.config import APPS, HEALTH_CHECK_TIMEOUT

# Import app blueprints
from apps.lead_time_analyzer.app import blueprint as lead_time_blueprint
from apps.initiative_viewer.app import blueprint as initiative_blueprint
from apps.epic_report.app import blueprint as epic_report_blueprint
from apps.pi_analyzer.app import blueprint as pi_blueprint
from apps.sprint_analyzer.app import blueprint as sprint_blueprint
from apps.pbc_analyzer.app import blueprint as pbc_blueprint
from apps.duplicate_detector.app import blueprint as duplicate_blueprint
from apps.psychological_safety.app import blueprint as psych_safety_blueprint
from apps.epic_fixversion.app import blueprint as epic_fixversion_blueprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('UnifiedDashboard')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'unified-dashboard-secret-key-change-in-production')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Register application blueprints (single-app, modular architecture)
app.register_blueprint(lead_time_blueprint, url_prefix='/lead-time-analyzer')
app.register_blueprint(initiative_blueprint, url_prefix='/initiative-viewer')
app.register_blueprint(epic_report_blueprint, url_prefix='/epic-report')
app.register_blueprint(pi_blueprint, url_prefix='/pi-analyzer')
app.register_blueprint(sprint_blueprint, url_prefix='/sprint-analyzer')
app.register_blueprint(pbc_blueprint, url_prefix='/pbc-analyzer')
app.register_blueprint(duplicate_blueprint, url_prefix='/duplicate-detector')
app.register_blueprint(psych_safety_blueprint, url_prefix='/psychological-safety')
app.register_blueprint(epic_fixversion_blueprint, url_prefix='/epic-fixversion')

logger.info("✅ Registered 9 application blueprints:")
logger.info("   - Lead Time Analyzer at /lead-time-analyzer")
logger.info("   - Initiative Viewer at /initiative-viewer")
logger.info("   - Epic Report at /epic-report")
logger.info("   - PI Analyzer at /pi-analyzer")
logger.info("   - Sprint Analyzer at /sprint-analyzer")
logger.info("   - PBC Analyzer at /pbc-analyzer")
logger.info("   - Duplicate Detector at /duplicate-detector")
logger.info("   - Psychological Safety at /psychological-safety")
logger.info("   - Epic Fix Version at /epic-fixversion")

# ============================================================================
# DASHBOARD & NAVIGATION ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """
    Main dashboard - landing page showing all available applications.
    
    Returns:
        Rendered dashboard template with application links
    """
    logger.info("📊 Dashboard accessed")
    return render_template('dashboard.html', apps=APPS)


@app.route('/apps')
def list_apps():
    """
    API endpoint to list all available applications with metadata.
    
    Returns:
        JSON: List of applications with URLs, descriptions, and status
    """
    apps_list = []
    for app_id, app_info in APPS.items():
        apps_list.append({
            'id': app_id,
            'name': app_info['name'],
            'description': app_info['description'],
            'url': app_info['url'],
            'port': app_info['port'],
            'icon': app_info['icon'],
            'color': app_info['color']
        })
    
    return jsonify({
        'success': True,
        'total_apps': len(apps_list),
        'apps': apps_list
    })


@app.route('/health')
def health_check():
    """
    Aggregated health check across all registered applications.
    
    Queries each application's /health endpoint and reports status.
    
    Returns:
        JSON: Overall dashboard health and individual app statuses
    """
    logger.info("🏥 Health check requested")
    
    app_statuses = []
    healthy_count = 0
    total_apps = len(APPS)
    
    for app_id, app_info in APPS.items():
        try:
            health_url = f"{app_info['url']}/health"
            response = requests.get(health_url, timeout=HEALTH_CHECK_TIMEOUT)
            
            if response.status_code == 200:
                app_status = {
                    'id': app_id,
                    'name': app_info['name'],
                    'status': 'healthy',
                    'port': app_info['port'],
                    'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2)
                }
                healthy_count += 1
            else:
                app_status = {
                    'id': app_id,
                    'name': app_info['name'],
                    'status': 'unhealthy',
                    'port': app_info['port'],
                    'error': f'HTTP {response.status_code}'
                }
        
        except requests.exceptions.Timeout:
            app_status = {
                'id': app_id,
                'name': app_info['name'],
                'status': 'timeout',
                'port': app_info['port'],
                'error': 'Health check timeout'
            }
        
        except requests.exceptions.ConnectionError:
            app_status = {
                'id': app_id,
                'name': app_info['name'],
                'status': 'unreachable',
                'port': app_info['port'],
                'error': 'Service not running'
            }
        
        except Exception as e:
            app_status = {
                'id': app_id,
                'name': app_info['name'],
                'status': 'error',
                'port': app_info['port'],
                'error': str(e)
            }
        
        app_statuses.append(app_status)
    
    # Determine overall status
    if healthy_count == total_apps:
        overall_status = 'healthy'
    elif healthy_count > 0:
        overall_status = 'degraded'
    else:
        overall_status = 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'dashboard': 'healthy',
        'port': 5000,
        'timestamp': datetime.now().isoformat(),
        'apps': {
            'total': total_apps,
            'healthy': healthy_count,
            'unhealthy': total_apps - healthy_count
        },
        'details': app_statuses
    })


@app.route('/favicon.ico')
def favicon():
    """Favicon handler - returns 204 No Content."""
    return '', 204


# ============================================================================
# ============================================================================
# APP NAVIGATION - All apps now served via registered blueprints
# No redirects needed - blueprints serve content directly
# ============================================================================

# ============================================================================
# PROXY ROUTES (Optional - for backward compatibility)
# ============================================================================

@app.route('/analyze_epic_fixversion', methods=['POST'])
def proxy_analyze_epic_fixversion():
    """
    Proxy route for Epic Fix Version analysis (backward compatibility).
    
    Forwards requests to the Epic Fix Version microservice.
    """
    try:
        target_url = f"{APPS['epic_fixversion']['url']}/analyze"
        response = requests.post(target_url, data=request.form, timeout=60)
        return response.content, response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Proxy error (epic_fixversion): {str(e)}")
        return jsonify({'error': f'Proxy failed: {str(e)}'}), 503


@app.route('/export_epic_fixversion_pdf', methods=['POST'])
def proxy_export_epic_fixversion_pdf():
    """
    Proxy route for Epic Fix Version PDF export (backward compatibility).
    
    Forwards requests to the Epic Fix Version microservice.
    """
    try:
        target_url = f"{APPS['epic_fixversion']['url']}/export_pdf"
        response = requests.post(
            target_url,
            json=request.get_json(),
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        return response.content, response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Proxy error (epic_fixversion_pdf): {str(e)}")
        return jsonify({'error': f'Proxy failed: {str(e)}'}), 503


@app.route('/analyze_safety', methods=['POST'])
def proxy_analyze_safety():
    """
    Proxy route for Psychological Safety analysis (backward compatibility).
    
    Forwards requests to the Psychological Safety microservice.
    """
    try:
        target_url = f"{APPS['psychological_safety']['url']}/analyze_safety"
        response = requests.post(target_url, data=request.form, timeout=60)
        return response.content, response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Proxy error (psychological_safety): {str(e)}")
        return jsonify({'error': f'Proxy failed: {str(e)}'}), 503


@app.route('/get_trends', methods=['POST'])
def proxy_get_trends():
    """
    Proxy route for Psychological Safety trends (backward compatibility).
    
    Forwards requests to the Psychological Safety microservice.
    """
    try:
        target_url = f"{APPS['psychological_safety']['url']}/get_trends"
        response = requests.post(target_url, data=request.form, timeout=60)
        return response.content, response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Proxy error (psychological_safety_trends): {str(e)}")
        return jsonify({'error': f'Proxy failed: {str(e)}'}), 503


@app.route('/analyze_pbc', methods=['POST'])
def proxy_analyze_pbc():
    """
    Proxy route for PBC analysis (backward compatibility).
    
    Forwards requests to the PBC Analyzer microservice.
    """
    try:
        target_url = f"{APPS['pbc_analyzer']['url']}/analyze"
        response = requests.post(target_url, data=request.form, timeout=60)
        return response.content, response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Proxy error (pbc_analyzer): {str(e)}")
        return jsonify({'error': f'Proxy failed: {str(e)}'}), 503


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Page not found',
        'message': 'The requested endpoint does not exist',
        'available_routes': [
            '/',
            '/health',
            '/apps',
            '/initiative-viewer',
            '/epic-report',
            '/pi-analyzer',
            '/sprint-analyzer',
            '/pbc-analyzer',
            '/duplicate-detector',
            '/psychological-safety',
            '/epic-fixversion'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the Unified Dashboard application."""
    logger.info("=" * 80)
    logger.info("🚀 Starting Unified Dashboard - Jira Analytics Suite")
    logger.info("=" * 80)
    logger.info(f"📊 Dashboard Port: 5000")
    logger.info(f"📱 Registered Applications: {len(APPS)}")
    for app_id, app_info in APPS.items():
        logger.info(f"   - {app_info['name']} ({app_info['port']}): {app_info['description']}")
    logger.info("=" * 80)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    if debug:
        logger.info("🔧 Running in DEVELOPMENT mode")
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        logger.info("🏭 Running in PRODUCTION mode with Waitress")
        try:
            from waitress import serve
            serve(app, host='0.0.0.0', port=port, threads=4)
        except ImportError:
            logger.warning("⚠️  Waitress not available, falling back to Flask dev server")
            app.run(debug=False, host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
