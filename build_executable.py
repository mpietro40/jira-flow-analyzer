"""
Build script for creating a standalone Windows executable for any
microservice in the Jira Analytics Suite.

Usage
-----
    # Interactive menu (no argument)
    python build_executable.py

    # Build a specific app directly
    python build_executable.py initiative_viewer

    # Build all apps
    python build_executable.py --all

    # Clean previous build first, then build
    python build_executable.py initiative_viewer --clean

Output
------
    dist/<AppName>/          — folder-mode executable (portable, no install)
        <AppName>.exe        — double-click to start the service
        README.txt           — usage notes
        _internal/           — bundled Python runtime + templates

Author : Pietro Maffi
Date   : 2026-02-24
"""

import argparse
import os
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Application registry
# ─────────────────────────────────────────────────────────────────────────────
APPS: dict = {
    'unified_dashboard': {
        'name':        'JiraAnalyticsDashboard',
        'port':        5000,
        'description': 'Central Dashboard — gateway for all Jira analytics tools',
    },
    'initiative_viewer': {
        'name':        'InitiativeViewer',
        'port':        5001,
        'description': 'Initiative Viewer — lead times and initiative hierarchy',
    },
    'epic_report': {
        'name':        'EpicReportGenerator',
        'port':        5002,
        'description': 'Epic Report Generator — comprehensive epic visualisations',
    },
    'pi_analyzer': {
        'name':        'PIAnalyzer',
        'port':        5003,
        'description': 'PI Analyzer — Program Increment metrics and progress',
    },
    'sprint_analyzer': {
        'name':        'SprintAnalyzer',
        'port':        5004,
        'description': 'Sprint Analyzer — velocity and metric analysis',
    },
    'pbc_analyzer': {
        'name':        'PBCAnalyzer',
        'port':        5005,
        'description': 'PBC Analyzer — Program Backlog Confidence',
    },
    'duplicate_detector': {
        'name':        'DuplicateDetector',
        'port':        5006,
        'description': 'Duplicate Detector — find and manage duplicate Jira issues',
    },
    'psychological_safety': {
        'name':        'PsychologicalSafetyAnalyzer',
        'port':        5007,
        'description': 'Psychological Safety Analyzer — team safety metrics',
    },
    'epic_fixversion': {
        'name':        'EpicFixVersionAnalyzer',
        'port':        5008,
        'description': 'Epic Fix Version Analyzer — fix-version commitments',
    },
}

