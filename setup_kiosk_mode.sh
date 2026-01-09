#!/bin/bash
#
# Kiosk Mode Setup Script for Raspberry Pi Phone System
# Run this ONCE on the Raspberry Pi to configure auto-start without login
#

set -e

echo "🔧 Configuring Raspberry Pi for kiosk mode (auto-start GUI)..."
echo ""

# Step 1: Copy service file
echo "📁 Step 1/4: Installing systemd service..."
sudo cp ~/ProComm/systemd/phonesystem.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/phonesystem.service
echo "   ✅ Service file installed"

# Step 2: Disable login prompts on all consoles
echo "🚫 Step 2/4: Disabling login prompts on virtual consoles..."
sudo systemctl mask getty@tty1.service
sudo systemctl mask serial-getty@ttyS0.service
sudo systemctl mask serial-getty@ttyAMA0.service 2>/dev/null || true
echo "   ✅ Login prompts disabled"

# Step 3: Set default boot target to multi-user (no graphical login)
echo "🎯 Step 3/4: Setting boot target to multi-user..."
sudo systemctl set-default multi-user.target
echo "   ✅ Boot target configured"

# Step 4: Enable and reload phonesystem service
echo "🔄 Step 4/4: Enabling phonesystem service..."
sudo systemctl daemon-reload
sudo systemctl enable phonesystem.service
sudo systemctl restart phonesystem.service
echo "   ✅ Service enabled and started"

echo ""
echo "✅ ✅ ✅ KIOSK MODE CONFIGURED! ✅ ✅ ✅"
echo ""
echo "The phone system will now:"
echo "  ✓ Start automatically on boot"
echo "  ✓ Display on the framebuffer without login"
echo "  ✓ Use full screen resolution (no hardcoded 800x480)"
echo ""
echo "🔄 PLEASE REBOOT NOW to test: sudo reboot"
echo ""
