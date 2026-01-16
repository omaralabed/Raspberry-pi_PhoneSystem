#!/bin/bash
#
# Direct Deployment Script for PhoneSystem to Raspberry Pi
# Deploys the original PhoneSystem folder to the Pi
#

set -e  # Exit on error

# Configuration
PI_USER="procomm"
PI_HOST="192.168.1.221"
PI_DIR="~/PhoneSystem"
LOCAL_DIR="/Users/viewvision/Desktop/PhoneSystem"

echo "================================================"
echo "PhoneSystem - Direct Deployment to Pi"
echo "================================================"
echo ""
echo "Target: ${PI_USER}@${PI_HOST}"
echo "Remote Directory: ${PI_DIR}"
echo ""

# Step 1: Test SSH connection
echo "🔌 Step 1: Testing SSH connection..."
if ssh -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'Connection successful'" 2>/dev/null; then
    echo "   ✅ SSH connection successful"
else
    echo "   ❌ Cannot connect to ${PI_USER}@${PI_HOST}"
    echo "   Please check:"
    echo "   - Pi is powered on and connected to network"
    echo "   - IP address is correct (192.168.1.221)"
    echo "   - SSH is enabled on Pi"
    exit 1
fi

echo ""
echo "📦 Step 2: Transferring files to Raspberry Pi..."
echo "   This may take a few moments..."

# Use rsync for efficient file transfer (only changed files)
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude '*.md' \
    --exclude '*.sh' \
    --exclude 'docs/' \
    "${LOCAL_DIR}/" ${PI_USER}@${PI_HOST}:${PI_DIR}/

echo "   ✅ Files transferred"

echo ""
echo "🔍 Step 3: Verifying Python syntax on Pi..."
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && python3 -m py_compile src/*.py src/gui/*.py main.py 2>&1" || {
    echo "   ⚠️  Syntax check found issues (may be warnings)"
}

echo ""
echo "🔄 Step 4: Restarting phonesystem service..."
if ssh ${PI_USER}@${PI_HOST} "sudo systemctl restart phonesystem" 2>/dev/null; then
    echo "   ✅ Service restarted"
else
    echo "   ⚠️  Could not restart service (may not be installed yet)"
    echo "   To install service, run on Pi:"
    echo "   cd ${PI_DIR} && sudo python3 install.py"
fi

echo ""
echo "📊 Step 5: Checking service status..."
ssh ${PI_USER}@${PI_HOST} "systemctl is-active phonesystem 2>/dev/null && echo '   ✅ Service is RUNNING' || echo '   ⚠️  Service is not running (check logs)'"

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "To view logs:"
echo "  ssh ${PI_USER}@${PI_HOST} 'sudo journalctl -u phonesystem -f'"
echo ""
echo "To check service status:"
echo "  ssh ${PI_USER}@${PI_HOST} 'systemctl status phonesystem'"
echo ""
