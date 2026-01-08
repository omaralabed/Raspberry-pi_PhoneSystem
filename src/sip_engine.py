#!/usr/bin/env python3
"""
SIP Engine - PJSIP Wrapper
Manages 8 SIP accounts with single trunk credentials
"""

import json
import logging
import threading
from typing import List, Optional, Dict, Callable
import pjsua2 as pj

from .phone_line import PhoneLine, LineState

logger = logging.getLogger(__name__)


class SIPAccount(pj.Account):
    """Extended PJSIP Account with callbacks"""
    
    def __init__(self, phone_line: PhoneLine, engine):
        super().__init__()
        self.phone_line = phone_line
        self.engine = engine
        self.current_call = None
    
    def onRegState(self, prm: pj.OnRegStateParam) -> None:
        """Called when registration state changes"""
        info = self.getInfo()
        status = info.regStatus
        logger.info(f"Line {self.phone_line.line_id}: Registration status: {status}")
        
        if status == 200:  # OK
            logger.info(f"Line {self.phone_line.line_id}: Registered successfully")
        else:
            logger.error(f"Line {self.phone_line.line_id}: Registration failed: {status}")
    
    def onIncomingCall(self, prm: pj.OnIncomingCallParam) -> None:
        """Called on incoming call - we reject these (outgoing only)"""
        call = SIPCall(self, prm.callId)
        call_info = call.getInfo()
        logger.warning(f"Line {self.phone_line.line_id}: Rejecting incoming call from {call_info.remoteUri}")
        
        # Reject with 403 Forbidden (outgoing only system)
        prm = pj.CallOpParam()
        prm.statusCode = 403
        call.hangup(prm)


class SIPCall(pj.Call):
    """Extended PJSIP Call with state management"""
    
    def __init__(self, account: SIPAccount, call_id: int = pj.PJSUA_INVALID_ID):
        super().__init__(account, call_id)
        self.account = account
        self.phone_line = account.phone_line
    
    def onCallState(self, prm: pj.OnCallStateParam) -> None:
        """Called when call state changes"""
        info = self.getInfo()
        state = info.state
        
        logger.info(f"Line {self.phone_line.line_id}: Call state: {state}")
        
        if state == pj.PJSIP_INV_STATE_CALLING:
            self.phone_line.set_state(LineState.DIALING)
        
        elif state == pj.PJSIP_INV_STATE_EARLY:
            self.phone_line.set_state(LineState.RINGING)
        
        elif state == pj.PJSIP_INV_STATE_CONFIRMED:
            self.phone_line.call_connected(self.getId())
            self.account.current_call = self
        
        elif state == pj.PJSIP_INV_STATE_DISCONNECTED:
            self.phone_line.reset()
            self.account.current_call = None
            # Delete call object
            self.delete()
    
    def onCallMediaState(self, prm: pj.OnCallMediaStateParam) -> None:
        """Called when media state changes"""
        info = self.getInfo()
        
        for mi in info.media:
            if mi.type == pj.PJMEDIA_TYPE_AUDIO:
                if mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                    # Connect audio
                    call_media = self.getMedia(mi.index)
                    aud_media = pj.AudioMedia.typecastFromMedia(call_media)
                    
                    # Get sound device
                    snd = self.account.engine.ep.audDevManager().getPlaybackDevMedia()
                    
                    # Route audio
                    aud_media.startTransmit(snd)
                    snd.startTransmit(aud_media)
                    
                    logger.info(f"Line {self.phone_line.line_id}: Audio connected")


