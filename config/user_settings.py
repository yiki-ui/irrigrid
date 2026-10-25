#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User Settings Manager
Saves and loads user preferences
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

class SettingsManager:
    """Manage user settings with persistence"""
    
    def __init__(self):
        """Initialize settings manager"""
        self.settings_file = Path(__file__).parent / "user_settings.json"
        self.default_settings = {
            # Units
            "units": "metric",  # metric or imperial
            "currency": "RWF",
            
            # Display
            "theme": "dark",
            "language": "en",
            "show_tooltips": True,
            
            # Defaults
            "default_emitter_flow": 2.0,
            "default_emitter_spacing": 0.3,
            "default_lateral_spacing": 1.2,
            "default_operating_pressure": 100,
            
            # Last used location
            "last_province": None,
            "last_district": None,
            "last_sector": None,
            
            # Window
            "window_maximized": False,
            "window_width": 1400,
            "window_height": 900,
            
            # Features
            "auto_save": True,
            "auto_calculate": False,
            "show_advanced": False,
            
            # Recent files
            "recent_projects": [],
            
            # AI
            "groq_api_key": "",
            "ai_temperature": 0.5,
            
            # Map
            "map_zoom_level": 9,
            "map_show_terrain": True
        }
        
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                
                # Merge with defaults (in case new settings were added)
                settings = self.default_settings.copy()
                settings.update(saved_settings)
                
                print(f"[OK] Settings loaded from {self.settings_file}")
                return settings
            except Exception as e:
                print(f"[WARNING] Error loading settings: {e}")
                return self.default_settings.copy()
        else:
            print("[INFO] No settings file found, using defaults")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """Save settings to file"""
        try:
            # Create config directory if it doesn't exist
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            print(f"[ERROR] Error saving settings: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        self.save_settings()
        print("[OK] Settings reset to defaults")
    
    def add_recent_project(self, project_path: str):
        """Add a project to recent projects list"""
        recent = self.settings.get("recent_projects", [])
        
        # Remove if already in list
        if project_path in recent:
            recent.remove(project_path)
        
        # Add to front
        recent.insert(0, project_path)
        
        # Keep only last 10
        recent = recent[:10]
        
        self.settings["recent_projects"] = recent
        self.save_settings()
    
    def get_recent_projects(self) -> list:
        """Get list of recent projects"""
        return self.settings.get("recent_projects", [])


# Global settings instance
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
