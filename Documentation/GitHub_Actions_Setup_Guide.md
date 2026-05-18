# GitHub Actions POS Test Automation — Complete Setup & Lifecycle Guide

---

## Overview

This document explains how the GitHub Actions CI/CD pipeline is set up for the **R10 POS Test Automation** project — from initial configuration to test execution on a physical POS machine.

---

## Architecture at a Glance

```
Developer pushes code  ──►  GitHub detects push  ──►  GitHub Actions triggers workflow
                                                              │
                                                              ▼
                                              Self-Hosted Runner (POS Machine)
                                              picks up the job and runs the test
                                                              │
                                                              ▼
                                              Python script controls POS via pywinauto
                                                              │
                                                              ▼
                                              Result reported back to GitHub Actions UI
```

---

## Part 1 — One-Time Setup (Done Once Per Machine)

### 1.1 Register the Self-Hosted Runner

Because the POS application runs on a **specific physical Windows machine**, we use a **self-hosted runner** instead of GitHub's cloud runners.

**Steps:**
1. Go to: `https://github.com/khadarbasha2609/R10_Pywin_Automation/settings/actions/runners/new`
2. Select **Windows / x64**
3. Follow the commands shown — download the runner package and run `config.cmd` with the provided token
4. The runner registers itself to the repo with the label `[self-hosted, Windows, X64]`

### 1.2 Configure PowerShell Execution Policy

Run once on the POS machine (as Administrator) to allow scripts to execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
```

### 1.3 Python Virtual Environment

The repo includes a pre-built Python 3.12.4 virtual environment under `Lib/` and `Scripts/`.

- All packages are pre-installed (pytest, pywinauto, opencv, pillow, etc.)
- Additional packages (e.g., pytest-html) are installed from `Offline_lib/offline_packages/` — **no internet needed**
- The workflow calls `Scripts\python.exe` directly — no activation needed

---

## Part 2 — Starting the Runner (Before Every Test Session)

> ⚠️ **Important:** The runner must run **interactively** (not as a Windows Service) so it can control the POS UI.

### Why Interactive Mode?

Windows Services run in **Session 0** (no desktop access). pywinauto needs to see and click POS windows, which are only visible in the **user's desktop session**.

### How to Start the Runner

1. Stop the service (if running):
```powershell
Stop-Service "actions.runner.khadarbasha2609-R10_Pywin_Automation.1090SMNPRG007" -Force
```

2. Start the runner interactively in a **cmd window** (keep it open):
```cmd
cd C:\actions-runner
run.cmd
```

3. You should see:
```
√ Connected to GitHub
Listening for Jobs
```

> 🔁 You must repeat this step after every machine restart.

---

## Part 3 — Workflow File Explained (`main.yml`)

**Location:** `.github/workflows/main.yml`

```yaml
on:
  workflow_dispatch:   # Manual trigger from GitHub UI
  push:
    branches: [ main ] # Auto-trigger on every push to main
```

### Steps Breakdown

| Step | What It Does |
|------|-------------|
| **Checkout code** | Pulls the latest code from GitHub into the runner's workspace (`C:\actions-runner\_work\...`) |
| **Install dependencies** | Installs `pytest-html`, `jinja2`, `MarkupSafe` from the offline packages folder — no internet needed |
| **Verify Python** | Confirms Python 3.12.4 is available from the venv |
| **Run Test** | Executes the pytest test script against the live POS application |

### Key Configuration

```yaml
runs-on: [self-hosted, Windows, X64]   # Targets the POS machine runner

env:
  PYTHONIOENCODING: utf-8   # Required — prevents crashes from emoji in print statements
  PYTHONUTF8: 1             # Forces Python to use UTF-8 for all I/O

working-directory: Scripts\POS_Workspace   # pytest must run from here (pytest.ini lives here)
```

---

## Part 4 — How to Trigger the Workflow

### Method 1: Push to `main` branch (Automatic)
Any `git push origin main` triggers the workflow automatically.

### Method 2: Manual Trigger (On-Demand)
1. Go to: `https://github.com/khadarbasha2609/R10_Pywin_Automation/actions`
2. Click **"R10 POS Test Automation"**
3. Click **"Run workflow"** → **"Run workflow"**

---

## Part 5 — Test Execution Lifecycle

