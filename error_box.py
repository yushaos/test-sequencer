from PyQt5.QtWidgets import QListWidget
from PyQt5.QtCore import Qt

class ErrorBox:
    def __init__(self, list_widget: QListWidget, max_messages=3):
        self.error_list = list_widget
        self.max_messages = max_messages
        self.error_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.error_list.setTextElideMode(Qt.ElideNone)

    def add_error_message(self, message):
        if self.error_list.count() >= self.max_messages:
            self.error_list.takeItem(0)
        self.error_list.addItem(message)

    def clear(self):
        self.error_list.clear()
