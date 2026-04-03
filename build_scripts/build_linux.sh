#!/usr/bin/env bash
# ============================================================
#  build_linux.sh — Build Cold Outreach Automator for Linux
#
#  Run from the PROJECT ROOT (on a Linux machine):
#      chmod +x build_scripts/build_linux.sh
#      ./build_scripts/build_linux.sh
#
#  Prerequisites:
#    • Python 3.9+ with tkinter support:
#        Ubuntu/Debian: sudo apt-get install python3-tk python3-venv
#        Fedora:        sudo dnf install python3-tkinter
#    • FUSE (for running AppImages):
#        Ubuntu/Debian: sudo apt-get install fuse libfuse2
#    • wget (to download appimagetool)
# ============================================================

set -euo pipefail

APP_NAME="ColdOutreachAutomator"
APP_VERSION="1.0.0"
APPDIR="build_scripts/${APP_NAME}.AppDir"
DIST_DIR="dist"
APPIMAGE_NAME="${APP_NAME}_${APP_VERSION}_linux_x86_64.AppImage"

# ── Color helpers ──────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo ""
echo "============================================================"
echo "  Cold Outreach Automator — Linux AppImage Build Script"
echo "============================================================"
echo ""

# ── Step 1: Check Prerequisites ───────────────────────────────
command -v python3 >/dev/null 2>&1 || error "python3 not found. Install with: sudo apt-get install python3"
python3 -c "import tkinter" 2>/dev/null  || error "tkinter missing. Install: sudo apt-get install python3-tk"

# ── Step 2: Virtual environment ───────────────────────────────
if [ ! -d "venv" ]; then
    info "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
info "Using Python: $(which python3)"

# ── Step 3: Install dependencies ──────────────────────────────
info "Installing requirements..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

# ── Step 4: Clean and build with PyInstaller ──────────────────
info "Cleaning previous build..."
rm -rf build "${DIST_DIR}/${APP_NAME}" "${DIST_DIR}/${APPIMAGE_NAME}"

info "Running PyInstaller..."
pyinstaller ColdOutreachAutomator.spec --noconfirm --clean
info "PyInstaller complete."

# ── Step 5: Assemble the AppDir ───────────────────────────────
info "Assembling AppDir structure..."

APPDIRFULL="${DIST_DIR}/${APP_NAME}.AppDir"
rm -rf "$APPDIRFULL"
mkdir -p "${APPDIRFULL}/usr/bin"
mkdir -p "${APPDIRFULL}/usr/lib"

# Copy the PyInstaller one-folder output into usr/bin
cp -r "${DIST_DIR}/${APP_NAME}/"* "${APPDIRFULL}/usr/bin/"

# Copy AppRun (entry script)
cp "${APPDIR}/AppRun" "${APPDIRFULL}/AppRun"
chmod +x "${APPDIRFULL}/AppRun"

# Desktop entry
cp "${APPDIR}/${APP_NAME}.desktop" "${APPDIRFULL}/${APP_NAME}.desktop"

# Icon — AppImage standard: place at root of AppDir
cp "assets/icon.png" "${APPDIRFULL}/${APP_NAME}.png"
# Also at the conventional path
mkdir -p "${APPDIRFULL}/usr/share/icons/hicolor/256x256/apps"
cp "assets/icon.png" "${APPDIRFULL}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"

# ── Step 6: Download appimagetool ─────────────────────────────
APPIMAGETOOL="build_scripts/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    info "Downloading appimagetool..."
    wget -q -O "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
    info "appimagetool downloaded."
fi

# ── Step 7: Build the AppImage ────────────────────────────────
info "Building AppImage..."
# Ensure permissions are correct inside AppDir
chmod -R a+r "$APPDIRFULL"
find "$APPDIRFULL" -type d -exec chmod a+x {} +
chmod +x "${APPDIRFULL}/AppRun"
chmod +x "${APPDIRFULL}/usr/bin/${APP_NAME}"

ARCH=x86_64 "$APPIMAGETOOL" "$APPDIRFULL" "${DIST_DIR}/${APPIMAGE_NAME}"

deactivate

echo ""
echo "============================================================"
echo "  BUILD COMPLETE"
echo "  AppImage: ${DIST_DIR}/${APPIMAGE_NAME}"
echo ""
echo "  To run: chmod +x ${DIST_DIR}/${APPIMAGE_NAME}"
echo "          ./${DIST_DIR}/${APPIMAGE_NAME}"
echo "============================================================"
echo ""
