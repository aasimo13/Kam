#!/bin/bash

# Creates a desktop application that runs the installer when double-clicked

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create desktop file
cat > "$SCRIPT_DIR/USB-Camera-Tester-Installer.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=USB Camera Tester Installer
Comment=Install USB Camera Tester application
Exec=bash -c 'cd "$SCRIPT_DIR" && ./usb-camera-tester-installer.sh; echo "Press Enter to close..."; read'
Icon=camera-video
Terminal=true
Categories=System;Utility;
StartupNotify=true
EOF

# Make desktop file executable
chmod +x "$SCRIPT_DIR/USB-Camera-Tester-Installer.desktop"

echo "✅ Created desktop installer: USB-Camera-Tester-Installer.desktop"
echo "📋 You can now:"
echo "   • Double-click the .desktop file to run the installer"
echo "   • Copy it to ~/Desktop for easy access"
echo "   • Copy it to ~/.local/share/applications/ to add to applications menu"