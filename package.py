#!/usr/bin/env python3
"""
Packaging script for USB Camera Test Suite
Creates comprehensive distribution packages for all platforms
"""

import os
import sys
import shutil
import zipfile
import tarfile
import json
from pathlib import Path
from datetime import datetime
import argparse

class PackageBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.package_dir = self.project_dir / "packages"
        self.version = "1.0.0"
        self.app_name = "USB Camera Test Suite"

        # Create package directory
        self.package_dir.mkdir(exist_ok=True)

        # Clean previous packages
        self.clean_packages()

    def clean_packages(self):
        """Clean previous package builds"""
        if self.package_dir.exists():
            for item in self.package_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

    def create_source_package(self):
        """Create source code package"""
        print("📦 Creating source package...")

        package_name = f"usb-camera-test-suite-{self.version}-source"
        source_dir = self.package_dir / package_name

        # Create package directory
        source_dir.mkdir(exist_ok=True)

        # Files to include
        files_to_copy = [
            "camera_test_suite/",
            "assets/",
            "icons/",
            "templates/",
            "requirements.txt",
            "requirements-dev.txt",
            "setup.py",
            "pyinstaller.spec",
            "build.py",
            "package.py",
            "Makefile",
            "MANIFEST.in",
            "README.md",
            "INSTALL.md",
            "install.sh",
            "install.bat",
            "uninstall.sh",
            "uninstall.bat",
        ]

        # Copy files
        for file_path in files_to_copy:
            src = self.project_dir / file_path
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, source_dir / file_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, source_dir / file_path)

        # Create tarball
        tar_path = self.package_dir / f"{package_name}.tar.gz"
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(source_dir, arcname=package_name)

        # Clean up temporary directory
        shutil.rmtree(source_dir)

        print(f"   ✓ Source package: {tar_path}")
        return tar_path

    def create_windows_package(self):
        """Create Windows installation package"""
        print("🪟 Creating Windows package...")

        package_name = f"usb-camera-test-suite-{self.version}-windows"
        windows_dir = self.package_dir / package_name

        windows_dir.mkdir(exist_ok=True)

        # Files to include
        files_to_include = [
            "install.bat",
            "uninstall.bat",
            "README.md",
            "INSTALL.md",
            "requirements.txt",
            "camera_test_suite/",
            "assets/",
        ]

        # Copy files
        for file_path in files_to_include:
            src = self.project_dir / file_path
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, windows_dir / file_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, windows_dir / file_path)

        # Create Windows-specific README
        windows_readme = windows_dir / "README_WINDOWS.txt"
        with open(windows_readme, 'w') as f:
            f.write(f"""{self.app_name} v{self.version} - Windows Installation Package

INSTALLATION:
1. Right-click install.bat and select "Run as Administrator" (recommended)
   OR double-click install.bat to install for current user only

2. Follow the installation prompts

3. Launch from Desktop shortcut or Start Menu

REQUIREMENTS:
- Windows 10 or later
- Python 3.7+ (installer will guide you if not found)
- Camera connected to USB port

USAGE:
- Desktop: Use shortcuts created during installation
- Command Line: camera-test-gui (GUI) or camera-test-cli (command line)

UNINSTALLATION:
- Run uninstall.bat
- Or use "Uninstall" from Start Menu

For detailed instructions, see INSTALL.md

Support: https://github.com/your-repo/usb-camera-test-suite/issues
""")

        # Create ZIP package
        zip_path = self.package_dir / f"{package_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in windows_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(windows_dir.parent)
                    zf.write(file_path, arcname)

        # Clean up temporary directory
        shutil.rmtree(windows_dir)

        print(f"   ✓ Windows package: {zip_path}")
        return zip_path

    def create_macos_package(self):
        """Create macOS installation package"""
        print("🍎 Creating macOS package...")

        package_name = f"usb-camera-test-suite-{self.version}-macos"
        macos_dir = self.package_dir / package_name

        macos_dir.mkdir(exist_ok=True)

        # Files to include
        files_to_include = [
            "install.sh",
            "uninstall.sh",
            "README.md",
            "INSTALL.md",
            "requirements.txt",
            "camera_test_suite/",
            "assets/",
        ]

        # Copy files
        for file_path in files_to_include:
            src = self.project_dir / file_path
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, macos_dir / file_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, macos_dir / file_path)

        # Make scripts executable
        for script in ["install.sh", "uninstall.sh"]:
            script_path = macos_dir / script
            if script_path.exists():
                script_path.chmod(0o755)

        # Create macOS-specific README
        macos_readme = macos_dir / "README_MACOS.txt"
        with open(macos_readme, 'w') as f:
            f.write(f"""{self.app_name} v{self.version} - macOS Installation Package

INSTALLATION:
1. Open Terminal and navigate to this directory
2. Run: chmod +x install.sh && ./install.sh
3. Follow the installation prompts

REQUIREMENTS:
- macOS 10.15 (Catalina) or later
- Xcode Command Line Tools: xcode-select --install
- Camera connected to USB port

CAMERA PERMISSIONS:
Grant camera access in: System Preferences → Security & Privacy → Camera

USAGE:
- Applications folder: USB Camera Test Suite.app
- Command Line: camera-test-gui (GUI) or camera-test-cli (command line)

UNINSTALLATION:
Run: ./uninstall.sh

For detailed instructions, see INSTALL.md

Support: https://github.com/your-repo/usb-camera-test-suite/issues
""")

        # Create tarball
        tar_path = self.package_dir / f"{package_name}.tar.gz"
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(macos_dir, arcname=package_name)

        # Clean up temporary directory
        shutil.rmtree(macos_dir)

        print(f"   ✓ macOS package: {tar_path}")
        return tar_path

    def create_linux_package(self):
        """Create Linux installation package"""
        print("🐧 Creating Linux package...")

        package_name = f"usb-camera-test-suite-{self.version}-linux"
        linux_dir = self.package_dir / package_name

        linux_dir.mkdir(exist_ok=True)

        # Files to include
        files_to_include = [
            "install.sh",
            "uninstall.sh",
            "README.md",
            "INSTALL.md",
            "requirements.txt",
            "camera_test_suite/",
            "assets/",
        ]

        # Copy files
        for file_path in files_to_include:
            src = self.project_dir / file_path
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, linux_dir / file_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, linux_dir / file_path)

        # Make scripts executable
        for script in ["install.sh", "uninstall.sh"]:
            script_path = linux_dir / script
            if script_path.exists():
                script_path.chmod(0o755)

        # Create Linux-specific README
        linux_readme = linux_dir / "README_LINUX.txt"
        with open(linux_readme, 'w') as f:
            f.write(f"""{self.app_name} v{self.version} - Linux Installation Package

INSTALLATION:
1. Extract this archive
2. Open terminal in extracted directory
3. Run: chmod +x install.sh && ./install.sh
4. Follow the installation prompts

REQUIREMENTS:
- Python 3.7+
- OpenCV development libraries
- V4L utilities for camera support

For Ubuntu/Debian:
sudo apt update
sudo apt install python3 python3-pip python3-dev libopencv-dev v4l-utils

For Raspberry Pi:
Additional setup may be required. See INSTALL.md for details.

USAGE:
- Desktop: Look for "USB Camera Test Suite" in applications menu
- Command Line: camera-test-gui (GUI) or camera-test-cli (command line)

UNINSTALLATION:
Run: ./uninstall.sh

For detailed instructions, see INSTALL.md

Support: https://github.com/your-repo/usb-camera-test-suite/issues
""")

        # Create tarball
        tar_path = self.package_dir / f"{package_name}.tar.gz"
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(linux_dir, arcname=package_name)

        # Clean up temporary directory
        shutil.rmtree(linux_dir)

        print(f"   ✓ Linux package: {tar_path}")
        return tar_path

    def create_raspberry_pi_package(self):
        """Create Raspberry Pi specific package"""
        print("🍓 Creating Raspberry Pi package...")

        package_name = f"usb-camera-test-suite-{self.version}-raspberry-pi"
        rpi_dir = self.package_dir / package_name

        rpi_dir.mkdir(exist_ok=True)

        # Files to include (same as Linux but with Pi-specific configs)
        files_to_include = [
            "install.sh",
            "uninstall.sh",
            "README.md",
            "INSTALL.md",
            "requirements.txt",
            "camera_test_suite/",
            "assets/",
        ]

        # Copy files
        for file_path in files_to_include:
            src = self.project_dir / file_path
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, rpi_dir / file_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, rpi_dir / file_path)

        # Make scripts executable
        for script in ["install.sh", "uninstall.sh"]:
            script_path = rpi_dir / script
            if script_path.exists():
                script_path.chmod(0o755)

        # Create Raspberry Pi specific README
        rpi_readme = rpi_dir / "README_RASPBERRY_PI.txt"
        with open(rpi_readme, 'w') as f:
            f.write(f"""{self.app_name} v{self.version} - Raspberry Pi Installation Package

INSTALLATION:
1. Extract this archive
2. Open terminal in extracted directory
3. Run: chmod +x install.sh && ./install.sh
4. Reboot after installation: sudo reboot

REQUIREMENTS:
- Raspberry Pi OS (Bullseye or later recommended)
- Python 3.7+
- Camera module enabled in raspi-config
- USB camera connected

SETUP:
1. Enable camera: sudo raspi-config → Interface Options → Camera → Enable
2. Add user to video group: sudo usermod -a -G video $USER
3. Install system packages (installer handles this)

PERFORMANCE NOTES:
- For better performance, use a fast SD card (Class 10 or better)
- Consider increasing GPU memory split: sudo raspi-config → Advanced Options → Memory Split → 128
- For headless operation, use the CLI mode: camera-test-cli

USAGE:
- Desktop: Look for "USB Camera Test Suite" in applications menu
- Command Line: camera-test-gui (GUI) or camera-test-cli (command line)
- Headless: camera-test-cli --list-cameras

TROUBLESHOOTING:
- If camera not detected, check: lsusb | grep -i camera
- Test camera access: v4l2-ctl --list-devices
- Check permissions: ls -la /dev/video*

UNINSTALLATION:
Run: ./uninstall.sh

For detailed instructions, see INSTALL.md

Support: https://github.com/your-repo/usb-camera-test-suite/issues
""")

        # Create tarball
        tar_path = self.package_dir / f"{package_name}.tar.gz"
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(rpi_dir, arcname=package_name)

        # Clean up temporary directory
        shutil.rmtree(rpi_dir)

        print(f"   ✓ Raspberry Pi package: {tar_path}")
        return tar_path

    def create_package_manifest(self, packages):
        """Create manifest of all packages"""
        print("📋 Creating package manifest...")

        manifest = {
            "name": "USB Camera Test Suite",
            "version": self.version,
            "description": "Comprehensive hardware testing suite for WN-L2307k368 48MP USB camera",
            "created": datetime.now().isoformat(),
            "packages": {}
        }

        for package_path in packages:
            if package_path and package_path.exists():
                stat = package_path.stat()
                manifest["packages"][package_path.name] = {
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "checksum": self.calculate_checksum(package_path)
                }

        manifest_path = self.package_dir / "packages.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"   ✓ Package manifest: {manifest_path}")

    def calculate_checksum(self, file_path):
        """Calculate SHA256 checksum"""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def create_all_packages(self):
        """Create all distribution packages"""
        print(f"🚀 Creating all packages for {self.app_name} v{self.version}...")
        print("-" * 60)

        packages = []

        # Create all packages
        packages.append(self.create_source_package())
        packages.append(self.create_windows_package())
        packages.append(self.create_macos_package())
        packages.append(self.create_linux_package())
        packages.append(self.create_raspberry_pi_package())

        # Create manifest
        self.create_package_manifest(packages)

        # Summary
        print("-" * 60)
        print("✅ All packages created successfully!")
        print(f"\nPackages directory: {self.package_dir}")
        print("\nCreated packages:")

        total_size = 0
        for package_path in packages:
            if package_path and package_path.exists():
                size_mb = package_path.stat().st_size / (1024 * 1024)
                total_size += size_mb
                print(f"   📦 {package_path.name} ({size_mb:.1f} MB)")

        print(f"\nTotal size: {total_size:.1f} MB")

        return packages

def main():
    parser = argparse.ArgumentParser(description="Create distribution packages")
    parser.add_argument("--platform", choices=["windows", "macos", "linux", "raspberry-pi", "source", "all"],
                       default="all", help="Platform to package for")

    args = parser.parse_args()

    builder = PackageBuilder()

    if args.platform == "all":
        builder.create_all_packages()
    elif args.platform == "source":
        builder.create_source_package()
    elif args.platform == "windows":
        builder.create_windows_package()
    elif args.platform == "macos":
        builder.create_macos_package()
    elif args.platform == "linux":
        builder.create_linux_package()
    elif args.platform == "raspberry-pi":
        builder.create_raspberry_pi_package()

    return 0

if __name__ == "__main__":
    sys.exit(main())