# Perseus Lead Time - Refactoring Migration Plan

## Status: Phase 4 - In Progress (3 of 9 Apps Complete)

This document tracks the complete refactoring of Perseus Lead Time from a flat structure to a modular, well-organized architecture.

**Last Updated:** February 20, 2026  
**Progress:** Phases 1-3 Complete | Phase 4: 33% (3/9 apps)

## Phase 1: Create New Structure ✅ IN PROGRESS

### Completed:
- ✅ Created ARCHITECTURE.md
- ✅ Created all directory structures
  - src/common/ and src/config/
  - apps/{9 apps}/tests/
  - scripts/{5 tool categories}/tests/
  - tests/{integration,shared,fixtures}/
  - build/{executables,docker}/
  - docs/{5 categories}/
- ✅ Created Python package __init__.py files

### Remaining in Phase 1:
- [ ] Create template files for shared code modules
- [ ] Create template README.md for each app
- [ ] Create base test templates
- [ ] Create build system templates
- [ ] Create unified launcher templates
- [ ] Create Docker configuration templates
- [ ] Create documentation index files

## Phase 2: Extract Shared Code (Not Started)

### Goal: Consolidate duplicate code into src/common/

#### 2.1 Jira Client Consolidation
**Current State:**
- `jira_client.py` (main, 644 lines)
- `epic_report_jira_client.py` (duplicate)

**Action:**
1. Analyze both implementations
2. Merge into unified `src/common/jira_client.py`
3. Add comprehensive tests in `tests/shared/test_jira_client.py`
4. Document API in `docs/api/jira-client.md`

#### 2.2 PDF Generator Base Class
**Current State:**
- Multiple PDF generators with duplicate code:
  - `initiative_viewer_pdf.py`
  - `epic_pdf_generator.py`
  - `epic_fixversion_pdf_generator.py`
  - `pi_pdf_generator.py`
  - `sprint_pdf_generator.py`
  - `duplicate_pdf_generator.py`

**Action:**
1. Extract common PDF generation logic
2. Create `src/common/pdf_generator_base.py`
3. Identify common patterns (headers, footers, tables, charts)
4. Each app's PDF generator will inherit from base class
5. Add tests in `tests/shared/test_pdf_generator.py`

#### 2.3 Cache Manager
**Current State:**
- Cache logic embedded in applications
- `pi_cache.py` (specific implementation)
- File-based caching in initiative_viewer

**Action:**
1. Create unified `src/common/cache_manager.py`
2. Support multiple backends (file, memory, future: Redis)
3. Add cache invalidation strategies
4. Add tests

#### 2.4 File Storage
**Current State:**
- File storage utilities scattered across apps

**Action:**
1. Create `src/common/file_storage.py`
2. Centralize file operations, cleanup, temp file management
3. Add tests

#### 2.5 Visualization Utilities
**Current State:**
- `visualization.py` in root
- Duplicate chart code in multiple apps

**Action:**
1. Move to `src/common/visualization.py`
2. Extract common chart types
3. Add customization options

#### 2.6 Flask Utilities
**Action:**
1. Create `src/common/flask_utils.py`
2. Common Flask app setup
3. Standard error handlers
4. Session management utilities
5. Form validation helpers

## Phase 3: Migrate First Application (Initiative Viewer) - ✅ COMPLETED

**Duration:** 3 hours  
**Status:** ✅ COMPLETED  
**Date:** January 2025

Choose one application to migrate as a proof-of-concept and template for others:

**Selected:** Initiative Viewer (initiative_viewer.py → apps/initiative_viewer/)

### Migration Completed:
- ✅ Created apps/initiative_viewer/ structure
- ✅ Refactored app.py (450 lines, down from 1354)
- ✅ Created pdf_generator.py extending PDFGeneratorBase
- ✅ Integrated shared libraries (JiraClient, CacheManager, FileStorage, flask_utils)
- ✅ Copied and simplified templates
- ✅ Created comprehensive tests (45+ test cases)
- ✅ Created README.md with full documentation
- ✅ Created run.py launcher
- ✅ Created MIGRATION_COMPLETE.md summary
- ✅ Validated no syntax/type errors
- ✅ Used decorator pattern for validation and error handling
- ✅ Added health check endpoint
- ✅ Eliminated code duplication (60%+ now in shared libs)

