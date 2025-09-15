@echo off
REM USB Camera Test Suite - Windows Uninstaller
REM Safely removes all installed components

setlocal EnableDelayedExpansion

echo =====================================
echo USB Camera Test Suite - Uninstaller
echo =====================================
echo.

echo This will completely remove USB Camera Test Suite from your system.
echo This includes:
echo   - Application files
echo   - Desktop shortcuts
echo   - Start Menu entries
echo   - Command-line tools
echo   - Virtual environment
echo.

set /p CONTINUE="Continue with uninstallation? (y/N): "
if /i not "%CONTINUE%"=="y" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo Starting uninstallation...

REM Set paths
set INSTALL_DIR=%USERPROFILE%\.camera-test-suite
set DESKTOP=%USERPROFILE%\Desktop
set STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
set BATCH_DIR=%USERPROFILE%\.local\bin

echo.
echo Removing application files...

REM Remove virtual environment
if exist "%INSTALL_DIR%" (
    echo Removing virtual environment...
    rmdir /s /q "%INSTALL_DIR%" >nul 2>&1
    if exist "%INSTALL_DIR%" (
        echo WARNING: Could not remove %INSTALL_DIR%
        echo You may need to remove it manually
    ) else (
        echo ✓ Virtual environment removed
    )
) else (
    echo • Virtual environment not found
)

echo.
echo Removing shortcuts and menu entries...

REM Remove desktop shortcut
if exist "%DESKTOP%\USB Camera Test Suite.lnk" (
    del "%DESKTOP%\USB Camera Test Suite.lnk" >nul 2>&1
    echo ✓ Desktop shortcut removed
) else (
    echo • Desktop shortcut not found
)

REM Remove Start Menu folder
if exist "%STARTMENU%\USB Camera Test Suite" (
    rmdir /s /q "%STARTMENU%\USB Camera Test Suite" >nul 2>&1
    if exist "%STARTMENU%\USB Camera Test Suite" (
        echo WARNING: Could not remove Start Menu entries
    ) else (
        echo ✓ Start Menu entries removed
    )
) else (
    echo • Start Menu entries not found
)

echo.
echo Removing command-line tools...

REM Remove batch files
if exist "%BATCH_DIR%\camera-test-gui.bat" (
    del "%BATCH_DIR%\camera-test-gui.bat" >nul 2>&1
    echo ✓ GUI command tool removed
) else (
    echo • GUI command tool not found
)

if exist "%BATCH_DIR%\camera-test-cli.bat" (
    del "%BATCH_DIR%\camera-test-cli.bat" >nul 2>&1
    echo ✓ CLI command tool removed
) else (
    echo • CLI command tool not found
)

REM Remove batch directory if empty
if exist "%BATCH_DIR%" (
    dir /b "%BATCH_DIR%" | findstr . >nul
    if errorlevel 1 (
        rmdir "%BATCH_DIR%" >nul 2>&1
        echo ✓ Command tools directory removed
    )
)

echo.
echo Cleaning up PATH modifications...

REM Remove from PATH (this is complex in batch, so we'll just warn user)
echo %PATH% | findstr /i "%BATCH_DIR%" >nul
if not errorlevel 1 (
    echo WARNING: PATH modifications detected
    echo Please manually remove the following from your PATH environment variable:
    echo   %BATCH_DIR%
    echo You can do this in: Control Panel ^> System ^> Advanced System Settings ^> Environment Variables
    echo.
)

echo.
echo Checking for pip packages...

REM Try to uninstall pip package
pip list | findstr /i "usb-camera-test-suite" >nul 2>&1
if not errorlevel 1 (
    echo Found pip package. Uninstalling...
    pip uninstall usb-camera-test-suite -y >nul 2>&1
    echo ✓ Pip package removed
) else (
    echo • No pip package found
)

echo.
echo Cleaning up user data...

REM Remove configuration directories
if exist "%USERPROFILE%\.config\camera-test-suite" (
    rmdir /s /q "%USERPROFILE%\.config\camera-test-suite" >nul 2>&1
    echo ✓ Configuration directory removed
) else (
    echo • Configuration directory not found
)

if exist "%USERPROFILE%\AppData\Local\camera-test-suite" (
    rmdir /s /q "%USERPROFILE%\AppData\Local\camera-test-suite" >nul 2>&1
    echo ✓ Local data directory removed
) else (
    echo • Local data directory not found
)

REM Clean up test images
if exist "%USERPROFILE%\test_images" (
    rmdir /s /q "%USERPROFILE%\test_images" >nul 2>&1
    echo ✓ Test images directory removed
) else (
    echo • Test images directory not found
)

if exist "test_images" (
    rmdir /s /q "test_images" >nul 2>&1
    echo ✓ Local test images removed
)

echo.
echo Performing final cleanup check...

REM Check for remaining files
set REMAINING=0

if exist "%INSTALL_DIR%" (
    echo WARNING: Installation directory still exists: %INSTALL_DIR%
    set REMAINING=1
)

if exist "%DESKTOP%\USB Camera Test Suite.lnk" (
    echo WARNING: Desktop shortcut still exists
    set REMAINING=1
)

if exist "%STARTMENU%\USB Camera Test Suite" (
    echo WARNING: Start Menu entries still exist
    set REMAINING=1
)

if exist "%BATCH_DIR%\camera-test-gui.bat" (
    echo WARNING: GUI command tool still exists
    set REMAINING=1
)

if exist "%BATCH_DIR%\camera-test-cli.bat" (
    echo WARNING: CLI command tool still exists
    set REMAINING=1
)

echo.
echo ===============================================
echo Uninstallation completed!
echo ===============================================
echo.

echo What was removed:
echo   ✓ Application files and virtual environment
echo   ✓ Desktop and Start Menu shortcuts
echo   ✓ Command-line tools
echo   ✓ Configuration files

if %REMAINING%==1 (
    echo.
    echo WARNING: Some files could not be removed automatically.
    echo You may need to remove them manually or restart Windows.
    echo.
    echo USB Camera Test Suite has been mostly removed from your system.
) else (
    echo.
    echo ✓ All files successfully removed
    echo.
    echo USB Camera Test Suite has been completely removed from your system.
)

echo.
echo Thank you for using USB Camera Test Suite!
echo.
pause