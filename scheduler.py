import importlib.util
import sys
import os
import json

class Scheduler:
    def __init__(self):
        self.steps = {}
        
    def load_sequence(self, file_path):
        with open(file_path, 'r') as f:
            self.steps = json.load(f)
            
    def get_steps(self):
        return self.steps

    def execute_step(self, step):
        if not step['enable']:
            return True
            
        if not step['step_location']:
            return True
            
        try:
            # Get the directory containing the script
            script_dir = os.path.dirname(step['step_location'])
            
            # Add script directory to Python path if not already there
            if script_dir not in sys.path:
                sys.path.append(script_dir)
            
            # Import the module dynamically
            spec = importlib.util.spec_from_file_location(
                "module", step['step_location']
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the specified function
            func = getattr(module, step['function_name'])
            
            # Execute the function
            result = func()
            
            return result if result is not None else True
            
        except Exception as e:
            raise Exception(f"Error executing step {step['step_name']}: {str(e)}")
