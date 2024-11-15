"""
Core Components Package

Contains core functionality for TDMS file handling, data management,
and signal processing.
"""

from .tdms_handler import TDMSHandler
from .data_manager import DataManager, SignalCache, TableCache
from .signal_processor import SignalProcessor

# Component registry for dependency injection and testing
CORE_COMPONENTS = {
    'tdms_handler': TDMSHandler,
    'data_manager': DataManager,
    'signal_processor': SignalProcessor
}

# Configuration defaults for core components
CORE_DEFAULTS = {
    'tdms_handler': {
        'chunk_size': 1000000,
        'enable_caching': True,
        'cache_decimated': True
    },
    'data_manager': {
        'max_cache_size': 10,
        'quick_view_size': 1000,
        'enable_compression': False
    },
    'signal_processor': {
        'target_points': 1000000,
        'decimation_method': 'scipy',
        'interpolation': 'linear'
    }
}

class CoreError(Exception):
    """Base exception for core component errors"""
    pass

class ProcessingError(CoreError):
    """Exception raised during signal processing"""
    pass

class CacheError(CoreError):
    """Exception raised during cache operations"""
    pass

def create_component(component_type: str, *args, **kwargs):
    """
    Create core component instance
    
    Args:
        component_type: Type of component to create
        *args: Positional arguments for component constructor
        **kwargs: Keyword arguments for component constructor
        
    Returns:
        Instance of requested component
        
    Raises:
        CoreError: If component type is not found
    """
    if component_type not in CORE_COMPONENTS:
        raise CoreError(f"Component type '{component_type}' not found")
    
    # Merge default configuration with provided kwargs
    config = CORE_DEFAULTS.get(component_type, {}).copy()
    config.update(kwargs)
    
    return CORE_COMPONENTS[component_type](*args, **config)

def initialize_components(config: dict = None):
    """
    Initialize core components with configuration
    
    Args:
        config: Configuration dictionary for components
        
    Returns:
        Dictionary of initialized components
        
    Raises:
        CoreError: If initialization fails
    """
    if config is None:
        config = {}
    
    components = {}
    try:
        # Initialize TDMS handler
        tdms_config = {**CORE_DEFAULTS['tdms_handler'], 
                      **config.get('tdms_handler', {})}
        components['tdms_handler'] = TDMSHandler(**tdms_config)
        
        # Initialize data manager
        data_config = {**CORE_DEFAULTS['data_manager'],
                      **config.get('data_manager', {})}
        components['data_manager'] = DataManager(**data_config)
        
        # Initialize signal processor
        processor_config = {**CORE_DEFAULTS['signal_processor'],
                          **config.get('signal_processor', {})}
        components['signal_processor'] = SignalProcessor(**processor_config)
        
        return components
        
    except Exception as e:
        raise CoreError(f"Failed to initialize components: {str(e)}")

class ComponentManager:
    """Manager for core components lifecycle"""
    
    def __init__(self, config: dict = None):
        self.components = initialize_components(config)
        self._active = True
    
    def get_component(self, component_type: str):
        """Get component instance by type"""
        if not self._active:
            raise CoreError("ComponentManager is not active")
        return self.components.get(component_type)
    
    def cleanup(self):
        """Cleanup component resources"""
        if self._active:
            for component in self.components.values():
                if hasattr(component, 'cleanup'):
                    component.cleanup()
            self._active = False

# Module interface
__all__ = [
    'TDMSHandler',
    'DataManager',
    'SignalProcessor',
    'SignalCache',
    'TableCache',
    'CoreError',
    'ProcessingError',
    'CacheError',
    'create_component',
    'initialize_components',
    'ComponentManager',
    'CORE_COMPONENTS',
    'CORE_DEFAULTS'
]

# Module initialization
import logging

logger = logging.getLogger(__name__)

def _validate_dependencies():
    """Validate core dependencies"""
    required_packages = [
        'numpy',
        'nptdms',
        'scipy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        raise ImportError(f"Missing core dependencies: {', '.join(missing)}")

# Validate dependencies on import
try:
    _validate_dependencies()
    logger.info("Core components initialized successfully")
except ImportError as e:
    logger.error(f"Failed to initialize core components: {str(e)}")
    raise
