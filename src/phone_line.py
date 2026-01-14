#!/usr/bin/env python3
"""
Phone Line Manager
Manages individual phone line state and operations
"""

import time
from enum import Enum
from typing import Optional, Callable
import logging
import threading

logger = logging.getLogger(__name__)


class LineState(Enum):
    """Phone line states"""
    IDLE = "idle"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class AudioOutput:
    """Audio output routing options - flexible channel assignment"""
    def __init__(self, channel: int):
        """
        Initialize audio output
        
        Args:
            channel: Output channel number (0=no output, 1-8=physical outputs)
        """
        if not 0 <= channel <= 8:
            raise ValueError("Channel must be between 0 and 8 (0=no output)")
        self.channel = channel
    
    def __str__(self):
        if self.channel == 0:
            return "No Output"
        return f"Out {self.channel}"
    
    def __repr__(self):
        return f"AudioOutput(channel={self.channel})"
    
    def __eq__(self, other):
        if isinstance(other, AudioOutput):
            return self.channel == other.channel
        return False
    
    def __hash__(self):
        """Make AudioOutput hashable for use in sets/dicts"""
        return hash(self.channel)


class PhoneLine:
    """
    Manages a single phone line with SIP call control and audio routing
    """
    
    def __init__(self, line_id: int, sip_account_id: int = None, default_output: int = None):
        """
        Initialize a phone line
        
        Args:
            line_id: Line number (1-8)
            sip_account_id: SIP account ID (deprecated, not used with Baresip)
            default_output: Default output channel (0=no output, 1-8), defaults to 0
        """
        self.line_id = line_id
        self.sip_account_id = sip_account_id
        self.state = LineState.IDLE
        # Default to no output (0) - operator assigns manually
        self.audio_output = AudioOutput(default_output if default_output is not None else 0)
        
        # Call information
        self.call_id = None
        self.remote_number = None
        self.call_duration = 0
        self.call_start_time = None
        
        # Thread safety lock for state changes (reentrant to allow nested calls)
        self._lock = threading.RLock()
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_audio_route_change: Optional[Callable] = None
        
        logger.info(f"Line {line_id} initialized")
    
    def set_state(self, new_state: LineState) -> None:
        """
        Update line state and trigger callback
        
        Args:
            new_state: New line state
        """
        with self._lock:
            if self.state != new_state:
                # Validate state transition
                if not self._is_valid_transition(self.state, new_state):
                    logger.warning(f"Line {self.line_id}: Invalid transition {self.state.value} -> {new_state.value}")
                    return
                
                old_state = self.state
                self.state = new_state
                logger.info(f"Line {self.line_id}: {old_state.value} -> {new_state.value}")
                
                if self.on_state_change:
                    try:
                        self.on_state_change(self.line_id, old_state, new_state)
                    except Exception as e:
                        logger.error(f"Line {self.line_id}: State change callback error: {e}")
    
    def _is_valid_transition(self, from_state: LineState, to_state: LineState) -> bool:
        """
        Validate state machine transitions
        
        Valid transitions:
        - IDLE -> DIALING (outgoing call)
        - DIALING -> RINGING (call progressing)
        - DIALING -> CONNECTED (immediate answer)
        - RINGING -> CONNECTED (answered)
        - DIALING/RINGING/CONNECTED -> DISCONNECTED (hangup)
        - DISCONNECTED -> IDLE (cleanup)
        - Any state -> ERROR (error condition)
        - Any state -> same state (no-op, but allowed)
        """
        if from_state == to_state:
            return True
        
        # Allow transitions to ERROR from any state
        if to_state == LineState.ERROR:
            return True
        
        # Define valid transitions
        valid_transitions = {
            LineState.IDLE: [LineState.DIALING],
            LineState.DIALING: [LineState.RINGING, LineState.CONNECTED, LineState.DISCONNECTED],
            LineState.RINGING: [LineState.CONNECTED, LineState.DISCONNECTED],
            LineState.CONNECTED: [LineState.DISCONNECTED],
            LineState.DISCONNECTED: [LineState.IDLE],
            LineState.ERROR: [LineState.IDLE]  # Can recover from error
        }
        
        allowed = valid_transitions.get(from_state, [])
        return to_state in allowed
    
    def set_audio_output(self, output: AudioOutput) -> None:
        """
        Set audio routing for this line
        
        Args:
            output: IFB or PL
        """
        if self.audio_output != output:
            old_output = self.audio_output
            self.audio_output = output
            logger.info(f"Line {self.line_id}: Audio routing {old_output} -> {output}")
            
            if self.on_audio_route_change:
                try:
                    self.on_audio_route_change(self.line_id, output)
                except Exception as e:
                    logger.error(f"Line {self.line_id}: Audio route callback error: {e}")
    
    def cycle_audio_output(self) -> AudioOutput:
        """
        Cycle to next output channel (1->2->3...->8->1)
        
        Returns:
            New audio output setting
        """
        next_channel = (self.audio_output.channel % 8) + 1
        new_output = AudioOutput(next_channel)
        self.set_audio_output(new_output)
        return new_output
    
    def set_audio_channel(self, channel: int) -> bool:
        """
        Set specific audio output channel
        
        Args:
            channel: Output channel (0=no output, 1-8)
            
        Returns:
            True if successful
        """
        try:
            new_output = AudioOutput(channel)
            self.set_audio_output(new_output)
            return True
        except ValueError:
            return False
    
    def dial(self, phone_number: str) -> bool:
        """
        Initiate outgoing call
        
        Args:
            phone_number: Destination phone number
            
        Returns:
            True if dial initiated successfully
        """
        with self._lock:
            if self.state != LineState.IDLE:
                logger.warning(f"Line {self.line_id}: Cannot dial in state {self.state.value}")
                return False
            
            # Validate phone number
            if not phone_number or not isinstance(phone_number, str) or not phone_number.strip():
                logger.error(f"Line {self.line_id}: Invalid phone number: {phone_number}")
                return False
            
            self.remote_number = phone_number
            self.set_state(LineState.DIALING)
            logger.info(f"Line {self.line_id}: Dialing {phone_number}")
            return True
    
    def call_connected(self, call_id: str) -> None:
        """
        Mark call as connected
        
        Args:
            call_id: Call identifier (phone number or call ID string)
        """
        with self._lock:
            self.call_id = call_id
            self.call_start_time = time.time()
            self.set_state(LineState.CONNECTED)
            logger.info(f"Line {self.line_id}: Call connected (call_id={call_id})")
    
    def hangup(self) -> bool:
        """
        Terminate active call
        
        Returns:
            True if hangup initiated
        """
        with self._lock:
            if self.state not in [LineState.DIALING, LineState.RINGING, LineState.CONNECTED]:
                logger.warning(f"Line {self.line_id}: No active call to hang up")
                return False
            
            self.set_state(LineState.DISCONNECTED)
            logger.info(f"Line {self.line_id}: Hanging up")
            return True
    
    def reset(self) -> None:
        """Reset line to idle state"""
        with self._lock:
            # If currently in an active call state, transition through DISCONNECTED first
            if self.state in [LineState.DIALING, LineState.RINGING, LineState.CONNECTED]:
                self.set_state(LineState.DISCONNECTED)
            
            # Finalize call duration before clearing
            if self.call_start_time and self.state == LineState.DISCONNECTED:
                final_duration = int(time.time() - self.call_start_time)
                self.call_duration = final_duration
                logger.info(f"Line {self.line_id}: Call ended, duration: {final_duration}s")
            
            # Clear call data
            self.call_id = None
            self.remote_number = None
            self.call_start_time = None
            # Keep call_duration for logging/stats until next call
            
            # Transition to IDLE
            self.set_state(LineState.IDLE)
            logger.info(f"Line {self.line_id}: Reset to idle")
    
    def get_call_duration(self) -> int:
        """
        Get current call duration in seconds
        
        Returns:
            Call duration or 0 if not connected
        """
        with self._lock:
            if self.state == LineState.CONNECTED and self.call_start_time:
                return int(time.time() - self.call_start_time)
            return 0
    
    def is_available(self) -> bool:
        """Check if line is available for new call"""
        return self.state == LineState.IDLE
    
    def is_active(self) -> bool:
        """Check if line has an active call"""
        return self.state in [LineState.DIALING, LineState.RINGING, LineState.CONNECTED]
    
    def get_status_string(self) -> str:
        """
        Get human-readable status string
        
        Returns:
            Status string for display
        """
        with self._lock:
            if self.state == LineState.IDLE:
                return "Available"
            elif self.state == LineState.DIALING:
                return f"Dialing {self.remote_number or 'Unknown'}"
            elif self.state == LineState.RINGING:
                return f"Ringing {self.remote_number or 'Unknown'}"
            elif self.state == LineState.CONNECTED:
                # Calculate duration inline to avoid nested lock acquisition
                duration = 0
                if self.call_start_time:
                    duration = int(time.time() - self.call_start_time)
                mins, secs = divmod(duration, 60)
                number = self.remote_number or 'Unknown'
                return f"{number} ({mins:02d}:{secs:02d})"
            elif self.state == LineState.DISCONNECTED:
                return "Disconnecting..."
            else:
                return "Error"
    
    def __repr__(self) -> str:
        return (f"PhoneLine(id={self.line_id}, state={self.state.value}, "
                f"audio={self.audio_output}, number={self.remote_number})")
