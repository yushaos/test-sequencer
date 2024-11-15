"""
Custom graph widget for TDMS data visualization
"""

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThreadPool
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np
from typing import Dict, Optional, Tuple

from core.data_manager import DataManager
from core.signal_processor import SignalProcessor
from workers.plot_worker import PlotWorker
from config.settings import settings

class GraphWidgetSignals(QObject):
    """Signals for the graph widget"""
    plot_updated = pyqtSignal(str)  # signal_key
    cursor_moved = pyqtSignal(float, float, float, float)  # x1, y1, x2, y2
    range_changed = pyqtSignal(tuple, tuple)  # x_range, y_range

class GraphWidget(QWidget):
    """Custom widget for plotting TDMS data"""
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        
        self.data_manager = data_manager
        self.signals = GraphWidgetSignals()
        
        # Plot management
        self.current_plots: Dict[str, pg.PlotDataItem] = {}
        self.colors = settings.get_graph_colors()
        self.color_index = 0
        
        # Cursor management
        self.cursor_enabled = False
        self.cursor_vline = None
        self.cursor_vline2 = None
        self.cursor_hline = None
        self.cursor_hline2 = None
        self.cursor_active = 1
        self.cursor_positions = [None, None]
        self.cursor_y_values = [None, None]
        
        # View management
        self.auto_range_enabled = True
        self.last_view_range = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        
        # Configure view box
        view_box = self.plot_widget.getPlotItem().getViewBox()
        view_box.setMouseMode(pg.ViewBox.PanMode)
        view_box.setMouseEnabled(x=True, y=False)
        
        layout.addWidget(self.plot_widget)
    
    def setup_connections(self):
        """Setup signal connections"""
        # View range changes
        self.plot_widget.getPlotItem().getViewBox().sigRangeChanged.connect(
            self.on_range_changed)
    
    def add_plot(self, group_name: str, channel_name: str, 
                 time_data: np.ndarray, value_data: np.ndarray) -> None:
        """
        Add new plot to the graph
        
        Args:
            group_name: TDMS group name
            channel_name: Channel name
            time_data: X-axis data
            value_data: Y-axis data
        """
        signal_key = f"{group_name}/{channel_name}"
        
        if signal_key not in self.current_plots:
            # Get next color
            color = self.colors[self.color_index % len(self.colors)]
            self.color_index += 1
            
            # Create plot worker
            worker = PlotWorker(signal_key, value_data, time_data, color)
            
            # Connect worker signals
            worker.signals.chunk_ready.connect(self.on_plot_chunk_ready)
            worker.signals.data_stored.connect(self.on_data_stored)
            worker.signals.progress.connect(self.on_plot_progress)
            worker.signals.error.connect(self.on_plot_error)
            
            # Start worker using global thread pool
            QThreadPool.globalInstance().start(worker)
            
            # Emit the signal after adding the plot
            self.signals.plot_updated.emit(signal_key)
    
    def remove_plot(self, signal_key: str) -> None:
        """
        Remove plot from graph
        
        Args:
            signal_key: Signal identifier
        """
        if signal_key in self.current_plots:
            plot_item = self.current_plots[signal_key]
            self.plot_widget.removeItem(plot_item)
            del self.current_plots[signal_key]
            
            # Remove from data manager
            self.data_manager.remove_signal(signal_key)
            
            # Update cursors
            self.maintain_cursors()
            
            # Emit update signal
            self.signals.plot_updated.emit(signal_key)
    
    def clear_plots(self) -> None:
        """Clear all plots"""
        self.plot_widget.clear()
        self.current_plots.clear()
        self.color_index = 0
        
        # Reset cursors
        self.cursor_positions = [None, None]
        self.cursor_y_values = [None, None]
        self.cursor_active = 1
        
        # Clear data manager
        self.data_manager.clear_cache()
    
    def on_plot_chunk_ready(self, signal_key: str, y_data: np.ndarray, 
                           x_data: np.ndarray, color: str, is_final: bool) -> None:
        """Handle plot data chunks"""
        if signal_key not in self.current_plots:
            # Create new plot
            pen = pg.mkPen(color=color, width=2)
            plot = self.plot_widget.plot(x_data, y_data, pen=pen)
            self.current_plots[signal_key] = plot
            
            # Enable auto range for first plot
            if len(self.current_plots) == 1:
                self.plot_widget.getPlotItem().enableAutoRange()
        else:
            # Update existing plot
            self.current_plots[signal_key].setData(x_data, y_data)
        
        # Maintain cursors
        self.maintain_cursors()
        
        if is_final:
            self.signals.plot_updated.emit(signal_key)
    
    def on_data_stored(self, signal_key: str, y_data: np.ndarray, 
                      x_data: np.ndarray) -> None:
        """Handle full resolution data storage"""
        self.data_manager.cache_signal(signal_key, x_data, y_data)
    
    def on_plot_progress(self, progress: int) -> None:
        """Handle plot progress updates"""
        # Could be used to update a progress bar
        pass
    
    def on_plot_error(self, error_msg: str) -> None:
        """Handle plot errors"""
        print(f"Plot error: {error_msg}")
    
    def on_range_changed(self, view_box, ranges) -> None:
        """Handle view range changes"""
        if not self.auto_range_enabled:
            x_range, y_range = ranges
            
            # Update plots with visible data
            for signal_key, plot in self.current_plots.items():
                data = self.data_manager.get_signal_data(signal_key)
                if data:
                    x_data, y_data = data
                    visible_x, visible_y = SignalProcessor.get_visible_data(
                        x_data, y_data, x_range)
                    plot.setData(visible_x, visible_y)
            
            # Update cursor positions
            if self.cursor_enabled:
                self.update_cursor_values()
            
            # Emit range changed signal
            self.signals.range_changed.emit(x_range, y_range)
            
            self.last_view_range = ranges
    
    def toggle_cursor(self, enabled: bool) -> None:
        """Toggle cursor visibility"""
        self.cursor_enabled = enabled
        
        if enabled:
            if not self.cursor_vline:
                self._create_cursors()
            self._show_cursors()
        else:
            self._hide_cursors()
    
    def _create_cursors(self) -> None:
        """Create cursor lines"""
        # Create cursor 1
        pen1 = pg.mkPen(color='#FF69B4', width=2, style=Qt.DashLine)
        self.cursor_vline = pg.InfiniteLine(angle=90, movable=True, pen=pen1)
        self.cursor_hline = pg.InfiniteLine(angle=0, movable=True, pen=pen1)
        
        # Create cursor 2
        pen2 = pg.mkPen(color='#FFA500', width=2, style=Qt.DashLine)
        self.cursor_vline2 = pg.InfiniteLine(angle=90, movable=True, pen=pen2)
        self.cursor_hline2 = pg.InfiniteLine(angle=0, movable=True, pen=pen2)
        
        # Set z-values
        for cursor in [self.cursor_vline, self.cursor_hline, 
                      self.cursor_vline2, self.cursor_hline2]:
            cursor.setZValue(1000)
            
        # Connect drag events
        self.cursor_vline.sigPositionChanged.connect(
            lambda: self.on_cursor_dragged(1))
        self.cursor_vline2.sigPositionChanged.connect(
            lambda: self.on_cursor_dragged(2))
    
    def _show_cursors(self) -> None:
        """Show cursor lines"""
        if not self.current_plots:
            return
            
        # Get current view range
        view_range = self.plot_widget.getPlotItem().viewRange()
        x_min, x_max = view_range[0]
        
        # Position cursors
        x1 = x_min + (x_max - x_min) * 0.4
        x2 = x_min + (x_max - x_min) * 0.6
        
        # Set positions
        self.cursor_positions = [x1, x2]
        self.update_cursor_values()
        
        # Show cursors
        for cursor in [self.cursor_vline, self.cursor_hline, 
                      self.cursor_vline2, self.cursor_hline2]:
            if cursor not in self.plot_widget.items():
                self.plot_widget.addItem(cursor)
    
    def _hide_cursors(self) -> None:
        """Hide cursor lines"""
        for cursor in [self.cursor_vline, self.cursor_hline, 
                      self.cursor_vline2, self.cursor_hline2]:
            if cursor in self.plot_widget.items():
                self.plot_widget.removeItem(cursor)
    
    def on_cursor_dragged(self, cursor_num: int) -> None:
        """Handle cursor drag events"""
        v_cursor = self.cursor_vline if cursor_num == 1 else self.cursor_vline2
        h_cursor = self.cursor_hline if cursor_num == 1 else self.cursor_hline2
        
        x_pos = v_cursor.getXPos()
        self.cursor_positions[cursor_num - 1] = x_pos
        
        self.update_cursor_values()
    
    def update_cursor_values(self) -> None:
        """Update cursor Y values"""
        if not self.cursor_enabled or not self.current_plots:
            return
            
        for i, x_pos in enumerate(self.cursor_positions):
            if x_pos is not None:
                # Get Y value from the first plot
                first_plot = next(iter(self.current_plots.values()))
                x_data, y_data = first_plot.getData()
                y_val = SignalProcessor.get_y_at_x(x_pos, x_data, y_data)
                
                # Update horizontal cursor
                h_cursor = self.cursor_hline if i == 0 else self.cursor_hline2
                if y_val is not None:
                    h_cursor.setPos(y_val)
                    self.cursor_y_values[i] = y_val
        
        # Emit cursor moved signal
        self.signals.cursor_moved.emit(
            self.cursor_positions[0], self.cursor_y_values[0],
            self.cursor_positions[1], self.cursor_y_values[1]
        )
    
    def maintain_cursors(self) -> None:
        """Ensure cursors remain visible when plots update"""
        if self.cursor_enabled:
            for cursor in [self.cursor_vline, self.cursor_hline, 
                         self.cursor_vline2, self.cursor_hline2]:
                if cursor in self.plot_widget.items():
                    self.plot_widget.removeItem(cursor)
                    self.plot_widget.addItem(cursor)
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.clear_plots()
