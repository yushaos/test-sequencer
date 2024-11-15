"""
Custom file dialog implementations for TDMS Viewer
"""

from PyQt5.QtWidgets import (QFileDialog, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QComboBox, QCheckBox, QPushButton,
                           QDialogButtonBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import List, Optional, Tuple
import os

from config.settings import settings

class TDMSFileDialog(QFileDialog):
    """Enhanced file dialog for TDMS files"""
    
    def __init__(self, parent: Optional[QWidget] = None,
                 caption: str = "Select TDMS File",
                 directory: str = "",
                 filter: str = "TDMS Files (*.tdms)"):
        """
        Initialize TDMS file dialog
        
        Args:
            parent: Parent widget
            caption: Dialog caption
            directory: Starting directory
            filter: File filter pattern
        """
        super().__init__(parent, caption, directory, filter)
        
        # Configure dialog
        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setViewMode(QFileDialog.Detail)
        self.setFileMode(QFileDialog.ExistingFile)
        
        # Add custom widgets
        self.setup_additional_widgets()
    
    def setup_additional_widgets(self):
        """Setup additional dialog widgets"""
        # Get the dialog's layout
        layout = self.layout()
        
        # Create widget for additional controls
        additional_widget = QWidget(self)
        additional_layout = QVBoxLayout(additional_widget)
        
        # Recent files section
        recent_group = QWidget()
        recent_layout = QHBoxLayout(recent_group)
        
        recent_label = QLabel("Recent Files:")
        self.recent_combo = QComboBox()
        self.recent_combo.setMinimumWidth(200)
        self.populate_recent_files()
        
        recent_layout.addWidget(recent_label)
        recent_layout.addWidget(self.recent_combo)
        
        # Options section
        options_group = QWidget()
        options_layout = QGridLayout(options_group)
        
        # Add to recent files checkbox
        self.add_recent_cb = QCheckBox("Add to recent files")
        self.add_recent_cb.setChecked(True)
        
        # Remember directory checkbox
        self.remember_dir_cb = QCheckBox("Remember directory")
        self.remember_dir_cb.setChecked(True)
        
        # Auto-load time channels checkbox
        self.auto_load_time_cb = QCheckBox("Auto-load time channels")
        self.auto_load_time_cb.setChecked(True)
        
        # Add options to grid
        options_layout.addWidget(self.add_recent_cb, 0, 0)
        options_layout.addWidget(self.remember_dir_cb, 0, 1)
        options_layout.addWidget(self.auto_load_time_cb, 1, 0)
        
        # Add sections to additional layout
        additional_layout.addWidget(recent_group)
        additional_layout.addWidget(options_group)
        
        # Add preview section if needed
        if self.should_show_preview():
            preview_widget = self.create_preview_widget()
            additional_layout.addWidget(preview_widget)
        
        # Add the additional widget to the dialog's layout
        layout.addWidget(additional_widget)
        
        # Connect signals
        self.recent_combo.currentIndexChanged.connect(self.on_recent_selected)
    
    def populate_recent_files(self):
        """Populate recent files combo box"""
        recent_files = settings.get('file_settings.recent_files', [])
        self.recent_combo.clear()
        self.recent_combo.addItem("-- Select Recent File --")
        
        for file_path in recent_files:
            if os.path.exists(file_path):
                self.recent_combo.addItem(os.path.basename(file_path), file_path)
    
    def on_recent_selected(self, index: int):
        """
        Handle recent file selection
        
        Args:
            index: Selected index
        """
        if index > 0:  # Skip the placeholder item
            file_path = self.recent_combo.itemData(index)
            if file_path and os.path.exists(file_path):
                self.selectFile(file_path)
    
    def should_show_preview(self) -> bool:
        """
        Check if file preview should be shown
        
        Returns:
            True if preview should be shown
        """
        return settings.get('file_settings.show_preview', True)
    
    def create_preview_widget(self) -> QWidget:
        """
        Create file preview widget
        
        Returns:
            Preview widget
        """
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        # Preview label
        preview_label = QLabel("File Preview:")
        preview_label.setAlignment(Qt.AlignLeft)
        
        # Preview content (could be customized based on file type)
        self.preview_content = QLabel("Select a file to preview")
        self.preview_content.setAlignment(Qt.AlignLeft)
        self.preview_content.setWordWrap(True)
        self.preview_content.setMinimumHeight(100)
        self.preview_content.setStyleSheet(
            "QLabel { background-color: white; padding: 5px; }"
        )
        
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_content)
        
        return preview_widget
    
    def update_preview(self, file_path: str):
        """
        Update file preview
        
        Args:
            file_path: Path to selected file
        """
        if hasattr(self, 'preview_content'):
            try:
                # Read first few lines of file
                preview_text = f"File: {os.path.basename(file_path)}\n\n"
                preview_text += f"Size: {os.path.getsize(file_path):,} bytes\n"
                preview_text += f"Modified: {os.path.getmtime(file_path)}\n"
                
                self.preview_content.setText(preview_text)
            except Exception as e:
                self.preview_content.setText(f"Error previewing file: {str(e)}")
    
    def selectedFiles(self) -> List[str]:
        """
        Get selected files with additional processing
        
        Returns:
            List of selected file paths
        """
        files = super().selectedFiles()
        
        if files and self.add_recent_cb.isChecked():
            self.add_to_recent_files(files[0])
            
        if files and self.remember_dir_cb.isChecked():
            settings.set('file_settings.last_directory', 
                        os.path.dirname(files[0]))
        
        return files
    
    def add_to_recent_files(self, file_path: str):
        """
        Add file to recent files list
        
        Args:
            file_path: File path to add
        """
        recent_files = settings.get('file_settings.recent_files', [])
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Add to start of list
        recent_files.insert(0, file_path)
        
        # Limit list size
        max_recent = settings.get('file_settings.max_recent_files', 10)
        recent_files = recent_files[:max_recent]
        
        # Save updated list
        settings.set('file_settings.recent_files', recent_files)
    
    def get_dialog_options(self) -> dict:
        """
        Get current dialog options
        
        Returns:
            Dictionary of dialog options
        """
        return {
            'add_to_recent': self.add_recent_cb.isChecked(),
            'remember_directory': self.remember_dir_cb.isChecked(),
            'auto_load_time': self.auto_load_time_cb.isChecked()
        }

def get_open_filename(parent: Optional[QWidget] = None, 
                     caption: str = "Select TDMS File",
                     directory: str = "",
                     filter: str = "TDMS Files (*.tdms)") -> Tuple[str, dict]:
    """
    Show file open dialog
    
    Args:
        parent: Parent widget
        caption: Dialog caption
        directory: Starting directory
        filter: File filter pattern
        
    Returns:
        Tuple of (selected file path, dialog options)
    """
    dialog = TDMSFileDialog(parent, caption, directory, filter)
    
    if dialog.exec_() == QFileDialog.Accepted:
        files = dialog.selectedFiles()
        options = dialog.get_dialog_options()
        return (files[0] if files else "", options)
    
    return ("", {})
