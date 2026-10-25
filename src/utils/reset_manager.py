#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reset Manager
Handles application reset, factory defaults, and restart
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings

from src.utils.cache_manager import CacheManager
from src.utils.session_manager import SessionManager


class ResetManager:
    """Manages application reset operations"""
    
    def __init__(self, parent=None):
        """
        Initialize reset manager
        
        Args:
            parent: Parent widget for dialogs
        """
        self.parent = parent
        self.cache_manager = CacheManager()
        self.session_manager = SessionManager()
        self.settings = QSettings("IrrigationDSS", "AquaCropWat")
    
    def confirm_reset(self, title: str, message: str, items: List[str]) -> bool:
        """
        Show confirmation dialog for reset operations
        
        Args:
            title: Dialog title
            message: Main message
            items: List of items that will be reset
            
        Returns:
            True if user confirms
        """
        items_text = "\n".join([f"  • {item}" for item in items])
        full_message = f"{message}\n\nThis will reset:\n{items_text}\n\n⚠️ This action cannot be undone!\n\nContinue?"
        
        reply = QMessageBox.warning(
            self.parent,
            title,
            full_message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    def reset_settings_only(self) -> bool:
        """
        Reset application settings to defaults
        
        Returns:
            Success status
        """
        items = [
            "Application preferences",
            "Window layout",
            "Calculation settings",
            "UI customization"
        ]
        
        if not self.confirm_reset("Reset Settings", "Reset all application settings to defaults?", items):
            return False
        
        try:
            # Clear all settings
            self.settings.clear()
            
            # Set default values
            defaults = {
                'theme': 'light',
                'language': 'en',
                'units': 'metric',
                'autosave_interval': 5,
                'eto_method': 'penman-monteith',
                'map_provider': 'openstreetmap',
                'restore_session': True,
                'cache_limit_mb': 500,
                'show_tooltips': True,
                'confirm_delete': True
            }
            
            for key, value in defaults.items():
                self.settings.setValue(f'pref_{key}', value)
            
            self.settings.sync()
            
            QMessageBox.information(
                self.parent,
                "Settings Reset",
                "Application settings have been reset to defaults.\n\nPlease restart the application."
            )
            
            return True
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Failed to reset settings: {e}"
            )
            return False
    
    def reset_cache(self) -> bool:
        """
        Clear all cache
        
        Returns:
            Success status
        """
        items = [
            "Application cache",
            "GIS map tiles",
            "AI response cache",
            "Autosave files",
            "Temporary files"
        ]
        
        if not self.confirm_reset("Clear Cache", "Clear all cached data?", items):
            return False
        
        try:
            results = self.cache_manager.clear_all_cache()
            
            if all(results.values()):
                QMessageBox.information(
                    self.parent,
                    "Cache Cleared",
                    "All cache has been cleared successfully."
                )
                return True
            else:
                failed = [k for k, v in results.items() if not v]
                QMessageBox.warning(
                    self.parent,
                    "Partial Success",
                    f"Some cache could not be cleared: {', '.join(failed)}"
                )
                return False
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Failed to clear cache: {e}"
            )
            return False
    
    def reset_session(self) -> bool:
        """
        Clear saved session
        
        Returns:
            Success status
        """
        items = [
            "Last session data",
            "Project state",
            "UI state",
            "Recent projects list"
        ]
        
        if not self.confirm_reset("Clear Session", "Clear saved session data?", items):
            return False
        
        try:
            self.session_manager.clear_session()
            self.session_manager.clear_recent_projects()
            
            QMessageBox.information(
                self.parent,
                "Session Cleared",
                "Saved session has been cleared."
            )
            return True
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Failed to clear session: {e}"
            )
            return False
    
    def reset_database(self, confirm: bool = True) -> bool:
        """
        Clear database (requires explicit confirmation)
        
        Args:
            confirm: Show confirmation dialog
            
        Returns:
            Success status
        """
        items = [
            "All projects",
            "All users",
            "All irrigation events",
            "All chat history",
            "All saved data"
        ]
        
        if confirm:
            if not self.confirm_reset(
                "⚠️ Clear Database",
                "⚠️ WARNING: This will delete ALL your data!",
                items
            ):
                return False
        
        try:
            from config.database import engine, Base
            from src.database.models import User, Project, IrrigationEvent
            from src.database.chat_history import ChatSession, ChatMessage
            
            # Drop all tables
            Base.metadata.drop_all(bind=engine)
            
            # Recreate tables (empty)
            Base.metadata.create_all(bind=engine)
            
            QMessageBox.information(
                self.parent,
                "Database Cleared",
                "All database data has been cleared.\n\nThe application will restart."
            )
            
            return True
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Failed to clear database: {e}"
            )
            return False
    
    def factory_reset(self) -> bool:
        """
        Complete factory reset - everything
        
        Returns:
            Success status
        """
        items = [
            "ALL application settings",
            "ALL cache and temporary files",
            "ALL saved sessions",
            "ALL recent projects",
            "⚠️ ALL database data (projects, users, events)",
            "⚠️ ALL chat history"
        ]
        
        # Double confirmation for factory reset
        reply1 = QMessageBox.warning(
            self.parent,
            "⚠️⚠️ FACTORY RESET ⚠️⚠️",
            "⚠️ WARNING: This will DELETE EVERYTHING!\n\n"
            "This action will:\n" + "\n".join([f"  • {item}" for item in items]) + "\n\n"
            "⚠️ THIS CANNOT BE UNDONE! ⚠️\n\n"
            "Are you ABSOLUTELY SURE?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply1 != QMessageBox.Yes:
            return False
        
        # Second confirmation
        reply2 = QMessageBox.warning(
            self.parent,
            "⚠️ Final Confirmation",
            "This is your last chance!\n\n"
            "Type 'RESET' to confirm factory reset:",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply2 != QMessageBox.Yes:
            return False
        
        try:
            # Clear everything
            success = True
            
            # 1. Clear cache
            self.cache_manager.clear_all_cache()
            
            # 2. Clear session
            self.session_manager.clear_session()
            self.session_manager.clear_recent_projects()
            
            # 3. Clear settings
            self.settings.clear()
            self.settings.sync()
            
            # 4. Clear database
            self.reset_database(confirm=False)
            
            QMessageBox.information(
                self.parent,
                "Factory Reset Complete",
                "Application has been reset to factory defaults.\n\n"
                "The application will now restart."
            )
            
            # Restart application
            self.restart_application()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Factory reset failed: {e}\n\n"
                "The application may be in an unstable state.\n"
                "Please reinstall if problems persist."
            )
            return False
    
    def restart_application(self):
        """Restart the application"""
        try:
            # Get the Python executable and script path
            python = sys.executable
            script = sys.argv[0]
            
            # Close current instance and start new one
            if sys.platform == "win32":
                # Windows
                subprocess.Popen([python, script])
            else:
                # Linux/Mac
                os.execl(python, python, script)
            
            # Exit current instance
            sys.exit(0)
            
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Failed to restart application: {e}\n\n"
                "Please restart manually."
            )
    
    def reset_specific_module(self, module: str) -> bool:
        """
        Reset specific application module
        
        Args:
            module: Module name ('gis', 'ai', 'calculations', 'projects')
            
        Returns:
            Success status
        """
        module_actions = {
            'gis': {
                'title': 'Reset GIS Module',
                'items': ['GIS cache', 'Map tiles', 'Location data'],
                'action': self.cache_manager.clear_gis_cache
            },
            'ai': {
                'title': 'Reset AI Module',
                'items': ['AI response cache', 'Chat history', 'AI settings'],
                'action': self._reset_ai_module
            },
            'calculations': {
                'title': 'Reset Calculations',
                'items': ['Cached results', 'Calculation settings'],
                'action': self._reset_calculations_module
            },
            'projects': {
                'title': 'Clear All Projects',
                'items': ['All project data', 'Recent projects list'],
                'action': self._reset_projects_module
            }
        }
        
        if module not in module_actions:
            return False
        
        config = module_actions[module]
        
        if not self.confirm_reset(config['title'], f"Reset {module} module?", config['items']):
            return False
        
        try:
            config['action']()
            QMessageBox.information(
                self.parent,
                "Module Reset",
                f"{config['title']} completed successfully."
            )
            return True
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Failed to reset {module} module: {e}"
            )
            return False
    
    def _reset_ai_module(self):
        """Reset AI module"""
        self.cache_manager.clear_ai_cache()
        # Clear chat history from database
        try:
            from config.database import SessionLocal
            from src.database.chat_history import ChatSession
            
            db = SessionLocal()
            db.query(ChatSession).delete()
            db.commit()
            db.close()
        except:
            pass
    
    def _reset_calculations_module(self):
        """Reset calculations module"""
        # Clear calculation cache
        session = self.session_manager.load_session()
        if session:
            session['calculations'] = {}
            self.session_manager.save_session(session)
    
    def _reset_projects_module(self):
        """Reset projects module"""
        # Clear all projects from database
        try:
            from config.database import SessionLocal
            from src.database.models import Project
            
            db = SessionLocal()
            db.query(Project).delete()
            db.commit()
            db.close()
            
            # Clear recent projects
            self.session_manager.clear_recent_projects()
        except:
            pass
    
    def get_reset_options(self) -> Dict:
        """
        Get available reset options
        
        Returns:
            Dictionary of reset options with descriptions
        """
        return {
            'settings': {
                'name': 'Reset Settings',
                'description': 'Reset application settings to defaults',
                'severity': 'low',
                'action': self.reset_settings_only
            },
            'cache': {
                'name': 'Clear Cache',
                'description': 'Clear all cached data and temporary files',
                'severity': 'low',
                'action': self.reset_cache
            },
            'session': {
                'name': 'Clear Session',
                'description': 'Clear saved session and recent projects',
                'severity': 'medium',
                'action': self.reset_session
            },
            'database': {
                'name': 'Clear Database',
                'description': 'Delete all projects, users, and data',
                'severity': 'high',
                'action': self.reset_database
            },
            'factory': {
                'name': 'Factory Reset',
                'description': 'Reset everything to factory defaults',
                'severity': 'critical',
                'action': self.factory_reset
            }
        }


# Example usage
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("RESET MANAGER TEST")
    print("=" * 60)
    print()
    
    manager = ResetManager()
    
    # Get reset options
    options = manager.get_reset_options()
    
    print("Available Reset Options:")
    for key, opt in options.items():
        print(f"\n{opt['name']} ({opt['severity']})")
        print(f"  {opt['description']}")
    
    print("\nTest complete!")
