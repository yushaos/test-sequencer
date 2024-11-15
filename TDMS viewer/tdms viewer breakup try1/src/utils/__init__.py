"""
Utilities Package

Contains utility functions and helper classes for the TDMS Viewer application.
"""

import os
import sys
import logging
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
import time

from .helpers import (format_si_prefix, get_safe_range, calculate_optimal_decimation,
                     find_nearest_index, safe_cast)
from .signal_mapper import SignalMapper

logger = logging.getLogger(__name__)

# Performance monitoring decorators
def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to measure function execution time
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.debug(f"{func.__name__} execution time: {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def memory_tracker(func: Callable) -> Callable:
    """
    Decorator to track memory usage
    
    Args:
        func: Function to track
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        import psutil
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss
        
        result = func(*args, **kwargs)
        
        mem_after = process.memory_info().rss
        mem_diff = mem_after - mem_before
        logger.debug(f"{func.__name__} memory change: {mem_diff / 1024 / 1024:.2f} MB")
        
        return result
    return wrapper

# Error handling utilities
class RetryableError(Exception):
    """Error that can be retried"""
    pass

def retry_operation(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator for retrying operations
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between attempts in seconds
        
    Returns:
        Wrapped function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}")
                        time.sleep(delay)
                    
            raise last_error
        return wrapper
    return decorator

# Path handling utilities
def get_application_path() -> str:
    """
    Get application base path
    
    Returns:
        Application base directory path
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def ensure_dir_exists(path: str) -> None:
    """
    Ensure directory exists, create if necessary
    
    Args:
        path: Directory path
    """
    os.makedirs(path, exist_ok=True)

# Configuration utilities
class ConfigurationError(Exception):
    """Configuration related error"""
    pass

def load_json_config(filepath: str) -> Dict:
    """
    Load JSON configuration file
    
    Args:
        filepath: Path to JSON config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigurationError: If loading fails
    """
    import json
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {str(e)}")

def save_json_config(config: Dict, filepath: str) -> None:
    """
    Save configuration to JSON file
    
    Args:
        config: Configuration dictionary
        filepath: Output file path
        
    Raises:
        ConfigurationError: If saving fails
    """
    import json
    
    try:
        directory = os.path.dirname(filepath)
        if directory:
            ensure_dir_exists(directory)
            
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        raise ConfigurationError(f"Failed to save config: {str(e)}")

# Type conversion utilities
def convert_to_type(value: Any, target_type: type) -> Any:
    """
    Safely convert value to target type
    
    Args:
        value: Value to convert
        target_type: Target type
        
    Returns:
        Converted value or None if conversion fails
    """
    try:
        if target_type == bool:
            return str(value).lower() in ('true', '1', 'yes', 'on')
        return target_type(value)
    except (ValueError, TypeError):
        return None

# Module interface
__all__ = [
    # Helper functions
    'format_si_prefix',
    'get_safe_range',
    'calculate_optimal_decimation',
    'find_nearest_index',
    'safe_cast',
    
    # Signal mapping
    'SignalMapper',
    
    # Decorators
    'timing_decorator',
    'memory_tracker',
    'retry_operation',
    
    # Path utilities
    'get_application_path',
    'ensure_dir_exists',
    
    # Configuration utilities
    'load_json_config',
    'save_json_config',
    'ConfigurationError',
    
    # Type conversion
    'convert_to_type'
]

# Initialize utility components
def initialize_utils():
    """Initialize utility components"""
    try:
        # Validate application path
        app_path = get_application_path()
        ensure_dir_exists(app_path)
        
        # Set up logging
        log_path = os.path.join(app_path, 'logs')
        ensure_dir_exists(log_path)
        
        logger.info("Utility components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize utility components: {str(e)}")
        raise

# Initialize utils on import
initialize_utils()
