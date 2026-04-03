# Cold Outreach Automator

> A professional desktop application for running personalized cold email campaigns — built with Python and CustomTkinter.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/Tests-pytest-orange?logo=pytest)

---

## Overview

**Cold Outreach Automator** is a cross-platform desktop utility that lets you run personalized email campaigns directly from a clean GUI — no coding required. Load a CSV or Excel contact list, compose an HTML email template with dynamic placeholders, and fire off a tracked, throttled campaign straight from your Gmail account.

**Key highlights:**
- 🧩 **Template placeholders** — map `{{Column_Name}}` tags directly to spreadsheet columns
- 🔍 **Auto email derivation** — heuristically guesses missing emails via Google scraping
- 🛡️ **Test-first safety** — must send a test email before bulk send is unlocked
- ⏱️ **Anti-spam throttling** — randomized 45–90 s delay between sends
- 💾 **Idempotent sends** — tracks `Status` + `Date_Sent` columns; never double-sends

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Features](#features)
- [Spreadsheet Format](#spreadsheet-format)
- [Gmail App Password Setup](#gmail-app-password-setup)
- [Running Tests](#running-tests)
- [Building Distributables](#building-distributables)
- [Contributing](#contributing)

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/kumarshresth06/EmailAutomation.git
cd EmailAutomation

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
python3 main.py
```

> **macOS shortcut** — the `run.sh` script handles venv creation, dependency installation, and launch automatically:
> ```bash
> chmod +x run.sh && ./run.sh
> ```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.9+ | 3.11 recommended |
| pip | latest | bundled with Python |
| Gmail account | — | Needs 2-Step Verification enabled |

---

## Installation

### Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern GUI framework |
| `pandas` | CSV / Excel ingestion and state tracking |
| `openpyxl` | `.xlsx` read/write support |
| `requests` | HTTP requests for email derivation scraper |
| `beautifulsoup4` | HTML parsing for Google scrape results |
| `pillow` | Image handling (app icon) |
| `markdown` | Markdown → HTML rendering in UI |
| `tkinterweb` | Embedded HTML preview in GUI |
| `pytest` / `pytest-mock` | Test runner and SMTP mocking |

---

## Running the App

```bash
# Activate your virtual environment first
source venv/bin/activate

python3 main.py
```

The GUI will launch. Follow this workflow:

1. **Enter credentials** — Gmail address + [App Password](#gmail-app-password-setup)
2. **Set subject line** — supports `{{placeholder}}` syntax
3. **Load contact file** — select a `.csv` or `.xlsx` file
4. **Compose template** — use the rich-text HTML editor; insert `{{Column_Name}}` tags
5. **Send test email** — validates your first data row; result goes to your own inbox
6. **Start campaign** — bulk mode unlocks after a successful test send

---

## Project Structure

```
EmailAutomation/
├── main.py               # Entry point — bootstraps the GUI
├── app_ui.py             # CustomTkinter UI, threading, and campaign orchestration
├── data_service.py       # Spreadsheet ingestion, validation, and status tracking
├── email_service.py      # SMTP client with dynamic template rendering
├── email_guesser.py      # Heuristic email derivation via Google scraping
│
├── requirements.txt      # Python dependencies
├── run.sh                # macOS/Linux convenience launcher
│
├── tests/
│   ├── test_data_service.py   # Unit tests for data validation logic
│   └── test_email_service.py  # Unit tests for SMTP / template rendering
│
├── assets/
│   └── icon.png          # Application icon
│
├── build_scripts/        # OS-specific packaging scripts (PyInstaller)
├── ColdOutreachAutomator.spec  # PyInstaller build spec
├── README_PACKAGING.md   # Detailed packaging & distribution guide
└── helper.md             # In-app help content (placeholders, Gmail setup)
```

---

## Architecture

The codebase follows a **single-responsibility module pattern** — each file owns exactly one concern:

```
┌─────────────┐     loads      ┌─────────────────┐
│   main.py   │ ─────────────▶ │    app_ui.py     │
└─────────────┘                │  (UI + Threading) │
                               └────────┬──────────┘
                                        │ uses
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                  ┌──────────────┐ ┌──────────┐ ┌───────────────┐
                  │data_service.py│ │email_    │ │email_guesser.py│
                  │(DataHandler) │ │service.py│ │(EmailGuesser) │
                  │              │ │(EmailSend│ │               │
                  └──────────────┘ └──────────┘ └───────────────┘
```

| Module | Class | Responsibility |
|---|---|---|
| `main.py` | — | App bootstrap; spawns `ColdOutreachUI` |
| `app_ui.py` | `ColdOutreachUI` | Full GUI, campaign threading, user feedback |
| `data_service.py` | `DataHandler` | Load / validate spreadsheets; write `Status` + `Date_Sent` |
| `email_service.py` | `EmailSender` | SMTP auth, `{{placeholder}}` substitution, send |
| `email_guesser.py` | `EmailGuesser` | Derive missing emails from name + company via web scrape |

---

## Features

### 📝 Rich HTML Email Editor
The built-in editor lets you compose emails with standard formatting buttons (`Bold`, `Italic`, `Link`, `Paragraph`, `Line Break`). Highlight any text and click a button to wrap it in the appropriate HTML tag — no external editor needed.

### 🔁 Dynamic Placeholder Substitution
Use `{{Column_Name}}` in your subject or body. At send-time, each tag is replaced with the corresponding value from that contact's row.

```
Subject:  Quick note about {{Company}}
Body:     Hi {{First Name}}, I saw you're hiring for {{Role}}...
```

### 🔍 Heuristic Email Guesser
No `Email` column? No problem. If your sheet has `First Name`, `Last Name`, and `Company`, the app will:
1. Derive likely corporate domains from the company name via Google
2. Generate common email permutations (`first.last@`, `f.last@`, etc.)
3. Return its best match

### 🛡️ Test-First Safety Gate
The **Start Campaign** button is disabled by default. You must:
- Click **Send Test Email** (sends to your own inbox using row 1 of your data), **or**
- Check **Override Test Validation** to bypass

### ⏱️ Anti-Spam Throttling
Between each send in a bulk campaign, the app waits a **random 45–90 seconds**. This mimics human sending cadence and dramatically reduces Gmail spam-flag risk.

### 💾 Idempotent State Tracking
Two columns are automatically appended to your spreadsheet:

| Column | Value |
|---|---|
| `Status` | `Sent` on success |
| `Date_Sent` | ISO timestamp of send |

Restarting a campaign skips rows already marked `Sent` — safe to interrupt and resume at any time.

---

## Spreadsheet Format

Your contact file (`.csv` or `.xlsx`) must follow these rules:

### Option A — Email column present

| First Name | Last Name | Company | Email | Role |
|---|---|---|---|---|
| Jane | Doe | Acme Corp | jane@acme.com | Engineer |

- **Mandatory Placeholders**: The spreadsheet MUST include a column named exactly `Email` or `email` (see Option B below).
- **Additional Placeholders**: Users can define any custom placeholder in the email template using the `{{PLACEHOLDER_NAME}}` format.
- The name must be present in the attached Excel/CSV file as a column. The matching is case-insensitive, so `{{Role}}` will happily match a column called `role`. If any placeholder used in your template is completely missing from your file, the system will throw an error.

### Option B — Email column absent (auto-derivation)

| First Name | Last Name | Company | Role |
|---|---|---|---|
| Jane | Doe | Acme Corp | Engineer |

- Must include `First Name`, `Last Name`, and `Company`.
- The app will attempt to derive the email automatically.

> **Note:** Auto-derived emails are best-effort guesses. Always send a test email before launching a campaign.

---

## Gmail App Password Setup

Google requires an **App Password** when accessing Gmail via third-party scripts.

1. **Enable 2-Step Verification**
   Go to [myaccount.google.com/security](https://myaccount.google.com/security) → *How you sign in to Google* → turn on **2-Step Verification**.

2. **Generate an App Password**
   On the same Security page, search for **"App passwords"**. Select app: **Mail**, device: **Other** (name it anything), then click **Generate**.

3. **Copy the 16-character code**
   Paste it into the **App Password** field in the app. Store it somewhere safe — Google won't show it again.

---

## Running Tests

The test suite covers `DataHandler` and `EmailSender` with mocked SMTP and filesystem dependencies.

```bash
# Activate your virtual environment
source venv/bin/activate

# Run all tests
python3 -m pytest tests/ -v

# Run a specific test file
python3 -m pytest tests/test_email_service.py -v
```

Tests use `pytest-mock` to stub `smtplib.SMTP` — no real network calls are made.

---

## Building Distributables

Pre-built binaries for macOS (`.dmg`), Windows (`.exe`), and Linux (AppImage) can be built locally with PyInstaller.

See **[README_PACKAGING.md](./README_PACKAGING.md)** for the full step-by-step guide.

**Quick reference:**

| Platform | Script | Output |
|---|---|---|
| macOS | `build_scripts/build_mac.sh` | `.dmg` installer |
| Windows | `build_scripts/build_windows.bat` | `.exe` installer |
| Linux | `build_scripts/build_linux.sh` | AppImage |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests where appropriate
4. Run the test suite: `python3 -m pytest tests/ -v`
5. Open a Pull Request with a clear description of what changed and why

Please keep the single-responsibility module pattern intact when adding new features.

---

*Built with ❤️ using Python + CustomTkinter*
