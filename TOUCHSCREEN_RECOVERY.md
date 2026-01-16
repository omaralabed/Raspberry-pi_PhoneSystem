# Touchscreen Recovery Solutions

## Problem
The USB touchscreen (wch.cn USB2IIC_CTP_CONTROL) sometimes becomes unresponsive and requires a reboot to work again.

## Root Cause
This is a common issue with USB HID touchscreen devices where the USB connection or driver can hang, causing the touch input to stop working while the display continues to function normally.

## Solutions

### Option 1: Manual Reset (Quick Fix)
When the touchscreen stops working, run this command via SSH:
```bash
cd ~/ProComm
./reset_touchscreen.sh
```

This script will:
- Unbind the USB touchscreen driver
- Wait 1 second
- Rebind the USB touchscreen driver
- Restart the PhoneSystem service

**Much faster than a full reboot!**

### Option 2: Automatic Monitoring (Recommended)
Install the touchscreen monitor service to automatically detect and fix issues:

```bash
# Copy service file
sudo cp ~/ProComm/touchscreen-monitor.service /etc/systemd/system/

# Enable and start the service
sudo systemctl enable touchscreen-monitor
sudo systemctl start touchscreen-monitor

# Check status
sudo systemctl status touchscreen-monitor

# View logs
sudo journalctl -u touchscreen-monitor -f
```

The monitor service will:
- Check the touchscreen every 30 seconds
- Detect when it becomes unresponsive
- Automatically reset the USB device
- Restart the PhoneSystem service
- Log all actions to `/home/procomm/ProComm/touchscreen_monitor.log`

### Option 3: Sudoers Configuration (For Manual Script)
To run the reset script without password:

```bash
echo 'procomm ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/bus/usb/drivers/usbhid/unbind, /usr/bin/tee /sys/bus/usb/drivers/usbhid/bind, /bin/systemctl restart phonesystem' | sudo tee /etc/sudoers.d/procomm-touchscreen
sudo chmod 0440 /etc/sudoers.d/procomm-touchscreen
```

## Prevention Tips

1. **Use a powered USB hub** - The touchscreen may lose power if the Pi's USB power is insufficient
2. **Keep the USB cable secure** - Loose connections can cause intermittent issues
3. **Update firmware** - Check for Pi firmware updates: `sudo rpi-update`
4. **Increase USB power** - Add to `/boot/config.txt`:
   ```
   max_usb_current=1
   usb_max_current_enable=1
   ```

## Monitoring
Check the touchscreen device at any time:
```bash
# List input devices
ls -la /dev/input/

# Check touchscreen events
cat /proc/bus/input/devices | grep -A 10 "wch.cn"

# Test touch input
sudo evtest /dev/input/event0
```

## Device Information
- **Device**: wch.cn USB2IIC_CTP_CONTROL
- **Vendor ID**: 32d7
- **Product ID**: 0001
- **Event Device**: /dev/input/event0
- **USB Path**: usb-0000:01:00.0-1.3.1
