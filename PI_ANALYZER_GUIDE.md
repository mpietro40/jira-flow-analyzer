# PI Analyzer - Complete User Guide

## Overview
The PI (Program Increment) Analyzer is a comprehensive tool for analyzing Agile program increment metrics, specifically designed for ISDOP (and related) projects. It provides both basic completion metrics and advanced flow metrics analysis.

## Features

### Basic PI Analysis
- **Issue Completion Metrics**: Analyzes all issues completed during the PI period
- **Cross-Project Discovery**: Automatically discovers related projects through ISDOP Business Initiative relationships
- **Estimation Analysis**: Tracks estimated vs unestimated work
- **Professional PDF Reports**: Generates comprehensive reports with charts and recommendations

### Advanced Flow Metrics Analysis (Full Area Backlog)
When enabled, provides detailed flow metrics for each area backlog:

1. **Work in Progress (WIP)**: Items started but not finished during PI
2. **Throughput**: Number of items completed per week (calculated using statistical analysis)
3. **Work Item Age**: Average time from start to PI end for WIP items
4. **Cycle Time**: Average time from start to completion for finished items

## How to Use

### 1. Web Interface Access
- Start the application: `python pi_web_app.py`
- Open browser to: `http://localhost:5300`

### 2. Configuration
Fill in the required fields:

- **Jira Server URL**: Your organization's Jira instance (e.g., `https://company.atlassian.net`)
- **Access Token (PAT)**: Personal Access Token for authentication
- **PI Start Date**: Beginning of the Program Increment
- **PI End Date**: End of the Program Increment
- **Full Area Backlog Analysis**: Check this box to enable flow metrics analysis

### 3. Analysis Process

#### Basic Analysis (Default)
1. Discovers ISDOP Business Initiatives
2. For each initiative, finds all child issues using `childIssuesOf()` JQL function
3. Filters for issues completed during PI period
4. Analyzes by issue type and project
5. Generates completion metrics and estimation analysis

#### Full Backlog Analysis (Optional)
When checkbox is selected, additionally:
1. Fetches ALL issues from discovered projects (completed + in-progress)
2. Analyzes issue history to determine flow metrics
3. Calculates WIP, throughput, work item age, and cycle time
4. Provides per-project flow metrics dashboard

### 4. Results Interpretation

#### Summary Metrics
- **PI Duration**: Length of the program increment
- **Projects**: Number of related projects discovered
- **Completed Issues**: Total issues closed during PI
- **Total Estimates**: Sum of estimated work (in days)

#### Issue Type Analysis
For each issue type (Bug, Story, Feature, etc.):
- Count of completed issues
- Total estimated days
- Percentage of unestimated work

#### Project Analysis
For each related project:
- Number of completed issues
- Total estimated work

#### Flow Metrics (if enabled)
For each project area:
- **WIP**: Current work in progress count
- **Throughput**: Items completed per week
- **Work Item Age**: Average age of current WIP items
- **Cycle Time**: Average completion time for finished items

### 5. PDF Report Generation
Click "Download PDF Report" to generate a comprehensive report including:
- Executive summary
- Detailed metrics tables
- Flow metrics analysis (if enabled)
- Actionable recommendations
- Professional formatting with alternating row colors

## Technical Implementation

### Data Discovery Method
1. **Query**: `project = ISDOP AND issuetype = "Business Initiative"`
2. **For each initiative**: `issuekey in childIssuesOf("INITIATIVE-KEY") AND resolved >= "start" AND resolved <= "end"`
3. **Flow metrics**: Additional queries for WIP and historical data

### Flow Metrics Calculations
- **WIP**: Count of issues in "In Progress", "Doing", "Working", "Development" statuses
- **Throughput**: `completed_issues / (PI_duration_weeks)` with statistical analysis
- **Work Item Age**: `(PI_end_date - first_in_progress_date)` for WIP items
- **Cycle Time**: `(resolution_date - first_in_progress_date)` for completed items

### API Optimization
- Uses chunked queries (100-200 issues per request)
- Implements pagination for large datasets
- Includes safety limits to prevent API overload
- Eliminates duplicate API requests through caching

## Troubleshooting

### Common Issues

1. **No Business Initiatives Found**
   - Verify ISDOP project exists
   - Check if "Business Initiative" issue type is configured
   - Ensure proper permissions for the access token

2. **No Child Issues Found**
   - Verify initiatives have proper parent/child relationships
   - Check if `childIssuesOf()` JQL function is available in your Jira instance
   - Ensure child issues exist in the specified date range

3. **Flow Metrics Not Showing**
   - Ensure "Full Area Backlog Analysis" checkbox is selected
   - Verify issues have proper status transitions in their history
   - Check that in-progress statuses are correctly configured

4. **PDF Generation Fails**
   - Check server logs for detailed error messages
   - Ensure sufficient disk space for temporary files
   - Verify all required Python packages are installed

### Performance Considerations
- Large datasets may take several minutes to analyze
- Flow metrics analysis requires additional API calls
- Consider running during off-peak hours for large organizations

## Best Practices

### For Accurate Results
1. **Consistent Status Usage**: Ensure teams use standard status names
2. **Proper Estimation**: Encourage teams to estimate work items
3. **Clear Relationships**: Maintain proper parent/child relationships between initiatives and work items

### For Performance
1. **Reasonable Date Ranges**: Avoid analyzing extremely long periods
2. **Network Stability**: Ensure stable internet connection during analysis
3. **API Limits**: Be aware of your organization's Jira API rate limits

## Output Files
- **PDF Reports**: Saved with naming pattern `pi_analysis_YYYY-MM-DD_to_YYYY-MM-DD.pdf`
- **Temporary Files**: Automatically cleaned up after PDF generation

## Security Notes
- Access tokens are not stored permanently
- All API communications use HTTPS
- Temporary files are created in system temp directory and cleaned up
- No sensitive data is logged in plain text

## Support and Maintenance
- **Logs**: Check application logs for detailed debugging information
- **Updates**: Regularly update dependencies for security patches
- **Monitoring**: Monitor API usage to stay within organizational limits

---

*PI Analyzer Tool - Copyright 2025 Pietro Maffi*