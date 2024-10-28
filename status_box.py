from PyQt5.QtWidgets import QListWidget

class StatusBox:
    def __init__(self, list_widget: QListWidget):
        self.status_list = list_widget

    def add_status(self, message):
        self.status_list.addItem(message)

    def add_section_status(self, section_name):
        self.status_list.addItem(f"--- {section_name.upper()} ---")

    def clear(self):
        self.status_list.clear()
