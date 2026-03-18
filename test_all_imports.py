"""
Test all application imports
Verifies that all 9 applications can be imported successfully
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import(module_path, app_name, symbol_name):
    """Test importing a single application symbol."""
    try:
        exec(f"from {module_path} import {symbol_name}")
        print(f"✅ {app_name:25} imports successfully")
        return True
    except Exception as e:
        print(f"❌ {app_name:25} FAILED: {str(e)[:50]}")
        return False

def main():
    """Test all application imports"""
    print("="*70)
    print("  Testing All Application Imports")
    print("="*70)
    print()
    
    apps = [
        ('apps.unified_dashboard.app', 'Unified Dashboard', 'app'),
        ('apps.initiative_viewer.app', 'Initiative Viewer', 'blueprint'),
        ('apps.epic_report.app', 'Epic Report', 'blueprint'),
        ('apps.pi_analyzer.app', 'PI Analyzer', 'blueprint'),
        ('apps.sprint_analyzer.app', 'Sprint Analyzer', 'blueprint'),
        ('apps.pbc_analyzer.app', 'PBC Analyzer', 'blueprint'),
        ('apps.duplicate_detector.app', 'Duplicate Detector', 'blueprint'),
        ('apps.psychological_safety.app', 'Psychological Safety', 'blueprint'),
        ('apps.epic_fixversion.app', 'Epic Fix Version', 'blueprint'),
    ]
    
    results = []
    for module_path, app_name, symbol_name in apps:
        results.append(test_import(module_path, app_name, symbol_name))
    
    print()
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"  Results: {passed}/{total} applications passed")
    print("="*70)
    
    if passed == total:
        print()
        print("🎉 All applications can be imported successfully!")
        print("✅ Import fix is complete and working")
        return 0
    else:
        print()
        print("⚠️  Some applications failed to import")
        return 1

if __name__ == '__main__':
    sys.exit(main())
