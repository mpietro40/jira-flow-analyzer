"""
Epic Fix Version Distribution Web Application
Production-ready Flask app for analyzing epics by fix version across initiatives

Author: Epic Analysis Tool
Purpose: Analyze which epics are assigned to specific fix versions across initiatives
"""

from flask import Flask, render_template, request, jsonify, send_file
import logging
from datetime import datetime
from typing import List, Dict, Set
from collections import defaultdict
import json
from pathlib import Path
import tempfile

from jira_client import JiraClient
from epic_fixversion_pdf_generator import EpicFixVersionPDFGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('epic_fixversion.log')
    ]
)
logger = logging.getLogger('EpicFixVersionApp')

app = Flask(__name__)
app.secret_key = 'epic-fixversion-key-change-in-production'

# Results directory for persistence
RESULTS_DIR = Path(__file__).parent / 'epic_fixversion_results'
RESULTS_DIR.mkdir(exist_ok=True)

class EpicFixVersionAnalyzer:
    """Analyzes epics by fix version across initiatives"""
    
    def __init__(self, jira_client: JiraClient):
        self.jira_client = jira_client
    
    def analyze(self, initiative_jql: str, fix_version: str = None, excluded_statuses: List[str] = None) -> Dict:
        """
        Analyze epics across initiatives using hierarchy traversal
        
        Args:
            initiative_jql: JQL to find initiatives
            fix_version: Optional fix version to filter epics
            excluded_statuses: Optional list of statuses to exclude
            
        Returns:
            Analysis results with epics grouped by initiative
        """
        if excluded_statuses is None:
            excluded_statuses = ['Done', 'Closed', 'Abandoned']
        
        logger.info(f"🚀 Starting analysis")
        if fix_version:
            logger.info(f"🏷️ Fix version filter: {fix_version}")
        else:
            logger.info(f"🏷️ No fix version filter (all epics)")
        logger.info(f"🚫 Excluded statuses: {', '.join(excluded_statuses)}")
        logger.info(f"📋 Initiative JQL: {initiative_jql}")
        
        try:
            # Step 1: Fetch initiatives
            initiatives = self._fetch_initiatives(initiative_jql)
            if not initiatives:
                logger.warning("⚠️ No initiatives found")
                return {'error': 'No initiatives found with the given JQL query'}
            
            logger.info(f"✅ Found {len(initiatives)} initiatives")
            
            # Step 2: For each initiative, get epics through hierarchy
            results = []
            total_epics = 0
            
            for initiative in initiatives:
                initiative_key = initiative['key']
                initiative_summary = initiative.get('summary', 'No summary')
                
                logger.info(f"🔍 Analyzing initiative: {initiative_key}")
                
                # Get all child epics through hierarchy
                epics = self._get_initiative_epics_via_hierarchy(initiative_key, fix_version, excluded_statuses)
                
                if epics:
                    logger.info(f"  ✅ Found {len(epics)} epics")
                    total_epics += len(epics)
                    
                    results.append({
                        'initiative_key': initiative_key,
                        'initiative_summary': initiative_summary,
                        'epic_count': len(epics),
                        'epics': epics
                    })
                else:
                    logger.info(f"  ℹ️ No epics found")
            
            logger.info(f"✅ Analysis complete: {total_epics} total epics across {len(results)} initiatives")
            
            return {
                'success': True,
                'fix_version': fix_version or 'All',
                'excluded_statuses': excluded_statuses,
                'total_initiatives': len(initiatives),
                'initiatives_with_epics': len(results),
                'total_epics': total_epics,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}", exc_info=True)
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _fetch_initiatives(self, jql_query: str) -> List[Dict]:
        """Fetch initiatives using JQL"""
        try:
            logger.info(f"📥 Fetching initiatives...")
            initiatives = self.jira_client.fetch_issues(jql_query, max_results=1000)
            logger.info(f"📊 Fetched {len(initiatives)} initiatives")
            return initiatives
        except Exception as e:
            logger.error(f"❌ Failed to fetch initiatives: {str(e)}")
            raise
    
    def _get_initiative_epics_via_hierarchy(self, initiative_key: str, fix_version: str = None, excluded_statuses: List[str] = None) -> List[Dict]:
        """Get all epics for an initiative through hierarchy traversal"""
        try:
            # Build status exclusion clause
            status_exclusion = ''
            if excluded_statuses:
                status_list = ' AND '.join([f'status != "{status}"' for status in excluded_statuses])
                status_exclusion = f' AND {status_list}'
            
            # Use childIssuesOf to get all descendants including epics
            # This traverses: Initiative -> Feature -> Sub-Feature -> Epic
            if fix_version:
                jql = (f'issuekey in childIssuesOf("{initiative_key}") '
                       f'AND type = Epic '
                       f'AND fixVersion = "{fix_version}"'
                       f'{status_exclusion}')
            else:
                jql = (f'issuekey in childIssuesOf("{initiative_key}") '
                       f'AND type = Epic'
                       f'{status_exclusion}')
            
            logger.debug(f"  🔍 JQL: {jql}")
            
            # Fetch epics - note: fetch_issues includes fixVersions in fields
            epics = self.jira_client.fetch_issues(jql, max_results=2000)
            
            # Extract relevant epic information including fix version
            epic_list = []
            for epic in epics:
                # Get fix versions from epic
                fix_versions = self._extract_fix_versions(epic)
                fields = epic.get('fields', {})
                
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
                epic_list.append(epic_data)
                logger.debug(f"    📌 {epic_data['key']}: {epic_data['summary'][:50]}...")
            
            return epic_list
            
        except Exception as e:
            logger.warning(f"  ⚠️ Failed to get epics for {initiative_key}: {str(e)}")
            return []
    
    def _extract_project_key(self, issue: Dict) -> str:
        """Extract project key from issue"""
        if issue.get('project_key'):
            return issue['project_key']
        
        fields = issue.get('fields', {})
        if fields.get('project', {}).get('key'):
            return fields['project']['key']
        
        issue_key = issue.get('key', '')
        if '-' in issue_key:
            return issue_key.split('-')[0]
        
        return 'Unknown'
    
    def _extract_fix_versions(self, issue: Dict) -> List[str]:
        """Extract fix version names from issue"""
        # Try to get from fields first (raw API response)
        fields = issue.get('fields', {})
        fix_versions = fields.get('fixVersions', [])
        
        # If not found, try alternative field names
        if not fix_versions:
            fix_versions = fields.get('fixversions', [])
        
        if not fix_versions:
            return []
        
        # Extract names from version objects
        version_names = []
        for v in fix_versions:
            if isinstance(v, dict):
                name = v.get('name', '')
                if name:
                    version_names.append(name)
            elif isinstance(v, str):
                # In case it's already a string
                version_names.append(v)
        
        return version_names
    
    def _extract_custom_field(self, fields: Dict, field_id: str) -> str:
        """Extract custom field value from issue fields"""
        value = fields.get(field_id)
        if not value:
            return ''
        
        # Handle different field types
        if isinstance(value, dict):
            return value.get('value', value.get('name', str(value)))
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                return ', '.join([v.get('value', v.get('name', str(v))) for v in value])
            return ', '.join([str(v) for v in value])
        return str(value)
    
    def _extract_comments(self, fields: Dict) -> Dict:
        """Extract platform and impacts comments from issue"""
        comments = fields.get('comment', {})
        comment_list = comments.get('comments', [])
        
        result = {'platform': '', 'impacts': ''}
        
        for comment in comment_list:
            body = comment.get('body', '').lower()
            comment_text = comment.get('body', '')
            
            # Look for platform mentions
            if 'platform' in body and not result['platform']:
                result['platform'] = comment_text[:200]
            
            # Look for impact/delay mentions
            if any(word in body for word in ['impact', 'delay', 'risk']) and not result['impacts']:
                result['impacts'] = comment_text[:200]
        
        return result

