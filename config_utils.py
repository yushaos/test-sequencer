import os

def load_config(config_file='sequencer property/sequencer_property.txt'):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    return config

CONFIG = load_config()

def get_path(key, default):
    return CONFIG.get(key, default)
