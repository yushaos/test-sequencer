"""
Properties widget for displaying TDMS channel information
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                           QGroupBox, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pyqtgraph as pg
from typing import Dict, Optional, List

from utils.helpers import format_si_prefix

class PropertiesWidget(QWidget):
    """Widget for displaying channel properties and cursor information"""
    
    def __init__(self):
        super().__init__()
        
        # State tracking
        self.current_properties: Optional[Dict] = None
        self.current_statistics: Optional[Dict] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Legend group
        legend_group = QGroupBox("Legend")
        legend_layout = QVBoxLayout(legend_group)
        
        self.legend_tree = QTreeWidget()
        self.legend_tree.setHeaderLabels(["Signal", "Color"])
        self.legend_tree.setMinimumHeight(100)
        legend_layout.addWidget(self.legend_tree)
        
        # Properties group
        properties_group = QGroupBox("Channel Properties")
        properties_layout = QVBoxLayout(properties_group)
        
        self.properties_tree = QTreeWidget()
        self.properties_tree.setHeaderHidden(True)
        properties_layout.addWidget(self.properties_tree)
        
        # Statistics group
        statistics_group = QGroupBox("Statistics")
        statistics_layout = QVBoxLayout(statistics_group)
        
        self.statistics_tree = QTreeWidget()
        self.statistics_tree.setHeaderHidden(True)
        statistics_layout.addWidget(self.statistics_tree)
        
        # Add all groups to main layout
        layout.addWidget(legend_group)
        layout.addWidget(properties_group)
        layout.addWidget(statistics_group)
    
    def update_properties(self, properties: Dict) -> None:
        """
        Update channel properties display
        
        Args:
            properties: Dictionary of channel properties
        """
        self.current_properties = properties
        self.properties_tree.clear()
        
        if not properties:
            return
        
        # Add signal name as first item
        signal_name = properties.get('name', '')
        if signal_name:
            signal_item = QTreeWidgetItem(self.properties_tree)
            signal_item.setText(0, f"Signal: {signal_name}")
            signal_item.setBackground(0, pg.mkColor(200, 220, 255))
        
        # Basic properties section
        basic_props = QTreeWidgetItem(self.properties_tree, ["Basic Properties:"])
        
        # Add basic properties
        for key in ['name', 'length', 'data_type']:
            if key in properties:
                item = QTreeWidgetItem(basic_props)
                item.setText(0, f"{key.title()}: {properties[key]}")
        
        # Add description if available
        if 'description' in properties:
            item = QTreeWidgetItem(basic_props)
            item.setText(0, f"Description: {properties['description']}")
        
        # Custom properties section
        if 'properties' in properties and properties['properties']:
            custom_props = QTreeWidgetItem(self.properties_tree, ["Custom Properties:"])
            for key, value in properties['properties'].items():
                item = QTreeWidgetItem(custom_props)
                item.setText(0, f"{key}: {value}")
        
        # Expand all items
        self.properties_tree.expandAll()
    
    def update_legend(self, plots: List[tuple]) -> None:
        """
        Update legend display
        
        Args:
            plots: List of (signal_name, color) tuples
        """
        self.legend_tree.clear()
        
        for signal_name, color in plots:
            item = QTreeWidgetItem(self.legend_tree)
            item.setText(0, signal_name)
            
            # Create color indicator
            color_label = QLabel()
            color_box = (f'<div style="background-color: {color}; '
                        f'width: 20px; height: 10px; '
                        f'border: 1px solid black;"></div>')
            color_label.setText(color_box)
            
            self.legend_tree.setItemWidget(item, 1, color_label)
    
    def update_statistics(self, statistics: Dict) -> None:
        """
        Update statistics display
        
        Args:
            statistics: Dictionary of signal statistics
        """
        self.current_statistics = statistics
        self.statistics_tree.clear()
        
        if not statistics:
            return
        
        # Add statistics header
        stats_header = QTreeWidgetItem(self.statistics_tree, ["Signal Statistics:"])
        stats_header.setBackground(0, pg.mkColor(200, 220, 255))
        
        # Add basic statistics
        basic_stats = [
            ('Mean', 'mean'),
            ('Standard Deviation', 'std'),
            ('Minimum', 'min'),
            ('Maximum', 'max'),
            ('Peak-to-Peak', 'peak_to_peak')
        ]
        
        for display_name, key in basic_stats:
            if key in statistics:
                item = QTreeWidgetItem(stats_header)
                value = statistics[key]
                formatted_value = format_si_prefix(value)
                item.setText(0, f"{display_name}: {formatted_value}")
        
        # Expand all items
        self.statistics_tree.expandAll()
    
    def update_cursor_info(self, x1: Optional[float], y1: Optional[float],
                          x2: Optional[float], y2: Optional[float]) -> None:
        """
        Update cursor information in statistics
        
        Args:
            x1: X position of first cursor
            y1: Y position of first cursor
            x2: X position of second cursor
            y2: Y position of second cursor
        """
        if None in (x1, y1, x2, y2):
            return
            
        # Add cursor measurements to statistics
        cursor_stats = {
            'Cursor 1 X': x1,
            'Cursor 1 Y': y1,
            'Cursor 2 X': x2,
            'Cursor 2 Y': y2,
            'Delta X': abs(x2 - x1),
            'Delta Y': abs(y2 - y1)
        }
        
        # Find or create cursor measurements section
        cursor_header = None
        for i in range(self.statistics_tree.topLevelItemCount()):
            item = self.statistics_tree.topLevelItem(i)
            if item.text(0) == "Cursor Measurements:":
                cursor_header = item
                break
        
        if not cursor_header:
            cursor_header = QTreeWidgetItem(self.statistics_tree, ["Cursor Measurements:"])
            cursor_header.setBackground(0, pg.mkColor(200, 220, 255))
        
        # Clear previous cursor measurements
        while cursor_header.childCount():
            cursor_header.removeChild(cursor_header.child(0))
        
        # Add cursor measurements
        for name, value in cursor_stats.items():
            item = QTreeWidgetItem(cursor_header)
            formatted_value = format_si_prefix(value)
            item.setText(0, f"{name}: {formatted_value}")
        
        # Expand cursor section
        cursor_header.setExpanded(True)
    
    def clear_properties(self) -> None:
        """Clear all properties displays"""
        self.properties_tree.clear()
        self.statistics_tree.clear()
        self.legend_tree.clear()
        self.current_properties = None
        self.current_statistics = None
