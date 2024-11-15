"""
TDMS Viewer Package

A PyQt-based viewer for TDMS files with advanced visualization capabilities.
"""

__version__ = '1.0.0'
__author__ = 'TDMS Viewer Development Team'

# Version information
VERSION_INFO = {
    'major': 1,
    'minor': 0,
    'patch': 0,
    'release': 'final'
}

# Import main components for easier access
from .ui.main_window import TDMSMainWindow
from .core.tdms_handler import TDMSHandler
from .core.data_manager import DataManager
from .core.signal_processor import SignalProcessor

# Package-level constants
DEFAULT_CHUNK_SIZE = 1000000  # Default size for data chunking
MAX_CACHE_SIZE = 10  # Maximum number of signals to cache
SUPPORTED_EXTENSIONS = ['.tdms']  # Supported file extensions

class TDMSViewerError(Exception):
    """Base exception class for TDMS Viewer errors"""
    pass

class FileLoadError(TDMSViewerError):
    """Exception raised when there's an error loading a TDMS file"""
    pass

class ProcessingError(TDMSViewerError):
    """Exception raised when there's an error processing TDMS data"""
    pass

class ValidationError(TDMSViewerError):
    """Exception raised when there's a validation error"""
    pass

# Initialize module-level logging
import logging

def setup_logging(level=logging.INFO):
    """
    Setup package-level logging
    
    Args:
        level: Logging level (default: INFO)
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    # Create console handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger

# Create package logger
logger = setup_logging()

def get_version():
    """
    Get package version string
    
    Returns:
        Version string in format 'major.minor.patch'
    """
    version_parts = [
        str(VERSION_INFO['major']),
        str(VERSION_INFO['minor']),
        str(VERSION_INFO['patch'])
    ]
    
    version = '.'.join(version_parts)
    
    if VERSION_INFO['release'] != 'final':
        version += f"-{VERSION_INFO['release']}"
    
    return version

def get_version_info():
    """
    Get detailed version information
    
    Returns:
        Dictionary containing version information
    """
    return VERSION_INFO.copy()

def validate_environment():
    """
    Validate the runtime environment
    
    Raises:
        ImportError: If required dependencies are missing
        EnvironmentError: If environment is not properly configured
    """
    required_packages = [
        'PyQt5',
        'numpy',
        'nptdms',
        'pyqtgraph',
        'scipy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        raise ImportError(
            f"Missing required packages: {', '.join(missing_packages)}"
        )
    
    # Validate Qt environment
    try:
        from PyQt5.QtWidgets import QApplication
        if QApplication.instance() is None:
            pass
    except Exception as e:
        raise EnvironmentError(f"Qt environment validation failed: {str(e)}")

# Perform environment validation on import
try:
    validate_environment()
except (ImportError, EnvironmentError) as e:
    logger.error(f"Environment validation failed: {str(e)}")
    raise

# Package metadata
__all__ = [
    'TDMSMainWindow',
    'TDMSHandler',
    'DataManager',
    'SignalProcessor',
    'TDMSViewerError',
    'FileLoadError',
    'ProcessingError',
    'ValidationError',
    'setup_logging',
    'get_version',
    'get_version_info'
]
