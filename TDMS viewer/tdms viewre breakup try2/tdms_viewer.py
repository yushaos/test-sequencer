from PyQt5.QtWidgets import QMainWindow
from tdms_viewer_ui import TDMSViewerUI
from tdms_viewer_file import TDMSViewerFile
from tdms_viewer_plot import TDMSViewerPlot
from tdms_viewer_table import TDMSViewerTable
from tdms_viewer_cursor import TDMSViewerCursor

class TDMSViewer(QMainWindow, TDMSViewerUI, TDMSViewerFile, TDMSViewerPlot, TDMSViewerTable, TDMSViewerCursor):
    def __init__(self):
        super().__init__()
        self.setup_ui_main()       # From TDMSViewerUI
        self.setup_ui_file()       # From TDMSViewerFile
        self.setup_ui_plot()       # From TDMSViewerPlot
        self.setup_ui_table()      # From TDMSViewerTable
        self.setup_ui_cursor()     # From TDMSViewerCursor

        self.initialize_ui_variables()       # From TDMSViewerUI
        self.initialize_file_variables()     # From TDMSViewerFile
        self.initialize_plot_variables()     # From TDMSViewerPlot
        self.initialize_table_variables()    # From TDMSViewerTable
        self.initialize_cursor_variables()   # From TDMSViewerCursor

        self.connect_ui_signals()            # From TDMSViewerUI
        self.connect_file_signals()          # From TDMSViewerFile
        self.connect_plot_signals()          # From TDMSViewerPlot
        self.connect_table_signals()         # From TDMSViewerTable
        self.connect_cursor_signals()        # From TDMSViewerCursor
