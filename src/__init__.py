"""
PerseusLeadTime Source Code
Root package for shared code and utilities.

This package contains all shared, reusable code for PerseusLeadTime applications.
"""

__version__ = '2.0.0'
__author__ = 'Pietro Maffi'

# Import common utilities for easy access
from src.common import (
    JiraClient,
    CacheManager,
    PDFGeneratorBase,
    FileStorage,
    get_default_cache,
    get_default_storage
)

__all__ = [
    'JiraClient',
    'CacheManager',
    'PDFGeneratorBase',
    'FileStorage',
    'get_default_cache',
    'get_default_storage',
]
