#!/usr/bin/env python3
"""
USB Camera Hardware Test Suite - Simple Native Installer
Uses native macOS dialogs instead of Tkinter for maximum compatibility
"""

import subprocess
import sys
import os
import urllib.request
import zipfile
import shutil
from pathlib import Path
import tempfile
import time
import ssl

class SimpleNativeInstaller:
    def __init__(self):
        self.installation_path = "/Applications"
        self.app_name = "USB Camera Tester"
        self.temp_dir = None

    def show_dialog(self, title, message, buttons=["OK"], default_button="OK"):
        """Show native macOS dialog"""
        button_list = '", "'.join(buttons)
        script = f'''
        display dialog "{message}" ¬
        buttons {{"{button_list}"}} ¬
        default button "{default_button}" ¬
        with title "{title}" ¬
        with icon note
        '''

        try:
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split(':')[-1].strip()
            return None
        except:
            return None

    def show_progress(self, message):
        """Show progress in Terminal and log file"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        # Also log to file for debugging when run as app bundle
        try:
            log_file = os.path.expanduser("~/Desktop/installer_debug.log")
            with open(log_file, "a") as f:
                f.write(log_message + "\n")
        except:
            pass

    def run_installation(self):
        """Run the complete installation with native dialogs"""

        # Welcome dialog
        welcome_msg = """Welcome to USB Camera Hardware Test Suite Installer!

This installer will:
• Download the latest version from GitHub
• Install all required Python dependencies
• Create a professional macOS application
• Install to your Applications folder

Click 'Install' to begin or 'Cancel' to exit."""

        result = self.show_dialog("USB Camera Tester Installer", welcome_msg,
                                ["Install", "Cancel"], "Install")

        # Debug what we actually got
        self.show_progress(f"Dialog result: {repr(result)}")

        if result != "Install":
            self.show_progress("Installation cancelled by user.")
            return

        print("\n🚀 USB Camera Hardware Test Suite - Installation Starting")
        print("=" * 60)

        try:
            self.temp_dir = tempfile.mkdtemp(prefix="usb_camera_installer_")
            self.show_progress(f"Created temporary directory: {self.temp_dir}")

            # Step 1: Check system requirements
            self.show_progress("Checking system requirements...")
            self.check_system_requirements()

            # Step 2: Download application
            self.show_progress("Downloading USB Camera Tester...")
            self.download_application()

            # Step 3: Install Python dependencies
            self.show_progress("Installing Python dependencies...")
            self.install_dependencies()

            # Step 4: Create application bundle
            self.show_progress("Creating application bundle...")
            self.create_app_bundle()

            # Step 5: Install to Applications
            self.show_progress("Installing to Applications folder...")
            self.install_to_applications()

            # Step 6: Complete
            self.show_progress("Installation completed successfully!")

            print("\n🎉 Installation Complete!")
            print(f"USB Camera Tester installed to: {self.final_app_path}")

            # Success dialog
            success_msg = """Installation completed successfully!

USB Camera Tester is now available in:
• Applications folder
• Launchpad
• Spotlight search

