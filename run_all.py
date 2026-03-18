#!/usr/bin/env python3
"""
Run all Jira Analyzer Suite applications
Starts all 10 microservices in separate processes
"""

import subprocess
import sys
from pathlib import Path
import time
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Application definitions
APPS = [
    {'name': 'Unified Dashboard', 'port': 5000, 'script': 'apps/unified_dashboard/app.py'},
    {'name': 'Lead Time Analyzer', 'port': 5001, 'script': 'apps/lead_time_analyzer/app.py'},
    {'name': 'Initiative Viewer', 'port': 5011, 'script': 'apps/initiative_viewer/app.py'},
    {'name': 'Epic Report', 'port': 5002, 'script': 'apps/epic_report/app.py'},
    {'name': 'PI Analyzer', 'port': 5003, 'script': 'apps/pi_analyzer/app.py'},
    {'name': 'Sprint Analyzer', 'port': 5004, 'script': 'apps/sprint_analyzer/app.py'},
    {'name': 'PBC Analyzer', 'port': 5005, 'script': 'apps/pbc_analyzer/app.py'},
    {'name': 'Duplicate Detector', 'port': 5006, 'script': 'apps/duplicate_detector/app.py'},
    {'name': 'Psychological Safety', 'port': 5007, 'script': 'apps/psychological_safety/app.py'},
    {'name': 'Epic Fix Version', 'port': 5008, 'script': 'apps/epic_fixversion/app.py'},
]

def run_all():
    """Run all applications"""
    processes = []
    
    print("="*70)
    print("  Starting Jira Analyzer Suite - All Applications")
    print("="*70)
    print()
    
    for app in APPS:
        print(f"Starting {app['name']} on port {app['port']}...")
        
        try:
            # Start process in background
            process = subprocess.Popen(
                [sys.executable, app['script']],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            processes.append({
                'name': app['name'],
                'port': app['port'],
                'process': process
            })
            time.sleep(1)  # Wait a bit between starts
            
        except Exception as e:
            print(f"  ❌ Failed to start {app['name']}: {e}")
            continue
    
    print()
    print("="*70)
    print(f"  ✅ Started {len(processes)} applications")
    print("="*70)
    print()
    print("Access the applications:")
    print()
    
    for p in processes:
        print(f"  {p['name']:25} http://localhost:{p['port']}")
    
    print()
    print("Main Dashboard: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop all services")
    print("="*70)
    
    try:
        # Wait for Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("Stopping all services...")
        for p in processes:
            p['process'].terminate()
        print("All services stopped.")

if __name__ == '__main__':
    run_all()
