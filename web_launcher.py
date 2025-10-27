"""
Web-based Launcher for Render.com Deployment
Automatically starts the unified Jira Analytics Suite.

Author: Pietro Maffi
Purpose: Deploy-friendly launcher for Render.com
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('WebLauncher')

def main():
    """Main launcher function for web deployment."""
    logger.info("🚀 Starting Jira Analytics Suite for web deployment...")
    
    # Import and run the unified web application
    try:
        from main_app import app
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"🌐 Starting unified web application on port {port}")
        app.run(debug=False, host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"❌ Error starting web application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists("main_app.py"):
        logger.error("❌ Error: main_app.py not found in current directory")
        logger.error(f"Current directory: {os.getcwd()}")
        sys.exit(1)
    
    main()