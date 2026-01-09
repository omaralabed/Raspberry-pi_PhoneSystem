#!/bin/bash
#
# ProComm Phone System - One-Click Deployment Script
#
# This script pushes local changes to GitHub, then updates the application
# on the Raspberry Pi and restarts the service.
#
# It requires a one-time setup on the Pi for passwordless sudo.
# See `setup_passwordless_sudo.sh` for instructions.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
PI_USER="procomm"
PI_HOST="100.100.196.210"
PROJECT_DIR="~/ProComm"
SERVICE_NAME="phonesystem"

# --- Git Operations ---
echo "🚀 Step 1/3: Pushing latest changes to GitHub..."
git add -A
# Commit only if there are changes to commit.
if ! git diff-index --quiet HEAD; then
    git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi
git push origin main
echo "✅ Git push complete."
echo ""


# --- Remote Deployment on Pi ---
echo "� Step 2/3: Deploying updates to Raspberry Pi..."

ssh -t "${PI_USER}@${PI_HOST}" "
    set -e # Exit on error within the SSH session
    
    echo '  -> Connected to Pi.'
    
    echo '  -> Navigating to project directory...'
    cd ${PROJECT_DIR}
    
    echo '  -> Stashing local changes (if any)...'
    git stash
    
    echo '  -> Pulling latest code from GitHub...'
    git pull origin main
    
    echo '  -> Verifying Python syntax...'
    python3 -m py_compile src/*.py main.py
    
    echo '  -> Restarting service (requires passwordless sudo)...'
    sudo systemctl restart ${SERVICE_NAME}
    
    echo '  -> Service restarted.'
"
echo "✅ Remote deployment complete."
echo ""

echo "🎉🎉🎉 DEPLOYMENT FINISHED! 🎉🎉🎉"
echo ""
echo "To check service status, run:"
echo "  ssh ${PI_USER}@${PI_HOST} 'systemctl status ${SERVICE_NAME} --no-pager'"
