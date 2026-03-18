# Epic Report

**Version:** 2.0.0  
**Author:** Pietro Maffi  
**Port:** 5002 (default)

## Overview

The Epic Report application analyzes Jira issues from a JQL query and identifies their parent Epics, providing a comprehensive report with child count analysis.

## Features

- **Parent Epic Discovery**: Automatically finds parent Epics for all issues in a JQL query
- **Child Count Analysis**: Counts open and closed children for each Epic
- **Epic Keys Export**: Generates CSV list of all Epic keys
- **Issues Without Epics**: Identifies issues that don't have a parent Epic
- **Smart Caching**: 5-minute cache for repeated queries
- **Modern UI**: Bootstrap-based responsive interface
- **Security**: Input validation, rate limiting, XSS protection

## Quick Start

### Option 1: Run Standalone

```bash
cd apps/epic_report
python run.py
```

The application will open automatically in your default browser at `http://localhost:5002`.

### Option 2: Run via Launcher

```bash
# From project root
python launch_all.py --apps epic_report
```

### Option 3: Docker

```bash
cd build/docker
docker-compose up epic_report
```

## Usage

1. **Enter Jira Credentials**
   - Jira URL: Your Atlassian instance (e.g., `https://company.atlassian.net`)
   - Access Token: Generate from Jira → Account Settings → Security → API Tokens

2. **Enter JQL Query**
   - Example: `project = MYPROJECT AND status = "In Progress"`
   - The query should return the child issues (not the Epics themselves)

3. **Analyze**
   - Click "Analyze Epics"
   - View Epic list with child counts
   - Copy Epic keys as CSV for further processing

## Use Cases

### Finding Epics for Sprint Planning
```jql
sprint = "Sprint 42" AND type != Epic
```
Returns all Epics that have work in Sprint 42.

### Identifying Incomplete Epics
Use the report to find Epics with high open child counts.

### Bulk Epic Operations
Copy the CSV list of Epic keys to use in:
- JQL queries: `issuekey in (EPIC-1,EPIC-2,EPIC-3)`
- Bulk updates
- Dashboard filters

## Output

The report provides:

1. **Summary Statistics**
   - Total Epics found
   - Total issues analyzed
   - Total open children across all Epics
   - Issues without Epic links

2. **Epic Table**
   - Epic Key (clickable link to Jira)
   - Epic Summary
   - Status
   - Assignee
   - Project
   - Open Children Count
   - Total Children Count

3. **Epic Keys CSV**
   - Comma-separated list of all Epic keys
   - Copy button for easy use

4. **Issues Without Epics**
   - List of issues that don't have a parent Epic
   - Useful for data quality checks

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `production` or `development`
- `SECRET_KEY`: Flask secret key (auto-generated if not set)
- `CACHE_DIR`: Cache storage directory (default: `data/cache/epic_report`)
- `STORAGE_DIR`: Data storage directory (default: `data/storage/epic_report`)

### Customization

Edit [app.py](app.py) to modify:
- Port number (default: 5002)
- Cache duration (default: 5 minutes)
- Max JQL length (default: 2000 characters)
- Max results limit (default: 5000 issues)
- Epic Link field IDs

## Architecture

```
apps/epic_report/
├── app.py                    # Main Flask application
├── run.py                    # Standalone launcher
├── README.md                 # This file
├── requirements.txt          # Dependencies
├── templates/
│   └── index_epic.html       # Main UI
├── tests/                    # Unit tests
│   ├── test_app.py           # Application tests
│   └── conftest.py           # Test configuration
└── static/                   # Static assets (empty - using CDN)
```

## Dependencies

Core:
- Flask 3.0+
- Waitress 3.0+ (production server)
- Bootstrap 5 (CDN)
- Font Awesome 6 (CDN)

Shared:
- `src.common.JiraClient`: Jira API integration
- `src.common.CacheManager`: File-based caching
- `src.common.FileStorage`: Safe file operations
- `src.common.flask_utils`: Flask decorators and utilities

## Testing

```bash
# Run tests
cd apps/epic_report
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_app.py::test_analyze_epics_success
```

## Troubleshooting

**Connection Error**
- Verify Jira URL (no trailing slash)
- Check firewall settings
- Validate API token (may expire)

**No Epics Found**
- Check that issues actually have Epic links
- Verify Epic Link custom field is configured in Jira
- Ensure you have permission to view the Epics

**Timeout Error**
- Reduce the number of issues in JQL query
- Check network connection
- Jira server may be slow

**Epic Link Field Not Detected**
- The app automatically tries common field IDs
- Check Jira field configuration
- Add your custom field ID to `EPIC_LINK_FIELDS` in app.py

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Display input form |
| `/analyze_epics` | POST | Analyze issues and find parent Epics |
| `/health` | GET | Health check endpoint |

### POST /analyze_epics

**Request:**
```
jira_url: https://company.atlassian.net
access_token: your-token
jql_query: project = TEST
```

**Response:**
```json
{
    "success": true,
    "analysis_date": "2026-02-20T10:30:00",
    "total_issues_analyzed": 25,
    "epic_keys_csv": "EPIC-1,EPIC-2,EPIC-3",
    "epics": [
        {
            "key": "EPIC-1",
            "summary": "Epic Summary",
            "status": "In Progress",
            "assignee": "John Doe",
            "project": "PROJ",
            "open_count": 5,
            "closed_count": 3,
            "total_count": 8
        }
    ],
    "issues_without_epic": [],
    "summary": {
        "total_epics": 3,
        "total_open_children": 15,
        "issues_without_epic": 0
    }
}
```

## Security Features

- **Input Validation**: All inputs are validated and sanitized
- **Rate Limiting**: Prevents API abuse (via decorators)
- **XSS Protection**: Content Security Policy headers
- **Secure Headers**: HSTS, X-Frame-Options, etc.
- **JQL Sanitization**: Prevents injection attacks

## Version History

### 2.0.0 (2026)
- Complete rewrite with modular architecture
- Shared library integration (JiraClient, CacheManager, etc.)
- Comprehensive unit tests (30+ test cases)
- Improved error handling with decorators
- Health check endpoint for monitoring
- 5-minute caching for performance
- Eliminated code duplication (667 lines removed)

### 1.0.0 (Previous)
- Original implementation with custom Jira client
- Basic parent Epic analysis
- Manual caching

## Migration Notes

**From Version 1.0.0:**
- epic_report_jira_client.py (662 lines) → Replaced with shared JiraClient
- epic_report_app.py (307 lines) → Refactored app.py (330 lines)
- Total code reduction: ~640 lines (66% reduction via shared libraries)
- No PDF generation (not needed for this app)
- Same port (5002) for compatibility

## License

Internal use only. © Bosch.

## Support

For questions or issues:
- Author: Pietro Maffi
- Documentation: [ARCHITECTURE.md](../../ARCHITECTURE.md)
- API Reference: [docs/api/README.md](../../docs/api/README.md)
- Migration Template: [APPLICATION_MIGRATION_TEMPLATE.md](../../APPLICATION_MIGRATION_TEMPLATE.md)
