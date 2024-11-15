"""
Toolbar widget for graph controls and cursor functionality
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                           QLineEdit, QComboBox, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional, Tuple

from ui.widgets.graph_widget import GraphWidget
from utils.helpers import format_si_prefix

class ToolbarWidget(QWidget):
    """Toolbar widget for graph controls"""
    
    # Custom signals
    range_changed = pyqtSignal(float, float, float, float)  # x_min, x_max, y_min, y_max
    scale_changed = pyqtSignal(str)  # scale_mode
    
    def __init__(self, graph_widget: GraphWidget):
        super().__init__()
        
        self.graph_widget = graph_widget
        
        # State tracking
        self.cursor_enabled = False
        self.current_scale = "1 Scale"
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup widget UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        
        # Zoom controls
        self.zoom_in_btn = QPushButton("🔍+ Zoom In")
        self.zoom_out_btn = QPushButton("🔍- Zoom Out")
        self.reset_btn = QPushButton("↺ Reset")
        
        # Cursor controls
        self.cursor_btn = QPushButton("Cursor")
        self.cursor_btn.setCheckable(True)
        self.cursor_btn.setStyleSheet("""
            QPushButton:checked {
                background-color: #ADD8E6;
                border: 1px solid #0078D7;
            }
        """)
        
        self.center_cursor_btn = QPushButton("⌖ Center Cursors")
        
        # Range controls
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setSpacing(5)
        
        # X-axis range
        range_layout.addWidget(QLabel("X:"))
        self.x_min_input = QLineEdit()
        self.x_max_input = QLineEdit()
        self.x_min_input.setPlaceholderText("min")
        self.x_max_input.setPlaceholderText("max")
        self.x_min_input.setFixedWidth(100)
        self.x_max_input.setFixedWidth(100)
        
        # Y-axis range
        range_layout.addWidget(QLabel("Y:"))
        self.y_min_input = QLineEdit()
        self.y_max_input = QLineEdit()
        self.y_min_input.setPlaceholderText("min")
        self.y_max_input.setPlaceholderText("max")
        self.y_min_input.setFixedWidth(100)
        self.y_max_input.setFixedWidth(100)
        
        # Add inputs to range layout
        range_layout.addWidget(self.x_min_input)
        range_layout.addWidget(self.x_max_input)
        range_layout.addWidget(self.y_min_input)
        range_layout.addWidget(self.y_max_input)
        
        # Apply button
        self.apply_range_btn = QPushButton("Apply")
        range_layout.addWidget(self.apply_range_btn)
        
        # Cursor info panel
        self.setup_cursor_info_panel()
        
        # Scale selector
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Y-Axes:"))
        self.scale_selector = QComboBox()
        self.scale_selector.addItems(["1 Scale", "2 Scale"])
        scale_layout.addWidget(self.scale_selector)
        
        # Add all widgets to main layout
        layout.addWidget(self.zoom_in_btn)
        layout.addWidget(self.zoom_out_btn)
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.cursor_btn)
        layout.addWidget(self.center_cursor_btn)
        layout.addWidget(range_widget)
        layout.addWidget(self.cursor_info_widget)
        layout.addLayout(scale_layout)
        layout.addStretch()
    
    def setup_cursor_info_panel(self):
        """Setup cursor information panel"""
        self.cursor_info_widget = QWidget()
        cursor_info_layout = QHBoxLayout(self.cursor_info_widget)
        cursor_info_layout.setSpacing(10)
        
        # Snap selector
        self.cursor_snap_selector = QComboBox()
        self.cursor_snap_selector.setMinimumWidth(150)
        cursor_info_layout.addWidget(QLabel("Snap to:"))
        cursor_info_layout.addWidget(self.cursor_snap_selector)
        
        # Cursor position labels
        self.cursor_x_label = QLabel("X: -")
        self.cursor_y_label = QLabel("Y: -")
        self.cursor_delta_x = QLabel("ΔX: -")
        self.cursor_delta_y = QLabel("ΔY: -")
        
        for label in [self.cursor_x_label, self.cursor_y_label,
                     self.cursor_delta_x, self.cursor_delta_y]:
            cursor_info_layout.addWidget(label)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Button connections
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.reset_btn.clicked.connect(self.reset_view)
        self.cursor_btn.clicked.connect(self.toggle_cursor)
        self.center_cursor_btn.clicked.connect(self.center_cursors)
        self.apply_range_btn.clicked.connect(self.apply_manual_range)
        
        # Scale selector
        self.scale_selector.currentTextChanged.connect(self.on_scale_changed)
        
        # Cursor snap selector
        self.cursor_snap_selector.currentIndexChanged.connect(self.on_snap_changed)
        
        # Graph widget connections
        self.graph_widget.signals.cursor_moved.connect(self.update_cursor_info)
        self.graph_widget.signals.range_changed.connect(self.update_range_inputs)
    
    def zoom_in(self):
        """Handle zoom in"""
        self.graph_widget.zoom_in()
    
    def zoom_out(self):
        """Handle zoom out"""
        self.graph_widget.zoom_out()
    
    def reset_view(self):
        """Reset view to show all data"""
        self.graph_widget.reset_zoom()
    
    def toggle_cursor(self):
        """Toggle cursor visibility"""
        self.cursor_enabled = self.cursor_btn.isChecked()
        self.graph_widget.toggle_cursor(self.cursor_enabled)
        self.center_cursor_btn.setEnabled(self.cursor_enabled)
        self.cursor_snap_selector.setEnabled(self.cursor_enabled)
    
    def center_cursors(self):
        """Center cursors in current view"""
        if self.cursor_enabled:
            self.graph_widget.center_cursors()
    
    def apply_manual_range(self):
        """Apply manually entered ranges"""
        try:
            x_min = float(self.x_min_input.text() or 'nan')
            x_max = float(self.x_max_input.text() or 'nan')
            y_min = float(self.y_min_input.text() or 'nan')
            y_max = float(self.y_max_input.text() or 'nan')
            
            if all(map(lambda x: not isinstance(x, float) or not x != x,
                      [x_min, x_max, y_min, y_max])):
                self.range_changed.emit(x_min, x_max, y_min, y_max)
                self.graph_widget.set_range(x_min, x_max, y_min, y_max)
        except ValueError:
            pass
    
    def update_range_inputs(self, x_range: Tuple[float, float], 
                          y_range: Tuple[float, float]):
        """
        Update range input values
        
        Args:
            x_range: Tuple of (x_min, x_max)
            y_range: Tuple of (y_min, y_max)
        """
        self.x_min_input.setText(f"{x_range[0]:.6f}")
        self.x_max_input.setText(f"{x_range[1]:.6f}")
        self.y_min_input.setText(f"{y_range[0]:.6f}")
        self.y_max_input.setText(f"{y_range[1]:.6f}")
    
    def update_cursor_info(self, x1: Optional[float], y1: Optional[float],
                          x2: Optional[float], y2: Optional[float]):
        """
        Update cursor information display
        
        Args:
            x1: X position of first cursor
            y1: Y position of first cursor
            x2: X position of second cursor
            y2: Y position of second cursor
        """
        if None in (x1, y1, x2, y2):
            self.cursor_x_label.setText("X1: - | X2: -")
            self.cursor_y_label.setText("Y1: - | Y2: -")
            self.cursor_delta_x.setText("ΔX: -")
            self.cursor_delta_y.setText("ΔY: -")
            return
        
        # Format cursor positions
        self.cursor_x_label.setText(
            f"X1: {format_si_prefix(x1)} | X2: {format_si_prefix(x2)}")
        self.cursor_y_label.setText(
            f"Y1: {format_si_prefix(y1)} | Y2: {format_si_prefix(y2)}")
        
        # Calculate and format deltas
        delta_x = abs(x2 - x1)
        delta_y = abs(y2 - y1)
        self.cursor_delta_x.setText(f"ΔX: {format_si_prefix(delta_x)}")
        self.cursor_delta_y.setText(f"ΔY: {format_si_prefix(delta_y)}")
    
    def on_scale_changed(self, scale_mode: str):
        """
        Handle scale mode changes
        
        Args:
            scale_mode: New scale mode
        """
        if scale_mode != self.current_scale:
            self.current_scale = scale_mode
            self.scale_changed.emit(scale_mode)
    
    def on_snap_changed(self, index: int):
        """
        Handle cursor snap changes
        
        Args:
            index: Selected index in snap selector
        """
        if index >= 0:
            signal_key = self.cursor_snap_selector.itemData(index)
            self.graph_widget.set_cursor_snap_target(signal_key)
    
    def update_snap_selector(self, signals: list):
        """
        Update snap selector options
        
        Args:
            signals: List of available signals
        """
        self.cursor_snap_selector.clear()
        for signal_key, display_name in signals:
            self.cursor_snap_selector.addItem(display_name, signal_key)
