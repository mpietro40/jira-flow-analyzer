# Test Results

This directory contains test execution results and reports.

## Contents

- **test_reports/** - HTML and XML test reports
- **coverage_reports/** - Code coverage analysis
- **screenshots/** - Visual evidence of functionality
- **logs/** - Test execution logs

## Generating Reports

### Run Tests with HTML Report
```bash
pytest ATDD/acceptance_tests/ -v --html=ATDD/test_results/report.html --self-contained-html
```

### Generate Coverage Report
```bash
pytest ATDD/acceptance_tests/ -v --cov=. --cov-report=html:ATDD/test_results/coverage
```

### Generate JUnit XML Report
```bash
pytest ATDD/acceptance_tests/ -v --junitxml=ATDD/test_results/junit.xml
```

## Latest Results

Test results are automatically generated when running the test suite. Check the timestamp on files to see the most recent execution.

## CI/CD Integration

These reports can be integrated with CI/CD pipelines:
- Jenkins: Use JUnit XML plugin
- GitLab CI: Artifact reports
- GitHub Actions: Test reporting actions
