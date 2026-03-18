"""
Initiative Viewer - Flask Application (Refactored)
Displays hierarchical Jira structure: Business Initiative → Feature → Sub-Feature → Epic
With area-based organization and risk probability color coding.

Author: Pietro Maffi
Version: 2.0.0
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, render_template, request, jsonify, session, send_file
import logging
from typing import List, Dict, Optional, Set, Any, Union
from collections import defaultdict
from datetime import datetime, timedelta
import io
from apps.initiative_viewer.pdf_generator import PAGE_A4_LANDSCAPE, PAGE_SUPER_WIDE

# Import shared utilities
from src.common import (
    JiraClient,
    CacheManager,
    FileStorage,
    validate_jira_credentials,
    handle_errors,
    log_request,
    get_jira_client_from_request
)
from src.config import get_config

# Import app-specific modules
from apps.initiative_viewer.pdf_generator import InitiativeViewerPDFGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('InitiativeViewer')

# Configuration
config = get_config()

# Create Blueprint instead of Flask app
blueprint = Blueprint('initiative_viewer', __name__,
                     template_folder='templates',
                     static_folder='static')

# Initialize utilities
cache = CacheManager(cache_dir=os.path.join(config.CACHE_DIR, 'initiative_viewer'))
storage = FileStorage(base_path=os.path.join(config.STORAGE_DIR, 'initiative_viewer'))


@blueprint.route('/favicon.ico')
def favicon():
    """Serve the favicon so browsers don't log 404s."""
    return blueprint.send_static_file('favicon.ico')

# Canonical set of Jira statuses that count as "done".
# All values are lowercase — compare with  epic_status.lower()
COMPLETED_STATUSES = {'done', 'closed', 'completed', 'complete', 'resolved', 'prd deployed'}

# Confidence Level field → numeric risk mapping (used as fallback when risk field is absent).
# Reflects PI planning assessment commitment at the team level:
#   Committed (green=1), Tentative (orange=3), Out (red=5), Added (purple=6), None (no assessment)
CONFIDENCE_LEVEL_MAP: dict = {
    'committed': 1,   # fully committed — delivered as planned
    'tentative': 3,   # tentative commitment — at risk of slipping
    'out':       5,   # not deliverable in this PI
    'added':     6,   # new topic integrated into the backlog during the PI (purple)
    'none':      None,  # default — no PI assessment yet
}


def compute_initiative_completion(initiative: Dict) -> Dict:
    """
    Calculate epic completion ratio for an initiative.

    Uses epic statuses already present in the fetched hierarchy — zero extra Jira queries.

    Returns:
        dict with keys ``total`` (int), ``done`` (int), ``pct`` (int 0-100).
    """
    total = 0
    done = 0
    for feature in initiative.get('features', []):
        for sub_feature in feature.get('sub_features', []):
            for epics in sub_feature.get('epics_by_area', {}).values():
                for epic in epics:
                    total += 1
                    if epic.get('status', '').lower() in COMPLETED_STATUSES:
                        done += 1
    pct = round(100 * done / total) if total > 0 else 0
    return {'total': total, 'done': done, 'pct': pct}


# Helper functions

def filter_empty_hierarchy(initiatives: List[Dict]) -> List[Dict]:
    """Filter out features and sub-features without epics for cleaner exports."""
    filtered_initiatives = []
    
    for initiative in initiatives:
        filtered_features = []
        
        for feature in initiative.get('features', []):
            filtered_sub_features = []
            
            for sub_feature in feature.get('sub_features', []):
                epics_by_area = sub_feature.get('epics_by_area', {})
                total_epics = sum(len(epics) for epics in epics_by_area.values())
                
                if total_epics > 0:
                    filtered_sub_features.append(sub_feature)
            
            if filtered_sub_features:
                feature_copy = feature.copy()
                feature_copy['sub_features'] = filtered_sub_features
                filtered_features.append(feature_copy)
        
        if filtered_features:
            initiative_copy = initiative.copy()
            initiative_copy['features'] = filtered_features
            filtered_initiatives.append(initiative_copy)
    
    return filtered_initiatives


def get_most_recent_cache_data() -> Optional[Dict]:
    """Get the most recent cached analysis data."""
    try:
        cached_items = cache.list_cached()
        if not cached_items:
            return None
        
        # Get most recent valid cache
        valid_items = [item for item in cached_items if item.get('is_valid', False)]
        if not valid_items:
            return None
        
        most_recent = max(valid_items, key=lambda x: x.get('timestamp', ''))
        return cache.get(most_recent['key'])
    except Exception as e:
        logger.error(f"Error loading cached data: {e}")
        return None


