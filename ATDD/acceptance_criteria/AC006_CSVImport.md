# AC006: CSV Import Functionality

## Feature
As a user, I want to import issue keys from CSV files so that I can analyze specific sets of issues without writing JQL.

## Acceptance Criteria

### AC006.1: CSV Parsing
**Given** CSV file with issue keys  
**When** file is uploaded  
**Then** issue keys are extracted  
**And** valid keys are identified

### AC006.2: Column Detection
**Given** CSV with various column names  
**When** file is parsed  
**Then** key columns are auto-detected  
**And** keys are extracted from correct columns

### AC006.3: Key Validation
**Given** CSV with mixed content  
**When** keys are extracted  
**Then** only valid Jira keys are accepted (PROJECT-123 format)  
**And** invalid entries are ignored

### AC006.4: Duplicate Handling
**Given** CSV with duplicate keys  
**When** keys are extracted  
**Then** duplicates are removed  
**And** unique keys are processed

### AC006.5: Subtask Inclusion
**Given** CSV with parent issue keys  
**When** "include subtasks" is enabled  
**Then** parent issues and subtasks are fetched  
**And** all related issues are analyzed

### AC006.6: Batch Processing
**Given** CSV with many issue keys  
**When** issues are fetched  
**Then** keys are processed in batches  
**And** all issues are retrieved

## Test Evidence
- test_csv_functionality.py::test_csv_parsing
- test_csv_functionality.py::test_column_detection
- test_csv_functionality.py::test_key_validation
- test_csv_functionality.py::test_batch_processing

## Status
✅ SATISFIED - All tests passing
