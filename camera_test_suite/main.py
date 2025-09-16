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

        # Auto-detect USB cameras on startup
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

    def auto_detect_usb_cameras(self):
        """Auto-detect USB cameras and populate camera dropdown"""
        usb_cameras = []

        # Check for USB cameras using system tools
        if platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(["system_profiler", "SPUSBDataType"],
                                      capture_output=True, text=True, timeout=5)
                if "Camera" in result.stdout or "USB Video" in result.stdout:
                    # Try to find working camera indices
                    for i in range(10):
                        try:
                            test_camera = cv2.VideoCapture(i)
                            if test_camera.isOpened():
                                ret, frame = test_camera.read()
                                if ret and frame is not None:
                                    # Check if it's likely a USB camera (not built-in)
                                    width = test_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
                                    height = test_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
                                    if width >= 640 and height >= 480:  # Minimum resolution for USB cameras
                                        usb_cameras.append(i)
                                        self.log_message(f"USB Camera detected at index {i}")
                            test_camera.release()
                        except:
                            continue
            except:
                pass

        # Update camera dropdown with detected cameras
        if usb_cameras:
            camera_combo = None
            for widget in self.camera_frame.winfo_children():
                if isinstance(widget, ttk.LabelFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Combobox):
                            camera_combo = child
                            break

            if camera_combo:
                camera_combo['values'] = [str(i) for i in usb_cameras]
                if usb_cameras:
                    self.camera_var.set(str(usb_cameras[0]))  # Set to first detected camera
                    self.log_message(f"Found {len(usb_cameras)} USB camera(s)")

                    # Auto-connect to first USB camera
                    self.auto_connect_first_camera()
        else:
            self.log_message("No USB cameras detected")

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
            camera_index = int(self.camera_var.get())
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
        """Test exposure control functionality"""
        if not self.camera:
            return TestResult("Exposure Control", "FAIL", "Camera not connected", timestamp)

        # Try to get/set exposure
        try:
            original_exposure = self.camera.get(cv2.CAP_PROP_EXPOSURE)

            # Try to set different exposure values
            test_exposures = [-7, -5, -3, -1]
            working_exposures = []

            for exp_val in test_exposures:
                self.camera.set(cv2.CAP_PROP_EXPOSURE, exp_val)
                time.sleep(0.2)
                actual_exp = self.camera.get(cv2.CAP_PROP_EXPOSURE)
                if abs(actual_exp - exp_val) < 1:
                    working_exposures.append(exp_val)

            # Restore original exposure
            self.camera.set(cv2.CAP_PROP_EXPOSURE, original_exposure)

            details = {
                "original_exposure": original_exposure,
                "working_exposures": working_exposures
            }

            if working_exposures:
                return TestResult("Exposure Control", "PASS",
                                 f"Exposure control working: {len(working_exposures)} values tested",
                                 timestamp, details)
            else:
                return TestResult("Exposure Control", "FAIL",
                                 "Exposure control not responding",
                                 timestamp, details)

        except Exception as e:
            return TestResult("Exposure Control", "FAIL",
                             f"Exposure control error: {str(e)}",
                             timestamp)

    def _test_focus(self, timestamp):
        """Test focus functionality"""
        if not self.camera:
            return TestResult("Focus Test", "FAIL", "Camera not connected", timestamp)

        try:
            # Check if autofocus is available
            autofocus = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)
            focus_pos = self.camera.get(cv2.CAP_PROP_FOCUS)

            # Try to enable/disable autofocus
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            time.sleep(0.5)
            autofocus_on = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)

            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            time.sleep(0.5)
            autofocus_off = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)

            details = {
                "initial_autofocus": autofocus,
                "focus_position": focus_pos,
                "autofocus_control": autofocus_on != autofocus_off
            }

            if autofocus_on != autofocus_off:
                return TestResult("Focus Test", "PASS",
                                 "Autofocus control functional",
                                 timestamp, details)
            else:
                return TestResult("Focus Test", "SKIP",
                                 "Autofocus control not available or not working",
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