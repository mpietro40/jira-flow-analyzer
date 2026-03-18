"""
Flask Utilities - Shared Module
Common Flask decorators, utilities, and helpers for PerseusLeadTime applications.

Provides reusable Flask functionality including:
- Input validation decorators
- Error handling decorators
- Response formatting
- Common endpoint patterns
"""

import logging
import functools
from typing import Dict, Any, Optional, Callable
from flask import request, jsonify, Response
from datetime import datetime

logger = logging.getLogger('FlaskUtils')


# Validation decorators

def validate_jira_credentials(f: Callable) -> Callable:
    """
    Decorator to validate Jira credentials in request.
    
    Checks for required 'jira_url' and 'access_token' in request form/json.
    Returns 400 error if validation fails.
    
    Example:
        @app.route('/analyze', methods=['POST'])
        @validate_jira_credentials
        def analyze():
            jira_url = request.form['jira_url']
            access_token = request.form['access_token']
            # ... process request
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Get data from form or JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        # Validate required fields
        jira_url = data.get('jira_url', '').strip()
        access_token = data.get('access_token', '').strip()
        
        if not jira_url:
            logger.warning("⚠️ Missing jira_url in request")
            return jsonify({
                'error': True,
                'message': 'Jira URL is required'
            }), 400
        
        if not access_token:
            logger.warning("⚠️ Missing access_token in request")
            return jsonify({
                'error': True,
                'message': 'Access token is required'
            }), 400
        
        # Validate URL format
        if not jira_url.startswith(('http://', 'https://')):
            logger.warning(f"⚠️ Invalid Jira URL format: {jira_url}")
            return jsonify({
                'error': True,
                'message': 'Jira URL must start with http:// or https://'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_query_params(*required_params: str) -> Callable:
    """
    Decorator to validate query parameters.
    
    Args:
        *required_params: Names of required query parameters
        
    Example:
        @app.route('/search')
        @validate_query_params('project', 'status')
        def search():
            project = request.args['project']
            status = request.args['status']
            # ... process request
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            missing_params = []
            
            for param in required_params:
                if not request.args.get(param):
                    missing_params.append(param)
            
            if missing_params:
                logger.warning(f"⚠️ Missing query parameters: {missing_params}")
                return jsonify({
                    'error': True,
                    'message': f'Missing required parameters: {", ".join(missing_params)}'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def validate_form_fields(*required_fields: str) -> Callable:
    """
    Decorator to validate form fields.
    
    Args:
        *required_fields: Names of required form fields
        
    Example:
        @app.route('/submit', methods=['POST'])
        @validate_form_fields('name', 'email')
        def submit():
            name = request.form['name']
            email = request.form['email']
            # ... process request
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Get data from form or JSON
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
            
            missing_fields = []
            
            for field in required_fields:
                if not data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                logger.warning(f"⚠️ Missing form fields: {missing_fields}")
                return jsonify({
                    'error': True,
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# Error handling decorators

def handle_errors(f: Callable) -> Callable:
    """
    Decorator for comprehensive error handling.
    
    Catches exceptions and returns appropriate error responses.
    
    Example:
        @app.route('/analyze', methods=['POST'])
        @handle_errors
        def analyze():
            # ... may raise exceptions
            return {'result': 'success'}
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"⚠️ Validation error: {str(e)}")
            return jsonify({
                'error': True,
                'message': str(e),
                'type': 'validation_error'
            }), 400
        except PermissionError as e:
            logger.warning(f"⚠️ Permission error: {str(e)}")
            return jsonify({
                'error': True,
                'message': 'Permission denied',
                'type': 'permission_error'
            }), 403
        except Exception as e:
            logger.error(f"🚩 Unexpected error: {str(e)}", exc_info=True)
            return jsonify({
                'error': True,
                'message': 'An unexpected error occurred',
                'type': 'internal_error'
            }), 500
    
    return decorated_function


def log_request(f: Callable) -> Callable:
    """
    Decorator to log incoming requests.
    
    Example:
        @app.route('/analyze')
        @log_request
        def analyze():
            return {'result': 'success'}
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"📥 {request.method} {request.path} from {request.remote_addr}")
        
        start_time = datetime.now()
        result = f(*args, **kwargs)
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"📤 {request.method} {request.path} completed in {duration:.2f}s")
        
        return result
    
    return decorated_function


# Response formatting utilities

def success_response(data: Any, message: str = "Success") -> Dict:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Response dictionary
    """
    return {
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }


def error_response(message: str, error_type: str = "error", 
                   status_code: int = 500, details: Optional[Dict] = None) -> tuple:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        error_type: Type of error
        status_code: HTTP status code
        details: Optional error details
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'error': True,
        'message': message,
        'type': error_type,
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


# Jira client factory

def get_jira_client_from_request():
    """
    Create JiraClient from request data.
    
    Extracts credentials from request form/json and creates JiraClient instance.
    
    Returns:
        JiraClient instance
        
    Raises:
        ValueError: If credentials are missing or invalid
    """
    from src.common.jira_client import JiraClient
    
    # Get data from form or JSON
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    jira_url = data.get('jira_url', '').strip()
    access_token = data.get('access_token', '').strip()
    
    if not jira_url or not access_token:
        raise ValueError("Jira URL and access token are required")
    
    return JiraClient(jira_url, access_token)


# Date/time utilities

def format_date(date_str: Optional[str], format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Format date string.
    
    Args:
        date_str: ISO format date string
        format: Output format
        
    Returns:
        Formatted date string or None
    """
    if not date_str:
        return None
    
    try:
        if 'T' in date_str:
            # ISO format with time
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        return date_obj.strftime(format)
    except Exception as e:
        logger.warning(f"⚠️ Failed to parse date '{date_str}': {str(e)}")
        return date_str


def parse_jira_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse Jira date string to datetime object.
    
    Args:
        date_str: Jira date string (ISO format)
        
    Returns:
        datetime object or None
    """
    if not date_str:
        return None
    
    try:
        # Jira uses ISO format like "2024-01-15T10:30:45.123+0000"
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except Exception as e:
        logger.warning(f"⚠️ Failed to parse Jira date '{date_str}': {str(e)}")
        return None


def calculate_days_between(start_date: Optional[str], end_date: Optional[str]) -> Optional[int]:
    """
    Calculate days between two date strings.
    
    Args:
        start_date: Start date string
        end_date: End date string
        
    Returns:
        Number of days or None if dates invalid
    """
    try:
        start = parse_jira_date(start_date)
        end = parse_jira_date(end_date)
        
        if start and end:
            return (end - start).days
        
        return None
    except Exception as e:
        logger.warning(f"⚠️ Failed to calculate days between dates: {str(e)}")
        return None


# Caching utilities

def cache_in_session(key: str, data: Any):
    """
    Store data in Flask session.
    
    Args:
        key: Session key
        data: Data to store
    """
    from flask import session
    session[key] = data


def get_from_session(key: str, default: Any = None) -> Any:
    """
    Get data from Flask session.
    
    Args:
        key: Session key
        default: Default value if key not found
        
    Returns:
        Session data or default
    """
    from flask import session
    return session.get(key, default)


# Health check endpoint helper

def create_health_check_endpoint(app, checks: Optional[Dict[str, Callable]] = None):
    """
    Create a health check endpoint for the Flask app.
    
    Args:
        app: Flask application
        checks: Optional dictionary of check name -> check function
        
    Example:
        def check_database():
            return db.is_connected()
        
        create_health_check_endpoint(app, {
            'database': check_database
        })
    """
    @app.route('/health')
    def health_check():
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'app': app.name
        }
        
        if checks:
            check_results = {}
            all_healthy = True
            
            for check_name, check_func in checks.items():
                try:
                    check_results[check_name] = check_func()
                    if not check_results[check_name]:
                        all_healthy = False
                except Exception as e:
                    check_results[check_name] = False
                    all_healthy = False
                    logger.error(f"🚩 Health check '{check_name}' failed: {str(e)}")
            
            status['checks'] = check_results
            if not all_healthy:
                status['status'] = 'unhealthy'
                return jsonify(status), 503
        
        return jsonify(status), 200


# CORS helper (if needed)

def enable_cors(app, origins: str = "*"):
    """
    Enable CORS for Flask app.
    
    Args:
        app: Flask application
        origins: Allowed origins (default: all)
    """
    from flask import make_response
    
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = origins
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response


# Common route patterns

def create_form_route(app, route: str, template: str):
    """
    Create a simple form route that renders a template.
    
    Args:
        app: Flask application
        route: Route path
        template: Template name
        
    Example:
        create_form_route(app, '/analyze', 'analyze_form.html')
    """
    from flask import render_template
    
    @app.route(route)
    def form_view():
        return render_template(template)


# Pagination helper

def paginate_results(items: list, page: int = 1, per_page: int = 50) -> Dict:
    """
    Paginate a list of items.
    
    Args:
        items: List of items
        page: Page number (1-indexed)
        per_page: Items per page
        
    Returns:
        Dictionary with paginated data
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }
