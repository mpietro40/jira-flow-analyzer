# Application Migration Template

## 📋 Quick Reference for Migrating Applications

Based on successful initiative_viewer migration. Use this as a checklist for migrating the remaining 8 applications.

---

## 🎯 Migration Checklist

### Pre-Migration
- [ ] Read original application code (`*.py`)
- [ ] Identify Flask routes and endpoints
- [ ] Locate templates (`templates/*.html`)
- [ ] Identify static assets (`static/*`)
- [ ] Note unique dependencies
- [ ] Check for custom utilities that could be shared

### Step 1: Create App Structure (5 min)
```bash
cd apps/
mkdir <app_name>
cd <app_name>
mkdir templates tests static
```

### Step 2: Create app.py (30-60 min)
```python
"""
<App Name> - Flask Application (Refactored)
<Brief description>

Author: Pietro Maffi
Version: 2.0.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify
import logging
from waitress import serve
import webbrowser
import threading
import argparse

# Import shared utilities
from src.common import (
    JiraClient,
    CacheManager,
    FileStorage,
    validate_jira_credentials,
    handle_errors,
    log_request
)
from src.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('<AppName>')

# Configuration
config = get_config()
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Initialize utilities
cache = CacheManager(cache_dir=os.path.join(config.CACHE_DIR, '<app_name>'))
storage = FileStorage(base_path=os.path.join(config.STORAGE_DIR, '<app_name>'))

# Routes
@app.route('/')
@log_request
def index():
    """Display main page."""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'app': '<app_name>',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })

# CLI Entry Point
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='<App Name> Application')
    parser.add_argument('--port', type=int, default=<PORT>, help='Port to run on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser")
    
    args = parser.parse_args()
    
    if not args.no_browser and not args.debug:
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(f'http://localhost:{args.port}')
        threading.Thread(target=open_browser, daemon=True).start()
    
    if args.debug:
        app.run(host=args.host, port=args.port, debug=True)
    else:
        logger.info(f"🚀 Starting <App Name> on port {args.port}")
        serve(app, host=args.host, port=args.port, threads=4)

if __name__ == '__main__':
    main()
```

**Port Assignments:**
- initiative_viewer: 5001 ✅
- epic_report: 5002
- pi_analyzer: 5003
- sprint_analyzer: 5004
- pbc_analyzer: 5005
- duplicate_detector: 5006
- psychological_safety: 5007
- epic_fixversion: 5008
- unified_dashboard: 5000

### Step 3: Create PDF Generator (if needed) (30 min)
```python
"""
<App Name> PDF Generator
Extends PDFGeneratorBase
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.common import PDFGeneratorBase
from reportlab.lib.pagesizes import letter
from typing import List, Dict, BinaryIO

class <AppName>PDFGenerator(PDFGeneratorBase):
    """PDF Generator for <App Name>."""
    
    def __init__(self, jira_base_url: str):
        super().__init__()
        self.jira_base_url = jira_base_url
    
    def generate_report(self, data: List[Dict], output_file: BinaryIO, title: str):
        """Generate PDF report."""
        # Use self.create_document(), self.add_table(), etc.
        pass
```

### Step 4: Copy and Adapt Templates (15 min)
1. Copy templates from old location
2. Update paths and imports
3. Simplify if possible
4. Remove deprecated features
5. Test rendering

### Step 5: Create Support Files (15 min)

**__init__.py:**
```python
"""<App Name> Application"""
__version__ = '2.0.0'
```

**run.py:**
```python
"""Standalone launcher for <App Name>."""
from app import main

if __name__ == '__main__':
    main()
```

**requirements.txt:**
```
# <App Name> - Module Requirements
# Most dependencies in root requirements.txt
# List only app-specific dependencies here
```

### Step 6: Create Tests (60 min)

**tests/conftest.py:**
```python
"""Test configuration."""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def client():
    from apps.<app_name>.app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

**tests/test_app.py:**
```python
"""Unit tests for <App Name>."""
import pytest

def test_index_route(client):
    """Test index route."""
    response = client.get('/')
    assert response.status_code == 200

