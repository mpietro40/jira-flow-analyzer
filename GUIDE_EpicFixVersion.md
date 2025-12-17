# Epic Fix Version Analyzer - Complete Guide

## Overview
The Epic Fix Version Analyzer analyzes epic distribution by fix version across Jira initiatives using hierarchy traversal (Initiative → Feature → Sub-Feature → Epic).

## Quick Start

### Start Application
```bash
python epic_fixversion_app.py
```
Open browser to: `http://localhost:5400`

### Fill Form
- **Jira URL**: `https://your-company.atlassian.net`
- **Access Token**: Your PAT from Jira
- **Initiative JQL**: `project = ISDOP AND type = "Business Initiative"`
- **Fix Version**: `2025.Q1` (or leave empty for all epics)
- **Excluded Statuses**: `Done, Closed, Abandoned` (optional)

### Click "Analyze Distribution"
Results appear with modern table view and PDF export option.

## Features

### Hierarchy Traversal
- Automatic epic discovery through hierarchy
- Path: Initiative → Feature → Sub-Feature → Epic
- Uses Jira's `childIssuesOf()` function

### Optional Fix Version Filter
- Leave empty for all epics
- Specify version to filter (case-sensitive)
- Shows all fix versions in results

### Excluded Statuses Filter
- Skip epics in specific statuses
- Default: Done, Closed, Abandoned
- Customizable comma-separated list

### PDF Export
- Professional PDF reports
- Purple gradient styling
- Complete analysis data
- Automatic download

## Custom Fields Configuration

### Current Field Mapping
| Display Name | Field ID | Purpose |
|--------------|----------|---------|
| Magnitude/Complexity | `customfield_10037` | Epic size rating |
| Requesting Customer | `customfield_10095` | Who requested |
| CPO-APO Leading | `assignee` | Person leading |
| Starting Date | `customfield_10096` | Target start |
| What to Deliver | `customfield_10097` | Solution description |

### ⚠️ Important: Discover Your Field IDs

**These field IDs are specific to the original Jira instance.** Your instance will have different IDs.

### Find Your Custom Field IDs

Run the discovery tool:
```bash
python discover_custom_fields.py
```

This will:
1. List all custom fields with IDs
2. Suggest which fields to use
3. Generate mapping template
4. Save to `custom_fields_mapping.json`

### Update Application

Edit `epic_fixversion_app.py` (around line 140):
```python
epic_data = {
    'complexity': self._extract_custom_field(fields, 'customfield_XXXXX'),  # Your ID
    'requesting_customer': self._extract_custom_field(fields, 'customfield_YYYYY'),
    'target_start': self._extract_custom_field(fields, 'customfield_ZZZZZ'),
    'solution': self._extract_custom_field(fields, 'customfield_WWWWW'),
}
```

## API Endpoints

### POST /analyze
**Request**: Form data
```
jira_url: string (required)
access_token: string (required)
initiative_jql: string (required)
fix_version: string (optional)
excluded_statuses: string (optional)
```

**Response** (200):
```json
{
  "success": true,
  "fix_version": "2025.Q1",
  "total_initiatives": 15,
  "initiatives_with_epics": 12,
  "total_epics": 45,
  "excluded_statuses": ["Done", "Closed", "Abandoned"],
  "results": [...]
}
```

### GET /health
**Response**: `{"status": "healthy", "service": "Epic Fix Version Analyzer"}`

## Integration with Unified Suite

The Epic Fix Version analyzer is integrated into the unified suite at port 5000.

### Access from Unified Dashboard
- URL: `http://localhost:5000/epic-fixversion`
- From Dashboard: Click "Epic Fix Version" card

### Standalone Access
- URL: `http://localhost:5400`
- Run: `python epic_fixversion_app.py`

## Troubleshooting

### "No initiatives found"
- Verify JQL query syntax
- Check permissions to view initiatives
- Confirm initiatives exist

### "No epics found"
- Verify fix version spelling (case-sensitive)
- Check epics have fix version assigned
- Verify hierarchy: Initiative → Feature → Sub-Feature → Epic

### PDF Generation Issues
- Check browser download settings
- Ensure pop-ups not blocked
- Verify analysis completed
- Check logs: `epic_fixversion.log`

## Files Structure
```
PerseusLeadTime/
├── epic_fixversion_app.py          # Flask application
├── epic_fixversion_pdf_generator.py # PDF generator
├── templates/
│   └── epic_fixversion.html        # UI template
├── epic_fixversion_results/        # Results storage
│   └── *.json                      # Analysis results
└── epic_fixversion.log             # Application logs
```

---

**Version**: 1.2  
**Status**: ✅ Production Ready
