# Sprint Analyzer Application

**Version:** 2.0.0  
**Port:** 5004  
**Purpose:** Analyze sprint capacity, workload, and provide completion forecasts based on historical team velocity.

## Overview

Sprint Analyzer is a Flask-based web application that helps Scrum teams:
- **Assess Sprint Capacity**: Calculate available team capacity based on team size, sprint duration, and hours per day
- **Analyze Workload**: Evaluate current sprint workload including committed work, in-progress items, and remaining work
- **Forecast Completion**: Predict sprint success probability using historical velocity data
- **Generate Reports**: Create professional PDF reports with detailed sprint analysis

## Features

### Core Functionality
1. **Capacity Planning**
   - Configurable team size, sprint duration, and working hours
   - Automatic capacity calculation
   - Capacity utilization metrics

2. **Sprint Analysis**
   - Total story points and hours committed
   - Work completed vs. remaining
   - Issue type breakdown
   - Status distribution

3. **Historical Velocity Analysis**
   - Analyze past sprints (configurable months)
   - Calculate average velocity
   - Velocity trends and consistency
   - Standard deviation analysis

4. **Completion Forecasting**
   - Predict sprint outcome based on historical data
   - Risk assessment (High/Medium/Low)
   - Confidence levels
   - Workload feasibility analysis

5. **PDF Export**
   - Professional sprint analysis reports
   - Detailed capacity and workload metrics
   - Historical velocity charts
   - Recommendations and insights

## Quick Start

### Standalone Mode
```bash
# From this directory
python run.py
```

### Via Launcher
```bash
# From project root
python launchers/run_sprint_analyzer.py
```

### Using Docker
```bash
# From project root
docker-compose up sprint_analyzer
```

The application will be available at `http://localhost:5004`

## Configuration

### Capacity Settings
Configure team capacity in the UI or via POST request:
- **Team Size**: Number of team members (default: 8)
- **Sprint Days**: Duration in working days (default: 10)
- **Hours Per Day**: Working hours per day (default: 8)

### Completion Statuses
Define which Jira statuses indicate completed work (comma-separated):
```
Default: Done,Closed
```

### Excluded Issue Types
Specify issue types to exclude from analysis (comma-separated):
```
Default: Epic
```

### Historical Analysis
- **History Months**: Number of months to analyze for velocity calculation (default: 6)

## API Endpoints

### `GET /`
Display the sprint analysis form.

**Response:**
- HTML page with configuration form

### `POST /analyze_sprint`
Analyze a specific sprint.

**Request Parameters:**
- `jira_url` (required): Jira instance URL
- `access_token` (required): Jira API token
- `sprint_name` (required): Name of the sprint to analyze
- `history_months` (optional): Months of history to analyze (default: 6)
- `team_size` (optional): Number of team members (default: 8)
- `sprint_days` (optional): Sprint duration in days (default: 10)
- `hours_per_day` (optional): Working hours per day (default: 8)
- `completion_statuses` (optional): Comma-separated completed statuses
- `excluded_types` (optional): Comma-separated excluded issue types

**Response:**
```json
{
  "success": true,
  "results": {
    "sprint_info": {
      "name": "Sprint 42",
      "state": "active",
      "start_date": "2025-01-01",
      "end_date": "2025-01-14"
    },
    "capacity_analysis": {
      "total_capacity_hours": 640,
      "committed_hours": 480,
      "utilization_percent": 75.0
    },
    "workload_analysis": {
      "total_issues": 25,
      "completed_issues": 15,
      "in_progress_issues": 7,
      "not_started_issues": 3
    },
    "historical_velocity": {
      "average_velocity": 190.0,
      "completed_sprints": 12,
      "velocity_trend": "stable"
    },
    "forecast": {
      "completion_probability": "High",
      "risk_level": "Low",
      "recommendation": "Sprint is on track for successful completion"
    }
  }
}
```

### `POST /export_pdf`
Generate a PDF report for sprint analysis.

**Request Body (JSON):**
```json
{
  "results": { /* analysis results from /analyze_sprint */ }
}
```

**Response:**
- PDF file download

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "application": "sprint_analyzer",
  "version": "2.0.0"
}
```

## Usage Examples

### Basic Sprint Analysis
```python
import requests

response = requests.post('http://localhost:5004/analyze_sprint', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'sprint_name': 'Sprint 42'
})

results = response.json()
print(f"Sprint capacity: {results['results']['capacity_analysis']['total_capacity_hours']} hours")
print(f"Forecast: {results['results']['forecast']['completion_probability']}")
```

### Custom Configuration
```python
response = requests.post('http://localhost:5004/analyze_sprint', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'sprint_name': 'Sprint 42',
    'team_size': '10',
    'sprint_days': '12',
    'hours_per_day': '7',
    'history_months': '3',
    'completion_statuses': 'Done,Closed,Resolved',
    'excluded_types': 'Epic,Initiative'
})
```

### Generate PDF Report
```python
# First, get analysis results
analysis_response = requests.post('http://localhost:5004/analyze_sprint', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'sprint_name': 'Sprint 42'
})

results = analysis_response.json()

# Then export to PDF
pdf_response = requests.post(
    'http://localhost:5004/export_pdf',
    json={'results': results['results']},
    headers={'Content-Type': 'application/json'}
)

