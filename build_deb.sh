#!/bin/bash
set -e

# Configuration
APP_NAME="hyper-download-manager"
# Use a build directory in a location that supports symlinks (e.g., home dir)
TEMP_BUILD_DIR="/home/jackthesparrow/.gemini/FDM_build"
FINAL_OUTPUT_DIR="$(pwd)/Installers/deb"
VENV_PYTHON="/home/jackthesparrow/.gemini/FDM_venv/bin/python"
VENV_PYINSTALLER="/home/jackthesparrow/.gemini/FDM_venv/bin/pyinstaller"

echo "Using Python: $VENV_PYTHON"
echo "Using PyInstaller: $VENV_PYINSTALLER"
echo "Build Directory: $TEMP_BUILD_DIR"
echo "Final Output Directory: $FINAL_OUTPUT_DIR"

# 0. Increment Version
echo "Incrementing version..."
"$VENV_PYTHON" increment_version.py
VERSION=$(cat version.txt)
echo "Building version: $VERSION"

# 1. Prepare build environment
echo "Preparing build environment..."
rm -rf "$TEMP_BUILD_DIR"
mkdir -p "$TEMP_BUILD_DIR"
mkdir -p "$FINAL_OUTPUT_DIR"

# Copy source files to temp build dir
echo "Copying source to build directory..."
cp -r ./* "$TEMP_BUILD_DIR/"

cd "$TEMP_BUILD_DIR"

# Update yt-dlp to latest version before building
echo "Updating yt-dlp to latest version..."
"$VENV_PYTHON" -m pip install --upgrade yt-dlp

# 2. Build executable with PyInstaller
echo "Building executable..."
# Build with explicit arguments to ensure version.txt and assets are included
"$VENV_PYINSTALLER" --noconfirm --onedir --windowed --name "HyperDownloadManager" \
    --add-data "ui:ui" \
    --add-data "core:core" \
    --add-data "utils:utils" \
    --add-data "extension:extension" \
    --add-data "LICENSE.txt:." \
    --add-data "icon.png:." \
    --add-data "version.txt:." \
    main.py

echo "Building nm_host..."
"$VENV_PYINSTALLER" nm_host.spec

# 3. Create .deb directory structure
echo "Creating .deb directory structure..."
BUILD_DEB_DIR="build_deb"
mkdir -p "$BUILD_DEB_DIR/DEBIAN"
mkdir -p "$BUILD_DEB_DIR/opt/$APP_NAME"
mkdir -p "$BUILD_DEB_DIR/usr/share/applications"
mkdir -p "$BUILD_DEB_DIR/usr/share/icons/hicolor/512x512/apps"

# 4. Copy application files
echo "Copying application files..."
cp -r dist/HyperDownloadManager/* "$BUILD_DEB_DIR/opt/$APP_NAME/"
cp dist/nm_host "$BUILD_DEB_DIR/opt/$APP_NAME/"

# 5. Native Native Messaging Configuration
echo "Configuring Native Messaging..."
NM_HOST_NAME="com.hussnain.fdm"
ALLOWED_ORIGIN="chrome-extension://gjcibhkanadbielaoejhgjpggbehnblp/"
ALLOWED_EXTENSION="hdm-integration@hyperdownloadmanager.app"

# Create manifest
echo "Creating native messaging manifest..."
cat > "$BUILD_DEB_DIR/opt/$APP_NAME/nm_manifest.json" <<EOF
{
    "name": "$NM_HOST_NAME",
    "description": "Hyper Download Manager Native Host",
    "path": "/opt/$APP_NAME/nm_host",
    "type": "stdio",
    "allowed_origins": [
        "$ALLOWED_ORIGIN"
    ],
    "allowed_extensions": [
        "$ALLOWED_EXTENSION"
    ]
}
EOF

# Install manifest for Chrome/Chromium
echo "Installing manifest for Chrome..."
mkdir -p "$BUILD_DEB_DIR/etc/opt/chrome/native-messaging-hosts"
cp "$BUILD_DEB_DIR/opt/$APP_NAME/nm_manifest.json" "$BUILD_DEB_DIR/etc/opt/chrome/native-messaging-hosts/$NM_HOST_NAME.json"

# Install manifest for Chromium (Ubuntu often uses /etc/chromium)
mkdir -p "$BUILD_DEB_DIR/etc/chromium/native-messaging-hosts"
cp "$BUILD_DEB_DIR/opt/$APP_NAME/nm_manifest.json" "$BUILD_DEB_DIR/etc/chromium/native-messaging-hosts/$NM_HOST_NAME.json"

# Install manifest for Firefox
echo "Installing manifest for Firefox..."
mkdir -p "$BUILD_DEB_DIR/usr/lib/mozilla/native-messaging-hosts"
cp "$BUILD_DEB_DIR/opt/$APP_NAME/nm_manifest.json" "$BUILD_DEB_DIR/usr/lib/mozilla/native-messaging-hosts/$NM_HOST_NAME.json"

# 6. Create control file
echo "Creating control file..."
cat > "$BUILD_DEB_DIR/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Depends: libc6, libstdc++6
Maintainer: Your Name <your.email@example.com>
Description: high-performance download manager.
 Hyper Download Manager is a fast and efficient download manager
 built with Python and Qt.
EOF

# 7. Create desktop entry
echo "Creating desktop entry..."
cat > "$BUILD_DEB_DIR/usr/share/applications/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=Hyper Download Manager
Comment=High-performance download manager
Exec=/opt/$APP_NAME/HyperDownloadManager
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Utility;Network;
StartupWMClass=HyperDownloadManager
EOF

# 8. Install icon
echo "Installing icon..."
cp icon.png "$BUILD_DEB_DIR/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png"

# 9. Set permissions
echo "Setting permissions..."
chmod 755 "$BUILD_DEB_DIR/DEBIAN/control"
chmod -R 755 "$BUILD_DEB_DIR/opt/$APP_NAME"
# Ensure nm_host is executable
chmod 755 "$BUILD_DEB_DIR/opt/$APP_NAME/nm_host"
chmod 644 "$BUILD_DEB_DIR/usr/share/applications/$APP_NAME.desktop"

# 10. Build .deb package
echo "Building .deb package..."
DEB_FILENAME="${APP_NAME}_${VERSION}_amd64.deb"
dpkg-deb --build "$BUILD_DEB_DIR" "$DEB_FILENAME"

# 11. Copy artifacts back
echo "Copying artifacts back..."
cp "$DEB_FILENAME" "$FINAL_OUTPUT_DIR/"

# Cleanup
echo "Cleaning up..."
# Optionally remove the build dir, or keep it for debugging
# rm -rf "$TEMP_BUILD_DIR"

echo "Build complete: $FINAL_OUTPUT_DIR/$DEB_FILENAME"
