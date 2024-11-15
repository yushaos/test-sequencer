"""
Main window implementation for TDMS Viewer
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QGroupBox, QTabWidget)
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QIcon
import os

from ui.widgets.graph_widget import GraphWidget
from ui.widgets.table_widget import TableWidget
from ui.widgets.tree_widget import SignalTreeWidget
from ui.widgets.toolbar_widget import ToolbarWidget
from ui.widgets.properties_widget import PropertiesWidget
from ui.widgets.file_widget import FileWidget

from core.tdms_handler import TDMSHandler
from core.data_manager import DataManager
from config.settings import settings

class TDMSMainWindow(QMainWindow):
    """Main window for TDMS Viewer application"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.tdms_handler = TDMSHandler()
        self.data_manager = DataManager()
        self.threadpool = QThreadPool()
        
        # Set window properties
        self.setWindowTitle("TDMS Viewer")
        self.setup_window_state()
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
    
    def setup_window_state(self):
        """Setup initial window state"""
        window_state = settings.get_window_state()
        if window_state.get('maximized', True):
            self.setWindowState(Qt.WindowMaximized)
        else:
            size = window_state.get('size', [800, 600])
            pos = window_state.get('position', [100, 100])
            self.resize(*size)
            self.move(*pos)
    
    def setup_ui(self):
        """Setup user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(2)
        
        # Left panel (Signal Names)
        left_panel = QGroupBox("Signal Names")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(2)
        
        self.signal_tree = SignalTreeWidget()
        left_layout.addWidget(self.signal_tree)
        
        # Center panel
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(2)
        
        # File location widget
        self.file_widget = FileWidget()
        center_layout.addWidget(self.file_widget)
        
        # Tabs for Graph and Table
        self.tabs = QTabWidget()
        
        # Graph widget
        self.graph_widget = GraphWidget(self.data_manager)
        self.tabs.addTab(self.graph_widget, "Graph")
        
        # Table widget
        self.table_widget = TableWidget(self.data_manager)
        self.tabs.addTab(self.table_widget, "Table")
        
        center_layout.addWidget(self.tabs)
        
        # Toolbar
        self.toolbar = ToolbarWidget(self.graph_widget)
        center_layout.addWidget(self.toolbar)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(2)
        
        # Properties widget
        self.properties_widget = PropertiesWidget()
        right_layout.addWidget(self.properties_widget)
        
        # Add panels to main layout
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(center_panel, stretch=4)
        layout.addWidget(right_panel, stretch=1)
    
    def setup_connections(self):
        """Setup signal/slot connections"""
        # File handling
        self.file_widget.file_loaded.connect(self.on_file_loaded)
        
        # Signal tree
        self.signal_tree.signal_selected.connect(self.on_signal_selected)
        self.signal_tree.signal_deselected.connect(self.on_signal_deselected)
        
        # Tab changes
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Graph updates
        self.graph_widget.signals.plot_updated.connect(self.on_plot_updated)
        
        # Properties updates
        self.graph_widget.signals.cursor_moved.connect(self.properties_widget.update_cursor_info)
    
    def on_file_loaded(self, file_path: str):
        """Handle file loading"""
        if self.tdms_handler.load_file(file_path):
            # Update UI components
            self.signal_tree.update_tree(self.tdms_handler)
            self.graph_widget.clear_plots()
            self.table_widget.clear_table()
            self.properties_widget.clear_properties()
            
            # Save last directory
            settings.set_last_directory(os.path.dirname(file_path))
    
    def on_signal_selected(self, group_name: str, channel_name: str):
        """Handle signal selection"""
        # Get signal data
        time_data, value_data = self.tdms_handler.get_channel_data(
            group_name, channel_name)
        
        if time_data is not None and value_data is not None:
            # Update graph
            self.graph_widget.add_plot(group_name, channel_name, 
                                     time_data, value_data)
            
            # Update properties
            properties = self.tdms_handler.get_channel_properties(
                group_name, channel_name)
            self.properties_widget.update_properties(properties)
            
            # Update table if needed
            if self.tabs.currentIndex() == 1:
                self.table_widget.update_data()
    
    def on_signal_deselected(self, group_name: str, channel_name: str):
        """Handle signal deselection"""
        self.graph_widget.remove_plot(f"{group_name}/{channel_name}")
        if self.tabs.currentIndex() == 1:
            self.table_widget.update_data()
    
    def on_tab_changed(self, index: int):
        """Handle tab changes"""
        if index == 1:  # Table tab
            self.table_widget.update_data()
    
    def on_plot_updated(self, signal_key: str):
        """Handle plot updates"""
        if self.tabs.currentIndex() == 1:
            self.table_widget.update_data()
    
    def closeEvent(self, event):
        """Handle application closure"""
        # Save window state
        window_state = {
            'maximized': self.isMaximized(),
            'size': [self.width(), self.height()],
            'position': [self.x(), self.y()]
        }
        settings.set_window_state(window_state)
        
        # Clean up
        self.graph_widget.cleanup()
        self.table_widget.cleanup()
        
        event.accept()
