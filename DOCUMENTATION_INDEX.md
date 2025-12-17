# Jira Analytics Suite - Documentation Index

## 📚 Main Documentation

### [README.md](README.md)
**Start here!** Overview of the entire Jira Analytics Suite with quick start instructions, features list, and architecture overview.

---

## 🎯 Application-Specific Guides

### [GUIDE_UnifiedSuite.md](GUIDE_UnifiedSuite.md)
**Unified Dashboard & Launcher**
- How to use the unified suite (port 5000)
- Launcher menu options
- Benefits of unified vs individual apps
- Running options and configuration

### [GUIDE_EpicFixVersion.md](GUIDE_EpicFixVersion.md)
**Epic Fix Version Analyzer**
- Analyze epic distribution by fix version
- Hierarchy traversal (Initiative → Feature → Sub-Feature → Epic)
- Custom field configuration and discovery
- Status filtering and PDF export

### [GUIDE_PIAnalyzer.md](GUIDE_PIAnalyzer.md)
**PI (Program Increment) Analyzer**
- Product Increment completion analysis
- Flow metrics (WIP, Throughput, Cycle Time, Work Item Age)
- File-based storage and recovery
- Cross-project automatic discovery

### [GUIDE_SprintAnalyzer.md](GUIDE_SprintAnalyzer.md)
**Sprint Analyzer**
- Sprint forecasting and capacity analysis
- Historical velocity tracking
- Risk assessment and recommendations
- Time tracking analysis

---

## 🚀 Deployment & Operations

### [GUIDE_Deployment.md](GUIDE_Deployment.md)
**All Deployment Options**
- Docker deployment (recommended)
- Render.com cloud deployment
- Test machine installation
- Configuration and security

### [GUIDE_Troubleshooting.md](GUIDE_Troubleshooting.md)
**Common Issues & Solutions**
- Jira timeout issues and configuration
- Application-specific troubleshooting
- Docker issues
- General troubleshooting steps

---

## 🔧 Discovery Tools

### discover_custom_fields.py
**Find Jira Custom Field IDs**
```bash
python discover_custom_fields.py
```
Helps you discover custom field IDs in your Jira instance for proper field mapping.

### discover_statuses.py
**Find All Status Types**
```bash
python discover_statuses.py
```
Retrieves all status types from all Jira projects or a specific project.

---

## 📁 Directory-Specific Documentation

### epic_fixversion_results/README.md
Documentation for Epic Fix Version analysis results storage directory.

### pi_results/README.md
Documentation for PI analysis results storage directory.

---

## 📖 Quick Reference

### By Use Case

**I want to get started quickly**
→ [README.md](README.md) → Quick Start section

**I want to deploy to production**
→ [GUIDE_Deployment.md](GUIDE_Deployment.md)

**I'm having timeout issues**
→ [GUIDE_Troubleshooting.md](GUIDE_Troubleshooting.md) → Jira Timeout Issues

**I need to configure custom fields**
→ [GUIDE_EpicFixVersion.md](GUIDE_EpicFixVersion.md) → Custom Fields Configuration

**I want to understand flow metrics**
→ [GUIDE_PIAnalyzer.md](GUIDE_PIAnalyzer.md) → Flow Metrics Explained

**I want to use all tools from one place**
→ [GUIDE_UnifiedSuite.md](GUIDE_UnifiedSuite.md)

**I want to forecast sprint completion**
→ [GUIDE_SprintAnalyzer.md](GUIDE_SprintAnalyzer.md)

### By Application

| Application | Port | Guide | Standalone File |
|-------------|------|-------|-----------------|
| **Unified Suite** | 5000 | [GUIDE_UnifiedSuite.md](GUIDE_UnifiedSuite.md) | `main_app.py` |
| **Lead Time Analyzer** | 5100 | README.md | `app.py` |
| **PI Analyzer** | 5300 | [GUIDE_PIAnalyzer.md](GUIDE_PIAnalyzer.md) | `pi_web_app.py` |
| **Sprint Analyzer** | 5200 | [GUIDE_SprintAnalyzer.md](GUIDE_SprintAnalyzer.md) | `sprint_web_app.py` |
| **Epic Fix Version** | 5400 | [GUIDE_EpicFixVersion.md](GUIDE_EpicFixVersion.md) | `epic_fixversion_app.py` |
| **Duplicate Detector** | 5500 | README.md | (integrated) |

---

## 📝 Documentation Changes

### What Changed?
The documentation has been reorganized for clarity:

**Before**: 18 separate .md files with overlapping content
**After**: 6 focused guides + main README

### Merged Files

**GUIDE_EpicFixVersion.md** merged:
- EPIC_FIXVERSION_COMPLETE_GUIDE.md
- EPIC_FIXVERSION_INTEGRATION.md
- CUSTOM_FIELDS_GUIDE.md

**GUIDE_PIAnalyzer.md** merged:
- PI_ANALYZER_GUIDE.md
- README_PI_ANALYZER.md
- FLOW_METRICS_EXPLAINED.md
- PI_FILE_STORAGE.md
- PI_RECOVERY_GUIDE.md
- QUICK_START_FILE_STORAGE.md
- IMPLEMENTATION_SUMMARY.md

**GUIDE_SprintAnalyzer.md** merged:
- README_SPRINT_ANALYZER.md

**GUIDE_UnifiedSuite.md** merged:
- README_UNIFIED_SUITE.md

**GUIDE_Deployment.md** merged:
- DOCKER_DEPLOY.md
- RENDER_DEPLOYMENT_GUIDE.md
- DEPLOYMENT_CHECKLIST.md
- INSTALL_ON_TEST_MACHINE.md

**GUIDE_Troubleshooting.md** merged:
- TIMEOUT_TROUBLESHOOTING.md
- Common issues from other guides

**README.md** replaced:
- readme.MD (old HTML-style readme)

---

**Last Updated**: 2025  
**Documentation Version**: 2.0  
**Status**: ✅ Organized and Complete
