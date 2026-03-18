# Unified Dashboard - Jira Analytics Suite

Central navigation and gateway application for the complete Jira Analytics Suite. Provides a single entry point to access all analytics applications with health monitoring and backward-compatible proxy routes.

## Overview

The Unified Dashboard serves as the main landing page and routing gateway for all Jira analytics applications. It's a lightweight Flask application that orchestrates access to 8 independent microservices, each running on dedicated ports.

## Key Features

- **Dashboard Landing Page**: Professional homepage showcasing all available applications
- **Service Discovery**: Dynamic application listing via `/apps` API
- **Health Check Aggregation**: Monitors status of all registered applications
- **Smart Navigation**: Direct redirects to individual application services
- **Backward Compatible Proxies**: Proxy routes for legacy integrations
- **No Business Logic**: Pure routing layer - delegates all analysis to microservices
- **Production Ready**: Waitress WSGI server support
- **Error Handling**: Comprehensive error handlers and graceful degradation

## Architecture

### Gateway Pattern

```
User Request
     ↓
Unified Dashboard (Port 5000)
     ↓
[Route/Redirect]
     ↓
Individual Applications (Ports 5001-5008)
```

### Registered Applications

| Application | Port | Icon | Description |
|-------------|------|------|-------------|
| **Initiative Viewer** | 5001 | 🗂️ | 4-level hierarchical initiative visualization |
| **Epic Report** | 5002 | 📜 | Parent epic discovery and child count analysis |
| **PI Analyzer** | 5003 | 📅 | Program Increment planning and capacity analysis |
| **Sprint Analyzer** | 5004 | 🏃 | Sprint capacity and velocity forecasting |
| **PBC Analyzer** | 5005 | 📈 | Process Behavior Charts for lead time trends |
| **Duplicate Detector** | 5006 | 📋 | Find duplicate issues with similarity analysis |
| **Psychological Safety** | 5007 | ❤️ | Team psychological safety metrics |
| **Epic Fix Version** | 5008 | 🔀 | Epic distribution by fix version |

### Components

```
apps/unified_dashboard/
├── __init__.py           # Package initialization (Port 5000)
├── app.py                # Flask gateway application (343 lines)
├── config.py             # Application registry and configuration
├── run.py                # Standalone launcher
├── requirements.txt      # Dependencies
├── templates/
│   └── dashboard.html    # Main landing page
└── tests/
    ├── __init__.py
    ├── conftest.py       # Test fixtures (96 lines, 9 fixtures)
    └── test_app.py       # Test suite (348 lines, 35+ tests)
```

### Technology Stack

- **Flask 3.0.3**: Web framework
- **Waitress 3.0.2**: Production WSGI server (Windows-compatible)
- **Requests**: HTTP client for health checks and proxying
- **Bootstrap 5.1.3**: Frontend UI framework
- **Font Awesome 6.0**: Icons

## Installation

### Prerequisites

- Python 3.8-3.11
- All 8 analytics applications installed and configured
- Ports 5000-5008 available

### Setup

```bash
# From workspace root
pip install -r requirements.txt

# Or install specific app dependencies
cd apps/unified_dashboard
pip install -r requirements.txt
```

## Usage

### Running the Dashboard

#### Standalone Mode

```bash
# From apps/unified_dashboard directory
python run.py

# Or from workspace root
python -m apps.unified_dashboard.app
```

#### Production Mode (with Waitress)

```bash
# From workspace root
python apps/unified_dashboard/app.py
```

Dashboard will be available at: **http://localhost:5000**

### Accessing Applications

1. **Via Dashboard**: Navigate to http://localhost:5000 and click on any application card
2. **Direct URL**: Go directly to application ports (5001-5008)
3. **Navigation Routes**: Use `/initiative-viewer`, `/epic-report`, etc.

### Running All Services

To use the full suite, start all services:

```bash
# Terminal 1 - Initiative Viewer
python apps/initiative_viewer/run.py

# Terminal 2 - Epic Report
python apps/epic_report/run.py

# Terminal 3 - PI Analyzer
python apps/pi_analyzer/run.py

# Terminal 4 - Sprint Analyzer
python apps/sprint_analyzer/run.py

# Terminal 5 - PBC Analyzer
python apps/pbc_analyzer/run.py

# Terminal 6 - Duplicate Detector
python apps/duplicate_detector/run.py

# Terminal 7 - Psychological Safety
python apps/psychological_safety/run.py

# Terminal 8 - Epic Fix Version
python apps/epic_fixversion/run.py

# Terminal 9 - Unified Dashboard
python apps/unified_dashboard/run.py
```

