#!/usr/bin/env bash
# ============================================================
#  build_macos.sh — Build Cold Outreach Automator for macOS
#
#  Run from the PROJECT ROOT:
#      chmod +x build_scripts/build_macos.sh
#      ./build_scripts/build_macos.sh
#
#  Prerequisites:
#    • Python 3.9+ (from python.org — NOT the system Python)
#    • Homebrew: brew install create-dmg
#    • (Optional) An Apple Developer ID for code signing
# ============================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────
APP_NAME="ColdOutreachAutomator"
APP_VERSION="1.0.0"
BUNDLE_ID="com.yourname.coldoutreach"
DIST_DIR="dist"
DMG_NAME="${APP_NAME}_${APP_VERSION}_macOS.dmg"

# ── Code-signing (set your Developer ID here, or leave blank) ─
# To find your identity: security find-identity -v -p codesigning
CODESIGN_IDENTITY=""        # e.g. "Developer ID Application: Jane Doe (XXXXXXXXXX)"
NOTARIZE="false"            # Set to "true" only if you have an Apple Developer account
APPLE_ID=""                 # your Apple ID email (for notarization)
APPLE_TEAM_ID=""            # 10-character Team ID (for notarization)
APPLE_APP_PASSWORD=""       # App-specific password for notarization

# ── Color helpers ──────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo ""
echo "============================================================"
echo "  Cold Outreach Automator — macOS Build Script"
echo "============================================================"
echo ""

# ── Step 1: Check prerequisites ───────────────────────────────
command -v python3 >/dev/null 2>&1 || error "python3 not found. Install from https://python.org"
command -v brew    >/dev/null 2>&1 || warn  "Homebrew not found. DMG creation will be skipped. Install: https://brew.sh"

# ── Step 2: Virtual environment ───────────────────────────────
if [ ! -d "venv" ]; then
    info "Creating virtual environment..."
    python3 -m venv venv
fi
# shellcheck source=/dev/null
source venv/bin/activate
info "Using Python: $(which python3)"

# ── Step 3: Install dependencies ──────────────────────────────
info "Installing requirements..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
info "Dependencies ready."

# ── Step 4: Generate .icns icon ───────────────────────────────
if [ ! -f "assets/icon.icns" ]; then
    info "Generating icon.icns from icon.png..."
    mkdir -p /tmp/iconset.iconset
    SIZES=(16 32 128 256 512)
    for SIZE in "${SIZES[@]}"; do
        sips -z "$SIZE" "$SIZE" assets/icon.png --out "/tmp/iconset.iconset/icon_${SIZE}x${SIZE}.png"      2>/dev/null || true
        sips -z "$((SIZE*2))" "$((SIZE*2))" assets/icon.png --out "/tmp/iconset.iconset/icon_${SIZE}x${SIZE}@2x.png" 2>/dev/null || true
    done
    iconutil -c icns /tmp/iconset.iconset -o assets/icon.icns 2>/dev/null \
        && info "icon.icns created." \
        || warn "iconutil failed. Place icon.icns manually in assets/."
    rm -rf /tmp/iconset.iconset
fi

# ── Step 5: Clean previous build ──────────────────────────────
info "Cleaning previous build artifacts..."
rm -rf build "${DIST_DIR}/${APP_NAME}.app" "${DIST_DIR}/${APP_NAME}"

# ── Step 6: PyInstaller ───────────────────────────────────────
info "Running PyInstaller..."
pyinstaller ColdOutreachAutomator.spec --noconfirm --clean
info "PyInstaller complete. .app at: ${DIST_DIR}/${APP_NAME}.app"

# ── Step 7: Code Signing (optional) ───────────────────────────
if [ -n "$CODESIGN_IDENTITY" ]; then
    info "Code-signing the .app bundle..."
    codesign --deep --force --verify --verbose \
        --sign "$CODESIGN_IDENTITY" \
        --options runtime \
        --entitlements build_scripts/entitlements.plist \
        "${DIST_DIR}/${APP_NAME}.app" \
    && info "Code-signing complete." \
    || warn "Code-signing failed. The app will show a Gatekeeper warning on other Macs."
else
    warn "CODESIGN_IDENTITY is not set. Skipping code-signing."
    warn "The app will show 'unidentified developer' on other Macs."
    warn "Users can bypass with: right-click → Open → Open Anyway"
fi

# ── Step 8: Create the DMG ────────────────────────────────────
if command -v create-dmg >/dev/null 2>&1; then
    info "Creating DMG with create-dmg..."
    rm -f "${DIST_DIR}/${DMG_NAME}"

    create-dmg \
        --volname "${APP_NAME}" \
        --volicon "assets/icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 175 190 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 425 190 \
        --background "assets/dmg_background.png" \
        "${DIST_DIR}/${DMG_NAME}" \
        "${DIST_DIR}/${APP_NAME}.app" \
    || {
        warn "create-dmg with background failed; retrying without background..."
        create-dmg \
            --volname "${APP_NAME}" \
            --volicon "assets/icon.icns" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "${APP_NAME}.app" 175 190 \
            --hide-extension "${APP_NAME}.app" \
            --app-drop-link 425 190 \
            "${DIST_DIR}/${DMG_NAME}" \
            "${DIST_DIR}/${APP_NAME}.app"
    }

    info "DMG created: ${DIST_DIR}/${DMG_NAME}"
else
    warn "create-dmg not found. Install with: brew install create-dmg"
    warn "Skipping DMG creation. The .app is at: ${DIST_DIR}/${APP_NAME}.app"
fi

# ── Step 9: Notarization (optional) ───────────────────────────
if [ "$NOTARIZE" = "true" ] && [ -n "$CODESIGN_IDENTITY" ] && [ -f "${DIST_DIR}/${DMG_NAME}" ]; then
    info "Submitting DMG for Apple notarization..."
    xcrun notarytool submit "${DIST_DIR}/${DMG_NAME}" \
        --apple-id "$APPLE_ID" \
        --team-id "$APPLE_TEAM_ID" \
        --password "$APPLE_APP_PASSWORD" \
        --wait \
    && xcrun stapler staple "${DIST_DIR}/${DMG_NAME}" \
    && info "Notarization and stapling complete." \
    || warn "Notarization failed. Check xcrun output above."
else
    [ "$NOTARIZE" != "true" ] && warn "Notarization skipped (NOTARIZE is not 'true')."
fi

deactivate

echo ""
echo "============================================================"
echo "  BUILD COMPLETE"
echo "  .app   : ${DIST_DIR}/${APP_NAME}.app"
[ -f "${DIST_DIR}/${DMG_NAME}" ] && echo "  .dmg   : ${DIST_DIR}/${DMG_NAME}"
echo "============================================================"
echo ""
