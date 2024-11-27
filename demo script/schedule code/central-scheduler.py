import json
import time
from datetime import datetime
import logging
import sys
from typing import List, Dict, Any
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
        self.test_scripts = {}  # Store script instances
        
    def load_script(self, script_path: str, config_path: str, class_name: str):
        """Load a test script and its configuration"""
        try:
            # Import the test script module dynamically
            script_name = Path(script_path).stem
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the specified class
            if not hasattr(module, class_name):
                raise AttributeError(f"Class {class_name} not found in {script_path}")
            
            script_class = getattr(module, class_name)
            
            # Verify it has required methods
            if not all(hasattr(script_class, method) for method in ['load_config', 'execute_step']):
                raise AttributeError(f"Class {class_name} missing required methods")
            
            # Create instance of script class
            script_instance = script_class(config_path)
            self.test_scripts[script_name] = script_instance
            
            # Add all steps to the central schedule
            self._add_steps_to_schedule(script_instance, script_name)
            logger.info(f"Loaded script {script_name} with class {class_name}")
            
        except Exception as e:
            logger.error(f"Error loading script {script_path}: {str(e)}")
    
    def _add_steps_to_schedule(self, script_instance: Any, script_name: str):
        """Add steps from a script to the central schedule"""
        try:
            steps = script_instance.config.get('steps', [])
            
            for step in steps:
                # Validate required fields
                if 'execution_time' not in step:
                    logger.error(f"Step in {script_name} missing execution_time field, skipping")
                    continue
                    
                if 'name' not in step:
                    step['name'] = f"unnamed_step_{script_name}"
                    logger.warning(f"Step in {script_name} missing name field, using default: {step['name']}")
                
                try:
                    scheduled_step = (
                        float(step['execution_time']),
                        script_name,
                        step
                    )
                    heapq.heappush(self.scheduled_steps, scheduled_step)
                    logger.debug(f"Added step '{step['name']}' from {script_name} at time {step['execution_time']}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid execution_time in {script_name} step '{step.get('name')}': {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scheduling steps for {script_name}: {e}")
    
    def run(self):
        """Run all scheduled steps across all test scripts"""
        logger.info("Starting central scheduler execution")
        
        start_time = time.time()
        
        while self.scheduled_steps:
            next_execution_time, script_name, step = heapq.heappop(self.scheduled_steps)
            
            elapsed = time.time() - start_time
            wait_seconds = next_execution_time - elapsed
            
            if wait_seconds > 0:
                logger.info(f"Waiting {wait_seconds:.2f} seconds until {step['name']} from {script_name}")
                time.sleep(wait_seconds)
            
            script_instance = self.test_scripts[script_name]
            script_instance.execute_step(step)
        
        logger.info("All scheduled steps completed")

def main():
    scheduler = CentralScheduler()
    
    with open("central_scheduler_config.json", 'r') as f:
        scheduler_config = json.load(f)
    
    for script_info in scheduler_config['scripts']:
        scheduler.load_script(
            script_info['script_path'],
            script_info['config_path'],
            script_info['class_name']
        )
    
    scheduler.run()

if __name__ == "__main__":
    main()
