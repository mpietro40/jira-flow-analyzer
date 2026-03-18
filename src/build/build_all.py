"""
Master Build Script for Jira Analytics Suite
Creates Windows executables for all 9 applications

@author: Pietro Maffi
@date: 2026-02-20
@purpose: Automated build system for creating production-ready executables
"""
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Application definitions
APPS = {
    'unified_dashboard': {
        'name': 'JiraAnalyticsDashboard',
        'port': 5000,
        'script': 'apps/unified_dashboard/run.py',
        'templates': 'apps/unified_dashboard/templates',
        'static': 'apps/unified_dashboard/static',
        'description': 'Central dashboard and gateway for all Jira analytics tools'
    },
    'initiative_viewer': {
        'name': 'InitiativeViewer',
        'port': 5001,
        'script': 'apps/initiative_viewer/run.py',
        'templates': 'apps/initiative_viewer/templates',
        'static': 'apps/initiative_viewer/static',
        'description': 'View and analyze initiative lead times and metrics'
    },
    'epic_report': {
        'name': 'EpicReportGenerator',
        'port': 5002,
        'script': 'apps/epic_report/run.py',
        'templates': 'apps/epic_report/templates',
        'static': 'apps/epic_report/static',
        'description': 'Generate comprehensive epic reports with visualizations'
    },
    'pi_analyzer': {
        'name': 'PIAnalyzer',
        'port': 5003,
        'script': 'apps/pi_analyzer/run.py',
        'templates': 'apps/pi_analyzer/templates',
        'static': 'apps/pi_analyzer/static',
        'description': 'Analyze Program Increment metrics and progress'
    },
    'sprint_analyzer': {
        'name': 'SprintAnalyzer',
        'port': 5004,
        'script': 'apps/sprint_analyzer/run.py',
        'templates': 'apps/sprint_analyzer/templates',
        'static': 'apps/sprint_analyzer/static',
        'description': 'Sprint velocity and metric analysis tool'
    },
    'pbc_analyzer': {
        'name': 'PBCAnalyzer',
        'port': 5005,
        'script': 'apps/pbc_analyzer/run.py',
        'templates': 'apps/pbc_analyzer/templates',
        'static': 'apps/pbc_analyzer/static',
        'description': 'Program Backlog Confidence analyzer'
    },
    'duplicate_detector': {
        'name': 'DuplicateDetector',
        'port': 5006,
        'script': 'apps/duplicate_detector/run.py',
        'templates': 'apps/duplicate_detector/templates',
        'static': 'apps/duplicate_detector/static',
        'description': 'Detect and manage duplicate Jira issues'
    },
    'psychological_safety': {
        'name': 'PsychologicalSafetyAnalyzer',
        'port': 5007,
        'script': 'apps/psychological_safety/run.py',
        'templates': 'apps/psychological_safety/templates',
        'static': 'apps/psychological_safety/static',
        'description': 'Analyze team psychological safety metrics'
    },
    'epic_fixversion': {
        'name': 'EpicFixVersionAnalyzer',
        'port': 5008,
        'script': 'apps/epic_fixversion/run.py',
        'templates': 'apps/epic_fixversion/templates',
        'static': 'apps/epic_fixversion/static',
        'description': 'Analyze epic fix versions and commitments'
    }
}

