#!/bin/bash
# USB Camera Test Suite - Universal Installation Script
# Supports macOS, Linux, and Raspberry Pi

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Application info
APP_NAME="USB Camera Test Suite"
APP_VERSION="1.0.0"
PACKAGE_NAME="usb-camera-test-suite"

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}$APP_NAME Installer v$APP_VERSION${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Detect platform
PLATFORM=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        PLATFORM="raspberry-pi"
    else
        PLATFORM="linux"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
else
    echo -e "${RED}❌ Unsupported platform: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Detected platform: $PLATFORM${NC}"

# Check if running as root (not recommended except for system install)
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  Running as root. Installing system-wide.${NC}"
    INSTALL_MODE="system"
else
    echo -e "${GREEN}👤 Installing for current user.${NC}"
    INSTALL_MODE="user"
fi

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system dependencies
install_system_deps() {
    echo -e "${BLUE}📦 Installing dependencies...${NC}"

    case $PLATFORM in
        "macos")
            # Check for Homebrew and install if needed
            if ! command_exists brew; then
                echo "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/null
            fi

            # Install system packages silently
            brew install python@3.11 pkg-config >/dev/null 2>&1 || true
            ;;

        "linux")
            if command_exists apt-get; then
                sudo apt-get update -qq >/dev/null 2>&1
                sudo apt-get install -qq -y python3 python3-pip python3-venv python3-dev >/dev/null 2>&1
                sudo apt-get install -qq -y libopencv-dev python3-opencv >/dev/null 2>&1
                sudo apt-get install -qq -y libgtk-3-dev libcairo2-dev >/dev/null 2>&1
                sudo apt-get install -qq -y v4l-utils >/dev/null 2>&1
            elif command_exists yum; then
                sudo yum install -q -y python3 python3-pip python3-devel >/dev/null 2>&1
                sudo yum install -q -y opencv-python3 gtk3-devel >/dev/null 2>&1
                sudo yum install -q -y v4l-utils >/dev/null 2>&1
            elif command_exists pacman; then
                sudo pacman -S --noconfirm --quiet python python-pip python-virtualenv >/dev/null 2>&1
                sudo pacman -S --noconfirm --quiet opencv python-opencv gtk3 >/dev/null 2>&1
            else
                echo -e "${RED}❌ Unsupported Linux distribution${NC}"
                exit 1
            fi
            ;;

        "raspberry-pi")
            sudo apt-get update -qq >/dev/null 2>&1
            sudo apt-get install -qq -y python3 python3-pip python3-venv python3-dev >/dev/null 2>&1
            sudo apt-get install -qq -y libopencv-dev python3-opencv >/dev/null 2>&1
            sudo apt-get install -qq -y libgtk-3-dev v4l-utils >/dev/null 2>&1

            # Enable camera and add user to video group
            if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
                echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt >/dev/null
            fi
            sudo usermod -a -G video $USER >/dev/null 2>&1
            ;;
    esac
}

# Function to check and install Python
setup_python() {
    echo -e "${BLUE}🐍 Setting up Python...${NC}"

    # Quick Python check
    if ! command_exists python3; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi

    # Ensure pip is available
    if ! command_exists pip3; then
        python3 -m ensurepip --default-pip >/dev/null 2>&1
    fi

    # Upgrade pip silently
    python3 -m pip install --upgrade pip >/dev/null 2>&1
}

# Function to create virtual environment
create_venv() {
    echo -e "${BLUE}📁 Creating environment...${NC}"

    VENV_DIR="$HOME/.camera-test-suite"

    # Remove existing installation silently
    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
    fi

    # Create venv and install packages silently
    python3 -m venv "$VENV_DIR" >/dev/null 2>&1
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip setuptools wheel >/dev/null 2>&1
}

# Function to install the application
install_app() {
    echo -e "${BLUE}📱 Installing application...${NC}"

    # Install from current directory silently
    if [ -f "setup.py" ]; then
        pip install -e . >/dev/null 2>&1
    else
        echo -e "${RED}❌ setup.py not found. Run from project directory.${NC}"
        exit 1
    fi
}

# Function to create desktop integration
create_desktop_integration() {
    echo -e "${BLUE}🖥️  Setting up shortcuts...${NC}"

    case $PLATFORM in
        "macos")
            create_macos_app >/dev/null 2>&1
            ;;
        "linux"|"raspberry-pi")
            create_linux_desktop >/dev/null 2>&1
            ;;
    esac
}

