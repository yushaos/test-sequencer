import os
from pathlib import Path
import datetime
from PyQt5.QtWidgets import QMenu, QAction
from config_utils import get_path

class ResultFilesHandler:
    def __init__(self):
        self.tracking_file = Path(get_path('RESULT_FILES_TRACKING', r"F:\test sequencer\sequencer property\result files.txt"))

    def show_result_files_menu(self, parent):
        menu = QMenu(parent)
        result_files = self.get_recent_result_files()
        
        for file_path in result_files:
            action = QAction(file_path, parent)
            action.triggered.connect(lambda _, p=file_path: self.open_result_file(p, parent))
            menu.addAction(action)
        
        return menu

    def get_recent_result_files(self):
        if not self.tracking_file.exists():
            return []
        
        with open(self.tracking_file, 'r') as f:
            return [line.strip() for line in f.readlines()]

    def open_result_file(self, file_path, parent):
        if os.path.exists(os.path.dirname(file_path)):
            os.startfile(os.path.dirname(file_path))
        else:
            parent.error_list.addItem(f"Error: Directory not found: {os.path.dirname(file_path)}")

    def update_result_files_tracking(self, new_file_path):
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        
        existing_files = self.get_recent_result_files()
        existing_files.insert(0, new_file_path)  # Add the new file path at the beginning
        
        with open(self.tracking_file, 'w') as f:
            for file_path in existing_files[:20]:  # Keep only the last 20 entries
                f.write(f"{file_path}\n")

    def generate_tdms_file_path(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"random_data_{timestamp}"
        file_name = f"result_{timestamp}.tdms"
        folder_path = Path(get_path('RESULT_TDMS_PATH', r"F:\test sequencer\result TDMS")) / folder_name
        return str(folder_path / file_name)

    def generate_tdms_folder_path(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"random_data_{timestamp}"
        return str(Path(get_path('RESULT_TDMS_PATH', r"F:\test sequencer\result TDMS")) / folder_name)
