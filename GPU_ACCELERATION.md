# GPU Acceleration for Phone System

## Problem

The Phone System UI can become unresponsive on Raspberry Pi 4/5, especially at 1920x1080 resolution, because:

- **30% CPU usage** just to render 1920x1080 framebuffer
- Qt's **linuxfb backend uses software rendering** (no GPU acceleration)
- **Pi 4/5 GPU is not being utilized** for UI rendering

## Solution

Enable GPU-accelerated rendering using Qt's **EGLFS backend** with proper GPU drivers.

---

## Quick Setup

```bash
# Run the GPU acceleration setup script
sudo bash setup_gpu_acceleration.sh

# Reboot
sudo reboot
```

---

## Manual Setup

### 1. Install GPU Drivers and Mesa

```bash
sudo apt update
sudo apt install -y \
    libgles2-mesa-dev \
    libegl1-mesa-dev \
    mesa-common-dev \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libgles2 \
    libegl1
```

### 2. Verify GPU Device

```bash
# Check if GPU device exists
ls -l /dev/dri/

# Should see /dev/dri/card0
```

### 3. Create EGLFS KMS Configuration

```bash
sudo mkdir -p /etc/qt5

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
```

### 4. Update Systemd Service

The `phonesystem.service` file should already have these settings:

```ini
Environment=QT_QPA_PLATFORM=eglfs
Environment=QT_QPA_EGLFS_ALWAYS_SET_MODE=1
Environment=QT_QPA_EGLFS_INTEGRATION=eglfs_kms
Environment=QT_QPA_EGLFS_KMS_CONFIG=/etc/qt5/eglfs_kms_config.json
Environment=QT_OPENGL=es2
```

### 5. Set User Permissions

```bash
# Add user to render group for GPU access
sudo usermod -aG render,input,video,tty procomm
```

---

## Verification

### Check GPU is Being Used

```bash
# Monitor CPU usage (should be <10% for UI)
top

# Check if EGL/GPU libraries are loaded
ldd $(which python3) | grep -i egl

# Check system logs for GPU messages
journalctl -u phonesystem.service | grep -i egl
```

### Test GPU Acceleration

```bash
# Run test script
python3 -c "
import os
os.environ['QT_QPA_PLATFORM'] = 'eglfs'
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QLibraryInfo
app = QApplication([])
print('Platform:', app.platformName())
print('Qt Version:', QLibraryInfo.version().toString())
"
```

Expected output should show `eglfs` as the platform.

---

## Troubleshooting

### Issue: Still Using Software Rendering

**Symptoms:**
- High CPU usage (>20% for UI)
- UI is sluggish/unresponsive
- Logs show "software" or "llvmpipe" renderer

**Solutions:**

1. **Verify GPU device exists:**
   ```bash
   ls -l /dev/dri/
   ```

2. **Check GPU drivers are loaded:**
   ```bash
   dmesg | grep -i gpu
   lsmod | grep -i vc4
   ```

3. **Verify EGLFS config file:**
   ```bash
   cat /etc/qt5/eglfs_kms_config.json
   ```

4. **Try alternative EGLFS integration:**
   ```bash
   # In systemd service, try:
   Environment=QT_QPA_EGLFS_INTEGRATION=eglfs_kms_egldevice
   ```

5. **Use X11 backend as fallback:**
   ```bash
   # Change in systemd service:
   Environment=QT_QPA_PLATFORM=xcb
   # Requires X server to be running
   ```

### Issue: Black Screen / No Display

**Solutions:**

1. **Check framebuffer:**
   ```bash
   cat /proc/fb
   fbset
   ```

2. **Try different resolution:**
   ```bash
   # In eglfs_kms_config.json:
   "mode": "800x480"  # Try lower resolution first
   ```

3. **Check display connection:**
   ```bash
   /opt/vc/bin/tvservice -s
   ```

### Issue: Permission Denied on /dev/dri/card0

**Solution:**
```bash
sudo usermod -aG render procomm
# Then logout and login again, or reboot
```

### Issue: EGLFS Not Available

**Symptoms:**
- Error: "This application failed to start because no Qt platform plugin could be initialized"

**Solutions:**

1. **Install Qt EGLFS platform plugin:**
   ```bash
   sudo apt install qtbase5-dev qtbase5-private-dev
   ```

2. **Verify plugin exists:**
   ```bash
   find /usr/lib -name "*eglfs*" 2>/dev/null
   ```

3. **Check Qt plugin path:**
   ```bash
   python3 -c "from PyQt5.QtCore import QLibraryInfo; print(QLibraryInfo.location(QLibraryInfo.PluginsPath))"
   ```

---

## Alternative: X11 Backend with GPU Acceleration

If EGLFS doesn't work, use X11 with GPU acceleration:

### 1. Install X Server

```bash
sudo apt install xserver-xorg xserver-xorg-video-fbdev
```

### 2. Configure X Server for GPU

Create `/etc/X11/xorg.conf.d/99-gpu.conf`:

```conf
Section "Device"
    Identifier "GPU"
    Driver "modesetting"
    Option "AccelMethod" "glamor"
EndSection

Section "Screen"
    Identifier "Screen"
    Device "GPU"
EndSection
```

### 3. Update Systemd Service

```ini
Environment=QT_QPA_PLATFORM=xcb
Environment=DISPLAY=:0
```

### 4. Start X Server

```bash
sudo systemctl enable lightdm  # Or your display manager
```

---

## Performance Comparison

| Backend | CPU Usage (1920x1080) | GPU Usage | Responsiveness |
|---------|----------------------|-----------|----------------|
| **linuxfb** (software) | ~30% | 0% | Poor |
| **eglfs** (GPU) | <5% | 50-70% | Excellent |
| **xcb** (X11) | 5-10% | 30-50% | Good |

---

## Raspberry Pi Specific Notes

### Pi 4/5 GPU

- **VC4 (Pi 4)** or **VC6 (Pi 5)** GPU handles OpenGL ES 2.0
- EGLFS backend uses KMS (Kernel Mode Setting) for direct GPU access
- No X server needed for fullscreen applications

### Recommended Resolution

For best performance:
- **Pi 4**: Up to 1920x1080 @ 60Hz
- **Pi 5**: Up to 3840x2160 @ 60Hz (4K)

Lower resolutions = better performance:
- 800x480: Excellent (recommended for 7" touchscreen)
- 1280x720: Very Good
- 1920x1080: Good (requires GPU acceleration)

---

## References

- [Qt EGLFS Documentation](https://doc.qt.io/qt-5/embedded-linux.html#eglfs)
- [Raspberry Pi GPU Documentation](https://www.raspberrypi.com/documentation/computers/config_txt.html#gpu)
- [Mesa EGL Documentation](https://www.mesa3d.org/egl.html)

---

## Summary

✅ **GPU acceleration is CRITICAL** for responsive UI at 1920x1080  
✅ **EGLFS backend** provides direct GPU access without X server  
✅ **Mesa drivers** provide OpenGL ES 2.0 support  
✅ **Verify GPU is being used** - CPU should be <10% for UI rendering

If GPU acceleration is not working, the UI will be sluggish regardless of code optimizations.