Then navigate to: http://localhost:5000

## API Reference

### Routes

#### Dashboard & Navigation

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Main dashboard landing page |
| `/apps` | GET | List all registered applications (JSON) |
| `/health` | GET | Aggregated health check across all services |
| `/favicon.ico` | GET | Favicon handler (204 No Content) |

#### Application Navigation (Redirects)

| Route | Method | Redirect To | Description |
|-------|--------|-------------|-------------|
| `/initiative-viewer` | GET | Port 5001 | Initiative Viewer |
| `/lead-time` | GET | Port 5001 | Lead Time Analyzer (alias) |
| `/epic-report` | GET | Port 5002 | Epic Report |
| `/epic-analyzer` | GET | Port 5002 | Epic Analyzer (alias) |
| `/pi-analyzer` | GET | Port 5003 | PI Analyzer |
| `/sprint-analyzer` | GET | Port 5004 | Sprint Analyzer |
| `/pbc-analyzer` | GET | Port 5005 | PBC Analyzer |
| `/duplicate-detector` | GET | Port 5006 | Duplicate Detector |
| `/psychological-safety` | GET | Port 5007 | Psychological Safety |
| `/epic-fixversion` | GET | Port 5008 | Epic Fix Version |

#### Proxy Routes (Backward Compatibility)

| Route | Method | Proxy To | Description |
|-------|--------|----------|-------------|
| `/analyze_epic_fixversion` | POST | Port 5008 `/analyze` | Epic fix version analysis |
| `/export_epic_fixversion_pdf` | POST | Port 5008 `/export_pdf` | Epic fix version PDF export |
| `/analyze_safety` | POST | Port 5007 `/analyze_safety` | Psychological safety analysis |
| `/get_trends` | POST | Port 5007 `/get_trends` | Psychological safety trends |
| `/analyze_pbc` | POST | Port 5005 `/analyze` | PBC analysis |

### API Examples

#### List All Applications

```bash
curl http://localhost:5000/apps
```

**Response:**
```json
{
  "success": true,
  "total_apps": 8,
  "apps": [
    {
      "id": "initiative_viewer",
      "name": "Initiative Viewer",
      "description": "4-level hierarchical initiative visualization",
      "url": "http://localhost:5001",
      "port": 5001,
      "icon": "fa-sitemap",
      "color": "#667eea"
    },
    ...
  ]
}
```

#### Health Check

```bash
curl http://localhost:5000/health
```

**Response (All Healthy):**
```json
{
  "status": "healthy",
  "dashboard": "healthy",
  "port": 5000,
  "timestamp": "2026-02-20T10:30:00",
  "apps": {
    "total": 8,
    "healthy": 8,
    "unhealthy": 0
  },
  "details": [
    {
      "id": "initiative_viewer",
      "name": "Initiative Viewer",
      "status": "healthy",
      "port": 5001,
      "response_time_ms": 45.2
    },
    ...
  ]
}
```

**Response (Some Services Down):**
```json
{
  "status": "degraded",
  "dashboard": "healthy",
  "port": 5000,
  "timestamp": "2026-02-20T10:30:00",
  "apps": {
    "total": 8,
    "healthy": 6,
    "unhealthy": 2
  },
  "details": [
    {
      "id": "initiative_viewer",
      "name": "Initiative Viewer",
      "status": "healthy",
      "port": 5001,
      "response_time_ms": 45.2
    },
    {
      "id": "epic_report",
      "name": "Epic Report",
      "status": "unreachable",
      "port": 5002,
      "error": "Service not running"
    },
    ...
  ]
}
```

#### Using Proxy Routes

Proxy routes forward requests to individual services:

```bash
# Via dashboard proxy
curl -X POST http://localhost:5000/analyze_epic_fixversion \ -d "jira_url=https://company.atlassian.net" \
  -d "access_token=$PAT" \
  -d "initiative_jql=project = INIT" \
  -d "fix_version=2026-Q1"

# Equivalent direct call to service
curl -X POST http://localhost:5008/analyze \
  -d "jira_url=https://company.atlassian.net" \
  -d "access_token=$PAT" \
  -d "initiative_jql=project = INIT" \
  -d "fix_version=2026-Q1"
```

Both produce identical results. Proxy routes exist for backward compatibility.

