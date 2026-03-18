"""
Cache Manager - Shared Module
File-based caching system for Jira data to reduce API calls.

Provides persistent caching with configurable TTL and automatic cleanup.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pickle

logger = logging.getLogger('CacheManager')

# Default settings
DEFAULT_CACHE_DIR = './cache'
DEFAULT_TTL_MINUTES = 30
MAX_CACHE_AGE_DAYS = 7


class CacheManager:
    """
    File-based cache manager for Jira data.
    
    Provides persistent caching with TTL, automatic cleanup, and
    support for both JSON and binary data formats.
    
    Example:
        >>> cache = CacheManager()
        >>> cache.save('my_data', issues, metadata={'jql': 'project = PROJ'})
        >>> if cache.is_valid('my_data', max_age=3600):
        ...     issues = cache.get('my_data')
    """
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR, ttl_minutes: int = DEFAULT_TTL_MINUTES):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_minutes: Default time-to-live for cache entries in minutes
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_age = timedelta(days=MAX_CACHE_AGE_DAYS)
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🗄️ CacheManager initialized: dir={cache_dir}, ttl={ttl_minutes}min")
        
        # Clean up old cache files on initialization
        self._cleanup_old_files()
    
    def _generate_cache_key(self, key: str) -> str:
        """
        Generate a safe filename from cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Safe filename
        """
        # Use hash for long keys
        if len(key) > 50:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            return f"cache_{key_hash}"
        
        # Sanitize key for filename
        safe_key = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in key)
        return f"cache_{safe_key}"
    
    def _get_cache_path(self, key: str) -> Path:
        """Get full path for cache file."""
        filename = self._generate_cache_key(key)
        return self.cache_dir / f"{filename}.pkl"
    
    def _get_metadata_path(self, key: str) -> Path:
        """Get path for cache metadata file."""
        filename = self._generate_cache_key(key)
        return self.cache_dir / f"{filename}_meta.json"
    
    def save(self, key: str, data: Any, metadata: Optional[Dict] = None) -> bool:
        """
        Save data to cache.
        
        Args:
            key: Cache key
            data: Data to cache (must be picklable)
            metadata: Optional metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(key)
            
            # Save data using pickle
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Save metadata
            meta_data = {
                'key': key,
                'timestamp': datetime.now().isoformat(),
                'size': cache_path.stat().st_size,
                'metadata': metadata or {}
            }
            
            # Add data stats if it's a list
            if isinstance(data, list):
                meta_data['count'] = len(data)
            
            with open(meta_path, 'w') as f:
                json.dump(meta_data, f, indent=2)
            
            logger.info(f"💾 Cached data for key '{key}' ({meta_data.get('size', 0)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"🚩 Failed to save cache for '{key}': {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        try:
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                logger.debug(f"❌ Cache MISS for key '{key}'")
                return None
            
            # Load data
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            logger.info(f"📋 Cache HIT for key '{key}'")
            return data
            
        except Exception as e:
            logger.error(f"🚩 Failed to load cache for '{key}': {str(e)}")
            return None
    
    def get_metadata(self, key: str) -> Optional[Dict]:
        """
        Get metadata for cached item.
        
        Args:
            key: Cache key
            
        Returns:
            Metadata dictionary or None
        """
        try:
            meta_path = self._get_metadata_path(key)
            
            if not meta_path.exists():
                return None
            
            with open(meta_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"🚩 Failed to load metadata for '{key}': {str(e)}")
            return None
    
    def is_valid(self, key: str, max_age: Optional[int] = None) -> bool:
        """
        Check if cached data is valid (exists and not expired).
        
        Args:
            key: Cache key
            max_age: Maximum age in seconds (uses default TTL if None)
            
        Returns:
            True if cache is valid, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                return False
            
            # Get file modification time
            mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            age = datetime.now() - mod_time
            
            # Check against TTL or custom max_age
            if max_age is not None:
                max_age_delta = timedelta(seconds=max_age)
            else:
                max_age_delta = self.ttl
            
            is_valid = age < max_age_delta
            
            if not is_valid:
                logger.debug(f"⏰ Cache EXPIRED for key '{key}' (age: {age})")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"🚩 Failed to check cache validity for '{key}': {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete cached data.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(key)
            
            deleted = False
            
            if cache_path.exists():
                cache_path.unlink()
                deleted = True
            
            if meta_path.exists():
                meta_path.unlink()
            
            if deleted:
                logger.info(f"🗑️ Deleted cache for key '{key}'")
            
            return deleted
            
        except Exception as e:
            logger.error(f"🚩 Failed to delete cache for '{key}': {str(e)}")
            return False
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache files.
        
        Args:
            pattern: Optional pattern to match (clears all if None)
            
        Returns:
            Number of files deleted
        """
        try:
            count = 0
            
            if pattern:
                # Clear matching files
                for cache_file in self.cache_dir.glob(f"cache_{pattern}*.pkl"):
                    cache_file.unlink()
                    # Also delete metadata
                    meta_file = cache_file.with_suffix('.json')
                    if meta_file.exists():
                        meta_file.unlink()
                    count += 1
            else:
                # Clear all cache files
                for cache_file in self.cache_dir.glob("cache_*.pkl"):
                    cache_file.unlink()
                    count += 1
                for meta_file in self.cache_dir.glob("cache_*_meta.json"):
                    meta_file.unlink()
            
            logger.info(f"🗑️ Cleared {count} cache file(s)")
            return count
            
        except Exception as e:
            logger.error(f"🚩 Failed to clear cache: {str(e)}")
            return 0
    
    def list_cached(self) -> List[Dict]:
        """
        List all cached items with metadata.
        
        Returns:
            List of cache metadata dictionaries
        """
        cached_items = []
        
        try:
            for meta_file in self.cache_dir.glob("cache_*_meta.json"):
                try:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                        
                        # Add age information
                        timestamp = datetime.fromisoformat(meta['timestamp'])
                        age = datetime.now() - timestamp
                        meta['age_seconds'] = age.total_seconds()
                        meta['is_valid'] = age < self.ttl
                        
                        cached_items.append(meta)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to read metadata file {meta_file}: {str(e)}")
            
            return cached_items
            
        except Exception as e:
            logger.error(f"🚩 Failed to list cached items: {str(e)}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cached_items = self.list_cached()
            
            total_size = sum(item.get('size', 0) for item in cached_items)
            valid_count = sum(1 for item in cached_items if item.get('is_valid', False))
            expired_count = len(cached_items) - valid_count
            
            return {
                'total_items': len(cached_items),
                'valid_items': valid_count,
                'expired_items': expired_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_dir': str(self.cache_dir),
                'ttl_minutes': self.ttl.total_seconds() / 60
            }
            
        except Exception as e:
            logger.error(f"🚩 Failed to get cache stats: {str(e)}")
            return {}
    
    def _cleanup_old_files(self):
        """Remove cache files older than max_age."""
        try:
            count = 0
            cutoff_time = datetime.now() - self.max_age
            
            for cache_file in self.cache_dir.glob("cache_*.pkl"):
                mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                
                if mod_time < cutoff_time:
                    cache_file.unlink()
                    
                    # Also delete metadata
                    meta_file = cache_file.with_name(cache_file.stem + '_meta.json')
                    if meta_file.exists():
                        meta_file.unlink()
                    
                    count += 1
            
            if count > 0:
                logger.info(f"🧹 Cleaned up {count} old cache file(s)")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to cleanup old cache files: {str(e)}")


# Convenience functions for simple use cases
_default_cache = None

def get_default_cache() -> CacheManager:
    """Get or create default cache manager instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = CacheManager()
    return _default_cache


def cache_data(key: str, data: Any, metadata: Optional[Dict] = None) -> bool:
    """Save data to default cache."""
    return get_default_cache().save(key, data, metadata)


def get_cached_data(key: str) -> Optional[Any]:
    """Get data from default cache."""
    return get_default_cache().get(key)


def is_cache_valid(key: str, max_age: Optional[int] = None) -> bool:
    """Check if default cache is valid."""
    return get_default_cache().is_valid(key, max_age)
