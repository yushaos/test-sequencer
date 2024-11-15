"""
File selection widget with drag and drop support
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton,
                           QFileDialog, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from config.settings import settings

class FileWidget(QWidget):
    """Widget for file selection and display"""
    
    # Custom signals
    file_loaded = pyqtSignal(str)  # file_path
    file_error = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        
        self.current_file = ""
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # File path display
        self.file_location = QLineEdit()
        self.file_location.setPlaceholderText("File Location: Drag and drop TDMS file here or use browse button")
        self.file_location.setAcceptDrops(True)
        
        # Browse button with icon
        self.browse_btn = QPushButton()
        self.browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.browse_btn.setToolTip("Browse for TDMS file")
        self.browse_btn.setFixedWidth(40)
        
        # Add widgets to layout
        layout.addWidget(self.file_location)
        layout.addWidget(self.browse_btn)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.browse_btn.clicked.connect(self.browse_file)
        
        # Override drag and drop events
        self.file_location.dragEnterEvent = self.dragEnterEvent
        self.file_location.dropEvent = self.dropEvent
    
    def browse_file(self):
        """Open file dialog for selecting TDMS file"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open TDMS File",
            settings.get_last_directory(),
            "TDMS Files (*.tdms)"
        )
        
        if file_name:
            self.load_file(file_name)
    
    def load_file(self, file_path: str):
        """
        Load TDMS file
        
        Args:
            file_path: Path to TDMS file
        """
        if not file_path.lower().endswith('.tdms'):
            self.file_error.emit("Selected file is not a TDMS file")
            return
        
        try:
            # Update UI
            self.file_location.setText(file_path)
            self.current_file = file_path
            
            # Emit signal
            self.file_loaded.emit(file_path)
            
            # Update last directory
            settings.set_last_directory(file_path)
            
        except Exception as e:
            self.file_error.emit(f"Error loading file: {str(e)}")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handle drag enter events
        
        Args:
            event: Drag enter event
        """
        if event.mimeData().hasUrls():
            # Check if any URL is a TDMS file
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.tdms'):
                    event.accept()
                    return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """
        Handle drop events
        
        Args:
            event: Drop event
        """
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        
        # Find first TDMS file
        tdms_files = [f for f in files if f.lower().endswith('.tdms')]
        
        if tdms_files:
            self.load_file(tdms_files[0])
        else:
            self.file_error.emit("No valid TDMS file found in dropped items")
    
    def clear(self):
        """Clear current file selection"""
        self.file_location.clear()
        self.current_file = ""
    
    def get_current_file(self) -> str:
        """
        Get current file path
        
        Returns:
            Current file path or empty string
        """
        return self.current_file
