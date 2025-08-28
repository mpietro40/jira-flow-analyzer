    def get_epic_children(self, epic_key: str) -> List[Dict]:
        """
        Fetch all issues linked to an epic.
        
        Args:
            epic_key (str): The key of the epic
            
        Returns:
            List[Dict]: List of child issues
        """
        logger.info(f"🔍 Fetching child issues for epic: {epic_key}")
        
        try:
            # Get issues in the epic
            jql = f"'Epic Link' = {epic_key}"
            params = {
                'jql': jql,
                'maxResults': 500,  # Adjust if needed
                'fields': 'key,summary,status,timeoriginalestimate,timeestimate'
            }
            
            response = self.session.get(
                f'{self.base_url}/rest/api/2/search',
                params=params
            )
            response.raise_for_status()
            
            return response.json().get('issues', [])
            
        except Exception as e:
            logger.error(f"Error fetching epic children for {epic_key}: {str(e)}")
            return []
