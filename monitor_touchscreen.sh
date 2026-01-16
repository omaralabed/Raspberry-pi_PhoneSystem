#!/bin/bash
# Touchscreen Monitor and Auto-Recovery Script
# This script monitors the touchscreen and resets it if it becomes unresponsive

LOG_FILE="/home/procomm/ProComm/touchscreen_monitor.log"
CHECK_INTERVAL=30  # Check every 30 seconds
TOUCH_DEVICE="/dev/input/event0"  # Main touchscreen device

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_touchscreen() {
    # Check if the touch device exists and is readable
    if [ ! -e "$TOUCH_DEVICE" ]; then
        log "ERROR: Touch device $TOUCH_DEVICE not found!"
        return 1
    fi
    
    # Check if device is accessible
    if [ ! -r "$TOUCH_DEVICE" ]; then
        log "ERROR: Touch device $TOUCH_DEVICE not readable!"
        return 1
    fi
    
    # Check for recent events (timeout after 2 seconds)
    timeout 2 cat "$TOUCH_DEVICE" > /dev/null 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 124 ]; then
        # Timeout - no data received, but device is responsive
        return 0
    elif [ $exit_code -eq 0 ]; then
        # Data received - device is working
        return 0
    else
        # Error reading device
        log "ERROR: Failed to read from touch device (exit code: $exit_code)"
        return 1
    fi
}

reset_usb_device() {
    log "Attempting to reset USB touchscreen..."
    
    # Find the USB device path for the touchscreen
    USB_PATH=$(udevadm info --name="$TOUCH_DEVICE" | grep "ID_PATH=" | cut -d'=' -f2)
    
    if [ -z "$USB_PATH" ]; then
        log "ERROR: Could not find USB path for touchscreen"
        return 1
    fi
    
    log "USB Path: $USB_PATH"
    
    # Unbind and rebind the USB device
    for i in /sys/bus/usb/drivers/*/*; do
        if [[ $(basename "$i") == *"1.3.1"* ]]; then
            DEVICE=$(basename "$i")
            DRIVER=$(dirname "$i")
            
            log "Unbinding USB device: $DEVICE"
            echo "$DEVICE" > "$DRIVER/unbind" 2>/dev/null
            sleep 2
            
            log "Rebinding USB device: $DEVICE"
            echo "$DEVICE" > "$DRIVER/bind" 2>/dev/null
            sleep 2
            
            log "USB touchscreen reset complete"
            return 0
        fi
    done
    
    log "ERROR: Could not reset USB device"
    return 1
}

restart_phonesystem() {
    log "Restarting phonesystem service..."
    systemctl restart phonesystem
    sleep 3
    log "PhoneSystem service restarted"
}

# Main monitoring loop
log "=== Touchscreen Monitor Started ==="

FAILURE_COUNT=0
MAX_FAILURES=3

while true; do
    if ! check_touchscreen; then
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        log "Touch check failed ($FAILURE_COUNT/$MAX_FAILURES)"
        
        if [ $FAILURE_COUNT -ge $MAX_FAILURES ]; then
            log "Max failures reached - attempting recovery"
            
            # Try to reset the USB device
            if reset_usb_device; then
                log "USB reset successful - restarting application"
                restart_phonesystem
                FAILURE_COUNT=0
                sleep 10
            else
                log "USB reset failed - waiting before retry"
                sleep 5
            fi
        fi
    else
        if [ $FAILURE_COUNT -gt 0 ]; then
            log "Touch check passed - resetting failure count"
        fi
        FAILURE_COUNT=0
    fi
    
    sleep $CHECK_INTERVAL
done
