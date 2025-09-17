# USB Camera Tester - Professional macOS Installer

## 🚀 Quick Start

### For End Users
1. **Download**: Get the `USB_Camera_Tester_Installer_v2.0.dmg` file
2. **Mount**: Double-click the DMG to mount it
3. **Install**: Double-click "USB Camera Tester Installer.app"
4. **Follow**: The guided installation process

### For Developers/Distributors
1. **Build the installer**:
   ```bash
   ./build_installer.sh
   ```
2. **Distribute**: Share the generated `.dmg` file

---

## 📋 What the Installer Does

### Automatic Installation Process
1. **System Check**: Verifies macOS compatibility and Python installation
2. **Download**: Gets the latest version from GitHub repository
3. **Dependencies**: Installs all required Python packages:
   - OpenCV (camera operations)
   - NumPy (numerical processing)
   - Pillow (image handling)
   - Matplotlib (graphing)
   - PSUtil (system monitoring)
   - ReportLab (PDF generation)
4. **App Bundle**: Creates professional macOS application bundle
5. **Integration**: Installs to Applications folder with proper permissions
6. **Registration**: Registers with Launch Services for Spotlight/Launchpad

### Professional Features
- ✅ **Native macOS UI** with progress tracking
- ✅ **Detailed installation log** for troubleshooting
- ✅ **Automatic dependency management**
- ✅ **Proper app bundle creation** with Info.plist
- ✅ **Applications folder integration**
- ✅ **Launch Services registration**
- ✅ **Error handling and recovery**

---

## 🎯 End User Experience

### Installation Interface
```
📹 USB Camera Hardware Test Suite
Professional camera testing for WN-L2307k368 48MP modules
Version 2.0 - Production Ready

What's Included:
✓ Comprehensive PDAF autofocus testing
✓ White balance and exposure validation
✓ Image quality analysis with sharpness metrics
✓ USB interface performance testing
✓ Automated report generation (PDF, JSON, CSV)
✓ Cross-platform compatibility
✓ One-click installation with all dependencies

Installation Location: /Applications/USB Camera Tester.app

[████████████████████████████████████] 100%
Installation completed successfully!

[Install USB Camera Tester] [Cancel] [Show Log]
```

### Post-Installation
- **Application available in**:
  - Applications folder
  - Launchpad
  - Spotlight search
- **Desktop shortcut** (optional)
- **Automatic updates** through GitHub releases

---

## 🔧 Technical Details

### System Requirements
- **macOS**: 10.14 (Mojave) or later
- **Python**: 3.8+ (installer will guide if missing)
- **Disk Space**: ~200MB for complete installation
- **Permissions**: Administrator access for Applications folder

### File Structure
```
USB Camera Tester Installer.app/
├── Contents/
│   ├── Info.plist                 # App bundle metadata
│   ├── MacOS/
│   │   └── USB Camera Tester Installer  # Launcher script
│   └── Resources/
│       └── USB_Camera_Tester_Installer.py  # Main installer
```

### Security & Permissions
- **Code signing**: Ready for developer certificate
- **Notarization**: Prepared for Apple notarization
- **Gatekeeper**: Handles macOS security requirements
- **Camera access**: Requests permission for USB camera testing

---

## 🛠️ Build Process

### Prerequisites
```bash
# Ensure you have Python 3.8+
python3 --version

# Tkinter should be included with Python
python3 -c "import tkinter; print('Tkinter available')"
```

### Building the Installer
```bash
# Make build script executable (one time)
chmod +x build_installer.sh

# Build the installer
./build_installer.sh
```

### Build Output
```
installer_build/
├── USB Camera Tester Installer.app/     # Distributable app bundle
└── USB_Camera_Tester_Installer_v2.0.dmg # Disk image for distribution
```

---

## 📦 Distribution Options

### Option 1: Disk Image (Recommended)
- **File**: `USB_Camera_Tester_Installer_v2.0.dmg`
- **Benefits**: Professional presentation, includes documentation
- **Usage**: Double-click to mount, then run installer

### Option 2: App Bundle
- **File**: `USB Camera Tester Installer.app`
- **Benefits**: Direct execution, smaller file size
- **Usage**: Double-click to run installer

### Option 3: GitHub Releases
- Upload DMG to GitHub releases for automatic distribution
- Users can download directly from repository

---

## 🔍 Troubleshooting

### Common Issues

#### "Cannot open installer - unidentified developer"
**Solution**: Right-click installer → "Open" → "Open" in dialog

#### Python not found
**Solution**: Install Python from [python.org](https://python.org)

#### Permission denied during installation
**Solution**: Run installer with admin privileges

#### Installation fails on dependency
**Solution**: Check installation log for specific package errors

### Installation Log
The installer provides detailed logging:
```
[14:30:15] Checking system requirements...
[14:30:16] macOS version: 12.6
[14:30:16] Python version: Python 3.9.7
[14:30:17] Downloading from: https://github.com/aasimo13/Kam/archive/refs/heads/main.zip
[14:30:20] Extracting downloaded files...
[14:30:21] Installing Python packages...
[14:30:25] ✓ Installed opencv-python
...
```

---

## 🎉 Professional Features

### For End Users
- **One-click installation** - No technical knowledge required
- **Progress tracking** - Visual feedback during installation
- **Error recovery** - Graceful handling of issues
- **Professional UI** - Native macOS look and feel

### For Developers
- **GitHub integration** - Downloads latest version automatically
- **Modular design** - Easy to customize and extend
- **Logging system** - Detailed troubleshooting information
- **Cross-platform foundation** - Adaptable to Windows/Linux

### For IT Deployment
- **Silent installation** - Command-line options available
- **Enterprise ready** - Can be packaged for mass deployment
- **Update mechanism** - Built-in version checking
- **Uninstall support** - Clean removal process

---

## 📞 Support

- **GitHub Issues**: [https://github.com/aasimo13/Kam/issues](https://github.com/aasimo13/Kam/issues)
- **Documentation**: This README and inline code comments
- **Installation Log**: Check "Show Log" during installation for details

---

**This installer provides a professional, user-friendly way to deploy the USB Camera Tester application across your organization or to end customers.**