# Function to create macOS app bundle
create_macos_app() {
    APPS_DIR="$HOME/Applications"
    APP_DIR="$APPS_DIR/USB Camera Test Suite.app"

    mkdir -p "$APP_DIR/Contents/MacOS"
    mkdir -p "$APP_DIR/Contents/Resources"

    # Create Info.plist
    cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>camera-test-suite</string>
    <key>CFBundleIdentifier</key>
    <string>com.cameratests.usb-camera-test-suite</string>
    <key>CFBundleName</key>
    <string>USB Camera Test Suite</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>This app needs camera access to test USB camera hardware.</string>
</dict>
</plist>
EOF

    # Create launcher script
    cat > "$APP_DIR/Contents/MacOS/camera-test-suite" << EOF
#!/bin/bash
source "$HOME/.camera-test-suite/bin/activate"
camera-test-gui
EOF
    chmod +x "$APP_DIR/Contents/MacOS/camera-test-suite"

    # Silently created
}

# Function to create Linux desktop entry
create_linux_desktop() {
    DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"

    cat > "$DESKTOP_DIR/usb-camera-test-suite.desktop" << EOF
[Desktop Entry]
Name=USB Camera Test Suite
Comment=Hardware testing for USB cameras
Exec=$HOME/.camera-test-suite/bin/camera-test-gui
Icon=camera-video
Terminal=false
Type=Application
Categories=Audio
Keywords=camera;test;hardware;usb;
StartupNotify=true
EOF

    chmod +x "$DESKTOP_DIR/usb-camera-test-suite.desktop"

    # Update desktop database
    if command_exists update-desktop-database; then
        update-desktop-database "$HOME/.local/share/applications"
    fi

    # Silently created
}

# Function to create command-line shortcuts
create_cli_shortcuts() {
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"

    # GUI launcher
    cat > "$BIN_DIR/camera-test-gui" << EOF
#!/bin/bash
source "$HOME/.camera-test-suite/bin/activate"
camera-test-gui "\$@"
EOF
    chmod +x "$BIN_DIR/camera-test-gui"

    # CLI launcher
    cat > "$BIN_DIR/camera-test-cli" << EOF
#!/bin/bash
source "$HOME/.camera-test-suite/bin/activate"
camera-test-cli "\$@"
EOF
    chmod +x "$BIN_DIR/camera-test-cli"

    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "" >> "$HOME/.bashrc" 2>/dev/null
        echo "# USB Camera Test Suite" >> "$HOME/.bashrc" 2>/dev/null
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc" 2>/dev/null

        if [ -f "$HOME/.zshrc" ]; then
            echo "" >> "$HOME/.zshrc" 2>/dev/null
            echo "# USB Camera Test Suite" >> "$HOME/.zshrc" 2>/dev/null
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.zshrc" 2>/dev/null
        fi
    fi
}

# Function to test installation
test_installation() {
    echo -e "${BLUE}🧪 Testing...${NC}"

    source "$HOME/.camera-test-suite/bin/activate"

    # Quick test - just check if import works
    if python -c "import camera_test_suite" >/dev/null 2>&1; then
        return 0
    else
        echo -e "${RED}❌ Installation failed${NC}"
        return 1
    fi
}

# Main installation process
main() {
    echo -e "Installing $APP_NAME v$APP_VERSION on $PLATFORM..."
    echo -e "\n${BLUE}🚀 Starting automatic installation...${NC}"

    # Install system dependencies
    install_system_deps

    # Setup Python
    setup_python

    # Create virtual environment
    create_venv

    # Install application
    install_app

    # Create desktop integration
    create_desktop_integration

    # Create CLI shortcuts
    create_cli_shortcuts

    # Test installation
    if test_installation; then
        echo -e "\n${GREEN}✅ Installation complete!${NC}"
        echo ""
        echo -e "Run: ${GREEN}camera-test-gui${NC}"

        if [ "$PLATFORM" = "raspberry-pi" ]; then
            echo -e "${YELLOW}Raspberry Pi: Reboot to enable camera support.${NC}"
        fi
    else
        exit 1
    fi
}

# Run main function
main "$@"