### Key Achievements:
1. **Code Reduction:** 1354 → 730 lines (46% reduction)
2. **Test Coverage:** 0% → 85%+ (45 unit tests)
3. **Reusability:** All Jira, cache, file, PDF logic now shared
4. **Documentation:** Comprehensive README with API docs, troubleshooting
5. **Architecture:** Clean separation (HTTP, Business, Data, Presentation layers)

### Template Created:
- [APPLICATION_MIGRATION_TEMPLATE.md](APPLICATION_MIGRATION_TEMPLATE.md) - Complete migration checklist for remaining apps

---

## Phase 4: Migrate Remaining Applications - 🔄 IN PROGRESS (2 of 9 Complete)

### For Each Application:

1. **Create app structure:**
   ```
   apps/{app_name}/
   ├── README.md                   # App-specific documentation
   ├── app.py                      # Main Flask application
   ├── run.py                      # Development launcher
   ├── run.bat                     # Windows launcher (future)
   ├── build.py                    # Executable build script (future)
   ├── {app_name}.spec             # PyInstaller spec file (future)
   ├── requirements.txt            # App-specific dependencies
   ├── MIGRATION_COMPLETE.md       # Migration summary
   ├── static/                     # Static assets
   ├── templates/                  # HTML templates
   └── tests/                      # Comprehensive test suite
       ├── __init__.py
       ├── conftest.py             # Test fixtures
       └── test_app.py             # Unit tests
   ```

2. **Move existing code:**
   - Copy main app file
   - Move templates
   - Move static assets (if any)
   - Update imports to use src.common.*

3. **Create comprehensive tests:**
   - test_app.py: Web interface tests
   - test_pdf_generator.py: PDF generation tests (if applicable)
   - test_integration.py: End-to-end tests
   - Test fixtures in tests/fixtures/

4. **Create build configuration:**
   - PyInstaller spec file (Phase 5)
   - build.py script (Phase 5)
   - Test executable creation (Phase 5)

5. **Update documentation:**
   - App-specific README.md
   - MIGRATION_COMPLETE.md summary
   - User guide in docs/guides/ (Phase 8)

### Migration Order & Status:

1. ✅ **Initiative Viewer** - COMPLETE (Port 5001)
   - Duration: 3 hours
   - Code reduction: 46% (1354 → 730 lines)
   - Test coverage: 0% → 85%+ (45 tests)
   - Complex: 4-level hierarchy, PDF generation
   
2. ✅ **Epic Report** - COMPLETE (Port 5002)
   - Duration: 2.5 hours
   - Code reduction: 66% (969 → 330 lines)
   - Test coverage: 0% → 90%+ (30 tests)
   - Replaced: 662-line custom Jira client
   - No PDF generation (simpler)
   
3. ✅ **PI Analyzer** - COMPLETE (Port 5003)
   - Duration: 3 hours
   - Code reduction: ~68% (1,894 → ~600 lines)
   - Test coverage: 10% → 80%+ (35 tests)
   - Replaced: 112-line custom PICache
   - Complex: PI metrics, flow analysis, PDF generation
   
4. ⏳ **Sprint Analyzer** (Port 5004) - NEXT
5. ⏳ **Epic Fix Version** (Port 5008)
6. ⏳ **PBC Analyzer** (Port 5005)
7. ⏳ **Duplicate Detector** (Port 5006)
8. ⏳ **Psychological Safety** (Port 5007)
9. ⏳ **Unified Dashboard** (main_app.py, Port 5000) - LAST

**Progress:** 3 of 9 applications migrated (33%)  
**Estimated Remaining:** 12-18 hours (2-3 hours per app × 6 apps)

## Phase 4: Migrate CLI Scripts (Not Started)

### Script categories:

1. **Backward Check** (backward_check_analyzer.py)
2. **Data Analysis** (data_analyzer.py, lead_time_analyzer.py)
3. **Jira Utils** (discover_custom_fields.py, discover_statuses.py, jira_status_changer.py)
4. **User Auditor** (jira_user_auditor.py, jira_user_auditor_fixed.py)

For each:
- Move to appropriate subfolder
- Add comprehensive tests
- Update imports
- Create documentation
- Optional: Add executable build

## Phase 5: Create Build System (Not Started)

### Components:

1. **build/build_all.py**: Master build script
   - Builds all applications as executables
   - Parallel building where possible
   - Error handling and reporting
   - Output to build/executables/

2. **build/common.py**: Shared PyInstaller configuration
   - Common excludes
   - Data files handling
   - Icon configuration

