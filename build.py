#!/usr/bin/env python3
"""
Build script for USB Camera Test Suite
Handles building executables, packages, and installers for all platforms
"""

import os
import sys
import subprocess
import shutil
import platform
import zipfile
import tarfile
from pathlib import Path
import argparse

class Builder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.platform = platform.system().lower()

        # Clean up previous builds
        self.clean()

    def clean(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning previous builds...")

        dirs_to_clean = [self.build_dir, self.dist_dir, "*.egg-info"]

        for dir_pattern in dirs_to_clean:
            if "*" in str(dir_pattern):
                # Handle glob patterns
                for path in self.project_dir.glob(str(dir_pattern)):
                    if path.is_dir():
                        shutil.rmtree(path)
                        print(f"   Removed {path}")
            else:
                path = Path(dir_pattern)
                if path.exists():
                    shutil.rmtree(path)
                    print(f"   Removed {path}")

    def install_build_dependencies(self):
        """Install required build tools"""
        print("📦 Installing build dependencies...")

        build_deps = [
            "wheel",
            "setuptools>=65.0.0",
            "pyinstaller>=5.0.0",
            "pillow",  # For icon processing
        ]

        for dep in build_deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep],
                             check=True, capture_output=True)
                print(f"   ✓ {dep}")
            except subprocess.CalledProcessError as e:
                print(f"   ✗ Failed to install {dep}: {e}")
                return False

        return True

    def build_python_package(self):
        """Build Python wheel and source distribution"""
        print("🐍 Building Python package...")

        try:
            # Build wheel
            subprocess.run([sys.executable, "setup.py", "bdist_wheel"],
                          check=True, cwd=self.project_dir)
            print("   ✓ Wheel package created")

            # Build source distribution
            subprocess.run([sys.executable, "setup.py", "sdist"],
                          check=True, cwd=self.project_dir)
            print("   ✓ Source distribution created")

            return True

        except subprocess.CalledProcessError as e:
            print(f"   ✗ Python package build failed: {e}")
            return False

    def build_executable(self):
        """Build standalone executable with PyInstaller"""
        print(f"🔨 Building executable for {self.platform}...")

        try:
            # Run PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                "pyinstaller.spec"
            ]

            subprocess.run(cmd, check=True, cwd=self.project_dir)
            print(f"   ✓ Executable created for {self.platform}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"   ✗ Executable build failed: {e}")
            return False

    def create_installer_package(self):
        """Create platform-specific installer package"""
        print(f"📦 Creating installer package for {self.platform}...")

        if self.platform == "windows":
            return self._create_windows_installer()
        elif self.platform == "darwin":
            return self._create_macos_installer()
        elif self.platform == "linux":
            return self._create_linux_installer()
        else:
            print(f"   ⚠️  No installer package available for {self.platform}")
            return True

    def _create_windows_installer(self):
        """Create Windows installer package"""
        try:
            # Create installer directory
            installer_dir = self.dist_dir / "windows-installer"
            installer_dir.mkdir(exist_ok=True)

            # Copy executable
            exe_path = self.dist_dir / "camera-test-suite.exe"
            if exe_path.exists():
                shutil.copy2(exe_path, installer_dir)

            # Copy installation script
            install_script = self.project_dir / "install.bat"
            if install_script.exists():
                shutil.copy2(install_script, installer_dir)

            # Copy assets
            assets_dir = self.project_dir / "assets"
            if assets_dir.exists():
                shutil.copytree(assets_dir, installer_dir / "assets")

            # Create ZIP package
            zip_path = self.dist_dir / "usb-camera-test-suite-windows.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in installer_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(installer_dir)
                        zf.write(file_path, arcname)

            print(f"   ✓ Windows installer package: {zip_path}")
            return True

        except Exception as e:
            print(f"   ✗ Windows installer creation failed: {e}")
            return False

    def _create_macos_installer(self):
        """Create macOS installer package"""
        try:
            # Create installer directory
            installer_dir = self.dist_dir / "macos-installer"
            installer_dir.mkdir(exist_ok=True)

            # Copy app bundle
            app_path = self.dist_dir / "USB Camera Test Suite.app"
            if app_path.exists():
                shutil.copytree(app_path, installer_dir / "USB Camera Test Suite.app")

            # Copy installation script
            install_script = self.project_dir / "install.sh"
            if install_script.exists():
                shutil.copy2(install_script, installer_dir)
                os.chmod(installer_dir / "install.sh", 0o755)

            # Create DMG-like structure
            applications_link = installer_dir / "Applications"
            if not applications_link.exists():
                applications_link.symlink_to("/Applications")

            # Create tarball
            tar_path = self.dist_dir / "usb-camera-test-suite-macos.tar.gz"
            with tarfile.open(tar_path, 'w:gz') as tf:
                for file_path in installer_dir.rglob('*'):
                    if file_path.is_file() or file_path.is_symlink():
                        arcname = file_path.relative_to(installer_dir)
                        tf.add(file_path, arcname)

            print(f"   ✓ macOS installer package: {tar_path}")
            return True

        except Exception as e:
            print(f"   ✗ macOS installer creation failed: {e}")
            return False

    def _create_linux_installer(self):
        """Create Linux installer package"""
        try:
            # Create installer directory
            installer_dir = self.dist_dir / "linux-installer"
            installer_dir.mkdir(exist_ok=True)

            # Copy executable
            exe_path = self.dist_dir / "camera-test-suite"
            if exe_path.exists():
                shutil.copy2(exe_path, installer_dir)
                os.chmod(installer_dir / "camera-test-suite", 0o755)

            # Copy installation script
            install_script = self.project_dir / "install.sh"
            if install_script.exists():
                shutil.copy2(install_script, installer_dir)
                os.chmod(installer_dir / "install.sh", 0o755)

            # Copy desktop integration
            assets_dir = self.project_dir / "assets"
            if assets_dir.exists():
                shutil.copytree(assets_dir, installer_dir / "assets")

            # Create tarball
            tar_path = self.dist_dir / "usb-camera-test-suite-linux.tar.gz"
            with tarfile.open(tar_path, 'w:gz') as tf:
                for file_path in installer_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(installer_dir)
                        tf.add(file_path, arcname)

            print(f"   ✓ Linux installer package: {tar_path}")
            return True

        except Exception as e:
            print(f"   ✗ Linux installer creation failed: {e}")
            return False

    def build_all(self, skip_executable=False):
        """Build everything"""
        print("🚀 Building USB Camera Test Suite...")
        print(f"Platform: {self.platform}")
        print(f"Python: {sys.version}")
        print("-" * 50)

        success = True

        # Install build dependencies
        if not self.install_build_dependencies():
            success = False

        # Build Python package
        if success and not self.build_python_package():
            success = False

        # Build executable (optional, can be slow)
        if success and not skip_executable and not self.build_executable():
            success = False

        # Create installer package
        if success and not self.create_installer_package():
            success = False

        # Summary
        print("-" * 50)
        if success:
            print("✅ Build completed successfully!")
            print("\nBuild artifacts:")
            if self.dist_dir.exists():
                for item in self.dist_dir.iterdir():
                    print(f"   {item}")
        else:
            print("❌ Build failed!")

        return success

def main():
    parser = argparse.ArgumentParser(description="Build USB Camera Test Suite")
    parser.add_argument("--skip-executable", action="store_true",
                       help="Skip building executable (faster)")
    parser.add_argument("--clean-only", action="store_true",
                       help="Only clean build artifacts")

    args = parser.parse_args()

    builder = Builder()

    if args.clean_only:
        print("✅ Cleanup completed!")
        return 0

    success = builder.build_all(skip_executable=args.skip_executable)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())