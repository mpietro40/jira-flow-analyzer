"""
PI Analyzer Cache
Provides caching functionality for PI analyzer to avoid redundant Jira queries.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger('PICache')

class PICache:
    """
    In-memory cache for PI analyzer data to avoid redundant Jira queries.
    """
    
    def __init__(self, cache_ttl_minutes: int = 30):
        """
        Initialize cache with TTL.
        
        Args:
            cache_ttl_minutes (int): Cache time-to-live in minutes
        """
        self.cache = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        logger.info(f"🗄️ Initialized PI cache with {cache_ttl_minutes}min TTL")
    
    def _generate_cache_key(self, jql_query: str, max_results: int = 5000) -> str:
        """
        Generate cache key from JQL query and parameters.
        
        Args:
            jql_query (str): JQL query string
            max_results (int): Maximum results
            
        Returns:
            str: Cache key
        """
        cache_data = f"{jql_query}|{max_results}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def get_cached_issues(self, jql_query: str, max_results: int = 5000) -> Optional[List[Dict]]:
        """
        Get cached issues if available and not expired.
        
        Args:
            jql_query (str): JQL query string
            max_results (int): Maximum results
            
        Returns:
            Optional[List[Dict]]: Cached issues or None if not found/expired
        """
        cache_key = self._generate_cache_key(jql_query, max_results)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = cached_data['timestamp']
            
            # Check if cache is still valid
            if datetime.now() - cache_time < self.cache_ttl:
                logger.info(f"📋 Cache HIT for query (cached {len(cached_data['issues'])} issues)")
                return cached_data['issues']
            else:
                # Remove expired cache
                del self.cache[cache_key]
                logger.info(f"⏰ Cache EXPIRED for query")
        
        logger.info(f"❌ Cache MISS for query")
        return None
    
    def cache_issues(self, jql_query: str, issues: List[Dict], max_results: int = 5000):
        """
        Cache issues for future use.
        
        Args:
            jql_query (str): JQL query string
            issues (List[Dict]): Issues to cache
            max_results (int): Maximum results
        """
        cache_key = self._generate_cache_key(jql_query, max_results)
        
        self.cache[cache_key] = {
            'issues': issues,
            'timestamp': datetime.now(),
            'count': len(issues)
        }
        
        logger.info(f"💾 Cached {len(issues)} issues for future use")
    
    def clear_cache(self):
        """Clear all cached data."""
        cache_count = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️ Cleared {cache_count} cached queries")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics
        """
        total_entries = len(self.cache)
        total_issues = sum(entry['count'] for entry in self.cache.values())
        
        return {
            'total_entries': total_entries,
            'total_cached_issues': total_issues,
            'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60
        }