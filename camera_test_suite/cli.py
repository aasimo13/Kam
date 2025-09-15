#!/usr/bin/env python3
"""
Command-line interface for USB Camera Test Suite
Provides headless operation for automated testing
"""

import argparse
import sys
import json
import cv2
import time
from datetime import datetime
from .main import CameraHardwareTester, TestResult

class CLITester:
    def __init__(self):
        self.camera = None
        self.results = []

    def run_headless_tests(self, camera_index=0, output_file=None, tests=None):
        """Run tests without GUI"""
        print(f"USB Camera Test Suite v1.0.0 - CLI Mode")
        print(f"Testing camera at index {camera_index}")
        print("-" * 50)

        # Connect to camera
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                raise Exception("Camera not found")
            print("✓ Camera connected successfully")
        except Exception as e:
            print(f"✗ Camera connection failed: {e}")
            return False

        # Available tests
        available_tests = [
            "Camera Detection", "Resolution Test", "Frame Rate Test",
            "Exposure Control", "Focus Test", "White Balance",
            "Image Quality", "USB Interface", "Power Consumption",
            "Capture Test Image"
        ]

        # Use specified tests or all tests
        test_list = tests if tests else available_tests

        print(f"\nRunning {len(test_list)} tests...")
        print("-" * 50)

        # Create temporary GUI instance for test methods
        gui_tester = CameraHardwareTester()
        gui_tester.camera = self.camera

        # Run tests
        for i, test_name in enumerate(test_list):
            print(f"[{i+1}/{len(test_list)}] {test_name}...", end=" ")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = gui_tester._run_single_test(test_name)
            self.results.append(result)

            # Print result
            status_symbol = "✓" if result.status == "PASS" else "✗" if result.status == "FAIL" else "⚠"
            print(f"{status_symbol} {result.status}")
            if result.message:
                print(f"    {result.message}")

        # Clean up
        if self.camera:
            self.camera.release()

        # Print summary
        self.print_summary()

        # Save results
        if output_file:
            self.save_results(output_file)

        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

        pass_count = sum(1 for r in self.results if r.status == "PASS")
        fail_count = sum(1 for r in self.results if r.status == "FAIL")
        skip_count = sum(1 for r in self.results if r.status == "SKIP")

        print(f"Total Tests: {len(self.results)}")
        print(f"Passed:      {pass_count}")
        print(f"Failed:      {fail_count}")
        print(f"Skipped:     {skip_count}")

        success_rate = (pass_count / len(self.results)) * 100 if self.results else 0
        print(f"Success Rate: {success_rate:.1f}%")

        if fail_count > 0:
            print(f"\nFailed Tests:")
            for result in self.results:
                if result.status == "FAIL":
                    print(f"  - {result.test_name}: {result.message}")

    def save_results(self, filename):
        """Save results to file"""
        try:
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "camera_model": "WN-L2307k368 48MP BM",
                "test_mode": "CLI",
                "summary": {
                    "total": len(self.results),
                    "passed": sum(1 for r in self.results if r.status == "PASS"),
                    "failed": sum(1 for r in self.results if r.status == "FAIL"),
                    "skipped": sum(1 for r in self.results if r.status == "SKIP")
                },
                "results": []
            }

            for result in self.results:
                report_data["results"].append({
                    "test_name": result.test_name,
                    "status": result.status,
                    "message": result.message,
                    "timestamp": result.timestamp,
                    "details": result.details
                })

            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)

            print(f"\n✓ Results saved to {filename}")

        except Exception as e:
            print(f"\n✗ Failed to save results: {e}")

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="USB Camera Hardware Test Suite - CLI Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  camera-test-cli                           # Run all tests on camera 0
  camera-test-cli -c 1                      # Test camera 1
  camera-test-cli -o results.json           # Save results to file
  camera-test-cli -t "Camera Detection"     # Run specific test
  camera-test-cli --list-cameras            # List available cameras
        """
    )

    parser.add_argument("-c", "--camera", type=int, default=0,
                       help="Camera index to test (default: 0)")

    parser.add_argument("-o", "--output", type=str,
                       help="Output file for test results (JSON format)")

    parser.add_argument("-t", "--tests", nargs="+",
                       help="Specific tests to run")

    parser.add_argument("--list-cameras", action="store_true",
                       help="List available cameras and exit")

    parser.add_argument("--gui", action="store_true",
                       help="Launch GUI mode instead")

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args()

    if args.gui:
        # Launch GUI mode
        from .main import main as gui_main
        gui_main()
        return

    if args.list_cameras:
        # List available cameras
        print("Scanning for cameras...")
        found_cameras = []

        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    height, width = frame.shape[:2]
                    found_cameras.append((i, width, height))
                cap.release()

        if found_cameras:
            print("Available cameras:")
            for idx, width, height in found_cameras:
                print(f"  Camera {idx}: {width}x{height}")
        else:
            print("No cameras found")
        return

    # Run CLI tests
    cli_tester = CLITester()
    success = cli_tester.run_headless_tests(
        camera_index=args.camera,
        output_file=args.output,
        tests=args.tests
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()