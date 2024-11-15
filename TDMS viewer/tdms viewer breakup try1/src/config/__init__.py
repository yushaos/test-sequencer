"""
Configuration Package

Handles application configuration management, settings persistence,
and default configurations for the TDMS Viewer application.
"""

import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "window_state": {
        "maximized": True,
        "size": [800, 600],
        "position": [100, 100]
    },
    "graph_settings": {
        "default_colors": [
            "blue", "red", "green", "purple",
            "orange", "cyan", "magenta", "yellow"
        ],
        "line_width": 2,
        "show_grid": True,
        "enable_antialiasing": True,
        "background_color": "white"
    },
    "table_settings": {
        "chunk_size": 1000,
        "show_grid": True,
        "alternate_colors": True,
        "column_width": 150,
        "max_visible_rows": 1000000
    },
    "signal_pairs": [
        {"x": "Time", "y": "Value"},
        {"x": "Timestamp", "y": "Data"}
    ],
    "file_settings": {
        "last_directory": "",
        "recent_files": [],
        "max_recent_files": 10,
        "auto_load_last": False
    },
    "performance": {
        "max_cache_size": 10,
        "enable_threading": True,
        "thread_pool_size": 4,
        "enable_decimation": True,
        "target_points": 1000000
    },
    "cursor_settings": {
        "cursor_color_1": "#FF69B4",
        "cursor_color_2": "#FFA500",
        "line_style": "dashed",
        "line_width": 2,
        "show_cursor_info": True
    }
}

class ConfigError(Exception):
    """Base exception for configuration errors"""
    pass

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Optional configuration directory path
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_file = os.path.join(self.config_dir, 'tdms_viewer_config.json')
        self.config: Dict = {}
        self.load_config()
    
    def _get_default_config_dir(self) -> str:
        """Get default configuration directory"""
        if os.name == 'nt':  # Windows
            base_dir = os.environ.get('APPDATA', '')
        else:  # Unix/Linux/Mac
            base_dir = os.path.expanduser('~/.config')
        
        return os.path.join(base_dir, 'tdms_viewer')
    
    def ensure_config_dir(self) -> None:
        """Ensure configuration directory exists"""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def load_config(self) -> None:
        """Load configuration from file"""
        self.ensure_config_dir()
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults, preserving user settings
                    self.config = self._merge_configs(DEFAULT_CONFIG, loaded_config)
            else:
                self.config = DEFAULT_CONFIG.copy()
                self.save_config()
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = DEFAULT_CONFIG.copy()
    
    def save_config(self) -> None:
        """Save configuration to file"""
        self.ensure_config_dir()
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigError(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the nested dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self.save_config()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """
        Recursively merge configurations
        
        Args:
            default: Default configuration
            user: User configuration
            
        Returns:
            Merged configuration
        """
        merged = default.copy()
        
        for key, value in user.items():
            if (key in merged and isinstance(merged[key], dict) 
                and isinstance(value, dict)):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = DEFAULT_CONFIG.copy()
        self.save_config()
    
    def export_config(self, filepath: str) -> None:
        """
        Export configuration to file
        
        Args:
            filepath: Export file path
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            raise ConfigError(f"Failed to export configuration: {e}")
    
    def import_config(self, filepath: str) -> None:
        """
        Import configuration from file
        
        Args:
            filepath: Import file path
        """
        try:
            with open(filepath, 'r') as f:
                loaded_config = json.load(f)
                self.config = self._merge_configs(DEFAULT_CONFIG, loaded_config)
                self.save_config()
        except Exception as e:
            raise ConfigError(f"Failed to import configuration: {e}")

# Global configuration instance
config_manager = ConfigManager()

# Module interface
__all__ = [
    'config_manager',
    'ConfigManager',
    'ConfigError',
    'DEFAULT_CONFIG'
]

# Initialize logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
