# Phone System - Quick Reference Card

## 📞 SYSTEM OVERVIEW
```
┌─────────────────────────────────────────────────────────────┐
│  8 PHONE LINES → TOUCHSCREEN GUI → IFB/PL AUDIO ROUTING    │
│  Single Trunk • Outgoing Only • Real-time Control          │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 MAKING A CALL
```
1. TAP ────► Select available line (1-8)
2. DIAL ───► Enter phone number on keypad
3. CALL ───► Press green CALL button
4. ROUTE ──► Toggle 🔊 for IFB/PL selection
5. HANGUP ► Press Hang Up button when done
```

## 🎚️ AUDIO OUTPUTS
```
USB Audio Interface:
├─ Output 1 (Left)  ──► IFB Left  ──► Talent Headphones
├─ Output 2 (Right) ──► IFB Right ──► Talent Headphones
├─ Output 3 (Left)  ──► PL Left   ──► Crew Headphones
└─ Output 4 (Right) ──► PL Right  ──► Crew Headphones
```

## 🔵 LINE STATUS COLORS
```
🟢 GREEN (Light)  = Available/Idle
🟡 YELLOW         = Dialing/Ringing
🟢 GREEN (Bright) = Connected/Active
🔵 BLUE           = Selected for dialing
🔴 RED            = Error/Disconnected
```

## 🎧 IFB vs PL
```
IFB (Interruptible Foldback)  [Blue 🔵]
├─ For talent/presenters/hosts
├─ Can interrupt talent audio
└─ Usually more controlled environment

PL (Private Line)              [Orange 🟠]
├─ For crew/production/technical
├─ Internal production communication
└─ Coordination and technical direction
```

## ⚙️ ESSENTIAL COMMANDS

### Start System
```bash
cd ~/Desktop/PhoneSystem
python3 main.py
```

### View Logs
```bash
tail -f logs/phone_system.log
```

### Test Audio
```bash
# In GUI: Click "Test IFB" or "Test PL"
# Or command line:
speaker-test -D hw:1,0 -c 2 -t sine -f 1000
```

### Restart System
```bash
sudo systemctl restart phonesystem.service
```

### Check Service Status
```bash
sudo systemctl status phonesystem.service
```

## 🔧 CONFIGURATION FILES

### SIP Config: `config/sip_config.json`
```json
{
  "sip_server": "sip.yourprovider.com",
  "username": "account_id",
  "password": "password",
  "caller_id_number": "+15551234567",
  "num_lines": 8
}
```

### Audio Config: `config/audio_config.json`
```json
{
  "audio_device_name": "USB Audio Interface",
  "output_channels": {
    "ifb_left": 0,  "ifb_right": 1,
    "pl_left": 2,   "pl_right": 3
  },
  "sample_rate": 48000
}
```

## 🆘 TROUBLESHOOTING

### No Audio
```bash
aplay -l                    # List audio devices
pactl list sinks            # Check PulseAudio
pulseaudio -k && pulseaudio --start  # Restart audio
```

### SIP Registration Failed
```bash
ping sip.yourprovider.com   # Check connectivity
grep "Registration" logs/phone_system.log  # Check logs
```

### Touchscreen Not Working
```bash
xinput list                 # List input devices
xinput_calibrator           # Calibrate screen
```

### System Not Starting
```bash
journalctl -u phonesystem.service -f  # View service logs
python3 main.py             # Run manually to see errors
```

## 📊 SYSTEM REQUIREMENTS

### Hardware
- Raspberry Pi 4 (4GB) or Pi 5 (8GB)
- 7" Touchscreen (800x480+)
- USB Audio Interface (4+ outputs)
- Ethernet connection

### Software
- Ubuntu 22.04 LTS (ARM64)
- Python 3.10+
- PyQt5, PJSIP, PulseAudio

### Network
- Stable internet (1 Mbps per call)
- Open ports: 5060 UDP, 10000-20000 UDP

## 🎯 TYPICAL PRODUCTION SETUP

```
┌────────────────┐
│  Raspberry Pi  │
│  Phone System  │
└───────┬────────┘
        │ USB
   ┌────▼─────┐
   │  Audio   │
   │Interface │
   └─┬────┬───┘
     │    │
 IFB │    │ PL
     │    │
┌────▼────▼─────┐
│  Audio Mixer  │
└───────────────┘
     │    │
 Talent  Crew
  🎧    🎧
```

## 💾 BACKUP & RESTORE

### Backup Configuration
```bash
tar -czf phone-config-backup.tar.gz config/
```

### Restore Configuration
```bash
tar -xzf phone-config-backup.tar.gz
```

### Backup Full System
```bash
sudo dd if=/dev/mmcblk0 of=~/phone-backup.img bs=4M
```

## 📞 SIP PROVIDER EXAMPLES

### Twilio
```
Server: sip.twilio.com
Username: Account SID
Password: Auth Token
```

### Vonage
```
Server: sip.nexmo.com
Username: API Key
Password: API Secret
```

### Bandwidth
```
Server: sip.bandwidth.com
Username: Account ID
Password: API Token
```

## 🎓 OPERATOR TIPS

1. **Test Before Show** - Make test calls 30 min early
2. **Label Outputs** - Mark IFB and PL clearly
3. **Monitor Levels** - Watch audio meters
4. **Practice Routing** - Train on IFB/PL switching
5. **Keep Backup** - Have phone numbers written down
6. **Monitor Internet** - Keep 4G/5G backup ready

## 🔢 PORT FORWARDING (if needed)

### Router Configuration
```
SIP Signaling:  5060/UDP  → Raspberry Pi IP
RTP Audio:      10000-20000/UDP → Raspberry Pi IP
```

## 📁 FILE LOCATIONS

```
Application:   ~/Desktop/PhoneSystem/main.py
Logs:          ~/Desktop/PhoneSystem/logs/
Config:        ~/Desktop/PhoneSystem/config/
Service:       /etc/systemd/system/phonesystem.service
```

## 🚦 PRE-SHOW CHECKLIST

- [ ] System powered on and booted
- [ ] Touchscreen responsive
- [ ] Audio interface connected (check with `aplay -l`)
- [ ] Internet connected (check with `ping 8.8.8.8`)
- [ ] SIP registered (check logs)
- [ ] Test call successful
- [ ] IFB output tested
- [ ] PL output tested
- [ ] All 8 lines showing "Available"
- [ ] Backup internet connection ready

## 📚 DOCUMENTATION

| File | Purpose |
|------|---------|
| `QUICKSTART.md` | 5-minute setup guide |
| `README.md` | Full project documentation |
| `INSTALLATION.md` | Detailed installation steps |
| `ARCHITECTURE.md` | System design diagrams |

## 🆘 EMERGENCY CONTACTS

Keep handy:
- SIP Provider Support Number
- System Administrator Contact
- Audio Technician Contact
- IT Support Contact

---

## 💡 REMEMBER

**"One line, one number, eight channels of communication."**

- Each line can route independently to IFB or PL
- All lines use the same caller ID
- Toggle audio routing anytime during calls
- Monitor all lines simultaneously on touchscreen

---

## 🎉 QUICK REFERENCE COMPLETE

**Print this card and keep near your phone system!**

For full documentation, see README.md and INSTALLATION.md
