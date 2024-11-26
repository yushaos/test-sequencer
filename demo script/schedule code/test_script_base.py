from abc import ABC, abstractmethod

class TestScriptBase(ABC):
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
    
    @abstractmethod
    def load_config(self):
        """Load configuration file"""
        pass
        
    @abstractmethod
    def execute_step(self, step):
        """Execute a single test step"""
        pass 