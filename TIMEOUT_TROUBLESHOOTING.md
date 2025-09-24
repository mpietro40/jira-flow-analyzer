# Jira Timeout Troubleshooting Guide

## Common Timeout Issues

If you're experiencing timeout errors like:
```
⏰ Timeout on attempt 1/3 for batch at 200: HTTPSConnectionPool(...): Read timed out. (read timeout=60)
```

## Quick Solutions

### 1. **Use the Timeout Tester (Recommended)**
```bash
python timeout_tester.py
```
This will automatically test different configurations and recommend optimal settings.

### 2. **Manual Configuration**
Edit `timeout_config.json` and adjust these values:

**For Slow Servers:**
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

**For Very Slow Servers:**
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

## Configuration Parameters

| Parameter | Description | Recommended Values |
|-----------|-------------|-------------------|
| `connect_timeout` | Time to establish connection | 15-45 seconds |
| `read_timeout` | Time to wait for response | 60-300 seconds |
| `batch_size` | Issues per request | 25-200 |
| `min_batch_size` | Minimum when reducing | 5-50 |

## Automatic Recovery Features

The system now includes:

1. **Adaptive Batch Sizing**: Automatically reduces batch size when timeouts occur
2. **Exponential Backoff**: Increases wait time between retries
3. **Progressive Timeout**: Longer timeouts on retry attempts
4. **Batch Skipping**: Skips problematic batches to continue processing

## Performance Profiles

Use predefined profiles in `timeout_config.json`:

- **fast_server**: For responsive Jira instances
- **slow_server**: For slower corporate Jira servers  
- **very_slow_server**: For heavily loaded servers

## Monitoring Progress

Watch for these log messages:
- `🔄 Fetching batch starting at X (size: Y, attempt Z/3)` - Normal progress
- `🔧 Reducing batch size from X to Y due to timeouts` - Automatic adjustment
- `📈 Increasing batch size to X` - Recovery after successful batches
- `⏭️ Skipping batch at X due to persistent timeouts` - Batch skip (rare)

## Best Practices

1. **Start with timeout tester**: Run `python timeout_tester.py` first
2. **Monitor during peak hours**: Test during your organization's busy periods
3. **Adjust gradually**: Make small incremental changes to settings
4. **Check server status**: Verify Jira server health if all profiles fail

## Still Having Issues?

If timeouts persist:

1. Check your network connection
2. Verify Jira server status with your admin
3. Try running during off-peak hours
4. Consider using smaller date ranges for analysis
5. Contact your Jira administrator about server performance

## Emergency Settings

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