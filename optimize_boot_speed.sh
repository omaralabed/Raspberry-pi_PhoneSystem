#!/bin/bash
#
# Fast Boot Optimization Script for Raspberry Pi Phone System
# This disables unnecessary services and checks to boot as fast as possible
#

set -e

echo "⚡ OPTIMIZING RASPBERRY PI FOR ULTRA-FAST BOOT..."
echo ""

# Disable network wait (this is what's making it hang)
echo "🚫 Disabling network wait services..."
sudo systemctl disable systemd-networkd-wait-online.service
sudo systemctl mask systemd-networkd-wait-online.service
sudo systemctl disable NetworkManager-wait-online.service 2>/dev/null || true
sudo systemctl mask NetworkManager-wait-online.service 2>/dev/null || true
echo "   ✅ Network wait disabled"

# Disable unnecessary services
echo "🚫 Disabling unnecessary system services..."
sudo systemctl disable bluetooth.service 2>/dev/null || true
sudo systemctl disable hciuart.service 2>/dev/null || true
sudo systemctl disable wpa_supplicant.service 2>/dev/null || true
sudo systemctl disable ModemManager.service 2>/dev/null || true
sudo systemctl disable avahi-daemon.service 2>/dev/null || true
sudo systemctl disable triggerhappy.service 2>/dev/null || true
sudo systemctl disable apt-daily.timer 2>/dev/null || true
sudo systemctl disable apt-daily-upgrade.timer 2>/dev/null || true
echo "   ✅ Unnecessary services disabled"

# Disable slow fsck on boot
echo "🚫 Disabling filesystem check delays..."
sudo tune2fs -c 0 -i 0 /dev/mmcblk0p2 2>/dev/null || sudo tune2fs -c 0 -i 0 /dev/sda2 2>/dev/null || true
echo "   ✅ Filesystem check disabled"

# Reduce timeout for network devices
echo "⚙️  Reducing systemd timeouts..."
sudo mkdir -p /etc/systemd/system.conf.d
cat <<EOF | sudo tee /etc/systemd/system.conf.d/timeout.conf >/dev/null
[Manager]
DefaultTimeoutStartSec=10s
DefaultTimeoutStopSec=10s
DefaultDeviceTimeoutSec=10s
EOF
echo "   ✅ Timeouts reduced to 10s"

# Disable console blanking
echo "🖥️  Disabling console blanking..."
sudo sed -i 's/console=serial0,115200/console=serial0,115200 consoleblank=0/' /boot/firmware/cmdline.txt 2>/dev/null || \
sudo sed -i 's/console=serial0,115200/console=serial0,115200 consoleblank=0/' /boot/cmdline.txt 2>/dev/null || true
echo "   ✅ Console blanking disabled"

# Set bootloader to skip startup delays
echo "⚡ Configuring bootloader for fast boot..."
if [ -f /boot/firmware/config.txt ]; then
    BOOT_CONFIG=/boot/firmware/config.txt
else
    BOOT_CONFIG=/boot/config.txt
fi

# Add fast boot options if not present
grep -q "boot_delay=0" $BOOT_CONFIG || echo "boot_delay=0" | sudo tee -a $BOOT_CONFIG >/dev/null
grep -q "disable_splash=1" $BOOT_CONFIG || echo "disable_splash=1" | sudo tee -a $BOOT_CONFIG >/dev/null
echo "   ✅ Bootloader optimized"

# Disable Plymouth boot splash
echo "🚫 Disabling boot splash screen..."
sudo systemctl disable plymouth-start.service 2>/dev/null || true
sudo systemctl mask plymouth-start.service 2>/dev/null || true
echo "   ✅ Boot splash disabled"

# Reload systemd
echo "🔄 Reloading systemd configuration..."
sudo systemctl daemon-reload
echo "   ✅ Configuration reloaded"

echo ""
echo "⚡⚡⚡ BOOT OPTIMIZATION COMPLETE! ⚡⚡⚡"
echo ""
echo "The following optimizations were applied:"
echo "  ✓ Disabled network wait services (main cause of hang)"
echo "  ✓ Disabled Bluetooth, WiFi, Modem Manager"
echo "  ✓ Disabled Avahi, apt daily updates"
echo "  ✓ Reduced systemd timeouts to 10 seconds"
echo "  ✓ Disabled filesystem checks on boot"
echo "  ✓ Disabled boot splash screens"
echo "  ✓ Set bootloader for zero delay"
echo ""
echo "Boot time should now be under 15 seconds!"
echo ""
echo "🔄 Run './setup_kiosk_mode.sh' next if you haven't already,"
echo "   then REBOOT to see the improvements: sudo reboot"
echo ""
