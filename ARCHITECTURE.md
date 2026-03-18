# Perseus Lead Time - Architecture

## Overview

Perseus Lead Time is a suite of Jira analysis tools designed to help teams track and analyze their work using Jira data. The system is organized into multiple independent web applications and CLI tools that share common infrastructure.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│  Web Apps (Flask) │ Executables │ CLI Scripts │ Docker  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│  Initiative Viewer │ Epic Report │ PI Analyzer │ etc.   │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Shared Services                       │
│  Jira Client │ PDF Generator │ Cache │ File Storage     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   External Services                      │
│              Jira REST API │ File System                 │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Shared Infrastructure (`src/common/`)
- **Jira Client**: Unified API client for all Jira operations
- **PDF Generator Base**: Base class for PDF report generation
- **Cache Manager**: Caching layer for Jira data
- **File Storage**: File-based session storage
- **Visualization**: Shared charting and visualization utilities

### 2. Web Applications (`apps/`)
Each web application is self-contained with:
- Flask application
- Templates and static assets
- PDF generator (if applicable)
- Comprehensive test suite
- Individual launcher and build script

**Applications:**
- Initiative Viewer: Hierarchical initiative tracking
- Epic Report: Epic analysis and reporting
- Epic Fix Version: Fix version tracking
- PI Analyzer: Program Increment analysis
- Sprint Analyzer: Sprint metrics and analysis
- PBC Analyzer: Program Backlog Commitment tracking
- Duplicate Detector: Find duplicate issues
- Psychological Safety: Team safety metrics
- Unified Dashboard: All-in-one access point

### 3. CLI Tools (`scripts/`)
Command-line utilities for batch operations and automation.

### 4. Build System (`build/`)
- PyInstaller configuration for all apps
- Unified build scripts
- Executable output management

## Design Principles

1. **Separation of Concerns**: Each app is independent
2. **DRY (Don't Repeat Yourself)**: Shared code in `src/common/`
3. **Testability**: Every component has tests
4. **Deployability**: Multiple deployment options (Docker, executables, cloud)
5. **Maintainability**: Clear structure and documentation

## Data Flow

1. User submits form with Jira credentials and query
2. App validates input
3. Jira Client fetches data from Jira API
4. Data is cached for performance
5. App processes and analyzes data
6. Results displayed in web UI
7. Optional PDF export via PDF Generator

## Technology Stack

- **Backend**: Python 3.8+, Flask 3.0
- **Server**: Waitress (production), Flask dev server (development)
- **PDF Generation**: ReportLab
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Testing**: pytest, pytest-cov, pytest-mock
- **Build**: PyInstaller
- **Deployment**: Docker, Render, Heroku

## Security

- No credentials stored in code
- Session-based authentication
- File-based temporary storage with cleanup
- HTTPS recommended for production

## Performance

- Jira API caching reduces redundant calls
- Adaptive batch sizing for large queries
- Timeout configuration for slow connections
- File-based storage to avoid cookie size limits

## Future Enhancements

- Database backend option (PostgreSQL)
- User authentication system
- API for programmatic access
- Real-time updates via WebSockets
- Advanced analytics and ML features
