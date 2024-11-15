#!/usr/bin/env python3
"""
TDMS Viewer Application Entry Point
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_window import TDMSMainWindow
from config.settings import get_application_path

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application icon
    icon_path_png = os.path.join(get_application_path(), 'resources', 'TDMS viewer icon.png')
    icon_path_ico = os.path.join(get_application_path(), 'resources', 'TDMS viewer icon.ico')
    
    if os.path.exists(icon_path_png):
        app.setWindowIcon(QIcon(icon_path_png))
    elif os.path.exists(icon_path_ico):
        app.setWindowIcon(QIcon(icon_path_ico))
    
    # Create and show main window
    main_window = TDMSMainWindow()
    main_window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
