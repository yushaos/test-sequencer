"""
Workers Package

Contains background worker components for asynchronous processing
in the TDMS Viewer application.
"""

from PyQt5.QtCore import QThreadPool, QThread
from typing import Dict, Type, Optional
import logging

from .plot_worker import PlotWorker, PlotWorkerSignals
from .table_worker import TableWorker, TableWorkerSignals

logger = logging.getLogger(__name__)

# Worker registry
WORKER_REGISTRY = {
    'plot': PlotWorker,
    'table': TableWorker
}

# Default worker configurations
WORKER_DEFAULTS = {
    'plot': {
        'priority': QThread.NormalPriority,
        'initial_points': 1000000,
        'chunk_size': 100000,
        'enable_decimation': True
    },
    'table': {
        'priority': QThread.LowPriority,
        'chunk_size': 1000,
        'enable_progress': True,
        'batch_delay': 1  # ms delay between batches
    }
}

class WorkerError(Exception):
    """Base exception for worker-related errors"""
    pass

class WorkerManager:
    """Manages worker threads and lifecycle"""
    
    def __init__(self, thread_pool: Optional[QThreadPool] = None):
        """
        Initialize worker manager
        
        Args:
            thread_pool: Optional QThreadPool instance
        """
        self.thread_pool = thread_pool or QThreadPool.globalInstance()
        self.active_workers: Dict[str, list] = {
            'plot': [],
            'table': []
        }
        self.worker_count = 0
    
    def create_worker(self, worker_type: str, *args, **kwargs) -> Optional[Type]:
        """
        Create worker instance
        
        Args:
            worker_type: Type of worker to create
            *args: Positional arguments for worker
            **kwargs: Keyword arguments for worker
            
        Returns:
            Worker instance
            
        Raises:
            WorkerError: If worker type is not found
        """
        if worker_type not in WORKER_REGISTRY:
            raise WorkerError(f"Unknown worker type: {worker_type}")
        
        # Merge default configuration with provided kwargs
        config = WORKER_DEFAULTS.get(worker_type, {}).copy()
        config.update(kwargs)
        
        try:
            worker = WORKER_REGISTRY[worker_type](*args, **config)
            worker.worker_id = self.worker_count
            self.worker_count += 1
            self.active_workers[worker_type].append(worker)
            return worker
        except Exception as e:
            logger.error(f"Failed to create {worker_type} worker: {str(e)}")
            raise WorkerError(f"Worker creation failed: {str(e)}")
    
    def start_worker(self, worker: Type, priority: Optional[int] = None) -> None:
        """
        Start worker in thread pool
        
        Args:
            worker: Worker instance to start
            priority: Optional priority level
        """
        try:
            if priority is not None:
                self.thread_pool.start(worker, priority)
            else:
                self.thread_pool.start(worker)
        except Exception as e:
            logger.error(f"Failed to start worker: {str(e)}")
            raise WorkerError(f"Worker start failed: {str(e)}")
    
    def stop_worker(self, worker: Type) -> None:
        """
        Stop worker
        
        Args:
            worker: Worker instance to stop
        """
        if hasattr(worker, 'stop'):
            worker.stop()
        
        # Remove from active workers
        for worker_type, workers in self.active_workers.items():
            if worker in workers:
                workers.remove(worker)
    
    def stop_all_workers(self, worker_type: Optional[str] = None) -> None:
        """
        Stop all workers of given type or all types
        
        Args:
            worker_type: Optional worker type to stop
        """
        if worker_type:
            workers = self.active_workers.get(worker_type, []).copy()
            for worker in workers:
                self.stop_worker(worker)
        else:
            for worker_type in self.active_workers:
                self.stop_all_workers(worker_type)
    
    def cleanup(self) -> None:
        """Clean up manager resources"""
        self.stop_all_workers()
        self.thread_pool.clear()
        logger.debug("Worker manager cleaned up")

class WorkerMonitor:
    """Monitors worker status and progress"""
    
    def __init__(self, manager: WorkerManager):
        """
        Initialize worker monitor
        
        Args:
            manager: WorkerManager instance to monitor
        """
        self.manager = manager
        self.worker_status: Dict[int, dict] = {}
    
    def register_worker(self, worker: Type) -> None:
        """
        Register worker for monitoring
        
        Args:
            worker: Worker instance to monitor
        """
        if hasattr(worker, 'worker_id'):
            self.worker_status[worker.worker_id] = {
                'status': 'created',
                'progress': 0,
                'error': None
            }
    
    def update_status(self, worker_id: int, status: str, 
                     progress: Optional[int] = None, 
                     error: Optional[str] = None) -> None:
        """
        Update worker status
        
        Args:
            worker_id: Worker ID
            status: New status
            progress: Optional progress value
            error: Optional error message
        """
        if worker_id in self.worker_status:
            self.worker_status[worker_id].update({
                'status': status,
                'progress': progress if progress is not None 
                    else self.worker_status[worker_id]['progress'],
                'error': error
            })
    
    def get_status(self, worker_id: int) -> Optional[dict]:
        """
        Get worker status
        
        Args:
            worker_id: Worker ID
            
        Returns:
            Worker status dictionary or None if not found
        """
        return self.worker_status.get(worker_id)

# Module interface
__all__ = [
    'PlotWorker',
    'PlotWorkerSignals',
    'TableWorker',
    'TableWorkerSignals',
    'WorkerManager',
    'WorkerMonitor',
    'WorkerError'
]
