#!/bin/bash

# USB Camera Tester - Professional macOS Installer Builder
# Creates a distributable .app bundle for the installer

set -e

echo "🚀 Building USB Camera Tester Installer for macOS..."

# Configuration
INSTALLER_NAME="USB Camera Tester Installer"
BUNDLE_ID="com.usb-camera-tester.installer"
VERSION="2.0"
BUILD_DIR="installer_build"
INSTALLER_SCRIPT="USB_Camera_Tester_Installer.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Clean up any existing build
if [ -d "$BUILD_DIR" ]; then
    print_status "Cleaning up previous build..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"

# Check if installer script exists
if [ ! -f "$INSTALLER_SCRIPT" ]; then
    print_error "Installer script not found: $INSTALLER_SCRIPT"
    exit 1
fi

print_status "Creating application bundle structure..."

# Create app bundle structure
APP_BUNDLE="$BUILD_DIR/$INSTALLER_NAME.app"
CONTENTS_DIR="$APP_BUNDLE/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Copy the installer script
cp "$INSTALLER_SCRIPT" "$RESOURCES_DIR/"

# Create the launcher script
print_status "Creating launcher script..."

cat > "$MACOS_DIR/$INSTALLER_NAME" << 'EOF'
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCES_DIR="$SCRIPT_DIR/../Resources"

# Change to resources directory
cd "$RESOURCES_DIR"

# Launch the Python installer
if command -v python3 &> /dev/null; then
    python3 USB_Camera_Tester_Installer.py "$@"
elif command -v python &> /dev/null; then
    python USB_Camera_Tester_Installer.py "$@"
else
    osascript -e 'display dialog "Python is required but not installed. Please install Python 3.8 or later from python.org" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi
EOF

# Make launcher executable
chmod +x "$MACOS_DIR/$INSTALLER_NAME"

# Create Info.plist
print_status "Creating Info.plist..."

cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$INSTALLER_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleName</key>
    <string>$INSTALLER_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$INSTALLER_NAME</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 USB Camera Tester. All rights reserved.</string>
    <key>CFBundleDocumentTypes</key>
    <array/>
    <key>NSAppleEventsUsageDescription</key>
    <string>This installer needs to access system events to properly install the USB Camera Tester application.</string>
</dict>
</plist>
EOF

# Create an icon (using emoji for now, you can replace with an actual .icns file)
print_status "Creating application icon..."

# Create a simple icon using sips (macOS built-in tool)
# For a professional installer, you'd want to create a proper .icns file
cat > "$RESOURCES_DIR/create_icon.py" << 'EOF'
#!/usr/bin/env python3
import tkinter as tk
from tkinter import font
import sys

# Create a simple icon using tkinter
root = tk.Tk()
root.withdraw()  # Hide the main window

# Create a canvas for the icon
canvas = tk.Canvas(root, width=512, height=512, bg='white')

# Create a professional-looking icon
canvas.create_rectangle(50, 50, 462, 462, fill='#007AFF', outline='#005CBF', width=8)
canvas.create_text(256, 200, text='📹', font=('Arial', 120), fill='white')
canvas.create_text(256, 350, text='USB', font=('Arial', 40, 'bold'), fill='white')
canvas.create_text(256, 400, text='CAMERA', font=('Arial', 30, 'bold'), fill='white')
canvas.create_text(256, 430, text='TESTER', font=('Arial', 30, 'bold'), fill='white')

# Save as PostScript (can be converted to other formats)
canvas.postscript(file='icon.eps')

root.destroy()
EOF

# Run icon creation (optional)
cd "$RESOURCES_DIR"
if command -v python3 &> /dev/null; then
    python3 create_icon.py 2>/dev/null || true
fi
rm -f create_icon.py
cd - > /dev/null

print_status "Setting bundle permissions..."

# Set proper permissions
chmod -R 755 "$APP_BUNDLE"
chmod +x "$MACOS_DIR/$INSTALLER_NAME"

# Try to set extended attributes (quarantine removal)
print_status "Setting extended attributes..."
xattr -cr "$APP_BUNDLE" 2>/dev/null || true

# Create a disk image for distribution
print_status "Creating disk image for distribution..."

DMG_NAME="USB_Camera_Tester_Installer_v$VERSION.dmg"
DMG_TEMP="$BUILD_DIR/dmg_temp"

mkdir -p "$DMG_TEMP"
cp -R "$APP_BUNDLE" "$DMG_TEMP/"

# Create README for the DMG
cat > "$DMG_TEMP/README.txt" << 'EOF'
USB Camera Hardware Test Suite - Professional Installer

INSTALLATION INSTRUCTIONS:
1. Double-click "USB Camera Tester Installer.app"
2. Follow the on-screen instructions
3. The installer will automatically:
   - Download the latest version
   - Install all dependencies
   - Create the application bundle
   - Add to your Applications folder

SYSTEM REQUIREMENTS:
- macOS 10.14 or later
- Python 3.8 or later (will be prompted if missing)
- Administrator privileges for installation

WHAT'S INCLUDED:
- Comprehensive PDAF autofocus testing
- White balance and exposure validation
- Image quality analysis with sharpness metrics
- USB interface performance testing
- Automated report generation (PDF, JSON, CSV)
- Cross-platform compatibility

For support or issues, please visit:
https://github.com/aasimo13/Kam

© 2025 USB Camera Tester. All rights reserved.
EOF

# Create the DMG
if command -v hdiutil &> /dev/null; then
    hdiutil create -format UDZO -volname "USB Camera Tester Installer" -srcfolder "$DMG_TEMP" "$BUILD_DIR/$DMG_NAME"
    print_success "Disk image created: $BUILD_DIR/$DMG_NAME"
else
    print_warning "hdiutil not available, skipping DMG creation"
fi

# Clean up temp DMG folder
rm -rf "$DMG_TEMP"

print_success "Installation package built successfully!"

echo ""
echo "📦 Build Complete!"
echo "   App Bundle: $APP_BUNDLE"
echo "   Disk Image: $BUILD_DIR/$DMG_NAME"
echo ""
echo "🚀 To distribute:"
echo "   1. Share the .dmg file for easy installation"
echo "   2. Or share the .app bundle directly"
echo ""
echo "💡 The installer will:"
echo "   • Download latest version from GitHub"
echo "   • Install all Python dependencies"
echo "   • Create professional app bundle"
echo "   • Add to Applications folder"
echo "   • Set up desktop integration"
echo ""

# Test the installer (optional)
read -p "Would you like to test the installer now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Launching installer for testing..."
    open "$APP_BUNDLE"
fi

print_success "Build process complete! 🎉"