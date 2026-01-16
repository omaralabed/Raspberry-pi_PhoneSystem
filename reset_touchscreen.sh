#!/bin/bash
# Quick USB Touchscreen Reset Script
# Run this manually if touchscreen stops working

echo "Resetting USB Touchscreen..."

# Find and reset the touchscreen USB device
for device in /sys/bus/usb/drivers/usbhid/*; do
    if [[ -d "$device" && $(basename "$device") == *"1.3.1"* ]]; then
        DEVICE=$(basename "$device")
        echo "Found touchscreen device: $DEVICE"
        
        # Unbind
        echo "$DEVICE" | sudo tee /sys/bus/usb/drivers/usbhid/unbind > /dev/null
        sleep 1
        
        # Rebind
        echo "$DEVICE" | sudo tee /sys/bus/usb/drivers/usbhid/bind > /dev/null
        sleep 1
        
        echo "Touchscreen reset complete!"
        
        # Restart the phone system to reinitialize
        echo "Restarting PhoneSystem service..."
        sudo systemctl restart phonesystem
        
        echo "Done! Touchscreen should be working now."
        exit 0
    fi
done

echo "ERROR: Could not find touchscreen USB device"
exit 1
