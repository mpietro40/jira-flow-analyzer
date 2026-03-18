# Jira Analytics Suite - Build System

Comprehensive build system for creating Windows executables for all 9 Jira Analytics applications.

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Build Commands](#build-commands)
- [Applications](#applications)
- [Build Process](#build-process)
- [Output Structure](#output-structure)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

This build system uses **PyInstaller** to create standalone Windows executables for all applications in the Jira Analytics Suite. Each application is packaged with all its dependencies, templates, static files, and shared libraries.

### Features

✅ **Automated Builds**: Build all 9 applications with a single command  
✅ **Individual Builds**: Build specific applications when needed  
✅ **Clean Builds**: Remove old artifacts before building  
✅ **Auto-generated Specs**: Dynamic PyInstaller spec file generation  
✅ **Documentation**: Automatic README generation for each app  
✅ **Optimized**: Excludes test frameworks and unused dependencies  
✅ **Production-Ready**: Includes Waitress WSGI server for all apps  

## Requirements

### Software Requirements
- **Python 3.8 - 3.11**
- **PyInstaller 5.0+**
- **All application dependencies** (see requirements.txt)

### System Requirements
- **Windows 10 or later** (64-bit)
- **4GB RAM minimum** (8GB recommended)
- **2GB free disk space** (for build artifacts)
- **Virtual environment** (recommended)

### Install PyInstaller

```bash
# Inside your virtual environment
pip install pyinstaller

# Verify installation
pyinstaller --version
```

## Quick Start

### Build All Applications (Recommended)

**Windows:**
```batch
build_all_apps.bat
```

**Python:**
```bash
python src\build\build_all.py
```

This will:
1. Generate PyInstaller spec files for all 9 apps
2. Build executables for each application
3. Create README files for each app
4. Generate master README with suite information
5. Place all executables in `dist/` folder

### Build Single Application

**Windows:**
```batch
build_single_app.bat unified_dashboard
```

**Python:**
```bash
python src\build\build_all.py --app unified_dashboard
```

### Clean Build Artifacts

**Windows:**
```batch
clean_build.bat
```

**Python:**
```bash
python src\build\build_all.py --clean-only
```

## Build Commands

### Master Build Script

**Location:** `src/build/build_all.py`

```bash
# Build all applications
python src\build\build_all.py

# Build specific application
python src\build\build_all.py --app [app_name]

# Clean before building
python src\build\build_all.py --clean

# Clean specific app
python src\build\build_all.py --app [app_name] --clean

# Clean only (no build)
python src\build\build_all.py --clean-only
```

### Batch Scripts (Windows)

```batch
# Build all applications
build_all_apps.bat

# Build single application
build_single_app.bat [app_name]

# Clean build artifacts
clean_build.bat
```

## Applications

The build system supports all 9 applications:

| Application Key         | Executable Name               | Port | Description                          |
|-------------------------|-------------------------------|------|--------------------------------------|
| unified_dashboard       | JiraAnalyticsDashboard.exe    | 5000 | Central gateway and dashboard        |
| initiative_viewer       | InitiativeViewer.exe          | 5001 | Initiative lead time analysis        |
| epic_report             | EpicReportGenerator.exe       | 5002 | Epic reports with visualizations     |
| pi_analyzer             | PIAnalyzer.exe                | 5003 | Program Increment metrics            |
| sprint_analyzer         | SprintAnalyzer.exe            | 5004 | Sprint velocity analysis             |
| pbc_analyzer            | PBCAnalyzer.exe               | 5005 | Program Backlog Confidence           |
| duplicate_detector      | DuplicateDetector.exe         | 5006 | Duplicate issue detection            |
| psychological_safety    | PsychologicalSafetyAnalyzer.exe| 5007| Psychological safety metrics         |
| epic_fixversion         | EpicFixVersionAnalyzer.exe    | 5008 | Epic fix version analysis            |

## Build Process

### Step-by-Step Workflow

1. **Initialization**
   - Load application definitions from APPS dictionary
   - Create build/dist/specs directories
   - Validate environment

2. **Spec File Generation**
   - Auto-generate PyInstaller .spec files
   - Include templates and static files
   - Configure hidden imports (Flask, Waitress, reportlab, etc.)
   - Exclude test frameworks and unused dependencies
   - Save to `src/build/specs/[app_name].spec`

3. **Build Execution**
   - Run PyInstaller with generated spec
   - Bundle Python interpreter and dependencies
   - Include shared libraries (src/common)
   - Package templates and static files
   - Create standalone executable

4. **Documentation**
   - Generate app-specific README
   - Include quick start guide
   - Document port configuration
   - Troubleshooting tips
   - Integration instructions

5. **Verification**
   - Check executable creation
   - Validate file sizes
   - Test basic functionality (optional)

### Build Artifacts

During build, the following are created:

```
PerseusLeadTime/
├── build/                    # Build cache (can be deleted)
│   ├── [AppName]/
│   │   ├── Analysis-*.toc
│   │   ├── PKG-*.toc
│   │   └── xref-*.html
│
├── dist/                     # Final executables
│   ├── JiraAnalyticsDashboard.exe
│   ├── JiraAnalyticsDashboard_README.txt
│   ├── InitiativeViewer.exe
│   ├── InitiativeViewer_README.txt
│   ├── [... 9 executables + READMEs ...]
│   └── README.txt            # Master README
│
└── src/build/specs/          # Generated spec files
    ├── unified_dashboard.spec
    ├── initiative_viewer.spec
    └── [... 9 spec files ...]
```

## Output Structure

### Executable Package Contents

Each executable contains:

```
[AppName].exe
├── Python interpreter (embedded)
├── Application code
│   ├── apps/[app_name]/
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── templates/
│   │   └── static/
│   └── src/common/          # Shared libraries
│       ├── jira_client.py
│       ├── config_loader.py
│       ├── utils.py
│       ├── pdf_generator.py
│       └── validators.py
├── Dependencies
│   ├── Flask
│   ├── Waitress
│   ├── Requests
│   ├── Reportlab (if needed)
│   └── All pip packages
└── Runtime data (temporary)
```

### Executable Size Estimates

| Application              | Approximate Size |
|--------------------------|------------------|
| Unified Dashboard        | ~35 MB          |
| Initiative Viewer        | ~45 MB          |
| Epic Report Generator    | ~50 MB          |
| PI Analyzer              | ~40 MB          |
| Sprint Analyzer          | ~40 MB          |
| PBC Analyzer             | ~40 MB          |
| Duplicate Detector       | ~38 MB          |
| Psychological Safety     | ~38 MB          |
| Epic Fix Version         | ~45 MB          |
| **Total Suite**          | **~370 MB**     |

*Sizes include Python interpreter, all dependencies, and application code*

## Troubleshooting

### Common Issues

#### 1. PyInstaller Not Found

**Error:**
```
'pyinstaller' is not recognized as an internal or external command
```

**Solution:**
```bash
# Activate virtual environment first
Obeya\Scripts\activate.bat

# Install PyInstaller
pip install pyinstaller
```

#### 2. Module Not Found During Build

**Error:**
```
ModuleNotFoundError: No module named 'some_module'
```

**Solution:**
- Add the missing module to hidden imports in build_all.py
- Install the missing dependency: `pip install some_module`
- Update requirements.txt

#### 3. Templates Not Found at Runtime

**Error:**
```
jinja2.exceptions.TemplateNotFound: template.html
```

**Solution:**
- Verify templates are included in spec file datas section
- Check template paths are correct (apps/[app_name]/templates)
- Rebuild with `--clean` flag

#### 4. Build Takes Too Long

**Cause:** Large dependencies, slow disk, antivirus scanning

**Solution:**
- Use SSD for build directory
- Temporarily disable antivirus scanning for build folder
- Build individual apps instead of all at once
- Use `--clean` only when necessary

#### 5. Executable Won't Run

**Error:**
```
Failed to execute script [app_name]
```

**Solution:**
- Run from command line to see error messages
- Check Windows Event Viewer for details
- Verify all dependencies are bundled
- Try running as administrator

#### 6. Import Errors in Executable

**Error:**
```
ImportError: cannot import name 'X' from 'Y'
```

**Solution:**
- Add missing module to hiddenimports in spec file
- Verify src/common modules are included
- Check for circular imports
- Rebuild with verbose output

### Debug Mode

To see detailed build output:

```bash
# Run PyInstaller directly with debug flags
pyinstaller --clean --debug all src\build\specs\[app_name].spec
```

### Testing Executables

After building, test each executable:

```batch
# Test unified dashboard
cd dist
JiraAnalyticsDashboard.exe

# In browser: http://localhost:5000
# Verify dashboard loads and shows all apps
```

## Advanced Usage

### Custom Spec Files

To create custom spec files:

1. Generate base spec: `python src\build\build_all.py --app [app_name]`
2. Edit `src/build/specs/[app_name].spec`
3. Build with PyInstaller: `pyinstaller src\build\specs\[app_name].spec`

### Adding Custom Icons

Edit spec file and add icon parameter:

```python
exe = EXE(
    ...
    icon='path/to/icon.ico',
)
```

### One-Directory vs One-File

Current configuration: **One-File** (single .exe)

To change to One-Directory:

```python
# In spec file
exe = EXE(
    ...
    # Remove 'a.binaries, a.zipfiles, a.datas' from exe
)

# Add COLLECT after exe
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='[AppName]'
)
```

### UPX Compression

Current: **Enabled** (reduces file size ~30%)

To disable (faster build):

```python
# In spec file
exe = EXE(
    ...
    upx=False,
)
```

### Adding Data Files

To include additional files:

```python
# In spec file, add to datas
datas=[
    ...,
    ('path/to/file.txt', 'destination/folder'),
    ('entire_folder', 'destination_name'),
]
```

### Excluding More Modules

To reduce executable size:

```python
# In spec file, add to excludes
excludes=[
    ...,
    'module_to_exclude',
]
```

## Build Optimization Tips

### Speed Up Builds

1. **Use --noconfirm flag** (skip confirmation prompts)
2. **Don't clean every time** (cache speeds up rebuilds)
3. **Build on SSD** (faster I/O)
4. **Close antivirus temporarily** (prevents file scanning delays)
5. **Build only changed apps** (use --app flag)

### Reduce Executable Size

1. **Exclude unused modules** (add to excludes list)
2. **Use UPX compression** (enabled by default)
3. **Remove debug symbols** (strip=True)
4. **Optimize imports** (only import what's needed)

### Improve Startup Time

1. **Use One-Directory mode** (faster loading)
2. **Reduce hidden imports** (only essential modules)
3. **Optimize application code** (lazy imports)

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executables
        run: python src\build\build_all.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: jira-analytics-suite
          path: dist/*.exe
```

## Support

For build issues or questions:

1. Check this README first
2. Review PyInstaller documentation: https://pyinstaller.org/
3. Check application-specific README files
4. Contact your development team

## Version History

- **v2.0.0** (2026-02-20)
  - Comprehensive build system for all 9 applications
  - Auto-generated spec files
  - Batch script support
  - Master and per-app documentation
  - Waitress integration for production

- **v1.0.0** (Legacy)
  - Original monolithic build system
  - Manual spec file management

## License

Internal use only. All rights reserved.
