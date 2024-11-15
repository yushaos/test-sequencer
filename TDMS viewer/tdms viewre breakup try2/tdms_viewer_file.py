from PyQt5.QtWidgets import QFileDialog, QPushButton, QTreeWidgetItem
from nptdms import TdmsFile
from signal_mapper import SignalMapper
from utils import get_application_path
import json
import os

class TDMSViewerFile:
    def setup_ui_file(self):
        pass  # UI elements are set up in TDMSViewerUI

    def initialize_file_variables(self):
        self.last_directory = self.load_last_directory()
        self.signal_mapper = SignalMapper()
        self.current_tdms = None
        self.current_selected_signal = None

    def connect_file_signals(self):
        self.file_location.dragEnterEvent = self.dragEnterEvent
        self.file_location.dropEvent = self.dropEvent
        self.file_location.setAcceptDrops(True)
        self.browse_btn.clicked.connect(self.browse_file)


    def load_last_directory(self):
        config_path = os.path.join(get_application_path(), 'tdms_viewer_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('last_directory', '')
        except (FileNotFoundError, json.JSONDecodeError):
            return ''

    def save_last_directory(self, directory):
        config_path = os.path.join(get_application_path(), 'tdms_viewer_config.json')
        config = {}
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        config['last_directory'] = directory
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open TDMS File",
            self.last_directory,
            "TDMS Files (*.tdms)"
        )
        if file_name:
            self.last_directory = os.path.dirname(file_name)
            self.save_last_directory(self.last_directory)
            self.load_tdms_file(file_name)

    def load_tdms_file(self, file_path):
        self.file_location.setText(file_path)
        self.current_tdms = TdmsFile.read(file_path)
        self.legend_list.clear()
        self.graph_widget.clear()
        self.current_plots = {}
        self.color_index = 0
        self.properties_widget.clear()
        self.update_signal_tree()

    def update_signal_tree(self):
        self.signal_tree.clear()
        for group in self.current_tdms.groups():
            group_item = QTreeWidgetItem([group.name])
            self.signal_tree.addTopLevelItem(group_item)
            for channel in group.channels():
                if not channel.name.lower().endswith('_time'):
                    channel_item = QTreeWidgetItem([channel.name])
                    group_item.addChild(channel_item)
