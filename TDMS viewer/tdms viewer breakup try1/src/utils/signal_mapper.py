"""
Signal mapping functionality for TDMS Viewer
"""

from typing import Dict, Optional
from config.settings import settings

class SignalMapper:
    """Maps value channels to their corresponding time channels"""
    
    def __init__(self):
        self.mapping: Dict[str, str] = {}
        self.load_mapping()
    
    def load_mapping(self) -> None:
        """Load signal mappings from configuration"""
        signal_pairs = settings.get_signal_pairs()
        self.mapping = {item['y']: item['x'] for item in signal_pairs}
    
    def get_time_channel(self, value_channel: str) -> Optional[str]:
        """
        Get corresponding time channel name for a value channel
        
        Args:
            value_channel: Name of the value channel
            
        Returns:
            Corresponding time channel name or None if not found
        """
        # First try configured mapping
        if value_channel in self.mapping:
            return self.mapping[value_channel]
        
        # Then try default suffix
        return f"{value_channel}_Time"
    
    def add_mapping(self, value_channel: str, time_channel: str) -> None:
        """
        Add new signal mapping
        
        Args:
            value_channel: Name of the value channel
            time_channel: Name of the time channel
        """
        self.mapping[value_channel] = time_channel
        
        # Update configuration
        signal_pairs = settings.get_signal_pairs()
        signal_pairs.append({
            "x": time_channel,
            "y": value_channel
        })
        settings.config['signal_pairs'] = signal_pairs
        settings.save_config()
    
    def remove_mapping(self, value_channel: str) -> None:
        """
        Remove signal mapping
        
        Args:
            value_channel: Name of the value channel to remove
        """
        if value_channel in self.mapping:
            del self.mapping[value_channel]
            
            # Update configuration
            signal_pairs = settings.get_signal_pairs()
            signal_pairs = [pair for pair in signal_pairs 
                          if pair['y'] != value_channel]
            settings.config['signal_pairs'] = signal_pairs
            settings.save_config()
    
    def get_all_mappings(self) -> Dict[str, str]:
        """
        Get all current signal mappings
        
        Returns:
            Dictionary of value channel to time channel mappings
        """
        return self.mapping.copy()
    
    def clear_mappings(self) -> None:
        """Clear all signal mappings"""
        self.mapping.clear()
        settings.config['signal_pairs'] = []
        settings.save_config()
