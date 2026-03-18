# Duplicate Detector Application

**Version:** 2.0.0  
**Port:** 5006  
**Purpose:** Identify potential duplicate Jira stories using text similarity analysis

## Overview

Duplicate Detector is a Flask-based web application that analyzes Jira issues to identify potential duplicates based on text similarity. It helps teams maintain backlog quality by detecting stories with similar summaries and descriptions.

## Features

### Core Functionality
1. **Text Similarity Analysis**
   - Compare story summaries using SequenceMatcher algorithm
   - Compare story descriptions for deeper analysis
   - Configurable similarity threshold

2. **Duplicate Grouping**
   - Group similar stories together
   - Calculate similarity scores (0.0 to 1.0)
   - Rank groups by similarity strength

3. **Smart Filtering**
   - Analyze specific projects or multiple projects
   - Custom JQL queries for targeted analysis
   - Filter by issue type, status, or other criteria

4. **PDF Reports**
   - Generate professional duplicate analysis reports
   - Include similarity scores and issue details
   - Export for sharing with stakeholders

5. **Comprehensive Results**
   - Total issues analyzed
   - Number of duplicate groups found
   - Detailed similarity metrics
   - Issue metadata (key, summary, description, status)

## Quick Start

### Standalone Mode
```bash
# From this directory
python run.py
```

### Via Launcher
```bash
# From project root
python launchers/run_duplicate_detector.py
```

### Using Docker
```bash
# From project root
docker-compose up duplicate_detector
```

The application will be available at `http://localhost:5006`

## API Endpoints

### `GET /`
Display the duplicate detection form.

**Response:**
- HTML page with analysis form

### `POST /analyze_duplicates`
Analyze Jira issues for potential duplicates.

**Request Parameters:**
- `jira_url` (required): Jira instance URL
- `access_token` (required): Jira API token
- `jql_query` (required): JQL query to fetch issues

**Response:**
```json
{
  "success": true,
  "analysis_results": {
    "total_issues": 50,
    "duplicate_count": 12,
    "duplicate_groups": [
      {
        "group_id": 1,
        "similarity_score": 0.85,
        "issues": [
          {
            "key": "PROJ-101",
            "summary": "Implement user authentication",
            "description": "Create login and registration functionality",
            "status": "Open",
            "created": "2024-01-10",
            "project": "PROJ"
          },
          {
            "key": "PROJ-102",
            "summary": "Implement authentication system",
            "description": "Build user login and registration",
            "status": "Open",
            "created": "2024-01-15",
            "project": "PROJ"
          }
        ]
      }
    ],
    "jira_url": "https://your-company.atlassian.net",
    "jql_query": "project = PROJ AND type = Story",
    "request_date": "2026-02-20T12:00:00",
    "analysis_timestamp": "2026-02-20T12:00:00"
  }
}
```

### `POST /generate_duplicate_report`
Generate PDF report for duplicate analysis.

**Request Body (JSON):**
```json
{
  "analysis_results": { /* results from /analyze_duplicates */ }
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
  "application": "duplicate_detector",
  "version": "2.0.0",
  "port": 5006,
  "timestamp": "2026-02-20T12:00:00"
}
```

## Usage Examples

### Basic Duplicate Detection
```python
import requests

response = requests.post('http://localhost:5006/analyze_duplicates', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'jql_query': 'project = MYPROJECT AND type = Story AND status = Open'
})

results = response.json()
if results['success']:
    analysis = results['analysis_results']
    print(f"Analyzed {analysis['total_issues']} issues")
    print(f"Found {analysis['duplicate_count']} potential duplicates in {len(analysis['duplicate_groups'])} groups")
    
    for group in analysis['duplicate_groups']:
        print(f"\nGroup {group['group_id']} (similarity: {group['similarity_score']:.2f}):")
        for issue in group['issues']:
            print(f"  - {issue['key']}: {issue['summary']}")
```

