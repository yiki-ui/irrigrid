#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Session Manager
Handles session persistence, auto-restore, and state management
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from PyQt5.QtCore import QSettings


class SessionManager:
    """Manages application session state and persistence"""
    
    def __init__(self, app_name: str = "IrrigationDSS"):
        """
        Initialize session manager
        
        Args:
            app_name: Application name for settings
        """
        self.app_name = app_name
        self.settings = QSettings("IrrigationDSS", "AquaCropWat")
        self.session_file = Path.home() / ".irrigation_dss" / "last_session.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Session data structure
        self.session_data = {
            'timestamp': None,
            'project': {},
            'ui_state': {},
            'location': {},
            'calculations': {},
            'preferences': {}
        }
    
    def save_session(self, session_data: Dict[str, Any]):
        """
        Save current session state
        
        Args:
            session_data: Dictionary containing session state
        """
        try:
            # Add timestamp
            session_data['timestamp'] = datetime.now().isoformat()
            
            # Save to JSON file
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Also save to QSettings (backup)
            self.settings.setValue('last_session_timestamp', session_data['timestamp'])
            
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Load last session state
        
        Returns:
            Session data dictionary or None if not found
        """
        try:
            if not self.session_file.exists():
                return None
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            return session_data
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def save_project_state(self, project_data: Dict):
        """Save project-specific state"""
        session = self.load_session() or self.session_data.copy()
        session['project'] = project_data
        self.save_session(session)
    
    def save_ui_state(self, ui_data: Dict):
        """
        Save UI state (tab positions, window size, etc.)
        
        Args:
            ui_data: Dictionary containing:
                - current_tab: Active tab index
                - window_size: [width, height]
                - window_position: [x, y]
                - splitter_sizes: Splitter positions
                - visible_panels: Which panels are visible
        """
        session = self.load_session() or self.session_data.copy()
        session['ui_state'] = ui_data
        self.save_session(session)
    
    def save_location_state(self, location_data: Dict):
        """
        Save selected location data
        
        Args:
            location_data: Dictionary containing:
                - province, district, sector, cell
                - latitude, longitude
                - altitude
                - climate data
        """
        session = self.load_session() or self.session_data.copy()
        session['location'] = location_data
        self.save_session(session)
    
    def save_calculation_state(self, calculation_data: Dict):
        """
        Save calculation results and parameters
        
        Args:
            calculation_data: Calculation results to save
        """
        session = self.load_session() or self.session_data.copy()
        session['calculations'] = calculation_data
        self.save_session(session)
    
    def save_preferences(self, preferences: Dict):
        """
        Save user preferences
        
        Args:
            preferences: Dictionary containing:
                - theme: 'light' or 'dark'
                - language: 'en', 'rw', 'fr'
                - units: 'metric' or 'imperial'
                - autosave_interval: minutes
                - eto_method: calculation method
                - map_provider: GIS provider
        """
        session = self.load_session() or self.session_data.copy()
        session['preferences'] = preferences
        self.save_session(session)
        
        # Also save to QSettings for quick access
        for key, value in preferences.items():
            self.settings.setValue(f'pref_{key}', value)
    
    def get_project_state(self) -> Dict:
        """Get saved project state"""
        session = self.load_session()
        return session['project'] if session else {}
    
    def get_ui_state(self) -> Dict:
        """Get saved UI state"""
        session = self.load_session()
        return session['ui_state'] if session else {}
    
    def get_location_state(self) -> Dict:
        """Get saved location state"""
        session = self.load_session()
        return session['location'] if session else {}
    
    def get_calculation_state(self) -> Dict:
        """Get saved calculation state"""
        session = self.load_session()
        return session['calculations'] if session else {}
    
    def get_preferences(self) -> Dict:
        """Get user preferences"""
        session = self.load_session()
        if session and session.get('preferences'):
            return session['preferences']
        
        # Default preferences
        return {
            'theme': 'light',
            'language': 'en',
            'units': 'metric',
            'autosave_interval': 5,
            'eto_method': 'penman-monteith',
            'map_provider': 'openstreetmap',
            'restore_session': True,
            'cache_limit_mb': 500
        }
    
    def clear_session(self):
        """Clear saved session"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            self.settings.remove('last_session_timestamp')
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False
    
    def should_restore_session(self) -> bool:
        """Check if session should be restored"""
        preferences = self.get_preferences()
        return preferences.get('restore_session', True)
    
    def get_session_age(self) -> Optional[int]:
        """
        Get age of saved session in minutes
        
        Returns:
            Age in minutes or None if no session
        """
        session = self.load_session()
        if not session or 'timestamp' not in session:
            return None
        
        try:
            timestamp = datetime.fromisoformat(session['timestamp'])
            age = (datetime.now() - timestamp).total_seconds() / 60
            return int(age)
        except:
            return None
    
    def export_session(self, file_path: str):
        """
        Export session to file
        
        Args:
            file_path: Output file path
        """
        session = self.load_session()
        if session:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
    
    def import_session(self, file_path: str) -> bool:
        """
        Import session from file
        
        Args:
            file_path: Input file path
            
        Returns:
            Success status
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.save_session(session_data)
            return True
        except Exception as e:
            print(f"Error importing session: {e}")
            return False
    
    def get_session_info(self) -> Dict:
        """Get information about saved session"""
        session = self.load_session()
        
        if not session:
            return {
                'exists': False,
                'timestamp': None,
                'age_minutes': None,
                'has_project': False,
                'has_location': False
            }
        
        return {
            'exists': True,
            'timestamp': session.get('timestamp'),
            'age_minutes': self.get_session_age(),
            'has_project': bool(session.get('project')),
            'has_location': bool(session.get('location')),
            'has_ui_state': bool(session.get('ui_state')),
            'has_calculations': bool(session.get('calculations'))
        }
    
    # QSettings convenience methods
    def get_setting(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.value(key, default)
    
    def set_setting(self, key: str, value):
        """Set a setting value"""
        self.settings.setValue(key, value)
    
    def get_recent_projects(self) -> list:
        """Get list of recently opened projects"""
        recent = self.settings.value('recent_projects', [])
        if isinstance(recent, str):
            recent = [recent]
        return recent or []
    
    def add_recent_project(self, project_path: str, max_recent: int = 10):
        """Add project to recent list"""
        recent = self.get_recent_projects()
        
        # Remove if already exists
        if project_path in recent:
            recent.remove(project_path)
        
        # Add to front
        recent.insert(0, project_path)
        
        # Limit size
        recent = recent[:max_recent]
        
        self.settings.setValue('recent_projects', recent)
    
    def clear_recent_projects(self):
        """Clear recent projects list"""
        self.settings.remove('recent_projects')


# Example usage
if __name__ == "__main__":
    manager = SessionManager()
    
    print("=" * 60)
    print("SESSION MANAGER TEST")
    print("=" * 60)
    print()
    
    # Check for existing session
    info = manager.get_session_info()
    print(f"Existing Session: {info['exists']}")
    if info['exists']:
        print(f"  Age: {info['age_minutes']} minutes")
        print(f"  Has Project: {info['has_project']}")
        print(f"  Has Location: {info['has_location']}")
    print()
    
    # Save test session
    test_session = {
        'project': {
            'name': 'Test Project',
            'crop': 'Tomato',
            'area': 2.5
        },
        'ui_state': {
            'current_tab': 3,
            'window_size': [1200, 800]
        },
        'location': {
            'province': 'Eastern Province',
            'district': 'Bugesera',
            'latitude': -2.2167,
            'longitude': 30.1667
        }
    }
    
    manager.save_session(test_session)
    print("✓ Saved test session")
    
    # Load session
    loaded = manager.load_session()
    print(f"✓ Loaded session: {bool(loaded)}")
    
    # Get preferences
    prefs = manager.get_preferences()
    print(f"✓ Preferences: theme={prefs['theme']}, units={prefs['units']}")
    
    print("\n✓ Test complete!")
