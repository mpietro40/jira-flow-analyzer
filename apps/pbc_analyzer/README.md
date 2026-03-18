# PBC Analyzer Application

**Version:** 2.0.0  
**Port:** 5005  
**Purpose:** Process Behavior Charts (PBC) for Lead Time Analysis using Statistical Process Control (SPC)

## Overview

PBC Analyzer is a Flask-based web application that applies statistical process control techniques to analyze Jira lead time metrics. It helps teams identify trends, variations, and special causes in their delivery performance using Process Behavior Charts.

Based on: [DORA Metrics and Process Behavior Charts](https://www.infoq.com/articles/DORA-metrics-PBCs/)

## Features

### Core Functionality
1. **Lead Time Analysis**
   - Calculate lead time for resolved issues
   - Track time from creation to resolution
   - Analyze trends over time

2. **Statistical Process Control**
   - Calculate mean, median, and standard deviation
   - Establish upper and lower control limits (UCL/LCL)
   - Identify statistical outliers

3. **Special Cause Detection**
   - Automatically identify issues outside control limits
   - Flag unusual variations in lead time
   - Provide deviation metrics

4. **Project Discovery**
   - Traverse full issue hierarchy
   - Discover all related projects automatically
   - Analyze multiple projects from single query

5. **Data Persistence**
   - Cache analysis results for fast retrieval
   - Save analyses to persistent storage
   - List and retrieve historical analyses

6. **Flexible Configuration**
   - Configurable start date for analysis
   - Custom JQL queries
   - Debug mode for troubleshooting

## Quick Start

### Standalone Mode
```bash
# From this directory
python run.py
```

### Via Launcher
```bash
# From project root
python launchers/run_pbc_analyzer.py
```

### Using Docker
```bash
# From project root
docker-compose up pbc_analyzer
```

The application will be available at `http://localhost:5005`

## Configuration

### Configuration File
Create `pbc_config.json` in the project root with:
```json
{
  "start_date": "2024-08-01",
  "default_jql": "project = MYPROJECT AND type in (Story, Bug, Task) AND resolved is not EMPTY",
  "analysis_description": "Process Behavior Charts help identify trends and special causes in lead time metrics"
}
```

### Parameters
- **start_date**: Begin analysis from this date (format: YYYY-MM-DD)
- **default_jql**: Default JQL query for the UI form
- **analysis_description**: Help text displayed in the UI

## API Endpoints

### `GET /`
Display the PBC analysis form.

**Response:**
- HTML page with configuration form

### `POST /analyze_pbc`
Perform Process Behavior Chart analysis.

**Request Parameters:**
- `jira_url` (required): Jira instance URL
- `access_token` (required): Jira API token
- `jql_query` (required): JQL query to fetch issues
- `start_date` (optional): Start date for analysis (default: 2024-08-01)
- `debug` (optional): Enable debug logging (checkbox)

**Response:**
```json
{
  "success": true,
  "cached": false,
  "analysis_results": {
    "analysis_id": "pbc_20260220_120000",
    "timestamp": "2026-02-20T12:00:00",
    "start_date": "2024-08-01",
    "jql_query": "project = PROJ AND type in (Story, Bug)",
    "summary": {
      "total_projects": 2,
      "total_issues": 45,
      "date_range": {
        "start": "2024-08-01",
        "end": "2024-12-31"
      },
      "overall_stats": {
        "mean_lead_time": 5.2,
        "median_lead_time": 4.5,
        "std_dev": 2.1,
        "upper_control_limit": 11.5,
        "lower_control_limit": 0.0
      }
    },
    "projects": {
      "PROJ": {
        "project_key": "PROJ",
        "project_name": "Sample Project",
        "issues_analyzed": 30,
        "lead_time_stats": {
          "mean": 5.2,
          "median": 4.5,
          "std_dev": 2.1,
          "min": 1.5,
          "max": 10.3,
          "ucl": 11.5,
          "lcl": 0.0
        },
        "pbc_data": [
          {
            "issue_key": "PROJ-101",
            "lead_time_days": 4.5,
            "resolution_date": "2024-08-05",
            "issue_type": "Story"
          }
        ],
        "special_causes": [
          {
            "issue_key": "PROJ-115",
            "lead_time_days": 15.2,
            "reason": "Above upper control limit",
            "deviation": 3.7
          }
        ]
      }
    }
  }
}
```

### `GET /get_cached_results/<analysis_id>`
Retrieve previously saved analysis results.

**Parameters:**
- `analysis_id` (path): Analysis identifier (e.g., pbc_20260220_120000)

**Response:**
```json
{
  "success": true,
  "analysis_results": { /* full analysis data */ }
}
```

### `GET /list_cached_results`
List all available saved analyses.

**Response:**
```json
{
  "success": true,
  "cached_results": [
    {
      "analysis_id": "pbc_20260220_120000",
      "start_date": "2024-08-01",
      "timestamp": "2026-02-20T12:00:00",
      "total_projects": 2,
      "total_issues": 45,
      "filename": "pbc_20260220_120000.json"
    }
  ]
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "application": "pbc_analyzer",
  "version": "2.0.0",
  "port": 5005
}
```

## Usage Examples

### Basic PBC Analysis
```python
import requests

response = requests.post('http://localhost:5005/analyze_pbc', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'jql_query': 'project = MYPROJECT AND type in (Story, Bug) AND resolved is not EMPTY',
    'start_date': '2024-08-01'
})

results = response.json()
if results['success']:
    analysis = results['analysis_results']
    print(f"Analyzed {analysis['summary']['total_issues']} issues")
    print(f"Mean lead time: {analysis['summary']['overall_stats']['mean_lead_time']} days")
    print(f"UCL: {analysis['summary']['overall_stats']['upper_control_limit']} days")
```

### With Debug Mode
```python
response = requests.post('http://localhost:5005/analyze_pbc', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'jql_query': 'project = TEST',
    'start_date': '2024-01-01',
    'debug': 'on'  # Enable debug logging
})
```

### Retrieve Saved Analysis
```python
# First, get the analysis ID from the initial analysis
analysis_id = 'pbc_20260220_120000'

response = requests.get(f'http://localhost:5005/get_cached_results/{analysis_id}')
data = response.json()

if data['success']:
    analysis = data['analysis_results']
    print(f"Retrieved analysis from {analysis['timestamp']}")
```

### List All Analyses
```python
response = requests.get('http://localhost:5005/list_cached_results')
data = response.json()

print(f"Found {len(data['cached_results'])} saved analyses:")
for analysis in data['cached_results']:
    print(f"  - {analysis['analysis_id']}: {analysis['total_issues']} issues, {analysis['total_projects']} projects")
```

## Dependencies

All dependencies are managed at the project level. See `requirements.txt` in the project root.

### Key Dependencies:
- Flask 3.0: Web framework
- statistics: Statistical calculations (Python standard library)
- Jira API: Via shared JiraClient

## Architecture

### Application Structure
```
pbc_analyzer/
├── __init__.py              # Application version and metadata
├── app.py                   # Flask application and routes (300 lines)
├── run.py                   # Standalone launcher
├── analyzer.py              # PBCAnalyzer business logic (622 lines)
├── requirements.txt         # Additional dependencies (none)
├── README.md               # This file
├── templates/
│   └── index_pbc.html      # UI template
├── static/                 # Static assets
└── tests/
    ├── __init__.py
    ├── conftest.py         # Test fixtures
    └── test_app.py         # Unit tests (40+ tests)
```

### Shared Libraries Used
- `src.common.jira_client`: Unified Jira API client
- `src.common.cache_manager`: Caching for analysis results
- `src.common.file_storage`: Persistent storage for analyses
- `src.common.flask_utils`: Flask decorators and utilities

### Key Classes

#### PBCAnalyzer
Main analysis engine that:
- Traverses full issue hierarchy from Business Initiatives
- Discovers all related projects
- Calculates lead time for each resolved issue
- Computes statistical metrics (mean, median, std dev)
- Establishes control limits (UCL/LCL)
- Identifies special cause variations
- Generates per-project PBC data

**Methods:**
- `analyze(jql_query, start_date)`: Main analysis entry point
- `_traverse_full_hierarchy(issues)`: Recursively fetch all child issues
- `_calculate_lead_time(issue)`: Calculate days from creation to resolution
- `_compute_control_limits(lead_times)`: Calculate UCL/LCL using 3-sigma
- `_identify_special_causes(issues, ucl, lcl)`: Flag outliers

## Statistical Methodology

### Lead Time Calculation
```
Lead Time (days) = Resolution Date - Creation Date
```

### Control Limits
Process Behavior Charts use a moving range method:
```
Mean = Average of all lead times
Average Moving Range = Average of consecutive differences
Upper Control Limit (UCL) = Mean + (2.66 * Average Moving Range)
Lower Control Limit (LCL) = Mean - (2.66 * Average Moving Range) [minimum 0]
```

The 2.66 constant is derived from statistical process control theory for process limits with moving ranges.

### Special Cause Identification
Issues are flagged as special causes if:
- **Lead time > UCL**: Significantly longer than typical
- **Lead time < LCL**: Significantly shorter than typical (rare)

### Interpretation
- **Within Limits**: Indicates common cause variation (normal process variation)
- **Outside Limits**: Indicates special cause variation (investigate root cause)
- **Trending**: Multiple points consistently above/below mean may indicate process shift

## Testing

### Run Tests
```bash
# From project root
pytest apps/pbc_analyzer/tests/ -v

# With coverage
pytest apps/pbc_analyzer/tests/ --cov=apps.pbc_analyzer --cov-report=html
```

### Test Coverage
- **Routes**: All 6 Flask routes tested
- **Analysis**: PBC analysis workflow with various scenarios
- **Caching**: Cache hit/miss scenarios
- **Storage**: Persistent storage operations
- **Error Handling**: Connection failures, invalid data, exceptions
- **Integration**: Complete workflows from analysis to retrieval

### Test Fixtures
Located in `tests/conftest.py`:
- `client`: Flask test client
- `mock_jira_client`: Mocked Jira API
- `sample_pbc_issue`: Single issue for testing
- `sample_pbc_issues`: Multiple issues with varying lead times
- `sample_pbc_analysis`: Complete analysis structure
- `mock_pbc_analyzer`: Mocked analyzer
- `mock_cache_manager`: Mocked cache
- `mock_file_storage`: Mocked storage

## Troubleshooting

### Common Issues

**No Issues Found**
- Verify JQL query is correct
- Ensure resolved issues exist in the specified date range
- Check Jira API token has correct permissions

**Incorrect Lead Times**
- Verify `created` and `resolutiondate` fields exist
- Check for issues with null resolution dates
- Ensure date filtering is correct

**Large Analysis Times**
- Reduce date range (start_date closer to present)
- Limit JQL query to specific projects
- Use cache for repeated queries

**Special Causes Not Detected**
- Verify sufficient issue count (need >10 for valid statistics)
- Check if lead times have actual variation
- Review control limit calculations

**Cache Not Working**
- Check cache directory exists and is writable
- Verify cache TTL is appropriate
- Clear cache if stale: delete files in `cache/pbc_analyzer/`

## Performance Considerations

- **Hierarchy Traversal**: Large hierarchies may take time (30-60 seconds for 1000+ issues)
- **Caching**: Analysis results cached for 1 hour to improve performance
- **Persistent Storage**: All analyses saved to disk for historical reference
- **API Rate Limits**: Jira API rate limits may affect large analyses

## Use Cases

### Sprint Retrospectives
Analyze lead time trends to identify:
- Issues that took significantly longer than average
- Process improvements needed
- Team capacity issues

### Continuous Improvement
Track lead time over time to:
- Verify improvement initiatives are working
- Detect process degradation early
- Establish baseline performance metrics

### Team Performance
Compare lead times across:
- Different projects
- Issue types (Story vs Bug vs Task)
- Time periods

### Process Stability
Use control limits to:
- Determine if process is stable
- Identify when process has shifted
- Focus improvement efforts on special causes

## Migration Notes

This application was migrated from a monolithic structure to a modular architecture:
- **Code Reduction**: Eliminated custom Jira client and caching code
- **Shared Libraries**: Now uses centralized JiraClient, CacheManager, FileStorage
- **Improved Testing**: Added 40+ comprehensive unit tests
- **Better Organization**: Clear separation of concerns

For migration details, see `MIGRATION_COMPLETE.md`.

## Support

For issues or questions:
1. Check the test suite for examples
2. Review error logs in Flask console
3. Verify Jira API connectivity with `/health` endpoint
4. Enable debug mode for detailed logging
5. Consult project documentation in `docs/`

## Version History

**2.0.0** (Current)
- Migrated to modular architecture
- Integrated shared libraries (JiraClient, CacheManager, FileStorage)
- Added comprehensive test suite (40+ tests)
- Improved error handling and logging
- Enhanced persistence with dual cache + storage
- Added health check endpoint
- Improved configuration management

**1.0.0** (Legacy)
- Original monolithic implementation
- Basic PBC analysis and lead time metrics
- Custom file-based caching

## References

- [Process Behavior Charts](https://www.infoq.com/articles/DORA-metrics-PBCs/)
- [Statistical Process Control](https://en.wikipedia.org/wiki/Statistical_process_control)
- [DORA Metrics](https://www.devops-research.com/research.html)
- [Understanding Variation](https://deming.org/understanding-variation-the-key-to-managing-chaos/)
