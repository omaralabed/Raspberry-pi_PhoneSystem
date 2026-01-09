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
    clicked = pyqtSignal(int)  # line_id
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
        
        self._create_ui()
        self.update_display()
        
        logger.debug(f"Line widget created for line {line.line_id}")
    
    def _create_ui(self):
        """Create line widget UI"""
        self.setMinimumHeight(130)
        self.setMaximumHeight(160)
        
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
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(12)
        
        # Top row: Line number and audio label
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        self.line_label = QLabel(f"Line {self.line.line_id}")
        self.line_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.line_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                padding: 2px 5px;
            }
        """)
        top_row.addWidget(self.line_label)
        
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
        
        # Button row
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        
        # Audio channel picker with modern styling
        self.channel_picker = QComboBox()
        self.channel_picker.setMaximumWidth(125)
        self.channel_picker.setMinimumWidth(125)
        self.channel_picker.setMinimumHeight(45)
        self.channel_picker.addItem("🔇 None", 0)  # No output with icon
        for i in range(1, 9):
            self.channel_picker.addItem(f"🔊 {i}", i)
        self.channel_picker.setCurrentIndex(1)  # Default to channel 1
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
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid white;
                margin-right: 5px;
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
        
        button_row.addStretch()
        
        # Hangup button with modern gradient - bigger and more prominent
        self.hangup_btn = QPushButton("📞 HANG UP")
        self.hangup_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.hangup_btn.setMinimumHeight(50)
        self.hangup_btn.setMinimumWidth(130)
        self.hangup_btn.setVisible(True)  # Always visible for testing
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
                padding: 10px 20px;
                font-weight: bold;
                letter-spacing: 2px;
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
                padding: 11px 19px 9px 21px;
            }
        """)
        button_row.addWidget(self.hangup_btn)
        
        frame_layout.addLayout(button_row)
        
        # Make frame clickable
        self.frame.mousePressEvent = self._on_click
    
    def _on_click(self, event):
        """Handle click on line widget"""
        self.clicked.emit(self.line.line_id)
    
    def _on_hangup(self):
        """Handle hangup button click"""
        self.hangup_clicked.emit(self.line.line_id)
    
    def _on_channel_changed(self, index):
        """Handle channel selection change"""
        if index >= 0:
            channel = self.channel_picker.itemData(index)
            if channel != self.line.audio_output.channel:
                self.audio_channel_changed.emit(self.line.line_id, channel)
    
    def set_selected(self, selected: bool):
        """Set selection highlight"""
        self.is_selected = selected
        self._update_style()
    
    def update_display(self):
        """Update display based on line state"""
        # Status text
        self.status_label.setText(self.line.get_status_string())
        
        # Audio routing - show output channel number or "No Output"
        if self.line.audio_output.channel == 0:
            self.audio_label.setText("No Output")
        else:
            self.audio_label.setText(f"Out {self.line.audio_output.channel}")
        
        # Update channel picker to match current channel
        current_channel = self.line.audio_output.channel
        self.channel_picker.blockSignals(True)
        # Find the index for the channel value (0="None" is at index 0, channel 1 is at index 1, etc.)
        for i in range(self.channel_picker.count()):
            if self.channel_picker.itemData(i) == current_channel:
                self.channel_picker.setCurrentIndex(i)
                break
        self.channel_picker.blockSignals(False)
        
        # Show/hide hangup button
        self.hangup_btn.setVisible(self.line.is_active())
        
        # Update colors
        self._update_style()
    
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
