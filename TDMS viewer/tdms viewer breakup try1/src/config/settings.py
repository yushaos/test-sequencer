"""
Configuration management for TDMS Viewer
"""

import os
import sys
import json
from typing import Dict, Optional

def get_application_path() -> str:
    """Get the path to the application directory, works for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        return os.path.dirname(sys.executable)
    else:
        # If the application is run from a Python interpreter
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings:
    """Settings manager for TDMS Viewer"""
    
    def __init__(self):
        self.config_path = os.path.join(get_application_path(), 'config', 'tdms_viewer_config.json')
        self.config: Dict = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.create_default_config()
    
    def create_default_config(self) -> Dict:
        """Create and save default configuration"""
        default_config = {
            "last_directory": "",
            "signal_pairs": [
                {"x": "Time", "y": "Value"},
                {"x": "Timestamp", "y": "Data"}
            ],
            "window_state": {
                "maximized": True,
                "size": [800, 600],
                "position": [100, 100]
            },
            "graph_settings": {
                "default_colors": ['blue', 'red', 'green', 'purple', 'orange', 'cyan'],
                "line_width": 2,
                "show_grid": True
            }
        }
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        return default_config
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get_last_directory(self) -> str:
        """Get last used directory"""
        return self.config.get('last_directory', '')
    
    def set_last_directory(self, directory: str) -> None:
        """Set last used directory"""
        self.config['last_directory'] = directory
        self.save_config()
    
    def get_signal_pairs(self) -> list:
        """Get signal pair mappings"""
        return self.config.get('signal_pairs', [])
    
    def get_graph_colors(self) -> list:
        """Get graph color palette"""
        return self.config.get('graph_settings', {}).get('default_colors', [])
    
    def get_window_state(self) -> Dict:
        """Get saved window state"""
        return self.config.get('window_state', {})
    
    def set_window_state(self, state: Dict) -> None:
        """Save window state"""
        self.config['window_state'] = state
        self.save_config()

# Global settings instance
settings = Settings()
