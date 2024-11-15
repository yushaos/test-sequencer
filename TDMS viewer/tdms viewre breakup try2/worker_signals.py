from PyQt5.QtCore import QObject, pyqtSignal

class WorkerSignals(QObject):
    finished = pyqtSignal(str, object, object, str)

class PlotWorkerSignals(QObject):
    chunk_ready = pyqtSignal(str, object, object, str, bool)
    progress = pyqtSignal(int)
    data_stored = pyqtSignal(str, object, object)

class TableWorkerSignals(QObject):
    chunk_ready = pyqtSignal(int, list, int)
    finished = pyqtSignal()
