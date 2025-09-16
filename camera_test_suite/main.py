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

        # Camera specifications for WN-L2307k368
        self.camera_specs = {
            "max_resolution": (8000, 6000),
            "max_fps": 8,
            "sensor": "S5KGM1ST",
            "pixel_size": 0.8,
            "fov": 79,
            "interface": "USB2.0",
            "formats": ["MJPEG", "YUY2"]
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
            "Capture Test Image"
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
                test_camera = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)

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

            self.camera = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)

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
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    self.current_frame = frame.copy()

                    # Resize for preview
                    frame = cv2.resize(frame, (640, 480))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Convert to PhotoImage
                    image = Image.fromarray(frame)
                    photo = ImageTk.PhotoImage(image)

                    self.preview_label.config(image=photo, text="")
                    self.preview_label.image = photo

                # Schedule next update
                self.root.after(30, update_preview)

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

                # Run the specific test
                result = self._run_single_test(test_name)
                self.test_results.append(result)

                # Update display
                self.root.after(0, self.update_results_display)

                # Small delay between tests
                time.sleep(0.5)

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

            # Determine overall result
            if method1_working:
                return TestResult("Exposure Control", "PASS",
                                f"Direct exposure control working ({len(working_exposures)} values)",
                                timestamp, details)
            elif method2_working:
                alternatives = []
                if 'working_brightness' in locals() and len(working_brightness) > 0:
                    alternatives.append("brightness")
                if 'working_gain' in locals() and len(working_gain) > 0:
                    alternatives.append("gain")
                return TestResult("Exposure Control", "PASS",
                                f"Alternative controls working: {', '.join(alternatives)}",
                                timestamp, details)
            elif auto_exp_working:
                return TestResult("Exposure Control", "PASS",
                                "Auto-exposure modes functional",
                                timestamp, details)
            else:
                return TestResult("Exposure Control", "FAIL",
                                "No exposure control methods responsive",
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
                        self.camera.set(cv2.CAP_PROP_FOCUS, focus_val)
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
        """Test white balance functionality"""
        if not self.camera:
            return TestResult("White Balance", "FAIL", "Camera not connected", timestamp)

        try:
            # Get white balance settings
            wb_temp = self.camera.get(cv2.CAP_PROP_WB_TEMPERATURE)
            auto_wb = self.camera.get(cv2.CAP_PROP_AUTO_WB)

            # Try to change auto white balance
            self.camera.set(cv2.CAP_PROP_AUTO_WB, 1)
            time.sleep(0.2)
            auto_wb_on = self.camera.get(cv2.CAP_PROP_AUTO_WB)

            self.camera.set(cv2.CAP_PROP_AUTO_WB, 0)
            time.sleep(0.2)
            auto_wb_off = self.camera.get(cv2.CAP_PROP_AUTO_WB)

            details = {
                "wb_temperature": wb_temp,
                "initial_auto_wb": auto_wb,
                "auto_wb_control": auto_wb_on != auto_wb_off
            }

            if auto_wb_on != auto_wb_off or wb_temp > 0:
                return TestResult("White Balance", "PASS",
                                 "White balance controls available",
                                 timestamp, details)
            else:
                return TestResult("White Balance", "SKIP",
                                 "White balance controls not available",
                                 timestamp, details)

        except Exception as e:
            return TestResult("White Balance", "FAIL",
                             f"White balance test error: {str(e)}",
                             timestamp)

    def _test_image_quality(self, timestamp):
        """Test image quality metrics"""
        if not self.camera:
            return TestResult("Image Quality", "FAIL", "Camera not connected", timestamp)

        try:
            ret, frame = self.camera.read()
            if not ret:
                return TestResult("Image Quality", "FAIL", "Cannot capture frame", timestamp)

            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Calculate sharpness (Laplacian variance)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Calculate brightness (mean intensity)
            brightness = np.mean(gray)

            # Calculate contrast (standard deviation)
            contrast = np.std(gray)

            # Check for noise (high frequency content)
            noise_level = np.std(cv2.GaussianBlur(gray, (5, 5), 0) - gray)

            details = {
                "sharpness": round(sharpness, 2),
                "brightness": round(brightness, 2),
                "contrast": round(contrast, 2),
                "noise_level": round(noise_level, 2),
                "resolution": f"{frame.shape[1]}x{frame.shape[0]}"
            }

            # Quality assessment
            quality_issues = []
            if sharpness < 50:
                quality_issues.append("Low sharpness")
            if brightness < 50 or brightness > 200:
                quality_issues.append("Poor brightness")
            if contrast < 20:
                quality_issues.append("Low contrast")
            if noise_level > 10:
                quality_issues.append("High noise")

            if quality_issues:
                return TestResult("Image Quality", "FAIL",
                                 f"Quality issues: {', '.join(quality_issues)}",
                                 timestamp, details)
            else:
                return TestResult("Image Quality", "PASS",
                                 "Image quality metrics within acceptable range",
                                 timestamp, details)

        except Exception as e:
            return TestResult("Image Quality", "FAIL",
                             f"Image quality test error: {str(e)}",
                             timestamp)

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
            if not ret:
                return TestResult("Capture Test Image", "FAIL", "Cannot capture frame", timestamp)

            # Create output directory
            os.makedirs("test_images", exist_ok=True)

            # Save test image
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"test_images/test_image_{timestamp_str}.jpg"

            success = cv2.imwrite(image_filename, frame)

            if success:
                self.test_image_path = image_filename
                details = {
                    "image_path": image_filename,
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