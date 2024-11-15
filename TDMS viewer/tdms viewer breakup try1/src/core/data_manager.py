"""
Data management and caching for TDMS Viewer
"""

from typing import Dict, List, Optional, Tuple, Set
import numpy as np
from collections import OrderedDict

class SignalCache:
    """Cache for signal data"""
    def __init__(self):
        self.x_data: Optional[np.ndarray] = None
        self.y_data: Optional[np.ndarray] = None
        self.decimated_data: Optional[Tuple[np.ndarray, np.ndarray]] = None
        self.statistics: Optional[Dict] = None
        self.last_update: float = 0.0

class TableCache:
    """Cache for table data"""
    def __init__(self):
        self.headers: List[str] = []
        self.quick_view_data: List[List[str]] = []
        self.plot_keys: Set[str] = set()
        self.max_rows: int = 0
        self.quick_view_size: int = 1000
        self.is_fully_loaded: bool = False
        self.visible_columns: Set[int] = set()

class DataManager:
    """Manages data caching and access for TDMS Viewer"""
    
    def __init__(self, max_cache_size: int = 10):
        self.signal_cache: OrderedDict[str, SignalCache] = OrderedDict()
        self.table_cache = TableCache()
        self.max_cache_size = max_cache_size
    
    def cache_signal(self, signal_key: str, x_data: np.ndarray, 
                    y_data: np.ndarray) -> None:
        """
        Cache signal data
        
        Args:
            signal_key: Unique identifier for the signal
            x_data: X-axis data
            y_data: Y-axis data
        """
        # Remove oldest cache entry if cache is full
        if len(self.signal_cache) >= self.max_cache_size:
            self.signal_cache.popitem(last=False)
        
        # Create new cache entry
        cache = SignalCache()
        cache.x_data = x_data
        cache.y_data = y_data
        
        # Store in cache
        self.signal_cache[signal_key] = cache
    
    def get_signal_data(self, signal_key: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get cached signal data
        
        Args:
            signal_key: Unique identifier for the signal
            
        Returns:
            Tuple of (x_data, y_data) or None if not cached
        """
        if signal_key not in self.signal_cache:
            return None
            
        cache = self.signal_cache[signal_key]
        return cache.x_data, cache.y_data
    
    def cache_decimated_data(self, signal_key: str, x_data: np.ndarray, 
                           y_data: np.ndarray) -> None:
        """
        Cache decimated signal data
        
        Args:
            signal_key: Unique identifier for the signal
            x_data: Decimated X-axis data
            y_data: Decimated Y-axis data
        """
        if signal_key in self.signal_cache:
            self.signal_cache[signal_key].decimated_data = (x_data, y_data)
    
    def get_decimated_data(self, signal_key: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get cached decimated data
        
        Args:
            signal_key: Unique identifier for the signal
            
        Returns:
            Tuple of (decimated_x, decimated_y) or None if not cached
        """
        if signal_key not in self.signal_cache:
            return None
            
        cache = self.signal_cache[signal_key]
        return cache.decimated_data
    
    def cache_statistics(self, signal_key: str, statistics: Dict) -> None:
        """
        Cache signal statistics
        
        Args:
            signal_key: Unique identifier for the signal
            statistics: Dictionary of statistics
        """
        if signal_key in self.signal_cache:
            self.signal_cache[signal_key].statistics = statistics
    
    def get_statistics(self, signal_key: str) -> Optional[Dict]:
        """
        Get cached statistics
        
        Args:
            signal_key: Unique identifier for the signal
            
        Returns:
            Dictionary of statistics or None if not cached
        """
        if signal_key not in self.signal_cache:
            return None
            
        cache = self.signal_cache[signal_key]
        return cache.statistics
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.signal_cache.clear()
        self.table_cache = TableCache()
    
    def remove_signal(self, signal_key: str) -> None:
        """
        Remove signal from cache
        
        Args:
            signal_key: Unique identifier for the signal
        """
        if signal_key in self.signal_cache:
            del self.signal_cache[signal_key]
    
    def update_table_cache(self, headers: List[str], 
                          quick_view_data: List[List[str]]) -> None:
        """
        Update table cache with new data
        
        Args:
            headers: List of column headers
            quick_view_data: Initial rows of data for quick view
        """
        self.table_cache.headers = headers
        self.table_cache.quick_view_data = quick_view_data
        self.table_cache.is_fully_loaded = False
    
    def get_table_cache(self) -> TableCache:
        """
        Get table cache
        
        Returns:
            Current table cache
        """
        return self.table_cache
