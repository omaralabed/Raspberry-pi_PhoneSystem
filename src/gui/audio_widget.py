#!/usr/bin/env python3
"""
Audio Widget - Audio Routing Controls
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QGroupBox, QGridLayout, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class AudioWidget(QWidget):
    """
    Audio routing controls and status display with flexible output selection
    """
    
    def __init__(self, audio_router, parent=None):
        """
        Initialize audio widget
        
        Args:
            audio_router: AudioRouter instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.audio_router = audio_router
        self.available_label = None  # Label showing available lines
        self.output_labels = []  # Store label references for updates
        self._create_ui()
        
        logger.info("Audio widget initialized")
    
    def _create_ui(self):
        """Create audio controls UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Group box
        group = QGroupBox("Audio Routing")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        group.setStyleSheet("QGroupBox { color: white; }")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(5)
        
        # Info label
        info_label = QLabel("Click 🔊 on any line\nto cycle output channels")
        info_label.setFont(QFont("Arial", 9))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: white;")
        group_layout.addWidget(info_label)
        
        # Output channels display
        channels_frame = QFrame()
        channels_frame.setFrameStyle(QFrame.Box)
        channels_frame.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555;")
        channels_layout = QVBoxLayout(channels_frame)
        channels_layout.setContentsMargins(8, 8, 8, 8)
        channels_layout.setSpacing(3)
        
        channels_title = QLabel("Available Lines")
        channels_title.setFont(QFont("Arial", 10, QFont.Bold))
        channels_title.setAlignment(Qt.AlignCenter)
        channels_title.setStyleSheet("color: white;")
        channels_layout.addWidget(channels_title)
        
        # Show available lines (not assigned to any output)
        self.available_label = QLabel("Lines: (checking...)")
        self.available_label.setFont(QFont("Arial", 9))
        self.available_label.setAlignment(Qt.AlignLeft)
        self.available_label.setStyleSheet("color: #4ecdc4; padding: 3px;")
        self.available_label.setWordWrap(True)
        channels_layout.addWidget(self.available_label)
        
        # Show outputs 1-8 with assigned lines
        self.output_labels = []
        for i in range(1, 9):
            output_label = QLabel(f"Output {i} - (none)")
            output_label.setFont(QFont("Arial", 8))
            colors = ['#4af', '#fa4', '#4f4', '#f4f', '#ff4', '#4ff', '#f44', '#44f']
            output_label.setStyleSheet(f"color: {colors[i-1]};")
            channels_layout.addWidget(output_label)
            self.output_labels.append(output_label)
        
        group_layout.addWidget(channels_frame)
        
        # Test section
        test_frame = QFrame()
        test_frame.setFrameStyle(QFrame.Box)
        test_frame.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555;")
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(5, 5, 5, 5)
        
        test_title = QLabel("Test Audio Output")
        test_title.setFont(QFont("Arial", 9, QFont.Bold))
        test_title.setAlignment(Qt.AlignCenter)
        test_title.setStyleSheet("color: white;")
        test_layout.addWidget(test_title)
        
        # Channel selector
        selector_layout = QHBoxLayout()
        selector_label = QLabel("Channel:")
        selector_label.setFont(QFont("Arial", 9))
        selector_label.setStyleSheet("color: white;")
        selector_layout.addWidget(selector_label)
        
        self.channel_spinbox = QSpinBox()
        self.channel_spinbox.setRange(1, 8)
        self.channel_spinbox.setValue(1)
        self.channel_spinbox.setFont(QFont("Arial", 10))
        selector_layout.addWidget(self.channel_spinbox)
        
        test_layout.addLayout(selector_layout)
        
        # Test button
        self.test_btn = QPushButton("🔊 Test Selected Output")
        self.test_btn.setFont(QFont("Arial", 9))
        self.test_btn.clicked.connect(self._on_test_output)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a5a6a;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:pressed {
                background-color: #1a4a5a;
            }
        """)
        test_layout.addWidget(self.test_btn)
        
        group_layout.addWidget(test_frame)
        
        layout.addWidget(group)
    
    def _on_test_output(self):
        """Test selected output channel"""
        channel = self.channel_spinbox.value()
        logger.info(f"Testing output channel {channel}")
        self.audio_router.test_audio(channel, duration=1.0)
    
    def update_routing_display(self, lines):
        """
        Update the routing display with current line assignments
        
        Args:
            lines: List of PhoneLine objects (lines 1-8)
        """
        # Build mapping of output -> line
        output_to_line = {}
        available_lines = []
        
        for line in lines:
            channel = line.audio_output.channel
            if channel == 0:
                # Line not assigned to any output
                available_lines.append(line.line_id)
            else:
                # Line assigned to this output
                output_to_line[channel] = line.line_id
        
        # Update available lines label
        if available_lines:
            lines_str = ", ".join([f"Line {lid}" for lid in available_lines])
            self.available_label.setText(f"Lines: [{lines_str}]")
        else:
            self.available_label.setText("Lines: (all assigned)")
        
        # Update output labels
        colors = ['#4af', '#fa4', '#4f4', '#f4f', '#ff4', '#4ff', '#f44', '#44f']
        for i in range(1, 9):
            if i in output_to_line:
                line_id = output_to_line[i]
                self.output_labels[i-1].setText(f"Output {i} - Line {line_id}")
            else:
                self.output_labels[i-1].setText(f"Output {i} - (none)")
            self.output_labels[i-1].setStyleSheet(f"color: {colors[i-1]};")
