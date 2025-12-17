"""
Status Discovery Tool
Helps you find all status types in your Jira project

Usage:
    python discover_statuses.py
"""

import requests
import json
from datetime import datetime

def discover_statuses(jira_url, access_token):
    """
    Discover all status types across all Jira projects
    
    Args:
        jira_url: Your Jira URL (e.g., https://your-company.atlassian.net)
        access_token: Your Jira API token
    """
    print(f"🔍 Discovering statuses from all projects...\n")
    
    try:
        # Get all projects first
        projects_url = f"{jira_url}/rest/api/2/project"
        projects_response = requests.get(
            projects_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if projects_response.status_code != 200:
            print(f"❌ Error fetching projects: {projects_response.status_code}")
            print(projects_response.text)
            return
        
        projects = projects_response.json()
        print(f"✅ Found {len(projects)} projects\n")
        
        all_statuses = {}
        status_by_project = {}
        
        # Get statuses for each project
        for project in projects:
            project_key = project['key']
            project_name = project['name']
            print(f"  📂 Processing {project_key} - {project_name}...")
            
            url = f"{jira_url}/rest/api/2/project/{project_key}/statuses"
        
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                print(f"    ⚠️  Skipped (Error {response.status_code})")
                continue
            
            issue_types = response.json()
            status_by_project[project_key] = {'name': project_name, 'statuses': []}
            
            for issue_type in issue_types:
                for status in issue_type.get('statuses', []):
                    status_id = status['id']
                    status_name = status['name']
                    status_category = status['statusCategory']['name']
                    
                    if status_id not in all_statuses:
                        all_statuses[status_id] = {
                            'id': status_id,
                            'name': status_name,
                            'category': status_category,
                            'projects': []
                        }
                    
                    if project_key not in all_statuses[status_id]['projects']:
                        all_statuses[status_id]['projects'].append(project_key)
                    
                    if not any(s['id'] == status_id for s in status_by_project[project_key]['statuses']):
                        status_by_project[project_key]['statuses'].append({
                            'id': status_id,
                            'name': status_name,
                            'category': status_category
                        })
        
        print()
        
        print(f"✅ Found {len(all_statuses)} unique statuses across all projects\n")
        print("="*80)
        
        # Display all statuses
        print("\n📊 ALL UNIQUE STATUSES:\n")
        for status in sorted(all_statuses.values(), key=lambda x: x['name']):
            print(f"  🔹 {status['name']}")
            print(f"     ID: {status['id']}")
            print(f"     Category: {status['category']}")
            print(f"     Used in projects: {', '.join(status['projects'])}")
            print()
        
        # Display by project
        print("\n📋 STATUSES BY PROJECT:\n")
        for project_key, project_data in sorted(status_by_project.items()):
            print(f"  📌 {project_key} - {project_data['name']}:")
            for status in sorted(project_data['statuses'], key=lambda x: x['name']):
                print(f"     • {status['name']} (ID: {status['id']}, Category: {status['category']})")
            print()
        
        # Save to JSON
        output_data = {
            'jira_url': jira_url,
            'discovery_date': datetime.now().isoformat(),
            'total_projects': len(projects),
            'all_statuses': list(all_statuses.values()),
            'statuses_by_project': status_by_project
        }
        
        json_file = 'data/statuses_all_projects.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Statuses saved to: {json_file}")
        
        # Save to text file
        text_output = []
        text_output.append("="*80)
        text_output.append("STATUSES DISCOVERED FROM ALL JIRA PROJECTS")
        text_output.append(f"Jira URL: {jira_url}")
        text_output.append(f"Discovery Date: {datetime.now().isoformat()}")
        text_output.append("="*80)
        text_output.append("")
        text_output.append(f"Total projects: {len(projects)}")
        text_output.append(f"Total unique statuses: {len(all_statuses)}")
        text_output.append("")
        text_output.append("="*80)
        text_output.append("ALL UNIQUE STATUSES")
        text_output.append("="*80)
        text_output.append("")
        
        for status in sorted(all_statuses.values(), key=lambda x: x['name']):
            text_output.append(f"Status Name: {status['name']}")
            text_output.append(f"Status ID: {status['id']}")
            text_output.append(f"Category: {status['category']}")
            text_output.append(f"Used in Projects: {', '.join(status['projects'])}")
            text_output.append("-" * 80)
            text_output.append("")
        
        text_output.append("")
        text_output.append("="*80)
        text_output.append("STATUSES BY PROJECT")
        text_output.append("="*80)
        text_output.append("")
        
        for project_key, project_data in sorted(status_by_project.items()):
            text_output.append(f"Project: {project_key} - {project_data['name']}")
            text_output.append("")
            for status in sorted(project_data['statuses'], key=lambda x: x['name']):
                text_output.append(f"  - {status['name']} (ID: {status['id']}, Category: {status['category']})")
            text_output.append("")
            text_output.append("-" * 80)
            text_output.append("")
        
        text_file = 'statuses_all_projects.txt'
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text_output))
        
        print(f"💾 Text report saved to: {text_file}")
        
        # Summary
        print("\n" + "="*80)
        print("\n📈 SUMMARY:\n")
        print(f"  Total projects scanned: {len(projects)}")
        print(f"  Total unique statuses: {len(all_statuses)}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("="*80)
    print("🔧 JIRA STATUS DISCOVERY TOOL")
    print("="*80)
    print()
    
    jira_url = input("Enter your Jira URL (e.g., https://your-company.atlassian.net): ").strip()
    access_token = input("Enter your Jira API token: ").strip()
    
    if not jira_url or not access_token:
        print("❌ Both Jira URL and API token are required!")
        exit(1)
    
    discover_statuses(jira_url, access_token)
    
    print("\n" + "="*80)
    print("✅ Discovery complete!")
    print("="*80)
