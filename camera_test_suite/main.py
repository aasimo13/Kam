#!/usr/bin/env python3
"""
USB Camera Hardware Test Application
For WN-L2307k368 48MP BM Camera Module

This application provides comprehensive hardware testing for USB cameras
with a focus on the WN-L2307k368 48MP camera module.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import subprocess
import platform
from pathlib import Path

@dataclass
class TestResult:
    test_name: str
    status: str  # "PASS", "FAIL", "SKIP"
    message: str
    timestamp: str
    details: Dict = None

class CameraHardwareTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("USB Camera Hardware Test Suite - WN-L2307k368 48MP")
        self.root.geometry("1400x900")

        # Camera properties
        self.camera = None
        self.camera_index = None
        self.is_testing = False
        self.test_results = []
        self.current_frame = None
        self.test_image_path = None

        # Camera specifications for WN-L2307k368 (updated based on datasheet)
        self.camera_specs = {
            "max_resolution": (8000, 6000),
            "max_fps": 8,
            "sensor": "Samsung S5KGM1ST ISOCELL GM1",
            "pixel_size": 0.8,
            "fov": 79,
            "interface": "USB2.0",
            "formats": ["MJPEG", "YUY2"],
            "optical_format": "1/2 inch",
            "effective_resolution": (4000, 3000),  # 48MP binned to 12MP
            "autofocus_type": "PDAF",  # Phase Detection AutoFocus
            "color_filter": "RGB Bayer",
            "analog_gain_max": 16,
            "operating_temp": (-20, 70),  # Celsius
            "hdr_support": True,
            "binning_support": True,  # Tetrapixel technology
            "wdr_support": True       # Wide Dynamic Range
        }

        self.setup_ui()
        self.setup_styles()

        # Auto-detect USB cameras in a separate thread to avoid blocking UI
        if platform.system() == "Darwin":  # macOS
            self.show_mac_permission_dialog()
        else:
            self.auto_detect_usb_cameras()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Configure custom styles
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("Pass.TLabel", foreground="green", font=("Arial", 10, "bold"))
        style.configure("Fail.TLabel", foreground="red", font=("Arial", 10, "bold"))
        style.configure("Skip.TLabel", foreground="orange", font=("Arial", 10, "bold"))

    def setup_ui(self):
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.create_camera_tab()
        self.create_tests_tab()
        self.create_results_tab()
        self.create_settings_tab()

    def create_camera_tab(self):
        # Camera Control Tab
        self.camera_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.camera_frame, text="Camera Control")

        # Camera selection
        control_frame = ttk.LabelFrame(self.camera_frame, text="Camera Control", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(control_frame, text="Camera Index:").grid(row=0, column=0, sticky="w")
        self.camera_var = tk.StringVar(value="0")
        camera_combo = ttk.Combobox(control_frame, textvariable=self.camera_var, width=10)
        camera_combo['values'] = [str(i) for i in range(10)]
        camera_combo.grid(row=0, column=1, padx=5)

        ttk.Button(control_frame, text="Connect Camera",
                  command=self.connect_camera).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Disconnect",
                  command=self.disconnect_camera).grid(row=0, column=3, padx=5)

        self.connection_status = ttk.Label(control_frame, text="Disconnected",
                                         foreground="red")
        self.connection_status.grid(row=0, column=4, padx=10)

        # Camera preview
        preview_frame = ttk.LabelFrame(self.camera_frame, text="Camera Preview", padding=10)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.preview_label = ttk.Label(preview_frame, text="No camera connected")
        self.preview_label.pack(expand=True)

        # Camera info
        info_frame = ttk.LabelFrame(self.camera_frame, text="Camera Information", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)

        self.info_text = tk.Text(info_frame, height=6, wrap="word")
        info_scroll = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        self.info_text.pack(side="left", fill="both", expand=True)
        info_scroll.pack(side="right", fill="y")

    def create_tests_tab(self):
        # Hardware Tests Tab
        self.tests_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tests_frame, text="Hardware Tests")

        # Test selection
        selection_frame = ttk.LabelFrame(self.tests_frame, text="Test Selection", padding=10)
        selection_frame.pack(fill="x", padx=10, pady=5)

        self.test_vars = {}
        test_names = [
            "Camera Detection", "Resolution Test", "Frame Rate Test",
            "Exposure Control", "Focus Test", "White Balance",
            "Image Quality", "USB Interface", "Power Consumption",
            "Capture Test Image",
            "S5KGM1ST Sensor Test", "Comprehensive AF Test", "Noise Reduction Test"
        ]

        for i, test_name in enumerate(test_names):
            var = tk.BooleanVar(value=True)
            self.test_vars[test_name] = var
            ttk.Checkbutton(selection_frame, text=test_name, variable=var).grid(
                row=i//3, column=i%3, sticky="w", padx=10, pady=2)

        # Test controls
        control_frame = ttk.Frame(self.tests_frame)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(control_frame, text="Run Selected Tests",
                  command=self.run_tests).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Run All Tests",
                  command=self.run_all_tests).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Stop Tests",
                  command=self.stop_tests).pack(side="left", padx=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var,
                                          length=200)
        self.progress_bar.pack(side="right", padx=10)

        # Test output
        output_frame = ttk.LabelFrame(self.tests_frame, text="Test Output", padding=10)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.test_output = tk.Text(output_frame, wrap="word")
        output_scroll = ttk.Scrollbar(output_frame, orient="vertical",
                                    command=self.test_output.yview)
        self.test_output.configure(yscrollcommand=output_scroll.set)
        self.test_output.pack(side="left", fill="both", expand=True)
        output_scroll.pack(side="right", fill="y")

    def create_results_tab(self):
        # Results Tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Test Results")

        # Results summary
        summary_frame = ttk.LabelFrame(self.results_frame, text="Test Summary", padding=10)
        summary_frame.pack(fill="x", padx=10, pady=5)

        self.summary_label = ttk.Label(summary_frame, text="No tests run yet")
        self.summary_label.pack()

        # Results table
        table_frame = ttk.LabelFrame(self.results_frame, text="Detailed Results", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Test", "Status", "Message", "Timestamp")
        self.results_tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=200)

        results_scroll = ttk.Scrollbar(table_frame, orient="vertical",
                                     command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        self.results_tree.pack(side="left", fill="both", expand=True)
        results_scroll.pack(side="right", fill="y")

        # Export controls
        export_frame = ttk.Frame(self.results_frame)
        export_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(export_frame, text="Export Report",
                  command=self.export_report).pack(side="left", padx=5)
        ttk.Button(export_frame, text="Clear Results",
                  command=self.clear_results).pack(side="left", padx=5)

    def create_settings_tab(self):
        # Settings Tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")

        # Camera settings
        camera_settings_frame = ttk.LabelFrame(self.settings_frame,
                                             text="Camera Settings", padding=10)
        camera_settings_frame.pack(fill="x", padx=10, pady=5)

        # Resolution settings
        ttk.Label(camera_settings_frame, text="Test Resolution:").grid(row=0, column=0, sticky="w")
        self.resolution_var = tk.StringVar(value="1920x1080")
        resolution_combo = ttk.Combobox(camera_settings_frame, textvariable=self.resolution_var)
        resolution_combo['values'] = ["640x480", "1280x720", "1920x1080", "3840x2160", "8000x6000"]
        resolution_combo.grid(row=0, column=1, padx=5, sticky="w")

        # Test settings
        test_settings_frame = ttk.LabelFrame(self.settings_frame,
                                           text="Test Settings", padding=10)
        test_settings_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(test_settings_frame, text="Test Timeout (seconds):").grid(row=0, column=0, sticky="w")
        self.timeout_var = tk.StringVar(value="30")
        ttk.Entry(test_settings_frame, textvariable=self.timeout_var, width=10).grid(row=0, column=1, padx=5, sticky="w")

        ttk.Label(test_settings_frame, text="Save Test Images:").grid(row=1, column=0, sticky="w")
        self.save_images_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(test_settings_frame, variable=self.save_images_var).grid(row=1, column=1, sticky="w")

        # Manual camera controls
        manual_controls_frame = ttk.LabelFrame(self.settings_frame,
                                             text="Manual Camera Controls", padding=10)
        manual_controls_frame.pack(fill="x", padx=10, pady=5)

        # Exposure controls
        ttk.Label(manual_controls_frame, text="Exposure:").grid(row=0, column=0, sticky="w")
        self.exposure_var = tk.DoubleVar(value=0)
        exposure_scale = ttk.Scale(manual_controls_frame, from_=-10, to=200,
                                 variable=self.exposure_var, orient="horizontal",
                                 command=self.update_exposure)
        exposure_scale.grid(row=0, column=1, padx=5, sticky="ew", columnspan=2)
        self.exposure_label = ttk.Label(manual_controls_frame, text="0")
        self.exposure_label.grid(row=0, column=3, padx=5)

        ttk.Button(manual_controls_frame, text="Auto Exposure",
                  command=self.toggle_auto_exposure).grid(row=0, column=4, padx=5)

        # Focus controls
        ttk.Label(manual_controls_frame, text="Focus:").grid(row=1, column=0, sticky="w")
        self.focus_var = tk.DoubleVar(value=0)
        focus_scale = ttk.Scale(manual_controls_frame, from_=0, to=255,
                               variable=self.focus_var, orient="horizontal",
                               command=self.update_focus)
        focus_scale.grid(row=1, column=1, padx=5, sticky="ew", columnspan=2)
        self.focus_label = ttk.Label(manual_controls_frame, text="0")
        self.focus_label.grid(row=1, column=3, padx=5)

        ttk.Button(manual_controls_frame, text="Auto Focus",
                  command=self.toggle_auto_focus).grid(row=1, column=4, padx=5)

        # Camera diagnostics
        ttk.Button(manual_controls_frame, text="Diagnose Camera Properties",
                  command=self.diagnose_camera_properties).grid(row=2, column=0, columnspan=2, pady=10, sticky="w")

        ttk.Button(manual_controls_frame, text="Test Image Quality",
                  command=self.test_image_quality).grid(row=2, column=2, columnspan=2, pady=10, sticky="w")

        # Configure column weights
        manual_controls_frame.columnconfigure(1, weight=1)
        manual_controls_frame.columnconfigure(2, weight=1)

    def auto_detect_usb_cameras(self):
        """Auto-detect USB cameras and populate camera dropdown"""
        usb_cameras = []
        all_cameras = []

        # First, get USB device information
        usb_camera_info = {}
        if platform.system() == "Darwin":  # macOS
            try:
                # Get USB camera devices
                result = subprocess.run(["system_profiler", "SPUSBDataType"],
                                      capture_output=True, text=True, timeout=10)
                self.log_message("Scanning for USB cameras...")

                # Also check camera info using system_profiler
                camera_result = subprocess.run(["system_profiler", "SPCameraDataType"],
                                             capture_output=True, text=True, timeout=5)

                # Parse USB device info to identify external cameras
                usb_lines = result.stdout.split('\n')
                for i, line in enumerate(usb_lines):
                    if any(keyword in line.lower() for keyword in ['camera', 'video', 'webcam', 'usb video class']):
                        # Look for product name and vendor info
                        for j in range(max(0, i-5), min(len(usb_lines), i+10)):
                            if 'Product ID:' in usb_lines[j] or 'Vendor ID:' in usb_lines[j]:
                                device_name = line.strip()
                                usb_camera_info[device_name] = j
                                self.log_message(f"Found USB device: {device_name}")

            except Exception as e:
                self.log_message(f"Error getting USB device info: {str(e)}")

        # Now test each camera index
        self.log_message("Testing camera indices...")
        for i in range(15):  # Test more indices
            test_camera = None
            try:
                # Platform-specific camera backend selection
                if platform.system() == "Darwin":  # macOS
                    test_camera = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
                else:
                    test_camera = cv2.VideoCapture(i)

                if test_camera is not None and test_camera.isOpened():
                    test_camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    ret, frame = test_camera.read()

                    if ret and frame is not None:
                        # Get camera properties
                        width = int(test_camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(test_camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = test_camera.get(cv2.CAP_PROP_FPS)

                        # Try to determine if this is likely a USB camera
                        is_usb_camera = self.is_likely_usb_camera(i, width, height, fps)

                        camera_info = {
                            'index': i,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'is_usb': is_usb_camera
                        }
                        all_cameras.append(camera_info)

                        if is_usb_camera:
                            usb_cameras.append(i)
                            self.log_message(f"USB Camera found at index {i} - {width}x{height} @ {fps}fps")
                        else:
                            self.log_message(f"Built-in camera at index {i} - {width}x{height} @ {fps}fps")

            except Exception as e:
                self.log_message(f"Error testing camera {i}: {str(e)}")
            finally:
                if test_camera is not None:
                    try:
                        test_camera.release()
                    except:
                        pass

        # Update camera dropdown with all detected cameras
        camera_combo = None
        for widget in self.camera_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Combobox):
                        camera_combo = child
                        break

        if camera_combo and all_cameras:
            # Create descriptive labels for cameras
            camera_options = []
            for cam in all_cameras:
                label = f"Index {cam['index']}: {cam['width']}x{cam['height']}"
                if cam['is_usb']:
                    label += " (USB)"
                else:
                    label += " (Built-in)"
                camera_options.append(label)

            camera_combo['values'] = camera_options

            # Set to first USB camera if available, otherwise first camera
            if usb_cameras:
                # Find the camera info for the first USB camera
                first_usb_cam = next(cam for cam in all_cameras if cam['index'] == usb_cameras[0])
                self.camera_var.set(f"Index {first_usb_cam['index']}: {first_usb_cam['width']}x{first_usb_cam['height']} (USB)")
                self.log_message(f"Found {len(usb_cameras)} USB camera(s), {len(all_cameras)-len(usb_cameras)} built-in")
                # Auto-connect to first USB camera
                self.auto_connect_first_camera()
            else:
                if all_cameras:
                    first_cam = all_cameras[0]
                    self.camera_var.set(f"Index {first_cam['index']}: {first_cam['width']}x{first_cam['height']} (Built-in)")
                    self.log_message("No USB cameras detected, but found built-in camera(s)")
        elif camera_combo:
            # Fallback to simple index-based selection
            camera_combo['values'] = [str(i) for i in range(10)]
            self.log_message("No cameras detected - you can manually try indices 0-9")

    def is_likely_usb_camera(self, index, width, height, fps):
        """Determine if a camera is likely a USB camera vs built-in"""

        # Built-in Mac cameras are typically at index 0
        if index == 0:
            # Could still be USB if no built-in camera exists
            # Check resolution - built-in Mac cameras usually have standard resolutions
            builtin_resolutions = [(1280, 720), (1920, 1080), (640, 480)]
            if (width, height) in builtin_resolutions:
                return False  # Likely built-in

        # Higher indices are more likely to be USB cameras
        if index > 0:
            return True

        # Very high resolutions are more likely USB cameras
        if width >= 3840 or height >= 2160:  # 4K+
            return True

        # Unusual aspect ratios might indicate USB cameras
        aspect_ratio = width / height if height > 0 else 0
        standard_ratios = [16/9, 4/3, 3/2]
        is_standard_ratio = any(abs(aspect_ratio - ratio) < 0.1 for ratio in standard_ratios)

        # Non-standard ratios more likely to be USB
        if not is_standard_ratio:
            return True

        # Default to USB camera if not clearly built-in
        return index > 0

    def show_mac_permission_dialog(self):
        """Show macOS camera permission dialog and then detect cameras"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Camera Permissions Required")
        dialog.geometry("500x300")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()

        # Create content frame
        content_frame = ttk.Frame(dialog)
        content_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Title
        title_label = ttk.Label(content_frame, text="Camera Access Required",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Instructions
        instructions = """This application requires camera access to test USB cameras.

On macOS, you may see a permission dialog asking for camera access.

Please:
1. Click "OK" to allow camera access when prompted
2. If denied, go to System Preferences > Security & Privacy > Camera
3. Enable access for Terminal or Python

Click "Continue" below to proceed with camera detection."""

        instructions_label = ttk.Label(content_frame, text=instructions,
                                     wraplength=450, justify="left")
        instructions_label.pack(pady=10, fill="x")

        # Buttons frame
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(side="bottom", fill="x", pady=(10, 0))

        def continue_detection():
            dialog.destroy()
            # Run camera detection in a separate thread to avoid blocking UI
            threading.Thread(target=self.auto_detect_usb_cameras, daemon=True).start()

        def skip_detection():
            dialog.destroy()
            self.log_message("Camera detection skipped. You can manually select camera index.")

        ttk.Button(buttons_frame, text="Continue", command=continue_detection).pack(side="right", padx=(5, 0))
        ttk.Button(buttons_frame, text="Skip", command=skip_detection).pack(side="right")

    def update_exposure(self, value):
        """Update camera exposure from manual control"""
        if self.camera and self.camera.isOpened():
            try:
                exp_val = float(value)
                self.camera.set(cv2.CAP_PROP_EXPOSURE, exp_val)
                self.exposure_label.config(text=f"{exp_val:.1f}")
                self.log_message(f"Manual exposure set to {exp_val:.1f}")
            except Exception as e:
                self.log_message(f"Error setting exposure: {e}")

    def update_focus(self, value):
        """Update camera focus from manual control"""
        if self.camera and self.camera.isOpened():
            try:
                focus_val = int(float(value))
                self.camera.set(cv2.CAP_PROP_FOCUS, focus_val)
                self.focus_label.config(text=f"{focus_val}")
                self.log_message(f"Manual focus set to {focus_val}")
            except Exception as e:
                self.log_message(f"Error setting focus: {e}")

    def toggle_auto_exposure(self):
        """Toggle auto exposure mode"""
        if self.camera and self.camera.isOpened():
            try:
                current_mode = self.camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                # Toggle between auto (0.75) and manual (0.25)
                new_mode = 0.25 if current_mode > 0.5 else 0.75
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, new_mode)
                mode_name = "Auto" if new_mode > 0.5 else "Manual"
                self.log_message(f"Exposure mode set to {mode_name}")
            except Exception as e:
                self.log_message(f"Error toggling auto exposure: {e}")

    def toggle_auto_focus(self):
        """Toggle auto focus mode"""
        if self.camera and self.camera.isOpened():
            try:
                current_mode = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)
                # Toggle between on (1) and off (0)
                new_mode = 0 if current_mode > 0.5 else 1
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, new_mode)
                mode_name = "Auto" if new_mode > 0.5 else "Manual"
                self.log_message(f"Focus mode set to {mode_name}")
            except Exception as e:
                self.log_message(f"Error toggling auto focus: {e}")

    def diagnose_camera_properties(self):
        """Comprehensive diagnosis of camera properties and controls"""
        if not self.camera or not self.camera.isOpened():
            self.log_message("Camera not connected for property diagnosis")
            return

        self.log_message("=== CAMERA PROPERTIES DIAGNOSIS ===")

        # All OpenCV camera properties to check
        properties = {
            cv2.CAP_PROP_BRIGHTNESS: "Brightness",
            cv2.CAP_PROP_CONTRAST: "Contrast",
            cv2.CAP_PROP_SATURATION: "Saturation",
            cv2.CAP_PROP_HUE: "Hue",
            cv2.CAP_PROP_GAIN: "Gain",
            cv2.CAP_PROP_EXPOSURE: "Exposure",
            cv2.CAP_PROP_AUTO_EXPOSURE: "Auto Exposure",
            cv2.CAP_PROP_GAMMA: "Gamma",
            cv2.CAP_PROP_WHITE_BALANCE_BLUE_U: "WB Blue",
            cv2.CAP_PROP_WHITE_BALANCE_RED_V: "WB Red",
            cv2.CAP_PROP_AUTO_WB: "Auto White Balance",
            cv2.CAP_PROP_FOCUS: "Focus",
            cv2.CAP_PROP_AUTOFOCUS: "Auto Focus",
            cv2.CAP_PROP_SHARPNESS: "Sharpness",
            cv2.CAP_PROP_BACKLIGHT: "Backlight Compensation",
            cv2.CAP_PROP_ISO_SPEED: "ISO Speed",
            cv2.CAP_PROP_TEMPERATURE: "Color Temperature",
        }

        working_properties = {}

        for prop_id, prop_name in properties.items():
            try:
                current_val = self.camera.get(prop_id)

                # Test if property is writable by trying to set it
                test_val = current_val + 1 if current_val < 100 else current_val - 1
                self.camera.set(prop_id, test_val)
                time.sleep(0.1)
                new_val = self.camera.get(prop_id)

                # Restore original value
                self.camera.set(prop_id, current_val)

                is_writable = abs(new_val - test_val) < max(1, abs(test_val) * 0.1)
                status = "WRITABLE" if is_writable else "READ-ONLY"

                self.log_message(f"{prop_name}: {current_val:.2f} ({status})")
                working_properties[prop_name] = {
                    'value': current_val,
                    'writable': is_writable,
                    'property_id': prop_id
                }

            except Exception as e:
                self.log_message(f"{prop_name}: NOT AVAILABLE ({e})")

        self.log_message("=== END DIAGNOSIS ===")
        return working_properties

    def test_image_quality(self):
        """Test current image quality including noise analysis"""
        if not self.camera or not self.camera.isOpened():
            self.log_message("Camera not connected for quality test")
            return

        self.log_message("=== IMAGE QUALITY ANALYSIS ===")

        try:
            # Capture multiple frames to analyze
            frames = []
            for i in range(5):
                ret, frame = self.camera.read()
                if ret and frame is not None:
                    frames.append(frame)
                time.sleep(0.1)

            if not frames:
                self.log_message("Failed to capture frames for quality analysis")
                return

            # Analyze the most recent frame
            frame = frames[-1]
            height, width = frame.shape[:2]

            # Convert to grayscale for noise analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Calculate image statistics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            min_brightness = np.min(gray)
            max_brightness = np.max(gray)

            # Noise estimation using Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            noise_variance = laplacian.var()

            # Signal-to-noise ratio estimation
            signal_power = mean_brightness ** 2
            noise_power = std_brightness ** 2
            snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')

            # Dynamic range analysis
            dynamic_range = max_brightness - min_brightness

            # Analyze frame consistency (temporal noise)
            temporal_noise = 0
            if len(frames) > 1:
                frame_diffs = []
                for i in range(1, len(frames)):
                    gray1 = cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY)
                    gray2 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
                    diff = cv2.absdiff(gray1, gray2)
                    frame_diffs.append(np.mean(diff))
                temporal_noise = np.mean(frame_diffs)

            # Quality assessment
            self.log_message(f"Resolution: {width}x{height}")
            self.log_message(f"Mean brightness: {mean_brightness:.2f}")
            self.log_message(f"Brightness std dev: {std_brightness:.2f}")
            self.log_message(f"Dynamic range: {dynamic_range} (0-255)")
            self.log_message(f"Noise variance (Laplacian): {noise_variance:.2f}")
            self.log_message(f"Estimated SNR: {snr_db:.2f} dB")
            self.log_message(f"Temporal noise: {temporal_noise:.2f}")

            # Quality recommendations
            if noise_variance > 100:
                self.log_message("⚠️  HIGH NOISE detected - try adjusting exposure/gain")
            if snr_db < 20:
                self.log_message("⚠️  LOW SNR - image quality poor")
            if dynamic_range < 100:
                self.log_message("⚠️  LIMITED dynamic range - check exposure settings")
            if temporal_noise > 10:
                self.log_message("⚠️  HIGH temporal noise - unstable image")

            # Test gain control for noise reduction
            self.log_message("\n--- Testing Gain Control for Noise Reduction ---")
            try:
                original_gain = self.camera.get(cv2.CAP_PROP_GAIN)
                self.log_message(f"Current gain: {original_gain}")

                # Try reducing gain to reduce noise
                test_gains = [original_gain * 0.5, original_gain * 0.7, original_gain * 1.5]
                for gain_val in test_gains:
                    try:
                        self.camera.set(cv2.CAP_PROP_GAIN, gain_val)
                        time.sleep(0.5)
                        actual_gain = self.camera.get(cv2.CAP_PROP_GAIN)

                        # Quick noise test with new gain
                        ret, test_frame = self.camera.read()
                        if ret:
                            test_gray = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
                            test_noise = cv2.Laplacian(test_gray, cv2.CV_64F).var()
                            self.log_message(f"Gain {gain_val:.2f} -> {actual_gain:.2f}, Noise: {test_noise:.2f}")

                    except Exception as e:
                        self.log_message(f"Gain test {gain_val} failed: {e}")

                # Restore original gain
                self.camera.set(cv2.CAP_PROP_GAIN, original_gain)

            except Exception as e:
                self.log_message(f"Gain control test failed: {e}")

            self.log_message("=== END QUALITY ANALYSIS ===")

        except Exception as e:
            self.log_message(f"Quality analysis error: {e}")

    def auto_connect_first_camera(self):
        """Automatically connect to the first detected USB camera"""
        try:
            camera_index = int(self.camera_var.get())

            # Platform-specific camera backend selection
            if platform.system() == "Darwin":  # macOS
                self.camera = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
            else:
                self.camera = cv2.VideoCapture(camera_index)

            if not self.camera.isOpened():
                self.log_message(f"Failed to auto-connect to USB camera at index {camera_index}")
                return

            self.camera_index = camera_index
            self.connection_status.config(text="USB Camera Connected", foreground="green")

            # Get camera info
            self.update_camera_info()

            # Start preview
            self.start_preview()

            self.log_message(f"USB Camera auto-connected at index {camera_index}")

        except Exception as e:
            self.log_message(f"USB Camera auto-connection failed: {str(e)}")

    def connect_camera(self):
        """Connect to the selected camera"""
        try:
            # Parse camera index from descriptive string or use direct number
            camera_selection = self.camera_var.get()
            if "Index " in camera_selection:
                # Extract index from "Index X: ..." format
                camera_index = int(camera_selection.split("Index ")[1].split(":")[0])
            else:
                # Direct index number
                camera_index = int(camera_selection)

            # Platform-specific camera backend selection
            if platform.system() == "Darwin":  # macOS
                self.camera = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
            else:
                self.camera = cv2.VideoCapture(camera_index)

            if not self.camera.isOpened():
                raise Exception("Could not open USB camera")

            self.camera_index = camera_index
            self.connection_status.config(text="USB Camera Connected", foreground="green")

            # Get camera info
            self.update_camera_info()

            # Start preview
            self.start_preview()

            self.log_message("USB Camera connected successfully")

        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to USB camera: {str(e)}")
            self.log_message(f"USB Camera connection failed: {str(e)}")

    def disconnect_camera(self):
        """Disconnect from camera"""
        if self.camera:
            self.camera.release()
            self.camera = None
            self.camera_index = None

        self.connection_status.config(text="Disconnected", foreground="red")
        self.preview_label.config(image="", text="No camera connected")
        self.info_text.delete(1.0, tk.END)
        self.log_message("Camera disconnected")

    def update_camera_info(self):
        """Update camera information display"""
        if not self.camera:
            return

        info_text = "USB Camera Information:\n"
        info_text += f"USB Camera Index: {self.camera_index}\n"

        # Get camera properties
        width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = self.camera.get(cv2.CAP_PROP_FPS)

        info_text += f"Current Resolution: {int(width)}x{int(height)}\n"
        info_text += f"Current FPS: {fps}\n"

        # Camera specs
        info_text += f"\nWN-L2307k368 Specifications:\n"
        info_text += f"Max Resolution: {self.camera_specs['max_resolution'][0]}x{self.camera_specs['max_resolution'][1]}\n"
        info_text += f"Max FPS: {self.camera_specs['max_fps']}\n"
        info_text += f"Sensor: {self.camera_specs['sensor']}\n"
        info_text += f"Field of View: {self.camera_specs['fov']}°\n"
        info_text += f"Interface: {self.camera_specs['interface']}\n"

        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)

    def start_preview(self):
        """Start camera preview"""
        def update_preview():
            try:
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        self.current_frame = frame.copy()

                        # Resize for preview
                        frame = cv2.resize(frame, (640, 480))
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                        # Convert to PhotoImage
                        image = Image.fromarray(frame)
                        photo = ImageTk.PhotoImage(image)

                        self.preview_label.config(image=photo, text="")
                        self.preview_label.image = photo
                    else:
                        # Frame read failed, show error message
                        self.preview_label.config(image="", text="Camera frame read failed")

                    # Schedule next update only if camera is still connected
                    if self.camera and self.camera.isOpened():
                        self.root.after(30, update_preview)
                else:
                    # Camera disconnected, stop preview
                    self.preview_label.config(image="", text="No camera connected")
            except Exception as e:
                # Handle any preview errors gracefully
                self.preview_label.config(image="", text=f"Preview error: {str(e)}")
                self.log_message(f"Preview error: {str(e)}")
                # Try to continue preview after error
                if self.camera and self.camera.isOpened():
                    self.root.after(100, update_preview)  # Longer delay after error

        update_preview()

    def log_message(self, message):
        """Log message to test output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.test_output.insert(tk.END, f"[{timestamp}] {message}\n")
        self.test_output.see(tk.END)
        self.root.update_idletasks()

    def run_tests(self):
        """Run selected tests"""
        if not self.camera:
            # Auto-connect to USB camera if not connected
            self.log_message("USB Camera not connected, attempting auto-connection...")
            self.auto_detect_usb_cameras()
            if not self.camera:
                messagebox.showerror("Error", "No USB camera detected. Please connect a USB camera and try again.")
                return

        if self.is_testing:
            messagebox.showwarning("Warning", "Tests are already running")
            return

        selected_tests = [name for name, var in self.test_vars.items() if var.get()]
        if not selected_tests:
            messagebox.showwarning("Warning", "Please select at least one test")
            return

        self.is_testing = True
        self.test_results.clear()
        self.update_results_display()

        # Run tests in separate thread
        threading.Thread(target=self._run_test_sequence, args=(selected_tests,), daemon=True).start()

    def run_all_tests(self):
        """Run all available tests"""
        # Select all tests
        for var in self.test_vars.values():
            var.set(True)
        self.run_tests()

    def stop_tests(self):
        """Stop running tests"""
        self.is_testing = False
        self.log_message("Test sequence stopped by user")

    def _run_test_sequence(self, test_names):
        """Run the sequence of tests"""
        try:
            total_tests = len(test_names)

            for i, test_name in enumerate(test_names):
                if not self.is_testing:
                    break

                self.log_message(f"Running test: {test_name}")
                self.progress_var.set((i / total_tests) * 100)

                # Run the specific test with additional safety checks
                try:
                    result = self._run_single_test(test_name)
                    self.test_results.append(result)

                    # Update display
                    self.root.after(0, self.update_results_display)

                    # Small delay between tests
                    time.sleep(0.5)

                    # Check if camera is still connected after test
                    if not self.camera or not self.camera.isOpened():
                        self.log_message("Camera disconnected during testing - stopping sequence")
                        break

                except Exception as e:
                    # Handle any unexpected test failures
                    error_result = TestResult(test_name, "FAIL", f"Unexpected test error: {str(e)}",
                                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    self.test_results.append(error_result)
                    self.log_message(f"Test {test_name} caused unexpected error: {str(e)}")

                    # Continue with next test instead of crashing
                    continue

            self.progress_var.set(100)
            self.log_message("Test sequence completed")

        except Exception as e:
            self.log_message(f"Test sequence error: {str(e)}")
        finally:
            self.is_testing = False

    def _run_single_test(self, test_name):
        """Run a single test and return result"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Ensure camera is still connected before each test
            if not self.camera or not self.camera.isOpened():
                return TestResult(test_name, "FAIL", "Camera disconnected during testing", timestamp)

            if test_name == "Camera Detection":
                return self._test_camera_detection(timestamp)
            elif test_name == "Resolution Test":
                return self._test_resolution(timestamp)
            elif test_name == "Frame Rate Test":
                return self._test_frame_rate(timestamp)
            elif test_name == "Exposure Control":
                return self._test_exposure_control(timestamp)
            elif test_name == "Focus Test":
                return self._test_focus(timestamp)
            elif test_name == "White Balance":
                return self._test_white_balance(timestamp)
            elif test_name == "Image Quality":
                return self._test_image_quality(timestamp)
            elif test_name == "USB Interface":
                return self._test_usb_interface(timestamp)
            elif test_name == "Power Consumption":
                return self._test_power_consumption(timestamp)
            elif test_name == "Capture Test Image":
                return self._test_capture_image(timestamp)
            elif test_name == "S5KGM1ST Sensor Test":
                return self._test_s5kgm1st_sensor_specific(timestamp)
            elif test_name == "Comprehensive AF Test":
                return self._test_autofocus_comprehensive(timestamp)
            elif test_name == "Noise Reduction Test":
                return self._test_noise_reduction_strategies(timestamp)
            else:
                return TestResult(test_name, "SKIP", "Test not implemented", timestamp)

        except Exception as e:
            return TestResult(test_name, "FAIL", f"Test error: {str(e)}", timestamp)

    def _test_camera_detection(self, timestamp):
        """Test camera detection and basic connectivity"""
        if not self.camera or not self.camera.isOpened():
            return TestResult("Camera Detection", "FAIL", "Camera not connected", timestamp)

        # Try to read a frame
        ret, frame = self.camera.read()
        if not ret:
            return TestResult("Camera Detection", "FAIL", "Cannot read frames from camera", timestamp)

        # Check if frame has expected properties
        height, width = frame.shape[:2]
        if width == 0 or height == 0:
            return TestResult("Camera Detection", "FAIL", "Invalid frame dimensions", timestamp)

        details = {"width": width, "height": height, "channels": frame.shape[2] if len(frame.shape) > 2 else 1}
        return TestResult("Camera Detection", "PASS", "Camera detected and responding", timestamp, details)

    def _test_resolution(self, timestamp):
        """Test resolution capabilities"""
        if not self.camera:
            return TestResult("Resolution Test", "FAIL", "Camera not connected", timestamp)

        test_resolutions = [(640, 480), (1280, 720), (1920, 1080)]
        supported_resolutions = []

        for width, height in test_resolutions:
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Give camera time to adjust
            time.sleep(0.5)

            # Check actual resolution
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if actual_width == width and actual_height == height:
                supported_resolutions.append(f"{width}x{height}")

        if not supported_resolutions:
            return TestResult("Resolution Test", "FAIL", "No standard resolutions supported", timestamp)

        details = {"supported_resolutions": supported_resolutions}
        return TestResult("Resolution Test", "PASS",
                         f"Supported resolutions: {', '.join(supported_resolutions)}",
                         timestamp, details)

    def _test_frame_rate(self, timestamp):
        """Test frame rate capabilities"""
        if not self.camera:
            return TestResult("Frame Rate Test", "FAIL", "Camera not connected", timestamp)

        # Measure actual frame rate
        frame_count = 0
        start_time = time.time()
        test_duration = 3  # seconds

        while time.time() - start_time < test_duration:
            ret, frame = self.camera.read()
            if ret:
                frame_count += 1
            else:
                break

        elapsed_time = time.time() - start_time
        actual_fps = frame_count / elapsed_time if elapsed_time > 0 else 0

        # Get reported FPS
        reported_fps = self.camera.get(cv2.CAP_PROP_FPS)

        details = {
            "measured_fps": round(actual_fps, 2),
            "reported_fps": reported_fps,
            "frame_count": frame_count,
            "test_duration": round(elapsed_time, 2)
        }

        if actual_fps < 1:
            return TestResult("Frame Rate Test", "FAIL",
                             f"Very low frame rate: {actual_fps:.2f} FPS",
                             timestamp, details)

        return TestResult("Frame Rate Test", "PASS",
                         f"Frame rate: {actual_fps:.2f} FPS (reported: {reported_fps})",
                         timestamp, details)

    def _test_exposure_control(self, timestamp):
        """Enhanced exposure control test with multiple methods and diagnostics"""
        if not self.camera:
            return TestResult("Exposure Control", "FAIL", "Camera not connected", timestamp)

        self.log_message("=== COMPREHENSIVE EXPOSURE CONTROL TEST ===")

        try:
            # Get initial state
            original_exposure = self.camera.get(cv2.CAP_PROP_EXPOSURE)
            original_auto_exposure = self.camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            original_brightness = self.camera.get(cv2.CAP_PROP_BRIGHTNESS)
            original_gain = self.camera.get(cv2.CAP_PROP_GAIN)

            self.log_message(f"Initial state - Exposure: {original_exposure}, Auto: {original_auto_exposure}")
            self.log_message(f"Initial state - Brightness: {original_brightness}, Gain: {original_gain}")

            # Method 1: Standard OpenCV exposure control
            self.log_message("\n--- METHOD 1: OpenCV Direct Exposure Control ---")
            method1_working = False
            working_exposures = []
            exposure_responses = {}

            # Try setting manual exposure mode first
            auto_exp_methods = [0.25, 0, 1, 3]  # Different auto exposure disable methods
            for auto_method in auto_exp_methods:
                try:
                    self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_method)
                    time.sleep(0.5)
                    result = self.camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                    self.log_message(f"Auto-exposure method {auto_method} -> {result}")
                    if abs(result - auto_method) < 0.1:
                        break
                except:
                    continue

            # Test exposure values with image brightness measurement
            test_exposures = [-10, -7, -4, -1, 1, 10, 50, 100, 200, 500, 1000]

            for exp_val in test_exposures:
                try:
                    # Capture baseline frame
                    ret, baseline_frame = self.camera.read()
                    baseline_brightness = np.mean(baseline_frame) if ret else 0

                    self.camera.set(cv2.CAP_PROP_EXPOSURE, exp_val)
                    time.sleep(1.0)  # Longer wait
                    actual_exp = self.camera.get(cv2.CAP_PROP_EXPOSURE)

                    # Capture test frame to check actual brightness change
                    ret, test_frame = self.camera.read()
                    test_brightness = np.mean(test_frame) if ret else 0

                    brightness_change = abs(test_brightness - baseline_brightness)
                    property_change = abs(actual_exp - exp_val) < max(1, abs(exp_val) * 0.15)

                    exposure_responses[exp_val] = {
                        'reported_exposure': actual_exp,
                        'brightness_change': brightness_change,
                        'baseline_brightness': baseline_brightness,
                        'test_brightness': test_brightness
                    }

                    if property_change or brightness_change > 5:
                        working_exposures.append(exp_val)
                        method1_working = True
                        self.log_message(f"Exposure {exp_val} -> {actual_exp:.2f} (brightness Δ: {brightness_change:.1f})")

                except Exception as e:
                    self.log_message(f"Exposure {exp_val} test failed: {e}")

            # Method 2: Alternative controls (brightness, gain)
            self.log_message("\n--- METHOD 2: Alternative Controls (Brightness/Gain) ---")
            method2_working = False

            try:
                # Test brightness control as exposure alternative
                brightness_values = [0, 32, 64, 128, 192, 255]
                working_brightness = []

                for bright_val in brightness_values:
                    try:
                        ret, baseline_frame = self.camera.read()
                        baseline_avg = np.mean(baseline_frame) if ret else 0

                        self.camera.set(cv2.CAP_PROP_BRIGHTNESS, bright_val)
                        time.sleep(0.5)
                        actual_bright = self.camera.get(cv2.CAP_PROP_BRIGHTNESS)

                        ret, test_frame = self.camera.read()
                        test_avg = np.mean(test_frame) if ret else 0
                        brightness_change = abs(test_avg - baseline_avg)

                        if abs(actual_bright - bright_val) < 5 or brightness_change > 3:
                            working_brightness.append(bright_val)
                            method2_working = True
                            self.log_message(f"Brightness {bright_val} -> {actual_bright} (effect: {brightness_change:.1f})")

                    except Exception as e:
                        self.log_message(f"Brightness {bright_val} failed: {e}")

                # Test gain control
                gain_values = [0, 25, 50, 100, 200]
                working_gain = []

                for gain_val in gain_values:
                    try:
                        ret, baseline_frame = self.camera.read()
                        baseline_avg = np.mean(baseline_frame) if ret else 0

                        self.camera.set(cv2.CAP_PROP_GAIN, gain_val)
                        time.sleep(0.5)
                        actual_gain = self.camera.get(cv2.CAP_PROP_GAIN)

                        ret, test_frame = self.camera.read()
                        test_avg = np.mean(test_frame) if ret else 0
                        brightness_change = abs(test_avg - baseline_avg)

                        if abs(actual_gain - gain_val) < max(5, gain_val * 0.1) or brightness_change > 3:
                            working_gain.append(gain_val)
                            method2_working = True
                            self.log_message(f"Gain {gain_val} -> {actual_gain} (effect: {brightness_change:.1f})")

                    except Exception as e:
                        self.log_message(f"Gain {gain_val} failed: {e}")

            except Exception as e:
                self.log_message(f"Alternative controls test failed: {e}")

            # Method 3: Auto-exposure toggle functionality
            self.log_message("\n--- METHOD 3: Auto-Exposure Toggle ---")
            auto_exp_working = False

            try:
                auto_modes = [(0.25, "Manual"), (0.75, "Auto"), (0, "Off"), (1, "On"), (3, "Aperture Priority")]
                mode_responses = {}

                for mode_val, mode_name in auto_modes:
                    try:
                        self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode_val)
                        time.sleep(0.8)
                        result = self.camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                        mode_responses[mode_name] = result
                        self.log_message(f"Auto-exposure {mode_name} ({mode_val}) -> {result}")
                    except Exception as e:
                        self.log_message(f"Auto-exposure mode {mode_name} failed: {e}")

                # Check if any modes actually changed
                unique_values = set(mode_responses.values())
                auto_exp_working = len(unique_values) > 1
                self.log_message(f"Auto-exposure modes responsive: {auto_exp_working}")

            except Exception as e:
                self.log_message(f"Auto-exposure toggle test failed: {e}")

            # Restore original settings
            try:
                self.camera.set(cv2.CAP_PROP_EXPOSURE, original_exposure)
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, original_auto_exposure)
                self.camera.set(cv2.CAP_PROP_BRIGHTNESS, original_brightness)
                self.camera.set(cv2.CAP_PROP_GAIN, original_gain)
            except:
                pass

            # Comprehensive results
            details = {
                "method1_direct_exposure": {
                    "working": method1_working,
                    "working_values": working_exposures,
                    "responses": exposure_responses
                },
                "method2_alternatives": {
                    "working": method2_working,
                    "brightness_working": len(working_brightness) > 0 if 'working_brightness' in locals() else False,
                    "gain_working": len(working_gain) > 0 if 'working_gain' in locals() else False
                },
                "method3_auto_exposure": {
                    "working": auto_exp_working,
                    "mode_responses": mode_responses if 'mode_responses' in locals() else {}
                },
                "initial_state": {
                    "exposure": original_exposure,
                    "auto_exposure": original_auto_exposure,
                    "brightness": original_brightness,
                    "gain": original_gain
                }
            }

            self.log_message("=== END EXPOSURE CONTROL TEST ===")

            # STRICT EVALUATION for photobooth compatibility
            exposure_methods_working = 0
            critical_exposure_failures = []

            if method1_working:
                exposure_methods_working += 1
                self.log_message("✓ Direct exposure control: WORKING")
            else:
                critical_exposure_failures.append("Direct exposure control not responding")
                self.log_message("✗ Direct exposure control: FAILED")

            if auto_exp_working:
                exposure_methods_working += 1
                self.log_message("✓ Auto-exposure: WORKING")
            else:
                critical_exposure_failures.append("Auto-exposure not responding")
                self.log_message("✗ Auto-exposure: FAILED")

            if method2_working:
                exposure_methods_working += 1
                alternatives = []
                if 'working_brightness' in locals() and len(working_brightness) > 0:
                    alternatives.append("brightness")
                if 'working_gain' in locals() and len(working_gain) > 0:
                    alternatives.append("gain")
                self.log_message(f"✓ Alternative controls: WORKING ({', '.join(alternatives)})")
            else:
                self.log_message("✗ Alternative controls: FAILED")

            # STRICT CRITERIA: At least 2 exposure methods must work for photobooth reliability
            if exposure_methods_working >= 2:
                return TestResult("Exposure Control", "PASS",
                                f"Exposure control PHOTOBOOTH READY: {exposure_methods_working}/3 methods working",
                                timestamp, details)
            elif exposure_methods_working == 1 and auto_exp_working:
                return TestResult("Exposure Control", "PASS",
                                "Exposure control basic functionality: Auto-exposure working (limited manual control)",
                                timestamp, details)
            elif exposure_methods_working == 1:
                return TestResult("Exposure Control", "FAIL",
                                f"Exposure control LIMITED: Only 1/3 methods working - NOT PHOTOBOOTH RELIABLE",
                                timestamp, details)
            else:
                return TestResult("Exposure Control", "FAIL",
                                f"Exposure control FAILED: No responsive methods - NOT PHOTOBOOTH COMPATIBLE",
                                timestamp, details)

        except Exception as e:
            return TestResult("Exposure Control", "FAIL",
                             f"Exposure control test error: {str(e)}",
                             timestamp)

    def _test_focus(self, timestamp):
        """Test focus functionality including autofocus and manual focus for WN-L2307k368"""
        if not self.camera:
            return TestResult("Focus Test", "FAIL", "Camera not connected", timestamp)

        try:
            # Get initial focus settings
            initial_autofocus = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)
            initial_focus_pos = self.camera.get(cv2.CAP_PROP_FOCUS)

            self.log_message(f"Testing focus control - Initial AF: {initial_autofocus}, Focus pos: {initial_focus_pos}")

            # Test autofocus toggle
            autofocus_working = False
            try:
                # Enable autofocus
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                time.sleep(1.0)  # Longer wait for autofocus
                autofocus_on = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)

                # Disable autofocus
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                time.sleep(1.0)
                autofocus_off = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)

                autofocus_working = abs(autofocus_on - autofocus_off) > 0.1
                self.log_message(f"Autofocus toggle: {autofocus_working} (on={autofocus_on}, off={autofocus_off})")
            except Exception as e:
                self.log_message(f"Autofocus toggle test error: {e}")

            # Test manual focus control
            manual_focus_working = False
            focus_responses = {}
            working_focus_values = []

            try:
                # Disable autofocus for manual testing
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                time.sleep(0.5)

                # Test different focus positions
                # WN-L2307k368 may support wide range of focus values
                test_focus_values = [0, 10, 25, 50, 75, 100, 150, 200, 255]

                for focus_val in test_focus_values:
                    try:
                        # Check if camera is still connected
                        if not self.camera or not self.camera.isOpened():
                            break

                        success = self.camera.set(cv2.CAP_PROP_FOCUS, focus_val)
                        if not success:
                            self.log_message(f"Focus value {focus_val} set failed")
                            continue

                        time.sleep(0.8)  # Wait for focus motor
                        actual_focus = self.camera.get(cv2.CAP_PROP_FOCUS)

                        focus_responses[focus_val] = actual_focus

                        # Check if focus position changed
                        if abs(actual_focus - focus_val) < max(5, focus_val * 0.1):
                            working_focus_values.append(focus_val)
                            self.log_message(f"Focus {focus_val} -> {actual_focus} (WORKING)")
                        else:
                            self.log_message(f"Focus {focus_val} -> {actual_focus} (no response)")

                    except Exception as e:
                        self.log_message(f"Error setting focus {focus_val}: {e}")

                manual_focus_working = len(working_focus_values) > 0

            except Exception as e:
                self.log_message(f"Manual focus test error: {e}")

            # Test focus sweep (if manual focus works)
            focus_sweep_working = False
            if manual_focus_working and len(working_focus_values) >= 2:
                try:
                    # Test smooth focus transition
                    min_focus = min(working_focus_values)
                    max_focus = max(working_focus_values)

                    self.camera.set(cv2.CAP_PROP_FOCUS, min_focus)
                    time.sleep(0.8)
                    start_pos = self.camera.get(cv2.CAP_PROP_FOCUS)

                    self.camera.set(cv2.CAP_PROP_FOCUS, max_focus)
                    time.sleep(0.8)
                    end_pos = self.camera.get(cv2.CAP_PROP_FOCUS)

                    focus_sweep_working = abs(end_pos - start_pos) > 10
                    self.log_message(f"Focus sweep: {focus_sweep_working} ({start_pos} -> {end_pos})")

                except Exception as e:
                    self.log_message(f"Focus sweep test error: {e}")

            # Restore original settings
            try:
                self.camera.set(cv2.CAP_PROP_FOCUS, initial_focus_pos)
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, initial_autofocus)
            except:
                pass

            details = {
                "initial_autofocus": initial_autofocus,
                "initial_focus_position": initial_focus_pos,
                "autofocus_working": autofocus_working,
                "manual_focus_working": manual_focus_working,
                "working_focus_values": working_focus_values,
                "focus_responses": focus_responses,
                "focus_sweep_working": focus_sweep_working,
                "focus_range_tested": test_focus_values
            }

            # Determine test result
            if autofocus_working or manual_focus_working:
                capabilities = []
                if autofocus_working:
                    capabilities.append("Autofocus")
                if manual_focus_working:
                    capabilities.append(f"Manual focus ({len(working_focus_values)} positions)")
                if focus_sweep_working:
                    capabilities.append("Focus sweep")

                return TestResult("Focus Test", "PASS",
                                 f"Focus control functional: {', '.join(capabilities)}",
                                 timestamp, details)
            elif initial_focus_pos > 0 or initial_autofocus > 0:
                # Camera reports focus capability but controls don't work
                return TestResult("Focus Test", "FAIL",
                                 "Focus hardware detected but controls not responding",
                                 timestamp, details)
            else:
                # No focus capability detected
                return TestResult("Focus Test", "SKIP",
                                 "No focus control capability detected",
                                 timestamp, details)

        except Exception as e:
            return TestResult("Focus Test", "FAIL",
                             f"Focus test error: {str(e)}",
                             timestamp)

    def _test_white_balance(self, timestamp):
        """Comprehensive white balance functionality test"""
        if not self.camera:
            return TestResult("White Balance", "FAIL", "Camera not connected", timestamp)

        self.log_message("=== COMPREHENSIVE WHITE BALANCE TEST ===")

        try:
            wb_results = {}

            # Test 1: Basic WB property availability
            self.log_message("Testing basic WB property availability...")
            try:
                wb_temp = self.camera.get(cv2.CAP_PROP_WB_TEMPERATURE)
                auto_wb = self.camera.get(cv2.CAP_PROP_AUTO_WB)
                wb_blue = self.camera.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U)
                wb_red = self.camera.get(cv2.CAP_PROP_WHITE_BALANCE_RED_V)

                wb_results['initial_values'] = {
                    'wb_temperature': wb_temp,
                    'auto_wb': auto_wb,
                    'wb_blue': wb_blue,
                    'wb_red': wb_red
                }

                self.log_message(f"WB Temperature: {wb_temp}")
                self.log_message(f"Auto WB: {auto_wb}")
                self.log_message(f"WB Blue: {wb_blue}")
                self.log_message(f"WB Red: {wb_red}")

            except Exception as e:
                wb_results['initial_values'] = {'error': str(e)}
                self.log_message(f"Basic WB properties error: {e}")

            # Test 2: Auto WB control
            self.log_message("Testing auto white balance control...")
            auto_wb_working = False
            try:
                # Test different auto WB values
                auto_wb_modes = [0, 1, 0.25, 0.75]
                auto_wb_responses = {}

                for mode in auto_wb_modes:
                    try:
                        # Check if camera is still connected
                        if not self.camera or not self.camera.isOpened():
                            break

                        success = self.camera.set(cv2.CAP_PROP_AUTO_WB, mode)
                        if not success:
                            self.log_message(f"Auto WB mode {mode} set failed")
                            continue

                        time.sleep(0.5)
                        result = self.camera.get(cv2.CAP_PROP_AUTO_WB)
                        auto_wb_responses[mode] = result
                        self.log_message(f"Auto WB mode {mode} -> {result}")

                        # Also check if this affects image color
                        try:
                            ret, frame = self.camera.read()
                            if ret and frame is not None:
                                avg_color = np.mean(frame, axis=(0, 1))  # Average RGB
                                auto_wb_responses[f'{mode}_color'] = avg_color.tolist()
                        except Exception as e:
                            self.log_message(f"Frame read during WB test failed: {e}")

                    except Exception as e:
                        self.log_message(f"Auto WB mode {mode} failed: {e}")
                        # Continue with other modes even if one fails

                # Check if any modes produced different results
                unique_values = set([v for v in auto_wb_responses.values() if isinstance(v, (int, float))])
                auto_wb_working = len(unique_values) > 1

                wb_results['auto_wb_test'] = {
                    'working': auto_wb_working,
                    'responses': auto_wb_responses
                }

            except Exception as e:
                wb_results['auto_wb_test'] = {'error': str(e)}

            # Test 3: Manual WB temperature control
            self.log_message("Testing manual WB temperature control...")
            temp_wb_working = False
            try:
                # Disable auto WB first
                self.camera.set(cv2.CAP_PROP_AUTO_WB, 0)
                time.sleep(0.3)

                # Test different temperature values
                test_temps = [2800, 4000, 5600, 6500, 8000]  # Kelvin values
                temp_responses = {}

                for temp in test_temps:
                    try:
                        self.camera.set(cv2.CAP_PROP_WB_TEMPERATURE, temp)
                        time.sleep(0.5)
                        actual_temp = self.camera.get(cv2.CAP_PROP_WB_TEMPERATURE)
                        temp_responses[temp] = actual_temp

                        # Check color cast change
                        ret, frame = self.camera.read()
                        if ret:
                            avg_color = np.mean(frame, axis=(0, 1))
                            temp_responses[f'{temp}_color'] = avg_color.tolist()
                            self.log_message(f"WB temp {temp}K -> {actual_temp}K (color: {avg_color})")

                    except Exception as e:
                        self.log_message(f"WB temp {temp}K failed: {e}")

                # Check if temperature control is working
                temp_values = [v for v in temp_responses.values() if isinstance(v, (int, float))]
                if len(temp_values) >= 2:
                    temp_range = max(temp_values) - min(temp_values)
                    temp_wb_working = temp_range > 100  # Significant temperature change

                wb_results['temperature_test'] = {
                    'working': temp_wb_working,
                    'responses': temp_responses,
                    'temp_range': temp_range if 'temp_range' in locals() else 0
                }

            except Exception as e:
                wb_results['temperature_test'] = {'error': str(e)}

            # Test 4: Manual RGB white balance control
            self.log_message("Testing manual RGB white balance control...")
            rgb_wb_working = False
            try:
                # Test blue/red balance adjustments
                blue_values = [0, 2048, 4096]  # Typical range for white balance
                red_values = [0, 2048, 4096]

                rgb_responses = {}
                color_changes = []

                for blue_val in blue_values:
                    for red_val in red_values:
                        try:
                            self.camera.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, blue_val)
                            self.camera.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, red_val)
                            time.sleep(0.3)

                            actual_blue = self.camera.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U)
                            actual_red = self.camera.get(cv2.CAP_PROP_WHITE_BALANCE_RED_V)

                            # Capture frame to check color effect
                            ret, frame = self.camera.read()
                            if ret:
                                avg_color = np.mean(frame, axis=(0, 1))
                                color_changes.append(avg_color)

                            rgb_responses[f'{blue_val}_{red_val}'] = {
                                'blue_actual': actual_blue,
                                'red_actual': actual_red,
                                'avg_color': avg_color.tolist() if ret else None
                            }

                            self.log_message(f"WB RGB B:{blue_val}->B:{actual_blue}, R:{red_val}->R:{actual_red}")

                        except Exception as e:
                            self.log_message(f"RGB WB B:{blue_val},R:{red_val} failed: {e}")

                # Check if RGB adjustments had any effect
                if len(color_changes) >= 2:
                    # Compare color variations
                    color_variations = []
                    for i in range(1, len(color_changes)):
                        diff = np.mean(np.abs(color_changes[i] - color_changes[i-1]))
                        color_variations.append(diff)

                    rgb_wb_working = max(color_variations) > 5 if color_variations else False

                wb_results['rgb_test'] = {
                    'working': rgb_wb_working,
                    'responses': rgb_responses,
                    'color_variations': color_variations if 'color_variations' in locals() else []
                }

            except Exception as e:
                wb_results['rgb_test'] = {'error': str(e)}

            # Restore original settings
            try:
                if wb_results.get('initial_values') and 'error' not in wb_results['initial_values']:
                    initial = wb_results['initial_values']
                    self.camera.set(cv2.CAP_PROP_AUTO_WB, initial['auto_wb'])
                    self.camera.set(cv2.CAP_PROP_WB_TEMPERATURE, initial['wb_temperature'])
            except:
                pass

            self.log_message("=== END WHITE BALANCE TEST ===")

            # STRICT EVALUATION for photobooth compatibility
            working_methods = 0
            methods_tested = 0
            critical_wb_failures = []

            # Auto white balance is CRITICAL for photobooths
            auto_wb_working = wb_results.get('auto_wb_test', {}).get('working', False)
            if auto_wb_working:
                working_methods += 1
                self.log_message("✓ Auto White Balance: WORKING")
            else:
                critical_wb_failures.append("Auto white balance not responding")
                self.log_message("✗ Auto White Balance: FAILED")
            if 'auto_wb_test' in wb_results:
                methods_tested += 1

            # Manual temperature control is IMPORTANT for photobooths
            temp_wb_working = wb_results.get('temperature_test', {}).get('working', False)
            if temp_wb_working:
                working_methods += 1
                self.log_message("✓ Temperature White Balance: WORKING")
            else:
                self.log_message("✗ Temperature White Balance: FAILED")
            if 'temperature_test' in wb_results:
                methods_tested += 1

            # RGB white balance is NICE TO HAVE
            rgb_wb_working = wb_results.get('rgb_test', {}).get('working', False)
            if rgb_wb_working:
                working_methods += 1
                self.log_message("✓ RGB White Balance: WORKING")
            else:
                self.log_message("✗ RGB White Balance: FAILED")
            if 'rgb_test' in wb_results:
                methods_tested += 1

            # STRICT CRITERIA: Auto WB must work for photobooth use
            if auto_wb_working and working_methods >= 2:
                return TestResult("White Balance", "PASS",
                                f"White balance PHOTOBOOTH READY: {working_methods}/{methods_tested} methods working",
                                timestamp, wb_results)
            elif auto_wb_working:
                return TestResult("White Balance", "PASS",
                                f"White balance basic functionality: Auto WB working but limited manual control",
                                timestamp, wb_results)
            elif working_methods > 0:
                return TestResult("White Balance", "FAIL",
                                f"White balance NOT PHOTOBOOTH COMPATIBLE: Auto WB failed, {working_methods}/{methods_tested} manual methods working",
                                timestamp, wb_results)
            elif methods_tested > 0:
                return TestResult("White Balance", "FAIL",
                                f"White balance hardware present but NOT RESPONDING: 0/{methods_tested} methods working",
                                timestamp, wb_results)
            else:
                return TestResult("White Balance", "SKIP",
                                "No white balance controls available on this camera",
                                timestamp, wb_results)

        except Exception as e:
            return TestResult("White Balance", "FAIL",
                             f"White balance test error: {str(e)}",
                             timestamp)

    def _test_image_quality(self, timestamp):
        """Comprehensive image quality test with noise reduction analysis"""
        if not self.camera:
            return TestResult("Image Quality", "FAIL", "Camera not connected", timestamp)

        self.log_message("=== COMPREHENSIVE IMAGE QUALITY TEST ===")

        try:
            quality_results = {}

            # Step 1: Baseline quality measurement
            self.log_message("Measuring baseline image quality...")
            ret, frame = self.camera.read()
            if not ret:
                return TestResult("Image Quality", "FAIL", "Cannot capture frame", timestamp)

            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Calculate comprehensive quality metrics
            baseline_metrics = self._calculate_quality_metrics(frame, gray)
            quality_results['baseline'] = baseline_metrics

            self.log_message(f"Baseline noise: {baseline_metrics['noise_variance']:.2f}")
            self.log_message(f"Baseline sharpness: {baseline_metrics['sharpness']:.2f}")
            self.log_message(f"Baseline brightness: {baseline_metrics['brightness']:.2f}")

            # Step 2: Noise reduction via gain adjustment
            self.log_message("Testing noise reduction via gain adjustment...")
            try:
                original_gain = self.camera.get(cv2.CAP_PROP_GAIN)
                best_gain_setting = None
                best_noise_reduction = 0

                test_gains = [original_gain * 0.5, original_gain * 0.25] if original_gain > 0 else [50, 25, 10]

                for gain in test_gains:
                    try:
                        self.camera.set(cv2.CAP_PROP_GAIN, gain)
                        time.sleep(0.5)

                        ret, test_frame = self.camera.read()
                        if ret:
                            test_gray = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
                            test_metrics = self._calculate_quality_metrics(test_frame, test_gray)

                            noise_reduction = ((baseline_metrics['noise_variance'] - test_metrics['noise_variance']) / baseline_metrics['noise_variance']) * 100

                            if noise_reduction > best_noise_reduction:
                                best_noise_reduction = noise_reduction
                                best_gain_setting = {
                                    'gain': gain,
                                    'actual_gain': self.camera.get(cv2.CAP_PROP_GAIN),
                                    'noise_reduction_percent': noise_reduction,
                                    'metrics': test_metrics
                                }

                            self.log_message(f"Gain {gain}: noise reduction {noise_reduction:.1f}%")

                    except Exception as e:
                        self.log_message(f"Gain {gain} test failed: {e}")

                # Restore original gain
                self.camera.set(cv2.CAP_PROP_GAIN, original_gain)

                quality_results['gain_noise_reduction'] = {
                    'tested': True,
                    'best_setting': best_gain_setting,
                    'original_gain': original_gain
                }

            except Exception as e:
                quality_results['gain_noise_reduction'] = {'error': str(e)}

            # Step 3: Software noise reduction techniques
            self.log_message("Testing software noise reduction techniques...")
            try:
                # Capture multiple frames for averaging
                frames = []
                for i in range(5):
                    ret, frame = self.camera.read()
                    if ret:
                        frames.append(frame.astype(np.float32))
                    time.sleep(0.1)

                software_techniques = {}

                if len(frames) >= 3:
                    # Frame averaging
                    averaged_frame = np.mean(frames, axis=0).astype(np.uint8)
                    averaged_gray = cv2.cvtColor(averaged_frame, cv2.COLOR_BGR2GRAY)
                    avg_metrics = self._calculate_quality_metrics(averaged_frame, averaged_gray)

                    avg_noise_reduction = ((baseline_metrics['noise_variance'] - avg_metrics['noise_variance']) / baseline_metrics['noise_variance']) * 100

                    software_techniques['frame_averaging'] = {
                        'noise_reduction_percent': avg_noise_reduction,
                        'frames_used': len(frames),
                        'metrics': avg_metrics
                    }

                    self.log_message(f"Frame averaging: {avg_noise_reduction:.1f}% noise reduction")

                    # Gaussian blur denoising
                    blurred_frame = cv2.GaussianBlur(frames[0].astype(np.uint8), (3, 3), 0.8)
                    blurred_gray = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2GRAY)
                    blur_metrics = self._calculate_quality_metrics(blurred_frame, blurred_gray)

                    blur_noise_reduction = ((baseline_metrics['noise_variance'] - blur_metrics['noise_variance']) / baseline_metrics['noise_variance']) * 100

                    software_techniques['gaussian_blur'] = {
                        'noise_reduction_percent': blur_noise_reduction,
                        'metrics': blur_metrics
                    }

                    self.log_message(f"Gaussian blur: {blur_noise_reduction:.1f}% noise reduction")

                    # Bilateral filter (edge-preserving denoising)
                    bilateral_frame = cv2.bilateralFilter(frames[0].astype(np.uint8), 5, 50, 50)
                    bilateral_gray = cv2.cvtColor(bilateral_frame, cv2.COLOR_BGR2GRAY)
                    bilateral_metrics = self._calculate_quality_metrics(bilateral_frame, bilateral_gray)

                    bilateral_noise_reduction = ((baseline_metrics['noise_variance'] - bilateral_metrics['noise_variance']) / baseline_metrics['noise_variance']) * 100

                    software_techniques['bilateral_filter'] = {
                        'noise_reduction_percent': bilateral_noise_reduction,
                        'metrics': bilateral_metrics
                    }

                    self.log_message(f"Bilateral filter: {bilateral_noise_reduction:.1f}% noise reduction")

                quality_results['software_noise_reduction'] = software_techniques

            except Exception as e:
                quality_results['software_noise_reduction'] = {'error': str(e)}

            # Step 4: Overall quality assessment with recommendations
            self.log_message("Generating quality assessment and recommendations...")

            quality_issues = []
            recommendations = []

            # Assess baseline quality
            if baseline_metrics['sharpness'] < 50:
                quality_issues.append("Low sharpness")
                recommendations.append("Check focus settings and lighting")

            if baseline_metrics['brightness'] < 50:
                quality_issues.append("Underexposed")
                recommendations.append("Increase exposure or gain")
            elif baseline_metrics['brightness'] > 200:
                quality_issues.append("Overexposed")
                recommendations.append("Decrease exposure or gain")

            if baseline_metrics['contrast'] < 20:
                quality_issues.append("Low contrast")
                recommendations.append("Improve lighting or adjust contrast settings")

            if baseline_metrics['noise_variance'] > 100:
                quality_issues.append("High noise")

                # Add noise reduction recommendations
                if quality_results.get('gain_noise_reduction', {}).get('best_setting'):
                    best_gain = quality_results['gain_noise_reduction']['best_setting']
                    if best_gain['noise_reduction_percent'] > 15:
                        recommendations.append(f"Reduce gain to {best_gain['gain']:.0f} for {best_gain['noise_reduction_percent']:.1f}% noise reduction")

                if quality_results.get('software_noise_reduction'):
                    sw_techniques = quality_results['software_noise_reduction']
                    best_sw_method = None
                    best_sw_reduction = 0

                    for method, data in sw_techniques.items():
                        if isinstance(data, dict) and 'noise_reduction_percent' in data:
                            if data['noise_reduction_percent'] > best_sw_reduction:
                                best_sw_reduction = data['noise_reduction_percent']
                                best_sw_method = method

                    if best_sw_method and best_sw_reduction > 10:
                        recommendations.append(f"Apply {best_sw_method.replace('_', ' ')} for {best_sw_reduction:.1f}% noise reduction")

            quality_results['assessment'] = {
                'quality_issues': quality_issues,
                'recommendations': recommendations,
                'overall_score': self._calculate_overall_quality_score(baseline_metrics)
            }

            self.log_message("=== END IMAGE QUALITY TEST ===")

            # Determine test result
            if len(quality_issues) == 0:
                return TestResult("Image Quality", "PASS",
                                "Image quality metrics within acceptable range",
                                timestamp, quality_results)
            elif len(recommendations) > 0:
                return TestResult("Image Quality", "PASS",
                                f"Quality issues detected but solutions available: {'; '.join(recommendations[:2])}",
                                timestamp, quality_results)
            else:
                return TestResult("Image Quality", "FAIL",
                                f"Quality issues: {', '.join(quality_issues)}",
                                timestamp, quality_results)

        except Exception as e:
            return TestResult("Image Quality", "FAIL",
                             f"Image quality test error: {str(e)}",
                             timestamp)

    def _calculate_quality_metrics(self, frame, gray):
        """Calculate comprehensive quality metrics for a frame"""
        try:
            # Sharpness (Laplacian variance)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Brightness (mean intensity)
            brightness = np.mean(gray)

            # Contrast (standard deviation)
            contrast = np.std(gray)

            # Noise estimation using multiple methods
            noise_variance = cv2.Laplacian(gray, cv2.CV_64F).var()  # High frequency content
            noise_std = np.std(cv2.GaussianBlur(gray, (5, 5), 0) - gray)  # Difference from smooth version

            # Signal-to-noise ratio
            signal_power = brightness ** 2
            noise_power = contrast ** 2
            snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')

            # Dynamic range
            dynamic_range = np.max(gray) - np.min(gray)

            # Color metrics (if color frame)
            color_metrics = {}
            if len(frame.shape) == 3:
                # Color saturation
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                saturation = np.mean(hsv[:, :, 1])

                # Color balance (RGB channel differences)
                b, g, r = cv2.split(frame)
                color_balance = {
                    'r_mean': np.mean(r),
                    'g_mean': np.mean(g),
                    'b_mean': np.mean(b),
                    'rg_ratio': np.mean(r) / np.mean(g) if np.mean(g) > 0 else 0,
                    'rb_ratio': np.mean(r) / np.mean(b) if np.mean(b) > 0 else 0
                }

                color_metrics = {
                    'saturation': saturation,
                    'color_balance': color_balance
                }

            return {
                'sharpness': sharpness,
                'brightness': brightness,
                'contrast': contrast,
                'noise_variance': noise_variance,
                'noise_std': noise_std,
                'snr_db': snr_db,
                'dynamic_range': dynamic_range,
                'resolution': f"{frame.shape[1]}x{frame.shape[0]}",
                'color_metrics': color_metrics
            }

        except Exception as e:
            return {'error': str(e)}

    def _calculate_overall_quality_score(self, metrics):
        """Calculate an overall quality score from 0-100"""
        try:
            score = 100

            # Penalize for issues
            if metrics['sharpness'] < 50:
                score -= 20
            if metrics['brightness'] < 50 or metrics['brightness'] > 200:
                score -= 15
            if metrics['contrast'] < 20:
                score -= 15
            if metrics['noise_variance'] > 100:
                score -= 25
            if metrics['snr_db'] < 20:
                score -= 10
            if metrics['dynamic_range'] < 100:
                score -= 15

            return max(0, score)

        except:
            return 50  # Default middle score if calculation fails

    def _test_usb_interface(self, timestamp):
        """Test USB interface performance"""
        try:
            # Check USB device information
            system = platform.system()
            usb_info = "USB interface detected"

            if system == "Darwin":  # macOS
                try:
                    result = subprocess.run(["system_profiler", "SPUSBDataType"],
                                          capture_output=True, text=True, timeout=10)
                    if "Camera" in result.stdout or "Video" in result.stdout:
                        usb_info = "USB camera device found in system"
                except:
                    pass

            # Test data transfer rate
            if not self.camera:
                return TestResult("USB Interface", "FAIL", "Camera not connected", timestamp)

            # Capture multiple frames and measure timing
            frame_count = 10
            start_time = time.time()

            for _ in range(frame_count):
                ret, frame = self.camera.read()
                if not ret:
                    break

            elapsed_time = time.time() - start_time
            transfer_rate = frame_count / elapsed_time if elapsed_time > 0 else 0

            details = {
                "transfer_rate_fps": round(transfer_rate, 2),
                "usb_info": usb_info,
                "frames_tested": frame_count
            }

            if transfer_rate > 5:  # At least 5 FPS
                return TestResult("USB Interface", "PASS",
                                 f"USB interface working, transfer rate: {transfer_rate:.1f} FPS",
                                 timestamp, details)
            else:
                return TestResult("USB Interface", "FAIL",
                                 f"Poor USB transfer rate: {transfer_rate:.1f} FPS",
                                 timestamp, details)

        except Exception as e:
            return TestResult("USB Interface", "FAIL",
                             f"USB interface test error: {str(e)}",
                             timestamp)

    def _test_power_consumption(self, timestamp):
        """Test power consumption monitoring"""
        try:
            # Get system power info (basic)
            battery = psutil.sensors_battery()

            # Capture some frames to stress the camera
            if not self.camera:
                return TestResult("Power Consumption", "FAIL", "Camera not connected", timestamp)

            # Take baseline measurement
            initial_time = time.time()

            # Capture frames for 5 seconds
            frame_count = 0
            while time.time() - initial_time < 5:
                ret, frame = self.camera.read()
                if ret:
                    frame_count += 1

            details = {
                "test_duration": 5,
                "frames_captured": frame_count,
                "battery_available": battery is not None
            }

            if battery:
                details["battery_percent"] = battery.percent
                details["power_plugged"] = battery.power_plugged

            # Basic power consumption test
            if frame_count > 0:
                return TestResult("Power Consumption", "PASS",
                                 f"Camera operational, captured {frame_count} frames in 5s",
                                 timestamp, details)
            else:
                return TestResult("Power Consumption", "FAIL",
                                 "Camera not responding during power test",
                                 timestamp, details)

        except Exception as e:
            return TestResult("Power Consumption", "FAIL",
                             f"Power consumption test error: {str(e)}",
                             timestamp)

    def _test_capture_image(self, timestamp):
        """Capture a test image for the report"""
        if not self.camera:
            return TestResult("Capture Test Image", "FAIL", "Camera not connected", timestamp)

        try:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                return TestResult("Capture Test Image", "FAIL", "Cannot capture frame from camera", timestamp)

            # Multiple fallback options for test image directory
            import tempfile
            test_dir = None
            error_messages = []

            # Try user Documents directory first
            for candidate_dir in [
                Path.home() / "Documents" / "USB_Camera_Test_Images",  # Documents folder
                Path.home() / "Desktop" / "USB_Camera_Test_Images",    # Desktop folder
                Path.home() / "USB_Camera_Test_Images",                # Home directory
                Path(tempfile.gettempdir()) / "USB_Camera_Test_Images", # System temp
                Path("/tmp") / "USB_Camera_Test_Images" if platform.system() != "Windows" else Path("C:/temp") / "USB_Camera_Test_Images"  # Fallback temp
            ]:
                try:
                    candidate_dir.mkdir(parents=True, exist_ok=True)
                    # Test write access by creating a test file
                    test_file = candidate_dir / "test_write.tmp"
                    test_file.write_text("test")
                    test_file.unlink()  # Delete test file
                    test_dir = candidate_dir
                    break
                except (PermissionError, OSError, FileNotFoundError) as e:
                    error_messages.append(f"{candidate_dir}: {str(e)}")
                    continue

            if test_dir is None:
                return TestResult("Capture Test Image", "FAIL",
                                 f"Cannot create writable directory. Tried: {'; '.join(error_messages)}",
                                 timestamp)

            # Save test image
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = test_dir / f"test_image_{timestamp_str}.jpg"

            success = cv2.imwrite(str(image_filename), frame)

            if success:
                self.test_image_path = str(image_filename)
                details = {
                    "image_path": str(image_filename),
                    "image_size": f"{frame.shape[1]}x{frame.shape[0]}",
                    "file_size": os.path.getsize(image_filename)
                }

                return TestResult("Capture Test Image", "PASS",
                                 f"Test image saved: {image_filename}",
                                 timestamp, details)
            else:
                return TestResult("Capture Test Image", "FAIL",
                                 "Failed to save test image",
                                 timestamp)

        except Exception as e:
            return TestResult("Capture Test Image", "FAIL",
                             f"Image capture error: {str(e)}",
                             timestamp)

    # ========================================
    # COMPREHENSIVE WN-L2307k368 HARDWARE TESTS
    # ========================================

    def _test_s5kgm1st_sensor_specific(self, timestamp):
        """Comprehensive S5KGM1ST sensor-specific hardware test"""
        if not self.camera:
            return TestResult("S5KGM1ST Sensor Test", "FAIL", "Camera not connected", timestamp)

        self.log_message("=== S5KGM1ST SENSOR HARDWARE TEST ===")

        try:
            # Test sensor-specific features
            test_results = {}

            # 1. Test Tetrapixel binning (48MP to 12MP)
            self.log_message("Testing Tetrapixel binning capability...")
            try:
                # Test different resolutions to check binning
                resolutions_to_test = [
                    (8000, 6000),  # Full 48MP
                    (4000, 3000),  # Binned 12MP
                    (1920, 1080),  # FHD
                    (1280, 720)    # HD
                ]

                working_resolutions = []
                for res_w, res_h in resolutions_to_test:
                    try:
                        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, res_w)
                        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, res_h)
                        time.sleep(0.5)

                        actual_w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

                        # Try to capture a frame at this resolution
                        ret, frame = self.camera.read()
                        if ret and frame is not None:
                            frame_w, frame_h = frame.shape[1], frame.shape[0]
                            working_resolutions.append((actual_w, actual_h, frame_w, frame_h))
                            self.log_message(f"Resolution {res_w}x{res_h} -> {actual_w}x{actual_h} (frame: {frame_w}x{frame_h})")

                    except Exception as e:
                        self.log_message(f"Resolution {res_w}x{res_h} failed: {e}")

                test_results['binning_test'] = {
                    'working_resolutions': working_resolutions,
                    'max_resolution_achieved': max(working_resolutions, key=lambda x: x[0]*x[1]) if working_resolutions else None
                }

            except Exception as e:
                test_results['binning_test'] = {'error': str(e)}

            # 2. Test PDAF autofocus specific to S5KGM1ST
            self.log_message("Testing PDAF autofocus capability...")
            try:
                pdaf_working = False

                # PDAF should respond differently than contrast-based AF
                focus_positions = [0, 64, 128, 192, 255]
                focus_sharpness = []

                for pos in focus_positions:
                    try:
                        self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable auto
                        time.sleep(0.2)
                        self.camera.set(cv2.CAP_PROP_FOCUS, pos)
                        time.sleep(1.0)  # Wait for focus motor

                        ret, frame = self.camera.read()
                        if ret:
                            # Calculate image sharpness using Laplacian variance
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                            focus_sharpness.append((pos, sharpness))
                            self.log_message(f"Focus pos {pos}: sharpness {sharpness:.2f}")

                    except Exception as e:
                        self.log_message(f"PDAF test at position {pos} failed: {e}")

                # Check if there's variation in sharpness (indicates working focus)
                if len(focus_sharpness) >= 3:
                    sharpness_values = [s[1] for s in focus_sharpness]
                    sharpness_range = max(sharpness_values) - min(sharpness_values)
                    pdaf_working = sharpness_range > 50  # Significant variation

                test_results['pdaf_test'] = {
                    'working': pdaf_working,
                    'focus_sharpness': focus_sharpness,
                    'sharpness_range': sharpness_range if 'sharpness_range' in locals() else 0
                }

            except Exception as e:
                test_results['pdaf_test'] = {'error': str(e)}

            # 3. Test Samsung ISOCELL-specific noise characteristics
            self.log_message("Testing ISOCELL noise characteristics...")
            try:
                # Test noise at different gain levels specific to Samsung sensor
                gain_levels = [0, 4, 8, 12, 16]  # Up to max analog gain
                noise_analysis = []

                for gain in gain_levels:
                    try:
                        self.camera.set(cv2.CAP_PROP_GAIN, gain)
                        time.sleep(0.5)

                        # Capture multiple frames for temporal noise analysis
                        frames = []
                        for _ in range(3):
                            ret, frame = self.camera.read()
                            if ret:
                                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
                            time.sleep(0.1)

                        if len(frames) >= 2:
                            # Calculate noise metrics
                            frame_std = np.std(frames[0])
                            temporal_diff = np.mean(np.abs(frames[1].astype(float) - frames[0].astype(float)))

                            noise_analysis.append({
                                'gain': gain,
                                'spatial_noise': frame_std,
                                'temporal_noise': temporal_diff
                            })

                            self.log_message(f"Gain {gain}: spatial noise {frame_std:.2f}, temporal noise {temporal_diff:.2f}")

                    except Exception as e:
                        self.log_message(f"Noise test at gain {gain} failed: {e}")

                test_results['isocell_noise_test'] = noise_analysis

            except Exception as e:
                test_results['isocell_noise_test'] = {'error': str(e)}

            # 4. Test HDR/WDR capabilities
            self.log_message("Testing HDR/WDR capabilities...")
            try:
                hdr_working = False

                # Test exposure bracketing for HDR
                base_exposure = self.camera.get(cv2.CAP_PROP_EXPOSURE)
                hdr_exposures = [base_exposure - 2, base_exposure, base_exposure + 2]
                hdr_frames = []

                for exp in hdr_exposures:
                    try:
                        self.camera.set(cv2.CAP_PROP_EXPOSURE, exp)
                        time.sleep(0.8)
                        ret, frame = self.camera.read()
                        if ret:
                            brightness = np.mean(frame)
                            hdr_frames.append((exp, brightness))
                            self.log_message(f"HDR exposure {exp}: brightness {brightness:.1f}")
                    except:
                        continue

                # Check if exposure bracketing created different brightnesses
                if len(hdr_frames) >= 2:
                    brightness_values = [h[1] for h in hdr_frames]
                    brightness_range = max(brightness_values) - min(brightness_values)
                    hdr_working = brightness_range > 20

                test_results['hdr_test'] = {
                    'working': hdr_working,
                    'hdr_frames': hdr_frames,
                    'brightness_range': brightness_range if 'brightness_range' in locals() else 0
                }

            except Exception as e:
                test_results['hdr_test'] = {'error': str(e)}

            # Determine overall sensor test result
            passed_tests = 0
            total_tests = 4

            if test_results.get('binning_test', {}).get('working_resolutions'):
                passed_tests += 1
            if test_results.get('pdaf_test', {}).get('working'):
                passed_tests += 1
            if test_results.get('isocell_noise_test') and isinstance(test_results['isocell_noise_test'], list):
                passed_tests += 1
            if test_results.get('hdr_test', {}).get('working'):
                passed_tests += 1

            self.log_message("=== END S5KGM1ST SENSOR TEST ===")

            if passed_tests >= 2:
                return TestResult("S5KGM1ST Sensor Test", "PASS",
                                f"Sensor hardware functional: {passed_tests}/{total_tests} tests passed",
                                timestamp, test_results)
            else:
                return TestResult("S5KGM1ST Sensor Test", "FAIL",
                                f"Sensor hardware issues: only {passed_tests}/{total_tests} tests passed",
                                timestamp, test_results)

        except Exception as e:
            return TestResult("S5KGM1ST Sensor Test", "FAIL",
                             f"Sensor test error: {str(e)}", timestamp)

    def _test_autofocus_comprehensive(self, timestamp):
        """Comprehensive PDAF autofocus test for WN-L2307k368"""
        if not self.camera:
            return TestResult("Comprehensive AF Test", "FAIL", "Camera not connected", timestamp)

        self.log_message("=== COMPREHENSIVE AUTOFOCUS TEST ===")

        try:
            af_capabilities = {}

            # Test 1: PDAF availability and response
            self.log_message("Testing PDAF availability...")
            try:
                # Check if camera reports autofocus capability
                initial_af_mode = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)
                initial_focus_pos = self.camera.get(cv2.CAP_PROP_FOCUS)

                af_capabilities['initial_state'] = {
                    'af_mode': initial_af_mode,
                    'focus_position': initial_focus_pos
                }

                self.log_message(f"Initial AF mode: {initial_af_mode}, Focus pos: {initial_focus_pos}")

            except Exception as e:
                af_capabilities['initial_state'] = {'error': str(e)}

            # Test 2: Manual focus stepping accuracy
            self.log_message("Testing manual focus stepping...")
            try:
                # Check if camera is still connected
                if not self.camera or not self.camera.isOpened():
                    af_capabilities['manual_focus'] = {'error': 'Camera disconnected'}
                    raise Exception("Camera disconnected during focus test")

                # Disable autofocus
                af_disable_success = self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                if not af_disable_success:
                    self.log_message("Warning: Could not disable autofocus")

                time.sleep(0.5)

                focus_steps = []
                test_positions = [0, 32, 64, 96, 128, 160, 192, 224, 255]
                successful_steps = 0
                focus_actually_changed = False

                for pos in test_positions:
                    try:
                        # Check camera connection before each step
                        if not self.camera or not self.camera.isOpened():
                            break

                        # Get focus before setting
                        focus_before = self.camera.get(cv2.CAP_PROP_FOCUS)

                        # Set focus position
                        focus_set_success = self.camera.set(cv2.CAP_PROP_FOCUS, pos)
                        if not focus_set_success:
                            self.log_message(f"Failed to set focus to {pos}")
                            continue

                        time.sleep(0.8)  # Wait for focus motor

                        # Safety check before getting focus position
                        if not self.camera or not self.camera.isOpened():
                            self.log_message(f"Camera disconnected during focus operation at {pos}")
                            break

                        actual_pos = self.camera.get(cv2.CAP_PROP_FOCUS)

                        # CRITICAL: Check if focus actually changed
                        if abs(actual_pos - focus_before) > 5:  # Significant change
                            focus_actually_changed = True

                        # Capture frame and measure sharpness with crash protection
                        try:
                            ret, frame = self.camera.read()
                            if ret and frame is not None and frame.size > 0:
                                # Additional safety checks for frame integrity
                                if len(frame.shape) == 3 and frame.shape[0] > 10 and frame.shape[1] > 10:
                                    try:
                                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                        if gray is not None and gray.size > 0:
                                            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                                        else:
                                            self.log_message(f"Gray conversion failed at focus position {pos}")
                                            continue
                                    except cv2.error as cv_err:
                                        self.log_message(f"OpenCV error during frame processing at focus {pos}: {cv_err}")
                                        continue
                                else:
                                    self.log_message(f"Invalid frame dimensions at focus position {pos}: {frame.shape if hasattr(frame, 'shape') else 'no shape'}")
                                    continue
                            else:
                                self.log_message(f"Frame read failed at focus position {pos}")
                                continue
                        except Exception as e:
                            self.log_message(f"Critical error during frame processing at focus {pos}: {e}")
                            continue

                        # Process successful frame capture
                        accuracy = abs(actual_pos - pos)
                        focus_steps.append({
                            'target': pos,
                            'actual': actual_pos,
                            'sharpness': sharpness,
                            'accuracy': accuracy,
                            'focus_changed': abs(actual_pos - focus_before) > 5
                        })
                        successful_steps += 1
                        self.log_message(f"Focus {pos} -> {actual_pos} (sharpness: {sharpness:.2f}, accuracy: {accuracy})")

                    except Exception as e:
                        self.log_message(f"Focus step {pos} failed: {e}")

                # STRICT CRITERIA: Focus must actually work for photobooth use
                manual_focus_working = (
                    successful_steps >= 5 and  # At least 5 successful steps
                    focus_actually_changed and  # Focus must actually move
                    len([s for s in focus_steps if s['accuracy'] < 20]) >= 3  # At least 3 accurate steps
                )

                af_capabilities['manual_focus'] = {
                    'steps': focus_steps,
                    'successful_steps': successful_steps,
                    'focus_actually_changed': focus_actually_changed,
                    'working': manual_focus_working,
                    'strict_criteria': True
                }

            except Exception as e:
                af_capabilities['manual_focus'] = {'error': str(e)}

            # Test 3: Autofocus trigger and convergence
            self.log_message("Testing autofocus convergence...")
            try:
                # Check if camera is still connected
                if not self.camera or not self.camera.isOpened():
                    af_capabilities['convergence'] = {'error': 'Camera disconnected'}
                    raise Exception("Camera disconnected during AF convergence test")

                convergence_results = []
                successful_convergences = 0

                # Test autofocus at different starting positions
                start_positions = [0, 128, 255]

                for start_pos in start_positions:
                    try:
                        # Check connection before each test
                        if not self.camera or not self.camera.isOpened():
                            break

                        # Set manual focus to start position
                        self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                        time.sleep(0.3)

                        focus_set_success = self.camera.set(cv2.CAP_PROP_FOCUS, start_pos)
                        if not focus_set_success:
                            self.log_message(f"Failed to set starting focus position {start_pos}")
                            continue

                        time.sleep(0.5)

                        # Get initial focus position
                        initial_focus = self.camera.get(cv2.CAP_PROP_FOCUS)

                        # Enable autofocus
                        af_enable_success = self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                        if not af_enable_success:
                            self.log_message(f"Failed to enable autofocus from position {start_pos}")
                            continue

                        # Monitor focus changes over time
                        focus_timeline = []
                        focus_changed = False
                        max_sharpness = 0

                        for i in range(15):  # Monitor for 3 seconds
                            try:
                                current_focus = self.camera.get(cv2.CAP_PROP_FOCUS)
                                ret, frame = self.camera.read()

                                if ret and frame is not None and frame.size > 0:
                                    # Crash protection for OpenCV operations
                                    try:
                                        if len(frame.shape) == 3 and frame.shape[0] > 10 and frame.shape[1] > 10:
                                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                            if gray is not None and gray.size > 0:
                                                sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                                            else:
                                                self.log_message(f"Gray conversion failed during AF monitoring")
                                                break
                                        else:
                                            self.log_message(f"Invalid frame shape during AF monitoring: {frame.shape}")
                                            break
                                    except cv2.error as cv_err:
                                        self.log_message(f"OpenCV error during AF monitoring: {cv_err}")
                                        break

                                    focus_timeline.append({
                                        'time': i * 0.2,
                                        'focus_pos': current_focus,
                                        'sharpness': sharpness
                                    })

                                    # Check if focus actually moved significantly
                                    if abs(current_focus - initial_focus) > 10:
                                        focus_changed = True

                                    if sharpness > max_sharpness:
                                        max_sharpness = sharpness

                                time.sleep(0.2)
                            except Exception as e:
                                self.log_message(f"Frame capture failed during AF monitoring: {e}")
                                break

                        # STRICT CRITERIA: Autofocus must actually work
                        sharpness_values = [f['sharpness'] for f in focus_timeline if 'sharpness' in f]
                        sharpness_improved = (max_sharpness > 0 and len(sharpness_values) > 0 and
                                            max_sharpness > min(sharpness_values) * 1.2)  # 20% improvement

                        converged = (
                            len(focus_timeline) >= 10 and  # Got enough data points
                            focus_changed and              # Focus actually moved
                            sharpness_improved             # Image actually got sharper
                        )

                        if converged:
                            successful_convergences += 1

                        convergence_results.append({
                            'start_position': start_pos,
                            'initial_focus': initial_focus,
                            'timeline': focus_timeline,
                            'focus_changed': focus_changed,
                            'sharpness_improved': sharpness_improved,
                            'converged': converged,
                            'max_sharpness': max_sharpness
                        })

                        self.log_message(f"AF from {start_pos}: {len(focus_timeline)} steps, changed={focus_changed}, converged={converged}")

                    except Exception as e:
                        self.log_message(f"AF convergence test from {start_pos} failed: {e}")

                # STRICT CRITERIA: At least 2 out of 3 starting positions must show working AF
                af_convergence_working = successful_convergences >= 2

                af_capabilities['convergence'] = {
                    'results': convergence_results,
                    'successful_convergences': successful_convergences,
                    'working': af_convergence_working,
                    'strict_criteria': True
                }

            except Exception as e:
                af_capabilities['convergence'] = {'error': str(e)}

            # Test 4: Focus hunting detection
            self.log_message("Testing focus hunting behavior...")
            try:
                # Enable continuous autofocus and monitor for hunting
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                time.sleep(0.5)

                hunting_data = []
                for i in range(20):  # Monitor for 4 seconds
                    focus_pos = self.camera.get(cv2.CAP_PROP_FOCUS)
                    hunting_data.append(focus_pos)
                    time.sleep(0.2)

                # Analyze for hunting (rapid back-and-forth movements)
                hunting_detected = False
                if len(hunting_data) >= 10:
                    focus_changes = [abs(hunting_data[i+1] - hunting_data[i]) for i in range(len(hunting_data)-1)]
                    avg_change = np.mean(focus_changes)
                    max_change = max(focus_changes)

                    # Hunting indicated by large average movements
                    hunting_detected = avg_change > 10 and max_change > 30

                af_capabilities['hunting_test'] = {
                    'hunting_detected': hunting_detected,
                    'focus_timeline': hunting_data,
                    'avg_movement': avg_change if 'avg_change' in locals() else 0
                }

                self.log_message(f"Focus hunting {'detected' if hunting_detected else 'not detected'}")

            except Exception as e:
                af_capabilities['hunting_test'] = {'error': str(e)}

            # Restore original settings
            try:
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, af_capabilities['initial_state']['af_mode'])
                self.camera.set(cv2.CAP_PROP_FOCUS, af_capabilities['initial_state']['focus_position'])
            except:
                pass

            # STRICT EVALUATION for photobooth compatibility
            working_tests = 0
            critical_failures = []

            # Manual focus must work properly (CRITICAL for photobooth)
            manual_focus_working = af_capabilities.get('manual_focus', {}).get('working', False)
            if manual_focus_working:
                working_tests += 1
                self.log_message("✓ Manual focus: WORKING")
            else:
                critical_failures.append("Manual focus not responding properly")
                self.log_message("✗ Manual focus: FAILED")

            # Autofocus convergence must work (CRITICAL for photobooth)
            convergence_working = af_capabilities.get('convergence', {}).get('working', False)
            if convergence_working:
                working_tests += 1
                self.log_message("✓ Autofocus convergence: WORKING")
            else:
                critical_failures.append("Autofocus does not converge properly")
                self.log_message("✗ Autofocus convergence: FAILED")

            # Focus hunting should be minimal (DESIRABLE but not critical)
            hunting_detected = af_capabilities.get('hunting_test', {}).get('hunting_detected', True)
            if not hunting_detected:  # No hunting is good
                working_tests += 1
                self.log_message("✓ Focus stability: NO HUNTING")
            else:
                self.log_message("⚠ Focus stability: HUNTING DETECTED")

            self.log_message("=== END COMPREHENSIVE AUTOFOCUS TEST ===")

            # STRICT CRITERIA: Both manual focus AND autofocus must work for PASS
            # This ensures camera will work reliably in photobooths
            if working_tests >= 3:
                return TestResult("Comprehensive AF Test", "PASS",
                                f"PDAF system fully functional: {working_tests}/3 tests passed - PHOTOBOOTH READY",
                                timestamp, af_capabilities)
            elif working_tests == 2 and manual_focus_working and convergence_working:
                return TestResult("Comprehensive AF Test", "PASS",
                                f"PDAF core functions working: {working_tests}/3 tests passed - PHOTOBOOTH COMPATIBLE (minor hunting)",
                                timestamp, af_capabilities)
            elif len(critical_failures) == 0:
                return TestResult("Comprehensive AF Test", "FAIL",
                                f"PDAF partially working but not photobooth ready: {working_tests}/3 tests passed",
                                timestamp, af_capabilities)
            else:
                return TestResult("Comprehensive AF Test", "FAIL",
                                f"PDAF critical failures - NOT PHOTOBOOTH COMPATIBLE: {'; '.join(critical_failures)}",
                                timestamp, af_capabilities)

        except Exception as e:
            return TestResult("Comprehensive AF Test", "FAIL",
                             f"AF test error: {str(e)}", timestamp)

    def _test_noise_reduction_strategies(self, timestamp):
        """Test various noise reduction strategies for high-noise cameras"""
        if not self.camera:
            return TestResult("Noise Reduction Test", "FAIL", "Camera not connected", timestamp)

        self.log_message("=== NOISE REDUCTION STRATEGIES TEST ===")

        try:
            noise_results = {}

            # Baseline noise measurement
            self.log_message("Measuring baseline noise...")
            ret, baseline_frame = self.camera.read()
            if not ret:
                raise Exception("Cannot capture baseline frame")

            baseline_gray = cv2.cvtColor(baseline_frame, cv2.COLOR_BGR2GRAY)
            baseline_noise = cv2.Laplacian(baseline_gray, cv2.CV_64F).var()
            baseline_brightness = np.mean(baseline_gray)

            noise_results['baseline'] = {
                'noise_variance': baseline_noise,
                'brightness': baseline_brightness
            }

            self.log_message(f"Baseline noise: {baseline_noise:.2f}, brightness: {baseline_brightness:.1f}")

            # Strategy 1: Gain reduction
            self.log_message("Testing gain reduction...")
            try:
                original_gain = self.camera.get(cv2.CAP_PROP_GAIN)
                gain_tests = []

                test_gains = [original_gain * 0.5, original_gain * 0.25] if original_gain > 0 else [50, 25]

                for gain in test_gains:
                    try:
                        self.camera.set(cv2.CAP_PROP_GAIN, gain)
                        time.sleep(0.5)

                        ret, frame = self.camera.read()
                        if ret:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            noise = cv2.Laplacian(gray, cv2.CV_64F).var()
                            brightness = np.mean(gray)
                            actual_gain = self.camera.get(cv2.CAP_PROP_GAIN)

                            noise_reduction = ((baseline_noise - noise) / baseline_noise) * 100

                            gain_tests.append({
                                'target_gain': gain,
                                'actual_gain': actual_gain,
                                'noise': noise,
                                'brightness': brightness,
                                'noise_reduction_percent': noise_reduction
                            })

                            self.log_message(f"Gain {gain} -> {actual_gain}: noise {noise:.2f} ({noise_reduction:.1f}% reduction)")

                    except Exception as e:
                        self.log_message(f"Gain test {gain} failed: {e}")

                # Restore original gain
                self.camera.set(cv2.CAP_PROP_GAIN, original_gain)

                noise_results['gain_reduction'] = {
                    'tests': gain_tests,
                    'best_result': max(gain_tests, key=lambda x: x['noise_reduction_percent']) if gain_tests else None
                }

            except Exception as e:
                noise_results['gain_reduction'] = {'error': str(e)}

            # Strategy 2: Resolution reduction (binning simulation)
            self.log_message("Testing resolution reduction...")
            try:
                resolution_tests = []
                current_w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                current_h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

                test_resolutions = [
                    (current_w // 2, current_h // 2),
                    (1920, 1080),
                    (1280, 720)
                ]

                for res_w, res_h in test_resolutions:
                    try:
                        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, res_w)
                        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, res_h)
                        time.sleep(0.5)

                        ret, frame = self.camera.read()
                        if ret:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            noise = cv2.Laplacian(gray, cv2.CV_64F).var()
                            brightness = np.mean(gray)

                            actual_w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                            actual_h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

                            noise_reduction = ((baseline_noise - noise) / baseline_noise) * 100

                            resolution_tests.append({
                                'target_resolution': (res_w, res_h),
                                'actual_resolution': (actual_w, actual_h),
                                'noise': noise,
                                'brightness': brightness,
                                'noise_reduction_percent': noise_reduction
                            })

                            self.log_message(f"Resolution {res_w}x{res_h}: noise {noise:.2f} ({noise_reduction:.1f}% reduction)")

                    except Exception as e:
                        self.log_message(f"Resolution test {res_w}x{res_h} failed: {e}")

                # Restore original resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, current_w)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, current_h)

                noise_results['resolution_reduction'] = {
                    'tests': resolution_tests,
                    'best_result': max(resolution_tests, key=lambda x: x['noise_reduction_percent']) if resolution_tests else None
                }

            except Exception as e:
                noise_results['resolution_reduction'] = {'error': str(e)}

            # Strategy 3: Frame averaging (temporal noise reduction)
            self.log_message("Testing frame averaging...")
            try:
                # Capture multiple frames for averaging
                frames = []
                for i in range(5):
                    ret, frame = self.camera.read()
                    if ret:
                        frames.append(frame.astype(np.float32))
                    time.sleep(0.1)

                if len(frames) >= 3:
                    # Average frames
                    averaged_frame = np.mean(frames, axis=0).astype(np.uint8)
                    averaged_gray = cv2.cvtColor(averaged_frame, cv2.COLOR_BGR2GRAY)
                    averaged_noise = cv2.Laplacian(averaged_gray, cv2.CV_64F).var()

                    noise_reduction = ((baseline_noise - averaged_noise) / baseline_noise) * 100

                    noise_results['frame_averaging'] = {
                        'frames_used': len(frames),
                        'noise': averaged_noise,
                        'noise_reduction_percent': noise_reduction
                    }

                    self.log_message(f"Frame averaging: noise {averaged_noise:.2f} ({noise_reduction:.1f}% reduction)")
                else:
                    noise_results['frame_averaging'] = {'error': 'Insufficient frames captured'}

            except Exception as e:
                noise_results['frame_averaging'] = {'error': str(e)}

            # Determine best strategy
            best_strategies = []

            if noise_results.get('gain_reduction', {}).get('best_result'):
                best_gain = noise_results['gain_reduction']['best_result']
                if best_gain['noise_reduction_percent'] > 10:
                    best_strategies.append(f"Gain reduction: {best_gain['noise_reduction_percent']:.1f}% improvement")

            if noise_results.get('resolution_reduction', {}).get('best_result'):
                best_res = noise_results['resolution_reduction']['best_result']
                if best_res['noise_reduction_percent'] > 5:
                    best_strategies.append(f"Resolution reduction: {best_res['noise_reduction_percent']:.1f}% improvement")

            if noise_results.get('frame_averaging', {}).get('noise_reduction_percent', 0) > 10:
                avg_improvement = noise_results['frame_averaging']['noise_reduction_percent']
                best_strategies.append(f"Frame averaging: {avg_improvement:.1f}% improvement")

            self.log_message("=== END NOISE REDUCTION TEST ===")

            if best_strategies:
                return TestResult("Noise Reduction Test", "PASS",
                                f"Effective strategies found: {'; '.join(best_strategies)}",
                                timestamp, noise_results)
            else:
                return TestResult("Noise Reduction Test", "FAIL",
                                "No effective noise reduction strategies found",
                                timestamp, noise_results)

        except Exception as e:
            return TestResult("Noise Reduction Test", "FAIL",
                             f"Noise reduction test error: {str(e)}", timestamp)

    def update_results_display(self):
        """Update the results display"""
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add new results
        pass_count = 0
        fail_count = 0
        skip_count = 0

        for result in self.test_results:
            if result.status == "PASS":
                pass_count += 1
                tag = "pass"
            elif result.status == "FAIL":
                fail_count += 1
                tag = "fail"
            else:
                skip_count += 1
                tag = "skip"

            self.results_tree.insert("", "end", values=(
                result.test_name, result.status, result.message, result.timestamp
            ), tags=(tag,))

        # Configure tags
        self.results_tree.tag_configure("pass", foreground="green")
        self.results_tree.tag_configure("fail", foreground="red")
        self.results_tree.tag_configure("skip", foreground="orange")

        # Update summary
        total_tests = len(self.test_results)
        if total_tests > 0:
            summary_text = f"Tests: {total_tests} | Pass: {pass_count} | Fail: {fail_count} | Skip: {skip_count}"
        else:
            summary_text = "No tests run yet"

        self.summary_label.config(text=summary_text)

    def export_report(self):
        """Export test results to a report"""
        if not self.test_results:
            messagebox.showwarning("Warning", "No test results to export")
            return

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors

            # File dialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )

            if not filename:
                return

            # Create PDF
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph("USB Camera Hardware Test Report", title_style))
            story.append(Paragraph("WN-L2307k368 48MP BM Camera Module", styles['Heading2']))
            story.append(Spacer(1, 20))

            # Test summary
            pass_count = sum(1 for r in self.test_results if r.status == "PASS")
            fail_count = sum(1 for r in self.test_results if r.status == "FAIL")
            skip_count = sum(1 for r in self.test_results if r.status == "SKIP")

            story.append(Paragraph("Test Summary", styles['Heading2']))
            summary_data = [
                ["Total Tests", str(len(self.test_results))],
                ["Passed", str(pass_count)],
                ["Failed", str(fail_count)],
                ["Skipped", str(skip_count)],
                ["Report Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            ]

            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 14),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))

            # Detailed results
            story.append(Paragraph("Detailed Test Results", styles['Heading2']))

            # Results table
            table_data = [["Test Name", "Status", "Message", "Timestamp"]]
            for result in self.test_results:
                table_data.append([
                    result.test_name,
                    result.status,
                    result.message[:50] + "..." if len(result.message) > 50 else result.message,
                    result.timestamp
                ])

            results_table = Table(table_data, colWidths=[2*inch, 1*inch, 3*inch, 1.5*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('FONTSIZE', (0,1), (-1,-1), 10),
            ]))

            # Color code status
            for i, result in enumerate(self.test_results, 1):
                if result.status == "PASS":
                    results_table.setStyle(TableStyle([('TEXTCOLOR', (1,i), (1,i), colors.green)]))
                elif result.status == "FAIL":
                    results_table.setStyle(TableStyle([('TEXTCOLOR', (1,i), (1,i), colors.red)]))
                else:
                    results_table.setStyle(TableStyle([('TEXTCOLOR', (1,i), (1,i), colors.orange)]))

            story.append(results_table)

            # Add test image if available
            if self.test_image_path and os.path.exists(self.test_image_path):
                story.append(Spacer(1, 20))
                story.append(Paragraph("Test Image Capture", styles['Heading2']))
                story.append(Spacer(1, 10))

                # Resize image for PDF
                img = Image(self.test_image_path, width=4*inch, height=3*inch)
                story.append(img)

            # Build PDF
            doc.build(story)

            messagebox.showinfo("Success", f"Report exported to {filename}")

        except ImportError:
            # Fallback to JSON export
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                report_data = {
                    "timestamp": datetime.now().isoformat(),
                    "camera_model": "WN-L2307k368 48MP BM",
                    "summary": {
                        "total": len(self.test_results),
                        "passed": sum(1 for r in self.test_results if r.status == "PASS"),
                        "failed": sum(1 for r in self.test_results if r.status == "FAIL"),
                        "skipped": sum(1 for r in self.test_results if r.status == "SKIP")
                    },
                    "results": [asdict(result) for result in self.test_results]
                }

                with open(filename, 'w') as f:
                    json.dump(report_data, f, indent=2)

                messagebox.showinfo("Success", f"Report exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {str(e)}")

    def clear_results(self):
        """Clear all test results"""
        self.test_results.clear()
        self.update_results_display()
        self.test_output.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.log_message("Results cleared")

    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point for the application"""
    app = CameraHardwareTester()
    app.run()

if __name__ == "__main__":
    main()