def test_health_check(client):
    """Test health check."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
```

### Step 7: Create README.md (30 min)
Use [initiative_viewer/README.md](apps/initiative_viewer/README.md) as template:
- Overview
- Features
- Quick Start
- Usage
- Configuration
- API Endpoints
- Testing
- Troubleshooting

### Step 8: Validate (15 min)
```bash
# Check syntax
python -c "from apps.<app_name> import app; print('✅ Imports OK')"

# Run tests (when pytest installed)
cd apps/<app_name>
pytest tests/ -v

# Check for errors
# Use IDE or linter

# Test run (when dependencies installed)
python run.py --debug
```

---

## 🔄 Common Patterns

### 1. Using JiraClient
```python
from src.common import JiraClient

client = JiraClient(jira_url, access_token)
if not client.test_connection():
    return jsonify({'error': 'Connection failed'}), 401

issues = client.fetch_issues(jql_query, max_results=100)
```

### 2. Using CacheManager
```python
from src.common import CacheManager

cache = CacheManager(cache_dir='data/cache/my_app')

# Save
cache.save('key', data, metadata={'info': 'value'})

# Retrieve
if cache.is_valid('key', max_age=1800):  # 30 min
    data = cache.get('key')

# List cached
items = cache.list_cached()
```

### 3. Using FileStorage
```python
from src.common import FileStorage

storage = FileStorage(base_path='data/storage/my_app')

# Save JSON
storage.save_json('data.json', {'key': 'value'})

# Read JSON
data = storage.read_json('data.json')

# List files
files = storage.list_files(pattern='*.json')
```

### 4. Using Flask Decorators
```python
from src.common import validate_jira_credentials, handle_errors, log_request

@app.route('/analyze', methods=['POST'])
@log_request                      # Log request details
@validate_jira_credentials       # Validate Jira credentials
@handle_errors                    # Catch and format errors
def analyze():
    jira_url = request.form['jira_url']
    token = request.form['access_token']
    # ... logic
```

### 5. Using PDFGeneratorBase
```python
from src.common import PDFGeneratorBase

class MyPDFGenerator(PDFGeneratorBase):
    def generate_report(self, data, output_file):
        doc = self.create_document(output_file, title='My Report')
        story = []
        
        # Add elements
        story.append(self.create_title('Report Title'))
        story.append(self.create_spacer())
        
        # Add table
        table_data = [['Col1', 'Col2'], ['Data1', 'Data2']]
        story.append(self.create_table(table_data, style='alternating'))
        
        # Build
        doc.build(story)
```

---

## 🎯 Application-Specific Notes

### epic_report
- Port: 5002
- PDF: Epic status reports
- Special: Multiple chart types
- Shared: JiraClient, PDFGeneratorBase

### pi_analyzer
- Port: 5003
- PDF: PI progress reports
- Special: Sprint calculations
- Shared: JiraClient, CacheManager, PDFGeneratorBase

### sprint_analyzer
- Port: 5004
- No PDF (HTML only)
- Special: Sprint metrics dashboard
- Shared: JiraClient, CacheManager

### pbc_analyzer
- Port: 5005
- PDF: PBC (Program Backlog Checkpoint)
- Special: Backlog analysis
- Shared: JiraClient, PDFGeneratorBase

### duplicate_detector
- Port: 5006
- No PDF
- Special: MongoDB integration
- Shared: JiraClient, flask_utils

### psychological_safety
- Port: 5007
- No PDF (form-based)
- Special: Survey results
- Shared: FileStorage, flask_utils

### epic_fixversion
- Port: 5008
- No PDF
- Special: Bulk epic updates
- Shared: JiraClient, flask_utils

### unified_dashboard
- Port: 5000 (main)
- No PDF
- Special: Aggregates all apps
- Shared: All utilities

---

## 📊 Migration Time Estimates

| Task | Time |
|------|------|
| Structure creation | 5 min |
| app.py refactoring | 30-60 min |
| PDF generator (if needed) | 30 min |
| Templates | 15 min |
| Support files | 15 min |
| Tests | 60 min |
| README | 30 min |
| Validation | 15 min |
| **Total per app** | **3-4 hours** |

---

## ⚠️ Common Pitfalls

1. **Forgetting project_root path**
   ```python
   # Always add at top of app.py
   project_root = Path(__file__).parent.parent.parent
   sys.path.insert(0, str(project_root))
   ```

2. **Wrong import paths**
   ```python
   # ❌ Wrong
   from common import JiraClient
   
   # ✅ Correct
   from src.common import JiraClient
   ```

3. **Missing config**
   ```python
   # ❌ Wrong
   app.secret_key = 'hardcoded'
   
   # ✅ Correct
   from src.config import get_config
   config = get_config()
   app.secret_key = config.SECRET_KEY
   ```

4. **Not using decorators**
   ```python
   # ❌ Manual validation
   if not request.form.get('jira_url'):
       return jsonify({'error': 'Missing Jira URL'}), 400
   
   # ✅ Use decorator
   @validate_jira_credentials
   def my_route():
       # Validation handled automatically
   ```

5. **Duplicate code**
   ```python
   # ❌ Creating custom Jira client
   def fetch_from_jira():
       # ... custom implementation
   
   # ✅ Use shared client
   from src.common import JiraClient
   client = JiraClient(url, token)
   ```

---

## ✅ Success Criteria

For each migrated app, ensure:
- [ ] Runs standalone (`python run.py`)
- [ ] All routes work
- [ ] Templates render correctly
- [ ] Uses shared libraries (no duplication)
- [ ] Has 15+ unit tests
- [ ] README is complete
- [ ] No syntax/import errors
- [ ] Health check endpoint works
- [ ] Proper error handling
- [ ] Logging configured

---

## 📚 Reference Files

**Good examples:**
- [apps/initiative_viewer/app.py](apps/initiative_viewer/app.py) - Complete Flask app
- [apps/initiative_viewer/pdf_generator.py](apps/initiative_viewer/pdf_generator.py) - PDF generation
- [apps/initiative_viewer/README.md](apps/initiative_viewer/README.md) - Documentation
- [apps/initiative_viewer/tests/test_app.py](apps/initiative_viewer/tests/test_app.py) - Testing

**Shared libraries:**
- [src/common/jira_client.py](src/common/jira_client.py) - Jira API
- [src/common/cache_manager.py](src/common/cache_manager.py) - Caching
- [src/common/flask_utils.py](src/common/flask_utils.py) - Flask helpers
- [src/common/pdf_generator_base.py](src/common/pdf_generator_base.py) - PDF base

---

**Use this template to migrate the remaining 8 applications consistently!** 🚀
