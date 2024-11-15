from PyQt5.QtCore import QRunnable, QThread
from worker_signals import TableWorkerSignals

class TableWorker(QRunnable):
    def __init__(self, data_pairs, chunk_size=1000, start_col=0):
        super().__init__()
        self.data_pairs = data_pairs
        self.chunk_size = chunk_size
        self.start_col = start_col
        self.signals = TableWorkerSignals()
        self.should_continue = True

    def run(self):
        try:
            chunks = []
            for x_data, y_data, _ in self.data_pairs:
                chunks.append((x_data, y_data))
            max_rows = max(len(x) for x, _ in chunks)
            current_row = 0
            while current_row < max_rows and self.should_continue:
                chunk_data = self.process_chunk(chunks, current_row)
                self.signals.chunk_ready.emit(current_row, chunk_data, self.start_col)
                current_row += self.chunk_size
                QThread.msleep(1)
            if self.should_continue:
                self.signals.finished.emit()
        except Exception as e:
            print(f"Error in TableWorker: {e}")

    def process_chunk(self, chunks, start_row):
        end_row = min(start_row + self.chunk_size, max(len(x) for x, _ in chunks))
        chunk_data = []
        for row in range(start_row, end_row):
            row_data = []
            for x_arr, y_arr in chunks:
                if row < len(x_arr):
                    x_val = x_arr[row]
                    y_val = y_arr[row]
                    x_str = f"{x_val:.6f}" if isinstance(x_val, (int, float)) else str(x_val)
                    y_str = f"{y_val:.6f}" if isinstance(y_val, (int, float)) else str(y_val)
                    row_data.extend([x_str, y_str])
                else:
                    row_data.extend(["", ""])
            chunk_data.append(row_data)
        return chunk_data
