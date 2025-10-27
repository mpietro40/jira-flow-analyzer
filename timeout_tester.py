"""
Timeout Configuration Tester
Tests different timeout settings to help optimize Jira client performance.
"""

import json
import os
import time
from datetime import datetime
from jira_client import JiraClient

def load_credentials():
    """Get Jira credentials from user input."""
    print("\n🔐 Please enter your Jira credentials:")
    
    jira_url = input("Jira URL (e.g., https://company.atlassian.net): ").strip()
    if not jira_url:
        print("❌ Jira URL is required")
        return None, None
    
    access_token = input("Access Token: ").strip()
    if not access_token:
        print("❌ Access token is required")
        return None, None
    
    return jira_url, access_token

def test_timeout_profile(client, profile_name, settings, test_jql="project = ISDOP"):
    """Test a specific timeout profile."""
    print(f"\n🧪 Testing profile: {profile_name}")
    print(f"   Settings: {settings}")
    
    # Configure client with test settings
    client.configure_timeouts(**settings)
    
    start_time = time.time()
    success = False
    issues_fetched = 0
    
    try:
        # Test with a simple query first
        issues = client.fetch_issues(test_jql, max_results=50)
        issues_fetched = len(issues)
        success = True
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    if success:
        print(f"   ✅ Success: {issues_fetched} issues in {duration:.1f}s")
    else:
        print(f"   ❌ Failed after {duration:.1f}s")
    
    return {
        'profile': profile_name,
        'success': success,
        'duration': duration,
        'issues_fetched': issues_fetched,
        'settings': settings
    }

def main():
    """Main timeout testing function."""
    print("🔧 Jira Timeout Configuration Tester")
    print("=" * 50)
    
    # Get credentials
    jira_url, access_token = load_credentials()
    if not jira_url or not access_token:
        print("❌ Credentials are required to run the timeout tester")
        return
    
    # Create client
    client = JiraClient(jira_url, access_token)
    
    # Test connection first
    print("🔗 Testing basic connection...")
    if not client.test_connection():
        print("❌ Basic connection failed. Check your credentials and URL.")
        return
    
    print("✅ Basic connection successful")
    
    # Load timeout profiles
    config_path = os.path.join(os.path.dirname(__file__), 'timeout_config.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        profiles = config.get('performance_profiles', {})
    except Exception as e:
        print(f"❌ Failed to load timeout config: {e}")
        return
    
    # Test each profile
    results = []
    
    for profile_name, settings in profiles.items():
        result = test_timeout_profile(client, profile_name, settings)
        results.append(result)
        time.sleep(1)  # Brief pause between tests
    
    # Show recommendations
    print("\n📊 RESULTS SUMMARY")
    print("=" * 50)
    
    successful_profiles = [r for r in results if r['success']]
    
    if successful_profiles:
        # Find fastest successful profile
        fastest = min(successful_profiles, key=lambda x: x['duration'])
        
        print(f"🏆 Recommended profile: {fastest['profile']}")
        print(f"   Duration: {fastest['duration']:.1f}s")
        print(f"   Issues fetched: {fastest['issues_fetched']}")
        print(f"   Settings: {fastest['settings']}")
        
        # Update timeout_config.json with recommended settings
        try:
            config['timeout_settings'] = fastest['settings']
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n✅ Updated timeout_config.json with recommended settings")
        except Exception as e:
            print(f"⚠️ Failed to update config file: {e}")
            
    else:
        print("❌ All profiles failed. Your server may be experiencing issues.")
        print("💡 Try manually increasing timeouts in timeout_config.json")
    
    print("\n🔧 Manual Configuration:")
    print("   Edit timeout_config.json to fine-tune settings")
    print("   Increase read_timeout if you see timeout errors")
    print("   Decrease batch_size if queries are too complex")

if __name__ == "__main__":
    main()