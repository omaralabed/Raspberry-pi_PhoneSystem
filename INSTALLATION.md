# Detailed Installation Guide

## Raspberry Pi Phone System - Ubuntu 22.04 LTS Installation

This guide provides step-by-step instructions for setting up the phone system on a Raspberry Pi running Ubuntu 22.04 LTS.

---

## Hardware Setup

### 1. Raspberry Pi Configuration

**Recommended:**
- Raspberry Pi 5 (8GB RAM) - Best performance
- Raspberry Pi 4 (4GB RAM minimum, 8GB recommended)

**Required Peripherals:**
- Official Raspberry Pi 7" Touchscreen Display OR
- Any HDMI touchscreen (800x480 or higher)
- **USB Audio Interface with 8 outputs** (see recommendations below)
- MicroSD Card (32GB+, Class 10)
- Ethernet cable (recommended for SIP reliability)

### 2. Audio Interface Recommendations

**Desktop Units (Top-Panel Connectors):**

**RECOMMENDED: MOTU UltraLite-mk5** (~$595)
- USB-C (USB 3.0) connection
- 8 analog outputs on top/front panel
- Compact desktop design
- Ultra-low latency (<2ms)
- Excellent Linux/ALSA support
- Bus-powered (no external power needed)
- LCD screen and volume controls on top

**Alternative Options:**
- **Audient iD44** (~$599) - USB-C, desktop unit with top controls
- **PreSonus Studio 1824c** (~$499) - USB-C, rack-mountable but can sit on desk
- **2x Behringer UMC404HD** (~$200 total) - Budget option, USB 2.0, 4 outputs each

**What You Need:**
- Audio interface with **8 line outputs** (TRS balanced)
- **USB 3.0/USB-C** connection for best performance
- **Linux/ALSA compatible** (all recommended units are tested)
- **Desktop form factor** with top-accessible controls and connectors

### 3. Ubuntu Installation

1. Download Ubuntu 22.04 LTS for Raspberry Pi:
   ```bash
   # From your computer
   wget https://cdimage.ubuntu.com/releases/22.04/release/ubuntu-22.04.3-preinstalled-desktop-arm64+raspi.img.xz
   ```

2. Flash to microSD card using Raspberry Pi Imager or balenaEtcher

3. Boot Raspberry Pi and complete Ubuntu setup wizard

4. Update system:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo reboot
   ```

### 3. Touchscreen Configuration

For official 7" touchscreen:
```bash
# Should work automatically with Ubuntu 22.04
# Verify with:
xinput list
```

For other touchscreens, you may need to calibrate:
```bash
sudo apt install xinput-calibrator
xinput_calibrator
```

---

## Software Installation

### Option 1: Automated Installation (Recommended)

```bash
# Navigate to project directory
cd ~/Desktop/PhoneSystem

# Run installer (will prompt for sudo password when needed)
python3 install.py
```

The installer will:
- Check Ubuntu version
- Install system dependencies
- Build and install PJSIP with Python bindings
- Install Python packages
- Configure audio system
- Create systemd service for auto-start

### Option 2: Manual Installation

#### Step 1: System Dependencies

```bash
# Update package list
sudo apt update

# Install build tools
sudo apt install -y build-essential cmake pkg-config git wget curl

# Install Python development
sudo apt install -y python3-dev python3-pip python3-venv

# Install audio libraries
sudo apt install -y libasound2-dev portaudio19-dev pulseaudio pavucontrol

# Install PyQt5
sudo apt install -y python3-pyqt5 python3-pyqt5.qtmultimedia pyqt5-dev-tools

# Install PJSIP dependencies
sudo apt install -y libssl-dev libsrtp2-dev
```

#### Step 2: Build PJSIP with Python Bindings

```bash
# Download PJSIP
cd /tmp
git clone https://github.com/pjsip/pjproject.git
cd pjproject

# Configure and build
./configure --enable-shared --disable-video --disable-opencore-amr
make dep
make
sudo make install

