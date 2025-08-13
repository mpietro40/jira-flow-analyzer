"""
Script to run timezone-specific tests
"""

import subprocess
import sys

def run_timezone_tests():
    """Run all timezone-related tests."""
    
    print("Running timezone-specific tests...")
    
    # Run timezone tests specifically
    test_commands = [
        ["pytest", "tests/test_data_analyzer.py::TestDataAnalyzer::test_timezone_aware_date_parsing", "-v"],
        ["pytest", "tests/test_data_analyzer.py::TestDataAnalyzer::test_mixed_timezone_lead_time_calculation", "-v"],
        ["pytest", "tests/test_timezone_integration.py", "-v"],
        ["pytest", "tests/test_jira_client.py::TestJiraClient::test_process_issue_with_multiple_timezones", "-v"]
    ]
    
    all_passed = True
    
    for cmd in test_commands:
        print(f"\n>>> Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            print(result.stdout)
            print(result.stderr)
            all_passed = False
    
    if all_passed:
        print("\n🎉 All timezone tests passed!")
        return 0
    else:
        print("\n💥 Some timezone tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(run_timezone_tests())