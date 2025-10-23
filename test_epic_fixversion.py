"""
Test script for Epic Fix Version application
Validates the application structure without requiring dependencies
"""

import os
from pathlib import Path

def test_application_structure():
    """Test that all required files exist"""
    print("Testing Epic Fix Version Application Structure\n")
    
    base_dir = Path(__file__).parent
    
    # Required files
    required_files = [
        'epic_fixversion_app.py',
        'templates/epic_fixversion.html',
        'EPIC_FIXVERSION_GUIDE.md',
        'EPIC_FIXVERSION_QUICKSTART.md',
        'README_EPIC_FIXVERSION.md',
        'epic_fixversion_results/README.md'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"[OK] {file_path} ({size} bytes)")
        else:
            print(f"[MISSING] {file_path}")
            all_exist = False
    
    # Check directories
    print("\n[DIRS] Checking directories...")
    dirs = ['templates', 'epic_fixversion_results']
    for dir_name in dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"[OK] {dir_name}/ directory exists")
        else:
            print(f"[MISSING] {dir_name}/ directory")
            all_exist = False
    
    # Validate Python file syntax
    print("\n[PYTHON] Validating Python syntax...")
    app_file = base_dir / 'epic_fixversion_app.py'
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, app_file, 'exec')
        print(f"[OK] epic_fixversion_app.py - Valid Python syntax")
    except SyntaxError as e:
        print(f"[ERROR] epic_fixversion_app.py - Syntax error: {e}")
        all_exist = False
    
    # Validate HTML file
    print("\n[HTML] Validating HTML template...")
    html_file = base_dir / 'templates' / 'epic_fixversion.html'
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        if '<!DOCTYPE html>' in html_content and '</html>' in html_content:
            print(f"[OK] epic_fixversion.html - Valid HTML structure")
        else:
            print(f"[WARNING] epic_fixversion.html - Missing DOCTYPE or closing tag")
    except Exception as e:
        print(f"[ERROR] epic_fixversion.html - Error: {e}")
        all_exist = False
    
    # Check for key components in app file
    print("\n[COMPONENTS] Checking application components...")
    with open(app_file, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    components = {
        'Flask app': 'app = Flask(__name__)',
        'Analyzer class': 'class EpicFixVersionAnalyzer',
        'Analyze route': '@app.route(\'/analyze\'',
        'Health route': '@app.route(\'/health\'',
        'Logging': 'logging.basicConfig',
        'Results directory': 'RESULTS_DIR'
    }
    
    for component, search_str in components.items():
        if search_str in app_content:
            print(f"[OK] {component} - Found")
        else:
            print(f"[MISSING] {component}")
            all_exist = False
    
    # Summary
    print("\n" + "="*60)
    if all_exist:
        print("[SUCCESS] ALL TESTS PASSED!")
        print("\nApplication is ready to run:")
        print("   python epic_fixversion_app.py")
        print("\nDocumentation:")
        print("   - Quick Start: EPIC_FIXVERSION_QUICKSTART.md")
        print("   - User Guide: EPIC_FIXVERSION_GUIDE.md")
        print("   - README: README_EPIC_FIXVERSION.md")
        print("\nAccess at: http://localhost:5400")
    else:
        print("[FAILED] SOME TESTS FAILED")
        print("   Please check the errors above")
    print("="*60)
    
    return all_exist

if __name__ == '__main__':
    success = test_application_structure()
    exit(0 if success else 1)