ROOT = Path(__file__).parent.resolve()
DIST = ROOT / 'dist'
BUILD = ROOT / 'build'
TMP_LAUNCHERS = ROOT / '_tmp_launchers'   # generated entry points (gitignored)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _check_pyinstaller() -> None:
    """Abort early if PyInstaller is not available."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("ERROR: PyInstaller is not installed.")
        print("       Run:  pip install pyinstaller")
        sys.exit(1)


def _clean(app_key: str) -> None:
    """Remove previous build artefacts for one app."""
    app = APPS[app_key]
    for folder in [DIST / app['name'], BUILD / app_key]:
        if folder.exists():
            shutil.rmtree(folder)
            print(f"  Removed {folder}")


def _generate_launcher(app_key: str) -> Path:
    """
    Write a self-contained launcher script that correctly resolves templates
    both in normal Python mode and inside a PyInstaller bundle.

    We generate a *new* launcher rather than modifying the existing run.py so
    that the existing source files stay clean.
    """
    app = APPS[app_key]
    TMP_LAUNCHERS.mkdir(exist_ok=True)
    launcher = TMP_LAUNCHERS / f"run_{app_key}.py"

    # Build the source as a plain string so indentation is explicit and
    # not affected by textwrap.dedent heuristics.
    lines = [
        f'"""',
        f'Auto-generated standalone launcher for {app["name"]}.',
        f'DO NOT EDIT — re-run build_executable.py to regenerate.',
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'"""',
        f'import argparse',
        f'import os',
        f'import sys',
        f'',
        f'',
        f'def _base_path() -> str:',
        f'    """Return the runtime base directory.',
        f'',
        f'    * Normal Python  -> directory of this file (project root)',
        f'    * PyInstaller    -> sys._MEIPASS (temp extraction directory)',
        f'    """',
        f'    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):',
        f'        return sys._MEIPASS',
        f'    # When run from source, __file__ is inside _tmp_launchers/;',
        f'    # step one level up to reach the project root.',
        f'    return str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))',
        f'',
        f'',
        f'BASE = _base_path()',
        f'',
        f'# Make sure the project root is on sys.path so all imports resolve.',
        f'if BASE not in sys.path:',
        f'    sys.path.insert(0, BASE)',
        f'',
        f"os.environ['JIRA_SUITE_BASE'] = BASE",
        f'',
        f'',
        f'def create_app():',
        f'    """Build a fully-configured Flask application."""',
        f'    from flask import Flask',
        f'    from apps.{app_key}.app import blueprint',
        f'',
        f'    # When frozen, Blueprint.root_path points into the .pyc archive',
        f'    # (not a real folder).  Redirect it to the extracted datas location.',
        f'    if getattr(sys, "frozen", False):',
        f'        _app_root = os.path.join(BASE, "apps", "{app_key}")',
        f'        blueprint.root_path       = _app_root',
        f'        blueprint.template_folder = os.path.join(_app_root, "templates")',
        f'        blueprint.static_folder   = os.path.join(_app_root, "static")',
        f'',
        f'    flask_app = Flask(',
        f'        __name__,',
        f'        template_folder=os.path.join(BASE, "apps", "{app_key}", "templates"),',
        f'        static_folder=os.path.join(BASE, "apps", "{app_key}", "static"),',
        f'    )',
        f'    # Flask session requires a secret key.',
        f'    # Override via FLASK_SECRET_KEY env var if needed.',
        f"    flask_app.secret_key = os.environ.get('FLASK_SECRET_KEY', '{app_key}-jira-suite-2026')",
        f'    flask_app.register_blueprint(blueprint, url_prefix="/")',
        f'    return flask_app',
        f'',
        f'',
        f'def main():',
        f'    parser = argparse.ArgumentParser(description="{app["name"]} Launcher")',
        f'    parser.add_argument("--host", default="0.0.0.0",',
        f'                        help="Host to bind to (default: 0.0.0.0)")',
        f'    parser.add_argument("--port", type=int, default={app["port"]},',
        f'                        help="Port to run on (default: {app["port"]})")',
        f'    parser.add_argument("--debug", action="store_true",',
        f'                        help="Run Flask in debug mode (not for production)")',
        f'    parser.add_argument("--no-browser", dest="no_browser", action="store_true",',
        f'                        help="Do not open the browser automatically")',
        f'    args = parser.parse_args()',
        f'',
        f'    flask_app = create_app()',
        f'    print("")',
        f'    print("  {app["name"]}")',
        f'    print(f"  Running on  http://localhost:{{args.port}}")',
        f'    print("  Press Ctrl+C to stop")',
        f'    print("")',
        f'',        f'    if not args.no_browser:',
        f'        import threading, webbrowser',
        f'        url = f"http://localhost:{{args.port}}"',
        f'        threading.Timer(2.5, lambda: webbrowser.open(url)).start()',
        f'',        f'    if args.debug:',
        f'        flask_app.run(host=args.host, port=args.port, debug=True)',
        f'    else:',
        f'        from waitress import serve',
        f'        serve(flask_app, host=args.host, port=args.port)',
        f'',
        f'',
        f"if __name__ == '__main__':",
        f'    main()',
    ]

    launcher.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return launcher


def _collect_hidden_imports(app_key: str) -> list[str]:
    """Return the list of hidden imports for PyInstaller."""
    base = [
        # Flask stack
        'flask', 'werkzeug', 'werkzeug.security', 'werkzeug.serving',
        'jinja2', 'markupsafe', 'itsdangerous', 'click', 'blinker',
        # WSGI server
        'waitress', 'waitress.server', 'waitress.task',
        # HTTP / Jira
        'requests', 'urllib3', 'certifi',
        # Our shared modules
        'src.common.cache_manager', 'src.common.file_storage',
        'src.common.flask_utils',   'src.common.jira_client',
        # The app blueprint itself
        f'apps.{app_key}.app',
    ]

    if app_key in ('epic_report', 'initiative_viewer', 'epic_fixversion'):
        base += [
            'reportlab', 'reportlab.pdfgen', 'reportlab.pdfgen.canvas',
            'reportlab.lib', 'reportlab.lib.colors', 'reportlab.lib.pagesizes',
            'reportlab.lib.styles', 'reportlab.lib.units',
            'reportlab.platypus', 'reportlab.graphics', 'reportlab.graphics.shapes',
        ]

    return base


