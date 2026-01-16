#!/usr/bin/env python3
"""
SIP Settings Dialog - Configure SIP Provider Credentials
"""

import json
import os
import logging
from PyQt5.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox, 
                             QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class VirtualKeyboard(QWidget):
    """Simple on-screen keyboard"""
    
    key_pressed = pyqtSignal(str)
    close_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shift_active = False
        self.setFixedHeight(180)
        self._create_ui()
    
    def _create_ui(self):
        """Create compact keyboard"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.setStyleSheet("background-color: #1e293b; border-radius: 8px;")
        
        btn_style = """
            QPushButton {
                background-color: #475569;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                min-width: 30px;
            }
            QPushButton:pressed { background-color: #64748b; }
        """
        
        self.key_buttons = {}
        
        # Row 1: 1234567890
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        for key in ['1','2','3','4','5','6','7','8','9','0']:
            btn = QPushButton(key)
            btn.setFixedHeight(28)
            btn.setStyleSheet(btn_style)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda ch, k=key: self.key_pressed.emit(k))
            row1.addWidget(btn)
            self.key_buttons[key] = btn
        layout.addLayout(row1)
        
        # Row 2: qwertyuiop
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        for key in ['q','w','e','r','t','y','u','i','o','p']:
            btn = QPushButton(key)
            btn.setFixedHeight(28)
            btn.setStyleSheet(btn_style)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda ch, k=key: self._type_key(k))
            row2.addWidget(btn)
            self.key_buttons[key] = btn
        layout.addLayout(row2)
        
        # Row 3: asdfghjkl
        row3 = QHBoxLayout()
        row3.setSpacing(4)
        for key in ['a','s','d','f','g','h','j','k','l']:
            btn = QPushButton(key)
            btn.setFixedHeight(28)
            btn.setStyleSheet(btn_style)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda ch, k=key: self._type_key(k))
            row3.addWidget(btn)
            self.key_buttons[key] = btn
        layout.addLayout(row3)
        
        # Row 4: shift zxcvbnm backspace
        row4 = QHBoxLayout()
        row4.setSpacing(4)
        
        shift = QPushButton('⇧')
        shift.setFixedHeight(28)
        shift.setFixedWidth(50)
        shift.setCheckable(True)
        shift.setStyleSheet(btn_style)
        shift.setFocusPolicy(Qt.NoFocus)
        shift.clicked.connect(self._toggle_shift)
        row4.addWidget(shift)
        self.key_buttons['shift'] = shift
        
        for key in ['z','x','c','v','b','n','m']:
            btn = QPushButton(key)
            btn.setFixedHeight(28)
            btn.setStyleSheet(btn_style)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda ch, k=key: self._type_key(k))
            row4.addWidget(btn)
            self.key_buttons[key] = btn
        
        backsp = QPushButton('⌫')
        backsp.setFixedHeight(28)
        backsp.setFixedWidth(50)
        backsp.setStyleSheet("QPushButton { background-color: #dc2626; color: white; border: none; border-radius: 4px; font-size: 16px; } QPushButton:pressed { background-color: #b91c1c; }")
        backsp.setFocusPolicy(Qt.NoFocus)
        backsp.clicked.connect(lambda: self.key_pressed.emit('\b'))
        row4.addWidget(backsp)
        layout.addLayout(row4)
        
        # Row 5: @./ space . done
        row5 = QHBoxLayout()
        row5.setSpacing(4)
        
        special = QPushButton('@')
        special.setFixedHeight(28)
        special.setFixedWidth(40)
        special.setStyleSheet(btn_style)
        special.setFocusPolicy(Qt.NoFocus)
        special.clicked.connect(lambda: self.key_pressed.emit('@'))
        row5.addWidget(special)
        
        space = QPushButton('Space')
        space.setFixedHeight(28)
        space.setStyleSheet(btn_style)
        space.setFocusPolicy(Qt.NoFocus)
        space.clicked.connect(lambda: self.key_pressed.emit(' '))
        row5.addWidget(space, 1)
        
        dot = QPushButton('.')
        dot.setFixedHeight(28)
        dot.setFixedWidth(40)
        dot.setStyleSheet(btn_style)
        dot.setFocusPolicy(Qt.NoFocus)
        dot.clicked.connect(lambda: self.key_pressed.emit('.'))
        row5.addWidget(dot)
        
        done = QPushButton('Done')
        done.setFixedHeight(28)
        done.setFixedWidth(60)
        done.setStyleSheet("QPushButton { background-color: #16a34a; color: white; border: none; border-radius: 4px; font-weight: bold; } QPushButton:pressed { background-color: #15803d; }")
        done.setFocusPolicy(Qt.NoFocus)
        done.clicked.connect(self.close_requested.emit)
        row5.addWidget(done)
        layout.addLayout(row5)
    
    def _type_key(self, key):
        char = key.upper() if self.shift_active else key
        self.key_pressed.emit(char)
        if self.shift_active:
            self.shift_active = False
            self.key_buttons['shift'].setChecked(False)
            self._update_labels()
    
    def _toggle_shift(self):
        self.shift_active = self.key_buttons['shift'].isChecked()
        self._update_labels()
    
    def _update_labels(self):
        for key in 'qwertyuiopasdfghjklzxcvbnm':
            if key in self.key_buttons:
                self.key_buttons[key].setText(key.upper() if self.shift_active else key)


class SIPSettingsDialog(QDialog):
    """Dialog for configuring SIP provider credentials"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIP Settings")
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(850)  # Increased for keyboard + buttons
        
        self.active_input = None
        
        # Get config path
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(script_dir, "config", "sip_config.json")
        self.load_config()
        
        self._apply_theme()
        self._create_ui()
    
    def _apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
            }
            QLabel {
                color: #eaeaea;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #2d3748;
                color: white;
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                min-height: 35px;
            }
            QLineEdit:focus {
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
    
    def load_config(self):
        """Load current SIP configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load SIP config: {e}")
            self.config = {
                "sip_server": "sip.twilio.com",
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
