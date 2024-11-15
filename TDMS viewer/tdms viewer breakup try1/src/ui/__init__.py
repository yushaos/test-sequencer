"""
UI Components Package

Contains all user interface components for the TDMS Viewer application.
"""

from .main_window import TDMSMainWindow
from .widgets.graph_widget import GraphWidget
from .widgets.table_widget import TableWidget
from .widgets.tree_widget import SignalTreeWidget
from .widgets.toolbar_widget import ToolbarWidget
from .widgets.properties_widget import PropertiesWidget
from .widgets.file_widget import FileWidget

# Widget registry for dynamic widget management
WIDGET_REGISTRY = {
    'graph': GraphWidget,
    'table': TableWidget,
    'tree': SignalTreeWidget,
    'toolbar': ToolbarWidget,
    'properties': PropertiesWidget,
    'file': FileWidget
}

# Widget configuration defaults
WIDGET_DEFAULTS = {
    'graph': {
        'background': 'w',
        'show_grid': True,
        'enable_mouse': True,
        'enable_menu': True
    },
    'table': {
        'chunk_size': 1000,
        'show_grid': True,
        'alternate_colors': True,
        'column_width': 150
    },
    'tree': {
        'show_header': False,
        'selection_mode': 'single',
        'drag_enabled': True
    },
    'toolbar': {
        'show_cursor_info': True,
        'show_range_inputs': True,
        'show_scale_selector': True
    },
    'properties': {
        'show_legend': True,
        'show_statistics': True,
        'expand_all': True
    },
    'file': {
        'accept_drops': True,
        'show_browse_button': True,
        'filter': '*.tdms'
    }
}

class WidgetNotFoundError(Exception):
    """Exception raised when a requested widget is not found in the registry"""
    pass

def create_widget(widget_type: str, *args, **kwargs):
    """
    Create widget instance from registry
    
    Args:
        widget_type: Type of widget to create
        *args: Positional arguments for widget constructor
        **kwargs: Keyword arguments for widget constructor
        
    Returns:
        Instance of requested widget
        
    Raises:
        WidgetNotFoundError: If widget type is not found in registry
    """
    if widget_type not in WIDGET_REGISTRY:
        raise WidgetNotFoundError(f"Widget type '{widget_type}' not found")
    
    # Merge default configuration with provided kwargs
    widget_config = WIDGET_DEFAULTS.get(widget_type, {}).copy()
    widget_config.update(kwargs)
    
    return WIDGET_REGISTRY[widget_type](*args, **widget_config)

def apply_widget_style(widget, style_dict: dict):
    """
    Apply style configuration to widget
    
    Args:
        widget: Widget instance to style
        style_dict: Dictionary of style properties
    """
    # Qt stylesheet properties
    stylesheet_parts = []
    
    # Process style dictionary
    for key, value in style_dict.items():
        if key == 'background_color':
            stylesheet_parts.append(f"background-color: {value};")
        elif key == 'text_color':
            stylesheet_parts.append(f"color: {value};")
        elif key == 'border':
            stylesheet_parts.append(f"border: {value};")
        elif key == 'font':
            stylesheet_parts.append(f"font: {value};")
        elif key == 'padding':
            stylesheet_parts.append(f"padding: {value};")
        elif key == 'margin':
            stylesheet_parts.append(f"margin: {value};")
    
    if stylesheet_parts:
        widget.setStyleSheet(" ".join(stylesheet_parts))

# Public module interface
__all__ = [
    'TDMSMainWindow',
    'GraphWidget',
    'TableWidget',
    'SignalTreeWidget',
    'ToolbarWidget',
    'PropertiesWidget',
    'FileWidget',
    'create_widget',
    'apply_widget_style',
    'WidgetNotFoundError',
    'WIDGET_REGISTRY',
    'WIDGET_DEFAULTS'
]

# Module initialization
import logging

logger = logging.getLogger(__name__)

def initialize_ui():
    """Initialize UI components and verify environment"""
    try:
        from PyQt5.QtWidgets import QApplication
        if QApplication.instance() is None:
            logger.warning("No QApplication instance found")
        
        # Verify all widget classes are available
        for widget_name, widget_class in WIDGET_REGISTRY.items():
            if not callable(widget_class):
                raise ImportError(f"Widget '{widget_name}' is not properly initialized")
        
        logger.info("UI components initialized successfully")
        
    except ImportError as e:
        logger.error(f"Failed to initialize UI components: {str(e)}")
        raise

# Initialize UI components when module is imported
initialize_ui()
