"""
Simple Sprint Retriever - Get sprints from same project and board as input sprint
"""
import logging
import csv
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dateutil import parser

logger = logging.getLogger(__name__)

class SimpleSprintRetriever:
    """Simple sprint retriever: find input sprint's board, get all sprints from that board."""
    
    def __init__(self, jira_client):
        self.jira_client = jira_client
    
    def get_sprints_from_same_board(self, sprint_name: str, days_back: int = 180) -> List[Dict]:
        """
        Simple approach:
        1. Find the input sprint and its board
        2. Get all sprints from that same board
        3. Export to CSV
        
        Args:
            sprint_name: Sprint name or ID
            days_back: How many days back to look
            
        Returns:
            List of sprint dictionaries
        """
        logger.info(f"🎯 Finding board for sprint: {sprint_name}")
        
        # Step 1: Find the sprint and its board
        board_id = self._find_sprint_board(sprint_name)
        if not board_id:
            # Try alternative approach: search by sprint name in JQL
            logger.info(f"🔄 Trying alternative search for sprint: {sprint_name}")
            board_id = self._find_board_via_jql_search(sprint_name)
            
        if not board_id:
            logger.error(f"❌ Could not find board for sprint: {sprint_name}")
            return []
        
        logger.info(f"✅ Found sprint on board: {board_id}")
        
        # Step 2: Get all sprints from that board
        sprints = self._get_all_sprints_from_board(board_id, days_back)
        
        # Step 3: Export to CSV
        if sprints:
            self._export_to_csv(sprints, f"board_{board_id}_sprints")
        
        return sprints
    
    def _find_sprint_board(self, sprint_name: str) -> Optional[int]:
        """Find which board contains the sprint."""
        try:
            # Try direct API if sprint is numeric (ID)
            if sprint_name.isdigit():
                url = f"{self.jira_client.base_url}/rest/agile/1.0/sprint/{sprint_name}"
                logger.info(f"🔍 GET {url}")
                response = self.jira_client.session.get(url)
                logger.info(f"📡 Response: {response.status_code}")
                
                if response.status_code == 200:
                    sprint_data = response.json()
                    logger.info(f"📊 Sprint data retrieved: {sprint_data}")
                    board_id = sprint_data.get('originBoardId')
                    logger.info(f"✅ Found board {board_id} for sprint ID {sprint_name}")
                    return board_id
            
            # Get ALL projects from sprint issues
            project_keys = self._get_projects_from_sprint(sprint_name)
            if not project_keys:
                return None
            
            # Search boards in ALL projects
            for project_key in project_keys:
                board_id = self._search_sprint_in_project_boards(sprint_name, project_key)
                if board_id:
                    return board_id
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding sprint board: {str(e)}")
            return None
    
    def _get_projects_from_sprint(self, sprint_name: str) -> List[str]:
        """Get ALL project keys from sprint issues."""
        try:
            jql = f'sprint = {sprint_name}' if sprint_name.isdigit() else f'sprint = "{sprint_name}"'
            logger.info(f"🔍 JQL: {jql}")
            
            issues = self.jira_client.fetch_issues(jql, max_results=50)
            projects = set()
            
            for issue in issues:
                key = issue.get('key', '')
                if '-' in key:
                    project_key = key.split('-')[0]
                    projects.add(project_key)
            
            project_list = list(projects)
            logger.info(f"✅ Found projects: {project_list}")
            return project_list
            
        except Exception as e:
            logger.error(f"❌ Error getting projects: {str(e)}")
            return []
    
    def _search_sprint_in_project_boards(self, sprint_name: str, project_key: str) -> Optional[int]:
        """Search for sprint in project boards."""
        try:
            # Get boards for project
            url = f"{self.jira_client.base_url}/rest/agile/1.0/board"
            params = {'projectKeyOrId': project_key, 'maxResults': 50}
            logger.info(f"🔍 GET {url} with params: {params}")
            
            response = self.jira_client.session.get(url, params=params)
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code != 200:
                return None
            
            boards = response.json().get('values', [])
            logger.info(f"📋 Found {len(boards)} boards in project {project_key}")
            
            # Search each board for the sprint
            for board in boards:
                board_id = board.get('id')
                board_name = board.get('name', 'Unknown')
                
                if self._board_contains_sprint(board_id, sprint_name):
                    logger.info(f"✅ Found sprint in board: {board_name} (ID: {board_id})")
                    return board_id
            
            logger.warning(f"⚠️ Sprint not found in any board of project {project_key}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching boards: {str(e)}")
            return None
    
    def _board_contains_sprint(self, board_id: int, sprint_name: str) -> bool:
        """Check if board contains the sprint."""
        try:
            url = f"{self.jira_client.base_url}/rest/agile/1.0/board/{board_id}/sprint"
            params = {'maxResults': 200}  # Increased to get more sprints
            logger.info(f"🔍 Checking board {board_id} for sprint: {sprint_name}")
            
            response = self.jira_client.session.get(url, params=params)
            logger.info(f"📡 Board {board_id} response: {response.status_code}")
            
            if response.status_code != 200:
                return False
            
            sprints = response.json().get('values', [])
            logger.info(f"📊 Board {board_id} has {len(sprints)} sprints")
            
            for sprint in sprints:
                current_name = sprint.get('name', '')
                logger.debug(f"  🔍 Comparing '{current_name}' with '{sprint_name}'")
                if current_name == sprint_name:
                    logger.info(f"✅ Found sprint '{sprint_name}' on board {board_id}")
                    return True
            
            logger.info(f"⚠️ Sprint '{sprint_name}' not found on board {board_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking board {board_id}: {str(e)}")
            return False
    
    def _get_all_sprints_from_board(self, board_id: int, days_back: int) -> List[Dict]:
        """Get all sprints from the board."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            url = f"{self.jira_client.base_url}/rest/agile/1.0/board/{board_id}/sprint"
            params = {'maxResults': 200}
            logger.info(f"🔍 GET {url} with params: {params}")
            
            response = self.jira_client.session.get(url, params=params)
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to get sprints from board {board_id}")
                return []
            
            all_sprints = response.json().get('values', [])
            logger.info(f"📊 Found {len(all_sprints)} total sprints on board")
            
            # Log first few sprints for debugging
            for i, sprint in enumerate(all_sprints[:3]):
                logger.info(f"📊 Sprint {i+1}: {sprint}")
            
            # Filter by date and format - always include current sprint
            recent_sprints = []
            current_sprint_found = False
            
            for sprint in all_sprints:
                sprint_name = sprint.get('name', '')
                sprint_id = str(sprint.get('id', ''))
                
                # Always include the current sprint being analyzed
                is_current_sprint = (sprint_name == self.current_sprint_name if hasattr(self, 'current_sprint_name') else False) or sprint_id == str(self.current_sprint_id if hasattr(self, 'current_sprint_id') else '')
                
                if is_current_sprint or self._is_recent_sprint(sprint, cutoff_date):
                    recent_sprints.append({
                        'id': sprint.get('id'),
                        'name': sprint.get('name'),
                        'state': sprint.get('state'),
                        'start_date': sprint.get('startDate'),
                        'end_date': sprint.get('endDate'),
                        'complete_date': sprint.get('completeDate')
                    })
                    if is_current_sprint:
                        current_sprint_found = True
                        logger.info(f"✅ Current sprint found and included: {sprint_name}")
            
            logger.info(f"✅ Found {len(recent_sprints)} recent sprints (last {days_back} days)")
            return recent_sprints
            
        except Exception as e:
            logger.error(f"❌ Error getting sprints from board: {str(e)}")
            return []
    
    def _is_recent_sprint(self, sprint: Dict, cutoff_date: datetime) -> bool:
        """Check if sprint is recent enough."""
        try:
            date_str = (sprint.get('completeDate') or 
                       sprint.get('endDate') or 
                       sprint.get('startDate'))
            
            if date_str:
                sprint_date = parser.parse(date_str)
                return sprint_date >= cutoff_date
            
            return True  # Include sprints without dates
            
        except Exception:
            return True  # Include sprints with bad dates
    
    def _find_board_via_jql_search(self, sprint_name: str) -> Optional[int]:
        """Alternative method: find board by searching sprint issues and checking their sprint field."""
        try:
            # Get issues from the sprint
            jql = f'sprint = "{sprint_name}"'
            logger.info(f"🔍 Alternative search JQL: {jql}")
            
            issues = self.jira_client.fetch_issues(jql, max_results=1)
            if not issues:
                logger.warning(f"⚠️ No issues found for sprint: {sprint_name}")
                return None
            
            # Get detailed issue to access sprint information
            issue_key = issues[0].get('key')
            logger.info(f"🔍 Getting detailed info for issue: {issue_key}")
            
            response = self.jira_client.session.get(
                f"{self.jira_client.base_url}/rest/api/2/issue/{issue_key}",
                params={'fields': 'customfield_10020'}  # Sprint field
            )
            
            if response.status_code == 200:
                issue_data = response.json()
                sprint_field = issue_data.get('fields', {}).get('customfield_10020', [])
                
                # Sprint field contains sprint objects with originBoardId
                for sprint_obj in sprint_field or []:
                    if isinstance(sprint_obj, dict) and sprint_obj.get('name') == sprint_name:
                        board_id = sprint_obj.get('originBoardId')
                        if board_id:
                            logger.info(f"✅ Found board {board_id} via JQL search")
                            return board_id
            
            logger.warning(f"⚠️ Could not extract board ID from sprint field")
            return None
            
        except Exception as e:
            logger.error(f"❌ JQL search failed: {str(e)}")
            return None
    
    def _export_to_csv(self, sprints: List[Dict], filename_prefix: str):
        """Export sprints to CSV in data folder."""
        try:
            import os
            
            # Create data folder if it doesn't exist
            data_folder = "data"
            os.makedirs(data_folder, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.csv"
            filepath = os.path.join(data_folder, filename)
            
            logger.info(f"📊 Exporting {len(sprints)} sprints to: {filepath}")
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name', 'state', 'start_date', 'end_date', 'complete_date'])
                writer.writeheader()
                writer.writerows(sprints)
            
            full_path = os.path.abspath(filepath)
            logger.info(f"✅ CSV saved: {full_path}")
            
        except Exception as e:
            logger.error(f"❌ CSV export failed: {str(e)}")