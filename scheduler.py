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
        if not step['enable'] or not step['step_location']:
            return True
            
        try:
            # Get the directory containing the script
            script_dir = os.path.dirname(step['step_location'])
            if script_dir not in sys.path:
                sys.path.append(script_dir)
            
            # Handle script type - execute entire file
            if step.get('call_type') == 'script':
                with open(step['step_location']) as f:
                    script_content = f.read()
                namespace = {}
                exec(script_content, namespace)
                return True
            
            # Import the module for function/method calls    
            spec = importlib.util.spec_from_file_location("module", step['step_location'])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Handle method type - call method from class instance
            if step.get('call_type') == 'method':
                class_obj = getattr(module, step['class_name'])
                instance = class_obj()
                func = getattr(instance, step['function_name'])
            
            # Handle function type - call function directly
            else:
                func = getattr(module, step['function_name'])
            
            # Execute with argument if provided
            if step.get('argument'):
                result = func(step['argument'])
            else:
                result = func()
                
            return result if result is not None else True
            
        except Exception as e:
            raise Exception(f"Error executing step {step['step_name']}: {str(e)}")
