from PyQt5.QtWidgets import QProgressBar

class StatusBar:
    def __init__(self, progress_bar: QProgressBar):
        self.progress_bar = progress_bar

    def update_progress(self, current_step, total_steps):
        progress_percentage = (current_step + 1) / total_steps * 100
        self.progress_bar.setValue(int(progress_percentage))

    def set_complete(self):
        self.progress_bar.setValue(100)