def _collect_datas(app_key: str) -> list[tuple[str, str]]:
    """Return PyInstaller datas tuples (source, dest_inside_bundle)."""
    app_dir = ROOT / 'apps' / app_key
    common_dir = ROOT / 'src' / 'common'

    datas = [
        # Templates and static assets
        (str(app_dir / 'templates'), f'apps/{app_key}/templates'),
        (str(app_dir / 'static'),    f'apps/{app_key}/static'),
        # Full app package so blueprint __init__ + app.py are available
        (str(app_dir),               f'apps/{app_key}'),
        # Common shared modules (needed as importable source inside bundle)
        (str(common_dir),            'src/common'),
    ]

    # apps/__init__.py — only if it exists (optional namespace package marker)
    apps_init = ROOT / 'apps' / '__init__.py'
    if apps_init.exists():
        datas.append((str(apps_init), 'apps'))

    # Optional root-level config
    pi_cfg = ROOT / 'pi_config.json'
    if pi_cfg.exists():
        datas.append((str(pi_cfg), '.'))

    return datas


def _build_app(app_key: str) -> bool:
    """Build one application.  Returns True on success."""
    app = APPS[app_key]
    sep = '=' * 70
    print(f"\n{sep}")
    print(f"  Building  :  {app['name']}  (port {app['port']})")
    print(f"  {app['description']}")
    print(sep)

    # 1 — generate entry point
    launcher = _generate_launcher(app_key)
    print(f"  Launcher   : {launcher.name}")

    # 2 — assemble PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        # Single-file mode: everything packed into one .exe.
        # On launch Python self-extracts to %TEMP%\_MEIxxxxxx\ (transparent to user).
        # Startup is ~3-5 s slower than --onedir, but the exe is fully self-contained.
        '--onefile',
        f'--name={app["name"]}',
        f'--distpath={DIST}',
        f'--workpath={BUILD / app_key}',
        '--console',
    ]

    for hi in _collect_hidden_imports(app_key):
        cmd += ['--hidden-import', hi]

    for src, dst in _collect_datas(app_key):
        if os.path.exists(src):
            cmd += ['--add-data', f'{src}{os.pathsep}{dst}']
        else:
            print(f"  [WARN] datas source not found, skipping: {src}")

    # Exclude heavy dev/test libraries that are never used at runtime
    for exc in ('pytest', 'coverage', 'pandas', 'numpy', 'scipy',
                'matplotlib', 'IPython', 'jupyter', 'tkinter', 'PyQt5'):
        cmd += ['--exclude-module', exc]

    cmd.append(str(launcher))

    # 3 — run PyInstaller
    print(f"\n  Running PyInstaller …")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            check=True,
            capture_output=False,   # stream output so user sees progress
        )
    except subprocess.CalledProcessError:
        print(f"\n  ERROR: PyInstaller failed for {app['name']}")
        return False

    # 4 — write user-facing files into the dist folder
    out_dir = DIST / app['name']
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'README.txt').write_text(_readme(app_key), encoding='utf-8')
    (out_dir / 'HOW_TO_RUN.txt').write_text(_how_to_run(app_key), encoding='utf-8')

    print(f"\n  Build complete!")
    print(f"  Executable : {DIST / app['name'] / (app['name'] + '.exe')}")
    return True


def _readme(app_key: str) -> str:
    app = APPS[app_key]
    return textwrap.dedent(f"""\
        {app['name']}
        {'=' * len(app['name'])}
        {app['description']}

        DISTRIBUTION
        ------------
        Single-file executable — just copy {app['name']}.exe anywhere and run it.
        No installation, no _internal/ folder, no Python required on the target machine.

        Note: first launch takes ~5 seconds while Python self-extracts to a temp
        folder (%TEMP%\\_MEIxxxxxx\\).  Subsequent launches from the same session
        are fast.  The temp folder is deleted automatically when the app stops.

        Quick Start
        -----------
        1. Double-click  {app['name']}.exe
        2. Open your browser at  http://localhost:{app['port']}
        3. Press Ctrl+C in the console window to stop the server.

        Command-line options
        --------------------
            {app['name']}.exe --port 8080          Change the port
            {app['name']}.exe --host 127.0.0.1     Listen on localhost only
            {app['name']}.exe --debug               Debug mode (dev only)

        Requirements
        ------------
        - Windows 10 / 11 (64-bit)
        - Internet access to reach Jira
        - No additional software installation required

        Built: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        Part of the Jira Analytics Suite  (port {app['port']})
    """)