class BuildSystem:
    """Manages building of all Jira Analytics applications"""
    
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).parent.parent.parent
        self.build_dir = self.root_dir / 'build'
        self.dist_dir = self.root_dir / 'dist'
        self.specs_dir = self.root_dir / 'src' / 'build' / 'specs'
        
        # Ensure directories exist
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        
    def clean(self, app_name=None):
        """Clean previous build artifacts"""
        print(f"\n🧹 Cleaning build artifacts...")
        
        if app_name:
            # Clean specific app
            app_build = self.build_dir / app_name
            app_dist = self.dist_dir / APPS[app_name]['name']
            
            if app_build.exists():
                shutil.rmtree(app_build)
                print(f"   Removed {app_build}")
            
            if app_dist.exists():
                shutil.rmtree(app_dist)
                print(f"   Removed {app_dist}")
        else:
            # Clean all
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                print(f"   Removed {self.build_dir}")
            
            if self.dist_dir.exists():
                shutil.rmtree(self.dist_dir)
                print(f"   Removed {self.dist_dir}")
        
        print("✅ Cleanup complete")
    
    def generate_spec_file(self, app_key):
        """Generate PyInstaller spec file for an application"""
        app = APPS[app_key]
        spec_file = self.specs_dir / f"{app_key}.spec"
        
        # Common hidden imports
        hidden_imports = [
            # Flask and web framework
            "'flask'",
            "'werkzeug.security'",
            "'werkzeug.serving'",
            "'jinja2'",
            "'markupsafe'",
            "'itsdangerous'",
            "'click'",
            "'blinker'",
            
            # Waitress WSGI server
            "'waitress'",
            "'waitress.server'",
            "'waitress.task'",
            
            # HTTP and API
            "'requests'",
            "'urllib3'",
            "'certifi'",
            
            # Our common modules
            "'src.common.jira_client'",
            "'src.common.config_loader'",
            "'src.common.utils'",
            "'src.common.pdf_generator'",
            "'src.common.validators'",
        ]
        
        # App-specific imports based on functionality
        if app_key in ['epic_report', 'initiative_viewer', 'epic_fixversion']:
            hidden_imports.extend([
                # PDF generation
                "'reportlab'",
                "'reportlab.pdfgen'",
                "'reportlab.pdfgen.canvas'",
                "'reportlab.lib'",
                "'reportlab.lib.colors'",
                "'reportlab.lib.pagesizes'",
                "'reportlab.lib.styles'",
                "'reportlab.lib.units'",
                "'reportlab.platypus'",
                "'reportlab.graphics'",
                "'reportlab.graphics.shapes'",
                "'reportlab.graphics.charts'",
                "'PIL'",
                "'PIL.Image'",
            ])
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for {app['name']}
Auto-generated by build_all.py

Application: {app['description']}
Port: {app['port']}
"""
import sys
import os
from pathlib import Path

block_cipher = None

# Get the path to the project root
root_dir = Path(r"{self.root_dir}").resolve()

a = Analysis(
    [str(root_dir / "{app['script']}")],
    pathex=[str(root_dir)],
    binaries=[],
    datas=[
        # Application templates and static files
        (str(root_dir / "{app['templates']}"), "apps/{app_key}/templates"),
        (str(root_dir / "{app['static']}"), "apps/{app_key}/static"),

        # Full app package so blueprint template_folder resolves inside bundle
        (str(root_dir / "apps" / "{app_key}"), "apps/{app_key}"),

        # Common shared modules
        (str(root_dir / "src" / "common"), "src/common"),

        # Root-level JSON config (if present)
        *([(str(root_dir / "pi_config.json"), ".")] if (root_dir / "pi_config.json").exists() else []),
    ],
    hiddenimports=[
        {", ".join(hidden_imports)}
    ],
    hookspath=[str(root_dir / "src" / "build" / "hooks")],
    hooksconfig={{}},
    runtime_hooks=[str(root_dir / "src" / "build" / "runtime_hook.py")],
    excludes=[
        # Testing frameworks
        'pytest',
        'pytest-flask',
        'pytest-cov',
        'pytest-mock',
        'unittest',
        'nose',
        'coverage',
        
        # Heavy libraries not used
        'pandas',
        'numpy',
        'scipy',
        'matplotlib',
        'seaborn',
        'bokeh',
        'plotly',
        
        # Development tools
        'IPython',
        'jupyter',
        'notebook',
        'black',
        'pylint',
        'mypy',
        
        # GUI frameworks
        'tkinter',
        'turtle',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        
        # Other unused
        'test',
        'asyncio',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="{app['name']}",
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
    icon=None,
)
'''
        
        # Write spec file
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"   Created {spec_file.name}")
        return spec_file
    
    def build_app(self, app_key):
        """Build a single application"""
        app = APPS[app_key]
        print(f"\n{'='*70}")
        print(f"🚀 Building {app['name']} (Port {app['port']})")
        print(f"   {app['description']}")
        print(f"{'='*70}")
        
        # Generate spec file
        spec_file = self.generate_spec_file(app_key)
        
        # Build command
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]
        
        try:
            # Run PyInstaller
            result = subprocess.run(
                cmd,
                cwd=str(self.root_dir),
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Build completed successfully!")
            print(f"📁 Executable location: dist/{app['name']}.exe")
            
            # Create app-specific README
            self.create_app_readme(app_key)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed for {app['name']}")
            print(f"Error: {e.stderr}")
            return False
    
    def create_app_readme(self, app_key):
        """Create README for a specific application"""
        app = APPS[app_key]
        
        readme_content = f"""
