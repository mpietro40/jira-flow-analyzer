# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\a788055\\GITREPO\\JiraObeya\\JiraAnalyzerSuite\\_tmp_launchers\\run_initiative_viewer.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\a788055\\GITREPO\\JiraObeya\\JiraAnalyzerSuite\\apps\\initiative_viewer\\templates', 'apps/initiative_viewer/templates'), ('C:\\Users\\a788055\\GITREPO\\JiraObeya\\JiraAnalyzerSuite\\apps\\initiative_viewer\\static', 'apps/initiative_viewer/static'), ('C:\\Users\\a788055\\GITREPO\\JiraObeya\\JiraAnalyzerSuite\\apps\\initiative_viewer', 'apps/initiative_viewer'), ('C:\\Users\\a788055\\GITREPO\\JiraObeya\\JiraAnalyzerSuite\\src\\common', 'src/common'), ('C:\\Users\\a788055\\GITREPO\\JiraObeya\\JiraAnalyzerSuite\\pi_config.json', '.')],
    hiddenimports=['flask', 'werkzeug', 'werkzeug.security', 'werkzeug.serving', 'jinja2', 'markupsafe', 'itsdangerous', 'click', 'blinker', 'waitress', 'waitress.server', 'waitress.task', 'requests', 'urllib3', 'certifi', 'src.common.cache_manager', 'src.common.file_storage', 'src.common.flask_utils', 'src.common.jira_client', 'apps.initiative_viewer.app', 'reportlab', 'reportlab.pdfgen', 'reportlab.pdfgen.canvas', 'reportlab.lib', 'reportlab.lib.colors', 'reportlab.lib.pagesizes', 'reportlab.lib.styles', 'reportlab.lib.units', 'reportlab.platypus', 'reportlab.graphics', 'reportlab.graphics.shapes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'coverage', 'pandas', 'numpy', 'scipy', 'matplotlib', 'IPython', 'jupyter', 'tkinter', 'PyQt5'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InitiativeViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
