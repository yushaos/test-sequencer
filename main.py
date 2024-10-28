import sys
import csv
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem, QMenu, QAction,
    QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush
from scheduler import Scheduler
from ni_timer import NITimer
from previous_sequences import PreviousSequences
from pathlib import Path
import datetime
from result_files_handler import ResultFilesHandler
import time
from config_utils import get_path
from error_box import ErrorBox
from status_box import StatusBox
from status_bar import StatusBar
import json
from multiprocessing import Process, Queue
import queue
from threading import Thread

# Add this function before the TestSequencer class definition
def run_steps_worker(steps, step_queue, result_queue):
    total_steps = sum(len([s for s in section if s['enable']]) 
                     for section in steps.values())
    current_step = 0
    scheduler = Scheduler()
    scheduler.steps = steps

    for section, section_steps in steps.items():
        result_queue.put(('section', section))
        
        for step in section_steps:
            if not step['enable']:
                continue

            # Notify step start
            result_queue.put(('step_start', {
                'current': current_step,
                'total': total_steps,
                'name': step['step_name']
            }))

            try:
                # Start step execution
                step_thread = StepExecutionThread(scheduler, step)
                step_thread.start()
                
                # Wait for step completion or end signal
                while not step_thread.completed:
                    # Check for end signal every 100ms
                    try:
                        if not step_queue.empty() and step_queue.get_nowait() == 'end':
                            step_thread.join(timeout=1.0)
                            result_queue.put(('end', None))
                            return False
                    except queue.Empty:
                        pass
                    time.sleep(0.1)
                
                # Ensure thread is complete
                step_thread.join()
                
                # Check for errors
                if step_thread.error:
                    raise step_thread.error
                
                # Verify step result is explicitly True
                if step_thread.result is not True:
                    result_queue.put(('error', f"Step '{step['step_name']}' did not return True"))
                    return False
                
                # Step completed successfully
                result_queue.put(('step_complete', {
                    'current': current_step,
                    'total': total_steps,
                    'name': step['step_name'],
                    'result': True
                }))

            except Exception as e:
                result_queue.put(('step_error', {
                    'current': current_step,
                    'total': total_steps,
                    'name': step['step_name'],
                    'error': str(e)
                }))
                return False
            
            current_step += 1

    result_queue.put(('complete', None))
    return True

# Add this class at the top of the file with other imports
class StepExecutionThread(Thread):
    def __init__(self, scheduler, step):
        super().__init__()
        self.scheduler = scheduler
        self.step = step
        self.result = None
        self.error = None
        self.completed = False
        
    def run(self):
        try:
            # Execute the step and wait for completion
            self.result = self.scheduler.execute_step(self.step)
            self.completed = True
        except Exception as e:
            self.error = e
            self.completed = True

