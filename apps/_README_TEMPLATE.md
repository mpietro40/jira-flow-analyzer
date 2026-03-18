# {APP_NAME} - Template README

> Copy this template for each application in apps/{app_name}/README.md

# [Application Name]

Brief description of what this application does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Quick Start

```bash
# Run in development mode
python run.py

# Or from project root
cd apps/{app_name}
python run.py
```

Access at http://localhost:{PORT}

## Requirements

- Jira URL
- Access Token
- [Any specific requirements]

## Usage

### Step 1: Enter Credentials

- **Jira URL**: Your Jira instance
- **Access Token**: Personal Access Token

### Step 2: Configure Analysis

[Describe the input parameters]

### Step 3: Analyze

Click "Analyze" to process data

### Step 4: View Results

[Describe what the user will see]

### Step 5: Export (if applicable)

[Describe export options]

## Configuration

### Environment Variables

```bash
# Optional configuration
FLASK_ENV=development
APP_PORT={PORT}
CACHE_ENABLED=true
```

### Configuration File

See `config.py` for available settings.

## Testing

```bash
# Run tests for this app
pytest tests/

# With coverage
pytest --cov=. tests/

# Specific test file
pytest tests/test_app.py
```

## Building Executable

```bash
# Build standalone executable
python build.py

# Executable will be in: ../../build/executables/{AppName}.exe
```

## Docker

```bash
# Build Docker image
docker build -t {app_name} .

# Run container
docker run -p {PORT}:{PORT} {app_name}
```

## API Endpoints

### Web Routes

- `GET /` - Main form
- `POST /analyze` - Process analysis
- `GET /export_pdf` - Export results as PDF
- [Add other routes]

## Dependencies

### Required
- Flask 3.0+
- Jira Client (from src.common)
- [Other required dependencies]

### Optional
- [Optional dependencies]

## Troubleshooting

### Issue: [Common Issue 1]
**Solution**: [How to fix]

### Issue: [Common Issue 2]
**Solution**: [How to fix]

## Development

### File Structure

```
{app_name}/
├── app.py                 # Main Flask application
├── pdf_generator.py       # PDF generation (if applicable)
├── run.py                 # Development launcher
├── build.py               # Executable build script
├── {app_name}.spec        # PyInstaller configuration
├── requirements.txt       # App-specific requirements
├── README.md              # This file
├── static/                # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # HTML templates
│   ├── form.html
│   ├── results.html
│   └── components/
└── tests/                 # Test suite
    ├── __init__.py
    ├── conftest.py
    ├── test_app.py
    ├── test_pdf_generator.py
    ├── test_integration.py
    └── fixtures/
        └── mock_data.py
```

### Adding Features

1. Update `app.py` with new routes
2. Add templates as needed
3. Write tests for new functionality
4. Update this README
5. Update user guide in `docs/guides/`

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Maintain test coverage above 85%

## Contributing

See [Contributing Guide](../../docs/development/contributing.md)

## License

[License information]

## Related Documentation

- [Main README](../../README.md)
- [Architecture](../../ARCHITECTURE.md)
- [User Guide](../../docs/guides/{app_name}.md)
- [API Documentation](../../docs/api/)

## Support

- Report issues: [GitHub Issues](https://github.com/yourusername/PerseusLeadTime/issues)
- Ask questions: [Discussions](https://github.com/yourusername/PerseusLeadTime/discussions)

---

**Version**: 2.0.0
**Port**: {PORT}
**Status**: Active