with open('sprint_42_analysis.pdf', 'wb') as f:
    f.write(pdf_response.content)
```

## Dependencies

All dependencies are managed at the project level. See `requirements.txt` in the project root.

### Key Dependencies:
- Flask 3.0: Web framework
- pandas: Data analysis
- numpy: Statistical calculations
- Jira API: Via shared JiraClient

## Architecture

### Application Structure
```
sprint_analyzer/
├── __init__.py              # Application version and metadata
├── app.py                   # Flask application and routes
├── run.py                   # Standalone launcher
├── analyzer.py              # SprintAnalyzer business logic
├── sprint_retriever.py      # Sprint data retrieval
├── data_analyzer.py         # Statistical analysis utilities
├── pdf_generator.py         # PDF report generation
├── requirements.txt         # Additional dependencies (if any)
├── README.md               # This file
├── templates/
│   └── index_sprint.html   # UI template
├── static/                 # Static assets
└── tests/
    ├── __init__.py
    ├── conftest.py         # Test fixtures
    └── test_app.py         # Unit tests
```

### Shared Libraries Used
- `src.common.jira_client`: Unified Jira API client
- `src.common.flask_utils`: Flask decorators and utilities
- `src.common.cache_manager`: Caching support (via SprintAnalyzer)

### Key Classes

#### SprintAnalyzer
Main analysis engine that:
- Configures team capacity parameters
- Retrieves sprint and historical data
- Calculates workload and velocity metrics
- Generates completion forecasts
- Provides risk assessment

#### SimpleSprintRetriever
Handles sprint data retrieval:
- Finds sprint board
- Retrieves sprint details
- Gets historical sprints from same board

#### DataAnalyzer
Statistical analysis utilities:
- Calculate averages, medians, standard deviations
- Trend analysis
- Velocity calculations

#### SprintPDFReportGenerator
PDF generation:
- Professional formatting
- Charts and visualizations
- Detailed metrics tables

## Testing

### Run Tests
```bash
# From project root
pytest apps/sprint_analyzer/tests/ -v

# With coverage
pytest apps/sprint_analyzer/tests/ --cov=apps.sprint_analyzer --cov-report=html
```

### Test Coverage
- **Routes**: All 5 Flask routes tested
- **Configuration**: Capacity, statuses, and exclusion settings
- **Analysis Workflow**: End-to-end analysis and PDF generation
- **Error Handling**: Connection failures, missing data, exceptions
- **Integration**: Complete workflow from analysis to report

### Test Fixtures
Located in `tests/conftest.py`:
- `client`: Flask test client
- `mock_jira_client`: Mocked Jira API
- `sample_sprint_details`: Sprint metadata
- `sample_sprint_issues`: Test issues with estimates and time tracking
- `sample_historical_sprints`: Historical velocity data
- `sample_sprint_analysis`: Complete analysis structure

## Analysis Methodology

### Capacity Calculation
```
Total Capacity = Team Size × Sprint Days × Hours Per Day
```

### Velocity Calculation
```
Average Velocity = Sum(Completed Hours in Past Sprints) / Number of Sprints
```

### Completion Forecast
Based on:
1. **Current Progress**: Percentage of work completed
2. **Historical Velocity**: Team's average completion rate
3. **Remaining Work**: Hours left to complete
4. **Available Capacity**: Remaining capacity in sprint

**Risk Levels:**
- **Low**: Current pace exceeds historical average, high completion probability
- **Medium**: On track but close to capacity limits
- **High**: Behind schedule, at risk of incomplete sprint

## Troubleshooting

### Common Issues

**Sprint Not Found**
- Verify sprint name is exact (case-sensitive)
- Ensure sprint exists in Jira
- Check Jira API token has correct permissions

**No Historical Data**
- Reduce `history_months` parameter
- Ensure past sprints exist on the same board
- Verify sprints are marked as "closed" in Jira

**Capacity Calculation Incorrect**
- Review team_size, sprint_days, hours_per_day settings
- Check for excluded team members or holidays
- Verify completion_statuses match your Jira workflow

**PDF Generation Failed**
- Ensure analysis completed successfully first
- Check sufficient disk space for temporary files
- Verify all required data fields are present

## Performance Considerations

- **Historical Analysis**: Analyzing 6+ months may take longer for large boards
- **Caching**: Historical data is cached to improve performance
- **API Rate Limits**: Jira API rate limits may affect large analyses

## Migration Notes

This application was migrated from a monolithic structure to a modular architecture:
- **Code Reduction**: Eliminated duplicate Jira client code (~310 lines)
- **Shared Libraries**: Now uses centralized JiraClient and caching
- **Improved Testing**: Added 30+ comprehensive unit tests
- **Better Organization**: Clear separation of concerns

For migration details, see `MIGRATION_COMPLETE.md`.

## Support

For issues or questions:
1. Check the test suite for examples
2. Review error logs in Flask console
3. Verify Jira API connectivity with `/health` endpoint
4. Consult project documentation in `docs/`

## Version History

**2.0.0** (Current)
- Migrated to modular architecture
- Integrated shared libraries (JiraClient, flask_utils)
- Added comprehensive test suite (30+ tests)
- Improved error handling and logging
- Enhanced capacity configuration
- Added health check endpoint

**1.0.0** (Legacy)
- Original monolithic implementation
- Basic sprint analysis and PDF export
