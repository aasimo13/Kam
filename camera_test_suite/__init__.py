"""
USB Camera Hardware Test Suite
==============================

A comprehensive testing application for USB cameras with focus on the
WN-L2307k368 48MP BM camera module.

This package provides:
- Hardware testing capabilities
- GUI interface for easy operation
- Command-line interface for automation
- Professional reporting
- Cross-platform support (Mac, Windows, Linux, Raspberry Pi)

Usage:
    From GUI:
        >>> import camera_test_suite
        >>> camera_test_suite.main()

    From command line:
        $ camera-test-gui

Author: Camera Test Suite Team
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Camera Test Suite Team"
__license__ = "MIT"

from .main import CameraHardwareTester, main

__all__ = ["CameraHardwareTester", "main"]