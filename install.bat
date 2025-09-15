@echo off
REM USB Camera Test Suite - Windows Installation Script
REM Handles Python installation, dependencies, and desktop integration

setlocal EnableDelayedExpansion

REM Application info
set APP_NAME=USB Camera Test Suite
set APP_VERSION=1.0.0
set PACKAGE_NAME=usb-camera-test-suite

echo ====================================
echo %APP_NAME% Installer v%APP_VERSION%
echo ====================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator - System-wide installation
    set INSTALL_MODE=system
) else (
    echo Running as User - User installation
    set INSTALL_MODE=user
)

echo.
echo This will install %APP_NAME% v%APP_VERSION% on Windows
echo Install mode: %INSTALL_MODE%
echo.
set /p CONTINUE="Continue? (y/N): "
if /i not "%CONTINUE%"=="y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo Starting installation...

REM Create installation directory
set INSTALL_DIR=%USERPROFILE%\.camera-test-suite
if exist "%INSTALL_DIR%" (
    echo Removing existing installation...
    rmdir /s /q "%INSTALL_DIR%"
)
mkdir "%INSTALL_DIR%"

REM Check for Python
echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python not found. Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% found

REM Check Python version (simplified check for 3.x)
python -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)"
if %errorLevel% neq 0 (
    echo Python 3.7+ required, found %PYTHON_VERSION%
    pause
    exit /b 1
)

REM Check pip
echo.
echo Checking pip...
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing pip...
    python -m ensurepip --default-pip
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv "%INSTALL_DIR%"

REM Activate virtual environment
call "%INSTALL_DIR%\Scripts\activate.bat"

REM Upgrade pip in venv
python -m pip install --upgrade pip setuptools wheel

REM Install Visual C++ Build Tools if needed
echo.
echo Checking for Visual C++ Build Tools...
python -c "import distutils.util" >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Visual C++ Build Tools may be required for some packages
    echo You can download them from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

REM Install the application
echo.
echo Installing USB Camera Test Suite...
if exist "setup.py" (
    echo Installing from source...
    pip install -e .
) else (
    echo ERROR: setup.py not found. Please run this script from the project directory.
    pause
    exit /b 1
)

REM Install Windows-specific packages
echo Installing Windows-specific packages...
pip install pywin32

REM Create desktop shortcuts
echo.
echo Creating desktop shortcuts...

REM Create GUI shortcut
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_GUI=%DESKTOP%\USB Camera Test Suite.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_GUI%'); $Shortcut.TargetPath = '%INSTALL_DIR%\Scripts\python.exe'; $Shortcut.Arguments = '-m camera_test_suite'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = 'shell32.dll,23'; $Shortcut.Description = 'USB Camera Hardware Test Suite'; $Shortcut.Save()"

REM Create Start Menu shortcuts
set STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
mkdir "%STARTMENU%\USB Camera Test Suite" 2>nul

REM GUI Start Menu shortcut
set STARTMENU_GUI=%STARTMENU%\USB Camera Test Suite\USB Camera Test Suite.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU_GUI%'); $Shortcut.TargetPath = '%INSTALL_DIR%\Scripts\python.exe'; $Shortcut.Arguments = '-m camera_test_suite'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = 'shell32.dll,23'; $Shortcut.Description = 'USB Camera Hardware Test Suite - GUI'; $Shortcut.Save()"

REM CLI Start Menu shortcut
set STARTMENU_CLI=%STARTMENU%\USB Camera Test Suite\USB Camera Test Suite (CLI).lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU_CLI%'); $Shortcut.TargetPath = '%INSTALL_DIR%\Scripts\python.exe'; $Shortcut.Arguments = '-m camera_test_suite.cli'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = 'shell32.dll,22'; $Shortcut.Description = 'USB Camera Hardware Test Suite - Command Line'; $Shortcut.Save()"

REM Create batch files for command line usage
echo.
echo Creating command-line tools...

REM Create batch file directory
set BATCH_DIR=%USERPROFILE%\.local\bin
mkdir "%BATCH_DIR%" 2>nul

REM GUI batch file
echo @echo off > "%BATCH_DIR%\camera-test-gui.bat"
echo call "%INSTALL_DIR%\Scripts\activate.bat" >> "%BATCH_DIR%\camera-test-gui.bat"
echo python -m camera_test_suite %%* >> "%BATCH_DIR%\camera-test-gui.bat"

REM CLI batch file
echo @echo off > "%BATCH_DIR%\camera-test-cli.bat"
echo call "%INSTALL_DIR%\Scripts\activate.bat" >> "%BATCH_DIR%\camera-test-cli.bat"
echo python -m camera_test_suite.cli %%* >> "%BATCH_DIR%\camera-test-cli.bat"

REM Add to PATH if not already there
echo.
echo Checking PATH configuration...
echo %PATH% | findstr /i "%BATCH_DIR%" >nul
if %errorLevel% neq 0 (
    echo Adding to PATH...
    REM Add to user PATH
    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%B"
    if defined CURRENT_PATH (
        reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%CURRENT_PATH%;%BATCH_DIR%" /f >nul
    ) else (
        reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%BATCH_DIR%" /f >nul
    )

    REM Broadcast environment change
    powershell -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';%BATCH_DIR%', 'User')"
)

REM Create uninstaller
echo.
echo Creating uninstaller...
set UNINSTALLER=%INSTALL_DIR%\uninstall.bat
echo @echo off > "%UNINSTALLER%"
echo echo Uninstalling USB Camera Test Suite... >> "%UNINSTALLER%"
echo rmdir /s /q "%INSTALL_DIR%" >> "%UNINSTALLER%"
echo del "%SHORTCUT_GUI%" 2^>nul >> "%UNINSTALLER%"
echo rmdir /s /q "%STARTMENU%\USB Camera Test Suite" 2^>nul >> "%UNINSTALLER%"
echo del "%BATCH_DIR%\camera-test-gui.bat" 2^>nul >> "%UNINSTALLER%"
echo del "%BATCH_DIR%\camera-test-cli.bat" 2^>nul >> "%UNINSTALLER%"
echo echo USB Camera Test Suite uninstalled successfully. >> "%UNINSTALLER%"
echo pause >> "%UNINSTALLER%"

REM Add uninstaller to Start Menu
set UNINSTALL_SHORTCUT=%STARTMENU%\USB Camera Test Suite\Uninstall.lnk
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%UNINSTALL_SHORTCUT%'); $Shortcut.TargetPath = '%UNINSTALLER%'; $Shortcut.IconLocation = 'shell32.dll,31'; $Shortcut.Description = 'Uninstall USB Camera Test Suite'; $Shortcut.Save()"

REM Test installation
echo.
echo Testing installation...
call "%INSTALL_DIR%\Scripts\activate.bat"
python -c "import camera_test_suite; print('✓ Package import successful')"
if %errorLevel% neq 0 (
    echo ✗ Installation test failed
    pause
    exit /b 1
)

REM Installation complete
echo.
echo ====================================
echo Installation completed successfully!
echo ====================================
echo.
echo Usage:
echo   Desktop: Use shortcuts on Desktop and Start Menu
echo   Command: camera-test-gui (GUI mode)
echo   Command: camera-test-cli (CLI mode)
echo.
echo Note: You may need to restart your command prompt
echo       for the new PATH to take effect.
echo.
echo Installation directory: %INSTALL_DIR%
echo.

REM Ask to launch
set /p LAUNCH="Launch USB Camera Test Suite now? (y/N): "
if /i "%LAUNCH%"=="y" (
    start "" "%SHORTCUT_GUI%"
)

echo.
echo Installation complete! Press any key to exit.
pause >nul