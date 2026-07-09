# New Machine Setup Guide — RTL Automation

> Use this guide when setting up RTL Automation on a **fresh / rebuilt Windows machine**.  
> All installer files referenced below were stored in `C:\Pywin\` on the previous machine.

---

## Quick Summary of What's Needed

| Component | Version | Installer File |
|-----------|---------|----------------|
| Python | 3.12.4 (64-bit) | `python-3.12.4-amd64.exe` |
| Tesseract OCR | 5.5.0.20241111 | `tesseract-ocr-w64-setup-5.5.0.20241111.exe` |
| Microsoft Edge Enterprise | (x86 MSI) | `MicrosoftEdgeEnterpriseX86.msi` |
| Visual Studio Code | 1.121.0 | `VSCodeUserSetup-x64-1.121.0.exe` |
| Windows SDK | (setup) | `winsdksetup.exe` |
| Git | Latest | Download from https://git-scm.com |

---

## Step-by-Step Installation Order

### 1. Install Python 3.12.4

- Run `python-3.12.4-amd64.exe`
- **Important:** Check **"Add Python to PATH"** during install
- Choose **"Customize installation"** → install for **All Users**
- Default install path: `C:\Users\<username>\AppData\Local\Programs\Python\Python312\`

Verify:
```cmd
python --version
```
Expected: `Python 3.12.4`

---

### 2. Install Tesseract OCR

- Run `tesseract-ocr-w64-setup-5.5.0.20241111.exe`
- Install to default path: `C:\Program Files\Tesseract-OCR\`
- After install, **add Tesseract to System PATH**:
  - Open: `Control Panel → System → Advanced System Settings → Environment Variables`
  - Under **System Variables**, find `Path` → Edit → Add:
    ```
    C:\Program Files\Tesseract-OCR
    ```

Verify:
```cmd
tesseract --version
```
Expected: `tesseract v5.5.0.20241111`

---

### 3. Install Microsoft Edge

- Run `MicrosoftEdgeEnterpriseX86.msi`
- This installs the Enterprise version of Microsoft Edge required for POS browser automation

---

### 4. Install VS Code (Optional but Recommended)

- Run `VSCodeUserSetup-x64-1.121.0.exe`
- Install the **Python extension** inside VS Code after launch

---

### 5. Install Git

- Download from https://git-scm.com/download/win
- During install, select **"Git from the command line and also from 3rd-party software"**

---

## Step 6 — Clone the Repository

```cmd
mkdir C:\Pywin
cd C:\Pywin
git clone https://github.com/sumap-cloud/RTL.git "RTL Automation"
cd "RTL Automation"
```

---

## Step 7 — Set Up Python Virtual Environment

Create a new virtual environment inside the repo folder:

```cmd
cd "C:\Pywin\RTL Automation"
python -m venv .
```

This creates `Scripts\python.exe`, `Scripts\pip.exe`, etc. inside the repo folder.

---

## Step 8 — Install Python Packages

### Option A — Install from Offline packages (no internet needed)

All wheel files are stored in `Offline_lib\offline_packages\`:

```cmd
cd "C:\Pywin\RTL Automation"
Scripts\pip.exe install --no-index --find-links=Offline_lib\offline_packages -r Offline_lib\requirements.txt
```

### Option B — Install from internet

```cmd
cd "C:\Pywin\RTL Automation"
Scripts\pip.exe install -r Offline_lib\requirements.txt
```

---

### Full Package List (installed on previous machine)

```
certifi==2025.7.14
cffi==2.0.0
colorama==0.4.6
comtypes==1.4.11
cryptography==48.0.0
idna==3.10
iniconfig==2.1.0
numpy==1.26.4
opencv-python==4.10.0.84
packaging==25.0
pillow==10.3.0
pluggy==1.6.0
pycparser==3.0
Pygments==2.19.2
pyspnego==0.12.1
pytesseract==0.3.10
pytest==8.4.1
pytest-html==4.1.1
pytest-metadata==3.1.1
pywin32==306
pywinauto==0.6.9
PyYAML==6.0.2
requests==2.32.4
setuptools==80.9.0
six==1.17.0
smbprotocol==1.16.1
sspilib==0.5.0
urllib3==2.5.0
```

---

## Step 9 — Verify Tesseract Path in Scripts

The automation scripts use `pytesseract`. Make sure the path is set correctly.  
Check any config files or scripts for this line and update if needed:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## Step 10 — Configure GitHub Actions Self-Hosted Runner

Refer to: `Documentation\GitHub_Actions_Setup_Guide.md`

Key steps:
1. Go to the GitHub repo → **Settings → Actions → Runners → New self-hosted runner**
2. Follow the commands provided on that page to download and configure the runner
3. Run the runner as a **Windows Service** so it starts automatically

---

## Step 11 — Running Tests Manually

Double-click `run_tests.bat` in the repo root, **or** from command line:

```cmd
cd "C:\Pywin\RTL Automation"
Scripts\python.exe -m pytest Scripts\SCO_Workspace\Testing\Regression\ -v
```

Edit `run_tests.txt` to specify which test cases to run.

---

## Folder Structure Reference

```
C:\Pywin\
│
├── RTL Automation\              ← Git repository (clone here)
│   ├── Scripts\                 ← python.exe, pip.exe (venv)
│   ├── Lib\site-packages\       ← installed Python packages
│   ├── Offline_lib\
│   │   ├── offline_packages\    ← .whl files for offline install
│   │   ├── pandas_lib\          ← pandas wheel files
│   │   └── requirements.txt     ← package list
│   ├── Scripts\SCO_Workspace\
│   │   └── Testing\Regression\  ← TC_*.py test scripts
│   ├── Documentation\           ← setup guides
│   ├── run_tests.bat            ← double-click to run tests
│   └── run_tests.txt            ← list of test cases to run
│
├── python-3.12.4-amd64.exe      ← Keep these installers on USB/network share
├── tesseract-ocr-w64-setup-5.5.0.20241111.exe
├── MicrosoftEdgeEnterpriseX86.msi
├── VSCodeUserSetup-x64-1.121.0.exe
└── winsdksetup.exe
```

> ⚠️ **The installer .exe/.msi files are NOT stored in Git** (too large).  
> Save them to a **USB drive or network share** before the machine rebuild.

---

## Important Notes

- The **virtual environment** (`Scripts\`, `Lib\`) is embedded inside the repo folder.  
  After cloning, you must recreate it with `python -m venv .` and reinstall packages.
- **Tesseract must be on the System PATH** before running any OCR-related tests.
- The `run_tests.bat` uses `Scripts\python.exe` — this is the **venv Python**, not the system Python.
- Test results and HTML reports are saved to `Scripts\SCO_Workspace\Results\`.

---

## Installer Backup Recommendation

Copy the following files to a USB drive or network share before rebuilding:

```
python-3.12.4-amd64.exe           (~26 MB)
tesseract-ocr-w64-setup-5.5.0.20241111.exe  (~21 MB)
MicrosoftEdgeEnterpriseX86.msi    (~163 MB)
VSCodeUserSetup-x64-1.121.0.exe   (~159 MB)
winsdksetup.exe                   (~1.4 MB)
```

Total: ~370 MB — fits on any USB drive.
