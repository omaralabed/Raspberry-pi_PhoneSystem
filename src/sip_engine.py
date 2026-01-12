#!/usr/bin/env python3
"""
SIP Engine - Baresip Wrapper
Manages 8 SIP accounts using Baresip command-line tool
"""

import json
import logging
import subprocess
import threading
import time
import re
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from .phone_line import PhoneLine, LineState

logger = logging.getLogger(__name__)


class BaresipProcess:
    """Manages a Baresip subprocess for one SIP line"""
    
    def __init__(self, line_id: int, config: Dict[str, Any], phone_line: PhoneLine):
        self.line_id = line_id
        self.config = config
        self.phone_line = phone_line
        self.process: Optional[subprocess.Popen] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.running = False
        self.current_call_id: Optional[str] = None
        self.config_dir = Path.home() / f".baresip_line{line_id}"
        
    def _create_config_files(self) -> bool:
        """Create Baresip configuration files"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            # Secure directory permissions (only owner can read/write/execute)
            os.chmod(self.config_dir, 0o700)
            
            # Create accounts file
            accounts_file = self.config_dir / "accounts"
            sip_user = self.config.get("username", "")
            sip_server = self.config.get("sip_server", "")
            sip_password = self.config.get("password", "")
            
            # Format: <sip:user@domain>;auth_pass=password
            account_line = f"<sip:{sip_user}@{sip_server}>;auth_pass={sip_password}\n"
            
            with open(accounts_file, "w") as f:
                f.write(account_line)
            # Secure file permissions (only owner can read/write)
            os.chmod(accounts_file, 0o600)
            
            # Create config file
            config_file = self.config_dir / "config"
            with open(config_file, "w") as f:
                f.write(f"# Baresip configuration for Line {self.line_id}\n")
                f.write("\n# Audio settings\n")
                f.write("audio_player alsa,default\n")
                f.write("audio_source alsa,default\n")
                f.write("audio_alert alsa,default\n")
                f.write("\n# SIP settings\n")
                f.write("sip_listen 0.0.0.0:0\n")
                f.write("\n# Disable video\n")
                f.write("video_display no\n")
                f.write("video_source no\n")
                f.write("\n# Module path\n")
                f.write("module_path /usr/lib/baresip/modules\n")
                f.write("\n# Load modules\n")
                f.write("module alsa.so\n")
                f.write("module account.so\n")
                f.write("module menu.so\n")
                f.write("module stdio.so\n")
            
            logger.debug(f"Line {self.line_id}: Config files created in {self.config_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Line {self.line_id}: Failed to create config: {e}")
            return False
    
    def start(self) -> bool:
        """Start Baresip process"""
        try:
            if not self._create_config_files():
                return False
            
            # Start Baresip with verbose output
            cmd = ["baresip", "-f", str(self.config_dir), "-v"]
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.running = True
            
            # Start output monitor thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_output,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info(f"Line {self.line_id}: Baresip started (PID {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Line {self.line_id}: Failed to start Baresip: {e}")
            return False
    
    def _monitor_output(self) -> None:
        """Monitor Baresip stdout/stderr for state changes"""
        if not self.process or not self.process.stdout:
            return
        
        try:
            for line in iter(self.process.stdout.readline, ""):
                if not line or not self.running:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                logger.debug(f"Line {self.line_id}: {line}")
                
                # Parse Baresip output for events
                line_lower = line.lower()
                
                # Registration events
                if "register: 200 ok" in line_lower:
                    logger.info(f"Line {self.line_id}: SIP registration successful")
                    
                elif "register:" in line_lower and ("401" in line_lower or "403" in line_lower):
                    logger.error(f"Line {self.line_id}: SIP registration failed")
                
                # Call state events (be specific to avoid false matches)
                elif "call: connecting" in line_lower or "100 trying" in line_lower:
                    logger.info(f"Line {self.line_id}: Call connecting")
                    self.phone_line.set_state(LineState.DIALING)
                
                elif ("180 ringing" in line_lower or "call: ringing" in line_lower):
                    logger.info(f"Line {self.line_id}: Call ringing")
                    self.phone_line.set_state(LineState.RINGING)
                
                elif "call: established" in line_lower:
                    # Only transition to connected from valid call states
                    if self.phone_line.state in [LineState.DIALING, LineState.RINGING]:
                        logger.info(f"Line {self.line_id}: Call connected")
                        self.phone_line.call_connected(self.current_call_id)
                    else:
                        logger.debug(f"Line {self.line_id}: Ignoring 'established' in state {self.phone_line.state.value}")
                
                elif "call: closed" in line_lower or "call closed" in line_lower:
                    # Only reset if we have an active call ID
                    if self.current_call_id:
                        logger.info(f"Line {self.line_id}: Call ended")
                        self.phone_line.reset()
                        self.current_call_id = None
                    else:
                        logger.debug(f"Line {self.line_id}: Ignoring 'call closed' - already reset")
                
                elif "hangup" in line_lower and "ok" in line_lower:
                    # Only reset if we have an active call ID
                    if self.current_call_id:
                        logger.info(f"Line {self.line_id}: Hangup confirmed")
                        self.phone_line.reset()
                        self.current_call_id = None
                    else:
                        logger.debug(f"Line {self.line_id}: Ignoring 'hangup ok' - already reset")
                
        except Exception as e:
            if self.running:
                logger.error(f"Line {self.line_id}: Monitor thread crashed: {e}")
                self.running = False
                self.phone_line.reset()  # Reset line state on monitor failure
        finally:
            # Handle process death (stdout EOF reached)
            if self.running and self.process:
                exit_code = self.process.poll()
                if exit_code is not None:
                    logger.error(f"Line {self.line_id}: Baresip process died (exit code {exit_code})")
                    self.running = False
                    self.phone_line.reset()
    
    def make_call(self, phone_number: str) -> bool:
        """Make outgoing call"""
        if not self.running or not self.process or not self.process.stdin:
            logger.error(f"Line {self.line_id}: Baresip not running")
            return False
        
        if self.process.stdin.closed:
            logger.error(f"Line {self.line_id}: Baresip stdin closed")
            return False
        
        # Validate phone number - only allow digits, +, -, *, #, and spaces
        if not phone_number or not re.match(r'^[0-9+\-*#\s]+$', phone_number):
            logger.error(f"Line {self.line_id}: Invalid phone number format: {phone_number}")
            return False
        
        # Remove any whitespace
        phone_number = phone_number.replace(' ', '')
        
        # Validate not empty after whitespace removal
        if not phone_number:
            logger.error(f"Line {self.line_id}: Phone number is empty after whitespace removal")
            return False
        
        try:
            sip_uri = f"sip:{phone_number}@{self.config['sip_server']}"
            dial_cmd = f"/dial {sip_uri}\n"
            self.process.stdin.write(dial_cmd)
            self.process.stdin.flush()
            
            # Only update phone line state AFTER successful write/flush
            self.current_call_id = phone_number
            if not self.phone_line.dial(phone_number):
                logger.error(f"Line {self.line_id}: Phone line rejected dial request")
                return False
            
            logger.info(f"Line {self.line_id}: Dialing {phone_number}")
            return True
            
        except (BrokenPipeError, OSError) as e:
            logger.error(f"Line {self.line_id}: Baresip process died during dial: {e}")
            self.running = False
            self.phone_line.reset()  # Reset state on failure
            return False
        except Exception as e:
            logger.error(f"Line {self.line_id}: Failed to dial: {e}")
            self.phone_line.reset()  # Reset state on failure
            return False
    
    def hangup(self) -> bool:
        """Hang up current call"""
        logger.info(f"[BaresipProcess] Line {self.line_id}: hangup() called")
        
        if not self.running or not self.process or not self.process.stdin:
            logger.warning(f"Line {self.line_id}: Cannot hangup - process not running or no stdin")
            return False
        
        if self.process.stdin.closed:
            logger.warning(f"Line {self.line_id}: Baresip stdin already closed")
            return False
        
        try:
            logger.info(f"Line {self.line_id}: Writing 'h' (hangup) command to baresip stdin")
            self.process.stdin.write("h\n")
            self.process.stdin.flush()
            
            logger.info(f"Line {self.line_id}: Hangup command sent successfully")
            return True
            
        except (BrokenPipeError, OSError) as e:
            logger.error(f"Line {self.line_id}: Baresip process died during hangup: {e}")
            self.running = False
            self.phone_line.reset()  # Clean up state
            return False
        except Exception as e:
            logger.error(f"Line {self.line_id}: Failed to hangup: {e}")
            self.phone_line.reset()  # Clean up state
            return False
    
    def stop(self) -> None:
        """Stop Baresip process"""
        self.running = False
        
        if self.process:
            try:
                # Try graceful quit
                if self.process.stdin and not self.process.stdin.closed:
                    try:
                        self.process.stdin.write("/quit\n")
                        self.process.stdin.flush()
                    except (BrokenPipeError, OSError):
                        pass  # Process already dead
                
                # Wait briefly for graceful shutdown
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.warning(f"Line {self.line_id}: Error during stop: {e}")
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                # Explicitly close pipes to prevent resource leaks
                if self.process.stdin:
                    try:
                        self.process.stdin.close()
                    except:
                        pass
                if self.process.stdout:
                    try:
                        self.process.stdout.close()
                    except:
                        pass
            
            self.process = None
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
        
        logger.info(f"Line {self.line_id}: Baresip stopped")


class SIPEngine:
    """Main SIP engine managing multiple phone lines via Baresip"""
    
    def __init__(self, num_lines: int = 8):
        self.num_lines = num_lines
        self.lines: List[PhoneLine] = []
        self.baresip_processes: List[BaresipProcess] = []
        self.config: Dict[str, Any] = {}
        self.is_running = False
        
        for i in range(1, num_lines + 1):
            line = PhoneLine(line_id=i)
            self.lines.append(line)
    
    def load_config(self, config_path: str = "config/sip_config.json") -> bool:
        """Load SIP configuration from JSON file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.error(f"Config file not found: {config_path}")
                return False
            
            with open(config_file, "r") as f:
                self.config = json.load(f)
            
            required = ["username", "password", "sip_server"]
            for field in required:
                if field not in self.config:
                    logger.error(f"Missing required config field: {field}")
                    return False
                if not self.config[field]:
                    logger.error(f"Config field '{field}' cannot be empty")
                    return False
            
            logger.info(f"Loaded SIP config from {config_path}")
            logger.info(f"SIP Server: {self.config['sip_server']}")
            logger.info(f"Username: {self.config['username']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def start(self) -> bool:
        """Initialize and start SIP engine"""
        if self.is_running:
            logger.warning("SIP engine already running")
            return True
        
        if not self.config:
            logger.error("No configuration loaded")
            return False
        
        try:
            logger.info(f"Starting SIP engine with {self.num_lines} lines...")
            
            for i, line in enumerate(self.lines, start=1):
                baresip = BaresipProcess(i, self.config, line)
                
                if not baresip.start():
                    logger.error(f"Failed to start Baresip for line {i}")
                    self.stop()
                    return False
                
                self.baresip_processes.append(baresip)
                time.sleep(0.3)  # Small delay between starts to avoid resource contention
            
            self.is_running = True
            logger.info(f"SIP engine started successfully with {self.num_lines} lines")
            # Note: Removed unnecessary 2-second sleep here
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start SIP engine: {e}")
            self.stop()
            return False
    
    def stop(self) -> None:
        """Stop SIP engine and cleanup"""
        # Don't early return - we need to cleanup even if not fully started
        if not self.is_running and not self.baresip_processes:
            return
        
        logger.info("Stopping SIP engine...")
        
        # First, send hangup to all active calls
        for baresip in self.baresip_processes:
            if baresip.current_call_id:
                try:
                    baresip.hangup()
                except Exception as e:
                    logger.warning(f"Error hanging up line {baresip.line_id}: {e}")
        
        # Give adequate time for graceful hangup (2 seconds for network round-trip)
        time.sleep(2.0)
        
        # Now stop all processes
        for baresip in self.baresip_processes:
            try:
                baresip.stop()
            except Exception as e:
                logger.warning(f"Error stopping line {baresip.line_id}: {e}")
        
        self.baresip_processes.clear()
        
        for line in self.lines:
            line.reset()
        
        self.is_running = False
        logger.info("SIP engine stopped")
    
    def make_call(self, line_id: int, phone_number: str) -> bool:
        """Make outgoing call on specified line"""
        if not self.is_running:
            logger.error("SIP engine not running")
            return False
        
        if line_id < 1 or line_id > self.num_lines:
            logger.error(f"Invalid line ID: {line_id}")
            return False
        
        # Verify the line and baresip process exist
        if line_id > len(self.lines) or line_id > len(self.baresip_processes):
            logger.error(f"Line {line_id} not initialized")
            return False
        
        line = self.lines[line_id - 1]
        baresip = self.baresip_processes[line_id - 1]
        
        if not line.is_available():
            logger.warning(f"Line {line_id} not available (state: {line.state})")
            return False
        
        return baresip.make_call(phone_number)
    
    def hangup_call(self, line_id: int) -> bool:
        """Hang up call on specified line"""
        logger.info(f"[SIPEngine] hangup_call() called for line {line_id}")
        
        if line_id < 1 or line_id > self.num_lines:
            logger.error(f"Invalid line_id: {line_id}")
            return False
        
        # Verify the line and baresip process exist
        if line_id > len(self.lines) or line_id > len(self.baresip_processes):
            logger.error(f"Line {line_id} not initialized")
            return False
        
        line = self.lines[line_id - 1]
        baresip = self.baresip_processes[line_id - 1]
        
        if not line.is_active():
            logger.warning(f"Line {line_id}: No active call (state={line.state})")
            return False
        
        logger.info(f"Line {line_id}: Calling baresip.hangup()")
        return baresip.hangup()
    
    def get_line(self, line_id: int) -> Optional[PhoneLine]:
        """Get phone line object"""
        if 1 <= line_id <= self.num_lines:
            return self.lines[line_id - 1]
        return None
    
    def get_available_lines(self) -> List[PhoneLine]:
        """Get list of available lines"""
        return [line for line in self.lines if line.is_available()]
    
    def get_active_lines(self) -> List[PhoneLine]:
        """Get list of lines with active calls"""
        return [line for line in self.lines if line.is_active()]
