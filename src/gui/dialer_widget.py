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
        """Create dialer UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Number display
        self.number_display = QLineEdit()
        self.number_display.setReadOnly(True)
        self.number_display.setAlignment(Qt.AlignRight)
        self.number_display.setFont(QFont("Arial", 18, QFont.Bold))
        self.number_display.setMinimumHeight(50)
        self.number_display.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 2px solid #555;
                padding: 5px;
            }
        """)
        layout.addWidget(self.number_display)
        
        # Number pad grid
        grid = QGridLayout()
        grid.setSpacing(5)
        
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
        
        # Action buttons row
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)
        
        # Backspace button
        self.backspace_btn = QPushButton("⌫ Back")
        self.backspace_btn.setMinimumHeight(50)
        self.backspace_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.backspace_btn.setStyleSheet("""
            QPushButton {
                background-color: #8a5a2a;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #6a4a1a;
            }
        """)
        self.backspace_btn.clicked.connect(self._on_backspace)
        action_layout.addWidget(self.backspace_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMinimumHeight(50)
        self.clear_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #8a2a2a;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #6a1a1a;
            }
        """)
        self.clear_btn.clicked.connect(self._on_clear)
        action_layout.addWidget(self.clear_btn)
        
        layout.addLayout(action_layout)
        
        # Call button (large, prominent)
        self.call_btn = QPushButton("📞 CALL")
        self.call_btn.setMinimumHeight(60)
        self.call_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.call_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a8a2a;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #1a6a1a;
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
        """Create a number pad button"""
        btn = QPushButton(text)
        btn.setMinimumHeight(50)
        btn.setFont(QFont("Arial", 18, QFont.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: white;
                border: 1px solid #666;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #2a5a8a;
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