# Build Python bindings
cd pjsip-apps/src/python
sudo python3 setup.py install

# Update library cache
sudo ldconfig
```

#### Step 3: Install Python Packages

```bash
cd ~/Desktop/PhoneSystem
pip3 install -r requirements.txt
```

#### Step 4: Configure Audio

Create `~/.config/pulse/daemon.conf`:

```ini
# Low latency configuration
default-sample-rate = 48000
alternate-sample-rate = 48000
default-fragments = 2
default-fragment-size-msec = 5
high-priority = yes
nice-level = -11
realtime-scheduling = yes
realtime-priority = 9
```

Restart PulseAudio:
```bash
pulseaudio -k
pulseaudio --start
```

---

## Configuration

### 1. SIP Trunk Configuration

Edit `config/sip_config.json`:

```json
{
  "sip_server": "sip.yourprovider.com",
  "sip_port": 5060,
  "transport": "UDP",
  "username": "your_account_number",
  "password": "your_password",
  "caller_id_name": "Production Phone",
  "caller_id_number": "+15551234567",
  "num_lines": 8,
  "codec_priority": ["PCMU", "PCMA", "G722"],
  "registration_timeout": 300,
  "retry_interval": 30
}
```

**Popular SIP Providers:**
- **Twilio**: sip.twilio.com
- **Vonage (Nexmo)**: sip.nexmo.com
- **Bandwidth**: sip.bandwidth.com
- **Flowroute**: sip.flowroute.com

### 2. Audio Device Configuration

First, identify your audio device:
```bash
aplay -l
```

Output example:
```
card 1: Interface [USB Audio Interface], device 0: USB Audio [USB Audio]
```

Edit `config/audio_config.json`:

```json
{
  "audio_device_name": "USB Audio Interface",
  "audio_device_index": null,
  "output_channels": {
    "ifb_left": 0,
    "ifb_right": 1,
    "pl_left": 2,
    "pl_right": 3
  },
  "sample_rate": 48000,
  "buffer_size": 256,
  "latency": "low"
}
```

**Channel Mapping:**
- Channels 0-1: IFB output (stereo) - typically for talent/presenters
- Channels 2-3: PL output (stereo) - typically for crew/production

---

## Running the System

### Manual Start

```bash
cd ~/Desktop/PhoneSystem
python3 main.py
```

The GUI will appear in fullscreen mode on the touchscreen.

### Auto-Start on Boot

```bash
# Copy systemd service
sudo cp systemd/phonesystem.service /etc/systemd/system/

# Enable service
sudo systemctl enable phonesystem.service

# Start service
sudo systemctl start phonesystem.service

# Check status
sudo systemctl status phonesystem.service
```

### View Logs

```bash
# Application logs
tail -f logs/phone_system.log

# Systemd logs
journalctl -u phonesystem.service -f
```

---

## Testing

### 1. Test Audio Outputs

In the GUI:
1. Click "Test IFB" button - should hear 1kHz tone on IFB outputs
2. Click "Test PL" button - should hear 1kHz tone on PL outputs

Or from command line:
```bash
# Test speaker-test
speaker-test -D hw:1,0 -c 2 -t sine -f 1000
```

### 2. Test SIP Registration

Check logs for successful registration:
```bash
grep "Registered successfully" logs/phone_system.log
```

### 3. Make Test Call

1. Select Line 1 (click on line widget)
2. Enter a test phone number
3. Press CALL button
4. Verify call connects
5. Toggle audio routing (IFB/PL) during call
6. Hang up

---

## Troubleshooting

### Audio Issues

**No audio devices found:**
```bash
# Check USB connections
lsusb

# Check ALSA
aplay -l

# Check PulseAudio
pactl list sinks
```

**Audio latency too high:**
```bash
# Edit PulseAudio config
nano ~/.config/pulse/daemon.conf

# Set lower latency values
default-fragment-size-msec = 3

# Restart PulseAudio
pulseaudio -k && pulseaudio --start
```

### SIP Issues

**Registration fails:**
```bash
# Check network
ping sip.yourprovider.com

