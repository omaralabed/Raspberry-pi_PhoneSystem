#!/usr/bin/env python3
"""
Installation Script for Raspberry Pi Phone System
Ubuntu 22.04 LTS
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Installer:
    """Phone system installer for Ubuntu 22.04 LTS"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.errors = []
    
    def run_command(self, cmd: str, check=True) -> tuple:
        """Run shell command and return output"""
        try:
            logger.info(f"Running: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=True,
                text=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr
    
    def check_ubuntu_version(self) -> bool:
        """Verify Ubuntu 22.04 LTS"""
        logger.info("Checking Ubuntu version...")
        
        returncode, stdout, stderr = self.run_command("lsb_release -a", check=False)
        
        if "22.04" in stdout:
            logger.info("✓ Ubuntu 22.04 LTS detected")
            return True
        else:
            logger.warning("⚠ Not running Ubuntu 22.04 LTS - may have compatibility issues")
            return True  # Continue anyway
    
    def install_system_dependencies(self) -> bool:
        """Install system packages"""
        logger.info("Installing system dependencies...")
        
        packages = [
            # Build tools
            "build-essential",
            "cmake",
            "pkg-config",
            
            # Python development
            "python3-dev",
            "python3-pip",
            "python3-venv",
            
            # Audio libraries
            "libasound2-dev",
            "portaudio19-dev",
            "pulseaudio",
            "pavucontrol",
            
            # PyQt5 dependencies
            "python3-pyqt5",
            "python3-pyqt5.qtmultimedia",
            "pyqt5-dev-tools",
            
            # PJSIP dependencies
            "libssl-dev",
            "libsrtp2-dev",
            
            # Utilities
            "git",
            "wget",
            "curl",
        ]
        
        # Update package list
        returncode, _, _ = self.run_command("sudo apt-get update")
        if returncode != 0:
            self.errors.append("Failed to update package list")
            return False
        
        # Install packages
        packages_str = " ".join(packages)
        returncode, _, stderr = self.run_command(
            f"sudo apt-get install -y {packages_str}"
        )
        
        if returncode != 0:
            self.errors.append(f"Failed to install system packages: {stderr}")
            return False
        
        logger.info("✓ System dependencies installed")
        return True
    
    def install_pjsip(self) -> bool:
        """Install PJSIP from source with Python bindings"""
        logger.info("Installing PJSIP...")
        
        pjsip_dir = Path("/tmp/pjproject")
        
        # Clone PJSIP if not exists
        if not pjsip_dir.exists():
            logger.info("Downloading PJSIP...")
            returncode, _, _ = self.run_command(
                "git clone https://github.com/pjsip/pjproject.git /tmp/pjproject"
            )
            if returncode != 0:
                self.errors.append("Failed to clone PJSIP repository")
                return False
        
        # Build PJSIP
        os.chdir(pjsip_dir)
        
        commands = [
            "./configure --enable-shared --disable-video --disable-opencore-amr",
            "make dep",
            "make",
            "sudo make install",
        ]
        
        for cmd in commands:
            logger.info(f"Building PJSIP: {cmd}")
            returncode, _, stderr = self.run_command(cmd)
            if returncode != 0:
                self.errors.append(f"PJSIP build failed: {cmd}")
                logger.warning("PJSIP build may have failed, continuing...")
                break
        
        # Build Python bindings
        logger.info("Building PJSIP Python bindings...")
        os.chdir(pjsip_dir / "pjsip-apps" / "src" / "python")
        
        returncode, _, _ = self.run_command("sudo python3 setup.py install", check=False)
        if returncode != 0:
            logger.warning("⚠ PJSIP Python bindings installation may have failed")
            logger.info("You may need to install pjsua2 manually")
        else:
            logger.info("✓ PJSIP installed")
        
        # Return to base directory
        os.chdir(self.base_dir)
        return True
    
    def install_python_packages(self) -> bool:
        """Install Python packages from requirements.txt"""
        logger.info("Installing Python packages...")
        
        # Upgrade pip
        self.run_command("python3 -m pip install --upgrade pip")
        
        # Install requirements
        returncode, _, stderr = self.run_command(
            f"pip3 install -r {self.base_dir / 'requirements.txt'}"
        )
        
        if returncode != 0:
            self.errors.append(f"Failed to install Python packages: {stderr}")
            return False
        
        logger.info("✓ Python packages installed")
        return True
    
    def configure_audio(self) -> bool:
        """Configure PulseAudio for low latency"""
        logger.info("Configuring audio system...")
        
        # Create PulseAudio config directory
        pulse_dir = Path.home() / ".config" / "pulse"
        pulse_dir.mkdir(parents=True, exist_ok=True)
        
        # Create daemon.conf for low latency
        daemon_conf = pulse_dir / "daemon.conf"
        config = """
# Low latency configuration for phone system
default-sample-rate = 48000
alternate-sample-rate = 48000
default-fragments = 2
default-fragment-size-msec = 5
high-priority = yes
nice-level = -11
realtime-scheduling = yes
realtime-priority = 9
"""
        
        with open(daemon_conf, 'w') as f:
            f.write(config)
        
        logger.info("✓ Audio system configured")
        return True
    
    def create_systemd_service(self) -> bool:
        """Create systemd service for auto-start"""
        logger.info("Creating systemd service...")
        
        service_content = f"""[Unit]
Description=Raspberry Pi Phone System
After=network.target sound.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={self.base_dir}
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/{os.getenv('USER')}/.Xauthority"
ExecStart=/usr/bin/python3 {self.base_dir / 'main.py'}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical.target
"""
        
        service_dir = self.base_dir / "systemd"
        service_dir.mkdir(exist_ok=True)
        
        service_file = service_dir / "phonesystem.service"
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        logger.info(f"✓ Systemd service created: {service_file}")
        logger.info("To enable auto-start, run:")
        logger.info(f"  sudo cp {service_file} /etc/systemd/system/")
        logger.info("  sudo systemctl enable phonesystem.service")
        logger.info("  sudo systemctl start phonesystem.service")
        
        return True
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        logger.info("Creating directories...")
        
        dirs = [
            self.base_dir / "logs",
            self.base_dir / "config",
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(exist_ok=True)
            logger.info(f"  Created: {dir_path}")
        
        return True
    
    def verify_installation(self) -> bool:
        """Verify installation"""
        logger.info("Verifying installation...")
        
        # Check Python packages
        packages = ["PyQt5", "sounddevice", "numpy"]
        for package in packages:
            returncode, _, _ = self.run_command(
                f"python3 -c 'import {package}'",
                check=False
            )
            if returncode == 0:
                logger.info(f"  ✓ {package}")
            else:
                logger.warning(f"  ✗ {package} not found")
                self.errors.append(f"{package} not installed")
        
        # Check audio devices
        returncode, stdout, _ = self.run_command("aplay -l", check=False)
        if returncode == 0 and "card" in stdout:
            logger.info("  ✓ Audio devices found")
        else:
            logger.warning("  ⚠ No audio devices found")
        
        return len(self.errors) == 0
    
    def run(self) -> bool:
        """Run installation"""
        logger.info("="*60)
        logger.info("Raspberry Pi Phone System Installer")
        logger.info("Ubuntu 22.04 LTS")
        logger.info("="*60)
        
        steps = [
            ("Checking Ubuntu version", self.check_ubuntu_version),
            ("Creating directories", self.create_directories),
            ("Installing system dependencies", self.install_system_dependencies),
            ("Installing PJSIP", self.install_pjsip),
            ("Installing Python packages", self.install_python_packages),
            ("Configuring audio", self.configure_audio),
            ("Creating systemd service", self.create_systemd_service),
            ("Verifying installation", self.verify_installation),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n>>> {step_name}...")
            try:
                if not step_func():
                    logger.error(f"✗ {step_name} failed")
                    if self.errors:
                        logger.error("Errors:")
                        for error in self.errors:
                            logger.error(f"  - {error}")
                    return False
            except Exception as e:
                logger.error(f"✗ {step_name} failed with exception: {e}")
                return False
        
        logger.info("\n" + "="*60)
        logger.info("Installation completed successfully!")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Configure SIP credentials in config/sip_config.json")
        logger.info("2. Configure audio device in config/audio_config.json")
        logger.info("3. Run: python3 main.py")
        logger.info("\nFor auto-start on boot:")
        logger.info("  sudo cp systemd/phonesystem.service /etc/systemd/system/")
        logger.info("  sudo systemctl enable phonesystem.service")
        
        return True


def main():
    """Main entry point"""
    if os.geteuid() == 0:
        print("Don't run this script as root!")
        print("It will ask for sudo password when needed.")
        sys.exit(1)
    
    installer = Installer()
    success = installer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
