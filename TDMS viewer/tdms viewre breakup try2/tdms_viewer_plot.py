from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLabel, QTreeWidgetItem
from PyQt5.QtCore import QThreadPool, Qt
from plot_worker import PlotWorker
import pyqtgraph as pg
import numpy as np

class TDMSViewerPlot:
    def setup_ui_plot(self):
        pass  # UI elements are set up in TDMSViewerUI

    def initialize_plot_variables(self):
        self.current_plots = {}
        self.colors = ['blue', 'red', 'green', 'purple', 'orange', 'cyan', 'magenta', 'yellow']
        self.color_index = 0
        self.threadpool = QThreadPool()
        self.selection_order = 0
        self.progress_items = {}
        self.signal_cache = {}
        self.current_worker = None

    def connect_plot_signals(self):
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.reset_btn.clicked.connect(self.reset_zoom)
        self.graph_widget.getPlotItem().getViewBox().sigRangeChanged.connect(self.on_range_changed)
        self.apply_range_btn.clicked.connect(self.apply_manual_range)
        self.signal_tree.itemClicked.connect(self.on_signal_selected)

    def on_signal_selected(self, item, column):
        if not item.parent():
            group_name = item.text(0)
            self.update_properties(group_name, None)
            return
        group_name = item.parent().text(0)
        channel_name = item.text(0)
        signal_key = f"{group_name}/{channel_name}"
        if signal_key not in self.current_plots:
            self.plot_channel(group_name, channel_name)
        self.current_selected_signal = (group_name, channel_name)
        self.update_properties(group_name, channel_name)

    def plot_channel(self, group_name, channel_name):
        value_channel = self.current_tdms[group_name][channel_name]
        mapped_time_channel = self.signal_mapper.get_x_signal(channel_name)
        time_channel = None
        if mapped_time_channel:
            try:
                time_channel = self.current_tdms[group_name][mapped_time_channel]
            except KeyError:
                print(f"Warning: Mapped time channel {mapped_time_channel} not found")
        if not time_channel:
            time_channel_name = f"{channel_name}_Time"
            for ch in self.current_tdms[group_name].channels():
                if ch.name.lower() == time_channel_name.lower():
                    time_channel = ch
                    break
        signal_key = f"{group_name}/{channel_name}"
        if signal_key not in self.current_plots:
            color = self.colors[self.selection_order % len(self.colors)]
            self.selection_order += 1
            if time_channel is None:
                time_channel = np.arange(len(value_channel))
            worker = PlotWorker(signal_key, value_channel, time_channel, color)
            worker.signals.chunk_ready.connect(self.plot_chunk_finished)
            self.current_worker = worker
            self.threadpool.start(worker)
            if len(self.current_plots) == 0:
                self.graph_widget.getPlotItem().enableAutoRange()
            progress_item = QTreeWidgetItem()
            progress_item.setText(0, "Loading: 0%")
            self.progress_items[signal_key] = progress_item

    def plot_chunk_finished(self, signal_key, plot_data, time_data, color, is_final):
        if signal_key not in self.current_plots:
            pen = pg.mkPen(color=color, width=2)
            plot = self.graph_widget.plot(time_data, plot_data, pen=pen)
            self.current_plots[signal_key] = plot
            legend_item = QTreeWidgetItem(self.legend_list)
            channel_name = signal_key.split('/')[1]
            legend_item.setText(0, channel_name)
            color_box = f'<div style="background-color: {color}; width: 20px; height: 10px; border: 1px solid black;"></div>'
            legend_item.setText(1, "")
            legend_item.setData(1, Qt.DisplayRole, "")
            self.legend_list.setItemWidget(legend_item, 1, QLabel(color_box))
            if signal_key in self.progress_items:
                legend_item.removeChild(self.progress_items[signal_key])
                del self.progress_items[signal_key]
            group_name, channel_name = signal_key.split('/')
            self.current_selected_signal = (group_name, channel_name)
            self.update_properties(group_name, channel_name)
            self.update_snap_selector()
            if self.tabs.currentIndex() == 1:
                self.update_table(group_name, channel_name)
            self.maintain_cursors()
        else:
            self.current_plots[signal_key].setData(time_data, plot_data)

    def update_properties(self, group_name, channel_name):
        self.properties_widget.clear()
        try:
            if channel_name:
                channel = self.current_tdms[group_name][channel_name]
                signal_name = QTreeWidgetItem(self.properties_widget, [f"Signal: {group_name}/{channel_name}"])
                signal_name.setBackground(0, pg.mkColor(200, 220, 255))
                basic_props = QTreeWidgetItem(self.properties_widget, ["Basic Properties:"])
                QTreeWidgetItem(basic_props, [f"Name: {channel_name}"])
                QTreeWidgetItem(basic_props, [f"Length: {len(channel)}"])
                QTreeWidgetItem(basic_props, [f"Data Type: {channel.dtype}"])
                if hasattr(channel, 'description'):
                    QTreeWidgetItem(basic_props, [f"Description: {channel.description}"])
                if channel.properties:
                    props_item = QTreeWidgetItem(self.properties_widget, ["Custom Properties:"])
                    for prop, value in channel.properties.items():
                        QTreeWidgetItem(props_item, [f"{prop}: {value}"])
            else:
                group = self.current_tdms[group_name]
                group_name_item = QTreeWidgetItem(self.properties_widget, [f"Group: {group_name}"])
                group_name_item.setBackground(0, pg.mkColor(200, 220, 255))
                basic_props = QTreeWidgetItem(self.properties_widget, ["Basic Properties:"])
                QTreeWidgetItem(basic_props, [f"Name: {group_name}"])
                QTreeWidgetItem(basic_props, [f"Channel Count: {len(group.channels())}"])
                if group.properties:
                    props_item = QTreeWidgetItem(self.properties_widget, ["Custom Properties:"])
                    for prop, value in group.properties.items():
                        QTreeWidgetItem(props_item, [f"{prop}: {value}"])
            self.properties_widget.expandAll()
        except Exception as e:
            print(f"Error updating properties: {e}")

    def update_snap_selector(self):
        self.cursor_snap_selector.clear()
        for signal_key in self.current_plots.keys():
            channel = signal_key.split('/')[1]
            self.cursor_snap_selector.addItem(channel, signal_key)
        if self.current_plots:
            first_signal = next(iter(self.current_plots))
            self.current_snap_plot = self.current_plots[first_signal]

    def maintain_cursors(self):
        if self.cursor_enabled and self.cursor_vline:
            self.graph_widget.removeItem(self.cursor_vline)
            self.graph_widget.removeItem(self.cursor_hline)
            self.graph_widget.removeItem(self.cursor_vline2)
            self.graph_widget.removeItem(self.cursor_hline2)
            self.graph_widget.addItem(self.cursor_vline)
            self.graph_widget.addItem(self.cursor_hline)
            self.graph_widget.addItem(self.cursor_vline2)
            self.graph_widget.addItem(self.cursor_hline2)