# {app['name']}

{app['description']}

## Quick Start

1. Double-click `{app['name']}.exe` to start the application
2. The server will start on http://localhost:{app['port']}
3. Open your web browser and navigate to http://localhost:{app['port']}

## Configuration

The application looks for configuration in the following locations:
- Jira credentials: Environment variables or config files
- Application settings: See the web interface

## Port Configuration

Default Port: {app['port']}

If this port is already in use, you can change it by:
- Setting the PORT environment variable
- Using command line arguments (if supported)

## System Requirements

- Windows 10 or later
- Internet connection (for Jira API access)
- At least 2GB RAM
- ~100MB disk space

## Troubleshooting

### Application won't start
- Check if port {app['port']} is already in use
- Run as administrator if needed
- Check Windows Firewall settings

### Cannot connect to Jira
- Verify your Jira credentials
- Check internet connection
- Ensure Jira server is accessible

### Performance issues
- Close other applications
- Check system resources
- Reduce concurrent requests

## Integration with Dashboard

This application is part of the Jira Analytics Suite and can be accessed through:
- Direct URL: http://localhost:{app['port']}
- Unified Dashboard: http://localhost:5000

## Support

For technical support, contact your system administrator.

## Version Information

Built: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Application Key: {app_key}
Port: {app['port']}

## License

Internal use only. All rights reserved.
"""
        
        readme_path = self.dist_dir / f"{app['name']}_README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"📝 Created {readme_path.name}")
    
    def create_master_readme(self):
        """Create master README for all applications"""
        readme_content = f"""
# Jira Analytics Suite - Complete Package

Built: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Applications Included

"""
        for i, (key, app) in enumerate(APPS.items(), 1):
            readme_content += f"{i}. **{app['name']}** (Port {app['port']})\n"
            readme_content += f"   {app['description']}\n"
            readme_content += f"   Executable: {app['name']}.exe\n\n"
        
        readme_content += """
## Getting Started

### Quick Start - Launch Dashboard
1. Run `JiraAnalyticsDashboard.exe` first
2. Open http://localhost:5000 in your browser
3. Access all tools from the centralized dashboard

### Individual Applications
Each application can run independently:
1. Double-click the desired .exe file
2. Open the URL shown in the console
3. Use the application directly

## Starting All Services

To run the complete suite:

1. Start the Unified Dashboard:
   ```
   JiraAnalyticsDashboard.exe
   ```

2. Start individual services (in separate terminals):
   ```
   InitiativeViewer.exe
   EpicReportGenerator.exe
   PIAnalyzer.exe
   SprintAnalyzer.exe
   PBCAnalyzer.exe
   DuplicateDetector.exe
   PsychologicalSafetyAnalyzer.exe
   EpicFixVersionAnalyzer.exe
   ```

3. Access the dashboard at: http://localhost:5000

## Port Configuration

| Application              | Port | URL                       |
|--------------------------|------|---------------------------|
| Unified Dashboard        | 5000 | http://localhost:5000     |
| Initiative Viewer        | 5001 | http://localhost:5001     |
| Epic Report Generator    | 5002 | http://localhost:5002     |
| PI Analyzer              | 5003 | http://localhost:5003     |
| Sprint Analyzer          | 5004 | http://localhost:5004     |
| PBC Analyzer             | 5005 | http://localhost:5005     |
| Duplicate Detector       | 5006 | http://localhost:5006     |
| Psychological Safety     | 5007 | http://localhost:5007     |
| Epic Fix Version         | 5008 | http://localhost:5008     |

