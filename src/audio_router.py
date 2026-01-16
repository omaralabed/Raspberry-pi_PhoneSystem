#!/usr/bin/env python3
"""
Audio Router - PulseAudio Management
Routes each phone line audio to IFB or PL outputs
"""

import json
import logging
from typing import Dict, Optional, List
import sounddevice as sd
import threading
import numpy as np
import queue
import subprocess
import signal
import os

from .phone_line import PhoneLine, AudioOutput

logger = logging.getLogger(__name__)


def _tone_generator_process(device_index, device_name, channel, sample_rate, device_channels):
    """
    Standalone function to generate test tone in a separate process.
    This runs in its own process with its own memory space, completely isolated from the main GUI.
    """
    import sounddevice as sd
    import numpy as np
    import time
    import sys
    
    def callback(outdata, frames, time_info, status):
        if status:
            print(f'Audio status: {status}', file=sys.stderr, flush=True)
        t = np.linspace(0, frames / sample_rate, frames)
        tone = np.sin(2 * np.pi * 1000 * t) * 0.3  # 1kHz at 30% volume
        outdata.fill(0)
        outdata[:, channel - 1] = tone[:, np.newaxis]
    
    try:
        device = device_index if device_index is not None else device_name
        print(f'Starting tone on device={device}, channel={channel}', flush=True)
        
        stream = sd.OutputStream(
            device=device,
            channels=device_channels,
            callback=callback,
            samplerate=sample_rate,
            blocksize=256
        )
        stream.start()
        print(f'Tone playing on channel {channel}', flush=True)
        
        # Keep the process alive
        while True:
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Tone process error: {e}', file=sys.stderr, flush=True)
        sys.exit(1)


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
        self.device_channels = None  # Cache device channel count
        
        # Audio routing map: line_id -> output channel
        self.routing_map: Dict[int, int] = {}
        
        # Audio streams for each line
        self.streams: Dict[int, object] = {}
        self.audio_queues: Dict[int, queue.Queue] = {}
        
        # Test tone state
        self.test_tone_active = False
        self.test_tone_channel = None
        self.test_tone_stream = None
        self.test_tone_process = None  # Subprocess for tone generation
        
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
            # Don't actually query the device here to avoid locking it
            # The test tone child process will access the device independently
            
            # Just validate configuration
            if self.device_index is None and not self.device_name:
                logger.error("No audio device configured")
                return False
            
            # Assume configuration is correct - don't query device
            self.device_channels = self.num_outputs  # Use configured value
            
            self.is_running = True
            logger.info(f"Audio router started with device: {self.device_name or self.device_index}")
            logger.info(f"Device queries skipped to avoid hardware locking")
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
                except Exception:
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
            try:
                default_device = sd.default.device
                if default_device and len(default_device) > 1:
                    return default_device[1]  # Default output device
            except (TypeError, IndexError, AttributeError):
                logger.error("No default audio output device available")
                return None
            return None
        
        devices = sd.query_devices()
        
        for idx, device in enumerate(devices):
            if self.device_name.lower() in device['name'].lower():
                logger.info(f"Found audio device: {device['name']} (index={idx})")
                return idx
        
        logger.warning(f"Device '{self.device_name}' not found, using default")
        try:
            default_device = sd.default.device
            if default_device and len(default_device) > 1:
                return default_device[1]  # Default output device
        except (TypeError, IndexError, AttributeError):
            logger.error("No default audio output device available")
            return None
        return None
    
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
    
    def start_continuous_tone(self, channel: int) -> bool:
        """
        Start continuous test tone on specified output channel (truly non-blocking)
        
        Args:
            channel: Output channel (1-8) to test
            
        Returns:
            True (always returns immediately, actual tone starts asynchronously)
        """
        logger.info(f"[ENTRY] start_continuous_tone called for channel {channel}")
        
        # Validate outside lock first
        if not self.is_running:
            logger.error("Audio router not running")
            return False
        
        logger.info(f"[CHECK1] is_running passed")
        
        if not 1 <= channel <= self.num_outputs:
            logger.error(f"Invalid channel {channel}, must be 1-{self.num_outputs}")
            return False
        
        logger.info(f"[CHECK2] channel validation passed")
        
        # Launch subprocess in a daemon thread so THIS function returns immediately
        def start_in_thread():
            import sys
            try:
                print(f"[SPAWN_THREAD] Started for channel {channel}", file=sys.stderr, flush=True)
                logger.info(f"[THREAD] start_in_thread started for channel {channel}")
                
                # Stop any existing tone first (inside thread, blocking is OK)
                try:
                    old_proc = None
                    with self.lock:
                        if self.test_tone_process:
                            old_proc = self.test_tone_process
                            self.test_tone_process = None
                            self.test_tone_active = False
                            self.test_tone_channel = None
                    
                    # Kill old process if it exists (outside lock) - use kill immediately
                    if old_proc:
                        try:
                            logger.info(f"[THREAD] Killing old tone process PID {old_proc.pid}")
                            old_proc.kill()  # Force kill immediately
                            old_proc.wait(timeout=0.2)  # Brief wait
                            logger.info(f"[THREAD] Old tone process {old_proc.pid} killed")
                        except subprocess.TimeoutExpired:
                            logger.warning(f"[THREAD] Old process {old_proc.pid} didn't die, ignoring")
                        except Exception as e:
                            logger.warning(f"[THREAD] Error killing old process: {e}")
                except Exception as e:
                    logger.warning(f"[THREAD] Error in stop existing tone: {e}")
                
                # Get path to tone_generator.py
                import os.path
                import sys
                script_dir = os.path.dirname(os.path.abspath(__file__))
                tone_script = os.path.join(script_dir, 'tone_generator.py')
                
                # Launch subprocess with fresh Python interpreter
                # This avoids inheriting parent's PortAudio state
                # For tone testing, use the Scarlett USB device directly (index 1)
                # This is the actual audio interface - use it directly for tone testing
                device_arg = '1'  # Scarlett 8i6 USB device
                num_channels_arg = '6'  # Scarlett has 6 outputs
                
                logger.info(f"Tone will use Scarlett USB device (index 1), channel={channel}, num_channels={num_channels_arg}")
                
                logger.info(f"Starting tone: device={device_arg}, channel={channel}, num_channels={num_channels_arg}")
                
                # Redirect stderr to a log file so we can see errors
                import os
                log_file = os.path.join(os.path.dirname(tone_script), '..', 'logs', 'tone_generator.log')
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                
                proc = subprocess.Popen(
                    ['/usr/bin/python3', '-u', tone_script, device_arg, str(channel), '1000', '0.3', num_channels_arg],
                    stdout=subprocess.PIPE,
                    stderr=open(log_file, 'a'),  # Append to log file
                    stdin=subprocess.DEVNULL
                )
                
                print(f"Spawned tone generator PID {proc.pid} for channel {channel}", 
                      file=sys.stderr, flush=True)
                
                # Store process handle
                with self.lock:
                    self.test_tone_process = proc
                    self.test_tone_active = True
                    self.test_tone_channel = channel
                
                logger.info(f"Spawned tone process for Output {channel} (PID: {proc.pid})")
                
            except Exception as e:
                logger.error(f"Failed to spawn tone process: {e}", exc_info=True)
                with self.lock:
                    self.test_tone_active = False
                    self.test_tone_channel = None
        
        # Start the subprocess in a background thread
        logger.info(f"[BEFORE THREAD] About to create thread")
        spawn_thread = threading.Thread(target=start_in_thread, daemon=True)
        logger.info(f"[AFTER CREATE] Thread object created")
        spawn_thread.start()
        logger.info(f"[AFTER START] Thread.start() called")
        
        # Return IMMEDIATELY - don't wait for thread or subprocess
        logger.info(f"Initiated async tone start for channel {channel}")
        return True
    
    def stop_continuous_tone(self) -> bool:
        """
        Stop continuous test tone (non-blocking)
        
        Returns:
            True if stopped successfully
        """
        proc = None
        stopped_channel = None
        
        logger.info("[STOP] stop_continuous_tone called")
        
        with self.lock:
            if not self.test_tone_active:
                logger.info("[STOP] No active tone to stop")
                return True
            
            proc = self.test_tone_process
            stopped_channel = self.test_tone_channel
            
            logger.info(f"[STOP] Found active tone: PID={proc.pid if proc else 'None'}, channel={stopped_channel}")
            
            # Clear state immediately (before killing process)
            self.test_tone_process = None
            self.test_tone_active = False
            self.test_tone_channel = None
            
            # Stop old stream if it exists (legacy)
            if self.test_tone_stream:
                try:
                    self.test_tone_stream.stop()
                    self.test_tone_stream.close()
                except Exception:
                    pass
                self.test_tone_stream = None
        
        # Kill the subprocess immediately - use kill() for fast response
        if proc:
            try:
                pid = proc.pid
                logger.info(f"[STOP] Killing tone process immediately (PID: {pid})")
                # Force kill immediately - don't wait
                proc.kill()
                # Wait briefly to ensure it's dead
                import time
                time.sleep(0.1)
                if proc.poll() is None:  # Still running somehow
                    logger.warning(f"[STOP] Process {pid} still running after kill, trying system kill")
                    # Use system kill as backup
                    import subprocess
                    subprocess.run(['kill', '-9', str(pid)], timeout=0.5)
                else:
                    logger.info(f"[STOP] Tone process {pid} killed successfully")
            except Exception as e:
                logger.error(f"[STOP] Error killing tone process: {e}", exc_info=True)
                # Try system kill as last resort
                try:
                    import subprocess
                    subprocess.run(['kill', '-9', str(proc.pid)], timeout=0.5)
                    logger.info(f"[STOP] Used system kill for PID {proc.pid}")
                except:
                    pass
        
        # Safety: Kill ALL tone_generator processes (in case we lost track of one)
        # Try SIGTERM first (cleaner), then SIGKILL
        try:
            import subprocess
            # First try graceful termination
            result = subprocess.run(['pkill', '-TERM', '-f', 'tone_generator'], 
                                  timeout=0.5, capture_output=True)
            import time
            time.sleep(0.1)
            # Then force kill
            result = subprocess.run(['pkill', '-9', '-f', 'tone_generator'], 
                                  timeout=1.0, capture_output=True)
            if result.returncode == 0:
                logger.info("[STOP] Killed all tone_generator processes (safety cleanup)")
        except Exception as e:
            logger.warning(f"[STOP] Error in safety cleanup: {e}")
        
        if stopped_channel:
            logger.info(f"[STOP] Stopped continuous tone on Output {stopped_channel}")
        return True
    
    def cleanup(self):
        """Clean up audio router resources"""
        # Stop any active tone
        self.stop_continuous_tone()
        return True
    
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
