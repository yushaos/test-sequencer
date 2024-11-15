"""
Custom table widget for displaying TDMS data
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                           QProgressBar, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from typing import List, Optional, Dict

from core.data_manager import DataManager
from workers.table_worker import TableWorker

class TableWidget(QWidget):
    """Widget for displaying TDMS data in tabular format"""
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        
        self.data_manager = data_manager
        self.current_worker: Optional[TableWorker] = None
        self.worker_id = 0
        self.is_loading = False
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: transparent;
            }
            QProgressBar::chunk {
                background-color: #ADD8E6;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['X', 'Y'])
        
        # Configure table properties
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        
        # Set column widths
        for col in range(2):
            self.table.setColumnWidth(col, 150)
        
        layout.addWidget(self.table)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.table.verticalScrollBar().valueChanged.connect(self.on_scroll)
    
    def setup_table_structure(self, headers: List[str]) -> None:
        """
        Setup table structure with headers
        
        Args:
            headers: List of column headers
        """
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Hide row numbers
        self.table.verticalHeader().setVisible(False)
        
        # Set column widths
        for col in range(len(headers)):
            self.table.setColumnWidth(col, 150)
    
    def update_data(self) -> None:
        """Update table data"""
        # Cancel current worker if exists
        if self.current_worker:
            self.current_worker.stop()
        
        # Increment worker ID
        self.worker_id += 1
        current_id = self.worker_id
        
        # Get cached data
        table_cache = self.data_manager.get_table_cache()
        
        # Setup table structure
        self.setup_table_structure(table_cache.headers)
        
        # Update row count
        self.table.setRowCount(table_cache.max_rows)
        
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.is_loading = True
        
        # Create and start worker
        self.start_table_worker(current_id)
    
    def start_table_worker(self, worker_id: int) -> None:
        """
        Start table worker to load data
        
        Args:
            worker_id: Unique worker identifier
        """
        # Prepare data pairs
        data_pairs = []
        cache = self.data_manager.get_table_cache()
        
        for signal_key in cache.plot_keys:
            data = self.data_manager.get_signal_data(signal_key)
            if data:
                x_data, y_data = data
                data_pairs.append((x_data, y_data, signal_key))
        
        if not data_pairs:
            self.progress_bar.hide()
            self.is_loading = False
            return
        
        # Create worker
        worker = TableWorker(data_pairs)
        self.current_worker = worker
        
        # Connect signals
        worker.signals.chunk_ready.connect(
            lambda start_row, chunk_data, start_col:
            self.on_chunk_ready(start_row, chunk_data, start_col, worker_id)
        )
        worker.signals.progress.connect(self.on_progress)
        worker.signals.finished.connect(
            lambda: self.on_worker_finished(worker_id)
        )
        worker.signals.error.connect(self.on_worker_error)
        
        # Start worker
        worker.start()
    
    def on_chunk_ready(self, start_row: int, chunk_data: List[List[str]],
                      start_col: int, worker_id: int) -> None:
        """
        Handle data chunk updates
        
        Args:
            start_row: Starting row index
            chunk_data: Chunk data as list of rows
            start_col: Starting column index
            worker_id: Worker identifier
        """
        # Ignore updates from old workers
        if worker_id != self.worker_id:
            return
        
        # Update table with chunk data
        for row_offset, row_data in enumerate(chunk_data):
            row = start_row + row_offset
            for col_offset, value in enumerate(row_data):
                if value:  # Only set non-empty values
                    self.table.setItem(
                        row, start_col + col_offset,
                        QTableWidgetItem(str(value))
                    )
    
    def on_progress(self, progress: int) -> None:
        """
        Handle progress updates
        
        Args:
            progress: Progress percentage
        """
        self.progress_bar.setValue(progress)
    
    def on_worker_finished(self, worker_id: int) -> None:
        """
        Handle worker completion
        
        Args:
            worker_id: Worker identifier
        """
        if worker_id == self.worker_id:
            self.progress_bar.hide()
            self.is_loading = False
            self.current_worker = None
    
    def on_worker_error(self, error_msg: str) -> None:
        """
        Handle worker errors
        
        Args:
            error_msg: Error message
        """
        print(f"Table worker error: {error_msg}")
        self.progress_bar.hide()
        self.is_loading = False
    
    def on_scroll(self) -> None:
        """Handle table scrolling"""
        if not hasattr(self, 'last_scroll_time'):
            self.last_scroll_time = 0
        
        current_time = QTimer.currentTime().msecsSinceStartOfDay()
        if current_time - self.last_scroll_time < 100:  # Limit updates
            return
            
        self.last_scroll_time = current_time
        
        # Get visible range
        visible_rect = self.table.viewport().rect()
        first_visible_row = self.table.rowAt(visible_rect.top())
        last_visible_row = self.table.rowAt(visible_rect.bottom())
        
        if first_visible_row is not None and last_visible_row is not None:
            # Load data around visible area
            start_row = max(0, first_visible_row - 500)
            self.load_data_chunk(start_row)
    
    def load_data_chunk(self, start_row: int, chunk_size: int = 1000) -> None:
        """
        Load chunk of data
        
        Args:
            start_row: Starting row index
            chunk_size: Size of chunk to load
        """
        if self.is_loading:
            return
            
        cache = self.data_manager.get_table_cache()
        if start_row >= cache.max_rows:
            return
            
        end_row = min(start_row + chunk_size, cache.max_rows)
        
        # Check if chunk needs loading
        needs_loading = False
        for row in range(start_row, end_row):
            if not self.table.item(row, 0):
                needs_loading = True
                break
        
        if needs_loading:
            self.start_table_worker(self.worker_id)
    
    def clear_table(self) -> None:
        """Clear table contents"""
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['X', 'Y'])
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.current_worker:
            self.current_worker.stop()
        self.clear_table()
