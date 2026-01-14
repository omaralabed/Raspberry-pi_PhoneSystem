#!/usr/bin/env python3
"""
Main Window - TouchScreen GUI
"""

import sys
import json
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QFrame, QMessageBox, 
                             QComboBox, QDialog, QLineEdit, QSpinBox, QFormLayout, 
                             QDialogButtonBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent, QCoreApplication
from PyQt5.QtGui import QFont, QPalette, QColor
import logging

from .dialer_widget import DialerWidget
from .line_widget import LineWidget
from .audio_widget import AudioWidget
from .sip_settings import SIPSettingsDialog

logger = logging.getLogger(__name__)


class VirtualKeyboard(QWidget):
    """Modern virtual on-screen keyboard matching tvOS design"""
    
    key_pressed = pyqtSignal(str)
    close_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shift_active = False
        self.setFixedHeight(310)
        self._create_ui()
    
    def _create_ui(self):
        """Create tvOS-style keyboard layout using grid"""
        # Use grid layout for precise positioning
        grid = QGridLayout(self)
        grid.setSpacing(8)
        grid.setContentsMargins(15, 12, 15, 12)
        
        # Set widget background
        self.setStyleSheet("VirtualKeyboard { background-color: #18181b; border-radius: 12px; }")
        
        # Key style for regular keys
        key_style = "QPushButton { background-color: #3f3f46; color: white; border: none; border-radius: 8px; font-size: 20px; } QPushButton:pressed { background-color: #52525b; }"
        
        # Keyboard letters - 4 rows of 10 each (stored as uppercase for key reference)
        rows = [
            ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
            ['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
            ['u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3'],
            ['4', '5', '6', '7', '8', '9', '+', '-', '.', '@']
        ]
        
        self.key_buttons = {}
        
        # Add character keys to grid
        for row_idx, row in enumerate(rows):
            for col_idx, key in enumerate(row):
                btn = QPushButton(key)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.setFixedHeight(48)
                btn.setStyleSheet(key_style)
                btn.clicked.connect(lambda checked, k=key: self._on_key_click(k))
                grid.addWidget(btn, row_idx, col_idx)
                self.key_buttons[key] = btn
        
        # Bottom row (row 4) - abc spans 2 cols, Space spans 4 cols, Delete spans 2 cols, Done spans 2 cols
        # abc button
        abc_btn = QPushButton('abc')
        abc_btn.setFocusPolicy(Qt.NoFocus)
        abc_btn.setFixedHeight(52)
        abc_btn.setCheckable(True)
        abc_btn.setStyleSheet(key_style)
        abc_btn.clicked.connect(lambda: self._on_key_click('ABC'))
        grid.addWidget(abc_btn, 4, 0, 1, 2)
        self.key_buttons['ABC'] = abc_btn
        
        # Space button
        space_btn = QPushButton('Space')
        space_btn.setFocusPolicy(Qt.NoFocus)
        space_btn.setFixedHeight(52)
        space_btn.setStyleSheet(key_style)
        space_btn.clicked.connect(lambda: self._on_key_click('SPACE'))
        grid.addWidget(space_btn, 4, 2, 1, 4)
        
        # Delete button (orange)
        delete_btn = QPushButton('Delete')
        delete_btn.setFocusPolicy(Qt.NoFocus)
        delete_btn.setFixedHeight(52)
        delete_btn.setStyleSheet("QPushButton { background-color: #f97316; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; } QPushButton:pressed { background-color: #ea580c; }")
        delete_btn.clicked.connect(lambda: self._on_key_click('DEL'))
        grid.addWidget(delete_btn, 4, 6, 1, 2)
        
        # Done button (green)
        done_btn = QPushButton('Done')
        done_btn.setFocusPolicy(Qt.NoFocus)
        done_btn.setFixedHeight(52)
        done_btn.setStyleSheet("QPushButton { background-color: #22c55e; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; } QPushButton:pressed { background-color: #16a34a; }")
        done_btn.clicked.connect(lambda: self._on_key_click('Done'))
        grid.addWidget(done_btn, 4, 8, 1, 2)
    
    def _on_key_click(self, key):
        """Handle key press"""
        if key == 'ABC':
            self.shift_active = self.key_buttons['ABC'].isChecked()
            self._update_key_labels()
        elif key == 'SPACE':
            self.key_pressed.emit(' ')
        elif key == 'DEL':
            self.key_pressed.emit('\b')
        elif key == 'Done':
            self.key_pressed.emit('\n')
            self.close_requested.emit()
        else:
            char = key.upper() if self.shift_active else key.lower()
            self.key_pressed.emit(char)
            if self.shift_active and key.isalpha():
                self.shift_active = False
                self.key_buttons['ABC'].setChecked(False)
                self._update_key_labels()
    
    def _update_key_labels(self):
        """Update key labels based on shift state"""
        for key, btn in self.key_buttons.items():
            if len(key) == 1 and key.isalpha():
                btn.setText(key.upper() if self.shift_active else key.lower())
        if 'ABC' in self.key_buttons:
            self.key_buttons['ABC'].setText('ABC' if self.shift_active else 'abc')


class SIPSettingsDialog(QDialog):
    """Dialog for configuring SIP credentials"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIP Settings")
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(850)  # Increased for keyboard + buttons
        
        # Current active input field
        self.active_input = None
        
        # Load current config - use path relative to script location
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(script_dir, "config", "sip_config.json")
        self.load_config()
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e,
                    stop:1 #16213e
                );
            }
            QLabel {
                color: #eaeaea;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit, QSpinBox {
                background-color: #2d3748;
                color: white;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                min-height: 35px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid rgba(0, 212, 255, 0.6);
            }
            QPushButton {
                background-color: #4a5568;
                color: white;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #5a6578;
                border: 2px solid rgba(0, 212, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: #3d4758;
            }
        """)
        
        self._create_ui()
    
    def load_config(self):
        """Load current SIP configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load SIP config: {e}")
            self.config = {
                "sip_server": "sip.example.com",
                "sip_port": 5060,
                "transport": "UDP",
                "username": "",
                "password": "",
                "caller_id_name": "Production Phone",
                "caller_id_number": "",
            }
    
    def _create_ui(self):
        """Create settings dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title = QLabel("SIP Trunk Configuration")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #00d4ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Create all input fields and connect focus events
        self.input_fields = []
        
        # SIP Server
        self.server_input = QLineEdit(self.config.get("sip_server", ""))
        self.server_input.setPlaceholderText("e.g., sip.vonage.com")
        self.server_input.installEventFilter(self)
        self.input_fields.append(self.server_input)
        form_layout.addRow("SIP Server:", self.server_input)
        
        # SIP Port (text input for virtual keyboard)
        self.port_input = QLineEdit(str(self.config.get("sip_port", 5060)))
        self.port_input.setPlaceholderText("5060")
        self.port_input.installEventFilter(self)
        self.input_fields.append(self.port_input)
        form_layout.addRow("SIP Port:", self.port_input)
        
        # Transport
        self.transport_input = QComboBox()
        self.transport_input.addItems(["UDP", "TCP", "TLS"])
        self.transport_input.setCurrentText(self.config.get("transport", "UDP"))
        self.transport_input.setStyleSheet("""
            QComboBox {
                background-color: #2d3748;
                color: white;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                min-height: 35px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                selection-background-color: #00d4ff;
                selection-color: #1a1a2e;
                border: 2px solid rgba(0, 212, 255, 0.3);
            }
        """)
        form_layout.addRow("Transport:", self.transport_input)
        
        # Username
        self.username_input = QLineEdit(self.config.get("username", ""))
        self.username_input.setPlaceholderText("SIP Username")
        self.username_input.installEventFilter(self)
        self.input_fields.append(self.username_input)
        form_layout.addRow("Username:", self.username_input)
        
        # Password
        self.password_input = QLineEdit(self.config.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("SIP Password")
        self.password_input.installEventFilter(self)
        self.input_fields.append(self.password_input)
        form_layout.addRow("Password:", self.password_input)
        
        # Caller ID Name
        self.callerid_name_input = QLineEdit(self.config.get("caller_id_name", ""))
        self.callerid_name_input.setPlaceholderText("e.g., Production Phone")
        self.callerid_name_input.installEventFilter(self)
        self.input_fields.append(self.callerid_name_input)
        form_layout.addRow("Caller ID Name:", self.callerid_name_input)
        
        # Caller ID Number
        self.callerid_number_input = QLineEdit(self.config.get("caller_id_number", ""))
        self.callerid_number_input.setPlaceholderText("e.g., +1234567890")
        self.callerid_number_input.installEventFilter(self)
        self.input_fields.append(self.callerid_number_input)
        form_layout.addRow("Caller ID Number:", self.callerid_number_input)
        
        layout.addLayout(form_layout)
        
        # Add spacing before info label
        layout.addSpacing(15)
        
        # Info label
        info = QLabel("Tap a field to show keyboard • Changes require restart")
        info.setStyleSheet("color: #ffa500; font-size: 11px; font-weight: normal; padding: 5px 0px;")
        info.setWordWrap(True)
        info.setFixedHeight(25)
        layout.addWidget(info)
        
        # Add spacing before keyboard
        layout.addSpacing(10)
        
        # Virtual Keyboard
        self.keyboard = VirtualKeyboard(self)
        self.keyboard.key_pressed.connect(self._on_keyboard_key)
        self.keyboard.close_requested.connect(self._hide_keyboard)
        self.keyboard.hide()  # Hide keyboard initially
        layout.addWidget(self.keyboard)
        
        # Buttons - always visible at bottom
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFocusPolicy(Qt.NoFocus)  # Prevent stealing focus
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFocusPolicy(Qt.NoFocus)  # Prevent stealing focus
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def showEvent(self, event):
        """Handle dialog show - ensure keyboard starts hidden"""
        super().showEvent(event)
        # Clear any automatic focus and hide keyboard
        self.setFocus()  # Move focus to dialog itself
        self.keyboard.hide()
        self.active_input = None
    
    def _hide_keyboard(self):
        """Hide the virtual keyboard"""
        self.keyboard.hide()
        if self.active_input:
            self.active_input.clearFocus()
    
    def _show_keyboard(self):
        """Show the virtual keyboard"""
        self.keyboard.show()
    
    def eventFilter(self, obj, event):
        """Handle focus events to track active input field and show/hide keyboard"""
        if event.type() == QEvent.FocusIn:
            if isinstance(obj, QLineEdit):
                self.active_input = obj
                # Highlight active field
                obj.setStyleSheet("""
                    QLineEdit {
                        background-color: #2d3748;
                        color: white;
                        border: 2px solid #00d4ff;
                        border-radius: 6px;
                        padding: 8px;
                        font-size: 13px;
                        min-height: 35px;
                    }
                """)
                # Show keyboard when text field is focused
                self._show_keyboard()
        elif event.type() == QEvent.FocusOut:
            if isinstance(obj, QLineEdit):
                # Reset field style
                obj.setStyleSheet("""
                    QLineEdit {
                        background-color: #2d3748;
                        color: white;
                        border: 2px solid rgba(0, 212, 255, 0.3);
                        border-radius: 6px;
                        padding: 8px;
                        font-size: 13px;
                        min-height: 35px;
                    }
                """)
                # Hide keyboard when focus leaves text field (with slight delay to allow keyboard clicks)
                QTimer.singleShot(200, self._check_hide_keyboard)
        return super().eventFilter(obj, event)
    
    def _check_hide_keyboard(self):
        """Check if keyboard should be hidden (no text field has focus)"""
        # Check if any input field currently has focus
        for field in self.input_fields:
            if field.hasFocus():
                return  # Don't hide, a field still has focus
        # No text field has focus, hide keyboard and show buttons
        self._hide_keyboard()
    
    def _on_keyboard_key(self, key):
        """Handle virtual keyboard key press"""
        if not self.active_input:
            # Default to first input field
            self.active_input = self.server_input
            self.active_input.setFocus()
            return
        
        # Keep focus on active input
        if not self.active_input.hasFocus():
            self.active_input.setFocus()
        
        if key == '\b':  # Backspace
            self.active_input.backspace()
        elif key == '\n':  # Done - hide keyboard
            self._hide_keyboard()
        else:
            self.active_input.insert(key)
    
    def save_settings(self):
        """Save settings to config file"""
        try:
            # Update config
            self.config["sip_server"] = self.server_input.text()
            # Convert port text to integer, default to 5060 if invalid
            try:
                port = int(self.port_input.text())
                if port < 1 or port > 65535:
                    port = 5060
            except ValueError:
                port = 5060
            self.config["sip_port"] = port
            self.config["transport"] = self.transport_input.currentText()
            self.config["username"] = self.username_input.text()
            self.config["password"] = self.password_input.text()
            self.config["caller_id_name"] = self.callerid_name_input.text()
            self.config["caller_id_number"] = self.callerid_number_input.text()
            
            # Write to file
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("SIP settings saved successfully")
            
            # Show success message
            QMessageBox.information(
                self,
                "Settings Saved",
                "SIP settings have been saved.\n\nPlease restart the phone system for changes to take effect."
            )
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save SIP settings: {e}")
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save settings:\n{str(e)}"
            )


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
        
        # Cache for line selector state
        self._last_available_lines = None
        
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
        self.update_timer.start(2000)  # Update every 2 seconds (reduce CPU load)
        
        # Mouse cursor auto-hide setup
        self.cursor_hide_timer = QTimer()
        self.cursor_hide_timer.timeout.connect(self._hide_cursor)
        self.cursor_hide_timer.setSingleShot(True)
        self.cursor_visible = True
        
        # Install application-wide event filter to catch all mouse movements
        QCoreApplication.instance().installEventFilter(self)
        logger.info("Cursor auto-hide enabled with application-wide event filter")
        
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
        
        # Line selection dropdown - shows only available lines
        self.line_selector = QComboBox()
        self.line_selector.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.line_selector.setMinimumHeight(60)
        self.line_selector.setMinimumWidth(400)
        self.line_selector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.line_selector.currentIndexChanged.connect(self._on_line_selector_changed)
        self.line_selector.setStyleSheet("""
            QComboBox {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5568,
                    stop:1 #2d3748
                );
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 10px;
                padding: 15px;
                padding-right: 50px;
                color: white;
                font-weight: bold;
                font-size: 11pt;
            }
            QComboBox:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6578,
                    stop:1 #3d4758
                );
                border: 2px solid rgba(0, 212, 255, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
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
                min-width: 400px;
            }
        """)
        layout.addWidget(self.line_selector)
        
        # Dialer widget
        self.dialer = DialerWidget(self)
        self.dialer.call_requested.connect(self._on_call_requested)
        layout.addWidget(self.dialer, stretch=1)
        
        # Audio routing widget
        self.audio_widget = AudioWidget(self.audio_router, self)
        layout.addWidget(self.audio_widget)
        
        # Settings button at the bottom
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.settings_btn.setMinimumHeight(50)
        self.settings_btn.clicked.connect(self._show_settings)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5568,
                    stop:1 #2d3748
                );
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 10px;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6578,
                    stop:1 #3d4758
                );
                border: 2px solid rgba(0, 212, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3d4758,
                    stop:1 #2d3748
                );
            }
        """)
        layout.addWidget(self.settings_btn)
        
        return panel
    
    def _on_line_selector_changed(self, index: int):
        """Handle line selection from dropdown"""
        if index == 0:
            # "Select a line..." option
            self.selected_line_id = None
            logger.info("Line selection cleared")
        else:
            # Get the line_id from the combo box item data
            line_id = self.line_selector.itemData(index)
            if line_id:
                self.selected_line_id = line_id
                logger.info(f"Line {line_id} selected from dropdown")
    
    def _update_line_selector(self):
        """Update the line selector dropdown with available lines - with caching"""
        # Get current available lines
        available_lines = []
        for line_id in range(1, 9):
            line = self.sip_engine.get_line(line_id)
            if line and line.is_available():
                available_lines.append(line_id)
        
        # Check if available lines changed
        if tuple(available_lines) == self._last_available_lines:
            return  # No change, skip expensive update
        self._last_available_lines = tuple(available_lines)
        
        # Store current selection
        current_line = self.selected_line_id
        
        # Block signals while updating
        self.line_selector.blockSignals(True)
        self.line_selector.clear()
        
        # Add default option
        self.line_selector.addItem("Select a line to dial...", None)
        
        # Add available lines
        for line_id in available_lines:
            self.line_selector.addItem(f"Line {line_id} (Available)", line_id)
        
        # Restore selection if still valid
        if current_line:
            for i in range(self.line_selector.count()):
                if self.line_selector.itemData(i) == current_line:
                    self.line_selector.setCurrentIndex(i)
                    break
            else:
                # Line no longer available, reset
                self.selected_line_id = None
                self.line_selector.setCurrentIndex(0)
        else:
            self.line_selector.setCurrentIndex(0)
        
        # Unblock signals
        self.line_selector.blockSignals(False)
    
    def _on_call_requested(self, phone_number: str):
        """Handle call request from dialer"""
        if not self.selected_line_id:
            logger.warning("Call requested but no line selected")
            self._show_styled_message("No Line Selected", "Please select a line from the dropdown first")
            return
        
        line = self.sip_engine.get_line(self.selected_line_id)
        if not line.is_available():
            logger.warning(f"Line {self.selected_line_id} not available")
            self._show_styled_message("Line Unavailable", f"Line {self.selected_line_id} is not available")
            return
        
        # Make call
        logger.info(f"Making call on line {self.selected_line_id} to {phone_number}")
        self.make_call_signal.emit(self.selected_line_id, phone_number)
        
        # Clear selection - reset dropdown to "Select a line..."
        self.selected_line_id = None
        self.line_selector.setCurrentIndex(0)
        
        # Update UI
        self._update_display()
    
    def _on_hangup_clicked(self, line_id: int):
        """Handle hangup button click"""
        logger.info(f"[MainWindow] Hangup clicked signal received for line {line_id}")
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
        
        # Update line selector dropdown
        self._update_line_selector()
    
    def _show_styled_message(self, title: str, message: str):
        """Show a styled message dialog"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Style the message box for better visibility
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2a2a2a;
                color: white;
                font-size: 18px;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                min-width: 500px;
                max-width: 600px;
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
        
        # Position the dialog below the line selector dropdown
        selector_pos = self.line_selector.mapToGlobal(self.line_selector.rect().bottomLeft())
        msg_box.move(selector_pos.x(), selector_pos.y() + 10)
        
        msg_box.exec_()
    
    def _show_settings(self):
        """Show SIP settings dialog with authorization warning"""
        # Create custom warning dialog
        warning = QDialog(self)
        warning.setWindowTitle("Authorization Required")
        warning.setFixedSize(500, 250)
        warning.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border: 2px solid #3b82f6;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(warning)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Warning message
        label = QLabel("Only authorized users may change this setting.")
        label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(150, 60)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #4b5563;
            }
        """)
        cancel_btn.clicked.connect(warning.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedSize(150, 60)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #2563eb;
            }
        """)
        ok_btn.clicked.connect(warning.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        # Position over settings button
        btn_pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().center())
        warning.move(btn_pos.x() - warning.width() // 2, btn_pos.y() - warning.height() - 20)
        
        if warning.exec_() != QDialog.Accepted:
            return
        
        logger.info("Opening SIP settings dialog")
        dialog = SIPSettingsDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            logger.info("SIP settings updated - restart required")
    
    def eventFilter(self, obj, event):
        """Application-wide event filter to detect mouse movement"""
        if event.type() == QEvent.MouseMove:
            self._show_cursor()
            self.cursor_hide_timer.start(3000)  # Hide after 3 seconds
        return super().eventFilter(obj, event)
    
    def _show_cursor(self):
        """Show the mouse cursor"""
        if not self.cursor_visible:
            QCoreApplication.instance().restoreOverrideCursor()
            self.cursor_visible = True
            logger.info("Mouse cursor shown")
    
    def _hide_cursor(self):
        """Hide the mouse cursor after inactivity"""
        if self.cursor_visible:
            QCoreApplication.instance().setOverrideCursor(Qt.BlankCursor)
            self.cursor_visible = False
            logger.info("Mouse cursor hidden")
    
    def _show_settings(self):
        """Show SIP settings dialog"""
        logger.info("Opening SIP settings dialog")
        dialog = SIPSettingsDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            logger.info("SIP settings updated - restart required")
    
    def closeEvent(self, event):
        """Handle window close"""
        self.update_timer.stop()
        self.cursor_hide_timer.stop()
        QCoreApplication.instance().removeEventFilter(self)
        event.accept()
