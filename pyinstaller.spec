# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for USB Camera Test Suite
Creates standalone executables for different platforms
"""

import os
import sys
from pathlib import Path

# Application info
APP_NAME = "USB Camera Test Suite"
SCRIPT_PATH = "camera_test_suite/main.py"

# Platform detection
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform.startswith('darwin')
IS_LINUX = sys.platform.startswith('linux')

# Paths
current_dir = Path(SCRIPT_DIR if 'SCRIPT_DIR' in globals() else '.')
assets_dir = current_dir / "assets"
icons_dir = current_dir / "icons"

# Hidden imports (packages that PyInstaller might miss)
hiddenimports = [
    'cv2',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'numpy',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_tkagg',
    'reportlab',
    'reportlab.lib.pagesizes',
    'reportlab.platypus',
    'reportlab.lib.styles',
    'psutil',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'threading',
    'json',
    'datetime',
    'subprocess',
    'platform',
    'dataclasses',
]

# Platform-specific hidden imports
if IS_WINDOWS:
    hiddenimports.extend([
        'win32api',
        'win32gui',
        'win32con',
    ])
elif IS_MACOS:
    hiddenimports.extend([
        'Foundation',
        'AppKit',
    ])
elif IS_LINUX:
    hiddenimports.extend([
        'gi',
        'gi.repository.Gtk',
    ])

# Data files to include
datas = []

# Add assets if they exist
if assets_dir.exists():
    datas.append((str(assets_dir), 'assets'))

if icons_dir.exists():
    datas.append((str(icons_dir), 'icons'))

# Add templates and config if they exist
for dir_name in ['templates', 'config']:
    dir_path = current_dir / dir_name
    if dir_path.exists():
        datas.append((str(dir_path), dir_name))

# Binary excludes (to reduce file size)
excludes = [
    'tkinter.test',
    'test',
    'unittest',
    'pydoc',
    'doctest',
    'difflib',
]

# Analysis configuration
block_cipher = None

a = Analysis(
    [SCRIPT_PATH],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Platform-specific executable configuration
if IS_WINDOWS:
    # Windows executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='camera-test-suite',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # Set to True for debug version
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icons/camera-test-suite.ico' if (icons_dir / 'camera-test-suite.ico').exists() else None,
        version_file='version_info.txt' if Path('version_info.txt').exists() else None,
    )

elif IS_MACOS:
    # macOS executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='camera-test-suite',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file='assets/entitlements.plist' if (assets_dir / 'entitlements.plist').exists() else None,
    )

    # Create macOS app bundle
    app = BUNDLE(
        exe,
        name=f'{APP_NAME}.app',
        icon='icons/camera-test-suite.icns' if (icons_dir / 'camera-test-suite.icns').exists() else None,
        bundle_identifier='com.cameratests.usb-camera-test-suite',
        info_plist={
            'CFBundleDisplayName': APP_NAME,
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSCameraUsageDescription': 'This app needs camera access to test USB camera hardware.',
            'NSMicrophoneUsageDescription': 'This app may need microphone access to test camera audio.',
            'LSMinimumSystemVersion': '10.15',
            'NSHighResolutionCapable': True,
            'NSSupportsAutomaticGraphicsSwitching': True,
        },
    )

else:
    # Linux executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='camera-test-suite',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )