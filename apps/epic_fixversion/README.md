# Epic Fix Version Analyzer

Analyze epic distribution by fix version across Jira initiatives, providing insights into release planning and feature organization.

## Overview

The Epic Fix Version Analyzer traverses the Jira hierarchy (Initiative → Feature → Sub-Feature → Epic) to identify all epics associated with initiatives, optionally filtered by a specific fix version. It provides comprehensive reporting on epic distribution, complexity, and custom field data.

## Key Features

- **Hierarchy Traversal**: Automatically navigates Initiative → Feature → Sub-Feature → Epic relationships
- **Fix Version Filtering**: Analyze all epics or filter by specific fix version
- **Status Exclusion**: Configurable status filtering (default: Done, Closed, Abandoned, Cancelled, Resolved)
- **Custom Field Extraction**: 
  - Complexity (customfield_41340)
  - Requesting Customer (customfield_114641)
  - Target Start Date (customfield_42640)
  - Solution (customfield_116072)
- **Comment Analysis**: Extracts platform and impacts information from comments
- **PDF Export**: Professional PDF reports with detailed epic distribution
- **Result Persistence**: Saves analysis results to JSON files for historical tracking
- **Unified Dashboard Integration**: Alias routes for seamless dashboard integration

## Architecture

### Components

```
apps/epic_fixversion/
├── __init__.py           # Package initialization (Port 5008)
├── app.py                # Flask application (7 routes)
├── analyzer.py           # Epic fix version analysis logic
├── pdf_generator.py      # PDF report generation
├── run.py                # Standalone launcher
├── requirements.txt      # Dependencies
├── templates/
│   └── index_fixversion.html
└── tests/
    ├── __init__.py
    ├── conftest.py       # Test fixtures (12 fixtures)
    └── test_app.py       # Test suite (50+ tests)
```

### Technology Stack

- **Flask 3.0.3**: Web framework
- **Waitress 3.0.2**: Production WSGI server (Windows-compatible)
- **ReportLab**: PDF generation
- **Shared Libraries**:
  - `src.common.jira_client`: Jira API integration
  - `src.common.flask_utils`: Decorators (@validate_jira_credentials, @handle_errors, @log_request)

## Installation

### Prerequisites

- Python 3.8-3.11
- Jira Cloud instance with appropriate permissions
- Personal Access Token (PAT) for authentication

### Setup

```bash
# From workspace root
pip install -r requirements.txt

# Or install specific app dependencies
cd apps/epic_fixversion
pip install -r requirements.txt
```

## Usage

### Running the Application

#### Standalone Mode

```bash
# From apps/epic_fixversion directory
python run.py

# Or from workspace root
python -m apps.epic_fixversion.app
```

#### Development Mode

```bash
# From workspace root
python apps/epic_fixversion/app.py
```

Application will be available at: http://localhost:5008

### Analyze Epic Fix Version

#### Web Interface

