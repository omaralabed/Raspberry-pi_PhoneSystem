#!/usr/bin/env python3
"""
Audio Widget - Audio Routing Controls
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class AudioWidget(QWidget):
    """
    Audio routing controls and status display
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
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(5)
        
        # Info label
        info_label = QLabel("Click 🔊 on any line\nto toggle IFB/PL")
        info_label.setFont(QFont("Arial", 9))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        group_layout.addWidget(info_label)
        
        # IFB indicator
        ifb_frame = QFrame()
        ifb_frame.setFrameStyle(QFrame.Box)
        ifb_frame.setStyleSheet("background-color: #1a3a5a; border: 1px solid #4a7aaa;")
        ifb_layout = QVBoxLayout(ifb_frame)
        ifb_layout.setContentsMargins(5, 5, 5, 5)
        
        ifb_title = QLabel("🎧 IFB (Talent)")
        ifb_title.setFont(QFont("Arial", 10, QFont.Bold))
        ifb_title.setStyleSheet("color: #4af;")
        ifb_layout.addWidget(ifb_title)
        
        ifb_desc = QLabel("Interruptible Foldback\nChannels 1-2 (L/R)")
        ifb_desc.setFont(QFont("Arial", 8))
        ifb_desc.setAlignment(Qt.AlignLeft)
        ifb_layout.addWidget(ifb_desc)
        
        group_layout.addWidget(ifb_frame)
        
        # PL indicator
        pl_frame = QFrame()
        pl_frame.setFrameStyle(QFrame.Box)
        pl_frame.setStyleSheet("background-color: #5a3a1a; border: 1px solid #aa7a4a;")
        pl_layout = QVBoxLayout(pl_frame)
        pl_layout.setContentsMargins(5, 5, 5, 5)
        
        pl_title = QLabel("📻 PL (Crew)")
        pl_title.setFont(QFont("Arial", 10, QFont.Bold))
        pl_title.setStyleSheet("color: #fa4;")
        pl_layout.addWidget(pl_title)
        
        pl_desc = QLabel("Private Line\nChannels 3-4 (L/R)")
        pl_desc.setFont(QFont("Arial", 8))
        pl_desc.setAlignment(Qt.AlignLeft)
        pl_layout.addWidget(pl_desc)
        
        group_layout.addWidget(pl_frame)
        
        # Test buttons
        test_layout = QHBoxLayout()
        test_layout.setSpacing(5)
        
        self.test_ifb_btn = QPushButton("Test IFB")
        self.test_ifb_btn.setFont(QFont("Arial", 9))
        self.test_ifb_btn.clicked.connect(self._on_test_ifb)
        self.test_ifb_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a4a6a;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #1a3a5a;
            }
        """)
        test_layout.addWidget(self.test_ifb_btn)
        
        self.test_pl_btn = QPushButton("Test PL")
        self.test_pl_btn.setFont(QFont("Arial", 9))
        self.test_pl_btn.clicked.connect(self._on_test_pl)
        self.test_pl_btn.setStyleSheet("""
            QPushButton {
                background-color: #6a4a2a;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #5a3a1a;
            }
        """)
        test_layout.addWidget(self.test_pl_btn)
        
        group_layout.addLayout(test_layout)
        
        layout.addWidget(group)
    
    def _on_test_ifb(self):
        """Test IFB output"""
        logger.info("Testing IFB output")
        from ..phone_line import AudioOutput
        self.audio_router.test_audio(AudioOutput.IFB, duration=1.0)
    
    def _on_test_pl(self):
        """Test PL output"""
        logger.info("Testing PL output")
        from ..phone_line import AudioOutput
        self.audio_router.test_audio(AudioOutput.PL, duration=1.0)
