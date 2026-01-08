#!/usr/bin/env python3
"""
Raspberry Pi Phone System - Main Application
IFB/PL Communication System for Production Environments
"""

import sys
import os
import logging
import signal
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

from src.sip_engine import SIPEngine
from src.audio_router import AudioRouter
from src.phone_line import AudioOutput
from src.gui.main_window import MainWindow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/phone_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class PhoneSystemApp:
    """
    Main phone system application
    """
    
    def __init__(self):
        """Initialize phone system"""
        logger.info("="*60)
        logger.info("Phone System Starting")
        logger.info("="*60)
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Initialize Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Phone System")
        
        # Initialize components
        self.sip_engine = None
        self.audio_router = None
        self.main_window = None
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def initialize(self) -> bool:
        """
        Initialize all system components
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize audio router
            logger.info("Initializing audio router...")
            self.audio_router = AudioRouter()
            if not self.audio_router.start():
                logger.error("Failed to start audio router")
                self._show_error("Audio Router Error", 
                               "Failed to initialize audio system. Check audio device configuration.")
                return False
            
            # Initialize SIP engine
            logger.info("Initializing SIP engine...")
            self.sip_engine = SIPEngine()
            if not self.sip_engine.start():
                logger.error("Failed to start SIP engine")
                self._show_error("SIP Engine Error",
                               "Failed to initialize SIP system. Check SIP configuration.")
                return False
            
            # Setup audio routing for all lines
            for line in self.sip_engine.lines:
                self.audio_router.route_line(line)
            
            # Create main window
            logger.info("Creating main window...")
            self.main_window = MainWindow(self.sip_engine, self.audio_router)
            
            # Connect signals
            self.main_window.make_call_signal.connect(self._on_make_call)
            self.main_window.hangup_signal.connect(self._on_hangup)
            self.main_window.route_audio_signal.connect(self._on_route_audio)
            
            logger.info("System initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            self._show_error("Initialization Error", str(e))
            return False
    
    def _on_make_call(self, line_id: int, phone_number: str):
        """
        Handle make call request
        
        Args:
            line_id: Line number (1-8)
            phone_number: Destination number
        """
        logger.info(f"Making call on line {line_id} to {phone_number}")
        
        success = self.sip_engine.make_call(line_id, phone_number)
        
        if not success:
            logger.error(f"Failed to make call on line {line_id}")
            self._show_warning("Call Failed", 
                             f"Could not place call on Line {line_id}")
    
    def _on_hangup(self, line_id: int):
        """
        Handle hangup request
        
        Args:
            line_id: Line number (1-8)
        """
        logger.info(f"Hanging up line {line_id}")
        self.sip_engine.hangup_call(line_id)
    
    def _on_route_audio(self, line_id: int, output: str):
        """
        Handle audio routing change
        
        Args:
            line_id: Line number (1-8)
            output: "IFB" or "PL"
        """
        logger.info(f"Routing line {line_id} audio to {output}")
        
        audio_output = AudioOutput.IFB if output == "IFB" else AudioOutput.PL
        self.audio_router.update_routing(line_id, audio_output)
    
    def _show_error(self, title: str, message: str):
        """Show error dialog"""
        QMessageBox.critical(None, title, message)
    
    def _show_warning(self, title: str, message: str):
        """Show warning dialog"""
        QMessageBox.warning(None, title, message)
    
    def run(self) -> int:
        """
        Run the application
        
        Returns:
            Exit code
        """
        if not self.initialize():
            return 1
        
        # Show main window
        self.main_window.showFullScreen()  # Fullscreen for touchscreen
        logger.info("Application running")
        
        # Run Qt event loop
        exit_code = self.app.exec_()
        
        # Cleanup
        self.shutdown()
        
        return exit_code
    
    def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down...")
        
        if self.sip_engine:
            logger.info("Stopping SIP engine...")
            self.sip_engine.stop()
        
        if self.audio_router:
            logger.info("Stopping audio router...")
            self.audio_router.stop()
        
        logger.info("Shutdown complete")


def main():
    """Main entry point"""
    app = PhoneSystemApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
