import sys
import os

def get_application_path():
    """Get the path to the application directory, works for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
