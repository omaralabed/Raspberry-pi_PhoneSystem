#!/usr/bin/env python3
"""
Audio Router - PulseAudio Management
Routes each phone line audio to IFB or PL outputs
"""

import json
import logging
from typing import Dict, Optional, List
import sounddevice as sd
import numpy as np
import threading
import queue

from .phone_line import PhoneLine, AudioOutput

logger = logging.getLogger(__name__)


class AudioRouter:
    """
    Manages audio routing for 8 phone lines to IFB/PL outputs
    """
    
    def __init__(self, config_path: str = "config/audio_config.json"):
        """
        Initialize audio router
        
        Args:
            config_path: Path to audio configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Audio device configuration
        self.device_name = self.config.get("audio_device_name")
        self.device_index = self.config.get("audio_device_index")
        self.sample_rate = self.config.get("sample_rate", 48000)
        self.buffer_size = self.config.get("buffer_size", 256)
        
        # Number of output channels (up to 8)
        self.num_outputs = self.config.get("num_outputs", 8)
        
        # Audio routing map: line_id -> output channel
        self.routing_map: Dict[int, int] = {}
        
        # Audio streams for each line
        self.streams: Dict[int, object] = {}
        self.audio_queues: Dict[int, queue.Queue] = {}
        
        # State
        self.is_running = False
        self.lock = threading.Lock()
        
        logger.info(f"Audio router initialized: {self.device_name}")
        logger.info(f"Available outputs: 1-{self.num_outputs}")
    
    def _load_config(self) -> Dict:
        """Load audio configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded audio config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load audio config: {e}")
            raise
    
    def start(self) -> bool:
        """
        Start audio routing system
        
        Returns:
            True if started successfully
        """
        try:
            # Find audio device
            if self.device_index is None:
                self.device_index = self._find_device()
            
            if self.device_index is None:
                logger.error("Audio device not found")
                return False
            
            # Verify device has enough output channels
            device_info = sd.query_devices(self.device_index)
            max_outputs = device_info['max_output_channels']
            
            if max_outputs < self.num_outputs:
                logger.warning(f"Device has {max_outputs} outputs, configured for {self.num_outputs}")
                self.num_outputs = min(self.num_outputs, max_outputs)
            
            self.is_running = True
            logger.info(f"Audio router started on device: {device_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio router: {e}")
            return False
    
    def stop(self) -> None:
        """Stop audio routing system"""
        with self.lock:
            if not self.is_running:
                return
            
            logger.info("Stopping audio router...")
            
            # Stop all streams
            for line_id, stream in list(self.streams.items()):
                try:
                    stream.stop()
                    stream.close()
                except:
                    pass
            
            self.streams.clear()
            self.audio_queues.clear()
            self.is_running = False
            
            logger.info("Audio router stopped")
    
    def _find_device(self) -> Optional[int]:
        """Find audio device by name"""
        # If no device name configured, use default
        if not self.device_name:
            logger.info("No audio device name configured, using default")
            return sd.default.device[1]  # Default output device
        
        devices = sd.query_devices()
        
        for idx, device in enumerate(devices):
            if self.device_name.lower() in device['name'].lower():
                logger.info(f"Found audio device: {device['name']} (index={idx})")
                return idx
        
        logger.warning(f"Device '{self.device_name}' not found, using default")
        return sd.default.device[1]  # Default output device
    
    def route_line(self, line: PhoneLine) -> bool:
        """
        Set up audio routing for a phone line
        
        Args:
            line: PhoneLine object with audio_output setting
            
        Returns:
            True if routing configured successfully
        """
        if not self.is_running:
            logger.error("Audio router not running")
            return False
        
        with self.lock:
            # Get output channel from line
            channel = line.audio_output.channel
            
            # Channel 0 means no output (valid but no routing needed)
            if channel == 0:
                logger.info(f"Line {line.line_id}: No output assigned")
                self.routing_map[line.line_id] = 0
                return True
            
            if channel > self.num_outputs:
                logger.error(f"Line {line.line_id}: Channel {channel} exceeds available outputs ({self.num_outputs})")
                return False
            
            self.routing_map[line.line_id] = channel
            
            logger.info(f"Line {line.line_id}: Routed to Output {channel}")
            return True
    
    def update_routing(self, line_id: int, channel: int) -> bool:
        """
        Update audio routing for an active line
        
        Args:
            line_id: Line number (1-8)
            channel: Output channel (0=no output, 1-8=physical outputs)
            
        Returns:
            True if routing updated successfully
        """
        if not self.is_running:
            return False
        
        if not 1 <= line_id <= 8:
            logger.error(f"Invalid line_id {line_id}, must be 1-8")
            return False
        
        if not 0 <= channel <= self.num_outputs:
            logger.error(f"Invalid channel {channel}, must be 0-{self.num_outputs}")
            return False
        
        with self.lock:
            self.routing_map[line_id] = channel
            
            if channel == 0:
                logger.info(f"Line {line_id}: Audio routing disabled (no output)")
            else:
                logger.info(f"Line {line_id}: Audio routing updated to Output {channel}")
            return True
    
    def get_routing(self, line_id: int) -> Optional[int]:
        """
        Get current audio routing for a line
        
        Args:
            line_id: Line number
            
        Returns:
            Current output channel or None
        """
        return self.routing_map.get(line_id)
    
    def list_audio_devices(self) -> List[Dict]:
        """
        List all available audio devices
        
        Returns:
            List of device info dictionaries
        """
        devices = []
        for idx, device in enumerate(sd.query_devices()):
            if device['max_output_channels'] >= 2:  # Need at least stereo
                devices.append({
                    'index': idx,
                    'name': device['name'],
                    'outputs': device['max_output_channels'],
                    'sample_rate': device['default_samplerate']
                })
        return devices
    
    def test_audio(self, channel: int, duration: float = 1.0) -> bool:
        """
        Play test tone on specified output channel
        
        Args:
            channel: Output channel (1-8) to test
            duration: Test tone duration in seconds
            
        Returns:
            True if test successful
        """
        if not self.is_running:
            logger.error("Audio router not running")
            return False
        
        if not 1 <= channel <= self.num_outputs:
            logger.error(f"Invalid channel {channel}, must be 1-{self.num_outputs}")
            return False
        
        try:
            # Generate test tone (1 kHz sine wave)
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            tone = np.sin(2 * np.pi * 1000 * t) * 0.3  # 30% volume
            
            # Create multi-channel output
            num_device_channels = sd.query_devices(self.device_index)['max_output_channels']
            audio_data = np.zeros((len(tone), num_device_channels))
            
            # Assign tone to selected channel (channel-1 for 0-based index)
            audio_data[:, channel - 1] = tone
            
            # Play
            logger.info(f"Playing test tone on Output {channel}")
            sd.play(audio_data, self.sample_rate, device=self.device_index)
            sd.wait()
            
            logger.info("Test tone completed")
            return True
            
        except Exception as e:
            logger.error(f"Audio test failed: {e}")
            return False
    
    def get_status(self) -> Dict:
        """
        Get audio router status
        
        Returns:
            Status dictionary
        """
        device_info = sd.query_devices(self.device_index) if self.device_index else {}
        
        return {
            'running': self.is_running,
            'device': device_info.get('name', 'Unknown'),
            'device_index': self.device_index,
            'sample_rate': self.sample_rate,
            'num_outputs': self.num_outputs,
            'active_routes': len(self.routing_map)
        }
