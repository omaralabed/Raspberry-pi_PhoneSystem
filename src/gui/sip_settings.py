#!/usr/bin/env python3
"""
SIP Settings Dialog - Configure SIP Provider Credentials
"""

import json
import os
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox, 
                             QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class VirtualKeyboard(QWidget):
    """On-screen keyboard for touchscreen input"""
    
    key_pressed = pyqtSignal(str)
    close_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        from PyQt5.QtWidgets import QWidget
        super().__init__(parent)
        self.shift_active = False
        self.setFixedHeight(310)
        self._create_ui()
    
    def _create_ui(self):
        """Create keyboard layout"""
        grid = QGridLayout(self)
        grid.setSpacing(8)
        grid.setContentsMargins(15, 12, 15, 12)
        
        self.setStyleSheet("QWidget { background-color: #18181b; border-radius: 12px; }")
        
        key_style = "QPushButton { background-color: #3f3f46; color: white; border: none; border-radius: 8px; font-size: 20px; } QPushButton:pressed { background-color: #52525b; }"
        
        rows = [
            ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
            ['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
            ['u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3'],
            ['4', '5', '6', '7', '8', '9', '+', '-', '.', '@']
        ]
        
        self.key_buttons = {}
        
        for row_idx, row in enumerate(rows):
            for col_idx, key in enumerate(row):
                btn = QPushButton(key)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.setFixedHeight(48)
                btn.setStyleSheet(key_style)
                btn.clicked.connect(lambda checked, k=key: self._on_key_click(k))
                grid.addWidget(btn, row_idx, col_idx)
                self.key_buttons[key] = btn
        
        # Bottom row buttons
        abc_btn = QPushButton('abc')
        abc_btn.setFocusPolicy(Qt.NoFocus)
        abc_btn.setFixedHeight(52)
        abc_btn.setCheckable(True)
        abc_btn.setStyleSheet(key_style)
        abc_btn.clicked.connect(lambda: self._on_key_click('ABC'))
        grid.addWidget(abc_btn, 4, 0, 1, 2)
        self.key_buttons['ABC'] = abc_btn
        
        space_btn = QPushButton('Space')
        space_btn.setFocusPolicy(Qt.NoFocus)
        space_btn.setFixedHeight(52)
        space_btn.setStyleSheet(key_style)
        space_btn.clicked.connect(lambda: self._on_key_click('SPACE'))
        grid.addWidget(space_btn, 4, 2, 1, 4)
        
        delete_btn = QPushButton('Delete')
        delete_btn.setFocusPolicy(Qt.NoFocus)
        delete_btn.setFixedHeight(52)
        delete_btn.setStyleSheet("QPushButton { background-color: #f97316; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; } QPushButton:pressed { background-color: #ea580c; }")
        delete_btn.clicked.connect(lambda: self._on_key_click('DEL'))
        grid.addWidget(delete_btn, 4, 6, 1, 2)
        
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
    """Dialog for configuring SIP provider credentials"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIP Provider Settings")
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(850)
        
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
        self.server_input.setPlaceholderText("e.g., sip.vonage.com, sip.twilio.com")
        self.server_input.installEventFilter(self)
        self.input_fields.append(self.server_input)
        form_layout.addRow("SIP Server:", self.server_input)
        
        # SIP Port
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
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                selection-background-color: #00d4ff;
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
        layout.addSpacing(15)
        
        # Info label
        info = QLabel("Tap a field to show keyboard • Changes require system restart")
        info.setStyleSheet("color: #ffa500; font-size: 11px; font-weight: normal;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addSpacing(10)
        
        # Virtual Keyboard
        self.keyboard = VirtualKeyboard(self)
        self.keyboard.key_pressed.connect(self._on_keyboard_key)
        self.keyboard.close_requested.connect(self._hide_keyboard)
        self.keyboard.hide()
        layout.addWidget(self.keyboard)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFocusPolicy(Qt.NoFocus)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFocusPolicy(Qt.NoFocus)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def showEvent(self, event):
        """Handle dialog show"""
        super().showEvent(event)
        self.keyboard.hide()
        self.active_input = None
    
    def _hide_keyboard(self):
        """Hide virtual keyboard"""
        self.keyboard.hide()
        if self.active_input:
            self.active_input.clearFocus()
    
    def _show_keyboard(self):
        """Show virtual keyboard"""
        self.keyboard.show()
    
    def eventFilter(self, obj, event):
        """Handle focus events"""
        if event.type() == QEvent.FocusIn and isinstance(obj, QLineEdit):
            self.active_input = obj
            obj.setStyleSheet("QLineEdit { background-color: #2d3748; color: white; border: 2px solid #00d4ff; border-radius: 6px; padding: 8px; font-size: 13px; min-height: 35px; }")
            self._show_keyboard()
        elif event.type() == QEvent.FocusOut and isinstance(obj, QLineEdit):
            obj.setStyleSheet("QLineEdit { background-color: #2d3748; color: white; border: 2px solid rgba(0, 212, 255, 0.3); border-radius: 6px; padding: 8px; font-size: 13px; min-height: 35px; }")
            QTimer.singleShot(200, self._check_hide_keyboard)
        return super().eventFilter(obj, event)
    
    def _check_hide_keyboard(self):
        """Check if keyboard should be hidden"""
        for field in self.input_fields:
            if field.hasFocus():
                return
        self._hide_keyboard()
    
    def _on_keyboard_key(self, key):
        """Handle keyboard key press"""
        if not self.active_input:
            return
        
        if key == '\b':
            self.active_input.backspace()
        elif key == '\n':
            self._hide_keyboard()
        else:
            self.active_input.insert(key)
    
    def save_settings(self):
        """Save settings to config file"""
        try:
            # Update config
            self.config["sip_server"] = self.server_input.text()
            
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
