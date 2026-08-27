# R10_Pywin_Automation

R10 Stores QA Automation repo — Pywinauto.

Two independent automation projects live in this repository:

| Project | Location | What it drives |
|---|---|---|
| **SCO automation** | `Scripts/SCO_Workspace/` | NCR NEXTGENUI self-checkout — loyalty, offers, campaigns, redemptions. This is the actively maintained suite. |
| POS automation | `Scripts/POS_Workspace/` | Older R10 Point-of-Sale suite (pytest-based). |

## 📚 Start here — Knowledge Transfer pack

**[Documentation/KT_Sessions/](Documentation/KT_Sessions/00_KT_Pack_Index.md)** —
six presenter-ready sessions taking a complete beginner from installing the
software to writing and maintaining test scripts. If you are new to this
project, read these in order.

## Setup on a new machine

See **[Documentation/NEW_MACHINE_SETUP.md](Documentation/NEW_MACHINE_SETUP.md)**
for complete step-by-step instructions.

### Quick start

1. Clone this repo to `C:\Pywin\RTL Automation`.
2. Install Python 3.12.4, Tesseract OCR 5.5.0, Git and the Windows SDK
   (installers are in `C:\Pywin`).
3. Create the virtual environment **in the repo folder**:
   `"C:\Program Files\Python312\python.exe" -m venv .`
   > ⚠️ The repository root *is* the virtual environment (`pyvenv.cfg` sits at
   > the root). Always use `.\Scripts\python.exe`.
4. Install packages — offline:
   `Scripts\pip.exe install --no-index --find-links=Offline_lib\offline_packages -r Offline_lib\requirements.txt`
5. Double-click **`Run_Suite.bat`** and choose a banner (Sanity, Regression,
   BigW or NZ).

## Running tests

| Entry point | Scope |
|---|---|
| `Run_Suite.bat` | **Preferred.** Menu → Sanity / SM / Metro / BigW / NZ / Regression |
| `Scripts\SCO_Workspace\Testing\<Suite>\run_all_<Suite>.py` | Same, from the command line |
| `run_tests.bat` + `run_tests.txt` | Older list-driven runner (Regression only) |

Always run with the project root as the working directory:

```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe Scripts\SCO_Workspace\Testing\Sanity\TC_001_SCO_Registeredcardlessthan1000points.py
```

Reports land in `Scripts\SCO_Workspace\Results\<Suite>\` (not committed to git).

### The suites

| Suite | Scripts | Banner | Notes |
|---|---|---|---|
| `Sanity` | 11 | `SM` | Quick smoke — run this first |
| `SM` | 37 | `SM` | Supermarket |
| `Metro` | 37 | `Metro` | Metro |
| `BigW` | 32 | `BigW` | Not yet validated end to end on a BigW lane |
| `NZ` | 19 | `NZ` | Countdown / New Zealand |
| `Regression` | 37 | `SM` | **Legacy.** The original combined SM/Metro folder. `SM` is a byte-identical copy of it — change both, or retire this one. |

## Test data

All test data for every banner lives in a single file:

```
Scripts\SCO_Workspace\Data\RegressionSale.csv
```

Rows are selected by **Banner + TC_ID + Iteration**. Banner values are `SM`,
`Metro`, `BigW` and `NZ`.

Verify that every script actually finds its row — a mismatch does **not** raise,
it silently falls back to a hardcoded value and the test goes green on the wrong
data:

```powershell
.\Scripts\python.exe Scripts\SCO_Workspace\Tools\audit_csv_lookup.py
```

> ⚠️ **Never open this file in Excel.** Excel rewrites 13-digit card numbers as
> scientific notation (`9.35522E+12`) and the digits are lost permanently.
> Edit it in a plain-text editor. Check for damage with:
> `Select-String Scripts\SCO_Workspace\Data\RegressionSale.csv -Pattern "E\+\d"`

## Key documents

| Document | Purpose |
|---|---|
| [`Documentation/KT_Sessions/`](Documentation/KT_Sessions/00_KT_Pack_Index.md) | Six-session knowledge transfer pack |
| [`Documentation/NEW_MACHINE_SETUP.md`](Documentation/NEW_MACHINE_SETUP.md) | Machine setup from scratch |
| [`Documentation/GitHub_Actions_Setup_Guide.md`](Documentation/GitHub_Actions_Setup_Guide.md) | Self-hosted CI runner |
| `Scripts/SCO_Workspace/Team_Automation_Guide.md` | Day-to-day usage guide |
| `Scripts/SCO_Workspace/sco-automation.instructions.md` | **SCO domain knowledge** — auto_ids, popup behaviour, quirks |

## Recovering a stuck lane

```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe Scripts\SCO_Workspace\Components\Hard_reset_SCO.py
```

Tries to click back to the Welcome screen and, failing that, restarts the SCO
application and logs the lane back in. The batch runner does this automatically
between every test.
