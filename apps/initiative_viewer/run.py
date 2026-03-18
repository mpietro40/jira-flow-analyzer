"""
Standalone launcher for Initiative Viewer application.

Usage:
    python run.py                    # Start on default port 5001
    python run.py --port 5005        # Start on custom port
    python run.py --debug            # Start in debug mode
    python run.py --no-browser       # Don't open browser automatically
"""

import argparse

from flask import Flask
from waitress import serve

from apps.initiative_viewer.app import blueprint


def create_app():
    """Create standalone Flask app and register initiative blueprint."""
    app = Flask(__name__)
    app.register_blueprint(blueprint, url_prefix='/')
    return app


def main():
    """Run initiative viewer as standalone app."""
    parser = argparse.ArgumentParser(description='Initiative Viewer Launcher')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--no-browser', action='store_true', help='Compatibility flag (unused)')
    args = parser.parse_args()

    app = create_app()
    if args.debug:
        app.run(host=args.host, port=args.port, debug=True)
    else:
        serve(app, host=args.host, port=args.port)

if __name__ == '__main__':
    main()
