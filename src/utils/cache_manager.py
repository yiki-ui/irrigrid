#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cache Manager
Handles application cache, temporary files, and cleanup
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta


class CacheManager:
    """Manages application cache and temporary files"""
    
    def __init__(self):
        """Initialize cache manager"""
        self.cache_dir = Path(tempfile.gettempdir()) / "irrigation_dss_cache"
        self.autosave_dir = Path(tempfile.gettempdir()) / "irrigation_dss_autosave"
        self.gis_cache_dir = self.cache_dir / "gis_tiles"
        self.ai_cache_dir = self.cache_dir / "ai_responses"
        self.icon_cache_dir = Path.home() / "AppData" / "Local" / "IconCache.db"
        
        # Create cache directories
        self._ensure_cache_dirs()
    
    def _ensure_cache_dirs(self):
        """Create cache directories if they don't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.autosave_dir.mkdir(parents=True, exist_ok=True)
        self.gis_cache_dir.mkdir(parents=True, exist_ok=True)
        self.ai_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_size(self) -> Dict[str, int]:
        """
        Get cache size for each category
        
        Returns:
            Dictionary with cache sizes in bytes
        """
        def get_dir_size(path: Path) -> int:
            """Calculate directory size recursively"""
            if not path.exists():
                return 0
            
            total = 0
            try:
                for item in path.rglob('*'):
                    if item.is_file():
                        total += item.stat().st_size
            except (PermissionError, OSError):
                pass
            return total
        
        return {
            'total': get_dir_size(self.cache_dir),
            'autosave': get_dir_size(self.autosave_dir),
            'gis_tiles': get_dir_size(self.gis_cache_dir),
            'ai_responses': get_dir_size(self.ai_cache_dir)
        }
    
    def format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
    
    def clear_all_cache(self) -> Dict[str, bool]:
        """
        Clear all application cache
        
        Returns:
            Dictionary with success status for each category
        """
        results = {
            'general': self.clear_general_cache(),
            'gis': self.clear_gis_cache(),
            'ai': self.clear_ai_cache(),
            'autosave': self.clear_autosave_cache()
        }
        return results
    
    def clear_general_cache(self) -> bool:
        """Clear general application cache"""
        try:
            if self.cache_dir.exists():
                # Remove all files except subdirectories
                for item in self.cache_dir.iterdir():
                    if item.is_file():
                        item.unlink()
            return True
        except Exception as e:
            print(f"Error clearing general cache: {e}")
            return False
    
    def clear_gis_cache(self) -> bool:
        """Clear GIS map tiles cache"""
        try:
            if self.gis_cache_dir.exists():
                shutil.rmtree(self.gis_cache_dir)
                self.gis_cache_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error clearing GIS cache: {e}")
            return False
    
    def clear_ai_cache(self) -> bool:
        """Clear AI responses cache"""
        try:
            if self.ai_cache_dir.exists():
                shutil.rmtree(self.ai_cache_dir)
                self.ai_cache_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error clearing AI cache: {e}")
            return False
    
    def clear_autosave_cache(self, keep_latest: bool = True) -> bool:
        """
        Clear autosave files
        
        Args:
            keep_latest: If True, keeps the most recent autosave
            
        Returns:
            Success status
        """
        try:
            if not self.autosave_dir.exists():
                return True
            
            autosave_files = list(self.autosave_dir.glob("*_autosave.json"))
            
            if keep_latest and autosave_files:
                # Sort by modification time, newest first
                autosave_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                # Keep the first one, delete the rest
                for file in autosave_files[1:]:
                    file.unlink()
            else:
                # Delete all
                for file in autosave_files:
                    file.unlink()
            
            return True
        except Exception as e:
            print(f"Error clearing autosave cache: {e}")
            return False
    
    def clear_icon_cache(self) -> bool:
        """
        Clear Windows icon cache
        
        Note: This requires restarting Windows Explorer
        """
        try:
            import subprocess
            
            # Delete IconCache.db
            icon_cache_path = Path.home() / "AppData" / "Local" / "IconCache.db"
            if icon_cache_path.exists():
                try:
                    icon_cache_path.unlink()
                except PermissionError:
                    # File might be in use
                    pass
            
            # Delete icon cache database files
            explorer_cache = Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Explorer"
            if explorer_cache.exists():
                for file in explorer_cache.glob("iconcache_*.db"):
                    try:
                        file.unlink()
                    except PermissionError:
                        pass
            
            # Refresh icon cache (requires Explorer restart)
            try:
                subprocess.run(['ie4uinit.exe', '-show'], capture_output=True, timeout=5)
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Error clearing icon cache: {e}")
            return False
    
    def cleanup_old_files(self, days: int = 7) -> Dict[str, int]:
        """
        Delete files older than specified days
        
        Args:
            days: Delete files older than this
            
        Returns:
            Dictionary with count of deleted files per category
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted = {'cache': 0, 'autosave': 0, 'gis': 0, 'ai': 0}
        
        def delete_old_files_in_dir(directory: Path, category: str):
            """Delete old files in a directory"""
            if not directory.exists():
                return
            
            try:
                for file in directory.rglob('*'):
                    if file.is_file() and file.stat().st_mtime < cutoff_time:
                        file.unlink()
                        deleted[category] += 1
            except (PermissionError, OSError):
                pass
        
        # Clean each directory
        delete_old_files_in_dir(self.cache_dir, 'cache')
        delete_old_files_in_dir(self.autosave_dir, 'autosave')
        delete_old_files_in_dir(self.gis_cache_dir, 'gis')
        delete_old_files_in_dir(self.ai_cache_dir, 'ai')
        
        return deleted
    
    def get_autosave_files(self) -> List[Dict]:
        """
        Get list of autosave files
        
        Returns:
            List of dictionaries with file info
        """
        if not self.autosave_dir.exists():
            return []
        
        files = []
        for file in self.autosave_dir.glob("*_autosave.json"):
            stat = file.stat()
            files.append({
                'path': str(file),
                'name': file.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'age_minutes': (datetime.now().timestamp() - stat.st_mtime) / 60
            })
        
        # Sort by modification time, newest first
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files
    
    def cleanup_temp_directories(self):
        """Clean up empty directories in cache"""
        try:
            for directory in [self.cache_dir, self.gis_cache_dir, self.ai_cache_dir]:
                if directory.exists():
                    for subdir in directory.rglob('*'):
                        if subdir.is_dir() and not any(subdir.iterdir()):
                            subdir.rmdir()
        except Exception as e:
            print(f"Error cleaning up directories: {e}")
    
    def get_cache_statistics(self) -> Dict:
        """Get detailed cache statistics"""
        sizes = self.get_cache_size()
        autosave_files = self.get_autosave_files()
        
        return {
            'total_size': sizes['total'],
            'total_size_formatted': self.format_size(sizes['total']),
            'breakdown': {
                'autosave': {
                    'size': sizes['autosave'],
                    'size_formatted': self.format_size(sizes['autosave']),
                    'file_count': len(autosave_files)
                },
                'gis_tiles': {
                    'size': sizes['gis_tiles'],
                    'size_formatted': self.format_size(sizes['gis_tiles'])
                },
                'ai_responses': {
                    'size': sizes['ai_responses'],
                    'size_formatted': self.format_size(sizes['ai_responses'])
                }
            },
            'autosave_files': autosave_files
        }
    
    def set_cache_limit(self, limit_mb: int):
        """
        Set cache size limit and cleanup if exceeded
        
        Args:
            limit_mb: Maximum cache size in megabytes
        """
        sizes = self.get_cache_size()
        limit_bytes = limit_mb * 1024 * 1024
        
        if sizes['total'] > limit_bytes:
            # Cleanup oldest files first
            print(f"Cache size ({self.format_size(sizes['total'])}) exceeds limit ({limit_mb} MB)")
            deleted = self.cleanup_old_files(days=7)
            print(f"Deleted {sum(deleted.values())} old files")
            
            # If still over limit, cleanup more aggressively
            sizes = self.get_cache_size()
            if sizes['total'] > limit_bytes:
                self.cleanup_old_files(days=3)


# Example usage
if __name__ == "__main__":
    manager = CacheManager()
    
    print("=" * 60)
    print("CACHE MANAGER TEST")
    print("=" * 60)
    print()
    
    # Get statistics
    stats = manager.get_cache_statistics()
    print(f"Total Cache Size: {stats['total_size_formatted']}")
    print()
    
    print("Breakdown:")
    for category, info in stats['breakdown'].items():
        print(f"  {category}: {info['size_formatted']}")
        if 'file_count' in info:
            print(f"    Files: {info['file_count']}")
    print()
    
    # Autosave files
    if stats['autosave_files']:
        print("Autosave Files:")
        for file in stats['autosave_files'][:3]:  # Show first 3
            print(f"  {file['name']}")
            print(f"    Modified: {file['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Size: {manager.format_size(file['size'])}")
        print()
    
    print("✓ Test complete!")
