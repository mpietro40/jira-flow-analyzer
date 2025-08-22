# Sprint Analyzer 📊

A comprehensive sprint analysis tool that leverages historical Jira data to forecast sprint feasibility and provide actionable insights for agile teams.

## Features ✨

- **📈 Sprint Workload Analysis**: Analyzes estimated, remaining, and spent hours across all sprint issues
- **🔮 Feasibility Forecasting**: Predicts sprint completion probability based on historical velocity
- **📊 Status Breakdown**: Detailed analysis by issue status with time tracking
- **💡 Smart Recommendations**: Actionable insights based on data analysis
- **🎯 Risk Assessment**: Automatic risk level calculation (LOW/MEDIUM/HIGH)
- **📋 Comprehensive Reporting**: Detailed console reports with emoji indicators

## Architecture 🏗️

The Sprint Analyzer reuses existing components from the PerseusLeadTime framework:

```
sprint_analyzer.py
├── JiraClient (reused) - API connectivity and data fetching
├── DataAnalyzer (reused) - Core analytics capabilities  
└── SprintAnalyzer (new) - Sprint-specific analysis and forecasting
```

## Installation 🚀

### Prerequisites
- Python 3.7+
- Jira API access token
- Access to Jira instance with time tracking enabled

### Dependencies
All dependencies are already included in the PerseusLeadTime project:
```bash
pip install requests pandas numpy scipy python-dateutil
```

## Usage 💻

### Command Line Interface

```bash
python sprint_analyzer.py --jira-url https://your-company.atlassian.net --token YOUR_API_TOKEN --sprint "Sprint 2024-01"
```

#### Parameters:
- `--jira-url`: Your Jira server URL (required)
- `--token`: Jira API access token (required)  
- `--sprint`: Sprint name or ID (required)
- `--history-months`: Months of historical data for forecasting (default: 6)

### Example Usage

```bash
# Analyze current sprint with 6 months of historical data
python sprint_analyzer.py \
  --jira-url https://mycompany.atlassian.net \
  --token abcd1234efgh5678 \
  --sprint "Development Sprint 15"

# Analyze sprint with 3 months of historical data
python sprint_analyzer.py \
  --jira-url https://mycompany.atlassian.net \
  --token abcd1234efgh5678 \
  --sprint "Sprint 2024-Q1-03" \
  --history-months 3
```

## Sample Output 📋

```
============================================================
📊 SPRINT ANALYSIS REPORT: Development Sprint 15
============================================================

📈 SUMMARY:
  • Total Issues: 12
  • Estimated Hours: 96.0h
  • Remaining Hours: 64.0h
  • Progress: 33.3%
  • Risk Level: MEDIUM

🔮 FORECAST:
  • Completion Probability: 78%
  • Estimated Weeks Needed: 1.8

📋 STATUS BREAKDOWN:
  • To Do: 5 issues, 40.0h remaining
  • In Progress: 4 issues, 20.0h remaining
  • In Review: 2 issues, 4.0h remaining
  • Done: 1 issues, 0.0h remaining

💡 RECOMMENDATIONS:
  📝 2 issues lack time estimates - prioritize estimation
  📊 Historical estimates tend to be optimistic - add buffer time
  ✅ Monitor progress closely in first few days
============================================================
```

## Key Metrics Explained 📊

### Workload Analysis
- **Total Issues**: Count of all issues in the sprint
- **Estimated Hours**: Sum of original time estimates
- **Remaining Hours**: Sum of remaining time estimates
- **Time Spent**: Actual hours logged against issues
- **Progress**: Percentage completion based on time spent vs estimated

### Forecasting
- **Completion Probability**: Based on historical completion rates and current velocity
- **Estimated Weeks Needed**: Remaining work divided by historical velocity
- **Risk Level**: Automatic assessment based on workload and historical data
  - **LOW**: < 1 week remaining at current velocity
  - **MEDIUM**: 1-2 weeks remaining
  - **HIGH**: > 2 weeks remaining

### Historical Context
- **Average Velocity**: Hours completed per week based on historical data
- **Estimate Accuracy**: Ratio of actual vs estimated time from completed work
- **Completion Rate**: Percentage of issues completed in historical sprints

## Testing 🧪

Run the comprehensive test suite:

```bash
python test_sprint_analyzer.py
```

### Test Coverage
- ✅ Workload analysis calculations
- ✅ Historical velocity computation
- ✅ Forecast generation logic
- ✅ Recommendation algorithms
- ✅ Error handling and edge cases
- ✅ Report formatting
- ✅ API integration mocking

## Configuration ⚙️

### Jira Setup Requirements

1. **Time Tracking Enabled**: Ensure time tracking is enabled in your Jira project
2. **API Token**: Generate a personal access token in Jira
3. **Permissions**: User must have read access to:
   - Sprint data
   - Issue time tracking fields
   - Historical issue data

### Sprint Identification

The tool accepts sprint names or IDs in various formats:
- Sprint name: `"Development Sprint 15"`
- Sprint ID: `123`
- Partial matches: `"Sprint 15"`

## Logging 📝

The application uses the same emoji-enhanced logging style as the parent framework:

- 🚀 **Startup/Initialization**
- 🔍 **Data Fetching**
- 📊 **Analysis Operations**
- ✅ **Success Operations**
- ⚠️ **Warnings**
- 🚩 **Errors**
- 🔮 **Forecasting**
- 💡 **Recommendations**

## Integration with Existing Framework 🔗

The Sprint Analyzer seamlessly integrates with the PerseusLeadTime framework:

### Reused Components
- **JiraClient**: All API connectivity and authentication
- **DataAnalyzer**: Core analytics and data processing capabilities
- **Logging Configuration**: Consistent emoji-enhanced logging

### Extended Functionality
- **Time Tracking Analysis**: Enhanced issue processing for time estimates
- **Sprint-Specific Queries**: Specialized JQL for sprint data
- **Velocity Calculations**: Historical performance analysis
- **Feasibility Forecasting**: Predictive analytics for sprint planning

## Troubleshooting 🔧

### Common Issues

1. **Connection Failed**
   ```
   🚩 Failed to connect to Jira
   ```
   - Verify Jira URL format (include https://)
   - Check API token validity
   - Ensure network connectivity

2. **No Sprint Data**
   ```
   🚩 No issues found for sprint: Sprint Name
   ```
   - Verify sprint name/ID is correct
   - Check user permissions for sprint access
   - Ensure sprint exists and contains issues

3. **Missing Time Data**
   ```
   ⚠️ Could not fetch time data for ISSUE-123
   ```
   - Verify time tracking is enabled
   - Check user permissions for time tracking fields
   - Some issues may not have time estimates (normal)

### Debug Mode

For detailed debugging, modify the logging level:
```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

## Contributing 🤝

When extending the Sprint Analyzer:

1. **Follow Existing Patterns**: Use the same logging style and class structure
2. **Reuse Components**: Leverage existing JiraClient and DataAnalyzer classes
3. **Add Tests**: Include comprehensive test coverage for new features
4. **Document Changes**: Update this README with new functionality

## License 📄

This tool is part of the PerseusLeadTime analytics framework and follows the same licensing terms.

---

**Built with ❤️ for agile teams who want data-driven sprint planning**