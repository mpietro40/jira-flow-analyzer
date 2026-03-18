# Perseus Lead Time 🚀

> **Status: Undergoing Major Refactoring** 📦  
> We're reorganizing the project for better maintainability and testing. See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for details.

A comprehensive suite of Jira analysis tools for tracking initiatives, epics, sprints, and team metrics.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Applications](#applications)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Quick Start

### Run All Applications (Docker)
```bash
docker-compose up
```
Access the unified dashboard at http://localhost:5000

### Run Individual Application
```bash
cd apps/initiative_viewer
python run.py
```
Access at http://localhost:5001

### Build Executables
```bash
python build/build_all.py
# Executables will be in build/executables/
```

## 📱 Applications

### Web Applications

| Application | Description | Port | Status |
|------------|-------------|------|--------|
| **Unified Dashboard** | All-in-one access point | 5000 | ✅ Active |
| **Initiative Viewer** | Hierarchical initiative tracking | 5001 | ✅ Active |
| **Epic Report** | Epic analysis and reporting | 5002 | ✅ Active |
| **PI Analyzer** | Program Increment analysis | 5003 | ✅ Active |
| **Sprint Analyzer** | Sprint metrics and analysis | 5004 | ✅ Active |
| **Epic Fix Version** | Fix version tracking | 5005 | ✅ Active |
| **PBC Analyzer** | Program Backlog Commitment | 5006 | ✅ Active |
| **Duplicate Detector** | Find duplicate issues | 5007 | ✅ Active |
| **Psychological Safety** | Team safety metrics | 5008 | ✅ Active |

### CLI Tools

Located in `scripts/`:
- **Backward Check Analyzer**: Analyze backward dependencies
- **Data Analyzer**: General Jira data analysis
- **Lead Time Analyzer**: Track lead times
- **Jira Utils**: Status changers, field discovery
- **User Auditor**: Audit Jira user activity

## 💻 Installation

### Prerequisites
- Python 3.8+
- pip
- (Optional) Docker & Docker Compose

### Standard Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/PerseusLeadTime.git
cd PerseusLeadTime

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run all apps
python launch_all.py
```

### Development Installation
```bash
# Install with development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov=apps --cov-report=html
```

## 🎯 Usage

### Web Applications

Each application has its own folder with a dedicated launcher:

```bash
# Method 1: Individual app
cd apps/initiative_viewer
python run.py

# Method 2: Direct Python module
python -m apps.initiative_viewer.app

# Method 3: Use launcher script
./launch_all.bat  # Windows
./launch_all.sh   # Linux/Mac
```

### CLI Scripts

```bash
# Example: Run backward check analyzer
cd scripts/backward_check
python analyzer.py --help

# Example: Discover custom fields
cd scripts/jira_utils
python discover_custom_fields.py
```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 🛠️ Development

### Project Structure

```
PerseusLeadTime/
├── src/              # Shared code
│   ├── common/       # Shared utilities
│   └── config/       # Configuration
├── apps/             # Web applications
│   └── {app_name}/   # Each app is self-contained
├── scripts/          # CLI tools
├── tests/            # Integration tests
├── build/            # Build system
└── docs/             # Documentation
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

### Adding a New Application

1. Create app folder: `apps/my_new_app/`
2. Use template from `apps/initiative_viewer/`
3. Implement app logic in `app.py`
4. Add tests in `tests/`
5. Create `build.py` for executable
6. Update `docker-compose.yml`
7. Add documentation

### Code Standards

- Follow PEP 8
- Use type hints
- Write docstrings
- Maintain 85%+ test coverage
- Run `pytest` before committing

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Suite
```bash
# Test specific app
pytest apps/initiative_viewer/tests/

# Test shared code
pytest tests/shared/

# Test integration
pytest tests/integration/
```

### Coverage Report
```bash
pytest --cov=src --cov=apps --cov-report=html
# Open htmlcov/index.html
```

### Test Requirements
- All new code must have tests
- Maintain 85%+ coverage
- Tests must pass before merging

## 🚀 Deployment

### Render (Recommended for Web Apps)
See [docs/deployment/render.md](docs/deployment/render.md)

### Docker
See [docs/deployment/docker.md](docs/deployment/docker.md)

### Standalone Executables
```bash
python build/build_all.py
```
Executables in `build/executables/`

See [docs/deployment/standalone-executables.md](docs/deployment/standalone-executables.md)

### Heroku
See [docs/deployment/heroku.md](docs/deployment/heroku.md)

## 📚 Documentation

- **[Getting Started](docs/getting-started/)**: Installation and quick start
- **[Deployment Guides](docs/deployment/)**: Deploy to various platforms
- **[User Guides](docs/guides/)**: How to use each application
- **[Development](docs/development/)**: Contributing and architecture
- **[API Documentation](docs/api/)**: Shared code API reference

Full documentation index: [docs/INDEX.md](docs/INDEX.md)

## 🤝 Contributing

We welcome contributions! Please see [docs/development/contributing.md](docs/development/contributing.md) for guidelines.

### Quick Contributing Steps

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure tests pass and coverage is maintained
5. Submit a pull request

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

Built with:
- Flask
- ReportLab
- Pandas
- Matplotlib
- PyInstaller
- Many other great open source libraries

## 📞 Support

- 📖 [Documentation](docs/INDEX.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/PerseusLeadTime/issues)
- 💬 [Discussions](https://github.com/yourusername/PerseusLeadTime/discussions)

---

**Version**: 2.0.0 (Refactored)  
**Status**: Active Development  
**Last Updated**: February 2026
