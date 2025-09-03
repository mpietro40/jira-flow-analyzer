"""
Jira Analytics Suite Launcher
Choose between running individual applications or the unified suite.

Author: Pietro Maffi
Purpose: Easy launcher for all applications
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Launcher')

def print_banner():
    """Print application banner."""
    print("\n" + "="*60)
    print("🚀 JIRA ANALYTICS SUITE LAUNCHER")
    print("="*60)
    print("Choose how you want to run the applications:")
    print()

def print_menu():
    """Print menu options."""
    print("1. 🌟 Unified Suite (All apps in one - RECOMMENDED)")
    print("   └─ Access all tools from a single dashboard")
    print("   └─ Port: 5000")
    print()
    print("2. 📊 Lead Time Analyzer (Individual)")
    print("   └─ Flow metrics and cycle time analysis")
    print("   └─ Port: 5100")
    print()
    print("3. 📈 PI Analyzer (Individual)")
    print("   └─ Product Increment analysis")
    print("   └─ Port: 5300")
    print()
    print("4. 🏃 Sprint Analyzer (Individual)")
    print("   └─ Sprint forecasting and capacity analysis")
    print("   └─ Port: 5200")
    print()
    print("5. 📋 Epic Analyzer (Individual)")
    print("   └─ Epic estimate management")
    print("   └─ Port: 5100 (shares with Lead Time)")
    print()
    print("6. 🎯 Generate Presentation Only")
    print("   └─ Create PDF presentation without web interface")
    print()
    print("0. ❌ Exit")
    print()

def run_application(script_name, app_name, port=None):
    """Run a specific application."""
    try:
        logger.info(f"🚀 Starting {app_name}...")
        if port:
            print(f"🌐 {app_name} will be available at: http://localhost:{port}")
        print("📝 Press Ctrl+C to stop the application")
        print("-" * 50)
        
        # Run the application
        subprocess.run([sys.executable, script_name], check=True)
        
    except KeyboardInterrupt:
        logger.info(f"🛑 {app_name} stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error running {app_name}: {e}")
    except FileNotFoundError:
        logger.error(f"❌ Script not found: {script_name}")
        logger.error("Make sure you're running this from the correct directory")

def generate_presentation():
    """Generate presentation without web interface."""
    try:
        logger.info("🎨 Generating presentation...")
        from presentation_generator import main
        main()
        logger.info("✅ Presentation generated successfully!")
    except Exception as e:
        logger.error(f"❌ Error generating presentation: {e}")

def main():
    """Main launcher function."""
    while True:
        print_banner()
        print_menu()
        
        try:
            choice = input("Enter your choice (0-6): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
                
            elif choice == "1":
                run_application("main_app.py", "Unified Jira Analytics Suite", 5000)
                
            elif choice == "2":
                run_application("app.py", "Lead Time Analyzer", 5100)
                
            elif choice == "3":
                run_application("pi_web_app.py", "PI Analyzer", 5300)
                
            elif choice == "4":
                run_application("sprint_web_app.py", "Sprint Analyzer", 5200)
                
            elif choice == "5":
                print("ℹ️  Epic Analyzer uses the same interface as Lead Time Analyzer")
                print("   Navigate to the Epic Analysis section once the app loads.")
                run_application("app.py", "Epic Analyzer (via Lead Time App)", 5100)
                
            elif choice == "6":
                generate_presentation()
                input("Press Enter to continue...")
                
            else:
                print("❌ Invalid choice. Please enter a number between 0-6.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists("main_app.py"):
        print("❌ Error: Please run this script from the JiraObeya/PerseusLeadTime directory")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    main()