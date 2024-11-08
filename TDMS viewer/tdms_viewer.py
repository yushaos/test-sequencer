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
    def __init__(self, signal_key, channel, color):
        super().__init__()
        self.signal_key = signal_key
        self.channel = channel
        self.color = color
        self.signals = WorkerSignals()

    def run(self):
        data = self.channel[:]
        time = np.arange(len(data))
        self.signals.finished.emit(self.signal_key, data, time, self.color)

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
                channel_item = QTreeWidgetItem([channel.name])
                group_item.addChild(channel_item)

    def on_signal_selected(self, item, column):
        if item.parent():  # It's a channel
            group_name = item.parent().text(0)
            channel_name = item.text(0)
            signal_key = f"{group_name}/{channel_name}"
            
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
                self.update_properties(group_name, channel_name)
                self.update_table(group_name, channel_name)

    def plot_channel(self, group_name, channel_name):
        channel = self.current_tdms[group_name][channel_name]
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
            
            # Create worker for async plotting
            worker = PlotWorker(signal_key, channel, color)
            worker.signals.finished.connect(self.plot_finished)
            
            # Start the worker
            self.threadpool.start(worker)
            
            # Add placeholder to legend
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

    def update_properties(self, group_name, channel_name):
        self.properties_widget.clear()
        channel = self.current_tdms[group_name][channel_name]
        for prop, value in channel.properties.items():
            QTreeWidgetItem(self.properties_widget, [f"{prop}: {value}"])

    def update_table(self, group_name, channel_name):
        channel = self.current_tdms[group_name][channel_name]
        data = channel[:]
        time = np.arange(len(data))
        
        self.table_widget.setRowCount(len(data))
        for i, (t, y) in enumerate(zip(time, data)):
            self.table_widget.setItem(i, 0, QTableWidgetItem(str(t)))
            self.table_widget.setItem(i, 1, QTableWidgetItem(str(y)))

    def zoom_in(self):
        self.graph_widget.getViewBox().scaleBy((0.5, 0.5))

    def zoom_out(self):
        self.graph_widget.getViewBox().scaleBy((2, 2))

    def reset_zoom(self):
        self.graph_widget.getViewBox().autoRange()

    def toggle_cursor(self):
        # Implementation for cursor functionality
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = TDMSViewer()
    viewer.show()
    sys.exit(app.exec()) 