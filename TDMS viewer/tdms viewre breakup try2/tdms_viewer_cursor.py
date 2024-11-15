from PyQt5.QtWidgets import QLabel, QComboBox, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

class TDMSViewerCursor:
    def setup_ui_cursor(self):
        # Add cursor info panel
        self.cursor_info_panel = QWidget()
        cursor_info_layout = QHBoxLayout(self.cursor_info_panel)
        cursor_info_layout.setSpacing(10)
        self.cursor_snap_selector = QComboBox()
        self.cursor_snap_selector.setMinimumWidth(150)
        cursor_info_layout.addWidget(QLabel("Snap to:"))
        cursor_info_layout.addWidget(self.cursor_snap_selector)
        self.cursor_x_label = QLabel("X: -")
        self.cursor_y_label = QLabel("Y: -")
        self.cursor_delta_x = QLabel("ΔX: -")
        self.cursor_delta_y = QLabel("ΔY: -")
        for label in [self.cursor_x_label, self.cursor_y_label, self.cursor_delta_x, self.cursor_delta_y]:
            cursor_info_layout.addWidget(label)
        cursor_info_layout.addStretch()
        self.center_layout.addWidget(self.cursor_info_panel)

    def initialize_cursor_variables(self):
        self.cursor_enabled = False
        self.cursor_vline = None
        self.cursor_vline2 = None
        self.cursor_active = 1
        self.cursor_positions = [None, None]
        self.cursor_y_values = [None, None]
        self.current_snap_plot = None

    def connect_cursor_signals(self):
        self.cursor_btn.clicked.connect(self.toggle_cursor)
        self.center_cursor_btn.clicked.connect(self.center_cursors)
        self.cursor_snap_selector.currentIndexChanged.connect(self.on_snap_changed)

    def toggle_cursor(self):
        """Toggle cursor visibility and functionality"""
        self.cursor_enabled = self.cursor_btn.isChecked()
        if self.cursor_enabled:
            # Create cursors if they don't exist
            if not self.cursor_vline:
                pen1 = pg.mkPen({'color': '#FF69B4', 'width': 4, 'style': Qt.PenStyle.DashLine})
                pen2 = pg.mkPen({'color': '#FFA500', 'width': 4, 'style': Qt.PenStyle.DashLine})
                self.cursor_vline = pg.InfiniteLine(angle=90, movable=True, pen=pen1)
                self.cursor_hline = pg.InfiniteLine(angle=0, movable=True, pen=pen1)
                self.cursor_vline2 = pg.InfiniteLine(angle=90, movable=True, pen=pen2)
                self.cursor_hline2 = pg.InfiniteLine(angle=0, movable=True, pen=pen2)
                self.cursor_vline.setZValue(1000)
                self.cursor_hline.setZValue(1000)
                self.cursor_vline2.setZValue(1000)
                self.cursor_hline2.setZValue(1000)
                self.cursor_vline.sigPositionChanged.connect(lambda: self.on_cursor_dragged(1))
                self.cursor_vline2.sigPositionChanged.connect(lambda: self.on_cursor_dragged(2))
                self.cursor_hline.sigPositionChanged.connect(lambda: self.on_cursor_dragged(1))
                self.cursor_hline2.sigPositionChanged.connect(lambda: self.on_cursor_dragged(2))
            # Position cursors
            view_range = self.graph_widget.getPlotItem().viewRange()
            x_min, x_max = view_range[0]
            x1 = x_min + (x_max - x_min) * 0.4
            x2 = x_min + (x_max - x_min) * 0.6
            y1 = self.get_y_value_at_x(x1)
            y2 = self.get_y_value_at_x(x2)
            self.graph_widget.removeItem(self.cursor_vline)
            self.graph_widget.removeItem(self.cursor_hline)
            self.graph_widget.removeItem(self.cursor_vline2)
            self.graph_widget.removeItem(self.cursor_hline2)
            self.graph_widget.addItem(self.cursor_vline)
            self.graph_widget.addItem(self.cursor_hline)
            self.graph_widget.addItem(self.cursor_vline2)
            self.graph_widget.addItem(self.cursor_hline2)
            self.cursor_vline.setPos(x1)
            self.cursor_hline.setPos(y1 if y1 is not None else 0)
            self.cursor_vline2.setPos(x2)
            self.cursor_hline2.setPos(y2 if y2 is not None else 0)
            self.cursor_positions = [x1, x2]
            self.cursor_y_values = [y1, y2]
            self.cursor_vline.show()
            self.cursor_hline.show()
            self.cursor_vline2.show()
            self.cursor_hline2.show()
            self.update_cursor_info()
            try:
                self.graph_widget.scene().sigMouseMoved.disconnect(self.cursor_moved)
            except TypeError:
                pass
        else:
            if self.cursor_vline:
                self.cursor_vline.hide()
                self.cursor_hline.hide()
                self.cursor_vline2.hide()
                self.cursor_hline2.hide()
            self.cursor_positions = [None, None]
            self.cursor_y_values = [None, None]
            self.cursor_active = 1
            self.update_cursor_info()

    def on_cursor_dragged(self, cursor_num):
        v_cursor = self.cursor_vline if cursor_num == 1 else self.cursor_vline2
        h_cursor = self.cursor_hline if cursor_num == 1 else self.cursor_hline2
        x_pos = v_cursor.getXPos()
        y_pos = h_cursor.getYPos()
        y_val = self.get_y_value_at_x(x_pos)
        if y_val is not None:
            h_cursor.setPos(y_val)
            y_pos = y_val
        idx = cursor_num - 1
        self.cursor_positions[idx] = x_pos
        self.cursor_y_values[idx] = y_pos
        self.update_cursor_info()

    def get_y_value_at_x(self, x):
        closest_y = None
        min_distance = float('inf')
        for plot in self.current_plots.values():
            data = plot.getData()
            if len(data[0]) == 0:
                continue
            idx = np.searchsorted(data[0], x)
            if idx >= len(data[0]):
                idx = len(data[0]) - 1
            distance = abs(data[0][idx] - x)
            if distance < min_distance:
                min_distance = distance
                closest_y = data[1][idx]
        return closest_y

    def update_cursor_info(self):
        if None in self.cursor_positions:
            self.cursor_x_label.setText("X1: - | X2: -")
            self.cursor_y_label.setText("Y1: - | Y2: -")
            self.cursor_delta_x.setText("ΔX: -")
            self.cursor_delta_y.setText("ΔY: -")
            return
        x1, x2 = self.cursor_positions
        y1, y2 = self.cursor_y_values
        self.cursor_x_label.setText(f"X1: {self.format_si_prefix(x1)} | X2: {self.format_si_prefix(x2)}")
        self.cursor_y_label.setText(f"Y1: {self.format_si_prefix(y1)} | Y2: {self.format_si_prefix(y2)}")
        delta_x = abs(x2 - x1)
        delta_y = abs(y2 - y1)
        self.cursor_delta_x.setText(f"ΔX: {self.format_si_prefix(delta_x)}")
        self.cursor_delta_y.setText(f"ΔY: {self.format_si_prefix(delta_y)}")

    def format_si_prefix(self, value):
        prefixes = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        negative_prefixes = ['', 'm', 'µ', 'n', 'p', 'f', 'a', 'z', 'y']
        if value == 0:
            return "0"
        abs_value = abs(value)
        prefix_index = 0
        if abs_value >= 1:
            while abs_value >= 1000 and prefix_index < len(prefixes) - 1:
                abs_value /= 1000
                prefix_index += 1
            prefix = prefixes[prefix_index]
        else:
            while abs_value < 1 and prefix_index < len(negative_prefixes) - 1:
                abs_value *= 1000
                prefix_index += 1
            prefix = negative_prefixes[prefix_index]
        return f"{abs_value * (1 if value >= 0 else -1):.3f} {prefix}"

