# AC004: Cycle Time Analysis

## Feature
As a user, I want to analyze time spent in each status category so that I can identify bottlenecks.

## Acceptance Criteria

### AC004.1: Status Duration Calculation
**Given** issue with multiple status transitions  
**When** cycle time is analyzed  
**Then** time in each status is calculated  
**And** durations are accurate

### AC004.2: Status Categories
**Given** various status names  
**When** cycle time is analyzed  
**Then** statuses are grouped into categories:
- In Progress (Development, Doing, etc.)
- Testing (QA, Test, etc.)
- Validation (Review, Acceptance, etc.)
- Waiting (Blocked, On Hold, etc.)

### AC004.3: Overlapping Statuses
**Given** issue returning to previous status  
**When** cycle time is analyzed  
**Then** all time periods are summed  
**And** total time in status is accurate

### AC004.4: Current Status Duration
**Given** issue currently in a status  
**When** cycle time is analyzed  
**Then** time from last transition to now is included  
**And** calculation uses current timestamp

### AC004.5: Auto Status Discovery
**Given** issues with unknown status names  
**When** analysis is performed  
**Then** new statuses are discovered  
**And** fuzzy matching maps them to categories

## Test Evidence
- test_data_analyzer.py::test_calculate_cycle_times
- test_data_analyzer.py::test_status_categories
- test_data_analyzer.py::test_overlapping_statuses
- test_data_analyzer.py::test_auto_status_discovery

## Status
✅ SATISFIED - All tests passing
