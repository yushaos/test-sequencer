from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem, QMenu,
    QListWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush
import time

class TestSequencerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tester Sequencer")
        self.setGeometry(100, 100, 900, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.setup_ui()

    def setup_ui(self):
        # Top Button Layout
        top_button_layout = QHBoxLayout()
        
        self.load_sequence_btn = QPushButton("Load Sequence")
        self.run_btn = QPushButton("Run")
        self.end_sequence_btn = QPushButton("End Sequence")
        self.prev_sequence_btn = QPushButton("Previous Sequence")
        self.result_files_btn = QPushButton("Result Files")
        self.settings_btn = QPushButton("Settings")
        
        buttons = [
            self.load_sequence_btn, self.run_btn, self.end_sequence_btn,
            self.prev_sequence_btn, self.result_files_btn, self.settings_btn
        ]
        
        for btn in buttons:
            btn.setFixedHeight(30)
            btn.setFixedWidth(120)
            top_button_layout.addWidget(btn)
        
        self.main_layout.addLayout(top_button_layout)
        
        # Content Layout with 3 Columns
        content_layout = QHBoxLayout()
        
        # Column 1: Sequence List
        left_layout = QVBoxLayout()
        self.sequence_list = QListWidget()
        left_layout.addWidget(QLabel("Sequence Steps"))
        left_layout.addWidget(self.sequence_list)
        content_layout.addLayout(left_layout, 1)
        
        # Column 2: Progress Bar and Test Details
        center_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        center_layout.addWidget(QLabel("Test Progress"))
        center_layout.addWidget(self.progress_bar)

        self.table_placeholder = QTableWidget()
        self.table_placeholder.setRowCount(0)
        self.table_placeholder.setColumnCount(2)
        self.table_placeholder.setHorizontalHeaderLabels(["Step Name", "Duration"])
        
        header = self.table_placeholder.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_placeholder.setColumnWidth(1, 100)
        
        center_layout.addWidget(QLabel("Test Details"))
        center_layout.addWidget(self.table_placeholder)
        content_layout.addLayout(center_layout, 1)
        
        # Column 3: Status and Errors
        right_layout = QVBoxLayout()
        self.status_list = QListWidget()
        right_layout.addWidget(QLabel("Status"))
        right_layout.addWidget(self.status_list)
        
        self.error_list = QListWidget()
        self.error_list.setWordWrap(True)
        self.error_list.setStyleSheet("QListWidget { color: red; }")
        right_layout.addWidget(QLabel("Errors"))
        right_layout.addWidget(self.error_list)
        
        content_layout.addLayout(right_layout, 1)
        self.main_layout.addLayout(content_layout) 

    def highlight_current_step(self, step_index):
        # Calculate the actual list index including headers
        list_index = self.get_actual_list_index(step_index)
        
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            if isinstance(item, QListWidgetItem):
                text = item.text().strip()
                if text.startswith("---"):  # Section header
                    item.setBackground(QBrush(QColor(200, 200, 255)))  # Light blue
                elif i == list_index:  # Match the calculated index
                    item.setBackground(QBrush(QColor(255, 255, 0)))  # Yellow
                else:
                    item.setBackground(QBrush(QColor(255, 255, 255)))  # White

    def reset_step_highlights(self):
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            if isinstance(item, QListWidgetItem):
                item.setBackground(QBrush(QColor(255, 255, 255)))  # White background for all steps

    def update_test_details(self, step_name, duration):
        # Add timestamp to differentiate between same-named steps
        timestamp = time.strftime("%H:%M:%S")
        display_name = f"{step_name} ({timestamp})"
        
        # Always add new row for each step execution
        row = self.table_placeholder.rowCount()
        self.table_placeholder.insertRow(row)
        self.table_placeholder.setItem(row, 0, QTableWidgetItem(display_name))
        self.table_placeholder.setItem(row, 1, QTableWidgetItem(duration))

    def clear_test_details(self):
        self.table_placeholder.setRowCount(0)

    def update_sequence_list(self, steps):
        self.sequence_list.clear()
        for section in steps.keys():
            # Create a custom item for the section header
            header_item = QListWidgetItem(f"--- {section.upper()} ---")
            font = QFont()
            font.setPointSize(12)  # Increase font size
            font.setBold(True)     # Make it bold
            header_item.setFont(font)
            header_item.setBackground(QBrush(QColor(200, 200, 255)))  # Light blue background
            self.sequence_list.addItem(header_item)
            
            for step in steps[section]:
                if step['enable']:
                    step_item = QListWidgetItem(f"  {step['step_name']}")
                    step_item.setBackground(QBrush(QColor(255, 255, 255)))  # White background
                    self.sequence_list.addItem(step_item)

    def get_actual_list_index(self, step_index):
        # This is a placeholder - the actual implementation will need steps data
        # You'll need to implement this in TestSequencer or pass the steps data
        pass 