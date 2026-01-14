#!/usr/bin/env python3
"""
Line Widget - Individual Phone Line Status Display
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import logging

from ..phone_line import PhoneLine, LineState, AudioOutput

logger = logging.getLogger(__name__)


class LineWidget(QWidget):
    """
    Widget displaying status of a single phone line
    """
    
    # Signals
    hangup_clicked = pyqtSignal(int)  # line_id
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
        
        self._create_ui()
        self.update_display()
        
        logger.debug(f"Line widget created for line {line.line_id}")
    
    def _create_ui(self):
        """Create line widget UI"""
        self.setMinimumHeight(170)
        self.setMaximumHeight(200)
        
        # Main frame with modern styling
        self.frame = QFrame(self)
        self.frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:1 rgba(255, 255, 255, 0.04)
                );
                border: 2px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
            }
            QFrame:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 212, 255, 0.2),
                    stop:1 rgba(0, 212, 255, 0.1)
                );
                border: 2px solid rgba(0, 212, 255, 0.4);
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
                color: #00d4ff;
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
                color: #4ecdc4;
                background: rgba(78, 205, 196, 0.2);
                padding: 5px 10px;
                border-radius: 5px;
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
        self.channel_picker.setMaximumWidth(125)
        self.channel_picker.setMinimumWidth(125)
        self.channel_picker.setMinimumHeight(40)
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
        self.hangup_btn = QPushButton("📞 HANG UP")
        self.hangup_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.hangup_btn.setMinimumHeight(40)
        self.hangup_btn.setMaximumHeight(40)
        self.hangup_btn.setMinimumWidth(110)
        self.hangup_btn.setMaximumWidth(130)
        self.hangup_btn.setEnabled(False)  # Start disabled
        self.hangup_btn.clicked.connect(self._on_hangup)
        self.hangup_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff9f1a,
                    stop:1 #ff6b35
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
                    stop:0 #ffb84d,
                    stop:1 #ff8555
                );
                border: 3px solid #00d4ff;
            }
            QPushButton:pressed {
                background: #cc6600;
                padding: 9px 14px 7px 16px;
            }
            QPushButton:disabled {
                background: #4a4a4a;
                color: #888888;
                border: 2px solid #666666;
            }
        """)
        button_row.addWidget(self.hangup_btn)
        
        frame_layout.addLayout(button_row)
    
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
        
        # Position the dialog below this line widget
        widget_pos = self.mapToGlobal(self.rect().bottomLeft())
        msg_box.move(widget_pos.x(), widget_pos.y() + 10)
        
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
            return  # Nothing changed, skip expensive updates
        
        # Status text (only if state changed)
        if state_changed:
            self.status_label.setText(self.line.get_status_string())
            # Enable/disable hangup button based on line state
            is_active = self.line.is_active()
            self.hangup_btn.setEnabled(is_active)
            logger.debug(f"Line {self.line.line_id} update: state={current_state}, is_active={is_active}")
        
        # Audio routing (only if channel changed)
        if channel_changed:
            if current_channel == 0:
                self.audio_label.setText("No Output")
            else:
                self.audio_label.setText(f"Out {current_channel}")
            
            # Update channel picker
            self.channel_picker.blockSignals(True)
            for i in range(self.channel_picker.count()):
                if self.channel_picker.itemData(i) == current_channel:
                    self.channel_picker.setCurrentIndex(i)
                    break
            self.channel_picker.blockSignals(False)
        
        # Update colors (only if state, channel, or selection changed)
        self._update_style()
        
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
