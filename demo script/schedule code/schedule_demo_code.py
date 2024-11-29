import json
import time
from datetime import datetime
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TestScript:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        """Load the configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info("Successfully loaded configuration file")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
            sys.exit(1)

    def execute_step(self, step):
        """Execute a single test step"""
        logger.info(f"Executing step: {step['name']}")
        print(f"TEST STEP OUTPUT: {step['message']}")
        

    def run(self):
        """Run the test script according to the schedule"""
        logger.info("Starting test script execution")
        
        steps = sorted(self.config['steps'], 
                      key=lambda x: x['execution_time'])
        
        start_time = time.time()
        
        for step in steps:
            elapsed = time.time() - start_time
            wait_seconds = step['execution_time'] - elapsed
            
            if wait_seconds > 0:
                logger.info(f"Waiting {wait_seconds:.2f} seconds until {step['name']}")
                time.sleep(wait_seconds)
            
            self.execute_step(step)
        
        logger.info("Test script execution completed")
        return True

if __name__ == "__main__":
     # Allow config file path to be specified as command line argument
    config_path = sys.argv[1] if len(sys.argv) > 1 else "schedule_config.json"
    
    # Create and run test script
    test_script = TestScript(config_path)
    test_script.run()
