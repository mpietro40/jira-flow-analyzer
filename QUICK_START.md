# Jira Analytics Suite - Quick Start

## 🚀 The Easiest Way (Monolithic Mode)

```bash
cd JiraAnalyzerSuite
python run.py
```

✅ **ONE command starts everything!**  
✅ All apps served from http://localhost:5000  
✅ Dashboard links work immediately  

---

## Architecture Options

### Option 1: Monolithic (Recommended)
- All apps in ONE process
- Access everything through http://localhost:5000
- Internal URL routing works automatically

### Option 2: Microservices
- Each app on separate port
- More scalable, can deploy independently
- Requires all services running

---

## 10 Applications Available

1. **Lead Time Analyzer** (`/lead-time-analyzer`) - NEW! ✨
2. **Initiative Viewer** (`/initiative-viewer`)
3. **Epic Report** (`/epic-report`)
4. **PI Analyzer** (`/pi-analyzer`)
5. **Sprint Analyzer** (`/sprint-analyzer`)
6. **PBC Analyzer** (`/pbc-analyzer`)
7. **Duplicate Detector** (`/duplicate-detector`)
8. **Psychological Safety** (`/psychological-safety`)
9. **Epic Fix Version** (`/epic-fixversion`)
10. **Unified Dashboard** (`/`)

---

## Command Reference

```bash
# Monolithic (default)
python run.py
python run.py --monolithic

# Microservices (all apps separate)
python run.py --microservices
# OR
start_all.bat

# Single app (testing)
python run.py --app lead_time
python run.py --app dashboard
```

---

## What Just Happened?

✅ Lead Time Analyzer migrated to new structure  
✅ Clean folder architecture with 10 apps  
✅ Flexible launcher - choose your mode  
✅ Dashboard updated to show all 10 apps  

**Ready to go!** Just run: `python run.py`