## Configuration

### Application Registry ([config.py](config.py))

The `APPS` dictionary in [config.py](config.py) registers all available applications:

```python
APPS = {
    'app_id': {
        'name': 'Display Name',
        'description': 'Brief description',
        'url': 'http://localhost:PORT',
        'port': PORT,
        'icon': 'fa-icon-name',
        'color': '#hex-color'
    },
    ...
}
```

### Environment Variables

- `PORT`: Server port (default: 5000)
- `FLASK_ENV`: Environment mode (development/production)
- `SECRET_KEY`: Flask secret key (change in production)

### Health Check Timeout

Configure health check timeout in [config.py](config.py):

```python
HEALTH_CHECK_TIMEOUT = 2  # seconds
```

## Testing

### Run Tests

```bash
# From workspace root
pytest apps/unified_dashboard/tests/ -v

# With coverage
pytest apps/unified_dashboard/tests/ -v --cov=apps.unified_dashboard --cov-report=term-missing

# Run specific test class
pytest apps/unified_dashboard/tests/test_app.py::TestHealthCheck -v
```

### Test Coverage

The test suite includes **35+ tests** across 10 test classes:

1. **TestDashboardRoute** (2 tests): Landing page functionality
2. **TestAppsListAPI** (2 tests): Application listing API
3. **TestHealthCheck** (5 tests): Health check aggregation scenarios
4. **TestFaviconRoute** (1 test): Favicon handling
5. **TestNavigationRoutes** (10 tests): Navigation redirects
6. **TestProxyRoutes** (8 tests): Proxy route functionality
7. **TestErrorHandlers** (2 tests): Error page handling
8. **TestConfiguration** (3 tests): Configuration validation
9. **TestIntegration** (2+ tests): End-to-end workflows

**Target Coverage**: >80%

### Test Fixtures

Available fixtures (see [conftest.py](tests/conftest.py)):

- `client`: Flask test client
- `apps_config`: Application configuration
- `mock_health_response`: Mock successful health response
- `mock_health_response_unhealthy`: Mock unhealthy response
- `sample_app_list`: Sample application list
- `mock_successful_requests`: Mock successful HTTP requests
- `mock_timeout_requests`: Mock timeout scenarios
- `mock_connection_error_requests`: Mock connection errors
- `mock_proxy_response`: Mock proxy responses

## Dashboard Features

### Landing Page

The dashboard ([templates/dashboard.html](templates/dashboard.html)) provides:

- **Hero Section**: Suite overview with statistics
- **Application Cards**: Interactive cards for each application
  - Icon and color coding
  - Feature highlights
  - Launch buttons
- **Navigation Bar**: Quick access to dashboard and presentations
- **Responsive Design**: Mobile and desktop friendly
- **Bootstrap 5 Styling**: Modern, professional appearance

### Health Monitoring

The `/health` endpoint provides:

- **Overall Status**: healthy/degraded/unhealthy
- **Individual App Status**: Per-service health with response times
- **Error Details**: Specific error messages for failed checks
- **Timestamp**: When health check was performed

### Service Discovery

The `/apps` API enables:

- **Dynamic Application Listing**: Programmatic access to registered apps
- **Metadata Retrieval**: Name, description, URL, port, icon, color
- **Integration Support**: Easy integration with other tools

## Deployment

### Production Deployment

1. **Set Environment Variables**:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secret-key-here
   export PORT=5000
   ```

2. **Start Dashboard**:
   ```bash
   python apps/unified_dashboard/app.py
   ```

3. **Start All Services**: Ensure all 8 applications (ports 5001-5008) are running

### Docker Deployment (Future)

```dockerfile
# Dockerfile for unified dashboard
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY apps/unified_dashboard ./apps/unified_dashboard
CMD ["python", "apps/unified_dashboard/app.py"]
```

### Load Balancer Configuration

If using a reverse proxy (nginx, Apache):

```nginx
# nginx configuration
upstream jira_dashboard {
    server localhost:5000;
}

