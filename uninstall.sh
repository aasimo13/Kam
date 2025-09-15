#!/bin/bash
# USB Camera Test Suite - Universal Uninstaller Script
# Safely removes all installed components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}USB Camera Test Suite - Uninstaller${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Detect platform
PLATFORM=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        PLATFORM="raspberry-pi"
    else
        PLATFORM="linux"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
else
    echo -e "${RED}❌ Unsupported platform: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}Platform: $PLATFORM${NC}"
echo ""

# Confirm uninstallation
echo -e "${YELLOW}This will completely remove USB Camera Test Suite from your system.${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  • Application files"
echo -e "  • Desktop shortcuts"
echo -e "  • Command-line tools"
echo -e "  • Configuration files"
echo -e "  • Virtual environment"
echo ""
read -p "Continue with uninstallation? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Uninstallation cancelled.${NC}"
    exit 0
fi

echo -e "\n${BLUE}🗑️  Starting uninstallation...${NC}"

# Function to safely remove file/directory
safe_remove() {
    local path="$1"
    local description="$2"

    if [ -e "$path" ]; then
        rm -rf "$path" 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Could not remove $description: $path${NC}"
            return 1
        }
        echo -e "${GREEN}✓ Removed $description${NC}"
    else
        echo -e "${YELLOW}• $description not found${NC}"
    fi
}

# Remove virtual environment
safe_remove "$HOME/.camera-test-suite" "virtual environment"

# Remove command-line shortcuts
safe_remove "$HOME/.local/bin/camera-test-gui" "GUI command shortcut"
safe_remove "$HOME/.local/bin/camera-test-cli" "CLI command shortcut"

# Platform-specific cleanup
case $PLATFORM in
    "macos")
        echo -e "\n${BLUE}🍎 Cleaning up macOS integration...${NC}"

        # Remove app bundle
        safe_remove "$HOME/Applications/USB Camera Test Suite.app" "macOS app bundle"
        safe_remove "/Applications/USB Camera Test Suite.app" "system-wide macOS app bundle"

        # Remove Launch Services cache (requires restart)
        if command -v /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister >/dev/null 2>&1; then
            echo -e "${YELLOW}Rebuilding Launch Services database...${NC}"
            /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -kill -r -domain local -domain system -domain user
        fi
        ;;

    "linux"|"raspberry-pi")
        echo -e "\n${BLUE}🐧 Cleaning up Linux integration...${NC}"

        # Remove desktop entry
        safe_remove "$HOME/.local/share/applications/usb-camera-test-suite.desktop" "desktop entry"

        # Update desktop database
        if command -v update-desktop-database >/dev/null 2>&1; then
            echo -e "${YELLOW}Updating desktop database...${NC}"
            update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
        fi

        # Remove any system-wide desktop entries (requires sudo)
        if [ -f "/usr/share/applications/usb-camera-test-suite.desktop" ]; then
            echo -e "${YELLOW}System-wide desktop entry found. Remove it manually with:${NC}"
            echo -e "  ${GREEN}sudo rm /usr/share/applications/usb-camera-test-suite.desktop${NC}"
        fi
        ;;
esac

# Remove configuration and data directories
echo -e "\n${BLUE}📁 Cleaning up user data...${NC}"

safe_remove "$HOME/.config/camera-test-suite" "configuration directory"
safe_remove "$HOME/.local/share/camera-test-suite" "data directory"

# Clean up PATH modifications (basic cleanup)
echo -e "\n${BLUE}🔧 Cleaning up PATH modifications...${NC}"

# Remove from .bashrc
if [ -f "$HOME/.bashrc" ]; then
    if grep -q "USB Camera Test Suite" "$HOME/.bashrc"; then
        echo -e "${YELLOW}Found PATH modifications in .bashrc${NC}"
        # Create backup
        cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%s)"
        # Remove our lines
        grep -v "USB Camera Test Suite" "$HOME/.bashrc" > "$HOME/.bashrc.tmp" && mv "$HOME/.bashrc.tmp" "$HOME/.bashrc"
        grep -v 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" > "$HOME/.bashrc.tmp" && mv "$HOME/.bashrc.tmp" "$HOME/.bashrc" 2>/dev/null || true
        echo -e "${GREEN}✓ Cleaned up .bashrc${NC}"
    fi
fi

# Remove from .zshrc
if [ -f "$HOME/.zshrc" ]; then
    if grep -q "USB Camera Test Suite" "$HOME/.zshrc"; then
        echo -e "${YELLOW}Found PATH modifications in .zshrc${NC}"
        # Create backup
        cp "$HOME/.zshrc" "$HOME/.zshrc.backup.$(date +%s)"
        # Remove our lines
        grep -v "USB Camera Test Suite" "$HOME/.zshrc" > "$HOME/.zshrc.tmp" && mv "$HOME/.zshrc.tmp" "$HOME/.zshrc"
        grep -v 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.zshrc" > "$HOME/.zshrc.tmp" && mv "$HOME/.zshrc.tmp" "$HOME/.zshrc" 2>/dev/null || true
        echo -e "${GREEN}✓ Cleaned up .zshrc${NC}"
    fi
fi

# Remove any leftover test images
echo -e "\n${BLUE}🖼️  Cleaning up test images...${NC}"
safe_remove "$HOME/test_images" "test images directory"
safe_remove "$(pwd)/test_images" "local test images directory"

# Check for any remaining pip packages
echo -e "\n${BLUE}📦 Checking for pip packages...${NC}"
if pip list | grep -i "usb-camera-test-suite" >/dev/null 2>&1; then
    echo -e "${YELLOW}Found pip package. Uninstalling...${NC}"
    pip uninstall usb-camera-test-suite -y 2>/dev/null || true
    echo -e "${GREEN}✓ Pip package removed${NC}"
else
    echo -e "${YELLOW}• No pip package found${NC}"
fi

# Final cleanup check
echo -e "\n${BLUE}🔍 Final cleanup check...${NC}"

remaining_files=()
check_paths=(
    "$HOME/.camera-test-suite"
    "$HOME/.local/bin/camera-test-gui"
    "$HOME/.local/bin/camera-test-cli"
    "$HOME/.local/share/applications/usb-camera-test-suite.desktop"
    "$HOME/Applications/USB Camera Test Suite.app"
)

for path in "${check_paths[@]}"; do
    if [ -e "$path" ]; then
        remaining_files+=("$path")
    fi
done

if [ ${#remaining_files[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some files could not be removed:${NC}"
    for file in "${remaining_files[@]}"; do
        echo -e "  $file"
    done
    echo -e "${YELLOW}You may need to remove these manually.${NC}"
else
    echo -e "${GREEN}✓ All files successfully removed${NC}"
fi

# Summary
echo -e "\n${GREEN}===============================================${NC}"
echo -e "${GREEN}Uninstallation completed!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo -e "${BLUE}What was removed:${NC}"
echo -e "  ✓ Application files and virtual environment"
echo -e "  ✓ Command-line tools"
echo -e "  ✓ Desktop integration"
echo -e "  ✓ Configuration files"
echo ""

if [ "$PLATFORM" = "macos" ]; then
    echo -e "${YELLOW}Note: You may need to restart Finder for changes to take effect.${NC}"
fi

if [ ${#remaining_files[@]} -eq 0 ]; then
    echo -e "${GREEN}USB Camera Test Suite has been completely removed from your system.${NC}"
else
    echo -e "${YELLOW}Uninstallation mostly complete. Some files may need manual removal.${NC}"
fi

echo -e "\n${BLUE}Thank you for using USB Camera Test Suite!${NC}"