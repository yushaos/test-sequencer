import sys

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 

                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, 

                            QLabel, QTabWidget, QTableWidget, QTableWidgetItem,

                            QLineEdit, QFileDialog, QGroupBox, QProgressBar)

from PyQt6.QtCore import Qt, QMimeData, QRunnable, QThreadPool, pyqtSignal, QObject, QTimer, QTime, QThread

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

            # Use selection order for color instead of tree position

            color = self.colors[self.selection_order % len(self.colors)]

            self.selection_order += 1

            

            # Modified worker to pass both channels

            worker = PlotWorker(signal_key, value_channel, time_channel, color)

            worker.signals.finished.connect(self.plot_finished)

            

            self.threadpool.start(worker)

            

            # Add to legend

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

            elif event.type() == event.Type.KeyRelease:

                if event.key() == Qt.Key.Key_Control:

                    self.ctrl_pressed = False

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
        view_box = self.graph_widget.getViewBox()
        view_box.scaleBy((0.5, 0.5))

    def zoom_out(self):
        """Zoom out on the graph"""
        view_box = self.graph_widget.getViewBox()
        view_box.scaleBy((2, 2))

    def reset_zoom(self):
        """Reset zoom to fit all data"""
        view_box = self.graph_widget.getViewBox()
        view_box.autoRange()

    def toggle_cursor(self):
        """Toggle cursor visibility"""
        # Implementation for cursor functionality
        pass

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



if __name__ == '__main__':

    app = QApplication(sys.argv)

    viewer = TDMSViewer()

    viewer.show()

    sys.exit(app.exec()) 