class SIPEngine:
    """
    Main SIP engine managing 8 phone lines with single trunk
    """
    
    def __init__(self, config_path: str = "config/sip_config.json"):
        """
        Initialize SIP engine
        
        Args:
            config_path: Path to SIP configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # PJSIP objects
        self.ep: Optional[pj.Endpoint] = None
        self.transport: Optional[pj.TransportConfig] = None
        
        # Phone lines and accounts
        self.num_lines = self.config.get("num_lines", 8)
        self.lines: List[PhoneLine] = []
        self.accounts: List[SIPAccount] = []
        
        # State
        self.is_running = False
        self.lock = threading.Lock()
        
        logger.info(f"SIP Engine initialized for {self.num_lines} lines")
    
    def _load_config(self) -> Dict:
        """Load SIP configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded SIP config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load SIP config: {e}")
            raise
    
    def start(self) -> bool:
        """
        Start SIP engine and register all accounts
        
        Returns:
            True if started successfully
        """
        try:
            # Create PJSIP endpoint
            self.ep = pj.Endpoint()
            self.ep.libCreate()
            
            # Initialize endpoint
            ep_cfg = pj.EpConfig()
            ep_cfg.logConfig.level = 4  # Info level
            ep_cfg.logConfig.consoleLevel = 4
            self.ep.libInit(ep_cfg)
            
            # Create UDP transport
            transport_cfg = pj.TransportConfig()
            transport_cfg.port = 0  # Use any available port
            self.transport = self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)
            
            # Start the library
            self.ep.libStart()
            
            logger.info("PJSIP library started")
            
            # Create phone lines and SIP accounts
            for i in range(1, self.num_lines + 1):
                line = PhoneLine(line_id=i)
                self.lines.append(line)
                
                # Create and configure account
                account = SIPAccount(line, self)
                acc_cfg = pj.AccountConfig()
                
                # SIP credentials (same for all lines)
                sip_server = self.config["sip_server"]
                username = self.config["username"]
                password = self.config["password"]
                
                acc_cfg.idUri = f"sip:{username}@{sip_server}"
                acc_cfg.regConfig.registrarUri = f"sip:{sip_server}"
                acc_cfg.sipConfig.authCreds.append(
                    pj.AuthCredInfo("digest", "*", username, 0, password)
                )
                
                # Caller ID configuration
                caller_id_name = self.config.get("caller_id_name", "Phone System")
                caller_id_number = self.config.get("caller_id_number", username)
                acc_cfg.sipConfig.proxies = []
                
                # Create account
                account.create(acc_cfg)
                self.accounts.append(account)
                
                line.sip_account_id = account.getId()
                
                logger.info(f"Line {i}: Account created and registering")
            
            self.is_running = True
            logger.info(f"SIP engine started with {self.num_lines} lines")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start SIP engine: {e}")
            return False
    
    def stop(self) -> None:
        """Stop SIP engine and cleanup"""
        if not self.is_running:
            return
        
        logger.info("Stopping SIP engine...")
        
        # Hangup all active calls
        for account in self.accounts:
            if account.current_call:
                try:
                    account.current_call.hangup(pj.CallOpParam())
                except:
                    pass
        
        # Delete accounts
        for account in self.accounts:
            try:
                account.delete()
            except:
                pass
        
        # Destroy PJSIP
        if self.ep:
            try:
                self.ep.libDestroy()
            except:
                pass
        
        self.is_running = False
        logger.info("SIP engine stopped")
    
    def make_call(self, line_id: int, phone_number: str) -> bool:
        """
        Make outgoing call on specified line
        
        Args:
            line_id: Line number (1-8)
            phone_number: Destination number
            
        Returns:
            True if call initiated successfully
        """
        if not self.is_running:
            logger.error("SIP engine not running")
            return False
        
        if line_id < 1 or line_id > self.num_lines:
            logger.error(f"Invalid line ID: {line_id}")
            return False
        
        line = self.lines[line_id - 1]
        account = self.accounts[line_id - 1]
        
        if not line.is_available():
            logger.warning(f"Line {line_id} not available")
            return False
        
        try:
            # Mark line as dialing
            line.dial(phone_number)
            
            # Create call
            call = SIPCall(account)
            
            # Setup call parameters
            prm = pj.CallOpParam()
            prm.opt.audioCount = 1
            prm.opt.videoCount = 0
            
            # Make the call
            sip_uri = f"sip:{phone_number}@{self.config['sip_server']}"
            call.makeCall(sip_uri, prm)
            
            logger.info(f"Line {line_id}: Calling {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Line {line_id}: Failed to make call: {e}")
            line.reset()
            return False
    
    def hangup_call(self, line_id: int) -> bool:
        """
        Hang up call on specified line
        
        Args:
            line_id: Line number (1-8)
            
        Returns:
            True if hangup successful
        """
        if line_id < 1 or line_id > self.num_lines:
            return False
        
        line = self.lines[line_id - 1]
        account = self.accounts[line_id - 1]
        
        if not account.current_call:
            logger.warning(f"Line {line_id}: No active call")
            return False
        
        try:
            prm = pj.CallOpParam()
            account.current_call.hangup(prm)
            logger.info(f"Line {line_id}: Hanging up")
            return True
        except Exception as e:
            logger.error(f"Line {line_id}: Failed to hangup: {e}")
            return False
    
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
