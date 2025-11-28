# Custom Fields Guide - Epic Fix Version Analyzer

## What are Custom Fields?

Custom fields in Jira are additional fields that organizations add to track specific information beyond the standard Jira fields. Each custom field has a unique ID like `customfield_10037`.

## Current Field Mapping

The Epic Fix Version analyzer currently extracts these custom fields:

| Display Name | Field ID | Purpose |
|--------------|----------|---------|
| **Magnitude/Complexity** | `customfield_10037` | Epic size or complexity rating |
| **Requesting Customer** | `customfield_10095` | Who requested this epic |
| **CPO-APO Leading** | `assignee` | Person leading the epic (standard field) |
| **Starting Date** | `customfield_10096` | Target start date |
| **What to Deliver** | `customfield_10097` | Solution description |

## ⚠️ Important Note

**These field IDs are specific to the original Jira instance where this tool was developed.**

Your Jira instance will have **different custom field IDs**. You need to discover your own field IDs.

## How to Find Your Custom Field IDs

### Method 1: Use the Discovery Tool (Recommended)

Run the custom field discovery tool:

```bash
python discover_custom_fields.py
```

This will:
1. Connect to your Jira instance
2. List all custom fields with their IDs
3. Suggest which fields to use
4. Generate a mapping template
5. Save results to `custom_fields_mapping.json`

### Method 2: Manual Discovery via Jira API

1. **Get an issue with custom fields:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        "https://your-jira.com/rest/api/2/issue/EPIC-123"
   ```

2. **Look in the `fields` section** for entries like:
   ```json
   "customfield_10037": "Large",
   "customfield_10095": "Customer ABC",
   "customfield_10096": "2025-01-15"
   ```

3. **Match the values to your field names**

### Method 3: Jira Admin UI

1. Go to **Jira Settings** → **Issues** → **Custom Fields**
2. Click on a custom field
3. Look at the URL: `...customfield_10037`
4. The number in the URL is your field ID

## How to Update the Application

Once you've discovered your field IDs, update `epic_fixversion_app.py`:

### Find this section (around line 140):

```python
epic_data = {
    'key': epic['key'],
    'summary': epic.get('summary', 'No summary'),
    'status': epic.get('status', 'Unknown'),
    'project': self._extract_project_key(epic),
    'fix_versions': fix_versions,
    'complexity': self._extract_custom_field(fields, 'customfield_10037'),
    'requesting_customer': self._extract_custom_field(fields, 'customfield_10095'),
    'assignee': epic.get('assignee', 'Unassigned'),
    'target_start': self._extract_custom_field(fields, 'customfield_10096'),
    'solution': self._extract_custom_field(fields, 'customfield_10097'),
    'comments': self._extract_comments(fields)
}
```

### Replace with your field IDs:

```python
epic_data = {
    'key': epic['key'],
    'summary': epic.get('summary', 'No summary'),
    'status': epic.get('status', 'Unknown'),
    'project': self._extract_project_key(epic),
    'fix_versions': fix_versions,
    'complexity': self._extract_custom_field(fields, 'customfield_XXXXX'),  # Your complexity field
    'requesting_customer': self._extract_custom_field(fields, 'customfield_YYYYY'),  # Your customer field
    'assignee': epic.get('assignee', 'Unassigned'),
    'target_start': self._extract_custom_field(fields, 'customfield_ZZZZZ'),  # Your start date field
    'solution': self._extract_custom_field(fields, 'customfield_WWWWW'),  # Your solution field
    'comments': self._extract_comments(fields)
}
```

## Field Mapping Template

Use this template to document your field mappings:

```python
# My Jira Custom Field Mappings
CUSTOM_FIELDS = {
    'complexity': 'customfield_XXXXX',      # Field name: "Epic Complexity"
    'requesting_customer': 'customfield_YYYYY',  # Field name: "Requesting Customer"
    'target_start': 'customfield_ZZZZZ',    # Field name: "Target Start Date"
    'solution': 'customfield_WWWWW',        # Field name: "Solution Description"
}
```

## If You Don't Have These Fields

If your Jira doesn't have these custom fields, you can:

1. **Remove them** - Set to empty string:
   ```python
   'complexity': '',
   'requesting_customer': '',
   ```

2. **Use different fields** - Map to fields you do have:
   ```python
   'complexity': self._extract_custom_field(fields, 'customfield_YOUR_FIELD'),
   ```

3. **Keep as-is** - The app will show "N/A" for missing fields

## Quick Start

1. Run discovery tool:
   ```bash
   python discover_custom_fields.py
   ```

2. Review `custom_fields_mapping.json`

3. Update `epic_fixversion_app.py` with your field IDs

4. Test with a small query

5. Verify the data appears correctly in the results

## Need Help?

If you're unsure which fields to use, run the discovery tool and look for fields with names like:
- Complexity, Magnitude, Size
- Customer, Requester, Stakeholder
- Start Date, Target Date, Planned Date
- Solution, Deliverable, Description