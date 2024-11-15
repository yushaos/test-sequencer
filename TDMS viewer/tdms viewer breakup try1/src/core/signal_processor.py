"""
Signal processing operations for TDMS data
"""

from typing import Tuple, Optional
import numpy as np
from scipy import signal
from utils.helpers import get_safe_range, find_nearest_index

class SignalProcessor:
    """Handles signal processing operations"""
    
    @staticmethod
    def decimate_data(x_data: np.ndarray, y_data: np.ndarray, 
                     target_points: int = 1000000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Decimate data to target points while preserving signal characteristics
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            target_points: Target number of points
            
        Returns:
            Tuple of (decimated_x, decimated_y)
        """
        if len(x_data) <= target_points:
            return x_data, y_data
            
        # Calculate decimation factor
        factor = max(1, len(x_data) // target_points)
        
        # Use scipy.signal.decimate for proper anti-aliasing
        try:
            decimated_y = signal.decimate(y_data, factor, zero_phase=True)
            decimated_x = x_data[::factor]
            
            # Ensure same length
            min_len = min(len(decimated_x), len(decimated_y))
            return decimated_x[:min_len], decimated_y[:min_len]
        except Exception:
            # Fallback to simple decimation if signal.decimate fails
            return x_data[::factor], y_data[::factor]
    
    @staticmethod
    def get_visible_data(x_data: np.ndarray, y_data: np.ndarray,
                        view_range: Tuple[float, float],
                        target_points: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get data within visible range with adaptive resolution
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            view_range: Tuple of (x_min, x_max)
            target_points: Target number of points
            
        Returns:
            Tuple of (visible_x, visible_y)
        """
        x_min, x_max = view_range
        
        # Find indices of visible range
        start_idx = find_nearest_index(x_data, x_min)
        end_idx = find_nearest_index(x_data, x_max)
        
        if start_idx >= end_idx:
            return np.array([]), np.array([])
        
        # Get visible data
        visible_x = x_data[start_idx:end_idx]
        visible_y = y_data[start_idx:end_idx]
        
        # Decimate if necessary
        if len(visible_x) > target_points:
            return SignalProcessor.decimate_data(visible_x, visible_y, target_points)
        
        return visible_x, visible_y
    
    @staticmethod
    def get_y_at_x(x_value: float, x_data: np.ndarray, 
                   y_data: np.ndarray) -> Optional[float]:
        """
        Get Y value at specific X coordinate using interpolation
        
        Args:
            x_value: X coordinate
            x_data: X-axis data
            y_data: Y-axis data
            
        Returns:
            Interpolated Y value or None if out of range
        """
        if len(x_data) == 0 or x_value < x_data[0] or x_value > x_data[-1]:
            return None
            
        idx = find_nearest_index(x_data, x_value)
        
        # Simple linear interpolation between points
        if idx > 0 and idx < len(x_data):
            x0, x1 = x_data[idx-1], x_data[idx]
            y0, y1 = y_data[idx-1], y_data[idx]
            return y0 + (y1 - y0) * (x_value - x0) / (x1 - x0)
            
        return y_data[idx]
    
    @staticmethod
    def calculate_statistics(y_data: np.ndarray) -> dict:
        """
        Calculate basic statistics for signal data
        
        Args:
            y_data: Signal data
            
        Returns:
            Dictionary of statistics
        """
        valid_data = y_data[np.isfinite(y_data)]
        if len(valid_data) == 0:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "peak_to_peak": 0.0
            }
            
        return {
            "mean": float(np.mean(valid_data)),
            "std": float(np.std(valid_data)),
            "min": float(np.min(valid_data)),
            "max": float(np.max(valid_data)),
            "peak_to_peak": float(np.ptp(valid_data))
        }
