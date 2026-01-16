#!/usr/bin/env python3
"""
Main Window - TouchScreen GUI
"""

import sys
import json
import os
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QFrame, QMessageBox, 
                             QComboBox, QDialog, QLineEdit, QSpinBox, QFormLayout, 
                             QDialogButtonBox, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent, QCoreApplication, QProcess, QObject
from PyQt5.QtGui import QFont, QPalette, QColor
import logging

from .dialer_widget import DialerWidget
from .line_widget import LineWidget
from .audio_widget import AudioWidget
from .sip_settings import SIPSettingsDialog

logger = logging.getLogger(__name__)


def load_stylesheet():
    """Load the main CSS stylesheet"""
    css_path = Path(__file__).parent.parent.parent / 'config' / 'styles.css'
    try:
        with open(css_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load stylesheet: {e}")
        return ""


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
        
        # Load and apply global stylesheet
        stylesheet = load_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
            logger.info("Loaded global stylesheet from config/styles.css")
        
        # UI Setup
        self.setWindowTitle("Phone System - IFB/PL")
        
        # Get screen geometry and force window to use full screen size
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        logger.info(f"Screen detected: {screen_geometry.width()}x{screen_geometry.height()}")
        self.setGeometry(screen_geometry)
        
        # Make window fullscreen and responsive to any screen size
        self.showFullScreen()
        logger.info(f"Window geometry after showFullScreen: {self.geometry().width()}x{self.geometry().height()}")
        
        # NOTE: _apply_theme() removed - using CSS file instead (config/styles.css)
        
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
        """Apply professional broadcast theme"""
        # Broadcast-style dark theme with orange accents
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                border-radius: 4px;
            }
        """)
    
    def _create_ui(self):
        """Create main UI layout"""
        central_widget = QWidget()
        central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(5)
        
        
        # Top: Line status widgets (takes most space - now full width)
        line_panel = self._create_line_panel()
        line_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(line_panel, stretch=10)
        
        # Bottom: Compact test panel (Hold to Test + Channel + Settings)
        bottom_panel = self._create_bottom_test_panel()
        main_layout.addWidget(bottom_panel)
    
    def _create_line_panel(self) -> QWidget:
        """Create panel with 8 line status widgets - Broadcast style"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QGridLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create 8 line widgets (2 columns x 4 rows)
        self.line_widgets = []
        for i in range(8):
            line = self.sip_engine.get_line(i + 1)
            widget = LineWidget(line, self)
            widget.hangup_clicked.connect(self._on_hangup_clicked)
            widget.make_call.connect(self._on_line_make_call)
            widget.audio_channel_changed.connect(self._on_audio_channel_changed)
            
            row = i // 2
            col = i % 2
            layout.addWidget(widget, row, col)
            
            self.line_widgets.append(widget)
        
        return panel
    
    def _create_control_panel(self) -> QWidget:
        """Create dialer and audio control panel - Broadcast style"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top row: Line selector and Settings button
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # Line selection dropdown - shows only available lines
        self.line_selector = QComboBox()
        self.line_selector.setObjectName("line_selector")  # Use CSS from styles.css
        self.line_selector.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.line_selector.setMinimumHeight(60)
        self.line_selector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.line_selector.currentIndexChanged.connect(self._on_line_selector_changed)
        
        # Make dropdown list fill entire space - same as test channel
        self.line_selector.view().setMinimumWidth(600)
        self.line_selector.view().setMinimumHeight(752)  # Same as test channel
        self.line_selector.view().setSpacing(28)  # Big spacing between items
        self.line_selector.view().setUniformItemSizes(True)
        
        top_layout.addWidget(self.line_selector, stretch=1)
        
        # Settings button (gear icon only) - Broadcast style
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.settings_btn.setMinimumSize(50, 50)
        self.settings_btn.setMaximumSize(60, 60)
        self.settings_btn.clicked.connect(self._show_settings)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 2px solid #404040;
                border-radius: 4px;
                color: #ff6b35;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #ff6b35;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)
        top_layout.addWidget(self.settings_btn)
        
        layout.addLayout(top_layout)
        
        # Audio routing widget
        self.audio_widget = AudioWidget(self.audio_router, self)
        layout.addWidget(self.audio_widget)
        
        return panel
    
    def _create_bottom_test_panel(self) -> QWidget:
        """Create compact bottom panel with Hold to Test button, channel selector, and settings"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        panel.setMaximumHeight(80)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # Channel selector label
        channel_label = QLabel("Test Channel:")
        channel_label.setStyleSheet("color: #ff6b35; font-weight: bold; font-size: 11pt;")
        layout.addWidget(channel_label)
        
        # Channel dropdown (combobox) - vertical list picker
        self.test_channel_combo = QComboBox()
        self.test_channel_combo.setObjectName("test_channel_combo")  # Use CSS from styles.css
        self.test_channel_combo.setMinimumWidth(150)
        self.test_channel_combo.setMinimumHeight(60)
        self.test_channel_combo.setMaxVisibleItems(8)  # Show all 8 channels at once
        # Add all 8 channels
        for i in range(1, 9):
            self.test_channel_combo.addItem(f"Channel {i}", i)
        
        # Force items to fill entire dropdown list height - NO EMPTY SPACE
        # Keep list at good size, items will spread out to fill it
        self.test_channel_combo.view().setMinimumWidth(500)
        self.test_channel_combo.view().setMinimumHeight(752)  # Fixed list size
        self.test_channel_combo.view().setSpacing(28)  # BIGGER spacing to fill ALL the way to bottom
        self.test_channel_combo.view().setUniformItemSizes(True)
        
        layout.addWidget(self.test_channel_combo)
        
        # Hold to Test button
        self.hold_test_btn = QPushButton("🔊 Hold to Test")
        self.hold_test_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.hold_test_btn.setMinimumHeight(50)
        self.hold_test_btn.setMinimumWidth(200)
        self.hold_test_btn.pressed.connect(self._on_hold_test_pressed)
        self.hold_test_btn.released.connect(self._on_hold_test_released)
        self.hold_test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #00d4ff, stop:1 #0088cc);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #00e4ff, stop:1 #0099dd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #2ed573, stop:1 #26de81);
            }
        """)
        layout.addWidget(self.hold_test_btn)
        
        layout.addStretch()
        
        # Settings button (moved from top)
        settings_btn = QPushButton("⚙")
        settings_btn.setFont(QFont("Segoe UI", 18, QFont.Bold))
        settings_btn.setMinimumSize(55, 55)
        settings_btn.setMaximumSize(65, 65)
        settings_btn.clicked.connect(self._show_settings)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 2px solid #404040;
                border-radius: 4px;
                color: #ff6b35;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #ff6b35;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)
        layout.addWidget(settings_btn)
        
        return panel
    
    def _on_hold_test_pressed(self):
        """Start test tone when button pressed"""
        if not self.audio_router:
            logger.warning("Cannot test audio: audio router not available")
            return
        
        channel = self.test_channel_combo.currentData()  # Get selected channel number
        logger.info(f"Hold to Test pressed - starting tone on channel {channel}")
        self.audio_router.start_continuous_tone(channel)
    
    def _on_hold_test_released(self):
        """Stop test tone when button released"""
        if not self.audio_router:
            return
        
        logger.info("Hold to Test released - stopping tone")
        self.audio_router.stop_continuous_tone()
    
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
    
    def _on_hangup_clicked(self, line_id: int):
        """Handle hangup button click"""
        logger.info(f"[MainWindow] Hangup clicked signal received for line {line_id}")
        self.hangup_signal.emit(line_id)
    
    def _on_line_make_call(self, line_id: int, phone_number: str):
        """Handle make call from line widget popup dialer"""
        logger.info(f"[MainWindow] Making call on line {line_id} to {phone_number}")
        self.make_call_signal.emit(line_id, phone_number)
    
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
            
            # Center the message box on screen
            from PyQt5.QtWidgets import QApplication
            screen_center = QApplication.primaryScreen().geometry().center()
            msg.move(screen_center.x() - msg.width() // 2, screen_center.y() - msg.height() // 2)
            
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
        """Update all line displays - optimized for large screens"""
        try:
            # Update widgets - caching in update_display() prevents unnecessary work
            for widget in self.line_widgets:
                widget.update_display()
            
            # Update audio routing display (has its own caching)
            lines = [self.sip_engine.get_line(i) for i in range(1, 9)]
            self.audio_widget.update_routing_display(lines)
            
            # Update line selector dropdown (has its own caching)
            self._update_line_selector()
        except Exception as e:
            logger.error(f"Error in _update_display: {e}", exc_info=True)
    
    def _show_styled_message(self, title: str, message: str):
        """Show a styled message dialog"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Style the message box for better visibility - more compact for small screens
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2a2a2a;
                color: white;
                font-size: 14px;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                min-width: 300px;
                max-width: 400px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: 2px solid #666;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #888;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)
        
        # Center the message box on screen
        from PyQt5.QtWidgets import QApplication
        screen_center = QApplication.primaryScreen().geometry().center()
        msg_box.adjustSize()  # Ensure size is calculated
        msg_box.move(screen_center.x() - msg_box.width() // 2, screen_center.y() - msg_box.height() // 2)
        
        msg_box.exec_()
    
    def _show_settings(self):
        """Show settings menu with options"""
        # Create settings menu dialog
        menu_dialog = QDialog(self)
        menu_dialog.setWindowTitle("Settings")
        menu_dialog.setMinimumSize(600, 500)
        menu_dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                border: 3px solid #ff6b35;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(menu_dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("⚙ Settings")
        title.setStyleSheet("color: #ff6b35; font-size: 32pt; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # SIP Configuration button
        sip_btn = QPushButton("📞 SIP Configuration")
        sip_btn.setMinimumHeight(100)
        sip_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 2px solid #404040;
                border-radius: 8px;
                font-size: 24pt;
                font-weight: bold;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #ff6b35;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        sip_btn.clicked.connect(lambda: self._show_sip_settings(menu_dialog))
        layout.addWidget(sip_btn)
        
        # Network Configuration button
        network_btn = QPushButton("🌐 Network Configuration")
        network_btn.setMinimumHeight(100)
        network_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 2px solid #404040;
                border-radius: 8px;
                font-size: 24pt;
                font-weight: bold;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #00d4ff;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        network_btn.clicked.connect(lambda: self._show_network_settings(menu_dialog))
        layout.addWidget(network_btn)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(80)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 22pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7d8a94;
            }
            QPushButton:pressed {
                background-color: #5a6268;
            }
        """)
        close_btn.clicked.connect(menu_dialog.close)
        layout.addWidget(close_btn)
        
        # Position dialog on right side of screen
        from PyQt5.QtWidgets import QApplication
        menu_dialog.adjustSize()
        screen_geometry = QApplication.primaryScreen().geometry()
        # Position on right side with some margin from edge
        x_position = screen_geometry.width() - menu_dialog.width() - 50
        y_position = (screen_geometry.height() - menu_dialog.height()) // 2
        menu_dialog.move(x_position, y_position)
        
        menu_dialog.exec_()
    
    def _show_sip_settings(self, parent_dialog):
        """Show SIP settings dialog with authorization warning"""
        parent_dialog.hide()  # Hide menu temporarily
        
        # Create custom warning dialog
        warning = QDialog(self)
        warning.setWindowTitle("Authorization Required")
        warning.setMinimumSize(350, 200)
        warning.setMaximumSize(500, 300)
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
        label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumSize(100, 45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #4b5563;
            }
        """)
        cancel_btn.clicked.connect(warning.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setMinimumSize(100, 45)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #2563eb;
            }
        """)
        ok_btn.clicked.connect(warning.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        # Center dialog on screen
        from PyQt5.QtWidgets import QApplication
        warning.adjustSize()
        screen_center = QApplication.primaryScreen().geometry().center()
        warning.move(screen_center.x() - warning.width() // 2, 
                    screen_center.y() - warning.height() // 2)
        
        if warning.exec_() != QDialog.Accepted:
            parent_dialog.show()  # Show menu again
            return
        
        logger.info("Opening SIP settings dialog")
        dialog = SIPSettingsDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            logger.info("SIP settings updated - restart required")
        
        parent_dialog.show()  # Show menu again
    
    def _show_network_settings(self, parent_dialog):
        """Show network configuration dialog"""
        parent_dialog.hide()  # Hide menu temporarily
        
        # Create network settings dialog - compact, no extra space
        network_dialog = QDialog(self)
        network_dialog.setWindowTitle("Network Configuration")
        network_dialog.setModal(True)
        network_dialog.setMinimumWidth(800)
        network_dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                border: 3px solid #00d4ff;
                border-radius: 12px;
            }
        """)
        
        # Simple layout - compact spacing
        layout = QVBoxLayout(network_dialog)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title (same as SIP style)
        title = QLabel("Network Configuration")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #00d4ff; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Get current IP info and detect if static or DHCP
        import subprocess
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            current_ip = result.stdout.strip().split()[0] if result.stdout else "Unknown"
        except:
            current_ip = "Unknown"
        
        # Detect current network mode (check if route is static)
        is_static = False
        current_gateway = ""
        current_dns = ""
        try:
            # Check if route is static
            route_result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                         capture_output=True, text=True, timeout=2)
            if 'proto static' in route_result.stdout:
                is_static = True
                # Extract gateway
                parts = route_result.stdout.split()
                if 'via' in parts:
                    idx = parts.index('via')
                    if idx + 1 < len(parts):
                        current_gateway = parts[idx + 1]
            
            # Get DNS server
            dns_result = subprocess.run(['resolvectl', 'status', 'eth0'], 
                                       capture_output=True, text=True, timeout=2)
            for line in dns_result.stdout.split('\n'):
                if 'DNS Servers:' in line:
                    current_dns = line.split(':')[1].strip()
                    break
        except:
            pass
        
        # Current IP display (compact info label)
        mode_text = "Static IP" if is_static else "DHCP"
        ip_info = QLabel(f"Current: {current_ip} ({mode_text})")
        ip_info.setStyleSheet("color: #ffa500; font-size: 13px; font-weight: bold;")
        layout.addWidget(ip_info)
        
        layout.addSpacing(8)
        
        # Network mode selector
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("color: #eaeaea; font-size: 16px; font-weight: bold;")
        layout.addWidget(mode_label)
        
        mode_combo = QComboBox()
        mode_combo.setObjectName("network_mode_combo")
        mode_combo.addItem("DHCP (Automatic)", "dhcp")
        mode_combo.addItem("Manual (Static IP)", "manual")
        mode_combo.setMinimumHeight(60)  # Same as test channel
        mode_combo.setMaxVisibleItems(2)  # Show both options
        
        # Make dropdown list larger with better spacing (same as test channel)
        mode_combo.view().setMinimumWidth(700)
        mode_combo.view().setMinimumHeight(200)  # Tall enough for 2 items
        mode_combo.view().setSpacing(20)  # Good spacing between items
        mode_combo.view().setUniformItemSizes(True)
        
        mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d3748;
                color: white;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 12px;
                font-size: 18px;
                font-weight: bold;
                min-height: 60px;
            }
            QComboBox::drop-down {
                border: none;
                width: 40px;
            }
            QComboBox::down-arrow {
                width: 20px;
                height: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                selection-background-color: #00d4ff;
                selection-color: #1a1a2e;
                border: 2px solid rgba(0, 212, 255, 0.3);
                font-size: 20px;
                font-weight: bold;
                padding: 15px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 80px;
                padding: 15px;
            }
        """)
        
        # Set current mode in dropdown
        if is_static:
            mode_combo.setCurrentIndex(1)  # Select "Manual (Static IP)"
        else:
            mode_combo.setCurrentIndex(0)  # Select "DHCP"
        
        layout.addWidget(mode_combo)
        
        # Manual configuration section - using QFormLayout like SIP
        manual_config = QWidget()
        manual_layout = QVBoxLayout(manual_config)
        manual_layout.setSpacing(5)
        manual_layout.setContentsMargins(0, 10, 0, 0)
        
        # "Static IP" header
        static_header = QLabel("Static IP Settings")
        static_header.setStyleSheet("color: #00d4ff; font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        manual_layout.addWidget(static_header)
        
        # Form layout for fields (same as SIP)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Style for all input fields (bigger text)
        input_style = """
            QLineEdit {
                background-color: #2d3748;
                color: white;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 12px;
                font-size: 16px;
                min-height: 45px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 212, 255, 0.6);
            }
        """
        
        # Label style (bigger text)
        label_style = "color: #eaeaea; font-size: 16px; font-weight: bold;"
        
        # IP Address
        ip_input = QLineEdit()
        ip_input.setStyleSheet(input_style)
        ip_input.setPlaceholderText("e.g., 192.168.1.221")
        if is_static and current_ip != "Unknown":
            ip_input.setText(current_ip)
        else:
            ip_input.setText("192.168.1.221")
        ip_label = QLabel("IP Address:")
        ip_label.setStyleSheet(label_style)
        form_layout.addRow(ip_label, ip_input)
        
        # Subnet Mask
        subnet_input = QLineEdit()
        subnet_input.setStyleSheet(input_style)
        subnet_input.setPlaceholderText("e.g., 255.255.255.0")
        subnet_input.setText("255.255.255.0")
        subnet_label = QLabel("Subnet Mask:")
        subnet_label.setStyleSheet(label_style)
        form_layout.addRow(subnet_label, subnet_input)
        
        # Gateway
        gateway_input = QLineEdit()
        gateway_input.setStyleSheet(input_style)
        gateway_input.setPlaceholderText("e.g., 192.168.1.1")
        if is_static and current_gateway:
            gateway_input.setText(current_gateway)
        else:
            gateway_input.setText("192.168.1.1")
        gateway_label = QLabel("Gateway:")
        gateway_label.setStyleSheet(label_style)
        form_layout.addRow(gateway_label, gateway_input)
        
        # DNS Server
        dns_input = QLineEdit()
        dns_input.setStyleSheet(input_style)
        dns_input.setPlaceholderText("e.g., 8.8.8.8")
        if is_static and current_dns:
            dns_input.setText(current_dns)
        else:
            dns_input.setText("8.8.8.8")
        dns_label = QLabel("DNS Server:")
        dns_label.setStyleSheet(label_style)
        form_layout.addRow(dns_label, dns_input)
        
        manual_layout.addLayout(form_layout)
        
        manual_config.setVisible(False)  # Hidden by default
        layout.addWidget(manual_config)
        
        # Show manual config if currently using static IP
        if is_static:
            manual_config.setVisible(True)
        
        # Store input fields and active input for keyboard handling (same pattern as SIP)
        network_dialog.input_fields = [ip_input, subnet_input, gateway_input, dns_input]
        network_dialog.active_input = None
        
        # Event filter function for keyboard handling (matches SIP pattern)
        def network_event_filter(obj, event):
            """Handle focus events to track active input field and show/hide keyboard"""
            if event.type() == QEvent.FocusIn:
                if isinstance(obj, QLineEdit):
                    network_dialog.active_input = obj
                    # Highlight active field (bigger font)
                    obj.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d3748;
                            color: white;
                            border: 2px solid #00d4ff;
                            border-radius: 6px;
                            padding: 12px;
                            font-size: 16px;
                            min-height: 45px;
                        }
                    """)
                    # Show keyboard when text field is focused
                    keyboard.show()
            elif event.type() == QEvent.FocusOut:
                if isinstance(obj, QLineEdit):
                    # Reset field style (bigger font)
                    obj.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d3748;
                            color: white;
                            border: 2px solid rgba(0, 212, 255, 0.3);
                            border-radius: 6px;
                            padding: 12px;
                            font-size: 16px;
                            min-height: 45px;
                        }
                    """)
                    # Hide keyboard when focus leaves text field (with delay to allow keyboard clicks)
                    QTimer.singleShot(200, lambda: check_hide_keyboard())
            return False
        
        def check_hide_keyboard():
            """Check if keyboard should be hidden (no text field has focus)"""
            for field in network_dialog.input_fields:
                if field.hasFocus():
                    return  # Don't hide, a field still has focus
            keyboard.hide()
        
        # Install event filter on input fields
        ip_input.installEventFilter(network_dialog)
        subnet_input.installEventFilter(network_dialog)
        gateway_input.installEventFilter(network_dialog)
        dns_input.installEventFilter(network_dialog)
        
        # Override dialog's eventFilter to use our function
        network_dialog.eventFilter = network_event_filter
        
        # Add spacing before info label
        layout.addSpacing(10)
        
        # Info label (bigger font)
        info_label = QLabel("Tap a field to show keyboard")
        info_label.setStyleSheet("color: #ffa500; font-size: 13px; font-weight: bold; padding: 5px 0px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Add spacing before keyboard
        layout.addSpacing(8)
        
        # Virtual Keyboard (same pattern as SIP settings - built into dialog)
        keyboard = VirtualKeyboard(network_dialog)
        
        def handle_keyboard_key(key):
            """Handle virtual keyboard key press"""
            if not network_dialog.active_input:
                # Default to first input field
                if network_dialog.input_fields:
                    network_dialog.active_input = network_dialog.input_fields[0]
                    network_dialog.active_input.setFocus()
                return
            
            # Keep focus on active input
            if not network_dialog.active_input.hasFocus():
                network_dialog.active_input.setFocus()
            
            if key == '\b':  # Backspace
                network_dialog.active_input.backspace()
            elif key == '\n':  # Done - hide keyboard
                keyboard.hide()
            else:
                network_dialog.active_input.insert(key)
        
        keyboard.key_pressed.connect(handle_keyboard_key)
        keyboard.close_requested.connect(lambda: keyboard.hide())
        keyboard.hide()  # Hide keyboard initially
        layout.addWidget(keyboard)
        
        # Add spacing between keyboard and buttons
        layout.addSpacing(8)
        
        # Buttons - always visible at bottom
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.addStretch()
        
        save_btn = QPushButton("Save & Restart")
        save_btn.setFocusPolicy(Qt.NoFocus)
        save_btn.setMinimumHeight(50)
        save_btn.setMinimumWidth(150)
        save_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        save_btn.clicked.connect(network_dialog.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFocusPolicy(Qt.NoFocus)
        cancel_btn.setMinimumHeight(50)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        cancel_btn.clicked.connect(network_dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Position dialog at top of screen so keyboard is fully visible
        from PyQt5.QtWidgets import QApplication
        screen_geometry = QApplication.primaryScreen().geometry()
        network_dialog.adjustSize()
        
        # Position at top-right of screen
        x_position = screen_geometry.width() - network_dialog.width() - 50
        y_position = 20  # Near top of screen
        network_dialog.move(x_position, y_position)
        
        # Show keyboard when manual mode is shown
        def on_mode_changed_with_keyboard(index):
            is_manual = mode_combo.currentData() == "manual"
            manual_config.setVisible(is_manual)
            if not is_manual:
                # Hide keyboard when switching to DHCP
                keyboard.hide()
            
            # Resize and reposition dialog after mode change
            network_dialog.adjustSize()
            screen_geometry = QApplication.primaryScreen().geometry()
            x_position = screen_geometry.width() - network_dialog.width() - 50
            y_position = 20
            network_dialog.move(x_position, y_position)
        
        mode_combo.currentIndexChanged.connect(on_mode_changed_with_keyboard)
        
        # Handle dialog accepted (Save & Restart button)
        def on_dialog_accepted():
            # Close parent settings dialog first to prevent blocking
            if parent_dialog:
                parent_dialog.close()
            
            # Get selected mode and process configuration
            selected_mode = mode_combo.currentData()
            
            if selected_mode == "dhcp":
                # Configure DHCP
                self._configure_dhcp()
            elif selected_mode == "manual":
                # Configure static IP
                ip = ip_input.text().strip()
                subnet = subnet_input.text().strip()
                gateway = gateway_input.text().strip()
                dns = dns_input.text().strip()
                
                self._configure_static_ip(ip, subnet, gateway, dns)
            
            network_dialog.close()
        
        # Handle dialog rejected (Cancel button - backup handler)
        def on_dialog_rejected():
            logger.info("Network dialog rejected signal received")
            network_dialog.close()
            if parent_dialog:
                parent_dialog.close()
        
        # Connect signals (backup handlers)
        network_dialog.accepted.connect(on_dialog_accepted)
        network_dialog.rejected.connect(on_dialog_rejected)
        
        # Show dialogs (non-blocking)
        network_dialog.show()
    
    def _detect_network_type(self):
        """Detect if system uses netplan or dhcpcd"""
        try:
            # Check for netplan
            import os
            if os.path.exists('/etc/netplan'):
                return 'netplan'
            else:
                return 'dhcpcd'
        except:
            return 'dhcpcd'  # Default fallback
    
    def _configure_dhcp(self):
        """Configure network for DHCP"""
        try:
            # Ask for confirmation FIRST
            confirm_dialog = QMessageBox(self)
            confirm_dialog.setWindowTitle("Confirm Network Change")
            confirm_dialog.setText("Switch to DHCP (Automatic)?")
            confirm_dialog.setInformativeText("System will reboot to apply changes.\n\nContinue?")
            confirm_dialog.setIcon(QMessageBox.Question)
            confirm_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            confirm_dialog.setDefaultButton(QMessageBox.Ok)
            
            # Style the dialog
            confirm_dialog.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a1a;
                    min-width: 600px;
                    min-height: 400px;
                }
                QMessageBox QLabel {
                    color: white;
                    font-size: 24pt;
                    padding: 20px;
                    min-width: 500px;
                }
                QPushButton {
                    background-color: #ff6b35;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 22pt;
                    font-weight: bold;
                    padding: 15px 40px;
                    min-width: 180px;
                    min-height: 80px;
                }
                QPushButton:hover {
                    background-color: #ff8c5a;
                }
                QPushButton:default {
                    background-color: #00d4ff;
                }
                QPushButton:default:hover {
                    background-color: #33ddff;
                }
            """)
            
            # If user clicks Cancel, abort
            if confirm_dialog.exec_() != QMessageBox.Ok:
                logger.info("User cancelled DHCP configuration")
                return
            
            # User confirmed - proceed with configuration
            network_type = self._detect_network_type()
            
            if network_type == 'netplan':
                # Netplan YAML configuration for DHCP
                config_content = """# ProComm Network Configuration
# Generated by ProComm Phone System
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: false
"""
            else:
                # dhcpcd configuration for DHCP
                config_content = """# DHCP Configuration
# Generated by ProComm Phone System

# Use DHCP for eth0
interface eth0
"""
            
            # Write to temp location
            with open('/tmp/procomm_network.conf', 'w') as f:
                f.write(config_content)
            
            # Write network type
            with open('/tmp/procomm_network_type.txt', 'w') as f:
                f.write(network_type)
            
            logger.info(f"DHCP configuration saved ({network_type})")
            
            # Check if helper script exists
            script_path = os.path.expanduser("~/ProComm/update_network.sh")
            if not os.path.exists(script_path):
                logger.error(f"Helper script not found: {script_path}")
                QMessageBox.critical(self, "Error", 
                    f"Configuration helper script not found.\n\nPlease ensure {script_path} exists.")
                return
            
            # Apply the configuration using helper script
            result = subprocess.run(['sudo', '-n', script_path], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            
            if result.returncode == 0:
                logger.info("DHCP configuration applied successfully - rebooting...")
                subprocess.Popen(['sudo', 'reboot'])
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "password" in error_msg.lower() or "sudo" in error_msg.lower():
                    logger.error("Sudo not configured for passwordless access")
                    QMessageBox.warning(self, "Configuration Saved", 
                        "Configuration saved to /tmp/procomm_network.conf\n\nSudo access not configured. Please run:\nsudo ~/ProComm/update_network.sh\n\nThen restart the system.")
                else:
                    logger.error(f"Failed to apply configuration: {error_msg}")
                    QMessageBox.warning(self, "Partial Success", 
                        f"Configuration saved but failed to apply:\n{error_msg}\n\nPlease run manually:\nsudo ~/ProComm/update_network.sh")
                
        except subprocess.TimeoutExpired:
            logger.error("Configuration script timed out")
            QMessageBox.critical(self, "Error", "Configuration script timed out. Please check system logs.")
        except FileNotFoundError as e:
            logger.error(f"Command not found: {e}")
            QMessageBox.critical(self, "Error", f"Required command not found: {e}")
        except Exception as e:
            logger.error(f"Failed to configure DHCP: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{e}")
    
    def _configure_static_ip(self, ip, subnet, gateway, dns):
        """Configure network for static IP"""
        try:
            # Basic validation
            if not ip or not gateway or not dns:
                QMessageBox.warning(self, "Validation Error", 
                    "Please fill in all required fields:\n- IP Address\n- Gateway\n- DNS Server")
                return
            
            # Simple IP format validation
            def is_valid_ip(ip_str):
                parts = ip_str.split('.')
                if len(parts) != 4:
                    return False
                try:
                    return all(0 <= int(part) <= 255 for part in parts)
                except ValueError:
                    return False
            
            if not is_valid_ip(ip):
                QMessageBox.warning(self, "Validation Error", f"Invalid IP address: {ip}")
                return
            if not is_valid_ip(gateway):
                QMessageBox.warning(self, "Validation Error", f"Invalid gateway: {gateway}")
                return
            if not is_valid_ip(dns):
                QMessageBox.warning(self, "Validation Error", f"Invalid DNS server: {dns}")
                return
            
            # Convert subnet mask to CIDR notation (e.g., 255.255.255.0 -> /24)
            subnet_cidr_map = {
                '255.255.255.0': '24',
                '255.255.0.0': '16',
                '255.0.0.0': '8',
                '255.255.255.128': '25',
                '255.255.255.192': '26',
                '255.255.255.224': '27',
                '255.255.255.240': '28',
                '255.255.255.248': '29',
                '255.255.255.252': '30'
            }
            cidr = subnet_cidr_map.get(subnet, '24')  # Default to /24 if not found
            
            # Ask for confirmation FIRST
            confirm_dialog = QMessageBox(self)
            confirm_dialog.setWindowTitle("Confirm Network Change")
            confirm_dialog.setText("Apply Static IP Configuration?")
            confirm_dialog.setInformativeText(f"IP: {ip}/{cidr}\nGateway: {gateway}\nDNS: {dns}\n\nSystem will reboot to apply changes.\n\nContinue?")
            confirm_dialog.setIcon(QMessageBox.Question)
            confirm_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            confirm_dialog.setDefaultButton(QMessageBox.Ok)
            
            # Style the dialog
            confirm_dialog.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a1a;
                    min-width: 600px;
                    min-height: 400px;
                }
                QMessageBox QLabel {
                    color: white;
                    font-size: 24pt;
                    padding: 20px;
                    min-width: 500px;
                }
                QPushButton {
                    background-color: #ff6b35;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 22pt;
                    font-weight: bold;
                    padding: 15px 40px;
                    min-width: 180px;
                    min-height: 80px;
                }
                QPushButton:hover {
                    background-color: #ff8c5a;
                }
                QPushButton:default {
                    background-color: #00d4ff;
                }
                QPushButton:default:hover {
                    background-color: #33ddff;
                }
            """)
            
            # If user clicks Cancel, abort
            if confirm_dialog.exec_() != QMessageBox.Ok:
                logger.info("User cancelled static IP configuration")
                return
            
            # User confirmed - proceed with configuration
            # Detect network type
            network_type = self._detect_network_type()
            
            if network_type == 'netplan':
                # Netplan YAML configuration for static IP
                config_content = f"""# ProComm Network Configuration
