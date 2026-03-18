# Lead Time Analyzer

Flow metrics, cycle times, and comprehensive lead time analysis with hierarchical traversal capabilities.

## Features

- **Lead Time Calculation**: Complete flow metrics from start to finish
- **Cycle Time Metrics**: Time spent in different workflow stages
- **Hierarchical Analysis**: Traverse issue hierarchies for comprehensive analysis
- **CSV Import Support**: Import issue keys from CSV files
- **Interactive Charts**: Visual representation of metrics
- **PDF Reports**: Export comprehensive analysis reports

## Port

Runs on **port 5001**

## Dependencies

This app requires additional data analysis libraries:
- pandas (data manipulation)
- numpy (numerical operations)
- scipy (statistics)
- matplotlib & seaborn (visualizations)
- reportlab (PDF generation)

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Enter your Jira connection details:
   - Jira URL
   - Access Token
   - JQL Query or CSV file

3. Configure analysis options:
   - Time period (months)
   - Hierarchical traversal (optional)
   - Include subtasks (optional)

4. Generate reports and export to PDF

## Migration Notes

Migrated from `PerseusLeadTime/lead_time_analyzer.py` to JiraAnalyzerSuite structure.
Specialized modules retained for lead time-specific analysis.
