import json
import time
from datetime import datetime
import logging
import sys
from typing import List, Dict
import importlib.util
from pathlib import Path
import heapq

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class CentralScheduler:
    def __init__(self):
        self.scheduled_steps = []  # Will be used as a heap queue
        self.test_scripts = {}  # Store TestScript instances
        
    def load_script(self, script_path: str, config_path: str):
        """Load a test script and its configuration"""
        try:
            # Import the test script module dynamically
            script_name = Path(script_path).stem
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create instance of TestScript
            test_script = module.TestScript(config_path)
            self.test_scripts[script_name] = test_script
            
            # Add all steps to the central schedule
            self._add_steps_to_schedule(test_script, script_name)
            logger.info(f"Loaded script {script_name} with its configuration")
            
        except Exception as e:
            logger.error(f"Error loading script {script_path}: {str(e)}")
    
    def _add_steps_to_schedule(self, test_script: 'TestScript', script_name: str):
        """Add steps from a test script to the central schedule"""
        steps = test_script.config['steps']
        for step in steps:
            # Create tuple of (execution_time, script_name, step)
            scheduled_step = (
                step['execution_time'],
                script_name,
                step
            )
            heapq.heappush(self.scheduled_steps, scheduled_step)
    
    def run(self):
        """Run all scheduled steps across all test scripts"""
        logger.info("Starting central scheduler execution")
        
        start_time = time.time()
        
        while self.scheduled_steps:
            # Get next step with earliest execution time
            next_execution_time, script_name, step = heapq.heappop(self.scheduled_steps)
            
            # Calculate wait time
            elapsed = time.time() - start_time
            wait_seconds = next_execution_time - elapsed
            
            if wait_seconds > 0:
                logger.info(f"Waiting {wait_seconds:.2f} seconds until {step['name']} from {script_name}")
                time.sleep(wait_seconds)
            
            # Execute the step using its corresponding test script
            test_script = self.test_scripts[script_name]
            test_script.execute_step(step)
        
        logger.info("All scheduled steps completed")

def main():
    # Create the central scheduler
    scheduler = CentralScheduler()
    
    # Get script mappings from a configuration file
    with open("central_scheduler_config.json", 'r') as f:
        scheduler_config = json.load(f)
    
    # Load each script and its configuration
    for script_info in scheduler_config['scripts']:
        scheduler.load_script(
            script_info['script_path'],
            script_info['config_path']
        )
    
    # Run the central scheduler
    scheduler.run()

if __name__ == "__main__":
    main()
