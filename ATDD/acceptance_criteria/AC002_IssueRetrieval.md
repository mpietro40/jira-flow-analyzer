# AC002: Issue Retrieval via JQL

## Feature
As a user, I want to retrieve Jira issues using JQL queries so that I can analyze specific sets of issues.

## Acceptance Criteria

### AC002.1: Basic JQL Query
**Given** valid JQL query  
**When** issues are fetched  
**Then** all matching issues are retrieved  
**And** issue data includes key, summary, status, dates

### AC002.2: Pagination Handling
**Given** JQL query returning more than 200 issues  
**When** issues are fetched  
**Then** pagination is handled automatically  
**And** all issues are retrieved in batches

### AC002.3: Changelog Retrieval
**Given** issues with status transitions  
**When** issues are fetched  
**Then** complete changelog is included  
**And** status history is captured

### AC002.4: Custom Fields
**Given** issues with custom fields  
**When** issues are fetched  
**Then** custom fields are retrieved  
**And** field data is accessible

### AC002.5: Empty Result Set
**Given** JQL query with no matches  
**When** issues are fetched  
**Then** empty list is returned  
**And** no error is raised

### AC002.6: Batch Size Adaptation
**Given** timeout during large query  
**When** retry is attempted  
**Then** batch size is reduced  
**And** query continues with smaller batches

## Test Evidence
- test_jira_integration.py::test_fetch_issues_basic
- test_jira_integration.py::test_fetch_issues_pagination
- test_jira_integration.py::test_fetch_issues_with_changelog
- test_jira_integration.py::test_batch_size_adaptation

## Status
✅ SATISFIED - All tests passing
