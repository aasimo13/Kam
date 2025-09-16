#!/bin/bash

# USB Camera Tester - Auto-Executable Installation Script
# This script automatically makes itself executable and runs the installer

set -e

# Function to make script executable and run installer
run_installer() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local install_script="$script_dir/install.sh"

    echo "🚀 USB Camera Tester Auto-Installer"
    echo "===================================="
    echo ""

    # Check if install.sh exists
    if [ ! -f "$install_script" ]; then
        echo "❌ Error: install.sh not found in $script_dir"
        exit 1
    fi

    # Make install.sh executable if it isn't already
    if [ ! -x "$install_script" ]; then
        echo "🔧 Making install.sh executable..."
        chmod +x "$install_script"
    fi

    # Run the installer
    echo "▶️  Running USB Camera Tester installer..."
    echo ""
    "$install_script"
}

# Check if we're being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Make this script executable if it isn't already
    if [ ! -x "${BASH_SOURCE[0]}" ]; then
        chmod +x "${BASH_SOURCE[0]}" 2>/dev/null || {
            echo "⚠️  Please run: chmod +x $(basename "${BASH_SOURCE[0]}")"
            echo "Then run: ./$(basename "${BASH_SOURCE[0]}")"
            exit 1
        }
    fi

    run_installer
fi