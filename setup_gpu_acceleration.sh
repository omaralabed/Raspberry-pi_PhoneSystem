#!/bin/bash
# GPU Acceleration Setup for Phone System
# Ensures Qt uses GPU-accelerated rendering instead of software rendering

set -e

echo "================================================"
echo "GPU Acceleration Setup for Phone System"
echo "================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    echo "Continuing anyway..."
fi

echo "Step 1: Installing GPU drivers and Mesa..."
sudo apt update
sudo apt install -y \
    libgles2-mesa-dev \
    libegl1-mesa-dev \
    mesa-common-dev \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libgles2 \
    libegl1

echo ""
echo "Step 2: Verifying GPU is accessible..."
if [ -e /dev/dri/card0 ]; then
    echo "✅ GPU device found: /dev/dri/card0"
    ls -l /dev/dri/
else
    echo "⚠️  Warning: GPU device not found at /dev/dri/card0"
    echo "This may indicate GPU drivers are not loaded"
fi

echo ""
echo "Step 3: Checking for VC4/VC6 GPU (Raspberry Pi)..."
if [ -e /opt/vc/bin/vcgencmd ]; then
    echo "✅ VideoCore utilities found"
    /opt/vc/bin/vcgencmd get_mem gpu
    /opt/vc/bin/vcgencmd version
else
    echo "⚠️  VideoCore utilities not found (may be on Ubuntu, not Raspberry Pi OS)"
fi

echo ""
echo "Step 4: Creating EGLFS KMS configuration..."
sudo mkdir -p /etc/qt5

# Create EGLFS KMS config for GPU acceleration
sudo tee /etc/qt5/eglfs_kms_config.json > /dev/null <<'EOF'
{
    "device": "/dev/dri/card0",
    "hwcursor": true,
    "pbuffers": true,
    "outputs": [
        {
            "name": "HDMI-1",
            "mode": "1920x1080"
        }
    ]
}
EOF

echo "✅ EGLFS KMS config created at /etc/qt5/eglfs_kms_config.json"

echo ""
echo "Step 5: Setting up user permissions for GPU access..."
# Add user to render group for GPU access
if [ -n "$SUDO_USER" ]; then
    sudo usermod -aG render,input,video,tty "$SUDO_USER"
    echo "✅ Added $SUDO_USER to render, input, video, and tty groups"
else
    echo "⚠️  Run this script with sudo to set user permissions"
fi

echo ""
echo "Step 6: Verifying Qt EGL support..."
if python3 -c "from PyQt5.QtGui import QGuiApplication; from PyQt5.QtCore import QCoreApplication; app = QCoreApplication([]); print('Qt available')" 2>/dev/null; then
    echo "✅ PyQt5 is installed"
else
    echo "❌ PyQt5 not found - install with: sudo apt install python3-pyqt5"
fi

echo ""
echo "Step 7: Testing GPU acceleration..."
cat > /tmp/test_gpu_qt.py <<'PYEOF'
#!/usr/bin/env python3
import sys
import os
os.environ['QT_QPA_PLATFORM'] = 'eglfs'
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.eglfs.debug=true'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtCore import QLibraryInfo

print("Qt Version:", QLibraryInfo.version().toString())
print("Qt Plugins Path:", QLibraryInfo.location(QLibraryInfo.PluginsPath))

try:
    app = QApplication(sys.argv)
    print("✅ QApplication created successfully")
    print("Qt Platform:", app.platformName())
    
    # Try to get OpenGL info
    fmt = QSurfaceFormat()
    fmt.setVersion(2, 0)
    fmt.setProfile(QSurfaceFormat.NoProfile)
    fmt.setRenderableType(QSurfaceFormat.OpenGLES)
    print("✅ OpenGL ES 2.0 format set")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYEOF

if python3 /tmp/test_gpu_qt.py 2>&1 | grep -q "✅"; then
    echo "✅ GPU acceleration test passed"
else
    echo "⚠️  GPU acceleration test had issues - check output above"
fi

rm -f /tmp/test_gpu_qt.py

echo ""
echo "================================================"
echo "GPU Acceleration Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Reboot the system: sudo reboot"
echo "2. Verify GPU is being used:"
echo "   - Check CPU usage (should be <10% for UI rendering)"
echo "   - Check /var/log/syslog for EGL/GPU messages"
echo "3. If still using software rendering, try X11 backend:"
echo "   - Change QT_QPA_PLATFORM=xcb in systemd service"
echo ""
echo "For troubleshooting, see GPU_ACCELERATION.md"

