"""
Custom tree widget for TDMS signal selection
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from typing import Optional, List, Set, Tuple

from core.tdms_handler import TDMSHandler

class SignalTreeWidget(QTreeWidget):
    """Tree widget for displaying and selecting TDMS signals"""
    
    # Custom signals
    signal_selected = pyqtSignal(str, str)  # group_name, channel_name
    signal_deselected = pyqtSignal(str, str)  # group_name, channel_name
    selection_changed = pyqtSignal()  # General selection change notification
    
    def __init__(self):
        super().__init__()
        
        self.selected_signals: Set[Tuple[str, str]] = set()  # (group, channel) pairs
        self.current_tdms: Optional[TDMSHandler] = None
        
        # Selection tracking
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.first_selected_item: Optional[QTreeWidgetItem] = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup widget UI"""
        # Configure tree widget
        self.setHeaderHidden(True)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        
        # Set style for selection highlighting
        self.setStyleSheet("""
            QTreeWidget::item:selected {
                background-color: #ADD8E6;
            }
        """)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.itemClicked.connect(self.on_item_clicked)
        
        # Install event filter for keyboard modifiers
        self.installEventFilter(self)
    
    def update_tree(self, tdms_handler: TDMSHandler) -> None:
        """
        Update tree with TDMS file contents
        
        Args:
            tdms_handler: TDMS file handler
        """
        self.current_tdms = tdms_handler
        self.clear()
        self.selected_signals.clear()
        
        # Add groups and channels
        for group in tdms_handler.get_groups():
            group_item = QTreeWidgetItem([group.name])
            self.addTopLevelItem(group_item)
            
            for channel in tdms_handler.get_channels(group.name):
                # Skip time channels
                if not channel.name.lower().endswith('_time'):
                    channel_item = QTreeWidgetItem([channel.name])
                    group_item.addChild(channel_item)
        
        # Expand all items
        self.expandAll()
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle item click events
        
        Args:
            item: Clicked tree item
            column: Clicked column
        """
        if not item.parent():  # It's a group item
            return
            
        group_name = item.parent().text(0)
        channel_name = item.text(0)
        signal_key = (group_name, channel_name)
        
        if self.shift_pressed and self.first_selected_item:
            self.select_signal_range(self.first_selected_item, item)
            return
        
        if not (self.ctrl_pressed or self.shift_pressed):
            # Clear previous selection if not multi-selecting
            self.clear_selection()
            self.first_selected_item = item
        
        if signal_key in self.selected_signals:
            # Deselect signal
            self.selected_signals.remove(signal_key)
            item.setSelected(False)
            self.signal_deselected.emit(group_name, channel_name)
        else:
            # Select signal
            self.selected_signals.add(signal_key)
            item.setSelected(True)
            self.signal_selected.emit(group_name, channel_name)
        
        self.selection_changed.emit()
    
    def select_signal_range(self, first_item: QTreeWidgetItem, 
                          last_item: QTreeWidgetItem) -> None:
        """
        Select range of signals
        
        Args:
            first_item: First item in range
            last_item: Last item in range
        """
        if not first_item.parent() or not last_item.parent():
            return
        
        # Get all items in tree
        all_items = self.get_all_channel_items()
        
        # Find indices of first and last items
        try:
            first_idx = all_items.index(first_item)
            last_idx = all_items.index(last_item)
        except ValueError:
            return
        
        # Determine range based on which index is smaller
        start_idx = min(first_idx, last_idx)
        end_idx = max(first_idx, last_idx)
        
        # Clear previous selection if not using Ctrl
        if not self.ctrl_pressed:
            self.clear_selection()
        
        # Select all items in range
        for idx in range(start_idx, end_idx + 1):
            item = all_items[idx]
            group_name = item.parent().text(0)
            channel_name = item.text(0)
            signal_key = (group_name, channel_name)
            
            if signal_key not in self.selected_signals:
                self.selected_signals.add(signal_key)
                item.setSelected(True)
                self.signal_selected.emit(group_name, channel_name)
        
        self.selection_changed.emit()
    
    def get_all_channel_items(self) -> List[QTreeWidgetItem]:
        """
        Get all channel items in tree
        
        Returns:
            List of channel items
        """
        items = []
        for i in range(self.topLevelItemCount()):
            group = self.topLevelItem(i)
            for j in range(group.childCount()):
                items.append(group.child(j))
        return items
    
    def clear_selection(self) -> None:
        """Clear current selection"""
        # Emit deselected signals
        for group_name, channel_name in self.selected_signals:
            self.signal_deselected.emit(group_name, channel_name)
        
        self.selected_signals.clear()
        super().clearSelection()
        self.selection_changed.emit()
    
    def eventFilter(self, obj, event) -> bool:
        """
        Filter events for keyboard modifier tracking
        
        Args:
            obj: Event object
            event: Event type
            
        Returns:
            True if event was handled
        """
        if obj == self:
            if event.type() == event.KeyPress:
                if event.key() == Qt.Key_Control:
                    self.ctrl_pressed = True
                    self.setSelectionMode(QTreeWidget.MultiSelection)
                elif event.key() == Qt.Key_Shift:
                    self.shift_pressed = True
                    self.setSelectionMode(QTreeWidget.MultiSelection)
            elif event.type() == event.KeyRelease:
                if event.key() == Qt.Key_Control:
                    self.ctrl_pressed = False
                    if not self.shift_pressed:
                        self.setSelectionMode(QTreeWidget.SingleSelection)
                elif event.key() == Qt.Key_Shift:
                    self.shift_pressed = False
                    if not self.ctrl_pressed:
                        self.setSelectionMode(QTreeWidget.SingleSelection)
        
        return super().eventFilter(obj, event)
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events"""
        # Could be implemented to handle file drops
        event.ignore()
    
    def get_selected_signals(self) -> List[Tuple[str, str]]:
        """
        Get currently selected signals
        
        Returns:
            List of (group_name, channel_name) tuples
        """
        return list(self.selected_signals)