## System Requirements

- Windows 10 or later (64-bit)
- 4GB RAM minimum (8GB recommended)
- ~500MB disk space for all applications
- Internet connection for Jira API access
- Modern web browser (Chrome, Firefox, Edge)

## Configuration

### Jira Credentials
Set environment variables or use the web interface:
- JIRA_SERVER
- JIRA_EMAIL
- JIRA_TOKEN

### Application Settings
Each application has its own configuration through:
- Web interface
- Config files (if present)
- Command line arguments

## Troubleshooting

### Port Already in Use
If a port is busy:
1. Close the application using that port
2. Change the port in application settings
3. Use Task Manager to free the port

### Multiple Instances
- Only one instance per application can run
- Check Task Manager for running processes
- Kill existing processes if needed

### Performance
- Start only needed applications
- Close unused browser tabs
- Monitor system resources

### Firewall Issues
- Allow applications through Windows Firewall
- Run as administrator if needed
- Check antivirus settings

## Architecture

The suite uses a microservices architecture:
- Each application runs independently
- Unified Dashboard provides central access
- Applications can run standalone or together
- Health monitoring via dashboard

## Support

For technical assistance:
1. Check individual application READMEs
2. Contact your system administrator
3. Review application logs

## License

Internal use only. All rights reserved.

"""
        
        readme_path = self.dist_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"\n📝 Created master README.txt")
    
    def build_all(self):
        """Build all applications"""
        print(f"\n{'='*70}")
        print("🏗️  JIRA ANALYTICS SUITE - MASTER BUILD")
        print(f"{'='*70}")
        print(f"Building {len(APPS)} applications...")
        print(f"Root directory: {self.root_dir}")
        print(f"{'='*70}")
        
        success_count = 0
        failed_apps = []
        
        for app_key in APPS.keys():
            if self.build_app(app_key):
                success_count += 1
            else:
                failed_apps.append(app_key)
        
        # Create master README
        if success_count > 0:
            self.create_master_readme()
        
        # Summary
        print(f"\n{'='*70}")
        print("📊 BUILD SUMMARY")
        print(f"{'='*70}")
        print(f"✅ Successful: {success_count}/{len(APPS)}")
        
        if failed_apps:
            print(f"❌ Failed: {len(failed_apps)}")
            print("Failed applications:")
            for app in failed_apps:
                print(f"   - {APPS[app]['name']}")
        else:
            print("🎉 All applications built successfully!")
        
        print(f"\n📁 Output directory: {self.dist_dir}")
        print(f"{'='*70}")
        
        return len(failed_apps) == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Build Jira Analytics Suite executables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available applications:
{chr(10).join(f"  - {key}: {app['name']} (Port {app['port']})" for key, app in APPS.items())}

Examples:
  # Build all applications
  python build_all.py
  
  # Build specific application
  python build_all.py --app unified_dashboard
  
  # Clean and rebuild
  python build_all.py --clean
  
  # Clean specific app
  python build_all.py --app initiative_viewer --clean
"""
    )
    
    parser.add_argument(
        '--app',
        choices=list(APPS.keys()),
        help='Build specific application only'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build artifacts before building'
    )
    
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Only clean, do not build'
    )
    
    args = parser.parse_args()
    
    # Create build system
    build_system = BuildSystem()
    
    try:
        # Clean if requested
        if args.clean or args.clean_only:
            build_system.clean(args.app)
        
        # Exit if clean-only
        if args.clean_only:
            return 0
        
        # Build
        if args.app:
            # Build single app
            success = build_system.build_app(args.app)
            return 0 if success else 1
        else:
            # Build all apps
            success = build_system.build_all()
            return 0 if success else 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Build interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