class TestSequencer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tester Sequencer")
        self.setGeometry(100, 100, 900, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.setup_ui()
        self.scheduler = Scheduler()
        self.ni_timer = NITimer()
        self.previous_sequences = PreviousSequences()
        self.result_files_handler = ResultFilesHandler()
        
        # Disable both Run and End Sequence buttons initially
        self.run_btn.setEnabled(False)
        self.end_sequence_btn.setEnabled(False)
        
        self.max_error_messages = 3  # Set the maximum number of error messages

        self.error_box = ErrorBox(self.error_list)
        self.status_box = StatusBox(self.status_list)
        self.status_bar = StatusBar(self.progress_bar)

        # Add these lines
        self.step_queue = Queue()
        self.result_queue = Queue()
        self.step_process = None
        self.step_timer = QTimer()
        self.step_timer.timeout.connect(self.check_step_result)
        self.step_timer.start(100)  # Check every 100ms

    def setup_ui(self):
        # Top Button Layout
        top_button_layout = QHBoxLayout()
        
        # Reorder the buttons
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
        
        # Add Progress Bar above Test Details
        self.progress_bar = QProgressBar()
        center_layout.addWidget(QLabel("Test Progress"))
        center_layout.addWidget(self.progress_bar)

        self.table_placeholder = QTableWidget()
        self.table_placeholder.setRowCount(0)
        self.table_placeholder.setColumnCount(3)
        self.table_placeholder.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        center_layout.addWidget(QLabel("Test Details"))
        center_layout.addWidget(self.table_placeholder)
        
        content_layout.addLayout(center_layout, 1)
        
        # Column 3: Status and Errors
        right_layout = QVBoxLayout()
        
        self.status_list = QListWidget()
        right_layout.addWidget(QLabel("Status"))
        right_layout.addWidget(self.status_list)
        
        self.error_list = QListWidget()
        right_layout.addWidget(QLabel("Errors"))
        right_layout.addWidget(self.error_list)
        
        content_layout.addLayout(right_layout, 1)
        
        self.main_layout.addLayout(content_layout)
        
        self.connect_signals()
        
    def connect_signals(self):
        self.prev_sequence_btn.clicked.connect(self.show_previous_sequences)
        self.load_sequence_btn.clicked.connect(self.load_sequence)
        self.run_btn.clicked.connect(self.run_sequence)
        self.end_sequence_btn.clicked.connect(self.end_sequence)
        self.result_files_btn.clicked.connect(self.show_result_files_menu)
        
    def show_previous_sequences(self):
        sequences = self.previous_sequences.get_previous_sequences()
        if not sequences:
            self.status_list.addItem("No previous sequences found.")
            return
        
        menu = QMenu(self)
        for sequence in sequences:
            action = menu.addAction(sequence)
            action.triggered.connect(lambda _, s=sequence: self.load_sequence(s))
        
        self.prev_sequence_btn.setMenu(menu)
        self.prev_sequence_btn.showMenu()
        
    def load_sequence(self, file_name=None):
        if not file_name:
            default_dir = get_path('DEMO_SEQUENCER_PATH', r"F:\test sequencer\demo sequencer")
            file_name, _ = QFileDialog.getOpenFileName(
                self, 
                "Load Sequence", 
                default_dir, 
                "JSON Files (*.json)"  # Changed from CSV to JSON
            )
        
        if file_name:
            if not os.path.exists(file_name):
                self.add_error_message(f"Error: Sequence file not found: {file_name}")
                return
            try:
                self.sequence_list.clear()
                self.scheduler.load_sequence(file_name)  # Scheduler needs to be updated too
                self.update_sequence_list()
                self.status_list.clear()
                self.error_list.clear()
                self.status_list.addItem(f"Loaded sequence: {file_name}")
                
                self.run_btn.setEnabled(True)
                self.end_sequence_btn.setEnabled(False)
            except Exception as e:
                self.add_error_message(f"Error loading sequence: {str(e)}")

    def update_sequence_list(self):
        self.sequence_list.clear()
        steps = self.scheduler.get_steps()
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

    def run_sequence(self):
        self.status_box.clear()
        self.error_box.clear()
        self.reset_step_highlights()
        self.run_btn.setEnabled(False)
        self.end_sequence_btn.setEnabled(True)

        # Start the process worker with just the steps data
        steps_data = self.scheduler.get_steps()
        self.step_process = Process(target=run_steps_worker, 
                                  args=(steps_data, self.step_queue, self.result_queue))
        self.step_process.start()

    def check_step_result(self):
        try:
            while True:  # Process all available messages
                msg_type, data = self.result_queue.get_nowait()
                
                if msg_type == 'section':
                    self.status_box.add_section_status(data)
                
                elif msg_type == 'step_start':
                    self.status_box.add_status(f"Starting step: {data['name']}")
                    self.highlight_current_step(data['name'])
                    self.status_bar.update_progress(data['current'], data['total'])
                
                elif msg_type == 'step_complete':
                    self.status_box.add_status(f"Completed step: {data['name']}")
                    self.status_bar.update_progress(data['current'] + 1, data['total'])
                
                elif msg_type == 'step_error':
                    self.error_box.add_error_message(f"Error in {data['name']}: {data['error']}")
                    self.status_bar.update_progress(data['current'], data['total'])
                
                elif msg_type == 'complete':
                    self.status_box.add_status("Sequence completed successfully")
                    self.cleanup_process()
                
                elif msg_type == 'end':
                    self.status_box.add_status("Sequence ended early")
                    self.cleanup_process()

        except queue.Empty:
            pass

    def cleanup_process(self):
        if self.step_process:
            self.step_process.terminate()
            self.step_process.join()
            self.step_process = None
        
        self.run_btn.setEnabled(True)
        self.end_sequence_btn.setEnabled(False)
        self.status_bar.set_complete()
        self.reset_step_highlights()  # Add this line to clear highlights

    def end_sequence(self):
        if self.step_process and self.step_process.is_alive():
            try:
                # Clear the queue first
                while not self.step_queue.empty():
                    self.step_queue.get_nowait()
                # Put the end signal
                self.step_queue.put('end')
                self.status_list.addItem("Ending sequence early...")
                
                # Wait a short time for process to end
                self.step_process.join(timeout=1.0)
                
                # Force terminate if still running
                if self.step_process.is_alive():
                    self.step_process.terminate()
                    self.step_process.join()
                
                self.cleanup_process()
                
            except Exception as e:
                print(f"Error ending sequence: {e}")
                self.cleanup_process()

    def show_result_files_menu(self):
        menu = self.result_files_handler.show_result_files_menu(self)
        if menu.isEmpty():
            self.add_error_message("No result files found.")
        else:
            menu.exec_(self.result_files_btn.mapToGlobal(self.result_files_btn.rect().bottomLeft()))

    def update_current_step(self, current_step, total_steps, error_msg=None, section=None):
        if section:
            self.status_box.add_section_status(section)

        steps = self.scheduler.get_steps()
        current_step_count = 0

        for section, section_steps in steps.items():
            for step in section_steps:
                if step['enable']:
                    if current_step_count == current_step:
                        self.status_box.add_status(f"Executing step: {step['step_name']}")
                        self.highlight_current_step(step['step_name'])
                    current_step_count += 1

        self.status_bar.update_progress(current_step, total_steps)

        if error_msg:
            self.error_box.add_error_message(error_msg)

        QApplication.processEvents()

    def highlight_current_step(self, current_step_name):
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            if isinstance(item, QListWidgetItem):
                if item.text().startswith("---"):  # This is a section header
                    item.setBackground(QBrush(QColor(200, 200, 255)))  # Light blue for headers
                elif item.text().strip() == current_step_name:
                    item.setBackground(QBrush(QColor(255, 255, 0)))  # Yellow highlight for current step
                else:
                    item.setBackground(QBrush(QColor(255, 255, 255)))  # White background for other steps

    def get_header_count(self, step_index):
        header_count = 0
        steps = self.scheduler.get_steps()
        current_count = 0
        for section in steps:
            if current_count + len(steps[section]) > step_index:
                break
            header_count += 1
            current_count += len(steps[section])
        return header_count

    def reset_step_highlights(self):
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            if isinstance(item, QListWidgetItem):
                item.setBackground(QBrush(QColor(255, 255, 255)))  # White background for all steps

    def add_error_message(self, message):
        # Remove the oldest message if we've reached the maximum
        if self.error_list.count() >= self.max_error_messages:
            self.error_list.takeItem(0)
        
        # Add the new error message
        self.error_list.addItem(message)

    def is_step_enabled(self, step_name):
        for section in self.scheduler.steps.values():
            for step in section:
                if step['step_name'] == step_name:
                    return step['enable']
        return False

def main():
    app = QApplication(sys.argv)
    window = TestSequencer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
