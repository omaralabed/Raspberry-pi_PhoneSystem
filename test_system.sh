#!/bin/bash
# Quick test script for phone system components

echo "================================"
echo "Phone System Component Test"
echo "================================"

# Check Python version
echo -e "\n[1/6] Checking Python version..."
python3 --version

# Check audio devices
echo -e "\n[2/6] Checking audio devices..."
aplay -l 2>/dev/null | grep "card" || echo "No audio devices found"

# Check network connectivity
echo -e "\n[3/6] Checking network..."
ping -c 3 8.8.8.8 >/dev/null 2>&1 && echo "✓ Internet connected" || echo "✗ No internet"

# Check PulseAudio
echo -e "\n[4/6] Checking PulseAudio..."
pactl info >/dev/null 2>&1 && echo "✓ PulseAudio running" || echo "✗ PulseAudio not running"

# Check Python packages
echo -e "\n[5/6] Checking Python packages..."
python3 -c "import PyQt5" 2>/dev/null && echo "✓ PyQt5" || echo "✗ PyQt5 not installed"
python3 -c "import sounddevice" 2>/dev/null && echo "✓ sounddevice" || echo "✗ sounddevice not installed"
python3 -c "import numpy" 2>/dev/null && echo "✓ numpy" || echo "✗ numpy not installed"
baresip -h >/dev/null 2>&1 && echo "✓ baresip" || echo "✗ baresip not installed (run: sudo apt install baresip)"

# Check config files
echo -e "\n[6/6] Checking configuration..."
[ -f "config/sip_config.json" ] && echo "✓ SIP config exists" || echo "✗ SIP config missing"
[ -f "config/audio_config.json" ] && echo "✓ Audio config exists" || echo "✗ Audio config missing"

echo -e "\n================================"
echo "Test complete!"
echo "================================"
