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
    echo -e "\n${BLUE}📦 Installing system dependencies...${NC}"

    case $PLATFORM in
        "macos")
            # Check for Homebrew
            if ! command_exists brew; then
                echo -e "${YELLOW}Installing Homebrew...${NC}"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi

            # Install system packages
            brew install python@3.11 pkg-config || true
            ;;

        "linux")
            # Detect package manager and install deps
            if command_exists apt-get; then
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip python3-venv python3-dev
                sudo apt-get install -y libopencv-dev python3-opencv
                sudo apt-get install -y libgtk-3-dev libcairo2-dev libgirepository1.0-dev
                sudo apt-get install -y v4l-utils uvcdynctrl
            elif command_exists yum; then
                sudo yum install -y python3 python3-pip python3-devel
                sudo yum install -y opencv-python3 gtk3-devel cairo-devel
                sudo yum install -y v4l-utils
            elif command_exists pacman; then
                sudo pacman -S --noconfirm python python-pip python-virtualenv
                sudo pacman -S --noconfirm opencv python-opencv gtk3 cairo
                sudo pacman -S --noconfirm v4l-utils
            else
                echo -e "${RED}❌ Unsupported Linux distribution${NC}"
                exit 1
            fi
            ;;

        "raspberry-pi")
            # Raspberry Pi specific setup
            echo -e "${GREEN}🍓 Setting up for Raspberry Pi...${NC}"
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev
            sudo apt-get install -y libopencv-dev python3-opencv
            sudo apt-get install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
            sudo apt-get install -y libgtk-3-dev libqt5gui5 libqt5webkit5-dev libqt5test5
            sudo apt-get install -y v4l-utils uvcdynctrl

            # Enable camera
            if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
                echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
            fi

            # Add user to video group
            sudo usermod -a -G video $USER
            ;;
    esac
}

# Function to check and install Python
setup_python() {
    echo -e "\n${BLUE}🐍 Setting up Python environment...${NC}"

    # Check Python version
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

        # Check if version is compatible (3.7+)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
            echo -e "${RED}❌ Python 3.7+ required, found $PYTHON_VERSION${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi

    # Check pip
    if ! command_exists pip3; then
        echo -e "${YELLOW}Installing pip3...${NC}"
        python3 -m ensurepip --default-pip
    fi

    # Upgrade pip
    python3 -m pip install --upgrade pip
}

# Function to create virtual environment
create_venv() {
    echo -e "\n${BLUE}📁 Creating virtual environment...${NC}"

    VENV_DIR="$HOME/.camera-test-suite"

    if [ -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Removing existing installation...${NC}"
        rm -rf "$VENV_DIR"
    fi

    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"

    # Upgrade pip in venv
    pip install --upgrade pip setuptools wheel

    echo -e "${GREEN}✅ Virtual environment created at $VENV_DIR${NC}"
}

# Function to install the application
install_app() {
    echo -e "\n${BLUE}📱 Installing USB Camera Test Suite...${NC}"

    # Install from current directory
    if [ -f "setup.py" ]; then
        echo -e "${GREEN}Installing from source...${NC}"
        pip install -e .
    else
        echo -e "${RED}❌ setup.py not found. Please run this script from the project directory.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Application installed successfully${NC}"
}

# Function to create desktop integration
create_desktop_integration() {
    echo -e "\n${BLUE}🖥️  Setting up desktop integration...${NC}"

    case $PLATFORM in
        "macos")
            create_macos_app
            ;;
        "linux"|"raspberry-pi")
            create_linux_desktop
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

    echo -e "${GREEN}✅ macOS app created at $APP_DIR${NC}"
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

    echo -e "${GREEN}✅ Desktop entry created${NC}"
}

# Function to create command-line shortcuts
create_cli_shortcuts() {
    echo -e "\n${BLUE}⚡ Creating command-line shortcuts...${NC}"

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
        echo "" >> "$HOME/.bashrc"
        echo "# USB Camera Test Suite" >> "$HOME/.bashrc"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"

        if [ -f "$HOME/.zshrc" ]; then
            echo "" >> "$HOME/.zshrc"
            echo "# USB Camera Test Suite" >> "$HOME/.zshrc"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.zshrc"
        fi
    fi

    echo -e "${GREEN}✅ Command shortcuts created${NC}"
}

# Function to test installation
test_installation() {
    echo -e "\n${BLUE}🧪 Testing installation...${NC}"

    source "$HOME/.camera-test-suite/bin/activate"

    # Test CLI
    if camera-test-cli --version >/dev/null 2>&1; then
        echo -e "${GREEN}✅ CLI interface working${NC}"
    else
        echo -e "${RED}❌ CLI interface failed${NC}"
        return 1
    fi

    # Test import
    if python -c "import camera_test_suite; print('Import successful')" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Python package import working${NC}"
    else
        echo -e "${RED}❌ Python package import failed${NC}"
        return 1
    fi

    return 0
}

# Main installation process
main() {
    echo -e "This will install $APP_NAME v$APP_VERSION on your system."
    echo -e "Platform: $PLATFORM"
    echo -e "Install mode: $INSTALL_MODE"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled.${NC}"
        exit 0
    fi

    echo -e "\n${BLUE}🚀 Starting installation...${NC}"

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
        echo -e "\n${GREEN}🎉 Installation completed successfully!${NC}"
        echo ""
        echo -e "${BLUE}Usage:${NC}"
        echo -e "  GUI Mode:   ${GREEN}camera-test-gui${NC}"
        echo -e "  CLI Mode:   ${GREEN}camera-test-cli${NC}"
        echo -e "  Help:       ${GREEN}camera-test-cli --help${NC}"
        echo ""
        echo -e "${YELLOW}Note: You may need to restart your terminal or run:${NC}"
        echo -e "${YELLOW}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        echo ""

        if [ "$PLATFORM" = "raspberry-pi" ]; then
            echo -e "${YELLOW}Raspberry Pi users: Please reboot to enable camera support.${NC}"
        fi
    else
        echo -e "\n${RED}❌ Installation failed during testing.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"