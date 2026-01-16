#!/bin/bash
# Helper script to update network configuration
# Must be run with sudo privileges

CONFIG_FILE="/tmp/procomm_network.conf"
CONFIG_TYPE="/tmp/procomm_network_type.txt"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Read the config type (netplan or dhcpcd)
if [ -f "$CONFIG_TYPE" ]; then
    TYPE=$(cat "$CONFIG_TYPE")
else
    TYPE="dhcpcd"
fi

if [ "$TYPE" == "netplan" ]; then
    # Netplan configuration
    NETPLAN_FILE="/etc/netplan/50-cloud-init.yaml"
    
    # Backup existing config
    cp "$NETPLAN_FILE" "${NETPLAN_FILE}.backup" 2>/dev/null || true
    
    # Copy new configuration
    cp "$CONFIG_FILE" "$NETPLAN_FILE"
    chmod 600 "$NETPLAN_FILE"
    
    # Apply netplan configuration
    netplan apply
    echo "Network configuration updated via Netplan"
else
    # dhcpcd configuration
    # Backup existing config
    cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup 2>/dev/null || true
    
    # Copy the configuration
    cp "$CONFIG_FILE" /etc/dhcpcd.conf
    
    # Restart appropriate service
    if systemctl is-active --quiet dhcpcd; then
        systemctl restart dhcpcd
    else
        systemctl restart networking 2>/dev/null || true
    fi
    echo "Network configuration updated via dhcpcd"
fi

echo "Network configuration applied successfully"
