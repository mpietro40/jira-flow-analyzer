"""
File Storage - Shared Module
File storage and management utilities for PerseusLeadTime applications.

Provides safe file operations with proper error handling.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger('FileStorage')

# Default storage directory
DEFAULT_STORAGE_DIR = './storage'


class FileStorage:
    """
    File storage manager with safe operations and error handling.
    
    Provides utilities for saving, loading, and managing files
    with automatic directory creation and cleanup.
    
    Example:
        >>> storage = FileStorage('./my_storage')
        >>> storage.save('reports/my_report.pdf', pdf_data)
        >>> data = storage.load('reports/my_report.pdf')
        >>> files = storage.list_files('reports/', pattern='*.pdf')
    """
    
    def __init__(self, base_path: str = DEFAULT_STORAGE_DIR):
        """
        Initialize file storage.
        
        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 FileStorage initialized: {base_path}")
    
    def _get_full_path(self, relative_path: str) -> Path:
        """
        Get full path from relative path, ensuring it's within base_path.
        
        Args:
            relative_path: Relative file path
            
        Returns:
            Full path
            
        Raises:
            ValueError: If path tries to escape base directory
        """
        full_path = (self.base_path / relative_path).resolve()
        
        # Security check: ensure path is within base_path
        try:
            full_path.relative_to(self.base_path.resolve())
        except ValueError:
            raise ValueError(f"Path '{relative_path}' tries to escape base directory")
        
        return full_path
    
    def save(self, relative_path: str, data: Union[bytes, str, bytearray], 
             encoding: str = 'utf-8', binary: bool = False) -> bool:
        """
        Save data to file.
        
        Args:
            relative_path: Relative path to file
            data: Data to save (bytes or str)
            encoding: Text encoding (for string data)
            binary: Force binary mode
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_full_path(relative_path)
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            if binary or isinstance(data, (bytes, bytearray)):
                data_bytes = data if isinstance(data, bytes) else bytes(data) if isinstance(data, bytearray) else data.encode(encoding)
                with open(file_path, 'wb') as f:
                    f.write(data_bytes)
            else:
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(str(data))
            
            logger.info(f"💾 Saved file: {relative_path} ({file_path.stat().st_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"🚩 Failed to save file '{relative_path}': {str(e)}")
            return False
    
    def save_json(self, relative_path: str, data: Any, indent: int = 2) -> bool:
        """
        Save data as JSON file.
        
        Args:
            relative_path: Relative path to file
            data: Data to save (must be JSON-serializable)
            indent: JSON indentation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            json_str = json.dumps(data, indent=indent, default=str)
            return self.save(relative_path, json_str)
        except Exception as e:
            logger.error(f"🚩 Failed to save JSON '{relative_path}': {str(e)}")
            return False
    
    def load(self, relative_path: str, binary: bool = False, 
             encoding: str = 'utf-8') -> Optional[Union[bytes, str]]:
        """
        Load data from file.
        
        Args:
            relative_path: Relative path to file
            binary: Load in binary mode
            encoding: Text encoding (for text mode)
            
        Returns:
            File content or None if error
        """
        try:
            file_path = self._get_full_path(relative_path)
            
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {relative_path}")
                return None
            
            # Load file
            if binary:
                with open(file_path, 'rb') as f:
                    return f.read()
            else:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            
        except Exception as e:
            logger.error(f"🚩 Failed to load file '{relative_path}': {str(e)}")
            return None
    
    def load_json(self, relative_path: str) -> Optional[Any]:
        """
        Load data from JSON file.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            Parsed JSON data or None if error
        """
        try:
            content = self.load(relative_path)
            if content is None:
                return None
            return json.loads(content)
        except Exception as e:
            logger.error(f"🚩 Failed to load JSON '{relative_path}': {str(e)}")
            return None
    
    def exists(self, relative_path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            file_path = self._get_full_path(relative_path)
            return file_path.exists()
        except Exception as e:
            logger.error(f"🚩 Error checking file existence '{relative_path}': {str(e)}")
            return False
    
    def delete(self, relative_path: str) -> bool:
        """
        Delete file.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_full_path(relative_path)
            
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                    logger.info(f"🗑️ Deleted file: {relative_path}")
                    return True
                else:
                    logger.warning(f"⚠️ Not a file: {relative_path}")
                    return False
            else:
                logger.warning(f"⚠️ File not found: {relative_path}")
                return False
                
        except Exception as e:
            logger.error(f"🚩 Failed to delete file '{relative_path}': {str(e)}")
            return False
    
    def list_files(self, directory: str = '', pattern: str = '*', 
                   recursive: bool = False) -> List[str]:
        """
        List files in directory.
        
        Args:
            directory: Relative directory path (empty for root)
            pattern: File pattern (e.g., '*.pdf', '*.json')
            recursive: Search recursively
            
        Returns:
            List of relative file paths
        """
        try:
            dir_path = self._get_full_path(directory) if directory else self.base_path
            
            if not dir_path.exists():
                logger.warning(f"⚠️ Directory not found: {directory}")
                return []
            
            # Get files
            if recursive:
                file_paths = dir_path.rglob(pattern)
            else:
                file_paths = dir_path.glob(pattern)
            
            # Convert to relative paths
            files = []
            for file_path in file_paths:
                if file_path.is_file():
                    rel_path = file_path.relative_to(self.base_path)
                    files.append(str(rel_path))
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"🚩 Failed to list files in '{directory}': {str(e)}")
            return []
    
    def get_file_info(self, relative_path: str) -> Optional[Dict]:
        """
        Get file information.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            Dictionary with file info or None
        """
        try:
            file_path = self._get_full_path(relative_path)
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            return {
                'path': relative_path,
                'name': file_path.name,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir()
            }
            
        except Exception as e:
            logger.error(f"🚩 Failed to get file info '{relative_path}': {str(e)}")
            return None
    
    def copy_file(self, source: str, destination: str) -> bool:
        """
        Copy file within storage.
        
        Args:
            source: Source relative path
            destination: Destination relative path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            src_path = self._get_full_path(source)
            dst_path = self._get_full_path(destination)
            
            if not src_path.exists():
                logger.warning(f"⚠️ Source file not found: {source}")
                return False
            
            # Create destination directory
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(src_path, dst_path)
            logger.info(f"📋 Copied file: {source} → {destination}")
            return True
            
        except Exception as e:
            logger.error(f"🚩 Failed to copy file '{source}' → '{destination}': {str(e)}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """
        Move file within storage.
        
        Args:
            source: Source relative path
            destination: Destination relative path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            src_path = self._get_full_path(source)
            dst_path = self._get_full_path(destination)
            
            if not src_path.exists():
                logger.warning(f"⚠️ Source file not found: {source}")
                return False
            
            # Create destination directory
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(src_path), str(dst_path))
            logger.info(f"📦 Moved file: {source} → {destination}")
            return True
            
        except Exception as e:
            logger.error(f"🚩 Failed to move file '{source}' → '{destination}': {str(e)}")
            return False
    
    def create_directory(self, relative_path: str) -> bool:
        """
        Create directory (and parents if needed).
        
        Args:
            relative_path: Relative directory path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dir_path = self._get_full_path(relative_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created directory: {relative_path}")
            return True
        except Exception as e:
            logger.error(f"🚩 Failed to create directory '{relative_path}': {str(e)}")
            return False
    
    def delete_directory(self, relative_path: str, recursive: bool = False) -> bool:
        """
        Delete directory.
        
        Args:
            relative_path: Relative directory path
            recursive: Delete recursively (including contents)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dir_path = self._get_full_path(relative_path)
            
            if not dir_path.exists():
                logger.warning(f"⚠️ Directory not found: {relative_path}")
                return False
            
            if not dir_path.is_dir():
                logger.warning(f"⚠️ Not a directory: {relative_path}")
                return False
            
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()  # Only works if empty
            
            logger.info(f"🗑️ Deleted directory: {relative_path}")
            return True
            
        except Exception as e:
            logger.error(f"🚩 Failed to delete directory '{relative_path}': {str(e)}")
            return False
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for item in self.base_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
                elif item.is_dir():
                    dir_count += 1
            
            return {
                'base_path': str(self.base_path),
                'total_files': file_count,
                'total_directories': dir_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 3)
            }
            
        except Exception as e:
            logger.error(f"🚩 Failed to get storage stats: {str(e)}")
            return {}


# Convenience functions for default storage
_default_storage = None

def get_default_storage() -> FileStorage:
    """Get or create default storage manager instance."""
    global _default_storage
    if _default_storage is None:
        _default_storage = FileStorage()
    return _default_storage


def save_file(path: str, data: Union[bytes, str], **kwargs) -> bool:
    """Save file to default storage."""
    return get_default_storage().save(path, data, **kwargs)


def load_file(path: str, **kwargs) -> Optional[Union[bytes, str]]:
    """Load file from default storage."""
    return get_default_storage().load(path, **kwargs)


def file_exists(path: str) -> bool:
    """Check if file exists in default storage."""
    return get_default_storage().exists(path)
