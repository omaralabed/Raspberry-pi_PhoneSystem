# Raspberry Pi Phone System - IFB/PL Communication System

A professional 8-line phone system for Raspberry Pi with touchscreen interface, designed for broadcast and live event production with flexible IFB (Interruptible Foldback) and PL (Private Line) audio routing.

## Features

- **8 Concurrent Outgoing Phone Lines** - Make up to 8 simultaneous calls
- **Single Trunk/Caller ID** - All lines use one phone number for outgoing calls
- **Touchscreen GUI** - Intuitive dialer interface with visual feedback
- **Flexible Audio Routing** - Route each line to IFB or PL outputs independently
- **No Incoming Calls** - Outgoing only for production communication
- **Lightweight & Portable** - Runs on Raspberry Pi 4/5 with Ubuntu 22.04 LTS

## Hardware Requirements

### Minimum Specifications
- **Raspberry Pi 4 (4GB RAM)** or Raspberry Pi 5 (8GB recommended)
- **Official 7" Touchscreen** or compatible touchscreen display
- **USB Audio Interface** - Multi-channel (minimum 4 outputs for stereo IFB + PL)
  - **Option A (Budget):** DIY Raspberry Pi Pico 2 interface (~$150) - See [PICO2_AUDIO_INTERFACE.md](PICO2_AUDIO_INTERFACE.md)
  - **Option B (Commercial):** Behringer UMC1820, Focusrite Scarlett 18i20 (~$300-500)
  - For 2-wire party line XLR: Custom Pico 2 interface recommended
- **MicroSD Card** - 32GB or larger, Class 10
- **Power Supply** - Official Raspberry Pi power adapter
- **Network Connection** - Ethernet (recommended) or WiFi

### VoIP Service
- **SIP Trunk Provider** - Any provider supporting outbound calls (Twilio, Vonage, etc.)
- **Internet Connection** - Stable broadband (minimum 1 Mbps per concurrent call)

## Software Architecture

```
┌─────────────────────────────────────────────────────┐
│           PyQt5 Touchscreen Interface               │
│  (Dialer Pad, Call Status, Audio Routing Control)  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│         Python SIP Engine (PJSIP/pjsua2)            │
│  - 8 SIP accounts (same trunk credentials)          │
│  - Call management and control                      │
│  - Caller ID configuration                          │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│      PulseAudio / ALSA Audio Routing System         │
│  - Per-line audio output selection                  │
│  - IFB Output (Stereo L/R)                          │
│  - PL Output (Stereo L/R)                           │
└─────────────────────────────────────────────────────┘
```

## Installation

### Quick Start (Ubuntu 22.04 LTS on Raspberry Pi)

```bash
# Clone the repository
cd ~/Desktop
cd PhoneSystem

# Run the automated installer
sudo python3 install.py

# Configure your SIP credentials
nano config/sip_config.json

# Start the phone system
python3 main.py
```

### Manual Installation

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions.

## Configuration

### SIP Configuration (`config/sip_config.json`)
```json
{
  "sip_server": "sip.yourprovider.com",
  "sip_port": 5060,
  "username": "your_account",
  "password": "your_password",
  "caller_id": "+1234567890",
  "num_lines": 8
}
```

### Audio Configuration (`config/audio_config.json`)
```json
{
  "audio_device": "USB Audio Interface",
  "ifb_output": ["hw:1,0", "hw:1,1"],
  "pl_output": ["hw:1,2", "hw:1,3"],
  "sample_rate": 48000,
  "buffer_size": 256
}
```

## Usage

### Starting the System
```bash
python3 main.py
```

### Making a Call
1. Select an available line (1-8)
2. Enter phone number using on-screen dialer
3. Press "Call" button
4. Select audio routing (IFB or PL) for the line
5. Press "Hang Up" when finished

### Audio Routing
- **IFB (Interruptible Foldback)** - Typically for talent communication
- **PL (Private Line)** - Typically for crew communication
- Each line can be independently routed to either output
- Routing can be changed during an active call

## Project Structure

```
PhoneSystem/
├── README.md                 # This file
├── INSTALLATION.md          # Detailed installation guide
├── requirements.txt         # Python dependencies
├── main.py                  # Application entry point
├── install.py               # Automated installer
├── config/
│   ├── sip_config.json      # SIP trunk configuration
│   └── audio_config.json    # Audio routing configuration
├── src/
│   ├── __init__.py
│   ├── sip_engine.py        # PJSIP wrapper for 8 lines
│   ├── audio_router.py      # PulseAudio routing manager
│   ├── phone_line.py        # Individual line management
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py   # Main touchscreen interface
│       ├── dialer_widget.py # Dialer pad widget
│       ├── line_widget.py   # Line status widget
│       └── audio_widget.py  # Audio routing controls
├── systemd/
│   └── phoneystem.service   # Auto-start service
└── tests/
    ├── test_sip_engine.py
    ├── test_audio_router.py
    └── test_integration.py
```

## Technical Details

- **SIP Stack**: PJSIP 2.x via Python bindings
- **GUI Framework**: PyQt5 for touchscreen
- **Audio System**: PulseAudio with ALSA backend
- **Codec**: G.711 (μ-law/A-law) for broad compatibility
- **Latency**: ~20-50ms typical for audio routing

## Troubleshooting

### No Audio Output
```bash
# Check audio devices
aplay -l
pactl list sinks

# Test audio routing
python3 -m src.audio_router --test
```

### SIP Registration Failed
```bash
# Check network connectivity
ping sip.yourprovider.com

# Verify credentials in config/sip_config.json
# Check SIP logs in logs/sip_debug.log
```

### Touchscreen Not Responding
```bash
# Calibrate touchscreen
xinput_calibrator

# Check display settings
export DISPLAY=:0
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

## Author

Created for professional broadcast and live event production environments.