1. Navigate to http://localhost:5008
2. Enter your Jira credentials:
   - **Jira URL**: Your Jira Cloud instance URL (e.g., https://your-company.atlassian.net)
   - **Access Token**: Your Personal Access Token
3. Configure analysis:
   - **Initiative JQL**: JQL query to find initiatives (e.g., `project = MYPROJ AND type = Initiative`)
   - **Fix Version** (Optional): Specific fix version to filter epics (leave empty to analyze all epics)
   - **Excluded Statuses** (Optional): Comma-separated list of statuses to exclude (default: Done, Closed, Abandoned, Cancelled, Resolved)
4. Click "Analyze" to generate the report
5. Review epic distribution across initiatives
6. Click "Export PDF" to download a PDF report

#### API Endpoints

**Analyze Epics by Fix Version**

```bash
curl -X POST http://localhost:5008/analyze \
  -d "jira_url=https://your-company.atlassian.net" \
  -d "access_token=YOUR_PAT" \
  -d "initiative_jql=project = MYPROJ AND type = Initiative" \
  -d "fix_version=2026-Q1" \
  -d "excluded_statuses=Done, Closed"
```

**Response**:
```json
{
  "success": true,
  "fix_version": "2026-Q1",
  "excluded_statuses": ["Done", "Closed"],
  "total_initiatives": 5,
  "initiatives_with_epics": 4,
  "total_epics": 23,
  "results": [
    {
      "initiative_key": "INIT-100",
      "initiative_summary": "Q1 2026 Strategic Initiative",
      "epic_count": 8,
      "epics": [
        {
          "key": "EPIC-500",
          "summary": "Implement authentication system",
          "status": "In Progress",
          "project": "PROJ",
          "fix_versions": ["2026-Q1", "v2.5.0"],
          "complexity": "High",
          "requesting_customer": "Customer A",
          "assignee": "John Doe",
          "target_start": "2026-03-01",
          "solution": "OAuth 2.0 implementation",
          "comments": {
            "platform": "Microservices",
            "impacts": "Requires database migration"
          }
        }
      ]
    }
  ],
  "timestamp": "2026-01-15T10:30:00"
}
```

**Export PDF Report**

```bash
curl -X POST http://localhost:5008/export_pdf \
  -d "jira_url=https://your-company.atlassian.net" \
  -d "analysis_data=$(cat analysis_results.json)" \
  --output epic_fixversion_report.pdf
```

**Health Check**

```bash
curl http://localhost:5008/health
```

Response:
```json
{
  "status": "healthy",
  "port": 5008
}
```

### Unified Dashboard Integration

The application provides alias routes for unified dashboard integration:

- `/analyze_epic_fixversion` → Same as `/analyze`
- `/export_epic_fixversion_pdf` → Same as `/export_pdf`

## Configuration

### Environment Variables

- `PORT`: Server port (default: 5008)
- `FLASK_ENV`: Environment mode (development/production)

### Custom Field IDs

If your Jira instance uses different custom field IDs, update them in [analyzer.py](analyzer.py):

```python
# Current field IDs
COMPLEXITY_FIELD = 'customfield_41340'
REQUESTING_CUSTOMER_FIELD = 'customfield_114641'
TARGET_START_FIELD = 'customfield_42640'
SOLUTION_FIELD = 'customfield_116072'
```

### Default Excluded Statuses

Default statuses excluded from analysis (configurable):
- Done
- Closed
- Abandoned
- Cancelled
- Resolved

Override via the `excluded_statuses` parameter (comma-separated list).

## Analysis Logic

### Hierarchy Traversal

The analyzer follows this hierarchy:

```
Initiative (root)
├── Feature (Epic Link)
│   ├── Sub-Feature (Epic Link)
│   │   └── Epic
│   └── Epic
└── Epic (direct link)
```

**Process:**
1. Fetch initiatives matching the JQL query
2. For each initiative:
   - Find all Features linked via Epic Link
   - For each Feature, find Sub-Features
   - For each Sub-Feature, find Epics
   - Optionally filter epics by fix version
   - Exclude epics with specified statuses
3. Extract custom fields and comments
4. Aggregate results per initiative

### Fix Version Filtering

- **With Fix Version**: Only epics containing the specified fix version are included
- **Without Fix Version**: All epics are included (full epic inventory)

Epics can have multiple fix versions. An epic matches if the specified version is in its `fixVersions` list.

### Result Persistence

Results are automatically saved to:
```
epic_fixversion_results/epic_fixversion_<fix_version>_<timestamp>.json
```

File naming:
- **With Fix Version**: `epic_fixversion_2026-Q1_20260115_103000.json`
- **Without Fix Version**: `epic_fixversion_All_20260115_103000.json`

## Testing

### Run Tests

```bash
# From workspace root
pytest apps/epic_fixversion/tests/ -v

# With coverage
pytest apps/epic_fixversion/tests/ -v --cov=apps.epic_fixversion --cov-report=term-missing

# Run specific test class
pytest apps/epic_fixversion/tests/test_app.py::TestAnalyzeRoute -v
```

### Test Coverage

The test suite includes 50+ tests covering:

- **Basic Routes** (3 tests): Index, health check, favicon
- **Analyze Route** (10 tests): Validation, fix version filtering, status exclusion, error handling
- **PDF Export** (5 tests): Generation, validation, error handling
- **Epic Hierarchy** (8 tests): Traversal logic, multiple initiatives
- **Fix Version Filtering** (6 tests): Single version, no filter, multiple versions
- **Status Exclusion** (4 tests): Default statuses, custom statuses
- **Custom Fields** (5 tests): Complexity, customer, comments
- **Integration** (9+ tests): Complete workflows, edge cases

**Target Coverage**: >85%

### Test Fixtures

Available fixtures (see [conftest.py](tests/conftest.py)):

- `client`: Flask test client
- `mock_jira_client`: Mocked Jira client
- `sample_initiative`: Sample initiative issue
- `sample_epic`: Sample epic with fix versions
- `sample_epic_no_fixversion`: Epic without fix versions
- `sample_analysis_results`: Complete analysis results
- `mock_analyzer`: Mocked analyzer
- `mock_pdf_generator`: Mocked PDF generator
- `valid_analysis_request`: Valid request data
- `valid_analysis_request_no_fixversion`: Request without fix version
- `sample_pdf_request`: PDF export request

## Common Use Cases

### 1. Release Planning

**Scenario**: Identify all epics planned for Q1 2026 release

```bash
# Via API
curl -X POST http://localhost:5008/analyze \
  -d "jira_url=https://company.atlassian.net" \
  -d "access_token=$PAT" \
  -d "initiative_jql=project = STRATEGY AND type = Initiative" \
  -d "fix_version=2026-Q1"
```

**Output**: List of all initiatives with epics tagged for 2026-Q1, including:
- Epic count per initiative
- Complexity distribution
- Requesting customers
- Target start dates

### 2. Epic Inventory

**Scenario**: Get complete inventory of all epics across initiatives

```bash
# Via API (no fix_version parameter)
curl -X POST http://localhost:5008/analyze \
  -d "jira_url=https://company.atlassian.net" \
  -d "access_token=$PAT" \
  -d "initiative_jql=project = STRATEGY AND type = Initiative" \
  -d "fix_version="
```

**Output**: All epics regardless of fix version

### 3. Customer-Specific Analysis

**Scenario**: After running analysis, filter results by requesting customer

The results include `requesting_customer` field for each epic:

```python
# Post-process results
for initiative in results['results']:
    customer_epics = [
        e for e in initiative['epics'] 
        if e['requesting_customer'] == 'Customer A'
    ]
    print(f"{initiative['initiative_key']}: {len(customer_epics)} epics for Customer A")
```

### 4. Complexity Assessment

**Scenario**: Analyze complexity distribution for release planning

```python
# Extract complexity metrics
high_complexity = [e for init in results['results'] for e in init['epics'] if e['complexity'] == 'High']
medium_complexity = [e for init in results['results'] for e in init['epics'] if e['complexity'] == 'Medium']
low_complexity = [e for init in results['results'] for e in init['epics'] if e['complexity'] == 'Low']
```

### 5. Status-Based Filtering

**Scenario**: Exclude specific statuses for active work tracking

```bash
# Exclude Done, Blocked, and On Hold
curl -X POST http://localhost:5008/analyze \
  -d "jira_url=https://company.atlassian.net" \
  -d "access_token=$PAT" \
  -d "initiative_jql=project = STRATEGY" \
  -d "fix_version=2026-Q1" \
  -d "excluded_statuses=Done, Blocked, On Hold"
```

## Troubleshooting

### No Epics Found

**Problem**: Analysis returns 0 epics

**Solutions**:
1. Verify initiatives have Epic Links to Features/Epics
2. Check fix version spelling (case-sensitive)
3. Verify excluded statuses aren't filtering all epics
4. Ensure initiatives returned by JQL have proper hierarchy

### Custom Fields Missing

**Problem**: Complexity, requesting customer, or other fields show as empty

**Solutions**:
1. Verify custom field IDs match your Jira instance
2. Check field permissions (fields must be visible to the token owner)
3. Update field IDs in [analyzer.py](analyzer.py)

### PDF Generation Fails

**Problem**: PDF export returns error

**Solutions**:
1. Ensure ReportLab is installed: `pip install reportlab`
2. Check analysis data is valid JSON
3. Verify sufficient disk space for PDF creation

### Connection Timeout

**Problem**: Analysis times out for large datasets

**Solutions**:
1. Reduce scope of initiative JQL query
2. Use more specific fix version filter
3. Increase request timeout in your HTTP client
4. Consider breaking analysis into smaller batches

## API Reference

### Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Main application page |
| `/analyze` | POST | Analyze epics by fix version |
| `/export_pdf` | POST | Generate PDF report |
| `/health` | GET | Health check endpoint |
| `/favicon.ico` | GET | Favicon support |
| `/analyze_epic_fixversion` | POST | Alias for /analyze (dashboard integration) |
| `/export_epic_fixversion_pdf` | POST | Alias for /export_pdf (dashboard integration) |

### Request Parameters

**Analyze Route (`/analyze`, `/analyze_epic_fixversion`)**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jira_url` | string | Yes | Jira instance URL |
| `access_token` | string | Yes | Personal Access Token |
| `initiative_jql` | string | Yes | JQL query for initiatives |
| `fix_version` | string | No | Fix version to filter (empty = all epics) |
| `excluded_statuses` | string | No | Comma-separated status list (default: Done, Closed, Abandoned, Cancelled, Resolved) |

**Export PDF Route (`/export_pdf`, `/export_epic_fixversion_pdf`)**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jira_url` | string | Yes | Jira instance URL |
| `analysis_data` | JSON | Yes | Analysis results from /analyze |

## Performance Considerations

- **Large Hierarchies**: For initiatives with 100+ epics, analysis may take 30-60 seconds
- **API Rate Limits**: Jira Cloud has rate limits (approx 10 requests/second)
- **Caching**: Results are saved to disk for future reference
- **Pagination**: Currently loads all data in single request (consider pagination for very large datasets)

## Migration Notes

**From Original epic_fixversion_app.py:**

- Original: 682 lines (398 app + 284 PDF generator)
- Migrated: 412 lines core (162 app + 250 analyzer), 284 PDF (unchanged)
- **Line Reduction**: ~40% in application core
- **Test Coverage**: Added 50+ tests (0 → 50+)
- **Documentation**: Added comprehensive README and migration docs

**Key Improvements:**
- Separated concerns (app vs analyzer vs PDF)
- Added shared library integration (JiraClient, flask_utils)
- Comprehensive test coverage
- Alias routes for unified dashboard
- Enhanced error handling
- Production-ready with Waitress

## Related Applications

- **Initiative Viewer** (Port 5001): View initiative details and hierarchies
- **Epic Report** (Port 5002): Generate detailed epic reports
- **PI Analyzer** (Port 5003): Analyze Program Increment metrics
- **Unified Dashboard** (Port 5000): Central dashboard integrating all apps

## Support

For issues, feature requests, or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review test cases in [test_app.py](tests/test_app.py) for usage examples
3. Consult [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) for migration details

## Version History

- **v2.0.0** (2026-01-15): Complete migration to modular architecture
  - Separated Flask app and analyzer logic
  - Added comprehensive test suite (50+ tests)
  - Integrated shared libraries
  - Added unified dashboard compatibility
  - Enhanced documentation

- **v1.0.0** (Original): Monolithic application
  - Combined Flask app and analyzer in single file
  - Basic PDF generation
  - No test coverage