### Generate PDF Report
```python
# First, get analysis results
analysis_response = requests.post('http://localhost:5006/analyze_duplicates', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'jql_query': 'project = PROJ AND type = Story'
})

results = analysis_response.json()

# Then export to PDF
pdf_response = requests.post(
    'http://localhost:5006/generate_duplicate_report',
    json=results['analysis_results'],
    headers={'Content-Type': 'application/json'}
)

with open('duplicate_analysis.pdf', 'wb') as f:
    f.write(pdf_response.content)
```

### Analyze Multiple Projects
```python
response = requests.post('http://localhost:5006/analyze_duplicates', data={
    'jira_url': 'https://your-company.atlassian.net',
    'access_token': 'your_api_token',
    'jql_query': 'project in (PROJ1, PROJ2, PROJ3) AND type = Story AND status != Closed'
})
```

## Dependencies

All dependencies are managed at the project level. See `requirements.txt` in the project root.

### Key Dependencies:
- Flask 3.0: Web framework
- difflib: Text similarity (Python standard library)
- reportlab: PDF generation
- Jira API: Via shared JiraClient

## Architecture

### Application Structure
```
duplicate_detector/
├── __init__.py              # Application version and metadata
├── app.py                   # Flask application and routes (180 lines)
├── run.py                   # Standalone launcher
├── detector.py              # DuplicateDetector business logic (236 lines)
├── pdf_generator.py         # DuplicatePDFReportGenerator (279 lines)
├── requirements.txt         # Additional dependencies (none)
├── README.md               # This file
├── templates/
│   └── index_duplicate.html # UI template
├── static/                 # Static assets
└── tests/
    ├── __init__.py
    ├── conftest.py         # Test fixtures
    └── test_app.py         # Unit tests (40+ tests)
```

### Shared Libraries Used
- `src.common.jira_client`: Unified Jira API client
- `src.common.flask_utils`: Flask decorators and utilities

### Key Classes

#### DuplicateDetector
Main detection engine that:
- Fetches issues from Jira via JQL
- Analyzes text similarity between stories
- Groups similar stories together
- Calculates similarity scores
- Identifies potential duplicates

**Methods:**
- `analyze_duplicates(jql_query)`: Main analysis entry point
- `_calculate_similarity(text1, text2)`: Calculate text similarity score
- `_normalize_text(text)`: Clean and normalize text for comparison
- `_group_duplicates(issues)`: Group similar issues together
- `_find_similar_issues(issue, candidates)`: Find similar issues

**Similarity Algorithm:**
Uses Python's `difflib.SequenceMatcher` which implements:
- Ratcliff/Obershelp algorithm
- Returns ratio of matching characters (0.0 to 1.0)
- Considers word order and proximity

#### DuplicatePDFReportGenerator
PDF generation that:
- Creates professional reports
- Includes duplicate groups with similarity scores
- Shows issue details (key, summary, description, status)
- Adds metadata (analysis date, total counts)

## Similarity Detection Methodology

### Text Normalization
Before comparison, text is normalized:
1. Convert to lowercase
2. Remove extra whitespace
3. Remove special characters (optional)
4. Standardize punctuation

### Similarity Calculation
```python
similarity = SequenceMatcher(None, text1, text2).ratio()
# Returns value between 0.0 (completely different) and 1.0 (identical)
```

### Threshold Recommendations
- **0.90 - 1.00**: Very likely duplicates (almost identical)
- **0.75 - 0.89**: Likely duplicates (high similarity)
- **0.60 - 0.74**: Possible duplicates (moderate similarity)
- **0.00 - 0.59**: Unlikely duplicates (low similarity)

Default threshold: **0.70** (configurable in detector.py)

### Comparison Strategy
1. **Summary Comparison**: Primary similarity check
2. **Description Comparison**: Secondary check (if descriptions exist)
3. **Combined Score**: Weighted average (summary 70%, description 30%)

## Testing

### Run Tests
```bash
# From project root
pytest apps/duplicate_detector/tests/ -v

# With coverage
pytest apps/duplicate_detector/tests/ --cov=apps.duplicate_detector --cov-report=html
```

