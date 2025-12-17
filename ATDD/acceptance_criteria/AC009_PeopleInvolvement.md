# AC009: People Involvement Tracking

## Feature
As a user, I want to track people involvement across projects so that I can understand team engagement.

## Acceptance Criteria

### AC009.1: Reporter Tracking
**Given** issues with reporters  
**When** analysis is performed  
**Then** unique reporters are counted  
**And** count is accurate per project

### AC009.2: Assignee Tracking
**Given** issues with assignees  
**When** analysis is performed  
**Then** unique assignees are counted  
**And** unassigned issues are excluded

### AC009.3: Commenter Tracking
**Given** issues with comments  
**When** analysis is performed  
**Then** unique commenters are counted  
**And** all comment authors are included

### AC009.4: Overall Statistics
**Given** multiple projects analyzed  
**When** people involvement is calculated  
**Then** overall totals are provided  
**And** unique people across all projects are counted

### AC009.5: Per-Project Breakdown
**Given** issues from multiple projects  
**When** people involvement is calculated  
**Then** statistics per project are provided  
**And** each project shows its unique contributors

### AC009.6: Duplicate Prevention
**Given** person involved in multiple roles  
**When** total people count is calculated  
**Then** person is counted once  
**And** role-specific counts are separate

## Test Evidence
- test_data_analyzer.py::test_people_involvement_tracking
- test_data_analyzer.py::test_people_per_project
- test_data_analyzer.py::test_duplicate_prevention

## Status
✅ SATISFIED - All tests passing
