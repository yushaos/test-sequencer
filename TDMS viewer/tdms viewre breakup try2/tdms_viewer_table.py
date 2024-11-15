from PyQt5.QtWidgets import QTableWidgetItem, QProgressBar
from PyQt5.QtCore import QTimer, QTime, QThreadPool
from table_worker import TableWorker
from cache import TableCache, SignalCache

class TDMSViewerTable:
    def setup_ui_table(self):
        # Add progress bar for table loading
        self.table_progress = QProgressBar()
        self.table_progress.setMaximumHeight(2)
        self.table_progress.setTextVisible(False)
        self.table_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: transparent;
            }
            QProgressBar::chunk {
                background-color: #ADD8E6;
            }
        """)
        self.table_progress.hide()
        # Insert progress bar into the layout
        self.center_layout.insertWidget(1, self.table_progress)

    def initialize_table_variables(self):
        self.table_cache = TableCache()
        self.is_table_loading = False
        self.current_table_worker = None
        self.table_worker_id = 0
        self.last_scroll_update = 0
        self.threadpool = QThreadPool()

    def connect_table_signals(self):
        self.table_widget.verticalScrollBar().valueChanged.connect(self.on_table_scrolled)
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def update_table(self, group_name, channel_name):
        # Cancel any existing table worker
        if self.current_table_worker:
            self.current_table_worker.should_continue = False
        # Increment worker ID
        self.table_worker_id += 1
        current_id = self.table_worker_id
        # Get first two plot keys only
        current_plots = list(self.current_plots.keys())[:2]
        # Setup headers for at most two signals
        headers = []
        data_pairs = []
        for signal_key in current_plots:
            group, channel = signal_key.split('/')
            value_channel = self.current_tdms[group][channel]
            time_channel = None
            # Try to get mapped time channel
            mapped_time_channel = self.signal_mapper.get_x_signal(channel)
            if mapped_time_channel:
                try:
                    time_channel = self.current_tdms[group][mapped_time_channel]
                except KeyError:
                    pass
            if not time_channel:
                time_channel_name = f"{channel}_Time"
                for ch in self.current_tdms[group].channels():
                    if ch.name.lower() == time_channel_name.lower():
                        time_channel = ch
                        break
            if time_channel is None:
                continue
            headers.extend([f"{channel} Time", f"{channel} Value"])
            data_pairs.append((time_channel[:], value_channel[:], channel))
        # Setup table structure
        self.setup_table_structure(headers)
        # Load data if we have any
        if data_pairs:
            self.table_cache.plot_keys = set(current_plots)
            self.load_table_data(data_pairs, current_id)

    def setup_table_structure(self, headers):
        self.table_widget.clear()
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        # Hide row numbers (vertical header)
        self.table_widget.verticalHeader().setVisible(False)
        # Set column widths
        for col in range(len(headers)):
            self.table_widget.setColumnWidth(col, 150)
        # Calculate max rows from current plots
        max_rows = 0
        for signal_key in self.current_plots.keys():
            group, channel = signal_key.split('/')
            cache = self.get_cached_signal_data(group, channel)
            if cache and cache.x_data is not None:
                max_rows = max(max_rows, len(cache.x_data))
        # Ensure max_rows is at least 1
        max_rows = max(1, max_rows)
        self.table_widget.setRowCount(max_rows)
        self.table_cache.max_rows = max_rows
        self.table_cache.headers = headers

    def load_table_data(self, data_pairs, worker_id):
        if not data_pairs:
            self.is_table_loading = False
            self.table_progress.hide()
            return
        self.table_worker = TableWorker(data_pairs)
        self.current_table_worker = self.table_worker
        self.table_worker.worker_id = worker_id
        self.table_worker.signals.chunk_ready.connect(
            lambda start_row, chunk_data, start_col:
            self.on_incremental_chunk_ready(start_row, chunk_data, start_col, worker_id)
        )
        self.table_worker.signals.finished.connect(
            lambda: self.on_table_load_finished(worker_id)
        )
        self.threadpool.start(self.table_worker)

    def on_incremental_chunk_ready(self, start_row, chunk_data, start_col, worker_id):
        if worker_id != self.table_worker_id:
            return
        try:
            # Ensure table has enough rows
            if self.table_widget.rowCount() <= start_row + len(chunk_data):
                self.table_widget.setRowCount(start_row + len(chunk_data))
            # Update table with chunk data
            for row_offset, row_data in enumerate(chunk_data):
                row = start_row + row_offset
                for col_offset, value in enumerate(row_data):
                    if value:  # Only set non-empty values
                        self.table_widget.setItem(row, start_col + col_offset,
                                                  QTableWidgetItem(str(value)))
            # Update progress
            if self.table_cache.max_rows > 0:
                progress = min(100, (start_row / self.table_cache.max_rows) * 100)
                self.table_progress.setValue(int(progress))
        except Exception as e:
            print(f"Error in incremental update: {e}")

    def on_table_load_finished(self, worker_id):
        if worker_id == self.table_worker_id:
            self.is_table_loading = False
            self.table_cache.is_fully_loaded = True
            self.table_progress.hide()

    def on_table_scrolled(self):
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if current_time - self.last_scroll_update < 100:  # Limit updates to every 100ms
            return
        self.last_scroll_update = current_time
        visible_rect = self.table_widget.viewport().rect()
        first_visible_row = self.table_widget.rowAt(visible_rect.top())
        last_visible_row = self.table_widget.rowAt(visible_rect.bottom())
        if first_visible_row is not None and last_visible_row is not None:
            # Load a range around visible area
            start_row = max(0, first_visible_row - 500)
            self.load_cached_data_chunk(start_row, 0)

    def on_tab_changed(self, index):
        if index == 1:  # Table tab
            current_plots = set(self.current_plots.keys())
            # Only update table if plots have changed or table is empty
            if (current_plots != self.table_cache.plot_keys or
                self.table_widget.rowCount() == 0 or
                self.table_widget.columnCount() == 0):
                self.update_table(None, None)

    def get_cached_signal_data(self, group_name, channel_name):
        if not self.current_tdms:
            return None
        cache_key = f"{group_name}/{channel_name}"
        if cache_key not in self.signal_cache:
            value_channel = self.current_tdms[group_name][channel_name]
            time_channel_name = f"{channel_name}_Time"
            time_channel = None
            for ch in self.current_tdms[group_name].channels():
                if ch.name.lower() == time_channel_name.lower():
                    time_channel = ch
                    break
            if time_channel:
                cache = SignalCache()
                cache.x_data = time_channel[:]
                cache.y_data = value_channel[:]
                self.signal_cache[cache_key] = cache
        return self.signal_cache.get(cache_key)

    def load_cached_data_chunk(self, start_row, chunk_index, chunk_size=1000):
        if start_row >= self.table_cache.max_rows:
            return
        end_row = min(start_row + chunk_size, self.table_cache.max_rows)
        visible_rect = self.table_widget.viewport().rect()
        first_visible_row = self.table_widget.rowAt(visible_rect.top())
        last_visible_row = self.table_widget.rowAt(visible_rect.bottom())
        if (first_visible_row is not None and
            last_visible_row is not None and
            (start_row > last_visible_row + 1000 or end_row < first_visible_row - 1000)):
            if chunk_index * chunk_size < self.table_cache.max_rows:
                QTimer.singleShot(0, lambda: self.load_cached_data_chunk(
                    start_row + chunk_size, chunk_index + 1, chunk_size))
            return
        # Load the chunk
        for row in range(start_row, end_row):
            data_pairs = []
            for signal_key in self.current_plots.keys():
                group, channel = signal_key.split('/')
                cache = self.get_cached_signal_data(group, channel)
                if cache and cache.x_data is not None and row < len(cache.x_data):
                    data_pairs.extend([
                        f"{cache.x_data[row]:.6f}",
                        f"{cache.y_data[row]:.6f}"
                    ])
                else:
                    data_pairs.extend(["", ""])
            for col, value in enumerate(data_pairs):
                if value:
                    self.table_widget.setItem(row, col, QTableWidgetItem(value))
        # Schedule next chunk if needed
        if end_row < self.table_cache.max_rows:
            QTimer.singleShot(0, lambda: self.load_cached_data_chunk(
                end_row, chunk_index + 1, chunk_size))
