#!/usr/bin/env python3
"""
Line Widget - Individual Phone Line Status Display
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame)
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
    audio_toggle_clicked = pyqtSignal(int)  # line_id
    
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
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        
        # Main frame
        self.frame = QFrame(self)
        self.frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.frame.setLineWidth(2)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.frame)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(3)
        
        # Top row: Line number and status
        top_row = QHBoxLayout()
        
        self.line_label = QLabel(f"Line {self.line.line_id}")
        self.line_label.setFont(QFont("Arial", 12, QFont.Bold))
        top_row.addWidget(self.line_label)
        
        top_row.addStretch()
        
        self.audio_label = QLabel("IFB")
        self.audio_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.audio_label.setAlignment(Qt.AlignRight)
        top_row.addWidget(self.audio_label)
        
        frame_layout.addLayout(top_row)
        
        # Status label
        self.status_label = QLabel("Available")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setAlignment(Qt.AlignLeft)
        frame_layout.addWidget(self.status_label)
        
        # Button row
        button_row = QHBoxLayout()
        button_row.setSpacing(5)
        
        # Audio toggle button
        self.audio_btn = QPushButton("🔊")
        self.audio_btn.setMaximumWidth(40)
        self.audio_btn.setToolTip("Toggle IFB/PL")
        self.audio_btn.clicked.connect(self._on_audio_toggle)
        self.audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                border: 1px solid #666;
                border-radius: 3px;
            }
            QPushButton:pressed {
                background-color: #2a5a8a;
            }
        """)
        button_row.addWidget(self.audio_btn)
        
        button_row.addStretch()
        
        # Hangup button
        self.hangup_btn = QPushButton("Hang Up")
        self.hangup_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.hangup_btn.setVisible(False)
        self.hangup_btn.clicked.connect(self._on_hangup)
        self.hangup_btn.setStyleSheet("""
            QPushButton {
                background-color: #8a2a2a;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
            }
            QPushButton:pressed {
                background-color: #6a1a1a;
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
    
    def _on_audio_toggle(self):
        """Handle audio toggle button click"""
        self.audio_toggle_clicked.emit(self.line.line_id)
    
    def set_selected(self, selected: bool):
        """Set selection highlight"""
        self.is_selected = selected
        self._update_style()
    
    def update_display(self):
        """Update display based on line state"""
        # Status text
        self.status_label.setText(self.line.get_status_string())
        
        # Audio routing
        self.audio_label.setText(self.line.audio_output.value)
        
        # Show/hide hangup button
        self.hangup_btn.setVisible(self.line.is_active())
        
        # Update colors
        self._update_style()
    
    def _update_style(self):
        """Update widget styling based on state"""
        # Base style
        if self.is_selected:
            bg_color = "#2a5a8a"
            border_color = "#4a7aaa"
        elif self.line.state == LineState.IDLE:
            bg_color = "#3a3a3a"
            border_color = "#555555"
        elif self.line.state == LineState.CONNECTED:
            bg_color = "#2a6a2a"
            border_color = "#4a8a4a"
        elif self.line.state in [LineState.DIALING, LineState.RINGING]:
            bg_color = "#6a6a2a"
            border_color = "#8a8a4a"
        else:
            bg_color = "#6a2a2a"
            border_color = "#8a4a4a"
        
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 5px;
            }}
        """)
        
        # Audio label color
        if self.line.audio_output == AudioOutput.IFB:
            self.audio_label.setStyleSheet("color: #4af; font-weight: bold;")
        else:
            self.audio_label.setStyleSheet("color: #fa4; font-weight: bold;")
