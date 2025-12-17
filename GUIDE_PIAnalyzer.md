# PI Analyzer - Complete Guide

## Overview
The PI (Program Increment) Analyzer analyzes Agile program increment metrics for ISDOP projects, providing completion metrics and advanced flow metrics analysis.

## Quick Start

### Start Application
```bash
python pi_web_app.py
```
Open browser to: `http://localhost:5300`

### Configuration
- **Jira Server URL**: `https://company.atlassian.net`
- **Access Token (PAT)**: Personal Access Token
- **PI Start Date**: `YYYY-MM-DD`
- **PI End Date**: `YYYY-MM-DD`
- **Full Area Backlog Analysis**: Check for flow metrics

## Features

### Basic PI Analysis
- Issue completion metrics
- Cross-project discovery through ISDOP Business Initiative relationships
- Estimation analysis (estimated vs unestimated)
- Professional PDF reports with charts

### Advanced Flow Metrics (Full Area Backlog)
When enabled:
1. **Work in Progress (WIP)**: Items started but not finished
2. **Throughput**: Items completed per week
3. **Work Item Age**: Average time from start to PI end for WIP
4. **Cycle Time**: Average time from start to completion

## Flow Metrics Explained

### 1. Work in Progress (WIP)
**What**: Number of items currently being worked on

**Calculation**: Count of issues with status IN (In Progress, Doing, Working, Development)

**Why it matters**: High WIP indicates context switching. Lower WIP = faster delivery.

**Thresholds**:
- ✅ Healthy: < 10 items
- ⚠️ Warning: 10-15 items
- 🚨 Critical: > 15 items

### 2. Throughput
**What**: Average items completed per week

**Calculation**: `Total Completed Issues / Number of Weeks in PI`

**Why it matters**: Measures team velocity and delivery capacity.

### 3. Work Item Age
**What**: Average time WIP items have been in progress (days)

**Calculation**: `(Current Date - Date Item Started Progress)` averaged

**Why it matters**: High age indicates blocked or stalled work.

**Thresholds**:
- ✅ Healthy: < 14 days
- ⚠️ Warning: 14-21 days
- 🚨 Critical: > 21 days

### 4. Cycle Time
**What**: Average time to complete an item (days)

**Calculation**: `(Resolution Date - In Progress Start Date)` averaged

**Why it matters**: Predicts how long new work will take.

**Thresholds**:
- ✅ Healthy: < 21 days
- ⚠️ Warning: 21-30 days
- 🚨 Critical: > 30 days

## File Storage & Recovery

### Automatic Saving
- Every completed analysis saved to `pi_results/{start_date}_{end_date}.json`
- Happens automatically in background
- No user action required

### Persistent Storage
- Files survive server restarts
- Files survive system reboots
- Results available indefinitely

### Easy Retrieval
- Click "Load Available Results" button
- See all saved analyses with dates and issue counts
- Click any result to load instantly
- Generate PDF from any saved result

### If Connection Lost During Analysis

1. **Wait a moment** - Backend may still be processing
2. **Click "Load Available Results"**
3. **Select your analysis** from the list
4. **Download PDF** once loaded

### File Management

**View Files**:
```bash
dir pi_results\*.json
```

**Delete Old Files** (older than 90 days):
```powershell
Get-ChildItem pi_results\*.json | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-90)} | Remove-Item
```

**Backup**:
```bash
xcopy pi_results\*.json backup_location\ /Y
```

## Data Discovery Method

1. **Query**: `project = ISDOP AND issuetype = "Business Initiative"`
2. **For each initiative**: `issuekey in childIssuesOf("INITIATIVE-KEY") AND resolved >= "start" AND resolved <= "end"`
3. **Flow metrics**: Additional queries for WIP and historical data

## Results Interpretation

### Summary Metrics
- **PI Duration**: Length of program increment
- **Projects**: Number of related projects discovered
- **Completed Issues**: Total issues closed during PI
- **Total Estimates**: Sum of estimated work (days)

### Issue Type Analysis
For each type (Bug, Story, Feature):
- Count of completed issues
- Total estimated days
- Percentage of unestimated work

### Project Analysis
For each project:
- Number of completed issues
- Total estimated work

### Flow Metrics (if enabled)
For each project area:
- **WIP**: Current work in progress count
- **Throughput**: Items completed per week
- **Work Item Age**: Average age of WIP items
- **Cycle Time**: Average completion time

## PDF Report
Click "Download PDF Report" for comprehensive report including:
- Executive summary
- Detailed metrics tables
- Flow metrics analysis (if enabled)
- Actionable recommendations
- Professional formatting

## Troubleshooting

### No Business Initiatives Found
- Verify ISDOP project exists
- Check "Business Initiative" issue type configured
- Ensure proper permissions

### No Child Issues Found
- Verify initiatives have parent/child relationships
- Check `childIssuesOf()` JQL function available
- Ensure child issues exist in date range

### Flow Metrics Not Showing
- Ensure "Full Area Backlog Analysis" checked
- Verify issues have status transitions in history
- Check in-progress statuses configured

### No Saved Results Found
- Check if `pi_results/` directory exists
- Verify file permissions
- Check server logs for save errors

## Files Structure
```
PerseusLeadTime/
├── pi_analyzer.py              # Core analysis logic
├── pi_web_app.py              # Flask application
├── pi_pdf_generator.py        # PDF generator
├── templates/
│   └── pi_analyzer.html       # UI template
└── pi_results/                # Results storage
    └── *.json                 # Analysis results
```

## Integration with Unified Suite

### Access from Unified Dashboard
- URL: `http://localhost:5000/pi-analysis`
- From Dashboard: Click "PI Analyzer" card

### Standalone Access
- URL: `http://localhost:5300`
- Run: `python pi_web_app.py`

---

**Author**: Pietro Maffi  
**Version**: 2.0  
**Status**: ✅ Production Ready
