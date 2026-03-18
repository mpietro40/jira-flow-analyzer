"""
PyInstaller runtime hook — executed before the application starts.

Sets JIRA_SUITE_BASE so that any module can locate bundled assets
(templates, static files, config) without hard-coding paths.
"""
import os
import sys

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.environ.setdefault('JIRA_SUITE_BASE', sys._MEIPASS)
    # Ensure _MEIPASS is on sys.path so all bundled packages are importable
    if sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)
