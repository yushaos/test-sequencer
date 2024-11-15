"""
Dialogs Package

Contains custom dialog implementations for the TDMS Viewer application.
Provides a consistent interface for dialog creation and management.
"""

from .file_dialog import TDMSFileDialog, get_open_filename
from PyQt5.QtWidgets import QDialog, QWidget
from typing import Dict, Type, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Dialog registry
DIALOG_CLASSES = {
    'file': TDMSFileDialog
}

# Default dialog configurations
DIALOG_DEFAULTS = {
    'file': {
        'use_native': False,
        'show_preview': True,
        'remember_directory': True,
        'track_recent': True,
        'max_recent': 10
    }
}

class DialogError(Exception):
    """Base exception for dialog-related errors"""
    pass

class DialogFactory:
    """Factory class for creating dialogs"""
    
    @staticmethod
    def create_dialog(dialog_type: str, parent: Optional[QWidget] = None,
                     **kwargs) -> QDialog:
        """
        Create dialog instance
        
        Args:
            dialog_type: Type of dialog to create
            parent: Optional parent widget
            **kwargs: Additional dialog configuration
            
        Returns:
            Created dialog instance
            
        Raises:
            DialogError: If dialog type is not found or creation fails
        """
        if dialog_type not in DIALOG_CLASSES:
            raise DialogError(f"Unknown dialog type: {dialog_type}")
            
        try:
            # Merge default configuration with provided kwargs
            dialog_config = DIALOG_DEFAULTS.get(dialog_type, {}).copy()
            dialog_config.update(kwargs)
            
            # Create dialog instance
            dialog_class = DIALOG_CLASSES[dialog_type]
            dialog = dialog_class(parent=parent, **dialog_config)
            
            return dialog
            
        except Exception as e:
            logger.error(f"Failed to create {dialog_type} dialog: {str(e)}")
            raise DialogError(f"Dialog creation failed: {str(e)}")

class DialogManager:
    """Manages dialog creation and lifecycle"""
    
    def __init__(self):
        self.factory = DialogFactory()
        self.active_dialogs: Dict[str, QDialog] = {}
    
    def show_dialog(self, dialog_type: str, dialog_id: str,
                   parent: Optional[QWidget] = None, **kwargs) -> Tuple[int, Any]:
        """
        Show dialog and return result
        
        Args:
            dialog_type: Type of dialog to show
            dialog_id: Unique identifier for dialog
            parent: Optional parent widget
            **kwargs: Additional dialog configuration
            
        Returns:
            Tuple of (dialog result code, dialog data)
        """
        try:
            dialog = self.factory.create_dialog(dialog_type, parent, **kwargs)
            self.active_dialogs[dialog_id] = dialog
            
            result = dialog.exec_()
            
            # Get dialog specific data
            dialog_data = None
            if dialog_type == 'file':
                if result == dialog.Accepted:
                    dialog_data = {
                        'files': dialog.selectedFiles(),
                        'options': dialog.get_dialog_options()
                    }
            
            # Cleanup
            self.close_dialog(dialog_id)
            
            return result, dialog_data
            
        except Exception as e:
            logger.error(f"Failed to show dialog: {str(e)}")
            raise DialogError(f"Failed to show dialog: {str(e)}")
    
    def close_dialog(self, dialog_id: str) -> None:
        """
        Close and cleanup dialog
        
        Args:
            dialog_id: Dialog identifier
        """
        if dialog_id in self.active_dialogs:
            dialog = self.active_dialogs.pop(dialog_id)
            dialog.deleteLater()
    
    def close_all_dialogs(self) -> None:
        """Close all active dialogs"""
        for dialog_id in list(self.active_dialogs.keys()):
            self.close_dialog(dialog_id)

# Convenience functions
def show_file_dialog(parent: Optional[QWidget] = None,
                    caption: str = "Select TDMS File",
                    directory: str = "",
                    **kwargs) -> Tuple[str, dict]:
    """
    Show file selection dialog
    
    Args:
        parent: Optional parent widget
        caption: Dialog caption
        directory: Starting directory
        **kwargs: Additional dialog configuration
        
    Returns:
        Tuple of (selected file path, dialog options)
    """
    return get_open_filename(parent, caption, directory, **kwargs)

# Global dialog manager instance
dialog_manager = DialogManager()

# Module interface
__all__ = [
    # Dialog classes
    'TDMSFileDialog',
    
    # Management classes
    'DialogFactory',
    'DialogManager',
    'DialogError',
    
    # Convenience functions
    'show_file_dialog',
    'get_open_filename',
    
    # Global instances
    'dialog_manager',
    
    # Constants
    'DIALOG_CLASSES',
    'DIALOG_DEFAULTS'
]

def initialize_dialogs():
    """Initialize dialog system"""
    try:
        # Validate dialog classes
        for dialog_type, dialog_class in DIALOG_CLASSES.items():
            if not issubclass(dialog_class, QDialog):
                raise DialogError(
                    f"Invalid dialog class for {dialog_type}: "
                    f"must be QDialog subclass"
                )
        
        logger.info("Dialog system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize dialog system: {str(e)}")
        raise

# Initialize dialogs on import
initialize_dialogs()