def _how_to_run(app_key: str) -> str:
    app = APPS[app_key]
    return textwrap.dedent(f"""\
        HOW TO RUN — {app['name']}
        {'=' * (len('HOW TO RUN — ') + len(app['name']))}
        No installation required.

        STEP 1  Double-click  {app['name']}.exe
        STEP 2  Wait ~5 seconds for the server to start
                 (you will see a console window — leave it open)
        STEP 3  Open your browser and go to:

                    http://localhost:{app['port']}

        STEP 4  When finished, close the console window to stop the server.

        ─────────────────────────────────────────────────────────
        TROUBLESHOOTING

        "Windows protected your PC" warning
          → Click "More info", then "Run anyway"
          → This is a normal Windows SmartScreen warning for unsigned apps.

        The page does not load
          → Make sure the console window is still open.
          → Try refreshing after a few more seconds.

        "Port already in use" error in the console
          → Another instance is already running.  Close it first via Task Manager,
            or use a different port:
                {app['name']}.exe --port 5099
            then open  http://localhost:5099

        ─────────────────────────────────────────────────────────
        Need help?  Contact your IT contact or the app owner.
    """)


def _interactive_menu() -> str:
    """Show a numbered menu and return the chosen app_key."""
    print()
    print("  Jira Analytics Suite — Build Executable")
    print("  " + "─" * 50)
    keys = list(APPS)
    for i, key in enumerate(keys, 1):
        app = APPS[key]
        print(f"  {i:2d}.  {app['name']:<35} port {app['port']}")
    print(f"  {len(keys)+1:2d}.  Build ALL applications")
    print()

    while True:
        raw = input("  Enter number: ").strip()
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(keys):
                return keys[n - 1]
            if n == len(keys) + 1:
                return '__all__'
        print("  Invalid selection, try again.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description='Build standalone executables for Jira Analytics Suite microservices.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='\n'.join(
            f"  {k:<25} {v['name']} (port {v['port']})"
            for k, v in APPS.items()
        ),
    )
    parser.add_argument(
        'app',
        nargs='?',
        choices=list(APPS) + ['--all'],
        metavar='APP_NAME',
        help='App key to build (omit for interactive menu)',
    )
    parser.add_argument(
        '--all', dest='build_all', action='store_true',
        help='Build every application',
    )
    parser.add_argument(
        '--clean', action='store_true',
        help='Remove previous build artefacts before building',
    )
    args = parser.parse_args()

    _check_pyinstaller()

    # Determine what to build
    if args.build_all:
        targets = list(APPS)
    elif args.app:
        targets = [args.app]
    else:
        choice = _interactive_menu()
        targets = list(APPS) if choice == '__all__' else [choice]

    # Clean if requested
    if args.clean:
        print("\nCleaning previous artefacts …")
        for t in targets:
            _clean(t)

    # Build
    results: dict[str, bool] = {}
    for app_key in targets:
        results[app_key] = _build_app(app_key)

    # Summary
    print()
    print("=" * 70)
    print("  BUILD SUMMARY")
    print("=" * 70)
    ok  = [k for k, v in results.items() if v]
    err = [k for k, v in results.items() if not v]
    for k in ok:
        print(f"  OK    {APPS[k]['name']}")
    for k in err:
        print(f"  FAIL  {APPS[k]['name']}")
    print()
    if err:
        print(f"  {len(err)} build(s) failed.")
        return 1
    print(f"  All {len(ok)} build(s) succeeded.")
    print(f"  Output directory: {DIST}")
    print()
    print("  Each .exe is fully self-contained — copy or share it as a single file.")
    print("  First launch takes ~5 s while Python extracts to %TEMP%.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