```
1. GitHub sends job to runner
         │
         ▼
2. Runner pulls latest code from GitHub
         │
         ▼
3. Offline packages installed (pytest-html etc.)
         │
         ▼
4. pytest collects the test file
         │
         ▼
5. Test function runs:
   ├── Login to POS (checks if already logged in)
   ├── Add item via EAN barcode
   ├── Enter quantity via virtual numpad
   ├── Validate basket contents
   ├── Navigate to Loyalty mode → skip
   ├── Process Cash tender
   ├── Handle receipt popup
   └── Close cash drawer
         │
         ▼
6. Result sent back to GitHub Actions UI
   ✅ PASSED  or  ❌ FAILED with traceback
```

---

## Part 6 — Viewing Results

1. Go to: `https://github.com/khadarbasha2609/R10_Pywin_Automation/actions`
2. Click the latest workflow run
3. Click the job **"test-basic-sale-flow"**
4. Expand each step to see logs

### Reading the Output

| Log Message | Meaning |
|-------------|---------|
| `✅ POS is ready. No Sale button is present.` | POS already logged in, ready to go |
| `✅ Successfully processed item: 9300675014779` | Item scanned successfully |
| `❌ Login button not found` | POS is not on the login screen — check POS state |
| `UnicodeEncodeError` | PYTHONIOENCODING not set — fixed in workflow |
| `ElementNotFoundError` | pywinauto couldn't find a UI element — POS may be in wrong state |

---

## Part 7 — Offline Package Management

Since the POS machine has no internet access (firewall), all Python packages are stored in:

```
Offline_lib/offline_packages/
```

To add a new package:
1. Download the `.whl` file on a machine with internet
2. Copy it to `Offline_lib/offline_packages/`
3. Add the package name to the install step in `main.yml`
4. Add it to `Offline_lib/requirements.txt` for documentation

---

## Part 8 — Troubleshooting Quick Reference

| Problem | Cause | Fix |
|---------|-------|-----|
| Runner says "session already exists" | Runner is registered as a Windows Service | Stop service, run `run.cmd` interactively |
| `Execution policy` error | PowerShell blocks scripts | Run `Set-ExecutionPolicy RemoteSigned -Scope LocalMachine` |
| `UnicodeEncodeError` on emoji | Console encoding is cp1252 | Set `PYTHONIOENCODING: utf-8` in workflow env |
| `pytest-html` INTERNALERROR | pytest-html not installed | Installed via offline packages in workflow |
| `ElementNotFoundError` on POS element | POS in wrong state or wrong screen | Ensure POS is on sale-ready screen before triggering |
| Test PASSED but POS didn't move | Test used `return False` instead of `assert` | All steps now use `assert` to properly fail |
| Runner not picking up jobs | Runner stopped or running as service | Restart `run.cmd` interactively in cmd window |

---

## Part 9 — File Structure Reference

```
R10_Pywin_Automation/
├── .github/
│   └── workflows/
│       └── main.yml                    ← GitHub Actions workflow definition
├── Scripts/
│   ├── python.exe                      ← Venv Python executable (called directly)
│   └── POS_Workspace/
│       ├── pytest.ini                  ← pytest configuration
│       ├── Components/                 ← Reusable POS automation components
│       │   ├── Common_components/
│       │   │   ├── pos_login.py        ← Login handler
│       │   │   └── handle_any_popup_POS.py
│       │   ├── Salemode/
│       │   │   └── Keyin_item.py       ← EAN item entry
│       │   ├── Tenders/
│       │   │   └── Cash_tender_payment.py
│       │   └── Loyalty/
│       │       └── Loyalty_popup_validation.py
│       └── tests/
│           └── Legistlation/
│               ├── TC014_basic_sale_flow.py  ← Basic sale test
│               └── TC018_100QTy.py           ← 100x quantity test
├── Lib/
│   └── site-packages/                  ← All installed Python packages
└── Offline_lib/
    ├── requirements.txt                ← Package list for documentation
    └── offline_packages/               ← .whl files for offline install
```

---

## Summary

| What | Detail |
|------|--------|
| **Runner type** | Self-hosted, Windows, X64 |
| **Runner machine** | `1090SMNPRG007` (POS machine) |
| **Runner user** | `ValidUser` (Session 2 — active console) |
| **Python** | 3.12.4 (from repo venv `Scripts\python.exe`) |
| **Test framework** | pytest 8.4.1 + pytest-html 4.1.1 |
| **UI automation** | pywinauto 0.6.9 (UIA backend) |
| **Trigger** | Push to `main` or manual `workflow_dispatch` |
| **Internet required** | ❌ No — all packages in `Offline_lib/offline_packages/` |