### Test Coverage
- **Routes**: All 5 Flask routes tested
- **Duplicate Detection**: Similarity calculation, grouping, filtering
- **PDF Generation**: Report creation, error handling
- **Error Handling**: Connection failures, invalid data, exceptions
- **Integration**: Complete workflow from analysis to PDF

### Test Fixtures
Located in `tests/conftest.py`:
- `client`: Flask test client
- `mock_jira_client`: Mocked Jira API
- `sample_story`: Single story for testing
- `sample_duplicate_story`: Duplicate of sample story
- `sample_stories`: Multiple stories with duplicates
- `sample_duplicate_analysis`: Complete analysis structure
- `mock_duplicate_detector`: Mocked detector
- `mock_pdf_generator`: Mocked PDF generator

## Troubleshooting

### Common Issues

**No Duplicates Found**
- Lower similarity threshold in detector.py
- Check that stories have meaningful summaries
- Verify JQL query returns stories (not epics or tasks)
- Ensure sufficient issue count (need at least 2 issues)

**Too Many False Positives**
- Increase similarity threshold (try 0.80 or 0.85)
- Focus on summary similarity only
- Add more specific JQL filters

**Slow Performance**
- Limit JQL query scope (specific project, date range)
- Reduce number of issues analyzed
- Consider analyzing in batches

**PDF Generation Failed**
- Ensure reportlab is installed
- Check sufficient disk space for temporary files
- Verify all required data fields are present

## Performance Considerations

- **Analysis Speed**: O(n²) complexity for pairwise comparison
- **Small Dataset** (< 50 issues): < 5 seconds
- **Medium Dataset** (50-200 issues): 5-30 seconds
- **Large Dataset** (200+ issues): 30-120 seconds

**Optimization Tips:**
- Use specific JQL queries to reduce issue count
- Filter by project, date range, or status
- Analyze open stories only (closed stories less relevant)

## Use Cases

### Backlog Refinement
- Identify duplicate work before sprint planning
- Clean up backlog quality
- Merge similar stories

### Quality Assurance
- Detect accidental duplicate creation
- Ensure unique story definitions
- Maintain backlog integrity

### Knowledge Discovery
- Find related work across teams
- Identify common themes
- Consolidate similar requests

### Team Collaboration
- Share duplicate analysis with product owners
- Facilitate story consolidation discussions
- Improve backlog organization

## Configuration

### Similarity Threshold
Default: 0.70 (70% similarity)

To adjust, modify in `detector.py`:
```python
SIMILARITY_THRESHOLD = 0.75  # Increase for stricter matching
```

### Comparison Weight
Default: Summary 70%, Description 30%

To adjust weights in `detector.py`:
```python
SUMMARY_WEIGHT = 0.8  # Increase summary importance
DESCRIPTION_WEIGHT = 0.2  # Decrease description importance
```

## Migration Notes

This application was migrated from a monolithic structure to a modular architecture:
- **Code Reduction**: Eliminated duplicate Jira client code
- **Shared Libraries**: Now uses centralized JiraClient
- **Improved Testing**: Added 40+ comprehensive unit tests
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
- Added comprehensive test suite (40+ tests)
- Improved error handling and logging
- Enhanced PDF reports
- Added health check endpoint

**1.0.0** (Legacy)
- Original monolithic implementation
- Basic duplicate detection
- Simple PDF reports

## Future Enhancements

### Potential Improvements
1. **Machine Learning**: Use ML models for better similarity detection
2. **Fuzzy Matching**: Add fuzzy string matching (Levenshtein distance)
3. **Stemming/Lemmatization**: NLP techniques for better text comparison
4. **Bulk Operations**: Bulk merge or link detected duplicates
5. **Scheduled Analysis**: Automated periodic duplicate detection
6. **Configurable Thresholds**: UI-based threshold configuration
7. **Visual Similarity Matrix**: Heatmap of issue similarities
8. **Smart Suggestions**: Recommend which duplicate to keep

## References

- [Text Similarity with SequenceMatcher](https://docs.python.org/3/library/difflib.html)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Backlog Management Best Practices](https://www.atlassian.com/agile/product-management/backlogs)
