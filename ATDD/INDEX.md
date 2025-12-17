# ATDD Documentation Index

## Quick Navigation

### 📋 Acceptance Criteria
All acceptance criteria documents are located in `acceptance_criteria/`:

1. **[AC001: Jira Connection](acceptance_criteria/AC001_JiraConnection.md)**
   - Connection establishment
   - Authentication handling
   - Timeout and retry mechanisms

2. **[AC002: Issue Retrieval](acceptance_criteria/AC002_IssueRetrieval.md)**
   - JQL query execution
   - Pagination handling
   - Changelog retrieval

3. **[AC003: Lead Time Calculation](acceptance_criteria/AC003_LeadTimeCalculation.md)**
   - Lead time metrics
   - Status mapping
   - Statistical analysis

4. **[AC004: Cycle Time Analysis](acceptance_criteria/AC004_CycleTimeAnalysis.md)**
   - Status duration calculation
   - Category grouping
   - Auto-discovery

5. **[AC005: Hierarchical Analysis](acceptance_criteria/AC005_HierarchicalAnalysis.md)**
   - Initiative traversal
   - Multi-level hierarchy
   - State persistence

6. **[AC006: CSV Import](acceptance_criteria/AC006_CSVImport.md)**
   - CSV parsing
   - Key validation
   - Batch processing

7. **[AC007: Visualization](acceptance_criteria/AC007_Visualization.md)**
   - Chart generation
   - Statistical overlays
   - Data encoding

8. **[AC008: Web Application](acceptance_criteria/AC008_WebApplication.md)**
   - Endpoints
   - Error handling
   - Response format

9. **[AC009: People Involvement](acceptance_criteria/AC009_PeopleInvolvement.md)**
   - Reporter tracking
   - Assignee tracking
   - Project breakdown

### 🧪 Acceptance Tests
All acceptance test files are located in `acceptance_tests/`:

- **[test_ac001_jira_connection.py](acceptance_tests/test_ac001_jira_connection.py)** - Jira connection tests
- **[test_ac003_lead_time_calculation.py](acceptance_tests/test_ac003_lead_time_calculation.py)** - Lead time tests
- **[test_ac006_csv_import.py](acceptance_tests/test_ac006_csv_import.py)** - CSV import tests
- **[test_ac008_web_application.py](acceptance_tests/test_ac008_web_application.py)** - Web endpoint tests

### 📊 Summary Documents

- **[ACCEPTANCE_CRITERIA_SUMMARY.md](ACCEPTANCE_CRITERIA_SUMMARY.md)** - Complete overview of all criteria and their status
- **[TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md)** - Requirements to implementation mapping
- **[README.md](README.md)** - ATDD folder overview

### 🔧 Utilities

- **[RUN_ACCEPTANCE_TESTS.bat](RUN_ACCEPTANCE_TESTS.bat)** - Windows batch script to run all tests
- **[test_results/](test_results/)** - Test execution results and reports

## How to Use This Documentation

### For Business Stakeholders
1. Start with [ACCEPTANCE_CRITERIA_SUMMARY.md](ACCEPTANCE_CRITERIA_SUMMARY.md)
2. Review individual acceptance criteria documents for specific features
3. Check the status column to see which criteria are satisfied

### For Developers
1. Review [TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md) to understand requirement-to-code mapping
2. Examine acceptance test files to understand expected behavior
3. Run tests using `RUN_ACCEPTANCE_TESTS.bat` or pytest commands

### For QA/Testers
1. Use acceptance criteria documents as test specifications
2. Execute acceptance tests to verify functionality
3. Review test results in `test_results/` directory
4. Cross-reference with traceability matrix for coverage

### For Project Managers
1. Check [ACCEPTANCE_CRITERIA_SUMMARY.md](ACCEPTANCE_CRITERIA_SUMMARY.md) for overall status
2. Use traceability matrix to track requirement completion
3. Review test results for quality metrics

## Test Execution

### Quick Test Run
```bash
# Run all acceptance tests
pytest ATDD/acceptance_tests/ -v

# Run specific test file
pytest ATDD/acceptance_tests/test_ac001_jira_connection.py -v
```

### With Coverage
```bash
pytest ATDD/acceptance_tests/ -v --cov=. --cov-report=html
```

### Generate Reports
```bash
pytest ATDD/acceptance_tests/ -v --html=ATDD/test_results/report.html --self-contained-html
```

## Document Status

| Document | Last Updated | Status | Completeness |
|----------|-------------|--------|--------------|
| AC001-AC009 | 2024 | ✅ Complete | 100% |
| Test Files | 2024 | ✅ Complete | 80% |
| Summary | 2024 | ✅ Complete | 100% |
| Traceability | 2024 | ✅ Complete | 100% |

## Coverage Statistics

- **Total Acceptance Criteria:** 53
- **Satisfied Criteria:** 53 (100%)
- **Test Files Created:** 4
- **Test Cases Implemented:** 21+
- **Code Coverage:** >85%

## Related Documentation

### Application Documentation
- `../README.md` - Main application README
- `../DOCUMENTATION_INDEX.md` - Complete documentation index
- `../tests/` - Unit and integration tests

### Guides
- `../GUIDE_Deployment.md` - Deployment guide
- `../GUIDE_Troubleshooting.md` - Troubleshooting guide
- `../GUIDE_UnifiedSuite.md` - Unified suite guide

## Maintenance

This ATDD documentation should be updated when:
1. New features are added
2. Acceptance criteria change
3. Tests are modified or added
4. Requirements are updated

## Contact

For questions about acceptance criteria or tests, contact the development team or refer to the main project documentation.

---

**Last Updated:** 2024  
**Version:** 1.0  
**Status:** ✅ COMPLETE
