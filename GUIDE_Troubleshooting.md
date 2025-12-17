# Jira Analytics Suite - Troubleshooting Guide

## Jira Timeout Issues

### Common Timeout Errors
```
⏰ Timeout on attempt 1/3 for batch at 200: HTTPSConnectionPool(...): Read timed out. (read timeout=60)
```

### Quick Solutions

#### 1. Use the Timeout Tester (Recommended)
```bash
python timeout_tester.py
```
This will automatically test different configurations and recommend optimal settings.

#### 2. Manual Configuration
Edit `timeout_config.json` and adjust these values:

**For Slow Servers**:
```json
{
  "timeout_settings": {
    "connect_timeout": 30,
    "read_timeout": 180,
    "batch_size": 50,
    "min_batch_size": 10
  }
}
```

**For Very Slow Servers**:
```json
{
  "timeout_settings": {
    "connect_timeout": 45,
    "read_timeout": 300,
    "batch_size": 25,
    "min_batch_size": 5
  }
}
```

### Configuration Parameters

| Parameter | Description | Recommended Values |
|-----------|-------------|-------------------|
| `connect_timeout` | Time to establish connection | 15-45 seconds |
| `read_timeout` | Time to wait for response | 60-300 seconds |
| `batch_size` | Issues per request | 25-200 |
| `min_batch_size` | Minimum when reducing | 5-50 |

### Automatic Recovery Features

The system includes:
1. **Adaptive Batch Sizing**: Automatically reduces batch size when timeouts occur
2. **Exponential Backoff**: Increases wait time between retries
3. **Progressive Timeout**: Longer timeouts on retry attempts
4. **Batch Skipping**: Skips problematic batches to continue processing

### Performance Profiles

Use predefined profiles in `timeout_config.json`:
- **fast_server**: For responsive Jira instances
- **slow_server**: For slower corporate Jira servers  
- **very_slow_server**: For heavily loaded servers

### Monitoring Progress

Watch for these log messages:
- `🔄 Fetching batch starting at X (size: Y, attempt Z/3)` - Normal progress
- `🔧 Reducing batch size from X to Y due to timeouts` - Automatic adjustment
- `📈 Increasing batch size to X` - Recovery after successful batches
- `⏭️ Skipping batch at X due to persistent timeouts` - Batch skip (rare)

### Emergency Settings

If nothing works, try these minimal settings:
```json
{
  "timeout_settings": {
    "connect_timeout": 60,
    "read_timeout": 600,
    "batch_size": 10,
    "min_batch_size": 1
  }
}
```

### Best Practices

1. **Start with timeout tester**: Run `python timeout_tester.py` first
2. **Monitor during peak hours**: Test during your organization's busy periods
3. **Adjust gradually**: Make small incremental changes to settings
4. **Check server status**: Verify Jira server health if all profiles fail

### Still Having Issues?

If timeouts persist:
1. Check your network connection
2. Verify Jira server status with your admin
3. Try running during off-peak hours
4. Consider using smaller date ranges for analysis
5. Contact your Jira administrator about server performance

---

## Application-Specific Issues

### Epic Fix Version Analyzer

#### "No initiatives found"
- Verify JQL query syntax
- Check permissions to view initiatives
- Confirm initiatives exist matching query

#### "No epics found"
- Verify fix version spelling (case-sensitive)
- Check epics have fix version assigned
- Verify hierarchy: Initiative → Feature → Sub-Feature → Epic

#### PDF Generation Issues
- Check browser download settings
- Ensure pop-ups not blocked
- Verify analysis completed successfully
- Check logs: `epic_fixversion.log`

### PI Analyzer

#### No Business Initiatives Found
- Verify ISDOP project exists
- Check "Business Initiative" issue type configured
- Ensure proper permissions for access token

#### No Child Issues Found
- Verify initiatives have parent/child relationships
- Check `childIssuesOf()` JQL function available
- Ensure child issues exist in specified date range

#### Flow Metrics Not Showing
- Ensure "Full Area Backlog Analysis" checkbox selected
- Verify issues have status transitions in history
- Check in-progress statuses correctly configured

#### No Saved Results Found
- Check if `pi_results/` directory exists
- Verify file permissions
- Check server logs for save errors

#### Files Not Appearing
- Wait for analysis to complete (check logs)
- Refresh the results list
- Check disk space availability

#### Corrupted Files
- Delete the corrupted file
- Re-run the analysis
- Check server logs for errors during save

### Sprint Analyzer

#### Connection Failed
```
🚩 Failed to connect to Jira
```
- Verify Jira URL format (include https://)
- Check API token validity
- Ensure network connectivity

#### No Sprint Data
```
🚩 No issues found for sprint: Sprint Name
```
- Verify sprint name/ID is correct
- Check user permissions for sprint access
- Ensure sprint exists and contains issues

#### Missing Time Data
```
⚠️ Could not fetch time data for ISSUE-123
```
- Verify time tracking is enabled
- Check user permissions for time tracking fields
- Some issues may not have time estimates (normal)

---

## Docker Issues

### Port Conflicts
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Container Won't Start
```bash
# Check logs
docker-compose logs -f

# Rebuild
docker-compose down
docker-compose up --build -d
```

### Permission Issues
```bash
# Linux/Mac - Fix permissions
sudo chown -R $USER:$USER .
```

---

## General Troubleshooting Steps

### 1. Check Logs
Most applications create log files:
- `epic_fixversion.log`
- `pi_analyzer.log`
- `sprint_analyzer.log`
- Console output

### 2. Verify Jira Connection
Test with simple query in Jira's issue search to ensure:
- JQL syntax is correct
- You have permissions
- Issues exist

### 3. Check Environment
- Python version: 3.7+
- All dependencies installed: `pip install -r requirements.txt`
- Sufficient disk space
- Network connectivity

### 4. Test with Minimal Data
- Use small date ranges
- Test with single project
- Limit number of issues

### 5. Enable Debug Mode
```python
# In application file, change:
logging.basicConfig(level=logging.DEBUG)
```

---

## Getting Help

When reporting issues, include:
1. Error message from UI
2. Relevant log entries
3. JQL query used (if applicable)
4. Jira version
5. Application version
6. Steps to reproduce

---

**Last Updated**: 2025  
**Status**: ✅ Comprehensive troubleshooting guide
