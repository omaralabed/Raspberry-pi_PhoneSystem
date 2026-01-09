#!/usr/bin/env python3
"""
Dialer Widget - Touchscreen Number Pad
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLineEdit, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class DialerWidget(QWidget):
    """
    Touchscreen dialer pad with number entry and call button
    """
    
    # Signal emitted when call button is pressed
    call_requested = pyqtSignal(str)  # phone_number
    
    def __init__(self, parent=None):
        """Initialize dialer widget"""
        super().__init__(parent)
        
        self.phone_number = ""
        self._create_ui()
        
        logger.info("Dialer widget initialized")
    
    def _create_ui(self):
        """Create modern dialer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Number display with modern styling
        self.number_display = QLineEdit()
        self.number_display.setReadOnly(True)
        self.number_display.setAlignment(Qt.AlignRight)
        self.number_display.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.number_display.setMinimumHeight(60)
        self.number_display.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3748,
                    stop:1 #1a202c
                );
                color: #00d4ff;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 10px;
                padding: 10px 15px;
                letter-spacing: 2px;
            }
        """)
        layout.addWidget(self.number_display)
        
        # Number pad grid with modern buttons
        grid = QGridLayout()
        grid.setSpacing(8)
        
        # Button layout: standard phone pad
        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('*', 3, 0), ('0', 3, 1), ('#', 3, 2),
        ]
        
        for text, row, col in buttons:
            btn = self._create_number_button(text)
            grid.addWidget(btn, row, col)
        
        layout.addLayout(grid)
        
        # Action buttons row with modern styling
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        
        # Backspace button
        self.backspace_btn = QPushButton("Delete")
        self.backspace_btn.setMinimumHeight(55)
        self.backspace_btn.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.backspace_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff9f1a,
                    stop:1 #ff7f00
                );
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffb84d,
                    stop:1 #ff9933
                );
            }
            QPushButton:pressed {
                background: #cc6600;
                padding: 1px 0px 0px 1px;
            }
        """)
        self.backspace_btn.clicked.connect(self._on_backspace)
        action_layout.addWidget(self.backspace_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMinimumHeight(55)
        self.clear_btn.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b,
                    stop:1 #ee5a6f
                );
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff8585,
                    stop:1 #ff7289
                );
            }
            QPushButton:pressed {
                background: #cc3e3e;
                padding: 1px 0px 0px 1px;
            }
        """)
        self.clear_btn.clicked.connect(self._on_clear)
        action_layout.addWidget(self.clear_btn)
        
        layout.addLayout(action_layout)
        
        # Call button (large, prominent with glow effect)
        self.call_btn = QPushButton("📞 CALL")
        self.call_btn.setMinimumHeight(70)
        self.call_btn.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.call_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2ed573,
                    stop:1 #26de81
                );
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                letter-spacing: 3px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3ee583,
                    stop:1 #36ee91
                );
            }
            QPushButton:pressed {
                background: #1ea755;
                padding: 2px 0px 0px 2px;
            }
            QPushButton:disabled {
                background-color: #4a4a4a;
                color: #888;
            }
        """)
        self.call_btn.clicked.connect(self._on_call)
        self.call_btn.setEnabled(False)
        layout.addWidget(self.call_btn)
    
    def _create_number_button(self, text: str) -> QPushButton:
        """Create a modern number pad button"""
        btn = QPushButton(text)
        btn.setMinimumHeight(60)
        btn.setFont(QFont("Segoe UI", 22, QFont.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a5568,
                    stop:1 #2d3748
                );
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6578,
                    stop:1 #3d4758
                );
                border: 2px solid rgba(0, 212, 255, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00d4ff,
                    stop:1 #00a8cc
                );
                color: #1a1a2e;
                padding: 2px 0px 0px 2px;
            }
        """)
        btn.clicked.connect(lambda: self._on_digit_pressed(text))
        return btn
    
    def _on_digit_pressed(self, digit: str):
        """Handle number button press"""
        self.phone_number += digit
        self.number_display.setText(self.phone_number)
        self.call_btn.setEnabled(len(self.phone_number) > 0)
        logger.debug(f"Digit pressed: {digit}, number: {self.phone_number}")
    
    def _on_backspace(self):
        """Remove last digit"""
        if self.phone_number:
            self.phone_number = self.phone_number[:-1]
            self.number_display.setText(self.phone_number)
            self.call_btn.setEnabled(len(self.phone_number) > 0)
            logger.debug(f"Backspace, number: {self.phone_number}")
    
    def _on_clear(self):
        """Clear all digits"""
        self.phone_number = ""
        self.number_display.setText(self.phone_number)
        self.call_btn.setEnabled(False)
        logger.debug("Number cleared")
    
    def _on_call(self):
        """Emit call requested signal"""
        if self.phone_number:
            logger.info(f"Call requested: {self.phone_number}")
            self.call_requested.emit(self.phone_number)
            # Clear after calling
            self._on_clear()
