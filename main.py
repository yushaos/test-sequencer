import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QTableWidgetItem, QFileDialog, QMenu,
    QListWidgetItem
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QBrush, QColor, QFont
from gui.test_sequencer_ui import TestSequencerUI
from scheduler import Scheduler
from ni_timer import NITimer
from previous_sequences import PreviousSequences
from result_files_handler import ResultFilesHandler
from error_box import ErrorBox
from status_box import StatusBox
from status_bar import StatusBar
from config_utils import get_path
from multiprocessing import Process, Queue
import queue
from threading import Thread
import time

# Add this function before the TestSequencer class definition
def run_steps_worker(steps, step_queue, result_queue):
    total_steps = sum(len([s for s in section if s['enable']]) 
                     for section in steps.values())
    current_step = 0
    scheduler = Scheduler()
    scheduler.steps = steps

    for section, section_steps in steps.items():
        result_queue.put(('section', section))
        
        for step_index, step in enumerate(section_steps):
            if not step['enable']:
                continue

            # Send both step name AND index
            result_queue.put(('step_start', {
                'current': current_step,
                'total': total_steps,
                'name': step['step_name'],
                'list_index': current_step  # Add this line
            }))

            try:
                start_time = time.time()
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
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Include duration in step complete message
                result_queue.put(('step_complete', {
                    'current': current_step,
                    'total': total_steps,
                    'name': step['step_name'],
                    'result': True,
                    'duration': duration
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
            # Execute the specific function from the step file
            self.result = self.scheduler.execute_step(self.step)
            self.completed = True
        except Exception as e:
            self.error = e
            self.completed = True

class TestSequencer(TestSequencerUI):
    def __init__(self):
        super().__init__()
        
        self.scheduler = Scheduler()
        self.ni_timer = NITimer()
        self.previous_sequences = PreviousSequences()
        self.result_files_handler = ResultFilesHandler()
        
        self.run_btn.setEnabled(False)
        self.end_sequence_btn.setEnabled(False)
        
        self.max_error_messages = 3

        self.error_box = ErrorBox(self.error_list)
        self.status_box = StatusBox(self.status_list)
        self.status_bar = StatusBar(self.progress_bar)

        self.step_queue = Queue()
        self.result_queue = Queue()
        self.step_process = None
        self.step_timer = QTimer()
        self.step_timer.timeout.connect(self.check_step_result)
        self.step_timer.start(100)

        self.current_section = ""
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
                "JSON Files (*.json)"
            )
        
        if file_name:
            try:
                # Clear errors first
                self.error_list.clear()
                self.status_list.clear()
                
                if not os.path.exists(file_name):
                    self.error_box.add_error_message(f"Error: Sequence file not found: {file_name}")
                    return
                
                self.sequence_list.clear()
                self.scheduler.load_sequence(file_name)
                self.update_sequence_list()
                self.status_box.add_status(f"Loaded sequence: {file_name}")
                
                self.run_btn.setEnabled(True)
                self.end_sequence_btn.setEnabled(False)
                
            except Exception as e:
                self.error_box.add_error_message(f"Error loading sequence: {str(e)}")
                self.run_btn.setEnabled(False)
                self.end_sequence_btn.setEnabled(False)
                self.sequence_list.clear()

    def update_sequence_list(self):
        self.sequence_list.clear()
        steps = self.scheduler.get_steps()
        super().update_sequence_list(steps)

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
            while True:
                msg_type, data = self.result_queue.get_nowait()
                
                if msg_type == 'section':
                    self.current_section = data  # Add this line
                    if data.lower() == 'test':
                        self.clear_test_details()  # Clear table when test section starts
                    self.status_box.add_section_status(data)
                
                elif msg_type == 'step_start':
                    self.status_box.add_status(f"Starting step: {data['name']}")
                    self.highlight_current_step(data['list_index'])  # Use index instead of name
                    self.status_bar.update_progress(data['current'], data['total'])
                
                elif msg_type == 'step_complete':
                    if self.current_section.lower() == 'test':
                        # Update test details with step duration
                        duration = f"{data.get('duration', 0):.2f}s"
                        self.update_test_details(data['name'], duration)
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
        
        # Reset GUI to startup state
        self.run_btn.setEnabled(True)
        self.end_sequence_btn.setEnabled(False)
        self.status_bar.set_complete()
        self.reset_step_highlights()
        self.sequence_list.clear()  # Clear the sequence list
        self.error_box.clear()      # Clear error messages
        self.status_box.clear()     # Clear status messages
        self.run_btn.setEnabled(False)  # Disable run button until new sequence is loaded

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
                
            except Exception as e:
                print(f"Error ending sequence: {e}")
            finally:
                self.cleanup_process()  # Always cleanup, even if there's an error

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
                        self.highlight_current_step(current_step_count)
                    current_step_count += 1

        self.status_bar.update_progress(current_step, total_steps)

        if error_msg:
            self.error_box.add_error_message(error_msg)

        QApplication.processEvents()

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

    def get_actual_list_index(self, step_index):
        # Convert step index to list widget index (accounting for headers)
        steps = self.scheduler.get_steps()
        current_count = 0
        list_index = 0
        
        for section in steps:
            list_index += 1  # Add 1 for section header
            for step in steps[section]:
                if step['enable']:
                    if current_count == step_index:
                        return list_index
                    current_count += 1
                list_index += 1 if step['enable'] else 0
        return list_index

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

def main():
    app = QApplication(sys.argv)
    window = TestSequencer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
