import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import os
from utils import get_application_path
from tdms_viewer import TDMSViewer

if __name__ == '__main__':
    app = QApplication(sys.argv)
    icon_path_ico = os.path.join(get_application_path(), 'TDMS viewer icon.ico')
    if os.path.exists(icon_path_ico):
        app.setWindowIcon(QIcon(icon_path_ico))
    viewer = TDMSViewer()
    viewer.show()
    sys.exit(app.exec())
