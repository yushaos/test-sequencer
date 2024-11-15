import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton,
                            QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
                            QLineEdit, QFileDialog, QGroupBox, QProgressBar, QComboBox)
from PyQt5.QtCore import Qt, QMimeData, QRunnable, QThreadPool, pyqtSignal, QObject, QTimer, QTime, QThread
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPen, QIcon
from nptdms import TdmsFile
import pyqtgraph as pg
import numpy as np
from collections import defaultdict
from functools import lru_cache
from math import ceil
import json
import os
from scipy import signal
import bisect

def get_application_path():
    """Get the path to the application directory, works for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (compiled with PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # If the application is run from a Python interpreter
        return os.path.dirname(os.path.abspath(__file__))

class WorkerSignals(QObject):
    finished = pyqtSignal(str, object, object, str)  # signal_key, plot_data, time_data, color
class PlotWorkerSignals(QObject):
    chunk_ready = pyqtSignal(str, object, object, str, bool)  # signal_key, y_data, x_data, color, is_final
    progress = pyqtSignal(int)  # Progress percentage
    data_stored = pyqtSignal(str, object, object)  # signal_key, y_data, x_data
class PlotWorker(QRunnable):
    def __init__(self, signal_key, value_channel, time_channel, color):
        super().__init__()
        self.signal_key = signal_key
        self.value_channel = value_channel
        self.time_channel = time_channel
        self.color = color
        self.signals = PlotWorkerSignals()
        self.should_continue = True
        self.INITIAL_POINTS = 1000000
    def run(self):
        try:
            y_data = np.array(self.value_channel[:], dtype=np.float64)
            x_data = np.array(self.time_channel[:], dtype=np.float64)
            
            # Replace invalid values with NaN
            y_data[~np.isfinite(y_data)] = np.nan
            x_data[~np.isfinite(x_data)] = np.nan
            
            # Initial decimation for overview
            if len(x_data) > self.INITIAL_POINTS:
                x_decimated, y_decimated = self.decimate_data(x_data, y_data, self.INITIAL_POINTS)
                self.signals.chunk_ready.emit(self.signal_key, y_decimated, x_decimated, 
                                           self.color, True)
            else:
                self.signals.chunk_ready.emit(self.signal_key, y_data, x_data, 
                                           self.color, True)
                
            # Store full resolution data for later use
            self.signals.data_stored.emit(self.signal_key, y_data, x_data)
            
        except Exception as e:
            print(f"Error in PlotWorker: {e}")
    def decimate_data(self, x_data, y_data, target_points=1000000):
        """Decimate data to target points while preserving signal characteristics"""
        if len(x_data) <= target_points:
            return x_data, y_data
            
        # Calculate decimation factor
        factor = max(1, len(x_data) // target_points)
        
        # Use scipy.signal.decimate for proper anti-aliasing
        decimated_y = signal.decimate(y_data, factor, zero_phase=True)
        decimated_x = x_data[::factor]
        
        return decimated_x, decimated_y
    def get_visible_data(self, x_data, y_data, view_range):
        """Get data within visible range with adaptive resolution"""
        x_min, x_max = view_range
        
        # Find indices of visible range
        start_idx = bisect.bisect_left(x_data, x_min)
        end_idx = bisect.bisect_right(x_data, x_max)
        
        visible_x = x_data[start_idx:end_idx]
        visible_y = y_data[start_idx:end_idx]
        
        # Calculate target points based on screen width
        screen_width = self.graph_widget.width()
        target_points = min(screen_width * 2, len(visible_x))
        
        if len(visible_x) > target_points:
            return self.decimate_data(visible_x, visible_y, target_points)
        
        return visible_x, visible_y
class TableWorkerSignals(QObject):
    chunk_ready = pyqtSignal(int, list, int)  # start_row, chunk_data, start_col
    finished = pyqtSignal()
class TableWorker(QRunnable):
    def __init__(self, data_pairs, chunk_size=1000, start_col=0):
        super().__init__()
        self.data_pairs = data_pairs
        self.chunk_size = chunk_size
        self.start_col = start_col
        self.signals = TableWorkerSignals()
        self.should_continue = True
    def run(self):
        try:
            # Process data pairs directly without numpy conversion
            chunks = []
            for x_data, y_data, _ in self.data_pairs:
                chunks.append((x_data, y_data))
            max_rows = max(len(x) for x, _ in chunks)
            current_row = 0
            while current_row < max_rows and self.should_continue:
                chunk_data = self.process_chunk(chunks, current_row)
                self.signals.chunk_ready.emit(current_row, chunk_data, self.start_col)
                current_row += self.chunk_size
                QThread.msleep(1)  # Allow GUI updates
            if self.should_continue:
                self.signals.finished.emit()
        except Exception as e:
            print(f"Error in TableWorker: {e}")
    def process_chunk(self, chunks, start_row):
        """Process data chunk handling both numeric and non-numeric data"""
        end_row = min(start_row + self.chunk_size, max(len(x) for x, _ in chunks))
        chunk_data = []
        for row in range(start_row, end_row):
            row_data = []
            for x_arr, y_arr in chunks:
                if row < len(x_arr):
                    # Convert to string without formatting if not numeric
                    x_val = x_arr[row]
                    y_val = y_arr[row]
                    x_str = f"{x_val:.6f}" if isinstance(x_val, (int, float)) else str(x_val)
                    y_str = f"{y_val:.6f}" if isinstance(y_val, (int, float)) else str(y_val)
                    row_data.extend([x_str, y_str])
                else:
                    row_data.extend(["", ""])
            chunk_data.append(row_data)
        return chunk_data
class TableCache:
    def __init__(self):
        self.headers = []
        self.quick_view_data = []
        self.full_data = {}  # Changed to dict for per-signal caching
        self.plot_keys = set()
        self.max_rows = 0
        self.quick_view_size = 1000
        self.is_fully_loaded = False
        self.visible_columns = set()  # Track which columns are currently displayed
class SignalCache:
    def __init__(self):
        self.x_data = None
        self.y_data = None
class SignalMapper:
    def __init__(self):
        self.mapping = {}
        self.load_config()
    def load_config(self):
        config_path = os.path.join(get_application_path(), 'tdms_viewer_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.mapping = {item['y']: item['x'] for item in config['signal_pairs']}
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load signal mapping config: {e}")
            # Create default config
            default_config = {
                "last_directory": "",
                "signal_pairs": [
                    {"x": "Time", "y": "Value"},  # Default mapping example
                    {"x": "Timestamp", "y": "Data"}  # Another default mapping example
                ]
            }
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                # Write default config
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                print(f"Created default config file at: {config_path}")
                # Set default mapping
                self.mapping = {item['y']: item['x'] for item in default_config['signal_pairs']}
            except Exception as write_error:
                print(f"Error creating default config file: {write_error}")
                self.mapping = {}
    def get_x_signal(self, y_signal):
        """Get the corresponding x signal for a y signal"""
        return self.mapping.get(y_signal)
class TDMSViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.last_directory = self.load_last_directory()
        self.setWindowTitle("TDMS Viewer")
        self.setWindowState(Qt.WindowMaximized)
        # Update icon loading - try PNG first, fall back to ICO
        icon_path_png = os.path.join(get_application_path(), 'TDMS viewer icon.png')
        icon_path_ico = os.path.join(get_application_path(), 'TDMS viewer icon.ico')
        
        if os.path.exists(icon_path_png):
            self.setWindowIcon(QIcon(icon_path_png))
        elif os.path.exists(icon_path_ico):
            self.setWindowIcon(QIcon(icon_path_ico))
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        # Reduce spacing between panels
        layout.setSpacing(2)  # Reduce main layout spacing
        # Left panel (Signal Names)
        left_panel = QGroupBox("Signal Names")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(2)  # Now we can set spacing after creation
        self.signal_tree = QTreeWidget()
        self.signal_tree.setHeaderHidden(True)
        self.signal_tree.itemClicked.connect(self.on_signal_selected)
        self.signal_tree.setSelectionMode(QTreeWidget.SingleSelection)
        # Add this style for blue highlight
        self.signal_tree.setStyleSheet("""
            QTreeWidget::item:selected {
                background-color: #ADD8E6;
            }
        """)
        left_layout.addWidget(self.signal_tree)
        # Center panel
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(2)  # Now we can set spacing after creation
        # File location
        file_layout = QHBoxLayout()
        self.file_location = QLineEdit()
        self.file_location.setPlaceholderText("File Location: ")
        self.file_location.setAcceptDrops(True)
        self.file_location.dragEnterEvent = self.dragEnterEvent
        self.file_location.dropEvent = self.dropEvent
        browse_btn = QPushButton("📁")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_location)
        file_layout.addWidget(browse_btn)
        center_layout.addLayout(file_layout)
        # Tabs for Graph and Table
        self.tabs = QTabWidget()
        # Graph tab
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.showGrid(x=True, y=True)
        # Enable mouse panning by default
        self.graph_widget.getPlotItem().getViewBox().setMouseMode(pg.ViewBox.PanMode)
        # Only allow x-axis panning
        self.graph_widget.getPlotItem().getViewBox().setMouseEnabled(x=True, y=False)
        # Table tab
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(['X', 'Y'])
        self.tabs.addTab(self.graph_widget, "Graph")
        self.tabs.addTab(self.table_widget, "Table")
        center_layout.addWidget(self.tabs)
        # Bottom toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        # Left side buttons
        zoom_in_btn = QPushButton("🔍+ Zoom In")
        zoom_out_btn = QPushButton("🔍- Zoom Out")
        reset_btn = QPushButton("↺ Reset")
        self.cursor_btn = QPushButton("Cursor")
        self.cursor_btn.setCheckable(True)
        self.cursor_btn.setChecked(False)
        self.cursor_btn.setStyleSheet("""
            QPushButton:checked {
                background-color: #ADD8E6;
                border: 1px solid #0078D7;
            }
        """)
        # Add center cursor button after cursor button
        self.center_cursor_btn = QPushButton("⌖ Center Cursors")
        self.center_cursor_btn.clicked.connect(self.center_cursors)
        # Manual range inputs
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
        range_layout.addWidget(self.x_min_input)
        range_layout.addWidget(self.x_max_input)
        # Y-axis range
        range_layout.addWidget(QLabel("Y:"))
        self.y_min_input = QLineEdit()
        self.y_max_input = QLineEdit()
        self.y_min_input.setPlaceholderText("min")
        self.y_max_input.setPlaceholderText("max")
        self.y_min_input.setFixedWidth(100)
        self.y_max_input.setFixedWidth(100)
        range_layout.addWidget(self.y_min_input)
        range_layout.addWidget(self.y_max_input)
        # Add Apply button
        apply_range_btn = QPushButton("Apply")
        apply_range_btn.clicked.connect(self.apply_manual_range)
        range_layout.addWidget(apply_range_btn)
        # Connect to viewbox range changed signal to update input boxes
        self.graph_widget.getPlotItem().getViewBox().sigRangeChanged.connect(self.on_view_range_changed)
        # Add all widgets to toolbar
        toolbar_layout.addWidget(zoom_in_btn)
        toolbar_layout.addWidget(zoom_out_btn)
        toolbar_layout.addWidget(reset_btn)
        toolbar_layout.addWidget(self.cursor_btn)
        toolbar_layout.addWidget(self.center_cursor_btn)
        toolbar_layout.addWidget(range_widget)
        toolbar_layout.addStretch()
        center_layout.addWidget(toolbar)
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(2)  # Now we can set spacing after creation
        # Legend
        legend_group = QGroupBox("Legend")
        legend_layout = QVBoxLayout(legend_group)
        self.legend_list = QTreeWidget()
        self.legend_list.setHeaderLabels(["Signal", "Color"])
        self.legend_list.setMinimumHeight(100)  # Minimum height for legend box
        legend_layout.addWidget(self.legend_list)
        # Channel Properties
        properties_group = QGroupBox("Channel Properties")
        properties_layout = QVBoxLayout(properties_group)
        self.properties_widget = QTreeWidget()
        self.properties_widget.setHeaderHidden(True)
        properties_layout.addWidget(self.properties_widget)
        right_layout.addWidget(legend_group)
        right_layout.addWidget(properties_group)
        # Add panels to main layout
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(center_panel, stretch=4)
        layout.addWidget(right_panel, stretch=1)
        self.current_tdms = None
        self.current_plots = {}
        # Add color palette for different signals
        self.colors = ['blue', 'red', 'green', 'purple', 'orange', 'cyan', 'magenta', 'yellow']
        self.color_index = 0
        self.threadpool = QThreadPool()
        self.plot_queue = []
        self.progress_items = {}  # Add this line to initialize progress_items
        self.current_selected_signal = None
        # In __init__, after creating table_widget:
        self.table_widget.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table_widget.horizontalHeader().setStretchLastSection(False)
        self.table_widget.setShowGrid(True)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.verticalScrollBar().valueChanged.connect(self.on_table_scrolled)
        # Add tab changed connection
        self.tabs.currentChanged.connect(self.on_tab_changed)
        # Replace the simple table cache with new caching system
        self.table_cache = TableCache()
        self.signal_cache = {}  # Dictionary to store SignalCache objects
        self.is_table_loading = False
        self.current_chunk_timer = None
        # Add keyboard modifier tracking
        self.ctrl_pressed = False
        self.signal_tree.installEventFilter(self)
        # Add a counter to track selection order
        self.selection_order = 0
        # Add progress bar for table loading
        self.table_progress = QProgressBar()
        self.table_progress.setMaximumHeight(2)  # Very thin progress bar
        self.table_progress.setTextVisible(False)
        self.table_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: transparent;
            }
            QProgressBar::chunk {
                background-color: #ADD8E6;
            }
        """)
        self.table_progress.hide()
        center_layout.insertWidget(1, self.table_progress)  # Insert after file location
        # Track shift selection
        self.shift_pressed = False
        self.first_selected_item = None
        self.signal_tree.installEventFilter(self)
        # Add cursor info panel
        self.cursor_info_panel = QWidget()
        cursor_info_layout = QHBoxLayout(self.cursor_info_panel)
        cursor_info_layout.setSpacing(10)
        # Add snap selector
        self.cursor_snap_selector = QComboBox()
        self.cursor_snap_selector.setMinimumWidth(150)
        self.cursor_snap_selector.currentIndexChanged.connect(self.on_snap_changed)
        cursor_info_layout.addWidget(QLabel("Snap to:"))
        cursor_info_layout.addWidget(self.cursor_snap_selector)
        self.cursor_x_label = QLabel("X: -")
        self.cursor_y_label = QLabel("Y: -")
        self.cursor_delta_x = QLabel("ΔX: -")
        self.cursor_delta_y = QLabel("ΔY: -")
        for label in [self.cursor_x_label, self.cursor_y_label,
                     self.cursor_delta_x, self.cursor_delta_y]:
            cursor_info_layout.addWidget(label)
        cursor_info_layout.addStretch()
        # Don't hide the panel initially
        center_layout.addWidget(self.cursor_info_panel)
        # Initialize cursor variables
        self.cursor_enabled = False
        self.cursor_vline = None
        self.cursor_vline2 = None  # Second cursor
        self.cursor_active = 1  # Track which cursor is active (1 or 2)
        self.cursor_positions = [None, None]  # Store positions for both cursors
        self.cursor_y_values = [None, None]  # Store y values for both cursors
        self.current_snap_plot = None  # Track currently selected plot for snapping
        # Add button connections
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn.clicked.connect(self.zoom_out)
        reset_btn.clicked.connect(self.reset_zoom)
        self.cursor_btn.clicked.connect(self.toggle_cursor)
        # Add after other initializations
        self.signal_mapper = SignalMapper()
        # Store full resolution data
        self.full_res_data = {}
        
        # Connect view range changed signal
        self.graph_widget.getPlotItem().getViewBox().sigRangeChanged.connect(self.on_range_changed)
        self.current_table_worker = None  # Track current table worker
        self.table_worker_id = 0  # Track worker ID to handle cancellation
        # Add scale selector
        toolbar_layout.addWidget(QLabel("Y-Axes:"))
        self.scale_selector = QComboBox()
        self.scale_selector.addItems(["1 Scale", "2 Scale"])
        self.scale_selector.setCurrentText("1 Scale")
        self.scale_selector.currentTextChanged.connect(self.update_scales)
        toolbar_layout.addWidget(self.scale_selector)
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_tdms_file(files[0])
    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open TDMS File",
            self.last_directory,  # Use last directory
            "TDMS Files (*.tdms)"
        )
        if file_name:
            # Save new directory
            self.last_directory = os.path.dirname(file_name)
            self.save_last_directory(self.last_directory)
            self.load_tdms_file(file_name)
    def load_tdms_file(self, file_path):
        self.file_location.setText(file_path)
        self.current_tdms = TdmsFile.read(file_path)
        self.legend_list.clear()
        self.graph_widget.clear()
        self.current_plots.clear()
        self.color_index = 0  # Reset color index
        self.properties_widget.clear()  # Clear properties widget when loading new file
        self.update_signal_tree()
    def update_signal_tree(self):
        self.signal_tree.clear()
        for group in self.current_tdms.groups():
            group_item = QTreeWidgetItem([group.name])
            self.signal_tree.addTopLevelItem(group_item)
            for channel in group.channels():
                # Skip time channels and only show value channels
                if not channel.name.lower().endswith('_time'):
                    channel_item = QTreeWidgetItem([channel.name])
                    group_item.addChild(channel_item)
    def on_signal_selected(self, item, column):
        if not item.parent():  # It's a group
            group_name = item.text(0)
            self.update_properties(group_name, None)  # Show group properties
            return
        
        if self.shift_pressed and self.first_selected_item:
            self.select_signal_range(self.first_selected_item, item)
            return
        
        if not (self.ctrl_pressed or self.shift_pressed):
            self.first_selected_item = item
        
        group_name = item.parent().text(0)
        channel_name = item.text(0)
        signal_key = f"{group_name}/{channel_name}"
        
        # If Ctrl is not pressed, clear all existing plots and reset selection order
        if not self.ctrl_pressed:
            self.graph_widget.clear()
            self.current_plots.clear()
            self.legend_list.clear()
            self.selection_order = 0
            self.signal_tree.clearSelection()
            item.setSelected(True)  # Select only this item
        
        # Update scale selector based on number of selected signals
        selected_count = len(self.signal_tree.selectedItems())
        current_scale = int(self.scale_selector.currentText()[0])
        if current_scale > selected_count:
            self.scale_selector.setCurrentText(f"{selected_count} Scale")
        
        # Plot the selected signal
        if signal_key not in self.current_plots:
            self.plot_channel(group_name, channel_name)
        
        # Update properties
        self.current_selected_signal = (group_name, channel_name)
        self.update_properties(group_name, channel_name)
        
        # Force table update
        self.table_cache.plot_keys = set()
        self.update_table(group_name, channel_name)
    def plot_channel(self, group_name, channel_name):
        value_channel = self.current_tdms[group_name][channel_name]
        # Check if there's a mapping for this channel
        mapped_time_channel = self.signal_mapper.get_x_signal(channel_name)
        time_channel = None
        if mapped_time_channel:
            # Try to get the mapped time channel
            try:
                time_channel = self.current_tdms[group_name][mapped_time_channel]
            except KeyError:
                print(f"Warning: Mapped time channel {mapped_time_channel} not found")
        # Fallback to default _Time suffix if no mapping or mapping not found
        if not time_channel:
            time_channel_name = f"{channel_name}_Time"
            for ch in self.current_tdms[group_name].channels():
                if ch.name.lower() == time_channel_name.lower():
                    time_channel = ch
                    break
        signal_key = f"{group_name}/{channel_name}"
        if signal_key not in self.current_plots:
            color = self.colors[self.selection_order % len(self.colors)]
            self.selection_order += 1
            # If no time channel found, create a default x-axis
            if time_channel is None:
                time_channel = np.arange(len(value_channel))
            worker = PlotWorker(signal_key, value_channel, time_channel, color)
            worker.signals.chunk_ready.connect(self.plot_chunk_finished)
            worker.signals.progress.connect(self.update_plot_progress)
            self.current_worker = worker
            self.threadpool.start(worker)
            # Reset view range after clearing plots (if this is the first plot)
            if len(self.current_plots) == 0:
                self.graph_widget.getPlotItem().enableAutoRange()
            # Add progress item only
            progress_item = QTreeWidgetItem()
            progress_item.setText(0, "Loading: 0%")
            self.progress_items[signal_key] = progress_item
    def plot_chunk_finished(self, signal_key, plot_data, time_data, color, is_final):
        """Modified plot_chunk_finished to handle multiple scales"""
        scale_num = int(self.scale_selector.currentText()[0])
        plot_count = len(self.current_plots)
        
        if signal_key not in self.current_plots:
            # Get the plot item and determine plot index
            plot_item = self.graph_widget.getPlotItem()
            plot_index = len(self.current_plots)  # This will be 0 for first plot, 1 for second, etc.
            
            # Use consistent colors based on plot index
            colors = ['blue', 'red', 'green']
            color = colors[min(plot_index, len(colors)-1)]
            pen = pg.mkPen(color=color, width=2)
            
            if plot_index == 0:
                # First plot goes to main viewbox
                plot = plot_item.plot(time_data, plot_data, pen=pen)
            elif plot_index < scale_num:
                # Get all viewboxes
                viewboxes = [item for item in plot_item.scene().items() 
                            if isinstance(item, pg.ViewBox)]
                # Sort viewboxes to ensure correct order
                viewboxes.sort(key=lambda x: x.pos().x())
                
                if plot_index < len(viewboxes):
                    plot = pg.PlotDataItem(time_data, plot_data, pen=pen)
                    viewboxes[plot_index].addItem(plot)
                else:
                    # Create new viewbox and axis if needed
                    new_vb = pg.ViewBox()
                    plot_item.scene().addItem(new_vb)
                    new_vb.setXLink(plot_item.getViewBox())
                    
                    # Create new y axis
                    axis = pg.AxisItem('right')
                    axis.setZValue(1)
                    axis.setLabel(f'Scale {plot_index+1}', color=color)
                    plot_item.layout.addItem(axis, 2, plot_index+2)
                    axis.linkToView(new_vb)
                    
                    # Add plot to new viewbox
                    plot = pg.PlotDataItem(time_data, plot_data, pen=pen)
                    new_vb.addItem(plot)
            else:
                # Additional plots go to main viewbox
                plot = plot_item.plot(time_data, plot_data, pen=pen)
            
            self.current_plots[signal_key] = plot
            
            # Update legend with correct color
            legend_item = QTreeWidgetItem(self.legend_list)
            channel_name = signal_key.split('/')[1]
            legend_item.setText(0, channel_name)
            color_box = f'<div style="background-color: {color}; width: 20px; height: 10px; border: 1px solid black;"></div>'
            legend_item.setText(1, "")
            legend_item.setData(1, Qt.DisplayRole, "")
            self.legend_list.setItemWidget(legend_item, 1, QLabel(color_box))
            
            if signal_key in self.progress_items:
                legend_item.removeChild(self.progress_items[signal_key])
                del self.progress_items[signal_key]
                
            # Update properties
            group_name, channel_name = signal_key.split('/')
            self.current_selected_signal = (group_name, channel_name)
            self.update_properties(group_name, channel_name)
            
            # Update snap selector
            self.update_snap_selector()
            
            if self.tabs.currentIndex() == 1:
                self.update_table(None, None)
                
            self.maintain_cursors()
        else:
            # Update existing plot data
            self.current_plots[signal_key].setData(time_data, plot_data)
    def update_plot_progress(self, progress):
        signal_key = self.current_worker.signal_key
        if signal_key in self.progress_items:
            self.progress_items[signal_key].setText(0, f"Loading: {progress}%")
    def update_properties(self, group_name, channel_name):
        """Update properties panel for either group or channel"""
        self.properties_widget.clear()
        try:
            if channel_name:  # Channel selected
                channel = self.current_tdms[group_name][channel_name]
                # Add signal name as first item
                signal_name = QTreeWidgetItem(self.properties_widget, [f"Signal: {group_name}/{channel_name}"])
                signal_name.setBackground(0, pg.mkColor(200, 220, 255))
                # Add basic properties
                basic_props = QTreeWidgetItem(self.properties_widget, ["Basic Properties:"])
                QTreeWidgetItem(basic_props, [f"Name: {channel_name}"])
                QTreeWidgetItem(basic_props, [f"Length: {len(channel)}"])
                QTreeWidgetItem(basic_props, [f"Data Type: {channel.dtype}"])
                # Add description if available
                if hasattr(channel, 'description'):
                    QTreeWidgetItem(basic_props, [f"Description: {channel.description}"])
                # Add custom properties
                if channel.properties:
                    props_item = QTreeWidgetItem(self.properties_widget, ["Custom Properties:"])
                    for prop, value in channel.properties.items():
                        QTreeWidgetItem(props_item, [f"{prop}: {value}"])
            else:  # Group selected
                group = self.current_tdms[group_name]
                # Add group name as first item
                group_name_item = QTreeWidgetItem(self.properties_widget, [f"Group: {group_name}"])
                group_name_item.setBackground(0, pg.mkColor(200, 220, 255))
                # Add basic group properties
                basic_props = QTreeWidgetItem(self.properties_widget, ["Basic Properties:"])
                QTreeWidgetItem(basic_props, [f"Name: {group_name}"])
                QTreeWidgetItem(basic_props, [f"Channel Count: {len(group.channels())}"])
                # Add custom properties
                if group.properties:
                    props_item = QTreeWidgetItem(self.properties_widget, ["Custom Properties:"])
                    for prop, value in group.properties.items():
                        QTreeWidgetItem(props_item, [f"{prop}: {value}"])
            # Expand all items
            self.properties_widget.expandAll()
        except Exception as e:
            print(f"Error updating properties: {e}")
    @lru_cache(maxsize=32)
    def get_cached_signal_data(self, group_name, channel_name):
        """Cache signal data for faster access"""
        if not self.current_tdms:
            return None, None
        cache_key = f"{group_name}/{channel_name}"
        if cache_key not in self.signal_cache:
            value_channel = self.current_tdms[group_name][channel_name]
            time_channel_name = f"{channel_name}_Time"
            time_channel = None
            for ch in self.current_tdms[group_name].channels():
                if ch.name.lower() == time_channel_name.lower():
                    time_channel = ch
                    break
            if time_channel:
                cache = SignalCache()
                cache.x_data = time_channel[:]
                cache.y_data = value_channel[:]
                self.signal_cache[cache_key] = cache
        return self.signal_cache.get(cache_key)
    def prepare_quick_view_data(self):
        """Prepare first N rows of data for instant display"""
        if not self.current_plots:
            return [], []
        headers = []
        quick_data = []
        data_pairs = []
        for signal_key in self.current_plots.keys():
            group, channel = signal_key.split('/')
            cache = self.get_cached_signal_data(group, channel)
            if cache:
                headers.extend([f"{channel} (X)", f"{channel} (Y)"])
                data_pairs.append((cache.x_data, cache.y_data))
        # Prepare first N rows
        max_quick_rows = min(self.table_cache.quick_view_size,
                            max(len(x_data) for x_data, y_data in data_pairs))
        for row in range(max_quick_rows):
            row_data = []
            for x_data, y_data in data_pairs:
                if row < len(x_data):
                    row_data.extend([f"{x_data[row]:.6f}", f"{y_data[row]:.6f}"])
                else:
                    row_data.extend(["", ""])
            quick_data.append(row_data)
        return headers, quick_data
    def update_table(self, group_name, channel_name):
        """Update table with at most two signals"""
        # Cancel any existing table worker
        if self.current_table_worker:
            self.current_table_worker.should_continue = False
            
        # Increment worker ID
        self.table_worker_id += 1
        current_id = self.table_worker_id
        
        # Get first two plot keys only
        current_plots = list(self.current_plots.keys())[:2]
        
        # Setup headers for at most two signals
        headers = []
        data_pairs = []
        
        for signal_key in current_plots:
            group, channel = signal_key.split('/')
            value_channel = self.current_tdms[group][channel]
            time_channel = None
            
            # Try to get mapped time channel
            mapped_time_channel = self.signal_mapper.get_x_signal(channel)
            if mapped_time_channel:
                try:
                    time_channel = self.current_tdms[group][mapped_time_channel]
                except KeyError:
                    pass
                    
            if not time_channel:
                time_channel_name = f"{channel}_Time"
                for ch in self.current_tdms[group].channels():
                    if ch.name.lower() == time_channel_name.lower():
                        time_channel = ch
                        break
                        
            if time_channel is None:
                continue
                
            headers.extend([f"{channel} Time", f"{channel} Value"])
            data_pairs.append((time_channel[:], value_channel[:], channel))

        # Setup table structure
        self.setup_table_structure(headers)
        
        # Load data if we have any
        if data_pairs:
            self.table_cache.plot_keys = set(current_plots)
            self.load_table_data(data_pairs, current_id)
    def load_table_data(self, data_pairs, worker_id):
        """Start worker to load table data"""
        if not data_pairs:
            self.is_table_loading = False
            self.table_progress.hide()
            return

        self.table_worker = TableWorker(data_pairs)
        self.current_table_worker = self.table_worker  # Store reference to current worker
        self.table_worker.worker_id = worker_id  # Assign worker ID
        
        self.table_worker.signals.chunk_ready.connect(
            lambda start_row, chunk_data, start_col: 
            self.on_incremental_chunk_ready(start_row, chunk_data, start_col, worker_id)
        )
        self.table_worker.signals.finished.connect(
            lambda: self.on_table_load_finished(worker_id)
            )
        
        self.threadpool.start(self.table_worker)
    def on_incremental_chunk_ready(self, start_row, chunk_data, start_col, worker_id):
        """Handle new data for incremental updates"""
        # Ignore updates from old workers
        if worker_id != self.table_worker_id:
            return
            
        try:
            # Ensure table has enough rows
            if self.table_widget.rowCount() <= start_row + len(chunk_data):
                self.table_widget.setRowCount(start_row + len(chunk_data))
            # Update table with chunk data
            for row_offset, row_data in enumerate(chunk_data):
                row = start_row + row_offset
                for col_offset, value in enumerate(row_data):
                    if value:  # Only set non-empty values
                        self.table_widget.setItem(row, start_col + col_offset,
                                                QTableWidgetItem(str(value)))
            # Update progress
            if self.table_cache.max_rows > 0:
                progress = min(100, (start_row / self.table_cache.max_rows) * 100)
                self.table_progress.setValue(int(progress))
        except Exception as e:
            print(f"Error in incremental update: {e}")
    def on_table_load_finished(self, worker_id):
        """Called when table data loading is complete"""
        # Only process if this is the current worker
        if worker_id == self.table_worker_id:
            self.is_table_loading = False
            self.table_cache.is_fully_loaded = True
            self.table_progress.hide()
    def on_table_scrolled(self):
        if not hasattr(self, 'last_scroll_update'):
            self.last_scroll_update = 0
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if current_time - self.last_scroll_update < 100:  # Limit updates to every 100ms
            return
        self.last_scroll_update = current_time
        visible_rect = self.table_widget.viewport().rect()
        first_visible_row = self.table_widget.rowAt(visible_rect.top())
        last_visible_row = self.table_widget.rowAt(visible_rect.bottom())
        if first_visible_row is not None and last_visible_row is not None:
            # Load a range around visible area
            start_row = max(0, first_visible_row - 500)
            self.load_cached_data_chunk(start_row, 0)
    def eventFilter(self, obj, event):
        if obj == self.signal_tree:
            if event.type() == event.KeyPress:
                if event.key() == Qt.Key_Control:
                    self.ctrl_pressed = True
                    self.signal_tree.setSelectionMode(QTreeWidget.MultiSelection)
                elif event.key() == Qt.Key_Shift:
                    self.shift_pressed = True
                    self.signal_tree.setSelectionMode(QTreeWidget.MultiSelection)
            elif event.type() == event.KeyRelease:
                if event.key() == Qt.Key_Control:
                    self.ctrl_pressed = False
                    if not self.shift_pressed:
                        self.signal_tree.setSelectionMode(QTreeWidget.SingleSelection)
                elif event.key() == Qt.Key_Shift:
                    self.shift_pressed = False
                    if not self.ctrl_pressed:
                        self.signal_tree.setSelectionMode(QTreeWidget.SingleSelection)
        return super().eventFilter(obj, event)
    def prepare_data_pairs(self, plot_keys):
        """Prepare data pairs for table loading"""
        data_pairs = []
        for signal_key in plot_keys:
            group, channel = signal_key.split('/')
            cache = self.get_cached_signal_data(group, channel)
            if cache:
                data_pairs.append((cache.x_data, cache.y_data, channel))
        return data_pairs
    def zoom_in(self):
        """Zoom in on the graph"""
        view_box = self.graph_widget.getPlotItem().getViewBox()
        # Get current ranges
        x_range, y_range = view_box.viewRange()
        x_center = (x_range[0] + x_range[1]) / 2
        y_center = (y_range[0] + y_range[1]) / 2
        x_width = (x_range[1] - x_range[0]) * 0.5
        y_width = (y_range[1] - y_range[0]) * 0.5
        # Set new ranges
        view_box.setXRange(x_center - x_width/2, x_center + x_width/2, padding=0)
        view_box.setYRange(y_center - y_width/2, y_center + y_width/2, padding=0)
    def zoom_out(self):
        """Zoom out on the graph"""
        view_box = self.graph_widget.getPlotItem().getViewBox()
        # Get current ranges
        x_range, y_range = view_box.viewRange()
        x_center = (x_range[0] + x_range[1]) / 2
        y_center = (y_range[0] + y_range[1]) / 2
        x_width = (x_range[1] - x_range[0]) * 2
        y_width = (y_range[1] - y_range[0]) * 2
        # Set new ranges
        view_box.setXRange(x_center - x_width/2, x_center + x_width/2, padding=0)
        view_box.setYRange(y_center - y_width/2, y_center + y_width/2, padding=0)
    def reset_zoom(self):
        """Reset zoom to fit all data"""
        if not self.current_plots:
            return
        # Find the overall data range
        x_min = float('inf')
        x_max = float('-inf')
        y_min = float('inf')
        y_max = float('-inf')
        for plot in self.current_plots.values():
            x_data, y_data = plot.getData()
            if len(x_data) > 0:
                x_min = min(x_min, np.min(x_data))
                x_max = max(x_max, np.max(x_data))
                y_min = min(y_min, np.min(y_data))
                y_max = max(y_max, np.max(y_data))
        if x_min != float('inf'):
            # Add small padding
            x_padding = (x_max - x_min) * 0.02
            y_padding = (y_max - y_min) * 0.02
            self.graph_widget.setXRange(x_min - x_padding, x_max + x_padding, padding=0)
            self.graph_widget.setYRange(y_min - y_padding, y_max + y_padding, padding=0)
    def toggle_cursor(self):
        """Toggle cursor visibility and functionality"""
        self.cursor_enabled = self.cursor_btn.isChecked()
        if self.cursor_enabled:
            # Create both vertical and horizontal line cursors if they don't exist
            if not self.cursor_vline:
                pen1 = pg.mkPen({
                    'color': '#FF69B4',  # hot pink color
                    'width': 4,  # increased line thickness
                    'style': Qt.PenStyle.DashLine  # dashed line
                })
                pen2 = pg.mkPen({
                    'color': '#FFA500',  # orange color
                    'width': 4,  # increased line thickness
                    'style': Qt.PenStyle.DashLine  # dashed line
                })
                # Create vertical and horizontal lines for cursor 1
                self.cursor_vline = pg.InfiniteLine(angle=90, movable=True, pen=pen1)
                self.cursor_hline = pg.InfiniteLine(angle=0, movable=True, pen=pen1)
                # Create vertical and horizontal lines for cursor 2
                self.cursor_vline2 = pg.InfiniteLine(angle=90, movable=True, pen=pen2)
                self.cursor_hline2 = pg.InfiniteLine(angle=0, movable=True, pen=pen2)
                # Set high z-values to keep cursors on top
                self.cursor_vline.setZValue(1000)
                self.cursor_hline.setZValue(1000)
                self.cursor_vline2.setZValue(1000)
                self.cursor_hline2.setZValue(1000)
                # Connect drag events for both vertical and horizontal lines
                self.cursor_vline.sigPositionChanged.connect(lambda: self.on_cursor_dragged(1))
                self.cursor_vline2.sigPositionChanged.connect(lambda: self.on_cursor_dragged(2))
                self.cursor_hline.sigPositionChanged.connect(lambda: self.on_cursor_dragged(1))
                self.cursor_hline2.sigPositionChanged.connect(lambda: self.on_cursor_dragged(2))
            # Get current view range to position cursors
            view_range = self.graph_widget.getPlotItem().viewRange()
            x_min, x_max = view_range[0]
            y_min, y_max = view_range[1]
            # Position cursors at 40% and 60% of the visible range
            x1 = x_min + (x_max - x_min) * 0.4
            x2 = x_min + (x_max - x_min) * 0.6
            # Get y values for the cursor positions
            y1 = self.get_y_value_at_x(x1)
            y2 = self.get_y_value_at_x(x2)
            # Remove existing cursors if they're already in the plot
            self.graph_widget.removeItem(self.cursor_vline)
            self.graph_widget.removeItem(self.cursor_hline)
            self.graph_widget.removeItem(self.cursor_vline2)
            self.graph_widget.removeItem(self.cursor_hline2)
            # Add cursors to the plot
            self.graph_widget.addItem(self.cursor_vline)
            self.graph_widget.addItem(self.cursor_hline)
            self.graph_widget.addItem(self.cursor_vline2)
            self.graph_widget.addItem(self.cursor_hline2)
            # Set initial positions for both vertical and horizontal lines
            self.cursor_vline.setPos(x1)
            self.cursor_hline.setPos(y1 if y1 is not None else 0)
            self.cursor_vline2.setPos(x2)
            self.cursor_hline2.setPos(y2 if y2 is not None else 0)
            # Store positions and y values
            self.cursor_positions = [x1, x2]
            self.cursor_y_values = [y1, y2]
            # Show all cursor lines
            self.cursor_vline.show()
            self.cursor_hline.show()
            self.cursor_vline2.show()
            self.cursor_hline2.show()
            # Update cursor info
            self.update_cursor_info()
            # Disconnect mouse move events since we're using drag now
            try:
                self.graph_widget.scene().sigMouseMoved.disconnect(self.cursor_moved)
            except TypeError:
                pass
        else:
            # Hide all cursor lines
            if self.cursor_vline:
                self.cursor_vline.hide()
                self.cursor_hline.hide()
                self.cursor_vline2.hide()
                self.cursor_hline2.hide()
            # Reset positions
            self.cursor_positions = [None, None]
            self.cursor_y_values = [None, None]
            self.cursor_active = 1
            # Update cursor info with default values
            self.update_cursor_info()
    def on_cursor_dragged(self, cursor_num):
        """Handle cursor drag events"""
        v_cursor = self.cursor_vline if cursor_num == 1 else self.cursor_vline2
        h_cursor = self.cursor_hline if cursor_num == 1 else self.cursor_hline2
        x_pos = v_cursor.getXPos()
        y_pos = h_cursor.getYPos()
        # Get y value at current x position
        y_val = self.get_y_value_at_x(x_pos)
        # Update horizontal line position to match the y value from the plot
        if y_val is not None:
            h_cursor.setPos(y_val)
            y_pos = y_val
        # Update stored positions
        idx = cursor_num - 1
        self.cursor_positions[idx] = x_pos
        self.cursor_y_values[idx] = y_pos
        # Update cursor info
        self.update_cursor_info()
    def cursor_moved(self, pos):
        """Handle cursor movement"""
        if not self.cursor_enabled:
            return
        # Convert position to view coordinates
        view_pos = self.graph_widget.getPlotItem().vb.mapSceneToView(pos)
        if view_pos is None:
            return
        self.update_cursor_position(view_pos.x())
    def cursor_clicked(self, event):
        """Handle cursor click to set cursor positions"""
        if not self.cursor_enabled or event.button() != Qt.LeftButton:
            return
        pos = event.scenePos()
        view_pos = self.graph_widget.getPlotItem().vb.mapSceneToView(pos)
        # Update position for active cursor
        idx = self.cursor_active - 1
        self.cursor_positions[idx] = view_pos.x()
        self.cursor_y_values[idx] = self.get_y_value_at_x(view_pos.x())
        # Switch active cursor
        self.cursor_active = 2 if self.cursor_active == 1 else 1
        self.cursor_moved(pos)
    def get_y_value_at_x(self, x):
        """Get Y value at given X coordinate from current plots"""
        closest_y = None
        min_distance = float('inf')
        for plot in self.current_plots.values():
            data = plot.getData()
            if len(data[0]) == 0:
                continue
            idx = np.searchsorted(data[0], x)
            if idx >= len(data[0]):
                idx = len(data[0]) - 1
            distance = abs(data[0][idx] - x)
            if distance < min_distance:
                min_distance = distance
                closest_y = data[1][idx]
        return closest_y
    def update_cursor_info(self):
        """Update cursor information display"""
        if None in self.cursor_positions:
            self.cursor_x_label.setText("X1: - | X2: -")
            self.cursor_y_label.setText("Y1: - | Y2: -")
            self.cursor_delta_x.setText("ΔX: -")
            self.cursor_delta_y.setText("ΔY: -")
            return
        
        x1, x2 = self.cursor_positions
        y1, y2 = self.cursor_y_values
        
        self.cursor_x_label.setText(f"X1: {self.format_si_prefix(x1)} | X2: {self.format_si_prefix(x2)}")
        self.cursor_y_label.setText(f"Y1: {self.format_si_prefix(y1)} | Y2: {self.format_si_prefix(y2)}")
        
        delta_x = abs(x2 - x1)
        delta_y = abs(y2 - y1)
        
        self.cursor_delta_x.setText(f"ΔX: {self.format_si_prefix(delta_x)}")
        self.cursor_delta_y.setText(f"ΔY: {self.format_si_prefix(delta_y)}")
    def format_si_prefix(self, value):
        """Format number with SI prefix"""
        prefixes = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        negative_prefixes = ['', 'm', 'µ', 'n', 'p', 'f', 'a', 'z', 'y']
        
        if value == 0:
            return "0"
            
        abs_value = abs(value)
        prefix_index = 0
        
        if abs_value >= 1:
            while abs_value >= 1000 and prefix_index < len(prefixes) - 1:
                abs_value /= 1000
                prefix_index += 1
            prefix = prefixes[prefix_index]
        else:
            while abs_value < 1 and prefix_index < len(negative_prefixes) - 1:
                abs_value *= 1000
                prefix_index += 1
            prefix = negative_prefixes[prefix_index]
        
        return f"{abs_value * (1 if value >= 0 else -1):.3f} {prefix}"
    def on_tab_changed(self, index):
        """Handle tab change events"""
        if index == 1:  # Table tab
            current_plots = set(self.current_plots.keys())
            # Only update table if plots have changed or table is empty
            if (current_plots != self.table_cache.plot_keys or
                self.table_widget.rowCount() == 0 or
                self.table_widget.columnCount() == 0):
                self.update_table(None, None)
            # Don't call display_cached_table() as it clears existing data
    def on_view_range_changed(self, view_box, ranges):
        """Update input boxes when view range changes"""
        try:
            # Disable text changed signals temporarily to prevent feedback loop
            self.x_min_input.blockSignals(True)
            self.x_max_input.blockSignals(True)
            self.y_min_input.blockSignals(True)
            self.y_max_input.blockSignals(True)
            # Update X range inputs
            self.x_min_input.setText(f"{ranges[0][0]:.6f}")
            self.x_max_input.setText(f"{ranges[0][1]:.6f}")
            # Update Y range inputs
            self.y_min_input.setText(f"{ranges[1][0]:.6f}")
            self.y_max_input.setText(f"{ranges[1][1]:.6f}")
        finally:
            # Re-enable signals
            self.x_min_input.blockSignals(False)
            self.x_max_input.blockSignals(False)
            self.y_min_input.blockSignals(False)
            self.y_max_input.blockSignals(False)
    def center_cursors(self):
        """Center both cursors in the current view"""
        if not self.cursor_enabled or not self.cursor_vline:
            return
        # Get current view range
        view_range = self.graph_widget.getPlotItem().viewRange()
        x_min, x_max = view_range[0]
        x_center = (x_min + x_max) / 2
        x_range = x_max - x_min
        # Position cursors at 45% and 55% of the visible range
        x1 = x_center - (x_range * 0.05)  # 5% left of center
        x2 = x_center + (x_range * 0.05)  # 5% right of center
        # Get y values for the new positions
        y1 = self.get_y_value_at_x(x1)
        y2 = self.get_y_value_at_x(x2)
        # Set cursor positions
        self.cursor_vline.setPos(x1)
        self.cursor_hline.setPos(y1 if y1 is not None else 0)
        self.cursor_vline2.setPos(x2)
        self.cursor_hline2.setPos(y2 if y2 is not None else 0)
        # Update stored positions and y values
        self.cursor_positions = [x1, x2]
        self.cursor_y_values = [y1, y2]
        # Update cursor info
        self.update_cursor_info()
    def maintain_cursors(self):
        """Ensure cursors remain visible when plots are updated"""
        if self.cursor_enabled and self.cursor_vline:
            # Remove and re-add cursors to maintain proper z-order
            self.graph_widget.removeItem(self.cursor_vline)
            self.graph_widget.removeItem(self.cursor_hline)
            self.graph_widget.removeItem(self.cursor_vline2)
            self.graph_widget.removeItem(self.cursor_hline2)
            # Re-add cursors with high z-value
            self.graph_widget.addItem(self.cursor_vline)
            self.graph_widget.addItem(self.cursor_hline)
            self.graph_widget.addItem(self.cursor_vline2)
            self.graph_widget.addItem(self.cursor_hline2)
    def load_last_directory(self):
        """Load last used directory from config file"""
        config_path = os.path.join(get_application_path(), 'tdms_viewer_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('last_directory', '')
        except (FileNotFoundError, json.JSONDecodeError):
            return ''
    def save_last_directory(self, directory):
        """Save last used directory to config file"""
        config_path = os.path.join(get_application_path(), 'tdms_viewer_config.json')
        config = {}
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        config['last_directory'] = directory
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    def on_range_changed(self, view_box, ranges):
        """Handle view range changes"""
        if not self.full_res_data:
            return
        
        x_range = ranges[0]
        
        # Update plots with appropriate resolution
        for signal_key, (x_data, y_data) in self.full_res_data.items():
            if signal_key in self.current_plots:
                visible_x, visible_y = self.get_visible_data(x_data, y_data, x_range)
                self.current_plots[signal_key].setData(visible_x, visible_y)
        
        # Update range input boxes
        self.update_range_inputs(ranges)
    def apply_manual_range(self):
        """Apply manually entered axis ranges"""
        try:
            # Get X range
            if self.x_min_input.text() and self.x_max_input.text():
                x_min = float(self.x_min_input.text())
                x_max = float(self.x_max_input.text())
                if x_min < x_max:
                    self.graph_widget.setXRange(x_min, x_max, padding=0)
            
            # Get Y range
            if self.y_min_input.text() and self.y_max_input.text():
                y_min = float(self.y_min_input.text())
                y_max = float(self.y_max_input.text())
                if y_min < y_max:
                    self.graph_widget.setYRange(y_min, y_max, padding=0)
        except ValueError:
            # Handle invalid input silently
            pass
    def on_snap_changed(self, index):
        """Handle snap selection change"""
        if index >= 0:
            signal_key = self.cursor_snap_selector.itemData(index)
            if signal_key in self.current_plots:
                self.current_snap_plot = self.current_plots[signal_key]
                # Update cursor position with new snap target
                if self.cursor_enabled and self.cursor_vline:
                    pos = self.cursor_vline.getXPos()
                    self.update_cursor_position(pos)
    def setup_table_structure(self, headers):
        """Setup table headers and basic structure"""
        self.table_widget.clear()
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        # Hide row numbers (vertical header)
        self.table_widget.verticalHeader().setVisible(False)
        # Set column widths
        for col in range(len(headers)):
            self.table_widget.setColumnWidth(col, 150)
        # Calculate max rows from current plots
        max_rows = 0
        for signal_key in self.current_plots.keys():
            group, channel = signal_key.split('/')
            cache = self.get_cached_signal_data(group, channel)
            if cache and cache.x_data is not None:
                max_rows = max(max_rows, len(cache.x_data))
        # Ensure max_rows is at least 1
        max_rows = max(1, max_rows)
        self.table_widget.setRowCount(max_rows)
        self.table_cache.max_rows = max_rows
        self.table_cache.headers = headers
    def update_snap_selector(self):
        """Update the snap selector with current plot names"""
        self.cursor_snap_selector.clear()
        for signal_key in self.current_plots.keys():
            channel = signal_key.split('/')[1]
            self.cursor_snap_selector.addItem(channel, signal_key)
        # Set first plot as default if available
        if self.current_plots:
            first_signal = next(iter(self.current_plots))
            self.current_snap_plot = self.current_plots[first_signal]
    def load_cached_data_chunk(self, start_row, chunk_index, chunk_size=1000):
        """Load cached data in chunks to prevent UI freezing"""
        if start_row >= self.table_cache.max_rows:
            return
            
        end_row = min(start_row + chunk_size, self.table_cache.max_rows)
        visible_rect = self.table_widget.viewport().rect()
        first_visible_row = self.table_widget.rowAt(visible_rect.top())
        last_visible_row = self.table_widget.rowAt(visible_rect.bottom())
        
        # Only load visible chunks and nearby rows
        if (first_visible_row is not None and
            last_visible_row is not None and
            (start_row > last_visible_row + 1000 or end_row < first_visible_row - 1000)):
            # Skip non-visible chunks
            if chunk_index * chunk_size < self.table_cache.max_rows:
                QTimer.singleShot(0, lambda: self.load_cached_data_chunk(
                    start_row + chunk_size, chunk_index + 1, chunk_size))
            return
            
        # Load the chunk
        for row in range(start_row, end_row):
            data_pairs = []
            for signal_key in self.current_plots.keys():
                group, channel = signal_key.split('/')
                cache = self.get_cached_signal_data(group, channel)
                if cache and cache.x_data is not None and row < len(cache.x_data):
                    data_pairs.extend([
                        f"{cache.x_data[row]:.6f}",
                        f"{cache.y_data[row]:.6f}"
                    ])
                else:
                    data_pairs.extend(["", ""])
                
            for col, value in enumerate(data_pairs):
                if value:  # Only set non-empty values
                    self.table_widget.setItem(row, col, QTableWidgetItem(value))
                
        # Schedule next chunk if needed
        if end_row < self.table_cache.max_rows:
            QTimer.singleShot(0, lambda: self.load_cached_data_chunk(
                end_row, chunk_index + 1, chunk_size))
    def select_signal_range(self, first_item, last_item):
        """Select all signals between first_item and last_item, regardless of direction"""
        if not first_item.parent() or not last_item.parent():
            return
            
        # Clear existing plots if ctrl isn't pressed
        if not self.ctrl_pressed:
            self.graph_widget.clear()
            self.current_plots.clear()
            self.legend_list.clear()
            self.selection_order = 0
            self.signal_tree.clearSelection()
            
        # Get all items in the tree
        all_tree_items = []
        def collect_all_items(root):
            for i in range(root.childCount()):
                group = root.child(i)
                for j in range(group.childCount()):
                    item = group.child(j)
                    all_tree_items.append(item)
                    
        collect_all_items(self.signal_tree.invisibleRootItem())
        
        # Find indices of first and last items
        first_idx = all_tree_items.index(first_item)
        last_idx = all_tree_items.index(last_item)
        
        # Determine range based on which index is smaller
        start_idx = min(first_idx, last_idx)
        end_idx = max(first_idx, last_idx)
        
        # Select and plot all items in range
        for idx in range(start_idx, end_idx + 1):
            item = all_tree_items[idx]
            item.setSelected(True)
            group_name = item.parent().text(0)
            channel_name = item.text(0)
            signal_key = f"{group_name}/{channel_name}"
            if signal_key not in self.current_plots:
                self.plot_channel(group_name, channel_name)
            
        # Update properties for the last clicked item
        self.current_selected_signal = (last_item.parent().text(0), last_item.text(0))
        self.update_properties(*self.current_selected_signal)
        
        # Update table
        self.table_cache.plot_keys = set()
        self.update_table(None, None)
    def update_scales(self, scale_text):
        """Update the number of y-axes based on selection"""
        num_scales = int(scale_text[0])  # Extract number from "X Scale"
        
        # Get number of selected signals
        selected_count = len(self.signal_tree.selectedItems())
        
        # Adjust num_scales if it's greater than selected signals
        if num_scales > selected_count:
            num_scales = selected_count
            self.scale_selector.setCurrentText(f"{num_scales} Scale")
            return  # Return as setCurrentText will trigger this method again
        
        # Keep track of original plots
        original_plots = self.current_plots.copy()
        if not original_plots:
            return
            
        # Clear existing plots and viewboxes
        self.graph_widget.clear()
        self.legend_list.clear()
        self.current_plots.clear()
        
        # Get the plot item
        plot_item = self.graph_widget.getPlotItem()
        
        # Remove any existing right axes
        for ax in plot_item.scene().items():
            if isinstance(ax, pg.AxisItem) and ax.orientation == 'right':
                plot_item.scene().removeItem(ax)
        
        # Main viewbox (always exists)
        main_vb = plot_item.getViewBox()
        main_vb.setYLink(None)  # Unlink from any previous links
        
        # Colors for different axes
        colors = ['blue', 'red']  # Removed green since we only need 2 colors now
        
        # Get list of plots to process
        plot_items = list(original_plots.items())[:2]  # Limit to 2 plots
        if not plot_items:
            return
            
        # First pass: Plot first signal and get its range for scaling reference
        first_signal = plot_items[0]
        x_data, y_data = first_signal[1].getData()
        pen = pg.mkPen(color=colors[0], width=2)
        plot = plot_item.plot(x_data, y_data, pen=pen)
        self.current_plots[first_signal[0]] = plot
        
        # Get the main range after plotting first signal
        main_vb.enableAutoRange()
        main_range = main_vb.viewRange()[1]
        
        # Second pass: Plot remaining signal with proper scaling
        if len(plot_items) > 1:
            signal_key, plot_data = plot_items[1]
            x_data, y_data = plot_data.getData()
            pen = pg.mkPen(color=colors[1], width=2)
            
            # Calculate y-range for this signal
            y_min, y_max = np.nanmin(y_data), np.nanmax(y_data)
            padding = (y_max - y_min) * 0.1
            y_min -= padding
            y_max += padding
            
            # Create new y axis
            axis = pg.AxisItem('right')
            axis.setZValue(1)
            axis.setLabel('Scale 2', color=colors[1])
            plot_item.layout.addItem(axis, 2, 3)
            axis.setRange(y_min, y_max)
            
            # Scale the data to match the main viewbox range
            scale_factor = (main_range[1] - main_range[0]) / (y_max - y_min)
            offset = main_range[0] - y_min * scale_factor
            scaled_data = y_data * scale_factor + offset
            
            # Create plot in main viewbox
            plot = plot_item.plot(x_data, scaled_data, pen=pen)
            self.current_plots[signal_key] = plot
        
        # Update legend for all signals
        for i, (signal_key, _) in enumerate(plot_items):
            legend_item = QTreeWidgetItem(self.legend_list)
            channel_name = signal_key.split('/')[1]
            legend_item.setText(0, channel_name)
            color_box = f'<div style="background-color: {colors[i]}; width: 20px; height: 10px; border: 1px solid black;"></div>'
            legend_item.setText(1, "")
            legend_item.setData(1, Qt.DisplayRole, "")
            self.legend_list.setItemWidget(legend_item, 1, QLabel(color_box))
            legend_item.setBackground(0, pg.mkColor(200, 220, 255))
        
        # Final autorange to ensure everything is visible
        main_vb.enableAutoRange()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Update app icon loading
    icon_path_ico = os.path.join(get_application_path(), 'TDMS viewer icon.ico')
    
    if os.path.exists(icon_path_ico):
        app.setWindowIcon(QIcon(icon_path_ico))
        
    viewer = TDMSViewer()
    viewer.show()
    sys.exit(app.exec())