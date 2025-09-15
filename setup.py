#!/usr/bin/env python3
"""
Setup script for USB Camera Hardware Test Suite
Creates a complete installation package for the WN-L2307k368 48MP camera tester
"""

from setuptools import setup, find_packages
import os
import sys
from pathlib import Path

# Read README file
current_dir = Path(__file__).parent
readme_file = current_dir / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Version info
VERSION = "1.0.0"
DESCRIPTION = "Comprehensive hardware testing suite for WN-L2307k368 48MP USB camera"

# Platform-specific dependencies
platform_deps = []
if sys.platform.startswith('win'):
    platform_deps.extend(['pywin32'])
elif sys.platform.startswith('darwin'):
    platform_deps.extend(['pyobjc-framework-AVFoundation'])
elif sys.platform.startswith('linux'):
    platform_deps.extend(['v4l2-python3'])

setup(
    name="usb-camera-test-suite",
    version=VERSION,
    author="Camera Test Suite Developer",
    author_email="support@cameratests.com",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cameratests/usb-camera-test-suite",
    project_urls={
        "Bug Tracker": "https://github.com/cameratests/usb-camera-test-suite/issues",
        "Documentation": "https://github.com/cameratests/usb-camera-test-suite/wiki",
        "Source Code": "https://github.com/cameratests/usb-camera-test-suite",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "Topic :: Multimedia :: Graphics :: Capture :: Digital Camera",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    keywords="camera testing usb hardware automation quality-assurance opencv",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
        "psutil>=5.9.0",
        "matplotlib>=3.7.0",
        "reportlab>=4.0.0",
        "packaging>=21.0",
        "setuptools>=65.0.0",
    ] + platform_deps,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "build": [
            "pyinstaller>=5.0.0",
            "wheel>=0.38.0",
            "twine>=4.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "camera-test=camera_test_suite.main:main",
            "camera-test-cli=camera_test_suite.cli:main",
        ],
        "gui_scripts": [
            "camera-test-gui=camera_test_suite.main:main",
        ],
    },
    package_data={
        "camera_test_suite": [
            "assets/*",
            "icons/*",
            "templates/*",
            "config/*",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    platforms=["any"],
    license="MIT",
    test_suite="tests",
    cmdclass={},
)