server {
    listen 80;
    server_name analytics.yourcompany.com;
    
    location / {
        proxy_pass http://jira_dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Dashboard Loads But Apps Are Unreachable

**Problem**: Dashboard at port 5000 works, but clicking apps returns "Service not running"

**Solutions**:
1. Verify all services are running: `curl http://localhost:5001/health` (5001-5008)
2. Check firewall allows localhost connections on all ports
3. Review health check output: `curl http://localhost:5000/health`

### Health Check Shows Timeouts

**Problem**: Health check reports timeout for some services

**Solutions**:
1. Increase `HEALTH_CHECK_TIMEOUT` in [config.py](config.py)
2. Check if services are overloaded (increase resources)
3. Verify services respond to `/health` endpoint

### Proxy Routes Fail

**Problem**: Proxy routes return 503 errors

**Solutions**:
1. Verify target service is running
2. Check service accepts POST requests on proxy target endpoint
3. Increase proxy timeout (default 60 seconds)
4. Review service logs for errors

### Port Already in Use

**Problem**: `Address already in use` error when starting dashboard

**Solutions**:
1. Stop existing process on port 5000
2. Change port: `PORT=5001 python apps/unified_dashboard/app.py`
3. Find and kill process: `lsof -ti:5000 | xargs kill -9` (Unix) or `netstat -ano | findstr :5000` (Windows)

## Migration Notes

**From Original main_app.py:**

- **Original**: 1,010 lines (monolithic application with embedded business logic)
- **Migrated**: 343 lines (pure routing gateway)
- **Line Reduction**: 66% (667 lines removed)
- **Test Coverage**: Added 35+ tests (0 → 348 lines)
- **Documentation**: Added comprehensive README

**Key Improvements:**
- Removed all embedded business logic (moved to individual apps)
- Eliminated duplicate Jira client imports
- Removed complex analysis functions
- Added health check aggregation
- Added service discovery API
- Maintained backward compatibility with proxy routes
- Production-ready with Waitress
- Comprehensive test coverage

**Architecture Shift:**
- Monolithic → Microservices Gateway
- Embedded Logic → Delegated to Services
- Direct Imports → HTTP Redirects/Proxies

## Common Use Cases

### 1. Local Development

Start only the apps you're working on:

```bash
# Start just initiative viewer and dashboard
python apps/initiative_viewer/run.py &
python apps/unified_dashboard/run.py
```

### 2. Full Suite Demo

Start all services for a complete demo:

```bash
# Start script (Unix)
for port in 5001 5002 5003 5004 5005 5006 5007 5008; do
    python apps/$(app_name_for_port $port)/run.py &
done
python apps/unified_dashboard/run.py
```

### 3. Health Monitoring

Use health check for monitoring:

```bash
# Check every 60 seconds
watch -n 60 'curl -s http://localhost:5000/health | jq .'
```

### 4. Backward Compatible Integration

Existing integrations continue to work via proxy routes:

```python
# Old code - still works
import requests

response = requests.post(
    'http://localhost:5000/analyze_epic_fixversion',
    data={'jira_url': url, 'access_token': token, ...}
)
```

## Support

For issues, feature requests, or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review test cases in [test_app.py](tests/test_app.py) for usage examples
3. Consult [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) for migration details
4. Check individual application READMEs for app-specific issues

## Related Applications

- **Initiative Viewer** (Port 5001): See [apps/initiative_viewer/README.md](../initiative_viewer/README.md)
- **Epic Report** (Port 5002): See [apps/epic_report/README.md](../epic_report/README.md)
- **PI Analyzer** (Port 5003): See [apps/pi_analyzer/README.md](../pi_analyzer/README.md)
- **Sprint Analyzer** (Port 5004): See [apps/sprint_analyzer/README.md](../sprint_analyzer/README.md)
- **PBC Analyzer** (Port 5005): See [apps/pbc_analyzer/README.md](../pbc_analyzer/README.md)
- **Duplicate Detector** (Port 5006): See [apps/duplicate_detector/README.md](../duplicate_detector/README.md)
- **Psychological Safety** (Port 5007): See [apps/psychological_safety/README.md](../psychological_safety/README.md)
- **Epic Fix Version** (Port 5008): See [apps/epic_fixversion/README.md](../epic_fixversion/README.md)

## Version History

- **v2.0.0** (2026-02-20): Complete migration to gateway pattern
  - Converted from monolithic to microservices gateway
  - Removed all embedded business logic (667 lines)
  - Added health check aggregation
  - Added service discovery API
  - Added comprehensive test suite (35+ tests)
  - Maintained backward compatibility with proxy routes
  - Production-ready deployment with Waitress

- **v1.0.0** (Original): Monolithic main_app.py
  - Combined dashboard and business logic
  - Direct imports of all analytics components
  - 1,010 lines of mixed concerns
