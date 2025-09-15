# Installation Guide - USB Camera Test Suite

## Quick Install (Recommended)

### macOS & Linux
```bash
# Make installer executable and run
chmod +x install.sh
./install.sh
```

### Windows
```cmd
# Run installer as Administrator (recommended) or normal user
install.bat
```

### Universal Python Install
```bash
# Install directly from source
pip install -e .

# Or install with all dependencies
pip install -r requirements.txt
python setup.py install
```

---

## Installation Options

### Option 1: Automated Installer (Recommended)

The automated installers handle everything for you:
- ✅ Python environment setup
- ✅ Dependency installation
- ✅ Desktop integration
- ✅ Command-line tools
- ✅ System integration
- ✅ Uninstaller creation

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/usb-camera-test-suite/main/install.sh | bash
```

**Windows:**
Download and run `install.bat` as Administrator.

### Option 2: Manual Installation

1. **Install Python 3.7+**
   ```bash
   # Check Python version
   python3 --version
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install package**
   ```bash
   pip install -e .
   ```

4. **Run application**
   ```bash
   # GUI mode
   python -m camera_test_suite

   # CLI mode
   python -m camera_test_suite.cli --help
   ```

### Option 3: Standalone Executable

Download pre-built executables from the [Releases](https://github.com/your-repo/releases) page:

- **Windows:** `usb-camera-test-suite-windows.zip`
- **macOS:** `usb-camera-test-suite-macos.tar.gz`
- **Linux:** `usb-camera-test-suite-linux.tar.gz`

Extract and run the executable directly.

---

## Platform-Specific Instructions

### macOS

**Prerequisites:**
- macOS 10.15 (Catalina) or later
- Xcode Command Line Tools: `xcode-select --install`

**Installation:**
```bash
# Automated install
./install.sh

# Manual install
brew install python@3.11
pip3 install -r requirements.txt
python3 setup.py install
```

**Camera Permissions:**
- Grant camera access in System Preferences → Security & Privacy → Camera

### Windows

**Prerequisites:**
- Windows 10 or later
- Python 3.7+ from [python.org](https://python.org)
- Visual C++ Build Tools (for some packages)

**Installation:**
```cmd
REM Run as Administrator for system-wide install
install.bat

REM Or manual install
pip install -r requirements.txt
python setup.py install
```

**Camera Permissions:**
- Grant camera access in Settings → Privacy → Camera

### Linux (Ubuntu/Debian)

**Prerequisites:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-dev
sudo apt install libopencv-dev python3-opencv
sudo apt install v4l-utils uvcdynctrl
```

**Installation:**
```bash
./install.sh
```

### Raspberry Pi

**Prerequisites:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install libopencv-dev python3-opencv
sudo apt install libatlas-base-dev libhdf5-dev
sudo apt install v4l-utils

# Enable camera
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
```

**Installation:**
```bash
./install.sh
```

---

## Development Installation

For developers who want to contribute:

```bash
# Clone repository
git clone https://github.com/your-repo/usb-camera-test-suite.git
cd usb-camera-test-suite

# Install development dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Run tests
make test

# Run application
make dev
```

---

## Verification

After installation, verify everything works:

```bash
# Check installation
camera-test-cli --version

# List available cameras
camera-test-cli --list-cameras

# Run GUI
camera-test-gui

# Run quick test
make quick-test
```

---

## Build from Source

To build your own installers:

```bash
# Install build dependencies
pip install -r requirements-dev.txt

# Build Python packages
make build

# Build executable
make build-exe

# Build installer packages
make package

# Build everything
make all
```

---

## Troubleshooting

### Common Issues

**1. Camera Not Found**
```bash
# Check available cameras
ls /dev/video* (Linux)
system_profiler SPUSBDataType | grep -i camera (macOS)

# Check permissions
sudo usermod -a -G video $USER (Linux)
```

**2. Permission Denied**
```bash
# Fix permissions
chmod +x install.sh
sudo chown -R $USER:$USER ~/.camera-test-suite
```

**3. Python Version Issues**
```bash
# Use specific Python version
python3.9 -m pip install -r requirements.txt
python3.9 setup.py install
```

**4. Missing Dependencies**
```bash
# Install system packages
sudo apt install python3-dev libffi-dev (Linux)
brew install pkg-config (macOS)
```

### Getting Help

1. Check the [FAQ](FAQ.md)
2. Review [Common Issues](TROUBLESHOOTING.md)
3. Open an [Issue](https://github.com/your-repo/issues)
4. Check camera compatibility in [CAMERAS.md](CAMERAS.md)

---

## Uninstallation

### Automated Removal
```bash
# macOS/Linux
./uninstall.sh

# Windows
uninstall.bat
```

### Manual Removal
```bash
# Remove package
pip uninstall usb-camera-test-suite

# Remove installation directory
rm -rf ~/.camera-test-suite

# Remove command shortcuts
rm ~/.local/bin/camera-test-*

# Remove desktop entries (Linux)
rm ~/.local/share/applications/usb-camera-test-suite.desktop
```

---

## Next Steps

After installation:

1. **Connect your WN-L2307k368 camera**
2. **Run the GUI**: `camera-test-gui`
3. **Select your camera** in the Camera Control tab
4. **Run hardware tests** in the Hardware Tests tab
5. **Export results** in the Test Results tab

See the [User Guide](USER_GUIDE.md) for detailed usage instructions.