"""
TDMS file handling and management
"""

from typing import Dict, List, Optional, Tuple, Generator
import numpy as np
from nptdms import TdmsFile, TdmsGroup, TdmsChannel
from utils.signal_mapper import SignalMapper
from utils.helpers import calculate_optimal_decimation

class TDMSHandler:
    """Handles TDMS file operations and data management"""
    
    def __init__(self):
        self.current_file: Optional[TdmsFile] = None
        self.signal_mapper = SignalMapper()
        self._channel_cache: Dict[str, np.ndarray] = {}
    
    def load_file(self, file_path: str) -> bool:
        """
        Load TDMS file
        
        Args:
            file_path: Path to TDMS file
            
        Returns:
            True if file loaded successfully, False otherwise
        """
        try:
            self.current_file = TdmsFile.read(file_path)
            self._channel_cache.clear()
            return True
        except Exception as e:
            print(f"Error loading TDMS file: {e}")
            return False
    
    def get_groups(self) -> List[TdmsGroup]:
        """
        Get all groups in current file
        
        Returns:
            List of TDMS groups
        """
        if not self.current_file:
            return []
        return list(self.current_file.groups())
    
    def get_channels(self, group_name: str) -> List[TdmsChannel]:
        """
        Get all channels in a group
        
        Args:
            group_name: Name of the group
            
        Returns:
            List of TDMS channels
        """
        if not self.current_file or group_name not in self.current_file:
            return []
        return list(self.current_file[group_name].channels())
    
    def get_channel_data(self, group_name: str, channel_name: str, 
                        decimated: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get channel data with corresponding time data
        
        Args:
            group_name: Name of the group
            channel_name: Name of the channel
            decimated: Whether to return decimated data
            
        Returns:
            Tuple of (time_data, value_data)
        """
        if not self.current_file:
            return np.array([]), np.array([])
            
        cache_key = f"{group_name}/{channel_name}"
        
        # Try to get value data
        try:
            value_channel = self.current_file[group_name][channel_name]
            if cache_key not in self._channel_cache:
                self._channel_cache[cache_key] = np.array(value_channel[:])
            value_data = self._channel_cache[cache_key]
        except Exception:
            return np.array([]), np.array([])
            
        # Try to get time data
        time_channel_name = self.signal_mapper.get_time_channel(channel_name)
        time_data = None
        
        if time_channel_name:
            try:
                time_channel = self.current_file[group_name][time_channel_name]
                time_cache_key = f"{group_name}/{time_channel_name}"
                if time_cache_key not in self._channel_cache:
                    self._channel_cache[time_cache_key] = np.array(time_channel[:])
                time_data = self._channel_cache[time_cache_key]
            except Exception:
                pass
                
        if time_data is None:
            time_data = np.arange(len(value_data))
            
        # Handle decimation if requested
        if decimated:
            factor = calculate_optimal_decimation(len(value_data))
            if factor > 1:
                time_data = time_data[::factor]
                value_data = value_data[::factor]
                
        return time_data, value_data
    
    def get_channel_properties(self, group_name: str, 
                             channel_name: str) -> Dict:
        """
        Get channel properties
        
        Args:
            group_name: Name of the group
            channel_name: Name of the channel
            
        Returns:
            Dictionary of channel properties
        """
        if not self.current_file:
            return {}
            
        try:
            channel = self.current_file[group_name][channel_name]
            props = {
                "name": channel.name,
                "length": len(channel),
                "data_type": str(channel.dtype),
                "properties": channel.properties
            }
            return props
        except Exception:
            return {}
    
    def get_group_properties(self, group_name: str) -> Dict:
        """
        Get group properties
        
        Args:
            group_name: Name of the group
            
        Returns:
            Dictionary of group properties
        """
        if not self.current_file:
            return {}
            
        try:
            group = self.current_file[group_name]
            props = {
                "name": group.name,
                "channel_count": len(list(group.channels())),
                "properties": group.properties
            }
            return props
        except Exception:
            return {}
    
    def iterate_channel_data(self, group_name: str, channel_name: str, 
                           chunk_size: int = 1000000) -> Generator:
        """
        Iterate over channel data in chunks
        
        Args:
            group_name: Name of the group
            channel_name: Name of the channel
            chunk_size: Size of each chunk
            
        Yields:
            Tuples of (time_chunk, value_chunk)
        """
        if not self.current_file:
            return
            
        try:
            value_channel = self.current_file[group_name][channel_name]
            total_length = len(value_channel)
            
            for start in range(0, total_length, chunk_size):
                end = min(start + chunk_size, total_length)
                value_chunk = value_channel[start:end]
                time_chunk = np.arange(start, end)
                yield time_chunk, value_chunk
        except Exception:
            return
