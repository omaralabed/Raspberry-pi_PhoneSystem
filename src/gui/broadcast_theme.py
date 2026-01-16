#!/usr/bin/env python3
"""
Broadcast Professional Theme
Colors and styles matching professional broadcast equipment
"""

# Professional Broadcast Color Scheme
COLORS = {
    # Backgrounds
    'bg_primary': '#1a1a1a',      # Main dark background
    'bg_secondary': '#2a2a2a',    # Panel backgrounds
    'bg_panel': '#2d2420',        # Table/list rows
    'bg_highlight': '#3a3a3a',    # Hover states
    
    # Text
    'text_primary': '#ff6b35',    # Orange - main text (like broadcast labels)
    'text_secondary': '#ff8c42',  # Lighter orange
    'text_white': '#ffffff',      # White text
    'text_muted': '#999999',      # Dimmed text
    
    # Status indicators
    'status_active': '#22c55e',   # Green - ON AIR / Connected
    'status_warning': '#fbbf24',  # Yellow - Warning
    'status_error': '#ef4444',    # Red - Error / Offline
    'status_info': '#0ea5e9',     # Blue - Info / Selected
    
    # Accents
    'accent_blue': '#0ea5e9',     # Active selection
    'accent_orange': '#ff6b35',   # Primary accent
    'border': '#404040',          # Subtle borders
}

# Global stylesheet for broadcast theme
BROADCAST_STYLE = f"""
    QMainWindow {{
        background-color: {COLORS['bg_primary']};
    }}
    
    QWidget {{
        background-color: transparent;
        color: {COLORS['text_white']};
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    
    QLabel {{
        color: {COLORS['text_white']};
    }}
    
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
    }}
    
    QPushButton {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_white']};
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 12pt;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['bg_highlight']};
        border-color: {COLORS['accent_orange']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['bg_primary']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_muted']};
        border-color: {COLORS['border']};
    }}
    
    QLineEdit, QSpinBox {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['accent_orange']};
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 6px 12px;
        font-size: 14pt;
        font-weight: bold;
    }}
    
    QLineEdit:focus, QSpinBox:focus {{
        border-color: {COLORS['accent_blue']};
    }}
    
    QComboBox {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_white']};
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 11pt;
        font-weight: bold;
    }}
    
    QComboBox:hover {{
        border-color: {COLORS['accent_orange']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_white']};
        selection-background-color: {COLORS['accent_blue']};
        selection-color: {COLORS['text_white']};
        border: 2px solid {COLORS['border']};
    }}
    
    QScrollBar:vertical {{
        background: {COLORS['bg_primary']};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS['accent_orange']};
        border-radius: 6px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['text_secondary']};
    }}
"""
