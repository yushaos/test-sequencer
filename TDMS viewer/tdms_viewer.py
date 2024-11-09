import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton,
                            QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
                            QLineEdit, QFileDialog, QGroupBox, QProgressBar, QComboBox)
from PyQt6.QtCore import Qt, QMimeData, QRunnable, QThreadPool, pyqtSignal, QObject, QTimer, QTime, QThread
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPen
from nptdms import TdmsFile
import pyqtgraph as pg
import numpy as np
from collections import defaultdict
from functools import lru_cache
from math import ceil
import json
import os
class WorkerSignals(QObject):
    finished = pyqtSignal(str, object, object, str)  # signal_key, plot_data, time_data, color
class PlotWorkerSignals(QObject):
    chunk_ready = pyqtSignal(str, object, object, str, bool)  # signal_key, y_data, x_data, color, is_final
    progress = pyqtSignal(int)  # Progress percentage
class PlotWorker(QRunnable):
    def __init__(self, signal_key, value_channel, time_channel, color):
        super().__init__()
        self.signal_key = signal_key
        self.value_channel = value_channel
        self.time_channel = time_channel
        self.color = color
        self.signals = PlotWorkerSignals()
        self.should_continue = True
        self.CHUNK_SIZE = 500_000
    def run(self):
        try:
            total_points = len(self.value_channel)
            num_chunks = ceil(total_points / self.CHUNK_SIZE)
            for chunk_idx in range(num_chunks):
                if not self.should_continue:
                    return
                start_idx = chunk_idx * self.CHUNK_SIZE
                end_idx = min((chunk_idx + 1) * self.CHUNK_SIZE, total_points)
                y_data = self.value_channel[start_idx:end_idx]
                x_data = self.time_channel[start_idx:end_idx]
                is_final = chunk_idx == num_chunks - 1
                self.signals.chunk_ready.emit(self.signal_key, y_data, x_data, self.color, is_final)
                # Emit progress
                progress = int((chunk_idx + 1) / num_chunks * 100)
                self.signals.progress.emit(progress)
                # Small delay to keep GUI responsive
                QThread.msleep(1)
        except Exception as e:
            print(f"Error in PlotWorker: {e}")
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
            # Use numpy for faster data processing
            chunks = []
            for x_data, y_data, _ in self.data_pairs:
                x_arr = np.array(x_data)
                y_arr = np.array(y_data)
                chunks.append((x_arr, y_arr))
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
        """Process data chunk using numpy for better performance"""
        end_row = min(start_row + self.chunk_size, max(len(x) for x, _ in chunks))
        chunk_data = []
        for row in range(start_row, end_row):
            row_data = []
            for x_arr, y_arr in chunks:
                if row < len(x_arr):
                    row_data.extend([f"{x_arr[row]:.6f}", f"{y_arr[row]:.6f}"])
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
        config_path = os.path.join(os.path.dirname(__file__), 'tdms_viewer_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.mapping = {item['y']: item['x'] for item in config['signal_pairs']}
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load signal mapping config: {e}")
            self.mapping = {}
    
    def get_x_signal(self, y_signal):
        """Get the corresponding x signal for a y signal"""
        return self.mapping.get(y_signal)
class TDMSViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TDMS Viewer")
        self.setWindowState(Qt.WindowState.WindowMaximized)
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
        self.signal_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
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
        self.table_widget.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
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
        file_name, _ = QFileDialog.getOpenFileName(self, "Open TDMS File", "", "TDMS Files (*.tdms)")
        if file_name:
            self.load_tdms_file(file_name)
    def load_tdms_file(self, file_path):
        self.file_location.setText(file_path)
        self.current_tdms = TdmsFile.read(file_path)
        self.legend_list.clear()
        self.graph_widget.clear()
        self.current_plots.clear()
        self.color_index = 0  # Reset color index
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
        if not item.parent():  # Skip if it's a group
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
            # Check if we're selecting the same single signal that's already displayed
            if (len(self.current_plots) == 1 and
                list(self.current_plots.keys())[0] == signal_key):
                # Same signal, no need to update anything
                return
            self.graph_widget.clear()
            self.current_plots.clear()
            self.legend_list.clear()
            self.selection_order = 0  # Reset selection order counter
        # Plot the selected signal
        if signal_key not in self.current_plots:
            self.plot_channel(group_name, channel_name)
        # Update properties
        self.current_selected_signal = (group_name, channel_name)
        self.update_properties(group_name, channel_name)
        # Force table update for both single and multi-selection
        self.table_cache.plot_keys = set()  # Force cache invalidation
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
            
            # Add to legend
            legend_item = QTreeWidgetItem(self.legend_list)
            channel_name = signal_key.split('/')[1]
            legend_item.setText(0, channel_name)
            color_box = f'<div style="background-color: {color}; width: 20px; height: 10px; border: 1px solid black;"></div>'
            legend_item.setText(1, "")
            legend_item.setData(1, Qt.ItemDataRole.DisplayRole, "")
            self.legend_list.setItemWidget(legend_item, 1, QLabel(color_box))
            legend_item.setBackground(0, pg.mkColor(200, 220, 255))
            
            # Add progress item
            progress_item = QTreeWidgetItem(legend_item)
            progress_item.setText(0, "Loading: 0%")
            self.progress_items[signal_key] = progress_item
    def plot_chunk_finished(self, signal_key, plot_data, time_data, color, is_final):
        if signal_key not in self.current_plots:
            # First chunk - create new plot
            pen = pg.mkPen(color=color, width=2)
            plot = self.graph_widget.plot(time_data, plot_data, pen=pen)
            self.current_plots[signal_key] = plot
            # Update snap selector if this is the first plot
            if len(self.current_plots) == 1:
                self.current_snap_plot = plot
        else:
            # Append data to existing plot
            current_plot = self.current_plots[signal_key]
            existing_data = current_plot.getData()
            new_x = np.concatenate([existing_data[0], time_data])
            new_y = np.concatenate([existing_data[1], plot_data])
            current_plot.setData(new_x, new_y)
        if is_final:
            # Remove progress indicator from legend
            if signal_key in self.progress_items:
                legend_item = self.progress_items[signal_key].parent()
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
    def update_plot_progress(self, progress):
        signal_key = self.current_worker.signal_key
        if signal_key in self.progress_items:
            self.progress_items[signal_key].setText(0, f"Loading: {progress}%")
    def update_properties(self, group_name, channel_name):
        self.properties_widget.clear()
        channel = self.current_tdms[group_name][channel_name]
        # Add signal name as first item
        signal_name = QTreeWidgetItem(self.properties_widget, [f"Signal: {group_name}/{channel_name}"])
        signal_name.setBackground(0, pg.mkColor(200, 220, 255))
        # Add properties
        props_item = QTreeWidgetItem(self.properties_widget, ["Properties:"])
        for prop, value in channel.properties.items():
            QTreeWidgetItem(props_item, [f"{prop}: {value}"])
        # Expand all items
        self.properties_widget.expandAll()
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
        if self.is_table_loading and hasattr(self, 'table_worker'):
            self.table_worker.should_continue = False
        # Get current plot keys
        current_plots = set(self.current_plots.keys())
        # If the plots haven't changed and table is already populated, skip update
        if (current_plots == self.table_cache.plot_keys and
            self.table_widget.rowCount() > 0 and
            self.table_widget.columnCount() > 0):
            return
        self.is_table_loading = True
        self.table_progress.show()
        self.table_progress.setValue(0)
        # Clear table if no plots exist
        if not current_plots:
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            self.is_table_loading = False
            self.table_progress.hide()
            return
        # Setup headers
        headers = []
        for signal_key in current_plots:
            channel = signal_key.split('/')[1]
            headers.extend([f"{channel} (X)", f"{channel} (Y)"])
        # Setup table structure
        self.setup_table_structure(headers)
        # Prepare and load data
        data_pairs = self.prepare_data_pairs(current_plots)
        if data_pairs:
            self.table_cache.plot_keys = current_plots
            self.load_table_data(data_pairs)
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
            if event.type() == event.Type.KeyPress:
                if event.key() == Qt.Key.Key_Control:
                    self.ctrl_pressed = True
                    self.signal_tree.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
                elif event.key() == Qt.Key.Key_Shift:
                    self.shift_pressed = True
                    self.signal_tree.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
            elif event.type() == event.Type.KeyRelease:
                if event.key() == Qt.Key.Key_Control:
                    self.ctrl_pressed = False
                    if not self.shift_pressed:
                        self.signal_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
                elif event.key() == Qt.Key.Key_Shift:
                    self.shift_pressed = False
                    if not self.ctrl_pressed:
                        self.signal_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
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
    def load_table_data(self, data_pairs):
        """Start worker to load table data"""
        if not data_pairs:
            self.is_table_loading = False
            self.table_progress.hide()
            return
        self.table_worker = TableWorker(data_pairs)
        self.table_worker.signals.chunk_ready.connect(self.on_incremental_chunk_ready)
        self.table_worker.signals.finished.connect(self.on_table_load_finished)
        self.threadpool.start(self.table_worker)
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
    def on_incremental_chunk_ready(self, start_row, chunk_data, start_col):
        """Handle new data for incremental updates"""
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
                    'color': 'k',  # black color
                    'width': 2,
                    'style': Qt.PenStyle.DashLine  # dashed line
                })
                pen2 = pg.mkPen({
                    'color': '#006400',  # dark green color
                    'width': 2,
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
        if not self.cursor_enabled or event.button() != Qt.MouseButton.LeftButton:
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
        self.cursor_x_label.setText(f"X1: {x1:.6f} | X2: {x2:.6f}")
        self.cursor_y_label.setText(f"Y1: {y1:.6f} | Y2: {y2:.6f}")
        delta_x = abs(x2 - x1)
        delta_y = abs(y2 - y1)
        self.cursor_delta_x.setText(f"ΔX: {delta_x:.6f}")
        self.cursor_delta_y.setText(f"ΔY: {delta_y:.6f}")
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
    def on_table_load_finished(self):
        """Called when table data loading is complete"""
        self.is_table_loading = False
        self.table_cache.is_fully_loaded = True
        self.table_progress.hide()
    def load_cached_data_chunk(self, start_row, chunk_index, chunk_size=1000):
        """Load cached data in chunks to prevent UI freezing"""
        if not self.table_cache.full_data or start_row >= self.table_cache.max_rows:
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
    def display_cached_table(self):
        """Display cached table data"""
        if not self.table_cache.headers:
            return
        # Only setup table if it's empty
        if self.table_widget.rowCount() == 0 or self.table_widget.columnCount() == 0:
            self.table_widget.setColumnCount(len(self.table_cache.headers))
            self.table_widget.setHorizontalHeaderLabels(self.table_cache.headers)
            self.table_widget.verticalHeader().setVisible(False)  # Hide row numbers
            # Set column widths
            for col in range(len(self.table_cache.headers)):
                self.table_widget.setColumnWidth(col, 150)
            # Calculate max rows from current plots
            max_rows = 0
            for signal_key in self.current_plots.keys():
                group, channel = signal_key.split('/')
                cache = self.get_cached_signal_data(group, channel)
                if cache and cache.x_data is not None:
                    max_rows = max(max_rows, len(cache.x_data))
            # Set row count
            self.table_widget.setRowCount(max_rows)
            # Load initial visible data
            visible_rect = self.table_widget.viewport().rect()
            first_visible_row = self.table_widget.rowAt(visible_rect.top())
            last_visible_row = self.table_widget.rowAt(visible_rect.bottom())
            if first_visible_row is not None and last_visible_row is not None:
                start_row = max(0, first_visible_row - 500)
                self.load_cached_data_chunk(start_row, 0)
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
    def toggle_zoom(self):
        """Toggle between pan mode and zoom mode"""
        view_box = self.graph_widget.getPlotItem().getViewBox()
        is_zoom_mode = self.zoom_btn.isChecked()
        if is_zoom_mode:
            # Enable zoom mode
            view_box.setMouseMode(pg.ViewBox.RectMode)
            view_box.setMouseEnabled(x=True, y=True)  # Allow both x and y zooming
        else:
            # Pan Mode
            view_box.setMouseMode(pg.ViewBox.PanMode)
            view_box.setMouseEnabled(x=True, y=False)  # Only allow x-axis panning
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
    def on_snap_changed(self, index):
        """Handle snap selection change"""
        if index >= 0:
            signal_key = self.cursor_snap_selector.itemData(index)
            self.current_snap_plot = self.current_plots[signal_key]
            # Update cursor position with new snap target
            if self.cursor_enabled and self.cursor_vline:
                pos = self.cursor_vline.getXPos()
                self.update_cursor_position(pos)
    def update_cursor_position(self, x_pos):
        """Update cursor position with snapping to selected plot"""
        if not self.current_snap_plot:
            return
        # Get data from current snap target
        data = self.current_snap_plot.getData()
        if len(data[0]) == 0:
            return
        # Find closest x index
        idx = np.searchsorted(data[0], x_pos)
        if idx >= len(data[0]):
            idx = len(data[0]) - 1
        # Snap to exact x position from data
        snap_x = data[0][idx]
        snap_y = data[1][idx]
        # Update position for active cursor
        cursor = self.cursor_vline if self.cursor_active == 1 else self.cursor_vline2
        cursor.setPos(snap_x)
        # Store positions temporarily for hover preview
        temp_positions = list(self.cursor_positions)
        temp_y_values = list(self.cursor_y_values)
        temp_positions[self.cursor_active - 1] = snap_x
        temp_y_values[self.cursor_active - 1] = snap_y
        # Update cursor info with temporary values
        x1_text = f"{temp_positions[0]:.6f}" if temp_positions[0] is not None else "-"
        x2_text = f"{temp_positions[1]:.6f}" if temp_positions[1] is not None else "-"
        y1_text = f"{temp_y_values[0]:.6f}" if temp_y_values[0] is not None else "-"
        y2_text = f"{temp_y_values[1]:.6f}" if temp_y_values[1] is not None else "-"
        self.cursor_x_label.setText(f"X1: {x1_text} | X2: {x2_text}")
        self.cursor_y_label.setText(f"Y1: {y1_text} | Y2: {y2_text}")
        if all(pos is not None for pos in temp_positions):
            delta_x = abs(temp_positions[1] - temp_positions[0])
            delta_y = abs(temp_y_values[1] - temp_y_values[0])
            self.cursor_delta_x.setText(f"ΔX: {delta_x:.6f}")
            self.cursor_delta_y.setText(f"ΔY: {delta_y:.6f}")
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
if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = TDMSViewer()
    viewer.show()
    sys.exit(app.exec())