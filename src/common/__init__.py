"""
Common utilities and shared code for PerseusLeadTime applications.

This package provides shared libraries used across all applications:
- jira_client: Jira API integration
- cache_manager: File-based caching system
- pdf_generator_base: PDF report generation
- file_storage: File storage utilities
- flask_utils: Flask decorators and helpers
"""

__version__ = '2.0.0'

# Make common imports easily accessible
from .jira_client import JiraClient
from .cache_manager import CacheManager, get_default_cache, cache_data, get_cached_data, is_cache_valid
from .pdf_generator_base import PDFGeneratorBase, generate_simple_pdf
from .file_storage import FileStorage, get_default_storage, save_file, load_file, file_exists
from .flask_utils import (
    validate_jira_credentials,
    validate_query_params,
    validate_form_fields,
    handle_errors,
    log_request,
    success_response,
    error_response,
    get_jira_client_from_request,
    format_date,
    parse_jira_date,
    calculate_days_between,
    create_health_check_endpoint
)

__all__ = [
    # Classes
    'JiraClient',
    'CacheManager',
    'PDFGeneratorBase',
    'FileStorage',
    
    # Cache functions
    'get_default_cache',
    'cache_data',
    'get_cached_data',
    'is_cache_valid',
    
    # Storage functions
    'get_default_storage',
    'save_file',
    'load_file',
    'file_exists',
    
    # PDF functions
    'generate_simple_pdf',
    
    # Flask decorators
    'validate_jira_credentials',
    'validate_query_params',
    'validate_form_fields',
    'handle_errors',
    'log_request',
    
    # Flask utilities
    'success_response',
    'error_response',
    'get_jira_client_from_request',
    'format_date',
    'parse_jira_date',
    'calculate_days_between',
    'create_health_check_endpoint',
]