# Jira Hierarchy Fetcher

class JiraHierarchyFetcher:
    """Fetches Jira hierarchy: Business Initiative → Feature → Sub-Feature → Epic"""
    
    def __init__(self, jira_client: JiraClient):
        self.jira_client = jira_client
    
    def fetch_hierarchy(self, query: str, fix_version: str) -> List[Dict]:
        """
        Fetch complete hierarchy starting from Business Initiatives.
        
        Args:
            query: JQL query to filter initiatives
            fix_version: Fix version to filter features/sub-features
            
        Returns:
            Complete hierarchical data structure
        """
        logger.info(f"🔍 Fetching hierarchy for fixVersion: {fix_version}")
        
        # Step 1: Fetch Business Initiatives
        logger.info(f"⏳ Step 1/4: Fetching Business Initiatives...")
        initiatives = self._fetch_initiatives(query)
        logger.info(f"📊 Found {len(initiatives)} initiatives")
        
        # Step 2: For each initiative, fetch features
        logger.info(f"⏳ Step 2/4: Fetching Features...")
        for i, initiative in enumerate(initiatives, 1):
            logger.info(f"  📍 Processing initiative {i}/{len(initiatives)}: {initiative['key']}")
            initiative['features'] = self._fetch_features(initiative['key'], fix_version)
            logger.info(f"    ✓ Found {len(initiative['features'])} features")
            
            # Step 3: For each feature, fetch sub-features
            for feature in initiative['features']:
                feature['sub_features'] = self._fetch_sub_features(feature['key'], fix_version)
                logger.info(f"    ✓ Feature {feature['key']}: {len(feature['sub_features'])} sub-features")
                
                # Step 4: For each sub-feature, fetch epics by area
                for sub_feature in feature['sub_features']:
                    sub_feature['epics_by_area'] = self._fetch_epics_by_area(sub_feature['key'])
                    total_epics = sum(len(epics) for epics in sub_feature['epics_by_area'].values())
                    logger.info(f"      ✓ Sub-Feature {sub_feature['key']}: {total_epics} epics")
        
        return initiatives
    
    def _fetch_initiatives(self, query: str) -> List[Dict]:
        """Fetch Business Initiatives based on query."""
        try:
            issues = self.jira_client.fetch_issues(query, max_results=500)
            
            initiatives = []
            for issue in issues:
                initiative_data = self._fetch_issue_details(issue['key'])
                if initiative_data:
                    initiatives.append(initiative_data)
            
            return initiatives
        except Exception as e:
            logger.error(f"Failed to fetch initiatives: {str(e)}")
            raise
    
    def _fetch_features(self, initiative_key: str, fix_version: str) -> List[Dict]:
        """Fetch Features under an initiative with specific fixVersion."""
        jql = (f'issuekey in childIssuesOf("{initiative_key}") '
               f'AND issuetype = Feature '
               f'AND fixVersion = "{fix_version}"')
        
        try:
            issues = self.jira_client.fetch_issues(jql, max_results=200)
            
            if not issues:
                logger.info(f"ℹ️ No features found with fixVersion '{fix_version}' for {initiative_key}")
            
            features = []
            for issue in issues:
                feature_data = self._fetch_issue_details(issue['key'])
                if feature_data:
                    features.append(feature_data)
            
            return features
        except Exception as e:
            logger.error(f"Failed to fetch features for {initiative_key}: {str(e)}")
            return []
    
    def _fetch_sub_features(self, feature_key: str, fix_version: str) -> List[Dict]:
        """Fetch Sub-Features under a feature with specific fixVersion."""
        jql = (f'issuekey in childIssuesOf("{feature_key}") '
               f'AND issuetype = "Sub-Feature" '
               f'AND fixVersion = "{fix_version}"')
        
        try:
            issues = self.jira_client.fetch_issues(jql, max_results=200)
            
            if not issues:
                logger.debug(f"ℹ️ No sub-features found with fixVersion '{fix_version}' for {feature_key}")
            
            sub_features = []
            for issue in issues:
                sub_feature_data = self._fetch_issue_details(issue['key'])
                if sub_feature_data:
                    sub_features.append(sub_feature_data)
            
            return sub_features
        except Exception as e:
            logger.error(f"Failed to fetch sub-features for {feature_key}: {str(e)}")
            return []
    
    def _fetch_epics_by_area(self, sub_feature_key: str) -> Dict[str, List[Dict]]:
        """Fetch Epics linked to a sub-feature, organized by area (project)."""
        jql = f'issuekey in childIssuesOf("{sub_feature_key}") AND issuetype = Epic'
        
        try:
            issues = self.jira_client.fetch_issues(jql, max_results=500)
            
            epics_by_area = defaultdict(list)
            
            for issue in issues:
                epic_data = self._fetch_issue_details(issue['key'])
                if epic_data:
                    area = epic_data.get('project_key', 'Unknown')
                    epics_by_area[area].append(epic_data)
            
            return dict(epics_by_area)
        except Exception as e:
            logger.error(f"Failed to fetch epics for {sub_feature_key}: {str(e)}")
            return {}
    
    def _fetch_issue_details(self, issue_key: str) -> Optional[Dict]:
        """Fetch detailed information for a single issue including risk probability."""
        try:
            response = self.jira_client.session.get(
                f"{self.jira_client.base_url}/rest/api/2/issue/{issue_key}",
                params={'expand': 'names'},
                timeout=self.jira_client.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch details for {issue_key}")
                return None
            
            data = response.json()
            fields = data.get('fields', {})
            field_names = data.get('names', {})
            
            # Search for Risk-related and Confidence Level fields in a single pass
            risk_field_id = None
            confidence_field_id = None
            for field_id, field_name in field_names.items():
                field_name_lower = field_name.lower().strip()
                if risk_field_id is None and 'risk' in field_name_lower and (
                        'status' in field_name_lower or 'probability' in field_name_lower):
                    risk_field_id = field_id
                    logger.debug(f"🎯 Found risk field for {issue_key}: {field_name} ({field_id})")
                if confidence_field_id is None and field_name_lower == 'confidence level':
                    confidence_field_id = field_id
                    logger.debug(f"🎯 Found confidence level field for {issue_key}: {field_name} ({field_id})")
                if risk_field_id and confidence_field_id:
                    break
            
            # Extract basic fields
            assignee = fields.get('assignee')
            assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
            
            status = fields.get('status', {})
            status_name = status.get('name', 'Unknown')
            
            project = fields.get('project', {})
            project_key = project.get('key', 'Unknown')
            
            # Process risk probability — Confidence Level used as fallback when risk field absent/None
            risk_probability = None
            if risk_field_id:
                risk_value = fields.get(risk_field_id)
                risk_probability = self._normalize_risk_value(risk_value, issue_key)
            if risk_probability is None and confidence_field_id:
                conf_value = fields.get(confidence_field_id)
                risk_probability = self._normalize_confidence_value(conf_value, issue_key)

            return {
                'key': issue_key,
                'summary': fields.get('summary', 'No summary'),
                'assignee': assignee_name,
                'status': status_name,
                'project_key': project_key,
                'risk_probability': risk_probability
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch details for {issue_key}: {str(e)}")
            return None
    
    def _normalize_risk_value(self, risk_value: Union[int, str, dict, list, Any], issue_key: str) -> Optional[int]:
        """Normalize risk value to 1-5 scale."""
        if not risk_value:
            return None
        
        # Handle different data types
        processed_value = risk_value
        if isinstance(risk_value, dict):
            processed_value = risk_value.get('value')
        elif isinstance(risk_value, list) and risk_value:
            processed_value = risk_value[0].get('value') if isinstance(risk_value[0], dict) else risk_value[0]
        
        if not processed_value:
            return None
        
        risk_str = str(processed_value).lower()
        
        # Skip user ID fields
        if '(' in risk_str and ')' in risk_str:
            return None
        
        # Map text values to numeric scale
        if 'green' in risk_str or 'no risk' in risk_str or 'committed' in risk_str:
            return 1
        elif 'yellow' in risk_str or 'medium' in risk_str:
            return 3
        elif 'red' in risk_str or 'high risk' in risk_str or "can't deliver" in risk_str:
            return 5
        elif 'none' in risk_str or 'undefined' in risk_str:
            return None
        
        # Try numeric format
        try:
            if isinstance(processed_value, (int, float)):
                numeric_value = int(processed_value)
                if 1 <= numeric_value <= 5:
                    return numeric_value
            elif isinstance(processed_value, str):
                numeric_value = int(processed_value)
                if 1 <= numeric_value <= 5:
                    return numeric_value
        except (ValueError, TypeError):
            pass
        
        return None

    def _normalize_confidence_value(self, conf_value: Any, issue_key: str) -> Optional[int]:
        """
        Map «Confidence Level» field values to the numeric risk scale.

        Mapping (PI planning practice):
            Committed → 1  (green  — fully committed delivery)
            Tentative → 3  (orange — tentative / at risk)
            Out       → 5  (red    — will NOT be delivered this PI)
            Added     → 6  (purple — new topic added during PI)
            None      → None (no PI assessment yet)
        """
        if not conf_value:
            return None
        if isinstance(conf_value, dict):
            raw = conf_value.get('value') or conf_value.get('name', '')
        elif isinstance(conf_value, list) and conf_value:
            first = conf_value[0]
            raw = first.get('value') if isinstance(first, dict) else str(first)
        else:
            raw = str(conf_value)

        conf_str = (raw or '').strip().lower()
        risk = CONFIDENCE_LEVEL_MAP.get(conf_str)
        if risk is not None:
            logger.debug(f"🎯 Confidence Level '{raw}' → risk {risk} for {issue_key}")
        return risk


# Flask Routes

@blueprint.route('/')
@log_request
def index():
    """Display the main form."""
    return render_template('initiative_form.html')


@blueprint.route('/api/cache_check', methods=['GET'])
def api_cache_check():
    """Return whether a valid cache entry exists for the given params."""
    from flask import jsonify
    jira_url   = request.args.get('jira_url',   '').strip()
    query      = request.args.get('query',      '').strip()
    fix_version = request.args.get('fix_version', '').strip()
    if not all([jira_url, query, fix_version]):
        return jsonify({'has_cache': False, 'age_minutes': None})
    cache_key = f"{jira_url}_{query}_{fix_version}"
    has = cache.is_valid(cache_key, max_age=1800)
    age = None
    if has:
        try:
            items = cache.list_cached()
            match = next((i for i in items if i.get('key') == cache_key), None)
            if match and match.get('timestamp'):
                from datetime import datetime
                ts = datetime.fromisoformat(match['timestamp'])
                age = int((datetime.now() - ts).total_seconds() / 60)
        except Exception:
            pass
    return jsonify({'has_cache': has, 'age_minutes': age})


@blueprint.route('/analyze', methods=['POST'])
@log_request
def analyze():
    """Analyze Jira hierarchy and render results."""
    jira_url = request.form.get('jira_url', '').strip()
    access_token = request.form.get('access_token', '').strip()
    query = request.form.get('query', 'issuetype = "Business Initiative"').strip()
    fix_version = request.form.get('fix_version', '').strip()
    use_cache_form = request.form.get('use_cache') == 'true'
    enable_limit = request.form.get('enable_limit') == 'true'

    # Validate required fields
    if not all([jira_url, access_token, query, fix_version]):
        return render_template('initiative_form.html', error='All fields are required'), 400
    if not jira_url.startswith(('http://', 'https://')):
        return render_template('initiative_form.html', error='Jira URL must start with http:// or https://'), 400

    # Parse limit
    limit_count = None
    if enable_limit:
        try:
            limit_count = int(request.form.get('limit_count', 25))
            if limit_count <= 0:
                limit_count = None
        except (ValueError, TypeError):
            limit_count = 25

    # Check cache if requested
    if use_cache_form:
        cache_key = f"{jira_url}_{query}_{fix_version}"
        if cache.is_valid(cache_key, max_age=1800):
            logger.info("📋 Using cached data")
            cached_data = cache.get(cache_key)
            if cached_data:
                session['analysis_data'] = cache_key
                initiatives = cached_data.get('initiatives', [])
                if limit_count and len(initiatives) > limit_count:
                    initiatives = initiatives[:limit_count]
                all_areas = sorted(set(
                    area
                    for initiative in initiatives
                    for feature in initiative.get('features', [])
                    for sub_feature in feature.get('sub_features', [])
                    for area in sub_feature.get('epics_by_area', {}).keys()
                ))
                # Attach completion stats — no extra Jira queries, derived from cached epics
                for _ini in initiatives:
                    _ini['completion'] = compute_initiative_completion(_ini)
                return render_template(
                    'initiative_hierarchy.html',
                    initiatives=initiatives,
                    fix_version=fix_version,
                    all_areas=all_areas,
                    cached_mode=True,
                    completed_statuses=COMPLETED_STATUSES
                )
        logger.warning("⚠️ No valid cache found, fetching fresh data")

    try:
        logger.info(f"🔍 Fetching hierarchy from Jira: {jira_url}")
        client = JiraClient(jira_url, access_token)

        if not client.test_connection():
            return render_template(
                'initiative_form.html',
                error='Failed to connect to Jira. Check your URL and token.'
            ), 401

        fetcher = JiraHierarchyFetcher(client)
        initiatives = fetcher.fetch_hierarchy(query, fix_version)

        # Apply limit
        is_limited = False
        original_count = len(initiatives)
        if limit_count and original_count > limit_count:
            initiatives = initiatives[:limit_count]
            is_limited = True
            logger.info(f"⚠️ Limited to {limit_count} of {original_count} initiatives")

        # Collect all areas for table headers
        all_areas = sorted(set(
            area
            for initiative in initiatives
            for feature in initiative.get('features', [])
            for sub_feature in feature.get('sub_features', [])
            for area in sub_feature.get('epics_by_area', {}).keys()
        ))

        # Attach completion stats — no extra Jira queries, derived from already-fetched epics.
        # Computed BEFORE cache.save so exports reading from cache also get the stats.
        for _ini in initiatives:
            _ini['completion'] = compute_initiative_completion(_ini)

        # Save to cache
        cache_key = f"{jira_url}_{query}_{fix_version}"
        cache.save(cache_key, {
            'initiatives': initiatives,
            'jira_url': jira_url,
            'query': query,
            'fix_version': fix_version,
            'all_areas': all_areas,
            'is_limited': is_limited,
            'limit_count': limit_count if is_limited else None,
            'original_count': original_count if is_limited else None,
        }, metadata={'jira_url': jira_url, 'fix_version': fix_version})
        session['analysis_data'] = cache_key

        return render_template(
            'initiative_hierarchy.html',
            initiatives=initiatives,
            fix_version=fix_version,
            all_areas=all_areas,
            is_limited=is_limited,
            limit_count=limit_count if is_limited else None,
            original_count=original_count if is_limited else None,
            completed_statuses=COMPLETED_STATUSES
        )

    except Exception as e:
        logger.error(f"🚩 Analysis failed: {str(e)}", exc_info=True)
        return render_template('initiative_form.html', error=str(e)), 500


@blueprint.route('/export_pdf', methods=['GET'])
@log_request
@handle_errors
def export_pdf():
    """Export hierarchy as PDF."""
    cache_key = session.get('analysis_data')
    if not cache_key:
        return "No analysis data found. Please run analysis first.", 400
    
    analysis_data = cache.get(cache_key)
    if not analysis_data:
        return "Analysis data expired. Please run analysis again.", 400
    
    # Filter empty hierarchy
    filtered_initiatives = filter_empty_hierarchy(analysis_data['initiatives'])
    
    # Generate PDF
    pdf_generator = InitiativeViewerPDFGenerator(analysis_data['jira_url'])
    pdf_buffer = io.BytesIO()
    
    pdf_generator.generate_hierarchy_pdf(
        filtered_initiatives,
        pdf_buffer,
        fix_version=analysis_data['fix_version'],
        page_size=PAGE_A4_LANDSCAPE
    )

    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"initiative_hierarchy_{analysis_data['fix_version']}.pdf"
    )


@blueprint.route('/export_pdf_wide', methods=['GET'])
@log_request
@handle_errors
def export_pdf_wide():
    """Export hierarchy as wide/landscape PDF."""
    cache_key = session.get('analysis_data')
    if not cache_key:
        return "No analysis data found. Please run analysis first.", 400

    analysis_data = cache.get(cache_key)
    if not analysis_data:
        return "Analysis data expired. Please run analysis again.", 400

    filtered_initiatives = filter_empty_hierarchy(analysis_data['initiatives'])
    all_areas = analysis_data.get('all_areas') or sorted(set(
        area
        for i in filtered_initiatives
        for f in i.get('features', [])
        for sf in f.get('sub_features', [])
        for area in sf.get('epics_by_area', {}).keys()
    ))

    pdf_generator = InitiativeViewerPDFGenerator(analysis_data['jira_url'])
    pdf_buffer = io.BytesIO()
    pdf_generator.generate_hierarchy_pdf(
        filtered_initiatives,
        pdf_buffer,
        fix_version=analysis_data['fix_version'],
        page_size=PAGE_SUPER_WIDE
    )
    pdf_buffer.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Initiative_Report_{analysis_data['fix_version']}_Wide_{timestamp}.pdf"
    )


