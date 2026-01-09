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
        channels_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(42, 42, 42, 0.95),
                    stop:1 rgba(26, 26, 26, 0.95)
                );
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
            }
        """)
        channels_layout = QVBoxLayout(channels_frame)
        channels_layout.setContentsMargins(12, 10, 12, 10)
        channels_layout.setSpacing(8)
        
        # Title
        channels_title = QLabel("📊 Available Outputs")
        channels_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        channels_title.setAlignment(Qt.AlignCenter)
        channels_title.setStyleSheet("color: #00d4ff; padding: 5px;")
        channels_layout.addWidget(channels_title)
        
        # Show available lines in a nice box
        self.available_label = QLabel("Unassigned: (checking...)")
        self.available_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.available_label.setAlignment(Qt.AlignCenter)
        self.available_label.setStyleSheet("""
            QLabel {
                color: #2ed573;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(46, 213, 115, 0.2),
                    stop:1 rgba(46, 213, 115, 0.1)
                );
                border: 2px solid rgba(46, 213, 115, 0.4);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.available_label.setWordWrap(True)
        channels_layout.addWidget(self.available_label)
        
        # Outputs title
        outputs_title = QLabel("🔊 Output Assignments")
        outputs_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        outputs_title.setAlignment(Qt.AlignCenter)
        outputs_title.setStyleSheet("color: #00d4ff; padding: 5px 0px;")
        channels_layout.addWidget(outputs_title)
        
        # Grid layout for outputs (2 columns)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(6)
        
        # Show outputs 1-8 in a 2-column grid
        self.output_labels = []
        colors = ['#4af', '#fa4', '#4f4', '#f4f', '#ff4', '#4ff', '#f44', '#44f']
        for i in range(1, 9):
            output_label = QLabel(f"Out {i} → (none)")
            output_label.setFont(QFont("Segoe UI", 9))
            output_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors[i-1]};
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    padding: 5px 8px;
                }}
            """)
            row = (i - 1) // 2
            col = (i - 1) % 2
            grid_layout.addWidget(output_label, row, col)
            self.output_labels.append(output_label)
        
        channels_layout.addLayout(grid_layout)
        
        group_layout.addWidget(channels_frame)
        
        # Test section
        test_frame = QFrame()
        test_frame.setFrameStyle(QFrame.Box)
        test_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(42, 42, 42, 0.95),
                    stop:1 rgba(26, 26, 26, 0.95)
                );
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
            }
        """)
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(12, 10, 12, 10)
        test_layout.setSpacing(10)
        
        test_title = QLabel("🎵 Test Audio Output")
        test_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        test_title.setAlignment(Qt.AlignCenter)
        test_title.setStyleSheet("color: #00d4ff; padding: 5px;")
        test_layout.addWidget(test_title)
        
        # Channel selector with modern styling
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(10)
        
        selector_label = QLabel("Channel:")
        selector_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        selector_label.setStyleSheet("color: white;")
        selector_layout.addWidget(selector_label)
        
        self.channel_spinbox = QSpinBox()
        self.channel_spinbox.setRange(1, 8)
        self.channel_spinbox.setValue(1)
        self.channel_spinbox.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.channel_spinbox.setMinimumHeight(35)
        self.channel_spinbox.setStyleSheet("""
            QSpinBox {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 5px 10px;
                color: #00d4ff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: rgba(0, 212, 255, 0.2);
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: rgba(0, 212, 255, 0.4);
            }
            QSpinBox::up-arrow {
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow {
                width: 10px;
                height: 10px;
            }
        """)
        selector_layout.addWidget(self.channel_spinbox)
        selector_layout.addStretch()
        
        test_layout.addLayout(selector_layout)
        
        # Test button with modern gradient
        self.test_btn = QPushButton("🔊 Hold to Test")
        self.test_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.test_btn.setMinimumHeight(45)
        # Use press/release events instead of clicked
        self.test_btn.pressed.connect(self._on_test_pressed)
        self.test_btn.released.connect(self._on_test_released)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff,
                    stop:1 #0088cc
                );
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e4ff,
                    stop:1 #0099dd
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2ed573,
                    stop:1 #26de81
                );
                padding: 11px 9px 9px 11px;
            }
        """)
        test_layout.addWidget(self.test_btn)
        
        group_layout.addWidget(test_frame)
        
        layout.addWidget(group)
    
    def _on_test_output(self):
        """Test selected output channel (legacy - one shot)"""
        channel = self.channel_spinbox.value()
        logger.info(f"Testing output channel {channel}")
        self.audio_router.test_audio(channel, duration=1.0)
    
    def _on_test_pressed(self):
        """Start continuous tone when button is pressed"""
        channel = self.channel_spinbox.value()
        logger.info(f"Starting continuous tone on channel {channel}")
        self.audio_router.start_continuous_tone(channel)
    
    def _on_test_released(self):
        """Stop continuous tone when button is released"""
        logger.info("Stopping continuous tone")
        self.audio_router.stop_continuous_tone()
    
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
            lines_str = ", ".join([f"L{lid}" for lid in available_lines])
            self.available_label.setText(f"⚪ Unassigned: {lines_str}")
        else:
            self.available_label.setText("✅ All lines assigned to outputs")
        
        # Update output labels
        colors = ['#4af', '#fa4', '#4f4', '#f4f', '#ff4', '#4ff', '#f44', '#44f']
        for i in range(1, 9):
            if i in output_to_line:
                line_id = output_to_line[i]
                self.output_labels[i-1].setText(f"Out {i} → L{line_id}")
                self.output_labels[i-1].setStyleSheet(f"""
                    QLabel {{
                        color: {colors[i-1]};
                        background: qlineargradient(
                            x1:0, y1:0, x2:1, y2:0,
                            stop:0 rgba(46, 213, 115, 0.3),
                            stop:1 rgba(46, 213, 115, 0.1)
                        );
                        border: 1px solid rgba(46, 213, 115, 0.5);
                        border-radius: 4px;
                        padding: 5px 8px;
                        font-weight: bold;
                    }}
                """)
            else:
                self.output_labels[i-1].setText(f"Out {i} → (none)")
                self.output_labels[i-1].setStyleSheet(f"""
                    QLabel {{
                        color: {colors[i-1]};
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 4px;
                        padding: 5px 8px;
                    }}
                """)
