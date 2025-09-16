#!/bin/bash

# USB Camera Tester - Self-Contained Installation Script
# This script contains everything needed for installation

set -e

# Auto-make executable
if [ ! -x "${BASH_SOURCE[0]}" ]; then
    chmod +x "${BASH_SOURCE[0]}" 2>/dev/null || {
        echo "⚠️  Please run: chmod +x $(basename "${BASH_SOURCE[0]}")"
        echo "Then run: ./$(basename "${BASH_SOURCE[0]}")"
        exit 1
    }
fi

echo "🎥 USB Camera Tester Installation"
echo "=================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    echo "Detected OS: $OS"
else
    echo "Cannot detect OS. This script supports Ubuntu, Debian, and Raspberry Pi OS."
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt-get update -qq

# Install system dependencies
echo "🔧 Installing system dependencies..."

# Essential packages that should be available on all systems
ESSENTIAL_PACKAGES="python3 python3-pip python3-dev"

# Optional packages - install if available
OPTIONAL_PACKAGES="v4l-utils"

# Install essential packages
for package in $ESSENTIAL_PACKAGES; do
    if ! dpkg -l | grep -q "^ii  $package "; then
        echo "Installing $package..."
        sudo apt-get install -y $package
    else
        echo "$package is already installed"
    fi
done

# Install optional packages (don't fail if not available)
for package in $OPTIONAL_PACKAGES; do
    if apt-cache show $package >/dev/null 2>&1; then
        if ! dpkg -l | grep -q "^ii  $package "; then
            echo "Installing optional package $package..."
            sudo apt-get install -y $package || echo "Failed to install $package (optional)"
        else
            echo "$package is already installed"
        fi
    else
        echo "$package not available in repositories (optional)"
    fi
done

# Try to install OpenCV via apt first (faster), fallback to pip
echo "🎯 Installing OpenCV..."
if apt-cache show python3-opencv >/dev/null 2>&1; then
    sudo apt-get install -y python3-opencv || {
        echo "System OpenCV install failed, will use pip fallback"
        OPENCV_FROM_PIP=1
    }
else
    echo "System OpenCV not available, will install via pip"
    OPENCV_FROM_PIP=1
fi

# Install Python packages
echo "🐍 Installing Python packages..."

# Upgrade pip first
python3 -m pip install --user --upgrade pip

# Install minimal required packages
if [ "$OPENCV_FROM_PIP" = "1" ]; then
    echo "Installing OpenCV via pip (this may take a while)..."
    python3 -m pip install --user opencv-python
fi

# Try PyQt5 from system first, then pip
if apt-cache show python3-pyqt5 >/dev/null 2>&1; then
    sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtwidgets || {
        echo "System PyQt5 failed, installing via pip..."
        python3 -m pip install --user PyQt5
    }
else
    echo "Installing PyQt5 via pip..."
    python3 -m pip install --user PyQt5 || {
        echo "PyQt5 install failed - GUI will not be available"
        echo "CLI interface will still work"
    }
fi

# Install other Python dependencies
python3 -m pip install --user psutil numpy || {
    echo "Some Python packages failed to install"
    echo "Basic functionality should still work"
}

# Download and install the USB Camera Tester from current directory
echo "📥 Installing USB Camera Tester..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$SCRIPT_DIR/Kam" ]; then
    cd "$SCRIPT_DIR/Kam"
    python3 -m pip install --user -e .
else
    echo "❌ Error: Kam directory not found. Please ensure the installer is in the correct location."
    exit 1
fi

# Add user to video group if not already
if ! groups $USER | grep -q video; then
    echo "👤 Adding user to video group..."
    sudo usermod -a -G video $USER
    echo "⚠️  You need to log out and log back in for video group changes to take effect"
    NEED_LOGOUT=1
fi

# Create convenient launch scripts
echo "🚀 Creating launch scripts..."
mkdir -p ~/.local/bin

# CLI launcher
cat > ~/.local/bin/usb-camera-tester << 'EOF'
#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")/../../.."
python3 -m usb_camera_tester.cli.main "$@"
EOF
chmod +x ~/.local/bin/usb-camera-tester

# GUI launcher
cat > ~/.local/bin/usb-camera-gui << 'EOF'
#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")/../../.."
python3 -m usb_camera_tester.gui.main_window "$@"
EOF
chmod +x ~/.local/bin/usb-camera-gui

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "🛤️  Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

echo ""
echo "✅ Installation completed!"
echo ""
echo "🎯 Quick Start:"
echo "  usb-camera-tester detect    # Detect cameras"
echo "  usb-camera-tester test      # Test all cameras"
echo "  usb-camera-gui              # Launch GUI"
echo ""
echo "📖 Full documentation: README.md"

if [ "$NEED_LOGOUT" = "1" ]; then
    echo ""
    echo "⚠️  IMPORTANT: You need to log out and log back in"
    echo "   for camera permissions to work properly"
fi

echo ""
echo "🧪 Test the installation:"
echo "  usb-camera-tester devices   # List video devices"
echo ""