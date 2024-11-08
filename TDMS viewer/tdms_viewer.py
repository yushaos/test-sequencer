import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, 
                            QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
                            QLineEdit, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt, QMimeData, QRunnable, QThreadPool, pyqtSignal, QObject, QTimer, QTime
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from nptdms import TdmsFile
import pyqtgraph as pg
import numpy as np
from collections import defaultdict
from functools import lru_cache

class WorkerSignals(QObject):
    finished = pyqtSignal(str, object, object, str)  # signal_key, plot_data, time_data, color

class PlotWorker(QRunnable):
    def __init__(self, signal_key, value_channel, time_channel, color):
        super().__init__()
        self.signal_key = signal_key
        self.value_channel = value_channel
        self.time_channel = time_channel
        self.color = color
        self.signals = WorkerSignals()

    def run(self):
        y_data = self.value_channel[:]
        x_data = self.time_channel[:]
        self.signals.finished.emit(self.signal_key, y_data, x_data, self.color)

class TableWorkerSignals(QObject):
    chunk_ready = pyqtSignal(int, list)  # start_row, chunk_data
    finished = pyqtSignal()

class TableWorker(QRunnable):
    def __init__(self, data_pairs, chunk_size=1000):
        super().__init__()
        self.data_pairs = data_pairs
        self.chunk_size = chunk_size
        self.signals = TableWorkerSignals()

    def run(self):
        max_rows = max(len(x_data) for x_data, y_data, _ in self.data_pairs)
        current_row = 0
        
        while current_row < max_rows:
            chunk_data = []
            end_row = min(current_row + self.chunk_size, max_rows)
            
            for row in range(current_row, end_row):
                row_data = []
                for x_data, y_data, _ in self.data_pairs:
                    if row < len(x_data):
                        row_data.extend([f"{x_data[row]:.6f}", f"{y_data[row]:.6f}"])
                    else:
                        row_data.extend(["", ""])
                chunk_data.append(row_data)
            
            self.signals.chunk_ready.emit(current_row, chunk_data)
            current_row = end_row
        
        self.signals.finished.emit()

class TableCache:
    def __init__(self):
        self.headers = []
        self.quick_view_data = []  # First N rows for instant display
        self.full_data = []
        self.plot_keys = set()
        self.max_rows = 0
        self.quick_view_size = 1000  # Increased for smoother scrolling
        self.is_fully_loaded = False  # Track if full data is loaded

class SignalCache:
    def __init__(self):
        self.x_data = None
        self.y_data = None

class TDMSViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TDMS Viewer")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Left panel (Signal Names)
        left_panel = QGroupBox("Signal Names")
        left_layout = QVBoxLayout(left_panel)
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
        zoom_in_btn = QPushButton("🔍+ Zoom In")
        zoom_out_btn = QPushButton("🔍- Zoom Out")
        reset_btn = QPushButton("↺ Reset")
        cursor_btn = QPushButton("👆 Cursor On/Off")
        
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn.clicked.connect(self.zoom_out)
        reset_btn.clicked.connect(self.reset_zoom)
        cursor_btn.clicked.connect(self.toggle_cursor)
        
        toolbar_layout.addWidget(zoom_in_btn)
        toolbar_layout.addWidget(zoom_out_btn)
        toolbar_layout.addWidget(reset_btn)
        toolbar_layout.addWidget(cursor_btn)
        toolbar_layout.addStretch()
        
        center_layout.addWidget(toolbar)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
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
        if item.parent():  # It's a channel
            group_name = item.parent().text(0)
            channel_name = item.text(0)
            signal_key = f"{group_name}/{channel_name}"
            
            self.current_selected_signal = (group_name, channel_name)
            
            if signal_key in self.current_plots:
                # Unplot if already plotted
                self.graph_widget.removeItem(self.current_plots[signal_key])
                del self.current_plots[signal_key]
                
                # Remove from legend
                for i in range(self.legend_list.topLevelItemCount()):
                    if self.legend_list.topLevelItem(i).text(0) == signal_key:
                        self.legend_list.takeTopLevelItem(i)
                        break
            else:
                # Plot if not already plotted
                self.plot_channel(group_name, channel_name)
                
            # Update properties regardless of plot status
            self.update_properties(group_name, channel_name)
            self.update_table(group_name, channel_name)

    def plot_channel(self, group_name, channel_name):
        # Get both value and time channels
        value_channel = self.current_tdms[group_name][channel_name]
        time_channel_name = f"{channel_name}_Time"
        
        # Try case-insensitive match for time channel
        time_channel = None
        for ch in self.current_tdms[group_name].channels():
            if ch.name.lower() == time_channel_name.lower():
                time_channel = ch
                break
        
        if not time_channel:
            print(f"Warning: No time channel found for {channel_name}")
            return
        
        signal_key = f"{group_name}/{channel_name}"
        
        if signal_key not in self.current_plots:
            # Get signal's position in the tree for consistent color
            group_item = None
            for i in range(self.signal_tree.topLevelItemCount()):
                if self.signal_tree.topLevelItem(i).text(0) == group_name:
                    group_item = self.signal_tree.topLevelItem(i)
                    break
            
            signal_position = 0
            if group_item:
                for i in range(group_item.childCount()):
                    if group_item.child(i).text(0) == channel_name:
                        signal_position = i
                        break
            
            color = self.colors[signal_position % len(self.colors)]
            
            # Modified worker to pass both channels
            worker = PlotWorker(signal_key, value_channel, time_channel, color)
            worker.signals.finished.connect(self.plot_finished)
            
            self.threadpool.start(worker)
            
            # Add to legend as before...
            legend_item = QTreeWidgetItem(self.legend_list)
            legend_item.setText(0, signal_key)
            legend_item.setText(1, color.capitalize())
            legend_item.setBackground(0, pg.mkColor(200, 220, 255))
            legend_item.setBackground(1, pg.mkColor(200, 220, 255))

    def plot_finished(self, signal_key, plot_data, time_data, color):
        if signal_key not in self.current_plots:
            pen = pg.mkPen(color=color, width=2)
            plot = self.graph_widget.plot(time_data, plot_data, pen=pen)
            self.current_plots[signal_key] = plot
            
            # Update properties for the newly plotted signal
            group_name, channel_name = signal_key.split('/')
            self.current_selected_signal = (group_name, channel_name)
            self.update_properties(group_name, channel_name)
            
            # Update table if we're on the table tab
            if self.tabs.currentIndex() == 1:
                self.update_table(None, None)

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
        if self.is_table_loading:
            return
        
        self.is_table_loading = True
        
        # First, display quick view data
        headers, quick_data = self.prepare_quick_view_data()
        if not headers:
            self.is_table_loading = False
            return
        
        # Setup table with quick view data
        self.table_widget.clear()
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set column widths
        for col in range(len(headers)):
            self.table_widget.setColumnWidth(col, 150)
        
        # Display quick view data immediately
        self.table_widget.setRowCount(len(quick_data))
        for row, row_data in enumerate(quick_data):
            for col, value in enumerate(row_data):
                if value:
                    self.table_widget.setItem(row, col, QTableWidgetItem(value))
        
        # Update cache
        self.table_cache.headers = headers
        self.table_cache.quick_view_data = quick_data
        self.table_cache.plot_keys = set(self.current_plots.keys())
        
        # Prepare data pairs for full loading
        data_pairs = []
        for signal_key in self.current_plots.keys():
            group, channel = signal_key.split('/')
            cache = self.get_cached_signal_data(group, channel)
            if cache:
                data_pairs.append((cache.x_data, cache.y_data, channel))
        
        # Start worker for full data loading
        self.table_worker = TableWorker(data_pairs)
        self.table_worker.signals.chunk_ready.connect(self.on_table_chunk_ready)
        self.table_worker.signals.finished.connect(self.on_table_load_finished)
        
        # Set full row count
        max_rows = max(len(x_data) for x_data, y_data, _ in data_pairs)
        self.table_widget.setRowCount(max_rows)
        self.table_cache.max_rows = max_rows
        
        self.threadpool.start(self.table_worker)

    def on_table_chunk_ready(self, start_row, chunk_data):
        # Update table widget with new chunk only if visible
        if self.tabs.currentIndex() == 1:
            for row_offset, row_data in enumerate(chunk_data):
                row = start_row + row_offset
                for col, value in enumerate(row_data):
                    if value:
                        self.table_widget.setItem(row, col, QTableWidgetItem(value))
        
        # Always update cache
        while len(self.table_cache.full_data) <= start_row:
            self.table_cache.full_data.append([])
        self.table_cache.full_data[start_row:start_row + len(chunk_data)] = chunk_data

    def on_table_load_finished(self):
        self.is_table_loading = False
        self.table_cache.is_fully_loaded = True

    def zoom_in(self):
        self.graph_widget.getViewBox().scaleBy((0.5, 0.5))

    def zoom_out(self):
        self.graph_widget.getViewBox().scaleBy((2, 2))

    def reset_zoom(self):
        self.graph_widget.getViewBox().autoRange()

    def toggle_cursor(self):
        # Implementation for cursor functionality
        pass

    def on_tab_changed(self, index):
        if index == 1:  # Table tab
            current_plots = set(self.current_plots.keys())
            if current_plots != self.table_cache.plot_keys:
                # Plots have changed, need to recalculate
                self.update_table(None, None)
            else:
                # Use cached data if available
                self.display_cached_table()

    def display_cached_table(self):
        if not self.table_cache.headers:
            return
        
        # Setup table
        self.table_widget.clear()
        self.table_widget.setColumnCount(len(self.table_cache.headers))
        self.table_widget.setHorizontalHeaderLabels(self.table_cache.headers)
        self.table_widget.setRowCount(self.table_cache.max_rows)
        self.table_widget.verticalHeader().setVisible(False)
        
        # Set column widths
        for col in range(len(self.table_cache.headers)):
            self.table_widget.setColumnWidth(col, 150)
        
        # Display quick view data immediately
        for row, row_data in enumerate(self.table_cache.quick_view_data):
            for col, value in enumerate(row_data):
                if value:
                    self.table_widget.setItem(row, col, QTableWidgetItem(value))
        
        # If full data is cached, load it in chunks using a timer
        if self.table_cache.is_fully_loaded and self.table_cache.full_data:
            self.load_cached_data_chunk(len(self.table_cache.quick_view_data), 0)

    def load_cached_data_chunk(self, start_row, chunk_index, chunk_size=1000):
        """Load cached data in chunks to prevent UI freezing"""
        if not self.table_cache.full_data or start_row >= len(self.table_cache.full_data):
            return
        
        end_row = min(start_row + chunk_size, len(self.table_cache.full_data))
        visible_rect = self.table_widget.viewport().rect()
        first_visible_row = self.table_widget.rowAt(visible_rect.top())
        last_visible_row = self.table_widget.rowAt(visible_rect.bottom())
        
        # Only load visible chunks and nearby rows
        if (first_visible_row is not None and 
            last_visible_row is not None and 
            (start_row > last_visible_row + 1000 or end_row < first_visible_row - 1000)):
            # Skip non-visible chunks
            if chunk_index * chunk_size < len(self.table_cache.full_data):
                QTimer.singleShot(0, lambda: self.load_cached_data_chunk(
                    start_row + chunk_size, chunk_index + 1, chunk_size))
            return
        
        # Load the chunk
        for row in range(start_row, end_row):
            row_data = self.table_cache.full_data[row]
            for col, value in enumerate(row_data):
                if value:
                    self.table_widget.setItem(row, col, QTableWidgetItem(value))
        
        # Schedule next chunk
        if end_row < len(self.table_cache.full_data):
            QTimer.singleShot(0, lambda: self.load_cached_data_chunk(
                end_row, chunk_index + 1, chunk_size))

    # Add this method to handle scrolling
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = TDMSViewer()
    viewer.show()
    sys.exit(app.exec()) 