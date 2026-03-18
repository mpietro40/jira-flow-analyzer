# Initiative Viewer

**Version:** 2.0.0  
**Author:** Pietro Maffi  
**Port:** 5001 (default)

## Overview

The Initiative Viewer is a Flask-based web application that visualizes hierarchical Jira structures in a clear, organized manner:

```
Business Initiative
├── Feature (filtered by Fix Version)
│   └── Sub-Feature (filtered by Fix Version)
│       └── Epic (grouped by Area/Project)
│           └── Color-coded by Risk Probability (1-5 scale)
```

## Features

- **Hierarchical Visualization**: Navigate through 4 levels of Jira hierarchy
- **Risk Probability Color Coding**: Visual risk assessment (1=Low → 5=High)
- **Area-Based Organization**: Epics grouped by project/area for clarity
- **Fix Version Filtering**: Focus on specific program increments
- **Multiple Export Formats**: PDF, PDF Wide, HTML, Confluence Wiki
- **Caching**: 30-minute cache to improve performance
- **Modern UI**: Responsive design with smooth animations

## Quick Start

### Option 1: Run Standalone

```bash
cd apps/initiative_viewer
python run.py
```

The application will open automatically in your default browser at `http://localhost:5001`.

### Option 2: Run via Launcher

```bash
# From project root
python launch_all.py --apps initiative_viewer
```

### Option 3: Docker

```bash
cd build/docker
docker-compose up initiative_viewer
```

## Usage

1. **Enter Jira Credentials**
   - Jira URL: Your Atlassian instance (e.g., `https://company.atlassian.net`)
   - Access Token: Generate from Jira → Account Settings → Security → API Tokens

2. **Configure Query**
   - JQL Query: Filter Business Initiatives (e.g., `project = ISDOP`)
   - Fix Version: Target PI/version (e.g., `PI 2025.1`)

3. **Analyze**
   - Click "Analyze Initiatives"
   - View hierarchical results
   - Export as needed

## Risk Probability Scale

| Level | Description | Color |
|-------|-------------|-------|
| 1 | Low Risk | Light Green |
| 2 | Low-Medium | Yellow |
| 3 | Medium | Orange |
| 4 | Medium-High | Dark Orange |
| 5 | High Risk | Red |

## Export Options

- **PDF**: Vertical layout, one initiative per page
- **PDF Wide**: Horizontal layout, all areas in table format
- **HTML**: Shareable HTML file with embedded styles
- **Confluence Wiki**: Copy-paste ready wiki markup  

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `production` or `development`
- `SECRET_KEY`: Flask secret key (auto-generated if not set)
- `CACHE_DIR`: Cache storage directory (default: `data/cache/initiative_viewer`)
- `STORAGE_DIR`: Data storage directory (default: `data/storage/initiative_viewer`)

### Customization

Edit [app.py](app.py) to modify:
- Port number (default: 5001)
- Cache duration (default: 30 minutes)
- Completed statuses list
- Risk probability mappings

## Architecture

```
apps/initiative_viewer/
├── app.py                    # Main Flask application
├── pdf_generator.py          # PDF generation (extends PDFGeneratorBase)
├── run.py                    # Standalone launcher
├── README.md                 # This file
├── templates/
│   ├── initiative_form.html  # Input form
│   └── initiative_hierarchy.html  # Results view
└── tests/                    # Unit tests
    ├── test_app.py
    ├── test_pdf_generator.py
    └── test_hierarchy_fetcher.py
```

## Dependencies

Core:
- Flask 3.0+
- Waitress 3.0+ (production server)
- ReportLab 4.0+ (PDF generation)

Shared:
- `src.common.JiraClient`: Jira API integration
- `src.common.CacheManager`: File-based caching
- `src.common.FileStorage`: Safe file operations
- `src.common.flask_utils`: Flask decorators and utilities
- `src.common.PDFGeneratorBase`: Base PDF generator

## Testing

```bash
# Run tests
cd apps/initiative_viewer
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_app.py::test_index
```

## Troubleshooting

**Connection Error**
- Verify Jira URL (no trailing slash)
- Check firewall settings
- Validate API token (may expire)

**No Data Returned**
- Check JQL query syntax in Jira
- Verify Fix Version spelling (case-sensitive)
- Ensure Business Initiatives exist matching query

**Slow Performance**
- Use cache (loads in seconds for repeated queries)
- Limit number of initiatives
- Check network connection to Jira

**Risk Probability Not Showing**
- Jira custom fields vary by instance
- Check field name contains "risk" and "probability"/"status"
- Valid values: 1-5 (numeric) or Green/Yellow/Red (text)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Display input form |
| `/analyze` | POST | Fetch and analyze Jira hierarchy |
| `/export_pdf` | GET | Export as PDF (vertical) |
| `/export_pdf_wide` | GET | Export as PDF (horizontal) |
| `/export_html` | GET | Export as standalone HTML |
| `/export_confluence_wiki` | GET | Export as Confluence markup |
| `/health` | GET | Health check endpoint |

## Version History

### 2.0.0 (2025)
- Complete rewrite with modular architecture
- Shared library integration (JiraClient, CacheManager, etc.)
- Enhanced PDF generation with base class
- Improved caching with metadata
- Better error handling with decorators
- Health check endpoint for monitoring

### 1.0.0 (Previous)
- Original monolithic implementation
- Basic PDF export
- File-based data storage

## License

Internal use only. © Bosch.

## Support

For questions or issues:
- Author: Pietro Maffi
- Documentation: [ARCHITECTURE.md](../../ARCHITECTURE.md)
- API Reference: [docs/api/README.md](../../docs/api/README.md)
