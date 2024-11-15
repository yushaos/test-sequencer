from PyQt5.QtCore import QRunnable
import numpy as np
from scipy import signal
from worker_signals import PlotWorkerSignals

class PlotWorker(QRunnable):
    def __init__(self, signal_key, value_channel, time_channel, color):
        super().__init__()
        self.signal_key = signal_key
        self.value_channel = value_channel
        self.time_channel = time_channel
        self.color = color
        self.signals = PlotWorkerSignals()
        self.should_continue = True
        self.INITIAL_POINTS = 1000000

    def run(self):
        try:
            y_data = np.array(self.value_channel[:], dtype=np.float64)
            x_data = np.array(self.time_channel[:], dtype=np.float64)
            y_data[~np.isfinite(y_data)] = np.nan
            x_data[~np.isfinite(x_data)] = np.nan
            if len(x_data) > self.INITIAL_POINTS:
                x_decimated, y_decimated = self.decimate_data(x_data, y_data, self.INITIAL_POINTS)
                self.signals.chunk_ready.emit(self.signal_key, y_decimated, x_decimated, self.color, True)
            else:
                self.signals.chunk_ready.emit(self.signal_key, y_data, x_data, self.color, True)
            self.signals.data_stored.emit(self.signal_key, y_data, x_data)
        except Exception as e:
            print(f"Error in PlotWorker: {e}")

    def decimate_data(self, x_data, y_data, target_points=1000000):
        if len(x_data) <= target_points:
            return x_data, y_data
        factor = max(1, len(x_data) // target_points)
        decimated_y = signal.decimate(y_data, factor, zero_phase=True)
        decimated_x = x_data[::factor]
        return decimated_x, decimated_y
