# Sprint Analyzer - Complete Guide

## Overview
A comprehensive sprint analysis tool that leverages historical Jira data to forecast sprint feasibility and provide actionable insights for agile teams.

## Quick Start

### Start Application
```bash
python sprint_web_app.py
```
Open browser to: `http://localhost:5200`

### Command Line Interface
```bash
python sprint_analyzer.py --jira-url https://your-company.atlassian.net --token YOUR_API_TOKEN --sprint "Sprint 2024-01"
```

#### Parameters
- `--jira-url`: Your Jira server URL (required)
- `--token`: Jira API access token (required)  
- `--sprint`: Sprint name or ID (required)
- `--history-months`: Months of historical data for forecasting (default: 6)

## Features

### Sprint Workload Analysis
Analyzes estimated, remaining, and spent hours across all sprint issues

### Feasibility Forecasting
Predicts sprint completion probability based on historical velocity

### Status Breakdown
Detailed analysis by issue status with time tracking

### Smart Recommendations
Actionable insights based on data analysis

### Risk Assessment
Automatic risk level calculation (LOW/MEDIUM/HIGH)

### Comprehensive Reporting
Detailed console reports with emoji indicators

## Architecture

The Sprint Analyzer reuses existing components from the PerseusLeadTime framework:

```
sprint_analyzer.py
├── JiraClient (reused) - API connectivity and data fetching
├── DataAnalyzer (reused) - Core analytics capabilities  
└── SprintAnalyzer (new) - Sprint-specific analysis and forecasting
```

## Key Metrics Explained

### Workload Analysis
- **Total Issues**: Count of all issues in sprint
- **Estimated Hours**: Sum of original time estimates
- **Remaining Hours**: Sum of remaining time estimates
- **Time Spent**: Actual hours logged
- **Progress**: Percentage completion based on time spent vs estimated

### Forecasting
- **Completion Probability**: Based on historical completion rates and current velocity
- **Estimated Weeks Needed**: Remaining work divided by historical velocity
- **Risk Level**: Automatic assessment
  - **LOW**: < 1 week remaining at current velocity
  - **MEDIUM**: 1-2 weeks remaining
  - **HIGH**: > 2 weeks remaining

### Historical Context
- **Average Velocity**: Hours completed per week based on historical data
- **Estimate Accuracy**: Ratio of actual vs estimated time
- **Completion Rate**: Percentage of issues completed in historical sprints

## Sample Output

```
============================================================
📊 SPRINT ANALYSIS REPORT: Development Sprint 15
============================================================

📈 SUMMARY:
  • Total Issues: 12
  • Estimated Hours: 96.0h
  • Remaining Hours: 64.0h
  • Progress: 33.3%
  • Risk Level: MEDIUM

🔮 FORECAST:
  • Completion Probability: 78%
  • Estimated Weeks Needed: 1.8

📋 STATUS BREAKDOWN:
  • To Do: 5 issues, 40.0h remaining
  • In Progress: 4 issues, 20.0h remaining
  • In Review: 2 issues, 4.0h remaining
  • Done: 1 issues, 0.0h remaining

💡 RECOMMENDATIONS:
  📝 2 issues lack time estimates - prioritize estimation
  📊 Historical estimates tend to be optimistic - add buffer time
  ✅ Monitor progress closely in first few days
============================================================
```

## Jira Setup Requirements

1. **Time Tracking Enabled**: Ensure time tracking enabled in your Jira project
2. **API Token**: Generate personal access token in Jira
3. **Permissions**: User must have read access to:
   - Sprint data
   - Issue time tracking fields
   - Historical issue data

## Sprint Identification

The tool accepts sprint names or IDs in various formats:
- Sprint name: `"Development Sprint 15"`
- Sprint ID: `123`
- Partial matches: `"Sprint 15"`

## Testing

Run the comprehensive test suite:
```bash
python test_sprint_analyzer.py
```

### Test Coverage
- ✅ Workload analysis calculations
- ✅ Historical velocity computation
- ✅ Forecast generation logic
- ✅ Recommendation algorithms
- ✅ Error handling and edge cases
- ✅ Report formatting
- ✅ API integration mocking

## Troubleshooting

### Connection Failed
```
🚩 Failed to connect to Jira
```
- Verify Jira URL format (include https://)
- Check API token validity
- Ensure network connectivity

### No Sprint Data
```
🚩 No issues found for sprint: Sprint Name
```
- Verify sprint name/ID is correct
- Check user permissions for sprint access
- Ensure sprint exists and contains issues

### Missing Time Data
```
⚠️ Could not fetch time data for ISSUE-123
```
- Verify time tracking is enabled
- Check user permissions for time tracking fields
- Some issues may not have time estimates (normal)

## Integration with Unified Suite

### Access from Unified Dashboard
- URL: `http://localhost:5000/sprint-analysis`
- From Dashboard: Click "Sprint Analyzer" card

### Standalone Access
- URL: `http://localhost:5200`
- Run: `python sprint_web_app.py`

## Files Structure
```
PerseusLeadTime/
├── sprint_analyzer.py          # Core analysis logic
├── sprint_web_app.py          # Flask application
└── templates/
    └── sprint_analyzer.html   # UI template
```

---

**Status**: ✅ Production Ready  
**Built with ❤️ for agile teams who want data-driven sprint planning**