# Verify credentials
cat config/sip_config.json

# Check firewall
sudo ufw status

# Allow SIP if needed
sudo ufw allow 5060/udp
sudo ufw allow 10000:20000/udp  # RTP ports
```

**Call audio one-way:**
- Check NAT configuration with your SIP provider
- May need STUN server configuration
- Verify firewall allows RTP ports (10000-20000 UDP)

### Touchscreen Issues

**Touch not responding:**
```bash
# Check input devices
xinput list

# Calibrate
xinput_calibrator
```

**Display rotation:**
```bash
# Rotate display 180 degrees
xrandr --output DSI-1 --rotate inverted
```

### Performance Issues

**High CPU usage:**
```bash
# Check processes
top

# Reduce audio quality if needed
# Edit config/audio_config.json
"buffer_size": 512  # Increase from 256
```

---

## System Optimization

### 1. Disable Unnecessary Services

```bash
# Disable Bluetooth if not needed
sudo systemctl disable bluetooth

# Disable WiFi if using Ethernet
sudo systemctl disable wpa_supplicant
```

### 2. CPU Governor

```bash
# Set performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 3. Real-time Priority

Add user to audio group:
```bash
sudo usermod -aG audio $USER
```

Edit `/etc/security/limits.conf`:
```
@audio - rtprio 95
@audio - memlock unlimited
```

---

## Hardware Recommendations

### Audio Interfaces

**Budget:**
- Behringer UCA202 (2 channels) - requires USB hub for 4 outputs
- Behringer U-Control UCA222

**Recommended:**
- Behringer UMC404HD (4 outputs)
- Focusrite Scarlett 4i4 (4 outputs)
- PreSonus AudioBox USB 96

**Professional:**
- RME Babyface Pro FS
- MOTU M4
- Universal Audio Volt 476

### Touchscreens

**Official:**
- Raspberry Pi 7" Touchscreen Display (800x480)

**Alternative:**
- Waveshare 7" HDMI LCD (1024x600)
- Elecrow 7" Touchscreen (1024x600)

### Cases

- SmartiPi Touch 2 (for official touchscreen)
- Custom 3D printed enclosure

---

## Network Configuration

### Port Forwarding (if behind NAT)

Forward these ports to your Raspberry Pi:
- 5060/UDP - SIP signaling
- 10000-20000/UDP - RTP audio

### Static IP

Edit `/etc/netplan/50-cloud-init.yaml`:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

Apply:
```bash
sudo netplan apply
```

---

## Backup and Restore

### Backup Configuration

```bash
# Backup config files
tar -czf phoneystem-config-backup.tar.gz config/

# Backup entire system image
sudo dd if=/dev/mmcblk0 of=~/phoneystem-backup.img bs=4M status=progress
```

### Restore Configuration

```bash
# Restore config files
tar -xzf phonesystem-config-backup.tar.gz
```

---

## Support and Maintenance

### Updates

```bash
cd ~/Desktop/PhoneSystem
git pull
pip3 install -r requirements.txt --upgrade
sudo systemctl restart phonesystem.service
```

### Logs Rotation

Logs are stored in `logs/phone_system.log`. Configure logrotate:

Create `/etc/logrotate.d/phonesystem`:

```
/home/*/Desktop/PhoneSystem/logs/phone_system.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

## Production Deployment Checklist

- [ ] Ubuntu 22.04 LTS installed and updated
- [ ] Touchscreen working and calibrated
- [ ] USB audio interface connected and tested
- [ ] All 4 outputs verified (IFB L/R, PL L/R)
- [ ] SIP credentials configured
- [ ] Test call successful
- [ ] Audio routing tested (IFB and PL)
- [ ] Auto-start on boot enabled
- [ ] Static IP configured (if needed)
- [ ] Firewall rules configured
- [ ] Backup created
- [ ] Documentation accessible to operators

---

## License

MIT License - See LICENSE file for details
