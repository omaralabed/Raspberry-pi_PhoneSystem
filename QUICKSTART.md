# Quick Start Guide

## Raspberry Pi Phone System - IFB/PL

**Production-ready 8-line phone system for broadcast and live events**

---

## 🚀 Quick Setup (5 Minutes)

### 1. Install System

```bash
cd ~/Desktop/PhoneSystem
python3 install.py
```

Wait 15-30 minutes for complete installation.

### 2. Configure SIP

Edit `config/sip_config.json`:

```json
{
  "sip_server": "sip.yourprovider.com",
  "username": "your_account",
  "password": "your_password",
  "caller_id_number": "+15551234567"
}
```

### 3. Configure Audio

Connect USB audio interface, then:

```bash
aplay -l
```

Note your device name, edit `config/audio_config.json`:

```json
{
  "audio_device_name": "USB Audio Interface"
}
```

### 4. Run!

```bash
python3 main.py
```

---

## 📞 Using the Phone System

### Making a Call

1. **Select Line**: Tap any available line (green)
2. **Enter Number**: Use on-screen dialer pad
3. **Press CALL**: Call will be placed
4. **Route Audio**: Tap 🔊 to toggle between IFB/PL
5. **Hang Up**: Press "Hang Up" button when done

### Audio Routing

- **IFB** (Blue): Interruptible Foldback - for talent/presenters
- **PL** (Orange): Private Line - for crew/production team

Each of 8 lines can route independently to either output!

### Line Status Colors

- 🟢 **Green**: Available (idle)
- 🟡 **Yellow**: Dialing/Ringing
- 🟢 **Bright Green**: Connected (active call)
- 🔵 **Blue**: Selected for dialing

---

## 🎚️ Hardware Connections

### Audio Interface Outputs

```
Output 1 (Left)  → IFB Left Channel   → Headphones/Mixer
Output 2 (Right) → IFB Right Channel  → Headphones/Mixer
Output 3 (Left)  → PL Left Channel    → Headphones/Mixer
Output 4 (Right) → PL Right Channel   → Headphones/Mixer
```

### Typical Production Setup

```
┌─────────────────┐
│  Phone System   │
│  (Raspberry Pi) │
└────────┬────────┘
         │ USB
    ┌────▼────┐
    │  Audio  │
    │Interface│
    └──┬───┬──┘
       │   │
   IFB │   │ PL
       │   │
    ┌──▼───▼──┐
    │  Mixer  │
    └─────────┘
```

---

## 🔧 Common Tasks

### Test Audio Outputs

Click "Test IFB" or "Test PL" in the GUI.

### View Logs

```bash
tail -f logs/phone_system.log
```

### Auto-Start on Boot

```bash
sudo cp systemd/phonesystem.service /etc/systemd/system/
sudo systemctl enable phonesystem.service
sudo systemctl start phonesystem.service
```

### Restart Service

```bash
sudo systemctl restart phonesystem.service
```

---

## 🆘 Troubleshooting

### No Audio Device Found

```bash
# Check USB connection
lsusb

# List audio devices
aplay -l

# Restart PulseAudio
pulseaudio -k && pulseaudio --start
```

### SIP Registration Fails

```bash
# Verify network
ping sip.yourprovider.com

# Check credentials
cat config/sip_config.json

# View SIP logs
grep "Registration" logs/phone_system.log
```

### Touchscreen Not Working

```bash
# Calibrate
sudo apt install xinput-calibrator
xinput_calibrator
```

### Can't Make Calls

1. Check SIP registration: Look for "Registered successfully" in logs
2. Verify account has outbound calling enabled
3. Check account balance with provider
4. Try different phone number format (+1XXXXXXXXXX)

---

## 📊 System Requirements

### Minimum

- Raspberry Pi 4 (4GB RAM)
- Ubuntu 22.04 LTS
- 7" Touchscreen (800x480)
- USB Audio Interface (4 outputs)
- 100 Mbps Internet

### Recommended

- Raspberry Pi 5 (8GB RAM)
- Official 7" Touchscreen
- Professional USB Audio Interface
- Gigabit Ethernet
- UPS Power Supply

---

## 📞 SIP Provider Setup

### Twilio

```json
{
  "sip_server": "sip.twilio.com",
  "username": "your_account_sid",
  "password": "your_auth_token",
  "caller_id_number": "+15551234567"
}
```

### Vonage (Nexmo)

```json
{
  "sip_server": "sip.nexmo.com",
  "username": "your_api_key",
  "password": "your_api_secret",
  "caller_id_number": "+15551234567"
}
```

---

## 🎓 Tips for Production Use

1. **Label Everything**: Mark IFB and PL outputs clearly
2. **Test Before Show**: Make test calls 30 minutes before
3. **Backup Internet**: Have 4G/5G hotspot ready
4. **Monitor Volume**: Use audio meters on mixer
5. **Practice Routing**: Train operators on IFB/PL switching
6. **Have Support Number**: Keep provider support handy

---

## 📚 More Information

- Full documentation: `README.md`
- Detailed installation: `INSTALLATION.md`
- Configuration examples: `config/` directory
- Logs: `logs/phone_system.log`

---

## 🤝 Support

For issues:
1. Check logs: `logs/phone_system.log`
2. Review `INSTALLATION.md` troubleshooting section
3. Verify all connections and configurations

---

**Ready to go? Run `python3 main.py` and start making calls!** 📞
