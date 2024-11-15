import json
import os
from utils import get_application_path

class SignalMapper:
    def __init__(self):
        self.mapping = {}
        self.load_config()

    def load_config(self):
        config_path = os.path.join(get_application_path(), 'tdms_viewer_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.mapping = {item['y']: item['x'] for item in config['signal_pairs']}
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load signal mapping config: {e}")
            default_config = {
                "last_directory": "",
                "signal_pairs": [
                    {"x": "Time", "y": "Value"},
                    {"x": "Timestamp", "y": "Data"}
                ]
            }
            try:
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                print(f"Created default config file at: {config_path}")
                self.mapping = {item['y']: item['x'] for item in default_config['signal_pairs']}
            except Exception as write_error:
                print(f"Error creating default config file: {write_error}")
                self.mapping = {}

    def get_x_signal(self, y_signal):
        """Get the corresponding x signal for a y signal"""
        return self.mapping.get(y_signal)
