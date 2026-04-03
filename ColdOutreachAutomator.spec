# -*- mode: python ; coding: utf-8 -*-
#
# ColdOutreachAutomator.spec
# PyInstaller spec file for Cold Outreach Automator
#
# Usage:
#   pyinstaller ColdOutreachAutomator.spec
#
# Prerequisites:
#   pip install pyinstaller
#
# NOTE: This spec file is designed to be run from the project root directory.

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Resolve the project root (same folder this .spec file lives in) ──────────
block_cipher = None
PROJECT_ROOT = os.path.abspath(os.path.dirname(SPEC))

# ── Platform-specific icon path ───────────────────────────────────────────────
if sys.platform == "win32":
    APP_ICON = os.path.join(PROJECT_ROOT, "assets", "icon.ico")
elif sys.platform == "darwin":
    APP_ICON = os.path.join(PROJECT_ROOT, "assets", "icon.icns")
else:
    APP_ICON = os.path.join(PROJECT_ROOT, "assets", "icon.png")

# ── Hidden imports ────────────────────────────────────────────────────────────
# customtkinter renders its own theme files at runtime — collect them all.
# pandas/openpyxl have optional backends resolved at import time.
hidden_imports = [
    # --- CustomTkinter internals ---
    "customtkinter",
    "customtkinter.windows",
    "customtkinter.windows.widgets",
    "customtkinter.windows.widgets.appearance_mode",
    "customtkinter.windows.widgets.color_manager",
    "customtkinter.windows.widgets.font",
    "customtkinter.windows.widgets.image",
    "customtkinter.windows.widgets.scaling",
    "customtkinter.windows.widgets.theme",
    "customtkinter.windows.widgets.utility",
    # --- Tkinter (bundled with Python; declare explicitly for PyInstaller) ---
    "tkinter",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.ttk",
    "_tkinter",
    # --- pandas / openpyxl backends ---
    "pandas",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.tslibs.timedeltas",
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.styles.fills",
    "openpyxl.styles.alignment",
    "openpyxl.styles.fonts",
    "openpyxl.styles.borders",
    "openpyxl.cell",
    "openpyxl.reader",
    "openpyxl.writer",
    "openpyxl.utils",
    # --- Network / scraping ---
    "requests",
    "bs4",
    "urllib3",
    "certifi",
    "charset_normalizer",
    # --- Email stack ---
    "smtplib",
    "email",
    "email.mime",
    "email.mime.text",
    "email.mime.multipart",
    # --- Standard library helpers ---
    "threading",
    "re",
    "time",
    "random",
    "datetime",
    "secrets",
    "ssl",
    "hashlib",
    "bisect",
    "copy",
    "inspect",
    "json",
    "logging",
    "shutil",
    "tempfile",
    "traceback",
    "uuid",
]

# Collect all sub-modules for packages that use dynamic imports internally
hidden_imports += collect_submodules("customtkinter")
hidden_imports += collect_submodules("pandas")
hidden_imports += collect_submodules("openpyxl")

# ── Data files (non-Python runtime assets) ────────────────────────────────────
# Format: (source_path_or_glob, destination_folder_inside_bundle)
datas = []

# CustomTkinter ships its own theme JSON files, fonts, and images — MUST include
datas += collect_data_files("customtkinter")

# Your own application assets (icon, any future images/stylesheets)
datas += [
    (os.path.join(PROJECT_ROOT, "assets"), "assets"),
    (os.path.join(PROJECT_ROOT, "helper.md"), "."),
]

# ── Binaries to EXCLUDE (keeps the bundle lean) ───────────────────────────────
# Remove bloated test/example data from pandas, numpy, scipy etc.
excludes = [
    "matplotlib",
    "scipy",
    "sklearn",
    "skimage",
    "cv2",
    "IPython",
    "notebook",
    "jupyter",
    "sphinx",
    "docutils",
    "pydoc",
    "xmlrpc",
    "tkinter.test",
    "unittest",
    "pytest",
    "py",
    "_pytest",
    "setuptools",
    "asyncio",       # not used in this app
    "multiprocessing",
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(PROJECT_ROOT, "main.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── PYZ archive ───────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ColdOutreachAutomator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # compress with UPX if available — reduces size ~30%
    console=False,      # windowed app; set True only for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON,
)

# ── COLLECT (one-folder mode) ─────────────────────────────────────────────────
# All files land in dist/ColdOutreachAutomator/
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ColdOutreachAutomator",
)

# ── macOS .app bundle (only active when building on macOS) ───────────────────
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="ColdOutreachAutomator.app",
        icon=APP_ICON,
        bundle_identifier="com.yourname.coldoutreach",
        info_plist={
            "CFBundleName": "Cold Outreach Automator",
            "CFBundleDisplayName": "Cold Outreach Automator",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "© 2025 Your Name. All rights reserved.",
            # Required for Tkinter to capture keyboard events on macOS
            "NSPrincipalClass": "NSApplication",
            "NSAppleScriptEnabled": False,
        },
    )