Would you like to launch the application now?"""

            result = self.show_dialog("Installation Complete", success_msg,
                                    ["Launch", "Don't Launch"], "Launch")

            if result == "button returned:Launch":
                subprocess.run(["open", self.final_app_path])

        except Exception as e:
            error_msg = f"Installation failed: {str(e)}"
            self.show_progress(error_msg)
            print(f"\n❌ {error_msg}")

            self.show_dialog("Installation Failed",
                           f"Installation encountered an error:\n\n{str(e)}\n\nPlease try again.",
                           ["OK"], "OK")
        finally:
            self.cleanup_temp_files()

    def check_system_requirements(self):
        """Check if system meets requirements"""
        result = subprocess.run([sys.executable, '--version'],
                               capture_output=True, text=True)
        if result.returncode == 0:
            python_version = result.stdout.strip()
            self.show_progress(f"Python version: {python_version}")
        else:
            raise Exception("Python installation not found")

    def download_application(self):
        """Download the latest version from GitHub"""
        github_url = "https://github.com/aasimo13/Kam/archive/refs/heads/main.zip"
        download_path = os.path.join(self.temp_dir, "usb_camera_tester.zip")

        self.show_progress(f"Downloading from: {github_url}")

        # Handle SSL certificate issues on macOS
        try:
            urllib.request.urlretrieve(github_url, download_path)
        except (ssl.SSLError, urllib.error.URLError) as e:
            self.show_progress(f"Download error: {e}")
            self.show_progress("Trying alternative download method...")

            try:
                # Create unverified SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(github_url, download_path)
            except Exception as e2:
                self.show_progress("SSL fallback failed, using curl...")

                # Use curl as final fallback
                result = subprocess.run([
                    "curl", "-L", "-k", "-o", download_path, github_url
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    raise Exception(f"Download failed: {result.stderr}")

        # Extract the downloaded file
        self.show_progress("Extracting downloaded files...")
        extract_path = os.path.join(self.temp_dir, "extracted")
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        self.source_path = os.path.join(extract_path, "Kam-main")

    def install_dependencies(self):
        """Install required Python dependencies"""
        packages = [
            "opencv-python",
            "numpy",
            "Pillow",
            "matplotlib",
            "psutil",
            "reportlab"
        ]

        for package in packages:
            self.show_progress(f"Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)

            if result.returncode == 0:
                self.show_progress(f"✓ Installed {package}")
            else:
                self.show_progress(f"✗ Failed to install {package}")

    def create_app_bundle(self):
        """Create proper macOS application bundle"""
        app_bundle_path = os.path.join(self.temp_dir, f"{self.app_name}.app")

        # Create app bundle structure
        contents_dir = os.path.join(app_bundle_path, "Contents")
        macos_dir = os.path.join(contents_dir, "MacOS")
        resources_dir = os.path.join(contents_dir, "Resources")

        os.makedirs(macos_dir, exist_ok=True)
        os.makedirs(resources_dir, exist_ok=True)

        # Copy application files
        app_source = os.path.join(self.source_path, "camera_test_suite")
        app_dest = os.path.join(resources_dir, "camera_test_suite")

        if not os.path.exists(app_source):
            raise Exception(f"Source application files not found at: {app_source}")

        shutil.copytree(app_source, app_dest)

        # Create launcher script
        launcher_script = '''#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCES_DIR="$SCRIPT_DIR/../Resources"

# Find Python executable
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    osascript -e 'display dialog "Python is required. Please install Python from python.org" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Change to a clean directory to avoid numpy source conflicts
cd "$HOME"

# Launch the application with full path
exec "$PYTHON_CMD" "$RESOURCES_DIR/camera_test_suite/main.py" "$@"
'''

        launcher_path = os.path.join(macos_dir, "USBCameraTester")
        with open(launcher_path, 'w') as f:
            f.write(launcher_script)
        os.chmod(launcher_path, 0o755)

        # Create Info.plist
        info_plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>USBCameraTester</string>
    <key>CFBundleIdentifier</key>
    <string>com.usb-camera-tester.app</string>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleVersion</key>
    <string>2.0</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>This app needs camera access to test USB camera hardware functionality.</string>
</dict>
</plist>'''

        plist_path = os.path.join(contents_dir, "Info.plist")
        with open(plist_path, 'w') as f:
            f.write(info_plist)

        self.app_bundle_path = app_bundle_path

    def install_to_applications(self):
        """Install the app bundle to Applications folder"""
        final_app_path = os.path.join(self.installation_path, f"{self.app_name}.app")

        # Remove existing installation if present
        if os.path.exists(final_app_path):
            self.show_progress("Removing existing installation...")
            shutil.rmtree(final_app_path)

        # Copy app bundle to Applications
        self.show_progress(f"Installing to {final_app_path}...")
        shutil.copytree(self.app_bundle_path, final_app_path)

        # Verify installation
        if os.path.exists(final_app_path):
            self.show_progress(f"✓ Successfully installed to {final_app_path}")
        else:
            raise Exception("Installation verification failed")

        self.final_app_path = final_app_path

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            self.show_progress("Cleaning up temporary files...")
            shutil.rmtree(self.temp_dir, ignore_errors=True)

if __name__ == "__main__":
    installer = SimpleNativeInstaller()
    installer.run_installation()