# Generated by ProComm Phone System
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    eth0:
      dhcp4: false
      dhcp6: false
      addresses:
        - {ip}/{cidr}
      routes:
        - to: default
          via: {gateway}
      nameservers:
        addresses:
          - {dns}
"""
            else:
                # dhcpcd configuration for static IP
                config_content = f"""# Static IP Configuration
# Generated by ProComm Phone System

interface eth0
static ip_address={ip}/{cidr}
static routers={gateway}
static domain_name_servers={dns}
"""
            
            # Write to temp location
            with open('/tmp/procomm_network.conf', 'w') as f:
                f.write(config_content)
            
            # Write network type
            with open('/tmp/procomm_network_type.txt', 'w') as f:
                f.write(network_type)
            
            logger.info(f"Static IP configuration saved ({network_type}): {ip}/{cidr}")
            
            # Check if helper script exists
            script_path = os.path.expanduser("~/ProComm/update_network.sh")
            if not os.path.exists(script_path):
                logger.error(f"Helper script not found: {script_path}")
                QMessageBox.critical(self, "Error", 
                    f"Configuration helper script not found.\n\nPlease ensure {script_path} exists.")
                return
            
            # Apply the configuration using helper script (non-blocking)
            result = subprocess.run(['sudo', '-n', script_path], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            
            if result.returncode == 0:
                logger.info(f"Static IP configuration applied: {ip} - rebooting...")
                subprocess.Popen(['sudo', 'reboot'])
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "password" in error_msg.lower() or "sudo" in error_msg.lower():
                    logger.error("Sudo not configured for passwordless access")
                    QMessageBox.warning(self, "Configuration Saved", 
                        f"Configuration saved to /tmp/procomm_network.conf\n\nIP: {ip}/{cidr}\nGateway: {gateway}\nDNS: {dns}\n\nSudo access not configured. Please run:\nsudo ~/ProComm/update_network.sh\n\nThen restart the system.")
                else:
                    logger.error(f"Failed to apply configuration: {error_msg}")
                    QMessageBox.warning(self, "Partial Success", 
                        f"Configuration saved but failed to apply:\n{error_msg}\n\nPlease run manually:\nsudo ~/ProComm/update_network.sh")
                
        except subprocess.TimeoutExpired:
            logger.error("Configuration script timed out")
            QMessageBox.critical(self, "Error", "Configuration script timed out. Please check system logs.")
        except FileNotFoundError as e:
            logger.error(f"Command not found: {e}")
            QMessageBox.critical(self, "Error", f"Required command not found: {e}")
        except Exception as e:
            logger.error(f"Failed to configure static IP: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{e}")
    
    
    
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
    
    def closeEvent(self, event):
        """Handle window close"""
        self.update_timer.stop()
        self.cursor_hide_timer.stop()
        QCoreApplication.instance().removeEventFilter(self)
        event.accept()
