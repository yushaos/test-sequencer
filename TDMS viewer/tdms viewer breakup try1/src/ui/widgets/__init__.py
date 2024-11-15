"""
UI Widgets Package

Contains all custom widgets used in the TDMS Viewer application.
Provides a consistent interface for widget creation and management.
"""

from .graph_widget import GraphWidget
from .table_widget import TableWidget
from .tree_widget import SignalTreeWidget
from .toolbar_widget import ToolbarWidget
from .properties_widget import PropertiesWidget
from .file_widget import FileWidget

from PyQt5.QtWidgets import QWidget
from typing import Dict, Type, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Widget registry
WIDGET_CLASSES = {
    'graph': GraphWidget,
    'table': TableWidget,
    'tree': SignalTreeWidget,
    'toolbar': ToolbarWidget,
    'properties': PropertiesWidget,
    'file': FileWidget
}

# Default widget styles
DEFAULT_STYLES = {
    'graph': {
        'min_height': 300,
        'background': 'white',
        'font_family': 'Arial',
        'font_size': 10
    },
    'table': {
        'alternate_row_colors': True,
        'grid_visible': True,
        'column_width': 150,
        'font_family': 'Arial',
        'font_size': 10
    },
    'tree': {
        'indent': 20,
        'font_family': 'Arial',
        'font_size': 10,
        'selection_color': '#ADD8E6'
    },
    'toolbar': {
        'button_width': 80,
        'spacing': 5,
        'font_family': 'Arial',
        'font_size': 10
    },
    'properties': {
        'group_spacing': 5,
        'font_family': 'Arial',
        'font_size': 10,
        'header_color': '#E6E6E6'
    },
    'file': {
        'button_width': 40,
        'font_family': 'Arial',
        'font_size': 10
    }
}

class WidgetError(Exception):
    """Base exception for widget-related errors"""
    pass

class WidgetFactory:
    """Factory class for creating widgets"""
    
    @staticmethod
    def create_widget(widget_type: str, parent: Optional[QWidget] = None, 
                     **kwargs) -> QWidget:
        """
        Create widget instance
        
        Args:
            widget_type: Type of widget to create
            parent: Optional parent widget
            **kwargs: Additional widget configuration
            
        Returns:
            Created widget instance
            
        Raises:
            WidgetError: If widget type is not found or creation fails
        """
        if widget_type not in WIDGET_CLASSES:
            raise WidgetError(f"Unknown widget type: {widget_type}")
            
        try:
            # Merge default style with provided kwargs
            widget_style = DEFAULT_STYLES.get(widget_type, {}).copy()
            widget_style.update(kwargs)
            
            # Create widget instance
            widget_class = WIDGET_CLASSES[widget_type]
            widget = widget_class(parent=parent, **widget_style)
            
            # Apply common setup
            if hasattr(widget, 'setup_widget'):
                widget.setup_widget()
                
            return widget
            
        except Exception as e:
            logger.error(f"Failed to create {widget_type} widget: {str(e)}")
            raise WidgetError(f"Widget creation failed: {str(e)}")

class WidgetManager:
    """Manages widget lifecycle and configuration"""
    
    def __init__(self):
        self.widgets: Dict[str, QWidget] = {}
        self.factory = WidgetFactory()
    
    def create_widget(self, widget_type: str, widget_id: str, 
                     parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """
        Create and register widget
        
        Args:
            widget_type: Type of widget to create
            widget_id: Unique identifier for widget
            parent: Optional parent widget
            **kwargs: Additional widget configuration
            
        Returns:
            Created widget instance
        """
        widget = self.factory.create_widget(widget_type, parent, **kwargs)
        self.widgets[widget_id] = widget
        return widget
    
    def get_widget(self, widget_id: str) -> Optional[QWidget]:
        """
        Get widget by ID
        
        Args:
            widget_id: Widget identifier
            
        Returns:
            Widget instance or None if not found
        """
        return self.widgets.get(widget_id)
    
    def remove_widget(self, widget_id: str) -> None:
        """
        Remove widget
        
        Args:
            widget_id: Widget identifier
        """
        if widget_id in self.widgets:
            widget = self.widgets.pop(widget_id)
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
            widget.deleteLater()
    
    def cleanup(self) -> None:
        """Clean up all widgets"""
        for widget_id in list(self.widgets.keys()):
            self.remove_widget(widget_id)

# Global widget manager instance
widget_manager = WidgetManager()

# Module interface
__all__ = [
    # Widget classes
    'GraphWidget',
    'TableWidget',
    'SignalTreeWidget',
    'ToolbarWidget',
    'PropertiesWidget',
    'FileWidget',
    
    # Management classes
    'WidgetFactory',
    'WidgetManager',
    'WidgetError',
    
    # Global instances
    'widget_manager',
    
    # Constants
    'WIDGET_CLASSES',
    'DEFAULT_STYLES'
]

def initialize_widgets():
    """Initialize widget system"""
    try:
        # Validate widget classes
        for widget_type, widget_class in WIDGET_CLASSES.items():
            if not issubclass(widget_class, QWidget):
                raise WidgetError(
                    f"Invalid widget class for {widget_type}: "
                    f"must be QWidget subclass"
                )
        
        logger.info("Widget system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize widget system: {str(e)}")
        raise

# Initialize widgets on import
initialize_widgets()
