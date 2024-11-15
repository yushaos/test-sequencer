"""
Utility functions for TDMS Viewer
"""

from typing import Union, Tuple, Optional
import numpy as np

def format_si_prefix(value: float) -> str:
    """
    Format number with SI prefix
    
    Args:
        value: Number to format
        
    Returns:
        Formatted string with SI prefix
    """
    if value == 0:
        return "0"
        
    prefixes = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    negative_prefixes = ['', 'm', 'µ', 'n', 'p', 'f', 'a', 'z', 'y']
    
    abs_value = abs(value)
    prefix_index = 0
    
    if abs_value >= 1:
        while abs_value >= 1000 and prefix_index < len(prefixes) - 1:
            abs_value /= 1000
            prefix_index += 1
        prefix = prefixes[prefix_index]
    else:
        while abs_value < 1 and prefix_index < len(negative_prefixes) - 1:
            abs_value *= 1000
            prefix_index += 1
        prefix = negative_prefixes[prefix_index]
    
    return f"{abs_value * (1 if value >= 0 else -1):.3f} {prefix}"

def get_safe_range(data: np.ndarray) -> Tuple[float, float]:
    """
    Get min/max range of data safely handling NaN values
    
    Args:
        data: Input numpy array
        
    Returns:
        Tuple of (min, max) values
    """
    valid_data = data[np.isfinite(data)]
    if len(valid_data) == 0:
        return 0.0, 1.0
    return float(np.min(valid_data)), float(np.max(valid_data))

def calculate_optimal_decimation(length: int, target: int = 1000000) -> int:
    """
    Calculate optimal decimation factor for data reduction
    
    Args:
        length: Original data length
        target: Target data length
        
    Returns:
        Decimation factor
    """
    if length <= target:
        return 1
    return max(1, length // target)

def find_nearest_index(array: np.ndarray, value: float) -> int:
    """
    Find index of nearest value in sorted array
    
    Args:
        array: Sorted numpy array
        value: Value to find
        
    Returns:
        Index of nearest value
    """
    idx = np.searchsorted(array, value)
    if idx == 0:
        return 0
    if idx == len(array):
        return len(array) - 1
    if abs(value - array[idx-1]) < abs(value - array[idx]):
        return idx-1
    return idx

def safe_cast(value: str, type_: type) -> Optional[Union[int, float, str]]:
    """
    Safely cast string to given type
    
    Args:
        value: String value to cast
        type_: Type to cast to (int, float, or str)
        
    Returns:
        Cast value or None if casting fails
    """
    try:
        return type_(value)
    except (ValueError, TypeError):
        return None
