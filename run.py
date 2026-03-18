"""
Jira Analytics Suite - Flexible Launcher

Run apps in different modes:
  1. Monolithic: All apps in ONE process (recommended)
  2. Microservices: Each app in separate process
  3. Single App: Run just one app for testing

Usage:
    python run.py                      # Interactive menu
    python run.py --monolithic         # All apps in one (port 5000)
    python run.py --microservices      # All apps separate (ports 5000-5011)
    python run.py --app lead_time      # Run single app

Author: Pietro Maffi
"""

import sys
import argparse
from pathlib import Path
import subprocess
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Define all apps
APPS = {
    'dashboard': {'name': 'Unified Dashboard', 'port': 5000, 'script': 'apps/unified_dashboard/app.py'},
    'lead_time': {'name': 'Lead Time Analyzer', 'port': 5001, 'script': 'apps/lead_time_analyzer/app.py'},
    'initiative': {'name': 'Initiative Viewer', 'port': 5011, 'script': 'apps/initiative_viewer/app.py'},
    'epic': {'name': 'Epic Report', 'port': 5002, 'script': 'apps/epic_report/app.py'},
    'pi': {'name': 'PI Analyzer', 'port': 5003, 'script': 'apps/pi_analyzer/app.py'},
    'sprint': {'name': 'Sprint Analyzer', 'port': 5004, 'script': 'apps/sprint_analyzer/app.py'},
    'pbc': {'name': 'PBC Analyzer', 'port': 5005, 'script': 'apps/pbc_analyzer/app.py'},
    'duplicate': {'name': 'Duplicate Detector', 'port': 5006, 'script': 'apps/duplicate_detector/app.py'},
    'safety': {'name': 'Psychological Safety', 'port': 5007, 'script': 'apps/psychological_safety/app.py'},
    'fixversion': {'name': 'Epic Fix Version', 'port': 5008, 'script': 'apps/epic_fixversion/app.py'},
}


def run_monolithic():
    """
    Run in monolithic mode - import all apps into unified dashboard.
    All functionality served from ONE Flask app on port 5000.
    """
    print("="*80)
    print("🚀 Starting MONOLITHIC MODE")
    print("="*80)
    print("All apps served from: http://localhost:5000")
    print("="*80)
    
    # Import and run the unified dashboard
    # It will handle all routing internally
    from apps.unified_dashboard.app import app, main
    main()


def run_microservices():
    """
    Run in microservices mode - start each app in separate process.
    Each app runs on its own port.
    """
    print("="*80)
    print("🚀 Starting MICROSERVICES MODE")
    print("="*80)
    print(f"Starting {len(APPS)} services...")
    print("="*80)
    
    processes = []
    
    for app_id, app_info in APPS.items():
        print(f"Starting {app_info['name']} on port {app_info['port']}...")
        try:
            process = subprocess.Popen(
                [sys.executable, app_info['script'], '--no-browser'],
                cwd=str(project_root),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            processes.append({
                'name': app_info['name'],
                'port': app_info['port'],
                'process': process
            })
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    print("="*80)
    print(f"✅ Started {len(processes)} services")
    print("Main Dashboard: http://localhost:5000")
    print("="*80)
    print("Press Ctrl+C to stop all services")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all services...")
        for p in processes:
            p['process'].terminate()


def run_single_app(app_id):
    """Run a single app for testing."""
    if app_id not in APPS:
        print(f"❌ Unknown app: {app_id}")
        print(f"Available apps: {', '.join(APPS.keys())}")
        return
    
    app_info = APPS[app_id]
    print(f"🚀 Starting {app_info['name']} on port {app_info['port']}")
    print(f"🔗 Access at: http://localhost:{app_info['port']}")
    
    subprocess.run([sys.executable, app_info['script']])


def interactive_menu():
    """Show interactive menu."""
    print("="*80)
    print("Jira Analytics Suite - Launcher")
    print("="*80)
    print("Choose run mode:")
    print("  1. Monolithic (recommended) - All apps in ONE process")
    print("  2. Microservices - Each app separate")
    print("  3. Single App - Run one app for testing")
    print("="*80)
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == '1':
        run_monolithic()
    elif choice == '2':
        run_microservices()
    elif choice == '3':
        print("\nAvailable apps:")
        for i, (app_id, app_info) in enumerate(APPS.items(), 1):
            print(f"  {i}. {app_info['name']} ({app_id})")
        app_choice = input("\nEnter app name: ").strip().lower()
        run_single_app(app_choice)
    else:
        print("Invalid choice")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Jira Analytics Suite Launcher')
    parser.add_argument('--monolithic', action='store_true', help='Run in monolithic mode (default)')
    parser.add_argument('--microservices', action='store_true', help='Run in microservices mode')
    parser.add_argument('--app', type=str, help='Run single app')
    
    args = parser.parse_args()
    
    if args.microservices:
        run_microservices()
    elif args.app:
        run_single_app(args.app)
    elif args.monolithic or len(sys.argv) == 1:
        # Default to monolithic if no args provided
        run_monolithic()
    else:
        interactive_menu()


if __name__ == '__main__':
    main()
