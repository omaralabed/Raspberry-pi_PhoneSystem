#!/usr/bin/env python3
"""
Audio Widget - Audio Routing Controls
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QGroupBox, QGridLayout, QSpinBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QMouseEvent
import logging

logger = logging.getLogger(__name__)


class ToneWorker(QThread):
    """Worker thread for audio operations to prevent GUI blocking"""
    finished = pyqtSignal(bool)
    
    def __init__(self, audio_router, action, channel=None):
        super().__init__()
        self.audio_router = audio_router
        self.action = action  # 'start' or 'stop'
        self.channel = channel
    
    def run(self):
        try:
            if not self.audio_router:
                logger.warning("Cannot run tone worker: audio router not available")
                self.finished.emit(False)
                return
            
            if self.action == 'start' and self.channel is not None:
                result = self.audio_router.start_continuous_tone(self.channel)
            elif self.action == 'stop':
                result = self.audio_router.stop_continuous_tone()
            else:
                result = False
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Error in tone worker: {e}", exc_info=True)
            self.finished.emit(False)


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
        self._last_routing = {}  # Cache for routing state
        self._tone_worker = None  # Current tone worker thread
        self._button_pressed = False  # Track button state to prevent rapid toggling
        self._create_ui()
        
        logger.info(f"Audio widget initialized with audio_router={audio_router is not None}")
    
    def eventFilter(self, obj, event):
        """Event filter to catch button events"""
        if obj == self.test_btn:
            if event.type() == QEvent.MouseButtonPress:
                logger.info("EventFilter: MouseButtonPress detected")
                self._on_test_pressed()
            elif event.type() == QEvent.MouseButtonRelease:
                logger.info("EventFilter: MouseButtonRelease detected")
                self._on_test_released()
        return super().eventFilter(obj, event)
    
    def _create_ui(self):
        """Create audio controls UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        
        # Group box
        group = QGroupBox("Audio Routing")
        group.setFont(QFont("Arial", 10, QFont.Bold))
        group.setStyleSheet("QGroupBox { color: white; }")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(3)
        
        # Info label - more compact
        info_label = QLabel("Click 🔊 on line to cycle outputs")
        info_label.setFont(QFont("Arial", 8))
        info_label.setAlignment(Qt.AlignCenter)
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
                border-radius: 6px;
            }
        """)
        channels_layout = QVBoxLayout(channels_frame)
        channels_layout.setContentsMargins(6, 5, 6, 5)
        channels_layout.setSpacing(4)
        
        # Title
        channels_title = QLabel("📊 Outputs")
        channels_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        channels_title.setAlignment(Qt.AlignCenter)
        channels_title.setStyleSheet("color: #00d4ff; padding: 2px;")
        channels_layout.addWidget(channels_title)
        
        # Show available lines in a nice box
        self.available_label = QLabel("Unassigned: checking...")
        self.available_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.available_label.setAlignment(Qt.AlignCenter)
        self.available_label.setStyleSheet("""
            QLabel {
                color: #2ed573;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(46, 213, 115, 0.2),
                    stop:1 rgba(46, 213, 115, 0.1)
                );
                border: 1px solid rgba(46, 213, 115, 0.4);
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.available_label.setWordWrap(True)
        channels_layout.addWidget(self.available_label)
        
        # Outputs title - removed to save space, grid is self-explanatory
        
        # Grid layout for outputs (2 columns)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(3)
        
        # Show outputs 1-8 in a 2-column grid - more compact
        self.output_labels = []
        colors = ['#4af', '#fa4', '#4f4', '#f4f', '#ff4', '#4ff', '#f44', '#44f']
        for i in range(1, 9):
            output_label = QLabel(f"{i}→-")
            output_label.setFont(QFont("Segoe UI", 8))
            output_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors[i-1]};
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 3px;
                    padding: 2px 4px;
                }}
            """)
            row = (i - 1) // 2
            col = (i - 1) % 2
            grid_layout.addWidget(output_label, row, col)
            self.output_labels.append(output_label)
        
        channels_layout.addLayout(grid_layout)
        
        group_layout.addWidget(channels_frame)
        
        # Test section - more compact
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
                border-radius: 6px;
            }
        """)
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(8, 6, 8, 6)
        test_layout.setSpacing(5)
        
        test_title = QLabel("🎵 Test Output")
        test_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        test_title.setAlignment(Qt.AlignCenter)
        test_title.setStyleSheet("color: #00d4ff; padding: 2px;")
        test_layout.addWidget(test_title)
        
        # Channel selector with modern styling - more compact
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(5)
        
        selector_label = QLabel("Ch:")
        selector_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        selector_label.setStyleSheet("color: white;")
        selector_layout.addWidget(selector_label)
        
        self.channel_spinbox = QSpinBox()
        self.channel_spinbox.setRange(1, 8)
        self.channel_spinbox.setValue(1)
        self.channel_spinbox.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.channel_spinbox.setMinimumHeight(30)
        self.channel_spinbox.setStyleSheet("""
            QSpinBox {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 4px;
                padding: 3px 6px;
                color: #00d4ff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: rgba(0, 212, 255, 0.2);
                border: none;
                width: 18px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: rgba(0, 212, 255, 0.4);
            }
        """)
        selector_layout.addWidget(self.channel_spinbox)
        selector_layout.addStretch()
        
        test_layout.addLayout(selector_layout)
        
        # Test button - Simple toggle for touchscreen reliability
        self.test_btn = QPushButton("🔊 Start Test")
        self.test_btn.setCheckable(True)  # Make it a toggle button
        self.test_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.test_btn.setMinimumHeight(36)
        self._tone_playing = False
        
        # Simple clicked connection - works best with touchscreens
        def on_click_debug():
            print("BUTTON CLICKED!!!", flush=True)
            logger.error("BUTTON CLICKED - CALLING TOGGLE")
            self._on_test_toggle()
        
        self.test_btn.clicked.connect(on_click_debug)
        
        logger.info("Test button created as toggle button for touchscreen")
        
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff,
                    stop:1 #0088cc
                );
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                min-height: 36px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e4ff,
                    stop:1 #0099dd
                );
            }
            QPushButton:checked {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2ed573,
                    stop:1 #26de81
                );
            }
        """)
        test_layout.addWidget(self.test_btn)
        
        group_layout.addWidget(test_frame)
        
        layout.addWidget(group)
    
    def _on_test_output(self):
        """Test selected output channel (legacy - one shot)"""
        if not self.audio_router:
            logger.warning("Cannot test audio: audio router not available")
            return
        
        channel = self.channel_spinbox.value()
        logger.info(f"Testing output channel {channel}")
        self.audio_router.test_audio(channel, duration=1.0)
    
    def _on_test_pressed(self):
        """Start continuous tone when button is pressed (non-blocking)"""
        import sys
        import subprocess
        
        # Prevent rapid toggling
        if self._button_pressed:
            logger.warning("TEST BUTTON - Already pressed, ignoring")
            return
        
        self._button_pressed = True
        
        print("TEST BUTTON PRESSED", file=sys.stderr, flush=True)
        logger.info("TEST BUTTON PRESSED - Entry point")
        logger.error("TEST BUTTON PRESSED - USING ERROR LEVEL TO ENSURE VISIBILITY")
        
        try:
            if not self.audio_router:
                logger.warning("Cannot test audio: audio router not available")
                self._button_pressed = False
                return
            
            # Kill ALL existing tone processes first (safety)
            try:
                subprocess.run(['pkill', '-9', '-f', 'tone_generator'], 
                              timeout=0.5, capture_output=True)
                logger.info("TEST BUTTON - Killed all existing tone processes")
            except:
                pass
            
            # Get channel from spinbox
            channel = self.channel_spinbox.value()
            logger.info(f"TEST BUTTON - Starting tone on channel {channel} (from spinbox)")
            logger.error(f"TEST BUTTON - Channel value: {channel}")  # Use error level for visibility
            print(f"TEST BUTTON - Channel {channel}", file=sys.stderr, flush=True)
            
            # Stop any existing tone first (non-blocking)
            logger.info("TEST BUTTON - Stopping any existing tone first")
            self.audio_router.stop_continuous_tone()
            
            # Start tone directly (no delay needed - stop already handled cleanup)
            logger.info(f"TEST BUTTON - Starting tone on channel {channel}")
            try:
                self.audio_router.start_continuous_tone(channel)
                logger.info("TEST BUTTON - Tone started successfully")
            except Exception as e:
                logger.error(f"TEST BUTTON - Error starting tone: {e}", exc_info=True)
                self._button_pressed = False
        except Exception as e:
            logger.error(f"Error in test button: {e}", exc_info=True)
            print(f"ERROR: {e}", file=sys.stderr, flush=True)
            self._button_pressed = False
    
    def _on_test_toggle(self):
        """Toggle test tone on/off - simple and reliable for touchscreens"""
        if not self.audio_router:
            logger.warning("Cannot test audio: audio router not available")
            self.test_btn.setChecked(False)
            return
        
        print(f"TOGGLE CALLED - checked={self.test_btn.isChecked()}", flush=True)
        logger.error(f"TOGGLE FUNCTION ENTRY - checked={self.test_btn.isChecked()}")
        
        if self.test_btn.isChecked():
            # Start tone
            channel = self.channel_spinbox.value()
            logger.error(f"STARTING TONE on channel {channel}")
            print(f"STARTING TONE on channel {channel}", flush=True)
            self.test_btn.setText("🔇 Stop")
            try:
                self.audio_router.start_continuous_tone(channel)
                logger.error("Tone started successfully")
            except Exception as e:
                logger.error(f"Error starting tone: {e}", exc_info=True)
                print(f"ERROR: {e}", flush=True)
                self.test_btn.setChecked(False)
                self.test_btn.setText("🔊 Start Test")
        else:
            # Stop tone
            logger.error("STOPPING TONE")
            print("STOPPING TONE", flush=True)
            self.test_btn.setText("🔊 Start Test")
            try:
                self.audio_router.stop_continuous_tone()
                logger.error("Tone stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping tone: {e}", exc_info=True)
                print(f"ERROR stopping: {e}", flush=True)
    
    def update_routing_display(self, lines):
        """
        Update the routing display with current line assignments - with caching
        
        Args:
            lines: List of PhoneLine objects (lines 1-8)
        """
        # Build mapping of output -> line
        output_to_line = {}
        available_lines = []
        
        for line in lines:
            channel = line.audio_output.channel
            if channel == 0:
                available_lines.append(line.line_id)
            else:
                output_to_line[channel] = line.line_id
        
        # Check if routing changed
        current_routing = (tuple(sorted(output_to_line.items())), tuple(available_lines))
        if current_routing == self._last_routing:
            return  # Nothing changed, skip expensive updates
        self._last_routing = current_routing
        
        # Update available lines label
        if available_lines:
            lines_str = ", ".join([f"L{lid}" for lid in available_lines])
            self.available_label.setText(f"⚪ Unassigned Lines: {lines_str}")
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
