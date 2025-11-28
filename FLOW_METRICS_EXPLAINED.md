# Flow Metrics Calculation - PI Analyzer

## Overview
The PI Analyzer calculates 4 key flow metrics to measure team health and delivery predictability during a Program Increment (PI).

## The 4 Flow Metrics

### 1. Work in Progress (WIP)
**What it measures:** Number of items currently being worked on

**Calculation:**
```
WIP = Count of issues with status IN (In Progress, Doing, Working, Development)
```

**How it's calculated in code:**
- Query Jira for all issues in "in-progress" statuses at PI end date
- Count the total number of issues
- `wip_count = len(wip_issues)`

**Why it matters:** High WIP indicates context switching and reduced focus. Lower WIP = faster delivery.

---

### 2. Throughput
**What it measures:** Average number of items completed per week

**Calculation:**
```
Throughput = Total Completed Issues / Number of Weeks in PI
```

**How it's calculated in code:**
```python
pi_weeks = (pi_end_date - pi_start_date).days / 7
throughput = len(completed_issues) / pi_weeks
```

**Example:** 40 issues completed in 10 weeks = 4 items/week throughput

**Why it matters:** Measures team velocity and delivery capacity. Used for forecasting future work.

---

### 3. Work Item Age
**What it measures:** Average time WIP items have been in progress (in days)

**Calculation:**
```
For each WIP item:
  Age = Current Date - Date Item Started Progress
  
Average Age = Sum of all Ages / Number of WIP Items
```

**How it's calculated in code:**
```python
for issue in wip_issues:
    start_date = issue['in_progress_date']
    age_days = (pi_end_date - start_date).days
    ages.append(age_days)

avg_age = mean(ages)
```

**Why it matters:** High age indicates blocked or stalled work. Helps identify items needing attention.

---

### 4. Cycle Time
**What it measures:** Average time to complete an item from start to finish (in days)

**Calculation:**
```
For each completed item:
  Cycle Time = Resolution Date - In Progress Start Date
  
Average Cycle Time = Sum of all Cycle Times / Number of Completed Items
```

**How it's calculated in code:**
```python
for issue in completed_issues:
    start_date = issue['in_progress_date']
    end_date = issue['resolved_date']
    cycle_days = (end_date - start_date).days
    cycle_times.append(cycle_days)

avg_cycle_time = mean(cycle_times)
```

**Why it matters:** Predicts how long new work will take. Lower cycle time = faster delivery and better predictability.

---

## Data Sources

### Issues Analyzed:
- **Completed Issues:** Resolved during PI period with status in (Done, Closed, Resolved)
- **WIP Issues:** Current status in (In Progress, Doing, Working, Development)

### Key Dates Extracted:
1. **Created Date:** When issue was created
2. **In Progress Date:** First time issue moved to in-progress status (from changelog)
3. **Resolved Date:** When issue was completed

### Changelog Analysis:
The analyzer examines Jira changelog to find when each issue first entered an "in-progress" state:
```python
for history in changelog:
    if status changed to "In Progress":
        in_progress_date = history.created
        break
```

---

## Thresholds & Recommendations

### WIP Limits:
- ✅ **Healthy:** < 10 items
- ⚠️ **Warning:** 10-15 items
- 🚨 **Critical:** > 15 items

### Cycle Time:
- ✅ **Healthy:** < 21 days
- ⚠️ **Warning:** 21-30 days
- 🚨 **Critical:** > 30 days

### Work Item Age:
- ✅ **Healthy:** < 14 days
- ⚠️ **Warning:** 14-21 days
- 🚨 **Critical:** > 21 days

---

## Example Output

```json
{
  "work_in_progress": 12,
  "throughput_per_week": 4.2,
  "avg_work_item_age_days": 8.5,
  "avg_cycle_time_days": 18.3,
  "total_completed": 42,
  "coaching_recommendations": [
    {
      "metric": "Work in Progress",
      "severity": "Warning",
      "current_value": 12,
      "threshold": 10,
      "advice": "Consider implementing WIP limits to improve flow"
    }
  ]
}
```

---

## Summary

| Metric | Measures | Formula | Good Value |
|--------|----------|---------|------------|
| **WIP** | Items in progress | Count of active items | < 10 |
| **Throughput** | Delivery rate | Completed / Weeks | Stable trend |
| **Work Item Age** | Time in progress | Now - Start Date | < 14 days |
| **Cycle Time** | Time to complete | End - Start Date | < 21 days |

These metrics provide actionable insights for improving team flow and delivery predictability.