def save_results_to_file(fix_version: str, results: Dict) -> bool:
    """Save analysis results to JSON file"""
    try:
        # Sanitize fix version for filename
        safe_version = fix_version.replace('/', '_').replace('\\', '_').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_version}_{timestamp}.json"
        filepath = RESULTS_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to {filepath}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save results: {str(e)}")
        return False

@app.route('/')
def index():
    """Main page"""
    return render_template('epic_fixversion.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process analysis request"""
    try:
        # Extract form data
        jira_url = request.form.get('jira_url', '').strip()
        access_token = request.form.get('access_token', '').strip()
        initiative_jql = request.form.get('initiative_jql', '').strip()
        fix_version = request.form.get('fix_version', '').strip() or None  # Optional
        excluded_statuses_str = request.form.get('excluded_statuses', '').strip()
        
        # Parse excluded statuses
        excluded_statuses = None
        if excluded_statuses_str:
            excluded_statuses = [s.strip() for s in excluded_statuses_str.split(',') if s.strip()]
        
        logger.info(f"📥 Received analysis request")
        logger.info(f"  🌐 Jira URL: {jira_url}")
        logger.info(f"  📋 Initiative JQL: {initiative_jql}")
        logger.info(f"  🏷️ Fix Version: {fix_version or 'All (no filter)'}")
        logger.info(f"  🚫 Excluded Statuses: {excluded_statuses or 'Default (Done, Closed, Abandonned, Cancelled, Resolved)'}")
        
        # Validate inputs (fix_version is now optional)
        if not all([jira_url, access_token, initiative_jql]):
            logger.warning("⚠️ Missing required fields")
            return jsonify({
                'error': 'Missing required fields (Jira URL, Access Token, and Initiative JQL are required)',
                'error_type': 'ValidationError'
            }), 400
        
        # Initialize Jira client
        logger.info("🔗 Initializing Jira client...")
        jira_client = JiraClient(jira_url, access_token)
        
        # Test connection
        logger.info("🔌 Testing Jira connection...")
        if not jira_client.test_connection():
            logger.error("❌ Jira connection failed")
            return jsonify({
                'error': 'Failed to connect to Jira. Please check your URL and token.',
                'error_type': 'ConnectionError'
            }), 401
        
        logger.info("✅ Jira connection successful")
        
        # Perform analysis
        analyzer = EpicFixVersionAnalyzer(jira_client)
        results = analyzer.analyze(initiative_jql, fix_version, excluded_statuses)
        
        if 'error' in results:
            logger.error(f"❌ Analysis error: {results['error']}")
            return jsonify({
                'error': results['error'],
                'error_type': 'AnalysisError'
            }), 404
        
        # Save results to file
        save_results_to_file(fix_version, results)
        
        logger.info("✅ Analysis completed successfully")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Export analysis results to PDF"""
    try:
        data = request.get_json()
        analysis_data = data.get('analysis_data', data)
        jira_url = data.get('jira_url', '')
        
        logger.info("📄 Generating PDF report...")
        
        # Generate PDF
        pdf_generator = EpicFixVersionPDFGenerator()
        pdf_buffer = pdf_generator.generate_report(analysis_data, jira_url=jira_url)
        
        # Create filename
        fix_version = analysis_data.get('fix_version', 'All').replace('/', '_').replace('\\', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'epic_distribution_{fix_version}_{timestamp}.pdf'
        
        logger.info(f"✅ PDF generated: {filename}")
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'error_type': 'PDFGenerationError'
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Epic Fix Version Analyzer'
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Epic Fix Version Analyzer")
    logger.info(f"📁 Results directory: {RESULTS_DIR}")
    app.run(debug=True, host='0.0.0.0', port=5400)
