"""
Custom Field Discovery Tool
Helps you find the correct custom field IDs in your Jira instance

Usage:
    python discover_custom_fields.py
"""

import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime

def discover_custom_fields(jira_url, access_token, epic_id=None):
    """
    Discover all custom fields in your Jira instance
    
    Args:
        jira_url: Your Jira URL (e.g., https://your-company.atlassian.net)
        access_token: Your Jira API token
        epic_id: Optional Issue ID to fetch actual field values
    """
    if epic_id:
        print(f"🔍 Discovering custom fields from Issue {epic_id}...\n")
    else:
        print("🔍 Discovering custom fields in your Jira instance...\n")
    
    # Get all fields
    url = f"{jira_url}/rest/api/2/field"
    
    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return
        
        fields = response.json()
        
        # Filter custom fields only
        custom_fields = [f for f in fields if f['id'].startswith('customfield_')]
        
        print(f"✅ Found {len(custom_fields)} custom fields\n")
        print("="*80)
        
        # Group by common names
        relevant_keywords = ['complexity', 'magnitude', 'customer', 'requesting', 
                           'focal', 'start', 'target', 'solution', 'deliver']
        
        print("\n📋 POTENTIALLY RELEVANT CUSTOM FIELDS:\n")
        for field in custom_fields:
            field_name = field['name'].lower()
            if any(keyword in field_name for keyword in relevant_keywords):
                print(f"  🔹 {field['name']}")
                print(f"     ID: {field['id']}")
                print(f"     Type: {field['schema'].get('type', 'unknown')}")
                print()
        
        print("\n📋 ALL CUSTOM FIELDS:\n")
        for field in custom_fields:
            print(f"  • {field['name']}")
            print(f"    ID: {field['id']}")
            print(f"    Type: {field['schema'].get('type', 'unknown')}")
            print()
        
        # Save to file
        output_file = 'data\custom_fields_mapping.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(custom_fields, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Full field list saved to: {output_file}")
        
        # If Issue ID specified, get actual values from that Issue
        if epic_id:
            print(f"\n🔎 Fetching Issue {epic_id}...\n")
            epic_url = f"{jira_url}/rest/api/2/issue/{epic_id}"
            
            try:
                epic_response = requests.get(
                    epic_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    params={'fields': '*all'}
                )
                
                if epic_response.status_code == 200:
                    issue = epic_response.json()
                    issue_key = issue['key']
                    fields_data = issue.get('fields', {})
                    
                    print(f"✅ Found Issue: {issue_key}\n")
                    print("="*80)
                    print(f"\n📊 CUSTOM FIELDS WITH ACTUAL VALUES (from {issue_key}):\n")
                    
                    # Prepare data for text file
                    text_output = []
                    text_output.append("="*80)
                    text_output.append(f"CUSTOM FIELDS DISCOVERED FROM ISSUE: {issue_key}")
                    text_output.append(f"Jira URL: {jira_url}")
                    text_output.append(f"Discovery Date: {json.dumps(datetime.now().isoformat())}")
                    text_output.append("="*80)
                    text_output.append("")
                    
                    fields_with_values = []
                    fields_without_values = []
                    
                    # Separate fields with and without values
                    for field in custom_fields:
                        field_id = field['id']
                        field_value = fields_data.get(field_id)
                        
                        has_value = False
                        display_value = None
                        
                        if field_value is not None and field_value != '':
                            # Format value based on type
                            if isinstance(field_value, dict):
                                display_value = field_value.get('value', field_value.get('name', str(field_value)))
                                has_value = bool(display_value)
                            elif isinstance(field_value, list):
                                if field_value:
                                    display_value = ', '.join([str(v.get('name', v) if isinstance(v, dict) else v) for v in field_value])
                                    has_value = True
                            else:
                                display_value = str(field_value)
                                has_value = True
                        
                        field_info = {
                            'name': field['name'],
                            'id': field_id,
                            'type': field['schema'].get('type', 'unknown')
                        }
                        
                        if has_value and display_value:
                            field_info['value'] = display_value
                            fields_with_values.append(field_info)
                        else:
                            fields_without_values.append(field_info)
                    
                    # Console output - Fields WITH values
                    for field_info in fields_with_values:
                        print(f"  🔹 {field_info['name']}")
                        print(f"     ID: {field_info['id']}")
                        print(f"     Value: {field_info['value'][:100]}{'...' if len(field_info['value']) > 100 else ''}")
                        print(f"     Type: {field_info['type']}")
                        print()
                        
                        # Text file output
                        text_output.append(f"Field Name: {field_info['name']}")
                        text_output.append(f"Field ID: {field_info['id']}")
                        text_output.append(f"Field Type: {field_info['type']}")
                        text_output.append(f"Current Value: {field_info['value']}")
                        text_output.append("-" * 80)
                        text_output.append("")
                    
                    # Add separator
                    print("\n" + "="*80)
                    print(f"\n⚪ CUSTOM FIELDS WITHOUT VALUES (from {issue_key}):\n")
                    
                    text_output.append("")
                    text_output.append("="*80)
                    text_output.append("CUSTOM FIELDS WITHOUT VALUES")
                    text_output.append("="*80)
                    text_output.append("")
                    
                    # Console output - Fields WITHOUT values
                    for field_info in fields_without_values:
                        print(f"  ⚪ {field_info['name']}")
                        print(f"     ID: {field_info['id']}")
                        print(f"     Type: {field_info['type']}")
                        print()
                        
                        # Text file output
                        text_output.append(f"Field Name: {field_info['name']}")
                        text_output.append(f"Field ID: {field_info['id']}")
                        text_output.append(f"Field Type: {field_info['type']}")
                        text_output.append(f"Current Value: (empty)")
                        text_output.append("-" * 80)
                        text_output.append("")
                    
                    # Add summary statistics at the end
                    text_output.append("")
                    text_output.append("="*80)
                    text_output.append("SUMMARY")
                    text_output.append("="*80)
                    text_output.append("")
                    text_output.append(f"Custom fields with values: {len(fields_with_values)}")
                    text_output.append(f"Custom fields without values: {len(fields_without_values)}")
                    text_output.append(f"Total custom fields: {len(custom_fields)}")
                    text_output.append("")
                    text_output.append("="*80)
                    
                    # Save to text file
                    text_filename = f'custom_fields_{epic_id.replace("-", "_")}.txt'
                    with open(text_filename, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(text_output))
                    
                    print(f"\n💾 All custom fields saved to: {text_filename}")
                    print(f"   Fields with values: {len(fields_with_values)}")
                    print(f"   Fields without values: {len(fields_without_values)}")
                    print(f"   Total custom fields: {len(custom_fields)}")
                    
                    # Also save as JSON for programmatic use
                    json_filename = f'custom_fields_{epic_id.replace("-", "_")}.json'
                    with open(json_filename, 'w', encoding='utf-8') as f:
                        json.dump({
                            'epic_key': issue_key,
                            'jira_url': jira_url,
                            'discovery_date': datetime.now().isoformat(),
                            'fields_with_values': fields_with_values,
                            'fields_without_values': fields_without_values,
                            'total_fields': len(custom_fields)
                        }, f, indent=2, ensure_ascii=False)
                    
                    print(f"💾 JSON format saved to: {json_filename}")
                    
                else:
                    print(f"❌ Could not fetch Issue {epic_id}: {epic_response.status_code}")
                    print(epic_response.text)
            except Exception as e:
                print(f"❌ Error fetching Epic: {str(e)}")
        
        # Generate mapping template
        print("\n" + "="*80)
        print("\n📝 SUGGESTED FIELD MAPPING FOR epic_fixversion_app.py:\n")
        print("Replace these lines in the _get_initiative_epics_via_hierarchy method:\n")
        
        for field in custom_fields:
            field_name = field['name'].lower()
            if 'complexity' in field_name or 'magnitude' in field_name:
                print(f"    'complexity': self._extract_custom_field(fields, '{field['id']}'),  # {field['name']}")
            elif 'customer' in field_name or 'requesting' in field_name:
                print(f"    'requesting_customer': self._extract_custom_field(fields, '{field['id']}'),  # {field['name']}")
            elif 'start' in field_name or 'target' in field_name:
                print(f"    'target_start': self._extract_custom_field(fields, '{field['id']}'),  # {field['name']}")
            elif 'solution' in field_name or 'deliver' in field_name:
                print(f"    'solution': self._extract_custom_field(fields, '{field['id']}'),  # {field['name']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("="*80)
    print("🔧 JIRA CUSTOM FIELD DISCOVERY TOOL")
    print("="*80)
    print()
    
    jira_url = input("Enter your Jira URL (e.g., https://your-company.atlassian.net): ").strip()
    access_token = input("Enter your Jira API token: ").strip()
    epic_id = input("Enter Issue ID to analyze (e.g., PROJECT-1234) or press Enter to skip: ").strip()
    
    if not jira_url or not access_token:
        print("❌ Both Jira URL and API token are required!")
        exit(1)
    
    discover_custom_fields(jira_url, access_token, epic_id if epic_id else None)
    
    print("\n" + "="*80)
    print("✅ Discovery complete!")
    print("="*80)