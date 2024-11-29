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

                # Initialize class with config_path from arguments

                if step.get('argument') and isinstance(step['argument'], dict):

                    config_path = step['argument'].get('config_path')

                    instance = class_obj(config_path)

                else:

                    # If no config_path in arguments, try to get it from step location directory

                    default_config = os.path.join(script_dir, 'config.json')

                    instance = class_obj(default_config)

                

                # Always call run() instead of __init__

                return instance.run()

            

            # Handle function type - call standalone function

            else:

                func = getattr(module, step.get('function_name', 'run'))

                if step.get('argument'):

                    return func(step['argument'])

                return func()

                

        except Exception as e:

            raise RuntimeError(f"Error executing step {step['step_name']}: {str(e)}")