@blueprint.route('/export_html', methods=['GET'])
@log_request
def export_html():
    """Export hierarchy as Confluence-ready HTML file."""
    cache_key = session.get('analysis_data')
    if not cache_key:
        return "No analysis data found. Please run analysis first.", 400

    analysis_data = cache.get(cache_key)
    if not analysis_data:
        return "Analysis data expired. Please run analysis again.", 400

    filtered_initiatives = filter_empty_hierarchy(analysis_data['initiatives'])
    all_areas = analysis_data.get('all_areas') or sorted(set(
        area
        for i in filtered_initiatives
        for f in i.get('features', [])
        for sf in f.get('sub_features', [])
        for area in sf.get('epics_by_area', {}).keys()
    ))
    initiatives_with_features = sum(1 for init in filtered_initiatives if init.get('features'))

    html_content = render_template(
        'export_confluence.html',
        initiatives=filtered_initiatives,
        fix_version=analysis_data['fix_version'],
        all_areas=all_areas,
        query=analysis_data.get('query', ''),
        initiatives_with_features=initiatives_with_features,
        generated_date=datetime.now().strftime('%B %d, %Y at %H:%M'),
        year=datetime.now().year,
        is_limited=analysis_data.get('is_limited', False),
        limit_count=analysis_data.get('limit_count'),
        original_count=analysis_data.get('original_count'),
        completed_statuses=COMPLETED_STATUSES
    )
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        io.BytesIO(html_content.encode('utf-8')),
        mimetype='text/html',
        as_attachment=True,
        download_name=f"Initiative_Report_{analysis_data['fix_version']}_{timestamp}.html"
    )


