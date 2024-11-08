import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, 
                            QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
                            QLineEdit, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt, QMimeData, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from nptdms import TdmsFile
import pyqtgraph as pg
import numpy as np

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

        # Add tab changed connection
        self.tabs.currentChanged.connect(self.on_tab_changed)

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

    def update_table(self, group_name, channel_name):
        # Clear existing table
        self.table_widget.clear()
        
        # If no plots exist, return
        if not self.current_plots:
            return
        
        # Calculate total columns needed (2 columns per signal)
        total_columns = len(self.current_plots) * 2
        self.table_widget.setColumnCount(total_columns)
        
        # Hide row numbers
        self.table_widget.verticalHeader().setVisible(False)
        
        # Enable horizontal scrollbar
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set column headers and widths
        column_index = 0
        max_rows = 0
        data_pairs = []
        
        # Collect data from all plotted signals
        for signal_key in self.current_plots.keys():
            group, channel = signal_key.split('/')
            value_channel = self.current_tdms[group][channel]
            
            # Find corresponding time channel
            time_channel = None
            time_channel_name = f"{channel}_Time"
            for ch in self.current_tdms[group].channels():
                if ch.name.lower() == time_channel_name.lower():
                    time_channel = ch
                    break
            
            if time_channel:
                x_data = time_channel[:]
                y_data = value_channel[:]
                data_pairs.append((x_data, y_data, channel))
                max_rows = max(max_rows, len(y_data))
        
        # Set up headers and data
        headers = []
        for _, _, channel in data_pairs:
            headers.extend([f"{channel} (X)", f"{channel} (Y)"])
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        for col in range(total_columns):
            self.table_widget.setColumnWidth(col, 150)  # Set width to 150 pixels
        
        # Fill data
        self.table_widget.setRowCount(max_rows)
        for row in range(max_rows):
            for col, (x_data, y_data, _) in enumerate(data_pairs):
                if row < len(x_data):
                    x_item = QTableWidgetItem(f"{x_data[row]:.6f}")
                    y_item = QTableWidgetItem(f"{y_data[row]:.6f}")
                    self.table_widget.setItem(row, col*2, x_item)
                    self.table_widget.setItem(row, col*2+1, y_item)

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
        # Update table when switching to table tab
        if index == 1:  # Table tab
            self.update_table(None, None)  # Pass None to indicate we just want to refresh current plots

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = TDMSViewer()
    viewer.show()
    sys.exit(app.exec()) 