"""
Background worker for table data processing
"""

from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, QThread
from typing import List, Tuple, Any
import numpy as np

class TableWorkerSignals(QObject):
    """Signals for table worker"""
    chunk_ready = pyqtSignal(int, list, int)  # start_row, chunk_data, start_col
    progress = pyqtSignal(int)  # Progress percentage
    finished = pyqtSignal()
    error = pyqtSignal(str)  # error message

class TableWorker(QRunnable):
    """Worker for processing and displaying table data"""
    
    def __init__(self, data_pairs: List[Tuple[np.ndarray, np.ndarray, str]], 
                 chunk_size: int = 1000, start_col: int = 0):
        """
        Initialize table worker
        
        Args:
            data_pairs: List of (x_data, y_data, channel_name) tuples
            chunk_size: Number of rows to process at once
            start_col: Starting column index
        """
        super().__init__()
        self.data_pairs = data_pairs
        self.chunk_size = chunk_size
        self.start_col = start_col
        self.signals = TableWorkerSignals()
        self.should_continue = True
        
    def run(self) -> None:
        """Process and emit table data in chunks"""
        try:
            # Process data pairs directly
            chunks = []
            for x_data, y_data, _ in self.data_pairs:
                chunks.append((x_data, y_data))
            
            # Get maximum number of rows
            max_rows = max(len(x) for x, _ in chunks)
            
            if max_rows == 0:
                self.signals.finished.emit()
                return
            
            # Process data in chunks
            current_row = 0
            while current_row < max_rows and self.should_continue:
                # Process chunk
                chunk_data = self.process_chunk(chunks, current_row)
                
                # Emit chunk data
                self.signals.chunk_ready.emit(current_row, chunk_data, self.start_col)
                
                # Update progress
                progress = (current_row / max_rows) * 100
                self.signals.progress.emit(int(progress))
                
                # Move to next chunk
                current_row += self.chunk_size
                
                # Small delay to allow GUI updates
                QThread.msleep(1)
            
            if self.should_continue:
                self.signals.finished.emit()
                
        except Exception as e:
            self.signals.error.emit(f"Error in TableWorker: {str(e)}")
    
    def process_chunk(self, chunks: List[Tuple[np.ndarray, np.ndarray]], 
                     start_row: int) -> List[List[str]]:
        """
        Process a chunk of data
        
        Args:
            chunks: List of (x_data, y_data) arrays
            start_row: Starting row index
            
        Returns:
            List of row data
        """
        end_row = min(start_row + self.chunk_size, 
                     max(len(x) for x, _ in chunks))
        chunk_data = []
        
        for row in range(start_row, end_row):
            row_data = []
            for x_arr, y_arr in chunks:
                if row < len(x_arr):
                    # Format values appropriately
                    x_val = x_arr[row]
                    y_val = y_arr[row]
                    
                    # Handle numeric values
                    if isinstance(x_val, (int, float)):
                        x_str = f"{x_val:.6f}"
                    else:
                        x_str = str(x_val)
                        
                    if isinstance(y_val, (int, float)):
                        y_str = f"{y_val:.6f}"
                    else:
                        y_str = str(y_val)
                        
                    row_data.extend([x_str, y_str])
                else:
                    row_data.extend(["", ""])
            
            chunk_data.append(row_data)
        
        return chunk_data
    
    def stop(self) -> None:
        """Stop the worker"""
        self.should_continue = False
