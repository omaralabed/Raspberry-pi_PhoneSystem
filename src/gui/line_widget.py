#!/usr/bin/env python3
"""
Line Widget - Individual Phone Line Status Display
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont
import logging

from ..phone_line import PhoneLine, LineState, AudioOutput
from .dialer_widget import DialerWidget

logger = logging.getLogger(__name__)


class LineWidget(QWidget):
    """
    Widget displaying status of a single phone line
    """
    
    # Signals
    hangup_clicked = pyqtSignal(int)  # line_id
    dial_clicked = pyqtSignal(int)  # line_id - emitted when DIAL button clicked
    make_call = pyqtSignal(int, str)  # line_id, phone_number - emitted to make a call
    audio_channel_changed = pyqtSignal(int, int)  # line_id, channel
    
    def __init__(self, line: PhoneLine, parent=None):
        """
        Initialize line widget
        
        Args:
            line: PhoneLine object
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.line = line
        self.is_selected = False
        
        # Cache for state to avoid redundant updates
        self._last_state = None
        self._last_channel = None
        self._last_selected = None
        self._last_style_state = None  # Cache for style to avoid expensive updates
        
        self._create_ui()
        self.update_display()
        
        logger.debug(f"Line widget created for line {line.line_id}")
    
    def _create_ui(self):
        """Create line widget UI - Broadcast professional style"""
        # No fixed height - fully adaptive to available space
        
        # Main frame with broadcast styling
        self.frame = QFrame(self)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #2d2420;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QFrame:hover {
                background-color: #3a332d;
                border-color: #ff6b35;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.frame)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(8)
        
        # Top row: Line number and audio label
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Line number label (not clickable anymore - use dropdown instead)
        line_label = QLabel(f"Line {self.line.line_id}")
        line_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        line_label.setStyleSheet("""
            QLabel {
                color: #ff6b35;
                padding: 2px 5px;
            }
        """)
        top_row.addWidget(line_label)
        
        top_row.addStretch()
        
        self.audio_label = QLabel("IFB")
        self.audio_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.audio_label.setAlignment(Qt.AlignCenter)
        self.audio_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: #0ea5e9;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 85px;
                max-width: 100px;
            }
        """)
        top_row.addWidget(self.audio_label)
        
        frame_layout.addLayout(top_row)
        
        # Status label with modern font and more space
        self.status_label = QLabel("Available")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #95e1d3;
                padding: 6px 0px 8px 0px;
                min-height: 25px;
            }
        """)
        frame_layout.addWidget(self.status_label)
        
        # Button row - channel picker and hangup button side by side
        button_row = QHBoxLayout()
        button_row.setSpacing(15)  # Safe distance between buttons
        
        # Audio channel picker with modern styling
        self.channel_picker = QComboBox()
        # Remove fixed sizes - let it adapt
        self.channel_picker.addItem("🔇 None ▼", 0)  # No output with icon and down arrow
        for i in range(1, 9):
            self.channel_picker.addItem(f"🔊 {i}", i)
        self.channel_picker.setCurrentIndex(0)  # Default to None (matches phone_line default)
        self.channel_picker.currentIndexChanged.connect(self._on_channel_changed)
        self.channel_picker.setStyleSheet("""
            QComboBox {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a5568,
                    stop:1 #2d3748
                );
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
            QComboBox:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6578,
                    stop:1 #3d4758
                );
                border: 2px solid rgba(0, 212, 255, 0.5);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 0px;
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                selection-background-color: #00d4ff;
                selection-color: #1a1a2e;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        button_row.addWidget(self.channel_picker)
        
        # Hangup button next to picker with safe spacing
        # Action button - DIAL when idle, HANGUP when active
        self.action_btn = QPushButton("📞 DIAL")
        self.action_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.action_btn.clicked.connect(self._on_action_clicked)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2ed573,
                    stop:1 #26de81
                );
                color: white;
                border: 3px solid white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3ee583,
                    stop:1 #36ee91
                );
                border: 3px solid #00d4ff;
            }
            QPushButton:pressed {
                background: #1ea755;
                padding: 9px 14px 7px 16px;
            }
        """)
        button_row.addWidget(self.action_btn)
        
        frame_layout.addLayout(button_row)
    
    def _on_action_clicked(self):
        """Handle action button click - either dial or hangup based on line state"""
        is_active = self.line.is_active()
        if is_active:
            # Line is active - hangup
            self._on_hangup()
        else:
            # Line is idle - show popup dialer
            logger.info(f"[LineWidget] Dial button clicked for line {self.line.line_id}")
            self._show_popup_dialer()
    
    def _show_popup_dialer(self):
        """Show a large popup dialer for this line"""
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Dial - Line {self.line.line_id}")
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Line label
        line_label = QLabel(f"Line {self.line.line_id}")
        line_label.setStyleSheet("""
            QLabel {
                color: #ff6b35;
                font-size: 28px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        line_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(line_label)
        
        # Create dialer widget
        dialer = DialerWidget(dialog)
        layout.addWidget(dialer)
        
        # Connect dialer call signal
        def on_call(phone_number):
            logger.info(f"[LineWidget] Calling {phone_number} on line {self.line.line_id}")
            dialog.accept()
            # Emit signal to main window to make the call
            self.make_call.emit(self.line.line_id, phone_number)
        
        dialer.call_requested.connect(on_call)
        
        # Add Cancel button at the bottom
        cancel_btn = QPushButton("✖ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #555555, stop:1 #444444);
                color: white;
                border: 2px solid #666666;
                border-radius: 8px;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #666666, stop:1 #555555);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #333333, stop:1 #222222);
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        # Set dialog size - large and comfortable
        dialog.resize(800, 900)
        
        # Center on parent widget
        if self.window():
            parent_geo = self.window().geometry()
            dialog_geo = dialog.geometry()
            x = parent_geo.x() + (parent_geo.width() - dialog_geo.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - dialog_geo.height()) // 2
            dialog.move(x, y)
        
        # Show dialog
        dialog.exec_()
    
    def _on_hangup(self):
        """Handle hangup button click"""
        logger.info(f"[LineWidget] Hangup button clicked for line {self.line.line_id}")
        
        # Create custom message box with better styling
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('Confirm Hangup')
        msg_box.setText(f'Are you sure you want to hang up Line {self.line.line_id}?')
        
        # Add buttons
        yes_btn = msg_box.addButton('Yes', QMessageBox.YesRole)
        cancel_btn = msg_box.addButton('Cancel', QMessageBox.RejectRole)
        msg_box.setDefaultButton(cancel_btn)
        
        # Style the message box for better visibility
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2a2a2a;
                color: white;
                font-size: 18px;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                min-width: 400px;
                min-height: 80px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: 2px solid #666;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
                min-width: 120px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #888;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)
        
        # Center dialog on this line widget
        msg_box.adjustSize()
        widget_rect = self.rect()
        widget_center = self.mapToGlobal(widget_rect.center())
        dialog_size = msg_box.size()
        dialog_x = widget_center.x() - dialog_size.width() // 2
        dialog_y = widget_center.y() - dialog_size.height() // 2
        msg_box.move(dialog_x, dialog_y)
        
        # Show dialog and check response
        msg_box.exec_()
        
        if msg_box.clickedButton() == yes_btn:
            logger.info(f"[LineWidget] User confirmed hangup for line {self.line.line_id}")
            self.hangup_clicked.emit(self.line.line_id)
        else:
            logger.info(f"[LineWidget] User cancelled hangup for line {self.line.line_id}")
    
    def _on_channel_changed(self, index):
        """Handle channel selection change"""
        if index >= 0:
            channel = self.channel_picker.itemData(index)
            if channel != self.line.audio_output.channel:
                self.audio_channel_changed.emit(self.line.line_id, channel)
    
    def set_selected(self, selected: bool):
        """Set selection highlight"""
        self.is_selected = selected
        self._last_selected = None  # Force style update
        self._update_style()
    
    def update_display(self):
        """Update display based on line state - with caching to reduce CPU"""
        current_state = self.line.state
        current_channel = self.line.audio_output.channel
        
        # Check if anything actually changed
        state_changed = (current_state != self._last_state)
        channel_changed = (current_channel != self._last_channel)
        selected_changed = (self.is_selected != self._last_selected)
        
        if not (state_changed or channel_changed or selected_changed):
            # Nothing changed - skip all updates for better performance on large screens
            return
        
        # Status text (only if state changed)
        if state_changed:
            self.status_label.setText(self.line.get_status_string())
            # Update action button based on line state
            is_active = self.line.is_active()
            if is_active:
                # Show HANGUP button (red/orange)
                self.action_btn.setText("📞 HANG UP")
                self.action_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                    stop:0 #ff6b6b, stop:1 #ee5a52);
                        color: white;
                        border: 2px solid #c92a2a;
                        border-radius: 8px;
                        padding: 12px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                    stop:0 #fa5252, stop:1 #e03131);
                    }
                    QPushButton:pressed {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                    stop:0 #c92a2a, stop:1 #a61e1e);
                    }
                """)
            else:
                # Show DIAL button (green)
                self.action_btn.setText("📞 DIAL")
                self.action_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                    stop:0 #2ed573, stop:1 #26de81);
                        color: white;
                        border: 2px solid #20bf6b;
                        border-radius: 8px;
                        padding: 12px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                    stop:0 #26de81, stop:1 #20bf6b);
                    }
                    QPushButton:pressed {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                    stop:0 #20bf6b, stop:1 #0abf53);
                    }
                """)
            logger.debug(f"Line {self.line.line_id} update: state={current_state}, is_active={is_active}")
        
        # Audio routing (only if channel changed)
        if channel_changed:
            if current_channel == 0:
                self.audio_label.setText("No Output")
            else:
                self.audio_label.setText(f"Out {current_channel}")
            
            # Update channel picker only when channel actually changed
            # This is more efficient than syncing on every update
            self.channel_picker.blockSignals(True)
            for i in range(self.channel_picker.count()):
                if self.channel_picker.itemData(i) == current_channel:
                    self.channel_picker.setCurrentIndex(i)
                    break
            self.channel_picker.blockSignals(False)
        
        # Update colors (only if state, channel, or selection changed)
        # Check if style actually needs updating to avoid expensive operations on large screens
        style_key = (self.line.state, self.line.audio_output.channel, self.is_selected)
        if style_key != self._last_style_state:
            self._update_style()
            self._last_style_state = style_key
        
        # Update cache
        self._last_state = current_state
        self._last_channel = current_channel
        self._last_selected = self.is_selected
    
    def _update_style(self):
        """Update widget styling based on state with modern colors"""
        # State-based gradient colors
        if self.is_selected:
            gradient = """
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 212, 255, 0.3),
                    stop:1 rgba(0, 212, 255, 0.15)
                );
                border: 3px solid #00d4ff;
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
            """
        elif self.line.state == LineState.IDLE:
            gradient = """
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:1 rgba(255, 255, 255, 0.04)
                );
                border: 2px solid rgba(255, 255, 255, 0.15);
            """
        elif self.line.state == LineState.CONNECTED:
            gradient = """
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(46, 213, 115, 0.3),
                    stop:1 rgba(46, 213, 115, 0.15)
                );
                border: 2px solid #2ed573;
                box-shadow: 0 0 15px rgba(46, 213, 115, 0.3);
            """
        elif self.line.state in [LineState.DIALING, LineState.RINGING]:
            gradient = """
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 159, 26, 0.3),
                    stop:1 rgba(255, 159, 26, 0.15)
                );
                border: 2px solid #ff9f1a;
                box-shadow: 0 0 15px rgba(255, 159, 26, 0.3);
            """
        else:  # ERROR or DISCONNECTED
            gradient = """
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 107, 107, 0.3),
                    stop:1 rgba(255, 107, 107, 0.15)
                );
                border: 2px solid #ff6b6b;
            """
        
        self.frame.setStyleSheet(f"""
            QFrame {{
                {gradient}
                border-radius: 10px;
            }}
            QFrame:hover {{
                border: 2px solid rgba(0, 212, 255, 0.6);
            }}
        """)
        
        # Audio label color - vibrant colors for different outputs
        if self.line.audio_output.channel == 0:
            self.audio_label.setStyleSheet("""
                QLabel {
                    color: #999;
                    background: rgba(136, 136, 136, 0.15);
                    padding: 5px 10px;
                    border-radius: 5px;
                    min-width: 85px;
                    max-width: 100px;
                }
            """)
        else:
            colors = [
                '#00d4ff',  # Cyan
                '#ff9f1a',  # Orange  
                '#2ed573',  # Green
                '#ff6b6b',  # Red
                '#ffd93d',  # Yellow
                '#a29bfe',  # Purple
                '#fd79a8',  # Pink
                '#6c5ce7'   # Violet
            ]
            color = colors[(self.line.audio_output.channel - 1) % len(colors)]
            self.audio_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.25);
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 85px;
                    max-width: 100px;
                }}
            """)
