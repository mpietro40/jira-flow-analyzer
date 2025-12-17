# AC003: Lead Time Calculation

## Feature
As a user, I want to calculate lead times from "In Progress" to "Done" so that I can measure delivery performance.

## Acceptance Criteria

### AC003.1: Basic Lead Time
**Given** issue with "In Progress" and "Done" transitions  
**When** lead time is calculated  
**Then** time difference in days is returned  
**And** calculation is accurate

### AC003.2: Multiple Status Transitions
**Given** issue with multiple status changes  
**When** lead time is calculated  
**Then** first "In Progress" date is used  
**And** last "Done" date is used

### AC003.3: Incomplete Issues
**Given** issue still in progress (not done)  
**When** lead time is calculated  
**Then** issue is excluded from lead time metrics  
**And** no error is raised

### AC003.4: Status Mapping
**Given** custom status names (e.g., "Development", "Completed")  
**When** lead time is calculated  
**Then** statuses are mapped to standard categories  
**And** calculation uses mapped statuses

### AC003.5: Timezone Handling
**Given** issues with different timezone timestamps  
**When** lead time is calculated  
**Then** timezone differences are handled correctly  
**And** calculations are consistent

### AC003.6: Statistical Metrics
**Given** multiple issues with lead times  
**When** metrics are calculated  
**Then** average, median, P85, P95 are provided  
**And** all metrics are accurate

## Test Evidence
- test_data_analyzer.py::test_calculate_lead_times
- test_data_analyzer.py::test_lead_time_with_custom_statuses
- test_data_analyzer.py::test_lead_time_timezone_handling
- test_data_analyzer.py::test_statistical_metrics

## Status
✅ SATISFIED - All tests passing
