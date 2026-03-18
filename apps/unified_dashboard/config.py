"""
Application URLs Configuration

Maps application names to their service URLs for the unified dashboard.
"""

# Application service URLs (local development)
APPS = {
    'lead_time_analyzer': {
        'name': 'Lead Time Analyzer',
        'description': 'Flow metrics, cycle times, and lead time analysis',
        'url': 'http://localhost:5001',
        'port': 5001,
        'icon': 'fa-clock',
        'color': '#4169e1'
    },
    'initiative_viewer': {
        'name': 'Initiative Viewer',
        'description': '4-level hierarchical initiative visualization',
        'url': 'http://localhost:5011',
        'port': 5011,
        'icon': 'fa-sitemap',
        'color': '#667eea'
    },
    'epic_report': {
        'name': 'Epic Report',
        'description': 'Parent epic discovery and child count analysis',
        'url': 'http://localhost:5002',
        'port': 5002,
        'icon': 'fa-scroll',
        'color': '#764ba2'
    },
    'pi_analyzer': {
        'name': 'PI Analyzer',
        'description': 'Program Increment planning and capacity analysis',
        'url': 'http://localhost:5003',
        'port': 5003,
        'icon': 'fa-calendar-alt',
        'color': '#f093fb'
    },
    'sprint_analyzer': {
        'name': 'Sprint Analyzer',
        'description': 'Sprint capacity and velocity forecasting',
        'url': 'http://localhost:5004',
        'port': 5004,
        'icon': 'fa-running',
        'color': '#f5576c'
    },
    'pbc_analyzer': {
        'name': 'PBC Analyzer',
        'description': 'Process Behavior Charts for lead time trends',
        'url': 'http://localhost:5005',
        'port': 5005,
        'icon': 'fa-chart-line',
        'color': '#4facfe'
    },
    'duplicate_detector': {
        'name': 'Duplicate Detector',
        'description': 'Find duplicate issues with similarity analysis',
        'url': 'http://localhost:5006',
        'port': 5006,
        'icon': 'fa-copy',
        'color': '#00f2fe'
    },
    'psychological_safety': {
        'name': 'Psychological Safety',
        'description': 'Team psychological safety metrics and trends',
        'url': 'http://localhost:5007',
        'port': 5007,
        'icon': 'fa-heart',
        'color': '#43e97b'
    },
    'epic_fixversion': {
        'name': 'Epic Fix Version',
        'description': 'Epic distribution by fix version across initiatives',
        'url': 'http://localhost:5008',
        'port': 5008,
        'icon': 'fa-code-branch',
        'color': '#38f9d7'
    }
}

# Health check timeout (seconds)
HEALTH_CHECK_TIMEOUT = 2
