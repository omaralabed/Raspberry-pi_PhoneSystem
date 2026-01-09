#!/bin/bash
# Auto-deployment script for ProComm Phone System
# Pushes code from Mac to Raspberry Pi and restarts service

set -e  # Exit on error

PI_USER="procomm"
PI_HOST="100.100.196.210"
PI_DIR="~/ProComm"

echo "================================================"
echo "ProComm Phone System - Auto Deploy"
echo "================================================"
echo ""

# Step 1: Commit and push from Mac
echo "📦 Step 1: Committing changes locally..."
git add -A
if git diff --cached --quiet; then
    echo "   ℹ️  No changes to commit"
else
    read -p "   Enter commit message: " COMMIT_MSG
    git commit -m "$COMMIT_MSG"
    echo "   ✅ Changes committed"
fi

echo ""
echo "🚀 Step 2: Pushing to GitHub..."
git push origin main
echo "   ✅ Pushed to GitHub"

echo ""
echo "📥 Step 3: Pulling updates on Raspberry Pi..."
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && git stash && git pull origin main"
echo "   ✅ Code updated on Pi"

echo ""
echo "🔍 Step 4: Checking Python syntax..."
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && python3 -m py_compile src/*.py main.py"
echo "   ✅ Syntax check passed"

echo ""
echo "🔄 Step 5: Restarting service..."
ssh ${PI_USER}@${PI_HOST} "sudo systemctl restart phonesystem"
echo "   ✅ Service restarted"

echo ""
echo "📊 Step 6: Checking service status..."
ssh ${PI_USER}@${PI_HOST} "systemctl is-active phonesystem && echo '   ✅ Service is RUNNING' || echo '   ❌ Service is NOT running'"

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "View logs with: ssh ${PI_USER}@${PI_HOST} 'sudo journalctl -u phonesystem -f'"
