# Deployment Guide - Original PhoneSystem to Raspberry Pi

## Quick Deployment

### Option 1: Using rsync (Recommended - Only transfers changed files)

```bash
# From your Mac, in the PhoneSystem directory
cd /Users/viewvision/Desktop/PhoneSystem

# Transfer files (excludes cache, git, docs)
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude '*.md' \
    --exclude '*.sh' \
    --exclude 'docs/' \
    ./ procomm@192.168.1.221:~/PhoneSystem/
```

### Option 2: Using scp (Simple - Transfers all files)

```bash
# From your Mac
cd /Users/viewvision/Desktop/PhoneSystem

# Transfer entire folder
scp -r \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    . procomm@192.168.1.221:~/PhoneSystem/
```

### Option 3: Manual File Transfer

1. **Connect to Pi:**
   ```bash
   ssh procomm@192.168.1.221
   ```

2. **On Pi, create directory:**
   ```bash
   mkdir -p ~/PhoneSystem
   exit
   ```

3. **From Mac, transfer files:**
   ```bash
   cd /Users/viewvision/Desktop/PhoneSystem
   scp -r src/ config/ main.py requirements.txt systemd/ procomm@192.168.1.221:~/PhoneSystem/
   ```

---

## After Deployment

### 1. SSH to Pi and verify files:
```bash
ssh procomm@192.168.1.221
cd ~/PhoneSystem
ls -la
```

### 2. Check Python syntax:
```bash
python3 -m py_compile src/*.py src/gui/*.py main.py
```

### 3. Install/Update dependencies (if needed):
```bash
# Install Python packages
pip3 install -r requirements.txt

# Or if using system packages:
sudo apt install python3-pyqt5 python3-sounddevice python3-numpy
```

### 4. Restart the service:
```bash
sudo systemctl restart phonesystem
```

### 5. Check service status:
```bash
systemctl status phonesystem
```

### 6. View logs:
```bash
sudo journalctl -u phonesystem -f
```

---

## First Time Setup (if not already done)

If this is the first deployment, you may need to:

1. **Run the installer:**
   ```bash
   cd ~/PhoneSystem
   sudo python3 install.py
   ```

2. **Configure SIP settings:**
   ```bash
   nano config/sip_config.json
   ```

3. **Configure audio settings:**
   ```bash
   nano config/audio_config.json
   ```

4. **Enable and start service:**
   ```bash
   sudo systemctl enable phonesystem
   sudo systemctl start phonesystem
   ```

---

## Quick Deploy Script

I've created `deploy_to_pi.sh` for you. To use it:

```bash
cd /Users/viewvision/Desktop/PhoneSystem
chmod +x deploy_to_pi.sh
./deploy_to_pi.sh
```

This will:
- Test SSH connection
- Transfer files using rsync
- Verify Python syntax
- Restart the service
- Check service status

---

## Troubleshooting

**Connection refused:**
- Check Pi is powered on
- Verify IP: `ping 192.168.1.221`
- Check SSH is enabled: `sudo systemctl status ssh`

**Permission denied:**
- Check SSH key is set up: `ssh-copy-id procomm@192.168.1.221`
- Or use password: `ssh procomm@192.168.1.221`

**Service won't start:**
- Check logs: `sudo journalctl -u phonesystem -n 50`
- Verify config files exist: `ls -la config/`
- Check Python dependencies: `pip3 list | grep -E "PyQt5|sounddevice|numpy"`
