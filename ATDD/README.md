# Acceptance Test-Driven Development (ATDD)

This folder contains all acceptance criteria and acceptance tests that validate the functionality of the Jira Lead Time Analyzer application.

## Structure

- **acceptance_criteria/** - Detailed acceptance criteria for each feature
- **acceptance_tests/** - Executable acceptance tests that prove functionality
- **test_results/** - Test execution results and reports

## Coverage

The ATDD suite covers:
1. Jira API Integration
2. Data Analysis & Metrics Calculation
3. Hierarchical Analysis
4. Visualization Generation
5. CSV Import Functionality
6. PDF Report Generation
7. Web Application Endpoints

## Running Tests

```bash
# Run all acceptance tests
pytest ATDD/acceptance_tests/ -v

# Run specific feature tests
pytest ATDD/acceptance_tests/test_jira_integration.py -v
```

## Test Status

All tests validate that the application meets its acceptance criteria and business requirements.
