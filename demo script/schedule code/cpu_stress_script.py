import json
import time
from datetime import datetime
import logging
import sys
import math

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

    def cpu_stress(self, duration):
        """
        Execute CPU stress test for specified duration
        Uses mathematical computations to stress a single CPU thread
        """
        logger.info(f"Starting CPU stress for {duration} seconds")
        end_time = time.time() + duration
        
        # Perform heavy mathematical calculations until duration is reached
        while time.time() < end_time:
            # Complex mathematical operations to stress CPU
            for i in range(10000):
                math.sin(i) * math.cos(i)
                math.sqrt(i * math.pi)
                pow(i, 3)

    def execute_step(self, step):
        """Execute a single test step"""
        # logger.info(f"Executing step: {step['name']}")
        # logger.info(f"CPU stress duration: {step['stress_duration']} seconds")
        
        # Execute CPU stress for specified duration
        self.cpu_stress(step['stress_duration'])
        
        # logger.info(f"Completed step: {step['name']}")

    def run(self):
        """Run the stress test according to the schedule"""
        logger.info("Starting CPU stress test execution")
        
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
        
        logger.info("CPU stress test execution completed")

if __name__ == "__main__":
    # Allow config file path to be specified as command line argument
    config_path = sys.argv[1] if len(sys.argv) > 1 else "stress_config1.json"
    
    # Create and run stress test
    stress_test = TestScript(config_path)
    stress_test.run()