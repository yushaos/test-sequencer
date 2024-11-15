from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QTreeWidget, QPushButton,
    QLabel, QTabWidget, QTableWidget, QLineEdit
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg

class TDMSViewerUI:
    def setup_ui_main(self):
        self.setWindowTitle("TDMS Viewer")
        self.setWindowState(Qt.WindowMaximized)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(2)
        # Left panel (Signal Names)
        left_panel = QGroupBox("Signal Names")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(2)
        self.signal_tree = QTreeWidget()
        self.signal_tree.setHeaderHidden(True)
        left_layout.addWidget(self.signal_tree)
        # Center panel
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(2)
        # File location
        file_layout = QHBoxLayout()
        self.file_location = QLineEdit()
        self.file_location.setPlaceholderText("File Location: ")
        self.browse_btn = QPushButton("📁")  # Changed to instance variable
        file_layout.addWidget(self.file_location)
        file_layout.addWidget(self.browse_btn)
        center_layout.addLayout(file_layout)
        # Tabs for Graph and Table
        self.tabs = QTabWidget()
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.showGrid(x=True, y=True)
        self.table_widget = QTableWidget()
        self.tabs.addTab(self.graph_widget, "Graph")
        self.tabs.addTab(self.table_widget, "Table")
        center_layout.addWidget(self.tabs)
        # Bottom toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        self.zoom_in_btn = QPushButton("🔍+ Zoom In")
        self.zoom_out_btn = QPushButton("🔍- Zoom Out")
        self.reset_btn = QPushButton("↺ Reset")
        self.cursor_btn = QPushButton("Cursor")
        self.cursor_btn.setCheckable(True)
        self.center_cursor_btn = QPushButton("⌖ Center Cursors")
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setSpacing(5)
        range_layout.addWidget(QLabel("X:"))
        self.x_min_input = QLineEdit()
        self.x_max_input = QLineEdit()
        range_layout.addWidget(self.x_min_input)
        range_layout.addWidget(self.x_max_input)
        range_layout.addWidget(QLabel("Y:"))
        self.y_min_input = QLineEdit()
        self.y_max_input = QLineEdit()
        range_layout.addWidget(self.y_min_input)
        range_layout.addWidget(self.y_max_input)
        self.apply_range_btn = QPushButton("Apply")
        range_layout.addWidget(self.apply_range_btn)
        toolbar_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.zoom_out_btn)
        toolbar_layout.addWidget(self.reset_btn)
        toolbar_layout.addWidget(self.cursor_btn)
        toolbar_layout.addWidget(self.center_cursor_btn)
        toolbar_layout.addWidget(range_widget)
        center_layout.addWidget(toolbar)
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(2)
        legend_group = QGroupBox("Legend")
        legend_layout = QVBoxLayout(legend_group)
        self.legend_list = QTreeWidget()
        self.legend_list.setHeaderLabels(["Signal", "Color"])
        legend_layout.addWidget(self.legend_list)
        properties_group = QGroupBox("Channel Properties")
        properties_layout = QVBoxLayout(properties_group)
        self.properties_widget = QTreeWidget()
        self.properties_widget.setHeaderHidden(True)
        properties_layout.addWidget(self.properties_widget)
        right_layout.addWidget(legend_group)
        right_layout.addWidget(properties_group)
        layout.addWidget(left_panel, stretch=1)
        layout.addWidget(center_panel, stretch=4)
        layout.addWidget(right_panel, stretch=1)
        self.main_layout = layout
        self.center_layout = center_layout  # Save for later use

    def initialize_ui_variables(self):
        pass  # If you have any UI-specific variables to initialize

    def connect_ui_signals(self):
        pass  # If you have any UI-specific signals to connect

