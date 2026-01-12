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
from PyQt5.QtCore import QThread, pyqtSignal, Qt

from src.sip_engine import SIPEngine
from src.audio_router import AudioRouter
from src.gui.main_window import MainWindow

# Setup logging
# Create logs directory first
os.makedirs('logs', exist_ok=True)

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
        
        # Initialize Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Phone System")
        
        # Enable mouse cursor
        self.app.setOverrideCursor(Qt.ArrowCursor)
        self.app.restoreOverrideCursor()  # Reset to default
        
        # Initialize components
        self.sip_engine = None
        self.audio_router = None
        self.main_window = None
        
        # Setup signal handlers for clean shutdown using Qt's approach
        # This is async-signal-safe - just sets a flag that Qt event loop checks
        signal.signal(signal.SIGINT, lambda sig, frame: self.app.quit())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.app.quit())
    
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
                self.audio_router = None
                return False
            
            # Initialize SIP engine
            logger.info("Initializing SIP engine...")
            self.sip_engine = SIPEngine()
            
            # Load SIP configuration
            if not self.sip_engine.load_config():
                logger.error("Failed to load SIP configuration")
                self._show_error("SIP Configuration Error",
                               "Failed to load SIP configuration. Check config/sip_config.json exists and is valid.")
                self._cleanup_on_init_failure()
                return False
            
            # Start SIP engine
            if not self.sip_engine.start():
                logger.error("Failed to start SIP engine")
                self._show_error("SIP Engine Error",
                               "Failed to initialize SIP system. Check SIP configuration and network connectivity.")
                self._cleanup_on_init_failure()
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
            self._cleanup_on_init_failure()
            return False
    
    def _cleanup_on_init_failure(self):
        """Clean up partially initialized resources"""
        try:
            if self.sip_engine:
                logger.info("Cleaning up SIP engine...")
                self.sip_engine.shutdown()
                self.sip_engine = None
        except Exception as e:
            logger.error(f"Error cleaning up SIP engine: {e}")
        
        try:
            if self.audio_router:
                logger.info("Cleaning up audio router...")
                self.audio_router.stop()
                self.audio_router = None
        except Exception as e:
            logger.error(f"Error cleaning up audio router: {e}")
    
    def _on_make_call(self, line_id: int, phone_number: str):
        """
        Handle make call request
        
        Args:
            line_id: Line number (1-8)
            phone_number: Destination number
        """
        try:
            logger.info(f"Making call on line {line_id} to {phone_number}")
            
            success = self.sip_engine.make_call(line_id, phone_number)
            
            if not success:
                logger.error(f"Failed to make call on line {line_id}")
                self._show_warning("Call Failed", 
                                 f"Could not place call on Line {line_id}")
        except Exception as e:
            logger.error(f"Exception in _on_make_call: {e}", exc_info=True)
            self._show_error("Call Error", f"Error placing call: {e}")
    
    def _on_hangup(self, line_id: int):
        """
        Handle hangup request
        
        Args:
            line_id: Line number (1-8)
        """
        try:
            logger.info(f"Hanging up line {line_id}")
            self.sip_engine.hangup_call(line_id)
        except Exception as e:
            logger.error(f"Exception in _on_hangup: {e}", exc_info=True)
    
    def _on_route_audio(self, line_id: int, channel: int):
        """
        Handle audio routing change
        
        Args:
            line_id: Line number (1-8)
            channel: Output channel (1-8)
        """
        try:
            logger.info(f"Routing line {line_id} audio to Output {channel}")
            self.audio_router.update_routing(line_id, channel)
        except Exception as e:
            logger.error(f"Exception in _on_route_audio: {e}", exc_info=True)
    
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
        try:
            if not self.initialize():
                self.shutdown()  # Cleanup any partially initialized components
                return 1
            
            # Show main window
            self.main_window.showFullScreen()  # Fullscreen for touchscreen
            logger.info("Application running")
            
            # Run Qt event loop
            exit_code = self.app.exec_()
            
            # Cleanup
            self.shutdown()
            
            return exit_code
        except Exception as e:
            logger.error(f"Fatal error in run(): {e}", exc_info=True)
            self.shutdown()
            return 1
    
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