@blueprint.route('/export_confluence', methods=['GET'])
@log_request
def export_confluence():
    """Export hierarchy as Confluence Wiki Markup text file."""
    cache_key = session.get('analysis_data')
    if not cache_key:
        return "No analysis data found. Please run analysis first.", 400

    analysis_data = cache.get(cache_key)
    if not analysis_data:
        return "Analysis data expired. Please run analysis again.", 400

    filtered_initiatives = filter_empty_hierarchy(analysis_data['initiatives'])
    all_areas = analysis_data.get('all_areas') or sorted(set(
        area
        for i in filtered_initiatives
        for f in i.get('features', [])
        for sf in f.get('sub_features', [])
        for area in sf.get('epics_by_area', {}).keys()
    ))
    fix_version = analysis_data['fix_version']
    jira_url = analysis_data.get('jira_url', 'https://jira')
    query = analysis_data.get('query', '')

    base_url = "https://confluence.worldline-solutions.com/download/thumbnails/2627092118"

    wiki_lines = []
    wiki_lines.append(f"h1. Initiative Report - {fix_version}")
    wiki_lines.append("")
    wiki_lines.append(f"*Generated:* {datetime.now().strftime('%B %d, %Y at %H:%M')}")
    if query:
        wiki_lines.append(f"*Query:* {query}")
    wiki_lines.append("")
    wiki_lines.append("----")
    wiki_lines.append("")

    for initiative in filtered_initiatives:
        init_key = initiative.get('key', 'Unknown')
        init_summary = initiative.get('summary', '')
        init_cpo = initiative.get('assignee', 'Unknown')
        comp = initiative.get('completion') or compute_initiative_completion(initiative)
        comp_suffix = f" | {comp['done']}/{comp['total']} done ({comp['pct']}%)" if comp.get('total', 0) > 0 else ""
        wiki_lines.append(f"h2. [{init_key}|{jira_url}/browse/{init_key}] {init_summary}{comp_suffix} | 👤 CPO: {init_cpo}")
        wiki_lines.append("")

        # Table header — Feature | Sub-Feature | area1 | area2 ...
        header = "|| Feature || Sub-Feature ||"
        for area in all_areas:
            header += f" {area} ||"
        wiki_lines.append(header)

        for feature in initiative.get('features', []):
            fk = feature.get('key', '')
            fs = '*' + feature.get('summary', '').replace('|', '/').strip() + '*'
            fs_short = fs[:60] + '...' if len(fs) > 60 else fs

            for sub_feature in feature.get('sub_features', []):
                sfk = sub_feature.get('key', '')
                sfs = '*' + sub_feature.get('summary', '').replace('|', '/').strip() + '*'
                sfs_short = sfs[:60] + '...' if len(sfs) > 60 else sfs
                epics_by_area = sub_feature.get('epics_by_area', {})
                max_epics = max((len(v) for v in epics_by_area.values()), default=0)

                for idx in range(max(max_epics, 1)):
                    if idx == 0:
                        row = f"| [{fk}|{jira_url}/browse/{fk}] _{fs_short}_ | [{sfk}|{jira_url}/browse/{sfk}] _{sfs_short}_ |"
                    else:
                        row = "| | |"

                    for area in all_areas:
                        epics = epics_by_area.get(area, [])
                        if idx < len(epics):
                            epic = epics[idx]
                            ek = epic.get('key', '')
                            es = epic.get('summary', '').replace('|', '/').strip()
                            es_short = es[:50] + '...' if len(es) > 50 else es
                            estatus = epic.get('status', '').replace('|', '/').strip()
                            eassignee = epic.get('assignee', '').replace('|', '/').strip() or 'Unassigned'
                            risk = epic.get('risk_probability', None)
                            is_completed = estatus.lower() in COMPLETED_STATUSES

                            # Pick Confluence-hosted risk icon
                            if is_completed:
                                risk_icon = f"!{base_url}/Green.jpg!"
                            elif risk == 1:
                                risk_icon = f"!{base_url}/GreenLowRisk.jpg!"
                            elif risk == 2:
                                risk_icon = f"!{base_url}/Yellow.jpg!"
                            elif risk == 3:
                                risk_icon = f"!{base_url}/Orange.jpg!"
                            elif risk == 4:
                                risk_icon = f"!{base_url}/DarkOrange.png!"
                            elif risk == 5:
                                risk_icon = f"!{base_url}/Red.jpg!"
                            elif risk == 6:
                                risk_icon = f"!{base_url}/purple.jpg!"
                            else:
                                risk_icon = f"!{base_url}/unknown.jpg!"

                            meta = f"{{color:#718096}}(\U0001f464 {eassignee} / Status: {estatus}){{color}}"

                            if is_completed:
                                epic_info = f"{risk_icon} -[{ek}|{jira_url}/browse/{ek}]- _{es_short}_ {meta}"
                            else:
                                epic_info = f"{risk_icon} [{ek}|{jira_url}/browse/{ek}] _{es_short}_ {meta}"

                            row += f" {epic_info} |"
                        else:
                            row += " |"
                    wiki_lines.append(row)

        wiki_lines.append("")

    # Legend footer
    wiki_lines.append("----")
    wiki_lines.append("")
    wiki_lines.append("h3. Legend")
    wiki_lines.append(f" !{base_url}/Green.jpg! {'{color:green}'}Done / Resolved (Completed){'{color}'}")
    wiki_lines.append(f" !{base_url}/GreenLowRisk.jpg! Risk 1 - Low Risk - Committed")
    wiki_lines.append(f" !{base_url}/Yellow.jpg! Risk 2 - Low-Medium")
    wiki_lines.append(f" !{base_url}/Orange.jpg! Risk 3 - Medium")
    wiki_lines.append(f" !{base_url}/DarkOrange.png! Risk 4 - Medium-High")
    wiki_lines.append(f" !{base_url}/Red.jpg! Risk 5 - High Risk - *Out* (not deliverable this PI)")
    wiki_lines.append(f" !{base_url}/purple.jpg! Risk 6 - *Added* (new topic added during PI \u2014 purple)")
    wiki_lines.append(f" !{base_url}/unknown.jpg! Risk not set - *Unknown - None*")
    wiki_lines.append("* -Strikethrough- = *Completed/Done/Closed*")
    wiki_lines.append("")
    wiki_lines.append("h4. Generated with JiraAnalyzerSuite's Initiative Viewer app. For feedback or issues, contact Pietro Maffi.")

    wiki_text = "\n".join(wiki_lines)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        io.BytesIO(wiki_text.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f"Initiative_Report_Wiki_{fix_version}_{timestamp}.txt"
    )


@blueprint.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'app': 'initiative_viewer',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })


# Blueprint is registered in unified_dashboard - no standalone execution
