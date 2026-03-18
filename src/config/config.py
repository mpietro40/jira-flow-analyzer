"""
Configuration Module - Shared
Default configuration settings for PerseusLeadTime applications.

Applications can import and override these settings as needed.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Project root
# When PyInstaller bundles the app, __file__ lives inside sys._MEIPASS —
# a temp directory that is recreated on every launch and deleted on exit.
# Writable data (cache, storage, logs) must live next to the .exe instead.
if getattr(sys, 'frozen', False):
    # Frozen: use the directory that contains the running .exe
    PROJECT_ROOT = Path(sys.executable).parent
else:
    # Normal source run
    PROJECT_ROOT = Path(__file__).parent.parent.parent

# Application settings
APP_NAME = 'PerseusLeadTime'
APP_VERSION = '2.0.0'
APP_AUTHOR = 'Pietro Maffi'

# Flask settings
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = FLASK_ENV == 'development'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Server settings
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# Jira API settings
JIRA_DEFAULT_MAX_RESULTS = 5000
JIRA_DEFAULT_BATCH_SIZE = 200
JIRA_DEFAULT_MIN_BATCH_SIZE = 50
JIRA_CONNECT_TIMEOUT = 15  # seconds
JIRA_READ_TIMEOUT = 60     # seconds

# Cache settings
CACHE_DIR = PROJECT_ROOT / 'cache'
CACHE_TTL_MINUTES = int(os.getenv('CACHE_TTL_MINUTES', 120))
CACHE_MAX_AGE_DAYS = 7

# Storage settings
STORAGE_DIR = PROJECT_ROOT / 'storage'
UPLOAD_DIR = STORAGE_DIR / 'uploads'
EXPORT_DIR = STORAGE_DIR / 'exports'
REPORT_DIR = STORAGE_DIR / 'reports'

# Log settings
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# PDF settings
PDF_PAGE_SIZE = 'A4'
PDF_MARGIN = 72
PDF_FONT_SIZE = 10

# Application-specific defaults
DEFAULT_APPS = {
    'unified_dashboard': {'port': 5000, 'name': 'Unified Dashboard'},
    'initiative_viewer': {'port': 5001, 'name': 'Initiative Viewer'},
    'epic_report': {'port': 5002, 'name': 'Epic Report'},
    'pi_analyzer': {'port': 5003, 'name': 'PI Analyzer'},
    'sprint_analyzer': {'port': 5004, 'name': 'Sprint Analyzer'},
    'pbc_analyzer': {'port': 5005, 'name': 'PBC Analyzer'},
    'duplicate_detector': {'port': 5006, 'name': 'Duplicate Detector'},
    'psychological_safety': {'port': 5007, 'name': 'Psychological Safety'},
    'epic_fixversion': {'port': 5008, 'name': 'Epic FixVersion'},
}

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    """Base configuration class."""
    
    # App settings
    APP_NAME = APP_NAME
    APP_VERSION = APP_VERSION
    
    # Flask
    SECRET_KEY = SECRET_KEY
    DEBUG = DEBUG
    
    # Server
    HOST = HOST
    PORT = PORT
    
    # Jira
    JIRA_MAX_RESULTS = JIRA_DEFAULT_MAX_RESULTS
    JIRA_BATCH_SIZE = JIRA_DEFAULT_BATCH_SIZE
    JIRA_CONNECT_TIMEOUT = JIRA_CONNECT_TIMEOUT
    JIRA_READ_TIMEOUT = JIRA_READ_TIMEOUT
    
    # Cache
    CACHE_DIR = str(CACHE_DIR)
    CACHE_TTL_MINUTES = CACHE_TTL_MINUTES
    
    # Storage
    STORAGE_DIR = str(STORAGE_DIR)
    UPLOAD_DIR = str(UPLOAD_DIR)
    EXPORT_DIR = str(EXPORT_DIR)
    REPORT_DIR = str(REPORT_DIR)
    
    # Logging
    LOG_DIR = str(LOG_DIR)
    LOG_LEVEL = LOG_LEVEL
    LOG_FORMAT = LOG_FORMAT


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Use environment variables in production
    SECRET_KEY = os.getenv('SECRET_KEY')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    CACHE_TTL_MINUTES = 1  # Short TTL for tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: Optional[str] = None) -> Config:
    """
    Get configuration for specified environment.
    
    Args:
        env: Environment name (development, production, testing)
             Uses FLASK_ENV environment variable if not specified
        
    Returns:
        Configuration class instance
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')

    config_class = config.get(env, config['default'])

    if env == 'production' and not os.getenv('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in production")

    return config_class
