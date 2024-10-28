import csv
import importlib.util
import time
import os
import json
import sys
from ni_timer import NITimer
from previous_sequences import PreviousSequences

class Scheduler:
    def __init__(self):
        self.steps = {}
        self.current_section = None
        self.ni_timer = NITimer()
        self.previous_sequences = PreviousSequences()
        self.should_end_early = False
        self.errors = []
        
    def load_sequence(self, file_path):
        try:
            with open(file_path, 'r') as f:
                self.steps = json.load(f)
                
            # Store the sequence path for later use
            self.sequence_path = file_path
            self.previous_sequences.add_sequence(file_path)
            
            return True
        except Exception as e:
            raise Exception(f"Failed to load sequence: {str(e)}")

    def get_steps(self):
        return self.steps
        
    def run(self, callback=None):
        total_steps = sum(len([step for step in steps if step['enable']]) for steps in self.steps.values())
        current_step = 0
        self.should_end_early = False
        self.errors = []
        error_occurred = False

        for section, steps in self.steps.items():
            if callback:
                callback(current_step, total_steps, section=section)

            if error_occurred and section.lower() != 'cleanup':
                continue  # Skip to cleanup if an error occurred in setup or test

            for step in steps:
                if step['enable']:
                    if callback:
                        callback(current_step, total_steps)
                    
                    if self.should_end_early and section.lower() != 'cleanup':
                        error_occurred = True
                        break  # Skip to cleanup if ending early
                    
                    try:
                        result = self.execute_step(step)
                        if not result and section.lower() in ['setup', 'test']:
                            error_msg = f"Step '{step['step_name']}' in section '{section}' failed or returned False."
                            self.errors.append(error_msg)
                            if callback:
                                callback(current_step, total_steps, error_msg=error_msg)
                            error_occurred = True
                            break  # Skip to cleanup if a step fails in setup or test
                    except Exception as e:
                        error_msg = f"Error in step '{step['step_name']}': {str(e)}"
                        self.errors.append(error_msg)
                        if callback:
                            callback(current_step, total_steps, error_msg=error_msg)
                        error_occurred = True
                        break  # Skip to cleanup if an exception occurs
                    
                    current_step += 1

            if error_occurred and section.lower() != 'cleanup':
                break  # Skip to cleanup if an error occurred in setup or test

        # Always execute cleanup section if it exists
        if 'Cleanup' in self.steps:
            if callback:
                callback(current_step, total_steps, section='Cleanup')
            for step in self.steps['Cleanup']:
                if step['enable']:
                    if callback:
                        callback(current_step, total_steps)
                    try:
                        self.execute_step(step)
                    except Exception as e:
                        error_msg = f"Error in cleanup step '{step['step_name']}': {str(e)}"
                        self.errors.append(error_msg)
                        if callback:
                            callback(current_step, total_steps, error_msg=error_msg)
                    current_step += 1

        # Call the callback one last time after all steps are completed
        if callback:
            callback(total_steps, total_steps)
        return len(self.errors) == 0  # Return True if no errors, False otherwise
        
    def execute_step(self, step):
        print(f"Starting execution of step: {step['step_name']}")
        
        # Get the script location from step_location
        script_path = step.get('step_location')
        
        if not script_path:
            print("No script location provided")
            return False
            
        try:
            # Run the Python script as a subprocess
            import subprocess
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, 
                                  text=True)
            
            # Check if script executed successfully
            if result.returncode == 0:
                print(f"Script output: {result.stdout}")
                return True
            else:
                print(f"Script failed with error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error executing script: {e}")
            return False
            
    def end_sequence(self):
        self.should_end_early = True
        print("Sequence ending early. Skipping to cleanup steps.")
        
    def load_module(self, location):
        if not location:
            return None
        try:
            print(f"Attempting to load module from: {location}")
            
            # Convert relative path to absolute path
            if location.startswith('./'):
                # Get directory of the sequence file
                base_dir = os.path.dirname(self.sequence_path)
                location = os.path.join(base_dir, location[2:])
            
            # Handle spaces in path
            location = os.path.abspath(location)
            
            print(f"Resolved path: {location}")
            if not os.path.exists(location):
                print(f"File not found: {location}")
                return None
                
            spec = importlib.util.spec_from_file_location("module", location)
            if spec is None:
                print(f"Failed to create spec for module: {location}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"Successfully loaded module: {location}")
            return module
        except Exception as e:
            print(f"Error loading module from {location}: {str(e)}")
            return None
        
    def load_config(self, location):
        # Implementation for loading config
        # For now, we'll just return an empty dict
        return {}
