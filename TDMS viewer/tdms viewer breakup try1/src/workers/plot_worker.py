"""
Background worker for plot processing
"""

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import numpy as np
from core.signal_processor import SignalProcessor
from typing import Optional

class PlotWorkerSignals(QObject):
    """Signals for plot worker"""
    chunk_ready = pyqtSignal(str, np.ndarray, np.ndarray, str, bool)  # signal_key, y_data, x_data, color, is_final
    progress = pyqtSignal(int)  # Progress percentage
    data_stored = pyqtSignal(str, np.ndarray, np.ndarray)  # signal_key, y_data, x_data
    error = pyqtSignal(str)  # error message

class PlotWorker(QRunnable):
    """Worker for processing and plotting TDMS data"""
    
    def __init__(self, signal_key: str, value_data: np.ndarray, 
                 time_data: Optional[np.ndarray], color: str, 
                 initial_points=1000000, chunk_size=100000, enable_decimation=True):
        """
        Initialize plot worker
        
        Args:
            signal_key: Unique identifier for the signal
            value_data: Y-axis data
            time_data: X-axis data (optional)
            color: Plot color
        """
        super().__init__()
        
        self.signal_key = signal_key
        self.value_data = value_data
        self.time_data = time_data
        self.color = color
        self.signals = PlotWorkerSignals()
        self.should_continue = True
        
        # Constants
        self.INITIAL_POINTS = initial_points
        self.CHUNK_SIZE = chunk_size
    
    @pyqtSlot()
    def run(self) -> None:
        """Process and emit plot data"""
        try:
            # Check if data is numeric before processing
            if not all(isinstance(x, (int, float, np.number)) for x in self.value_data):
                # If data is not numeric, immediately emit an error without attempting to plot
                self.signals.error.emit(f"Cannot plot non-numeric data for {self.signal_key}")
                return
            
            # Convert data to numpy arrays
            y_data = np.array(self.value_data, dtype=np.float64)
            
            if self.time_data is not None:
                # Check time data is numeric
                if not all(isinstance(x, (int, float, np.number)) for x in self.time_data):
                    # If time data is non-numeric, use index
                    x_data = np.arange(len(y_data), dtype=np.float64)
                else:
                    x_data = np.array(self.time_data, dtype=np.float64)
            else:
                x_data = np.arange(len(y_data), dtype=np.float64)
            
            # Replace invalid values with NaN
            y_data = np.where(np.isfinite(y_data), y_data, np.nan)
            x_data = np.where(np.isfinite(x_data), x_data, np.nan)
            
            total_points = len(y_data)
            processed_points = 0
            
            # Initial decimation for overview
            if total_points > self.INITIAL_POINTS and self.should_continue:
                decimated_x, decimated_y = SignalProcessor.decimate_data(
                    x_data, y_data, self.INITIAL_POINTS)
                self.signals.chunk_ready.emit(
                    self.signal_key, decimated_y, decimated_x, self.color, False)
                
                # Update progress
                processed_points = self.INITIAL_POINTS
                progress = (processed_points / total_points) * 100
                self.signals.progress.emit(int(progress))
            
            # Process remaining data in chunks
            while processed_points < total_points and self.should_continue:
                chunk_end = min(processed_points + self.CHUNK_SIZE, total_points)
                chunk_x = x_data[processed_points:chunk_end]
                chunk_y = y_data[processed_points:chunk_end]
                
                self.signals.chunk_ready.emit(
                    self.signal_key, chunk_y, chunk_x, self.color, 
                    chunk_end == total_points)
                
                processed_points = chunk_end
                progress = (processed_points / total_points) * 100
                self.signals.progress.emit(int(progress))
            
            # Store full resolution data for later use
            if self.should_continue:
                self.signals.data_stored.emit(self.signal_key, y_data, x_data)
            
        except Exception as e:
            self.signals.error.emit(f"Error in PlotWorker: {str(e)}")
    
    def stop(self) -> None:
        """Stop the worker"""
        self.should_continue = False
