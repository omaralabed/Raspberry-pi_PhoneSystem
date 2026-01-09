#!/bin/bash
#
# COMPLETE SETUP SCRIPT - Run this ONCE on the Raspberry Pi
# This configures everything: kiosk mode, fast boot, and framebuffer GUI
#

set -e

echo "🚀🚀🚀 RASPBERRY PI PHONE SYSTEM - COMPLETE SETUP 🚀🚀🚀"
echo ""

# Step 1: Install updated service file
echo "📁 Step 1/5: Installing phonesystem service..."
sudo cp ~/ProComm/systemd/phonesystem.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/phonesystem.service
echo "   ✅ Service file installed"

# Step 2: Disable network wait (main cause of slow boot)
echo "⚡ Step 2/5: Disabling network wait services..."
sudo systemctl disable systemd-networkd-wait-online.service 2>/dev/null || true
sudo systemctl mask systemd-networkd-wait-online.service 2>/dev/null || true
sudo systemctl disable NetworkManager-wait-online.service 2>/dev/null || true
sudo systemctl mask NetworkManager-wait-online.service 2>/dev/null || true
echo "   ✅ Network wait disabled"

# Step 3: Disable unnecessary services for fast boot
echo "⚡ Step 3/5: Disabling unnecessary services..."
sudo systemctl disable bluetooth.service 2>/dev/null || true
sudo systemctl disable wpa_supplicant.service 2>/dev/null || true
sudo systemctl disable ModemManager.service 2>/dev/null || true
sudo systemctl disable avahi-daemon.service 2>/dev/null || true
sudo systemctl disable apt-daily.timer 2>/dev/null || true
sudo systemctl disable apt-daily-upgrade.timer 2>/dev/null || true
echo "   ✅ Unnecessary services disabled"

# Step 4: Reduce systemd timeouts
echo "⚙️  Step 4/5: Reducing systemd timeouts..."
sudo mkdir -p /etc/systemd/system.conf.d
cat <<EOF | sudo tee /etc/systemd/system.conf.d/timeout.conf >/dev/null
[Manager]
DefaultTimeoutStartSec=10s
DefaultTimeoutStopSec=10s
DefaultDeviceTimeoutSec=10s
EOF
echo "   ✅ Timeouts set to 10 seconds"

# Step 5: Disable login prompts and enable kiosk mode
echo "🖥️  Step 5/5: Configuring kiosk mode (no login)..."
sudo systemctl mask getty@tty1.service 2>/dev/null || true
sudo systemctl set-default multi-user.target
echo "   ✅ Kiosk mode configured"

# Step 6: Enable and start the service
echo "🔄 Step 6/5: Enabling phonesystem service..."
sudo systemctl daemon-reload
sudo systemctl enable phonesystem.service
sudo systemctl restart phonesystem.service
echo "   ✅ Service enabled and started"

# Wait a moment for service to start
sleep 2

# Check service status
echo ""
echo "📊 Service Status:"
sudo systemctl status phonesystem.service --no-pager -l | head -15

echo ""
echo "✅✅✅ SETUP COMPLETE! ✅✅✅"
echo ""
echo "Configuration applied:"
echo "  ✓ GUI will display on framebuffer (/dev/fb0)"
echo "  ✓ Full screen on your Dell monitor"
echo "  ✓ No login prompt - boots straight to GUI"
echo "  ✓ Fast boot (network waits disabled)"
echo "  ✓ All unnecessary services disabled"
echo ""
echo "🔄 REBOOT NOW to see the phone system start automatically:"
echo "   sudo reboot"
echo ""
