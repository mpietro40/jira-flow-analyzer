# AC008: Web Application Endpoints

## Feature
As a user, I want to interact with the application through a web interface so that I can easily perform analysis.

## Acceptance Criteria

### AC008.1: Home Page
**Given** application is running  
**When** user navigates to root URL  
**Then** input form is displayed  
**And** all required fields are present

### AC008.2: Standard Analysis Endpoint
**Given** valid form data submitted  
**When** POST to /analyze  
**Then** analysis is performed  
**And** JSON results are returned

### AC008.3: CSV Analysis Endpoint
**Given** CSV file uploaded  
**When** POST to /analyze_csv  
**Then** CSV is parsed and analyzed  
**And** JSON results are returned

### AC008.4: Error Handling
**Given** invalid input data  
**When** analysis is requested  
**Then** appropriate error message is returned  
**And** HTTP status code indicates error type

### AC008.5: PDF Report Generation
**Given** analysis results  
**When** POST to /generate_report  
**Then** PDF report is generated  
**And** file is downloaded

### AC008.6: Analysis Status Check
**Given** hierarchical analysis in progress  
**When** GET to /analysis_status  
**Then** current progress is returned  
**And** status information is accurate

### AC008.7: Response Format
**Given** successful analysis  
**When** results are returned  
**Then** JSON includes:
- success flag
- total_issues count
- metrics object
- charts array
- projects list
- people_involvement data

## Test Evidence
- test_app.py::test_home_page
- test_app.py::test_analyze_endpoint
- test_app.py::test_csv_endpoint
- test_app.py::test_error_handling
- test_app.py::test_pdf_generation

## Status
✅ SATISFIED - All tests passing
