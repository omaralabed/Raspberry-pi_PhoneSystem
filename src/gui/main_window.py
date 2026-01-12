#!/usr/bin/env python3
"""
Main Window - TouchScreen GUI
"""

import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import logging

from .dialer_widget import DialerWidget
from .line_widget import LineWidget
from .audio_widget import AudioWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main touchscreen interface for phone system
    """
    
    # Signals
    make_call_signal = pyqtSignal(int, str)  # line_id, phone_number
    hangup_signal = pyqtSignal(int)  # line_id
    route_audio_signal = pyqtSignal(int, int)  # line_id, output_channel
    
    def __init__(self, sip_engine, audio_router):
        """
        Initialize main window
        
        Args:
            sip_engine: SIPEngine instance
            audio_router: AudioRouter instance
        """
        super().__init__()
        
        self.sip_engine = sip_engine
        self.audio_router = audio_router
        
        # Selected line for dialing
        self.selected_line_id = None
        
        # UI Setup
        self.setWindowTitle("Phone System - IFB/PL")
        # Use available screen size instead of hardcoded resolution
        # self.setGeometry(0, 0, 800, 480)  # Old: 7" touchscreen resolution
        
        # Apply dark theme
        self._apply_theme()
        
        # Create UI
        self._create_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # Update every second
        
        logger.info("Main window initialized")
    
    def _apply_theme(self):
        """Apply modern gradient theme"""
        # Set main window background with gradient
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e,
                    stop:0.5 #16213e,
                    stop:1 #0f3460
                );
            }
            QLabel {
                color: #eaeaea;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                border-radius: 8px;
            }
        """)
    
    def _create_ui(self):
        """Create main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left panel: Line status widgets
        left_panel = self._create_line_panel()
        main_layout.addWidget(left_panel, stretch=2)
        
        # Right panel: Dialer and audio routing
        right_panel = self._create_control_panel()
        main_layout.addWidget(right_panel, stretch=1)
    
    def _create_line_panel(self) -> QWidget:
        """Create panel with 8 line status widgets"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(255, 255, 255, 0.02)
                );
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        layout = QGridLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Create 8 line widgets (2 columns x 4 rows)
        self.line_widgets = []
        for i in range(8):
            line = self.sip_engine.get_line(i + 1)
            widget = LineWidget(line, self)
            widget.clicked.connect(self._on_line_selected)
            widget.hangup_clicked.connect(self._on_hangup_clicked)
            widget.audio_channel_changed.connect(self._on_audio_channel_changed)
            
            row = i // 2
            col = i % 2
            layout.addWidget(widget, row, col)
            
            self.line_widgets.append(widget)
        
        return panel
    
    def _create_control_panel(self) -> QWidget:
        """Create dialer and audio control panel"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(255, 255, 255, 0.02)
                );
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Selected line display with modern styling
        self.selected_line_label = QLabel("Select a line to dial")
        self.selected_line_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.selected_line_label.setAlignment(Qt.AlignCenter)
        self.selected_line_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b,
                    stop:1 #ee5a6f
                );
                color: white;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.selected_line_label)
        
        # Dialer widget
        self.dialer = DialerWidget(self)
        self.dialer.call_requested.connect(self._on_call_requested)
        layout.addWidget(self.dialer, stretch=1)
        
        # Audio routing widget
        self.audio_widget = AudioWidget(self.audio_router, self)
        layout.addWidget(self.audio_widget)
        
        return panel
    
    def _on_line_selected(self, line_id: int):
        """Handle line selection"""
        if self.selected_line_id == line_id:
            # Deselect if clicking same line
            self.selected_line_id = None
            self.selected_line_label.setText("Select a line to dial")
            self.selected_line_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff6b6b,
                        stop:1 #ee5a6f
                    );
                    color: white;
                    padding: 15px;
                    border-radius: 10px;
                    font-weight: bold;
                }
            """)
        else:
            line = self.sip_engine.get_line(line_id)
            if line.is_available():
                self.selected_line_id = line_id
                self.selected_line_label.setText(f"Line {line_id} selected")
                self.selected_line_label.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(
                            x1:0, y1:0, x2:1, y2:0,
                            stop:0 #00d4ff,
                            stop:1 #00a8cc
                        );
                        color: white;
                        padding: 15px;
                        border-radius: 10px;
                        font-weight: bold;
                    }
                """)
            else:
                self.selected_line_label.setText(f"Line {line_id} busy")
        
        # Update line widget highlights
        for widget in self.line_widgets:
            widget.set_selected(widget.line.line_id == self.selected_line_id)
    
    def _on_call_requested(self, phone_number: str):
        """Handle call request from dialer"""
        if not self.selected_line_id:
            self.selected_line_label.setText("Please select a line first")
            return
        
        line = self.sip_engine.get_line(self.selected_line_id)
        if not line.is_available():
            self.selected_line_label.setText(f"Line {self.selected_line_id} not available")
            return
        
        # Make call
        logger.info(f"Making call on line {self.selected_line_id} to {phone_number}")
        self.make_call_signal.emit(self.selected_line_id, phone_number)
        
        # Clear selection
        self.selected_line_id = None
        self.selected_line_label.setText("Select a line to dial")
        self.selected_line_label.setStyleSheet("background-color: #3a3a3a; padding: 10px;")
        
        # Update UI
        self._update_display()
    
    def _on_hangup_clicked(self, line_id: int):
        """Handle hangup button click"""
        logger.info(f"Hanging up line {line_id}")
        self.hangup_signal.emit(line_id)
    
    def _on_audio_channel_changed(self, line_id: int, new_channel: int):
        """Handle audio channel selection change"""
        # If setting to None (0), no conflict check needed
        if new_channel == 0:
            line = self.sip_engine.get_line(line_id)
            line.set_audio_channel(new_channel)
            logger.info(f"Line {line_id}: Channel set to None")
            self.route_audio_signal.emit(line_id, new_channel)
            self._update_display()
            return
        
        # Check if another line is already using this channel
        conflicting_line = None
        for i in range(1, 9):
            if i != line_id:
                line = self.sip_engine.get_line(i)
                if line.audio_output.channel == new_channel:
                    conflicting_line = i
                    break
        
        if conflicting_line:
            # Show warning dialog
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Channel In Use")
            msg.setText(f"Output Channel {new_channel} is already in use by Line {conflicting_line}.")
            msg.setInformativeText(f"Line {conflicting_line} will be disconnected from this output.\n\nDo you want to proceed?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Cancel)
            
            # Style the message box to match dark theme
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2a2a2a;
                    color: #ddd;
                }
                QMessageBox QLabel {
                    color: #ddd;
                }
                QPushButton {
                    background-color: #505050;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 3px;
                    padding: 5px 15px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #606060;
                }
                QPushButton:pressed {
                    background-color: #404040;
                }
            """)
            
            result = msg.exec_()
            
            if result == QMessageBox.Yes:
                # User confirmed - disconnect conflicting line from output
                conflicting_line_obj = self.sip_engine.get_line(conflicting_line)
                conflicting_line_obj.set_audio_channel(0)  # Set to 0 (no output)
                logger.info(f"Line {conflicting_line}: Disconnected from Output {new_channel}")
                
                # Now assign the new line to this channel
                line = self.sip_engine.get_line(line_id)
                line.set_audio_channel(new_channel)
                logger.info(f"Line {line_id}: Channel changed to {new_channel}")
                self.route_audio_signal.emit(line_id, new_channel)
                self._update_display()
            else:
                # User cancelled - revert to previous channel
                logger.info(f"Line {line_id}: Channel change to {new_channel} cancelled")
                self._update_display()  # This will reset the picker to current channel
        else:
            # No conflict - proceed with channel change
            line = self.sip_engine.get_line(line_id)
            line.set_audio_channel(new_channel)
            logger.info(f"Line {line_id}: Channel changed to {new_channel}")
            self.route_audio_signal.emit(line_id, new_channel)
            self._update_display()
    
    def _update_display(self):
        """Update all line displays"""
        for widget in self.line_widgets:
            widget.update_display()
        
        # Update audio routing display
        lines = [self.sip_engine.get_line(i) for i in range(1, 9)]
        self.audio_widget.update_routing_display(lines)
    
    def closeEvent(self, event):
        """Handle window close"""
        self.update_timer.stop()
        event.accept()
