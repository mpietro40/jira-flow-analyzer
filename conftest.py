"""
Root conftest for JiraAnalyzerSuite test suite.

Ensures the project root (this directory) is on sys.path so that
  ``from apps.<sub-app>.app import ...`` works regardless of whether
  test directories use __init__.py (package-mode) or not.
"""
import sys
from pathlib import Path

# Add JiraAnalyzerSuite/ to sys.path so 'apps.*' and 'src.*' are importable
_PROJECT_ROOT = str(Path(__file__).parent)
# Always insert — avoid case-sensitivity / trailing-slash mismatches on Windows
sys.path.insert(0, _PROJECT_ROOT)