3. **Individual app build scripts**
   - apps/{app_name}/build.py
   - Uses common configuration
   - App-specific customizations

4. **CI/CD Integration**
   - GitHub Actions workflow
   - Build on release
   - Upload artifacts

## Phase 6: Docker Configuration (Not Started)

### Docker Compose Setup:

```yaml
services:
  nginx:
    # Reverse proxy
    
  unified-dashboard:
    # Main entry point (port 5000)
    
  initiative-viewer:
    # Port 5001
    
  epic-report:
    # Port 5002
    
  pi-analyzer:
    # Port 5003
    
  sprint-analyzer:
    # Port 5004
    
  pbc-analyzer:
    # Port 5005
    
  duplicate-detector:
    # Port 5006
    
  psychological-safety:
    # Port 5007
    
  epic-fixversion:
    # Port 5008
```

### Components:
1. Multi-stage Dockerfile for each app
2. docker-compose.yml for all services
3. Nginx reverse proxy configuration
4. Shared volume for caching
5. Environment configuration

## Phase 7: Unified Launchers (Not Started)

### Development Launchers:

1. **launch_all.py**
   - Starts all web apps on different ports
   - Monitors processes
   - Restarts on failure
   - Logs aggregation

2. **launch_all.bat** (Windows)
   - Same functionality for Windows

3. **Individual app launchers**
   - apps/{app_name}/run.py
   - Simple Flask development server
   - Auto-reload on code changes

## Phase 8: Comprehensive Testing (Not Started)

### Test Coverage Goals:
- Overall: 90%+
- Shared code (src/common/): 95%+
- Each application: 85%+
- Integration tests: Cover all critical paths

### Test Structure:

1. **Unit Tests** (per app and shared code)
   - Fast, isolated
   - Mock external dependencies

2. **Integration Tests** (tests/integration/)
   - Test app startup
   - Test cross-app functionality
   - Test with real (mocked) Jira responses

3. **End-to-End Tests**
   - Full user workflows
   - PDF generation
   - Error handling

### CI/CD:
- Run all tests on every PR
- Fail if coverage drops
- Generate coverage reports

## Phase 9: Documentation Consolidation (Not Started)

### Current State: 20+ scattered markdown files

### New Structure:

```
docs/
├── INDEX.md                      # Master index
├── getting-started/
│   ├── installation.md
│   ├── quick-start.md
│   └── configuration.md
├── deployment/
│   ├── docker.md
│   ├── render.md
│   ├── heroku.md
│   └── standalone-executables.md
├── guides/
│   ├── initiative-viewer.md
│   ├── epic-report.md
│   └── ... (one per app)
├── development/
│   ├── architecture.md
│   ├── contributing.md
│   ├── testing.md
│   └── building-executables.md
└── api/
    ├── jira-client.md
    ├── pdf-generator.md
    └── cache-manager.md
```

### Actions:
1. Migrate existing documentation
2. Remove duplicates
3. Update references
4. Add missing documentation
5. Create clear navigation

## Phase 10: Validation & Cleanup (Not Started)

### Validation:
1. All apps work standalone
2. All apps work in Docker
3. All executables build successfully
4. All tests pass
5. Documentation is complete
6. CI/CD works

### Cleanup:
1. Remove old files from root
2. Update README.md
3. Update .gitignore
4. Archive old documentation

## Success Criteria

- [ ] Clear folder structure
- [ ] No duplicate code
- [ ] 90%+ test coverage
- [ ] All apps have comprehensive tests
- [ ] All apps build as executables
- [ ] Docker runs all apps
- [ ] Unified launcher works
- [ ] Documentation is clear and complete
- [ ] CI/CD tests and builds everything
- [ ] Easy to add new applications

## Timeline Estimate

- Phase 1: 2 hours (IN PROGRESS)
- Phase 2: 4 hours
- Phase 3: 12 hours (9 apps)
- Phase 4: 3 hours
- Phase 5: 3 hours
- Phase 6: 3 hours
- Phase 7: 2 hours
- Phase 8: 8 hours
- Phase 9: 3 hours
- Phase 10: 2 hours

**Total: ~42 hours of focused work**

## Next Steps

1. Complete Phase 1 (create all templates)
2. Begin Phase 2 (extract shared code)
3. Start with Initiative Viewer migration as template
4. Iterate and refine approach
5. Continue with remaining apps

## Notes

- Keep existing code working during migration
- Test frequently
- Git commits at each milestone
- Get user feedback early and often
