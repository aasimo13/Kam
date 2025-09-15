# USB Camera Hardware Test Suite

A comprehensive testing application for the WN-L2307k368 48MP BM USB camera module, designed for both macOS development and Raspberry Pi deployment.

## Features

### Hardware Tests
- **Camera Detection**: Verifies camera connectivity and basic functionality
- **Resolution Test**: Tests supported resolutions up to 8000x6000 (48MP)
- **Frame Rate Test**: Measures actual vs reported frame rates
- **Exposure Control**: Tests exposure adjustment capabilities
- **Focus Test**: Verifies autofocus functionality
- **White Balance**: Tests automatic and manual white balance
- **Image Quality**: Analyzes sharpness, brightness, contrast, and noise
- **USB Interface**: Tests data transfer rates and USB connectivity
- **Power Consumption**: Monitors camera power usage during operation
- **Test Image Capture**: Takes a test photo for quality assessment

### User Interface
- **Tabbed Interface**: Organized into Camera Control, Hardware Tests, Test Results, and Settings
- **Live Preview**: Real-time camera feed during testing
- **Detailed Reporting**: Pass/Fail results with detailed metrics
- **Export Functionality**: Generate PDF or JSON test reports
- **Customizable Settings**: Configure test parameters and camera settings

## WN-L2307k368 48MP Camera Specifications

- **Sensor**: 1/2-inch S5KGM1ST CMOS
- **Max Resolution**: 8000×6000 pixels (48MP)
- **Frame Rate**: Up to 8fps at maximum resolution
- **Pixel Size**: 0.8×0.8 μm
- **Field of View**: 79°
- **Interface**: USB 2.0, UVC compliant
- **Formats**: MJPEG, YUY2
- **Module Size**: 38×38mm

## Installation

### Prerequisites
- Python 3.7 or higher
- USB camera connected to system

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- opencv-python (camera operations)
- Pillow (image processing)
- numpy (numerical operations)
- psutil (system monitoring)
- matplotlib (data visualization)
- reportlab (PDF report generation)

## Usage

### Running the Application
```bash
python main.py
```

### Basic Workflow
1. **Connect Camera**: Use the Camera Control tab to connect to your camera
2. **Configure Tests**: Select which tests to run in the Hardware Tests tab
3. **Run Tests**: Execute individual tests or run all tests
4. **View Results**: Check detailed results in the Test Results tab
5. **Export Report**: Generate a comprehensive test report (PDF/JSON)

### Camera Control
- Select camera index (usually 0 for the first camera)
- View live preview feed
- Monitor camera specifications and current settings

### Test Configuration
- Choose which hardware tests to perform
- Set test timeout and resolution preferences
- Enable/disable test image saving

## Cross-Platform Support

### macOS Development
- Full GUI support with Tkinter
- System profiler integration for USB device detection
- Battery monitoring support

### Raspberry Pi Deployment
- Optimized for headless operation
- GPIO integration ready
- Lightweight resource usage

## Test Results

Each test provides:
- **Status**: PASS, FAIL, or SKIP
- **Message**: Human-readable description
- **Timestamp**: When the test was performed
- **Details**: Technical metrics and measurements

### Test Report Features
- Executive summary with pass/fail statistics
- Detailed test results with timestamps
- Test image capture included in report
- Professional PDF formatting
- JSON export for data analysis

## Troubleshooting

### Common Issues
1. **Camera Not Detected**
   - Check USB connection
   - Verify camera index (try 0, 1, 2...)
   - Ensure no other applications are using the camera

2. **Permission Errors**
   - Grant camera access permissions
   - Run with appropriate user privileges

3. **Performance Issues**
   - Close other camera applications
   - Use lower resolution for testing if needed
   - Check USB port capabilities (USB 2.0 required)

### Platform-Specific Notes

#### macOS
- May require camera permissions in System Preferences
- Use built-in USB camera detection

#### Raspberry Pi
- Ensure adequate power supply for camera
- May need to enable camera in raspi-config
- Consider heat dissipation for extended testing

## Development

### Project Structure
```
├── main.py              # Main application
├── requirements.txt     # Python dependencies
├── test_images/         # Captured test images
└── README.md           # This file
```

### Extending Tests
Add new tests by implementing methods in the `_run_single_test()` function following the pattern:
```python
def _test_new_feature(self, timestamp):
    # Implement test logic
    return TestResult("Test Name", "PASS/FAIL", "Message", timestamp, details)
```

## Hardware Specifications Testing

The application specifically tests the WN-L2307k368 camera's capabilities:

- **Maximum resolution verification** (8000x6000)
- **Frame rate performance** at various resolutions
- **USB 2.0 interface compliance**
- **UVC compatibility**
- **Image sensor functionality**
- **Optical performance** (79° FOV verification)

## License

This project is designed for hardware testing and quality assurance of USB camera modules.

## Support

For issues or questions:
1. Check camera specifications match WN-L2307k368
2. Verify USB connection and system compatibility
3. Review test logs in the application output