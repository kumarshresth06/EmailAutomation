# 📦 Cold Outreach Automator — Packaging & Distribution Guide

> Build native installers for **Windows**, **macOS**, and **Linux** entirely on your local machine.  
> No CI/CD, no cloud pipelines — just your terminal and a few prerequisites.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Application Icon & Assets](#application-icon--assets)
3. [Common Prerequisites](#common-prerequisites)
4. [Accessing Bundled Assets in Code](#accessing-bundled-assets-in-code)
5. [Building on Windows](#building-on-windows)
6. [Building on macOS](#building-on-macos)
7. [Building on Linux](#building-on-linux)
8. [Troubleshooting](#troubleshooting)

---

## Project Structure

After running all build scripts, the project layout will look like:

```
EmailAutomation/
├── assets/
│   ├── icon.png          ← Source PNG logo (1024×1024)
│   ├── icon.ico          ← Windows icon (auto-generated)
│   └── icon.icns         ← macOS icon (auto-generated)
├── build_scripts/
│   ├── build_windows.bat         ← Windows build script
│   ├── installer_windows.iss     ← Inno Setup installer config
│   ├── build_macos.sh            ← macOS .app + .dmg build script
│   ├── entitlements.plist        ← macOS code-signing entitlements
│   ├── build_linux.sh            ← Linux AppImage build script
│   └── ColdOutreachAutomator.AppDir/
│       ├── AppRun                ← AppImage entry point
│       └── ColdOutreachAutomator.desktop
├── dist/                          ← All installer outputs land here
├── ColdOutreachAutomator.spec     ← PyInstaller spec file
├── main.py
├── requirements.txt
└── ...
```

---

## Application Icon & Assets

The generated logo is stored at `assets/icon.png`.

| Format | File | Used by |
|--------|------|---------|
| PNG (source) | `assets/icon.png` | Linux AppImage, source for conversion |
| ICO | `assets/icon.ico` | Windows EXE & installer |
| ICNS | `assets/icon.icns` | macOS .app bundle |

The `.ico` and `.icns` files are **auto-generated** by their respective build scripts via Python (Pillow) or the macOS `sips`/`iconutil` tools. You do not need to prepare them manually.

If you want to replace the logo:
1. Drop your new `icon.png` (recommended: 1024×1024 RGBA) into `assets/`.
2. Delete any old `icon.ico` / `icon.icns` so the scripts regenerate them.
3. Run the build script.

---

## Common Prerequisites

Regardless of platform, install PyInstaller into your project environment:

```bash
pip install pyinstaller
```

Ensure you're building from the **project root** directory:

```bash
cd /path/to/EmailAutomation
```

> **Important:** PyInstaller must be run on the **same OS** as the target platform. You cannot cross-compile (e.g., build a Windows `.exe` on macOS).

---

## Accessing Bundled Assets in Code

When PyInstaller packages your app, the working directory changes. Use this helper in your Python code to resolve paths to bundled files:

```python
import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, works for both:
    - Development (running from source)
    - PyInstaller frozen builds (sys._MEIPASS is set)
    """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)

# Usage:
# icon_path = resource_path("assets/icon.png")
# image = Image.open(icon_path)
```

Add this utility to a shared module (e.g., `utils.py`) and import it wherever asset paths are needed.

---

## Building on Windows

### Prerequisites

| Tool | Download | Notes |
|------|----------|-------|
| Python 3.9+ | [python.org](https://python.org/downloads) | ✅ Check "Add Python to PATH" at install |
| Inno Setup 6 | [jrsoftware.org](https://jrsoftware.org/isdl.php) | Required to build the `.exe` installer |
| Pillow | `pip install Pillow` | Auto-installed by the build script |

### Steps

1. **Open Command Prompt** (or PowerShell) as a regular user.

2. **Navigate to the project root:**
   ```bat
   cd C:\path\to\EmailAutomation
   ```

3. **Run the build script:**
   ```bat
   build_scripts\build_windows.bat
   ```

   The script will:
   - Create/activate a virtual environment
   - Install all dependencies + PyInstaller
   - Generate `assets\icon.ico` from `assets\icon.png`
   - Run PyInstaller using `ColdOutreachAutomator.spec`
   - Launch the Inno Setup compiler to produce the installer

4. **Collect your installer:**
   ```
   dist\ColdOutreachAutomator_Setup.exe
   ```

### Customizing the Installer

Edit `build_scripts\installer_windows.iss` to change:

| Setting | Variable | Default |
|---------|----------|---------|
| App name | `AppName` | `Cold Outreach Automator` |
| Version | `AppVersion` | `1.0.0` |
| Publisher | `AppPublisher` | `Your Name` |
| Install directory | `DefaultDirName` | `{autopf}\{AppName}` |

### Notes

- The installer runs **per-user** (no UAC prompt) by default. Change `PrivilegesRequired=lowest` to `admin` if a system-wide install is needed.
- UPX compression is enabled in the spec file. Install UPX from [upx.github.io](https://upx.github.io) and add it to `PATH` for ~30% smaller bundles.

---

## Building on macOS

### Prerequisites

| Tool | Install Command | Notes |
|------|----------------|-------|
| Python 3.9+ | [python.org](https://python.org) | Use the official installer, not system Python |
| Homebrew | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` | Required for `create-dmg` |
| create-dmg | `brew install create-dmg` | Creates the `.dmg` disk image |
| Xcode CLI Tools | `xcode-select --install` | Required for `sips`, `iconutil`, `codesign` |

### Steps

1. **Open Terminal** and navigate to the project root:
   ```bash
   cd /path/to/EmailAutomation
   ```

2. **Make the script executable** (first time only):
   ```bash
   chmod +x build_scripts/build_macos.sh
   ```

3. **Run the build script:**
   ```bash
   ./build_scripts/build_macos.sh
   ```

   The script will:
   - Create/activate a virtual environment
   - Install all dependencies + PyInstaller
   - Generate `assets/icon.icns` using `sips` + `iconutil`
   - Run PyInstaller (produces `dist/ColdOutreachAutomator.app`)
   - Package the `.app` into a drag-and-drop `.dmg`

4. **Collect your outputs:**
   ```
   dist/ColdOutreachAutomator.app
   dist/ColdOutreachAutomator_1.0.0_macOS.dmg
   ```

### Code Signing (Optional but Recommended)

Without code signing, macOS Gatekeeper will block the app on other Macs with the message *"cannot be opened because the developer cannot be verified."*

Users can bypass this with:
> **Right-click → Open → Open Anyway**

To properly sign (requires an [Apple Developer account](https://developer.apple.com)):

1. Find your signing identity:
   ```bash
   security find-identity -v -p codesigning
   ```
   Copy the string like: `Developer ID Application: Jane Doe (XXXXXXXXXX)`

2. Edit `build_scripts/build_macos.sh` and set:
   ```bash
   CODESIGN_IDENTITY="Developer ID Application: Jane Doe (XXXXXXXXXX)"
   ```

3. For notarization (distributing outside the App Store), also set:
   ```bash
   NOTARIZE="true"
   APPLE_ID="you@example.com"
   APPLE_TEAM_ID="XXXXXXXXXX"
   APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"   # App-specific password from appleid.apple.com
   ```

4. Re-run the script. It will sign, submit for notarization, and staple the ticket to the DMG.

---

## Building on Linux

### Prerequisites

| Tool | Install Command | Notes |
|------|----------------|-------|
| Python 3.9+ with tkinter | `sudo apt-get install python3 python3-venv python3-tk` | Fedora: `sudo dnf install python3-tkinter` |
| FUSE (libfuse2) | `sudo apt-get install fuse libfuse2` | Required to run AppImages |
| wget | `sudo apt-get install wget` | To download `appimagetool` |

> **Arch Linux:** `sudo pacman -S python tk fuse2 wget`

### Steps

1. **Open a terminal** and navigate to the project root:
   ```bash
   cd /path/to/EmailAutomation
   ```

2. **Make the script executable** (first time only):
   ```bash
   chmod +x build_scripts/build_linux.sh
   ```

3. **Run the build script:**
   ```bash
   ./build_scripts/build_linux.sh
   ```

   The script will:
   - Create/activate a virtual environment
   - Install all dependencies + PyInstaller
   - Run PyInstaller (produces `dist/ColdOutreachAutomator/`)
   - Assemble the AppDir structure
   - Download `appimagetool` automatically (saved to `build_scripts/`)
   - Produce a self-contained AppImage

4. **Collect your AppImage:**
   ```
   dist/ColdOutreachAutomator_1.0.0_linux_x86_64.AppImage
   ```

5. **Make it executable and run:**
   ```bash
   chmod +x dist/ColdOutreachAutomator_1.0.0_linux_x86_64.AppImage
   ./dist/ColdOutreachAutomator_1.0.0_linux_x86_64.AppImage
   ```

### Optional: Install as a System Application

```bash
# Copy the AppImage to a shared location
sudo cp dist/ColdOutreachAutomator_1.0.0_linux_x86_64.AppImage /usr/local/bin/ColdOutreachAutomator
sudo chmod +x /usr/local/bin/ColdOutreachAutomator

# Create a .desktop launcher entry
mkdir -p ~/.local/share/applications
cp build_scripts/ColdOutreachAutomator.AppDir/ColdOutreachAutomator.desktop ~/.local/share/applications/
cp assets/icon.png ~/.local/share/icons/ColdOutreachAutomator.png
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```

---

## Troubleshooting

### ❌ `ModuleNotFoundError` after bundling

A Python module was not detected by PyInstaller's analysis. Add it to the `hiddenimports` list in `ColdOutreachAutomator.spec`:

```python
hidden_imports = [
    ...
    "your_missing_module",
]
```

Then rebuild with `pyinstaller ColdOutreachAutomator.spec --noconfirm --clean`.

---

### ❌ Missing asset files at runtime

Use the `resource_path()` helper described in [Accessing Bundled Assets in Code](#accessing-bundled-assets-in-code) to resolve paths. Check that the asset folder is listed in the `datas` section of the `.spec` file.

---

### ❌ macOS: "App is damaged and can't be opened"

This happens when a quarantine attribute is set on a downloaded `.app`. Clear it:

```bash
xattr -dr com.apple.quarantine dist/ColdOutreachAutomator.app
```

---

### ❌ Linux: "FUSE not available" when running AppImage

Install FUSE and reboot:

```bash
sudo apt-get install fuse libfuse2
```

Alternatively, extract and run the AppImage without FUSE:
```bash
./ColdOutreachAutomator.AppImage --appimage-extract
./squashfs-root/AppRun
```

---

### ❌ Windows: Antivirus flags the EXE

This is a common false positive with PyInstaller-built executables. Options:
1. Submit the file for analysis at [VirusTotal](https://www.virustotal.com) and report false positives to AV vendors.
2. Purchase a code signing certificate (EV cert) from a CA like Sectigo or DigiCert and sign the EXE with `signtool.exe`.

---

*Last updated: 2026-04-03*
