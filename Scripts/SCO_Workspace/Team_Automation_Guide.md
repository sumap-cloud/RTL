# SCO Automation — Team Handout Guide

**Project:** Woolworths / BigW / NZ Self-Checkout (SCO) Test Automation
**Tech Stack:** Python + `pywinauto` (UIA backend) for the NCR NEXTGENUI SCO application
**Machine root:** `C:\Pywin\RTL Automation`
**Python interpreter (venv):** `C:\Pywin\RTL Automation\Scripts\python.exe`

This document is the onboarding/handover guide for the team taking over execution
of this automation suite. It explains what test suites exist, how the data
setup works, how to run tests (single script or full batch), how results are
reported, and the key gotchas that have already been discovered and fixed.

---

## 1. What's in this repository

```
RTL Automation/                        ← venv root — ALWAYS run scripts from here
├── Scripts/
│   ├── python.exe                     ← the interpreter to use for everything below
│   └── SCO_Workspace/                 ← all SCO automation code lives here
│       ├── Components/                ← shared reusable automation modules
│       ├── Data/                      ← test data CSVs
│       ├── Results/                   ← HTML reports + screenshots (auto-generated)
│       ├── Testing/
│       │   ├── Sanity/                ← quick smoke-test suite (11 scripts)
│       │   ├── Regression/            ← full Woolworths (SM) regression suite (37 scripts)
│       │   ├── BigW/                  ← Big W banner regression suite (32 scripts)
│       │   └── NZ/                    ← New Zealand banner regression suite (19 scripts)
│       └── sco-automation.instructions.md
```

### The four test suites

| Suite folder | Banner (CSV) | Purpose |
|---|---|---|
| `Testing/Sanity` | `SM` | Small smoke-test set (TC_001–TC_011) — run first to confirm the environment/EFT/EagleEye stack is healthy. |
| `Testing/Regression` | `SM` | Full Woolworths Supermarket regression pack (largest suite). |
| `Testing/BigW` | `BigW` | Same scenarios as Regression, adapted/re-verified for the Big W banner. |
| `Testing/NZ` | `NZ` | Same scenarios adapted for the New Zealand banner/store config. |

All four suites share the exact same `Components/` automation modules — a fix
made in `Components/` (e.g. `Complete_transaction.py`) benefits every suite
at once.

---

## 2. One-time machine setup (new team member / new machine)

1. Install Python 3.12 and this project's venv is already checked into the
   repo at `Scripts\`. Confirm the interpreter works:
   ```powershell
   & "C:\Pywin\RTL Automation\Scripts\python.exe" --version
   ```
2. If `pywinauto`/`win32gui`/etc. are missing (fresh clone/migration), install
   from the offline wheel cache — **no internet access is required/assumed
   on the SCO test machine**:
   ```powershell
   cd "C:\Pywin\RTL Automation\Offline_lib"
   pip install --no-index --find-links="offline_packages" -r requirements_clean.txt
   ```
   (`requirements_clean.txt` is the numbered `requirements.txt` with the list
   numbers stripped — regenerate it with a one-line PowerShell command if it's
   ever missing; see `requirements.txt` in the same folder.)
3. Confirm the NCR NEXTGENUI SCO application is installed, running, and the
   `RemedyEFTPOSServer` + `MultiSimulator.exe` (EFT simulator) processes are
   running — **these must NEVER be stopped while tests run**, they auto-approve
   card payments.
4. Set VS Code's Python interpreter (`.vscode/settings.json`) to
   `C:\Pywin\RTL Automation\Scripts\python.exe` if it isn't already.

---

## 3. ⚠️ CRITICAL: always run from the project root

**Every script must be run with `C:\Pywin\RTL Automation` as the current
working directory** — NOT from inside `Testing\NZ` or any suite subfolder.

```powershell
# ✅ CORRECT
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe "Scripts\SCO_Workspace\Testing\NZ\TC_02_VerifyBasketPointsFixedCampaign.py"

# ❌ WRONG — do not cd into the suite folder first
cd "C:\Pywin\RTL Automation\Scripts\SCO_Workspace\Testing\NZ"
python TC_02_VerifyBasketPointsFixedCampaign.py
```

**Why this matters:** `Components/report.py` writes its HTML report and
screenshots to a path that is relative to the process's current working
directory (`./Scripts/SCO_Workspace/Results`). If you run from the wrong
folder, the report/screenshots silently get written into a bogus **nested**
folder instead of the shared `Results/` folder, and you'll think the test
didn't produce a report at all. (This exact mistake happened once during
development and left a stray `Testing\NZ\Scripts\SCO_Workspace\Results\...`
folder — since cleaned up.)

The provided VS Code task (`.vscode/tasks.json` → "Run TC_02 (NZ Basket Points
Fixed Campaign)") already sets the correct working directory for you.

---

## 4. Test data — CSV

**File:** `Scripts\SCO_Workspace\Data\RegressionSale.csv` (local file, no SMB/network share needed)

| Column | Description |
|---|---|
| `Banner` | `SM` (Woolworths/Sanity/Regression), `BigW`, or `NZ` |
| `TC_ID` | Full test id, e.g. `TC_02_VerifyBasketPointsFixedCampaign` |
| `Iteration` | Row number for that TC_ID (usually `1`) |
| `Item_EAN` / `EAN_Codes` | Barcode(s) to scan — semicolon-separated for multiple |
| `Card_number` | Loyalty (EDR/SDC/etc.) card barcode |
| Other columns | Scenario-specific (offer text, choice offer, exclusion EANs, etc.) — each script documents which columns it reads in its own docstring. |

Each test script reads its row via `Components/Read_csv.py`:
```python
from Components.Read_csv import get_csv_value
val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, "Card_number")
```
If a column/row is missing, scripts fall back to a hardcoded default value
(printed as a `⚠️ Using fallback` warning) so a missing CSV row doesn't hard-crash
a script — but you should still add the correct row so the intended data is used.

**To add/update data for a new or existing scenario:** open `RegressionSale.csv`
directly (Excel or a text editor) and add/edit the row matching `Banner` +
`TC_ID` + `Iteration`.

---

## 5. Running tests

### 5a. Run a single script
```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe "Scripts\SCO_Workspace\Testing\NZ\TC_02_VerifyBasketPointsFixedCampaign.py"
```
Report: `Scripts\SCO_Workspace\Results\<TC_ID>.html` (screenshots alongside in
a subfolder of the same name).

### 5b. Run a whole suite (batch) — recommended for full regression passes
Each suite folder has its own `run_all_<Suite>.py` entry script:

```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe "Scripts\SCO_Workspace\Testing\NZ\run_all_NZ.py"
.\Scripts\python.exe "Scripts\SCO_Workspace\Testing\BigW\run_all_BigW.py"
.\Scripts\python.exe "Scripts\SCO_Workspace\Testing\Regression\run_all_Regression.py"
.\Scripts\python.exe "Scripts\SCO_Workspace\Testing\Sanity\run_all_Sanity.py"
```

**What the batch runner does (see `Components/Batch_runner.py`):**
1. Discovers every `TC_*.py` script directly in that suite's folder, sorted
   in natural TC-number order.
2. Resets the SCO to the **Welcome/idle screen** before the very first script.
3. Runs each script one at a time (as its own Python process).
4. **After every single script — whether it PASSED, FAILED, or crashed — it
   automatically resets the SCO back to the Welcome screen** before starting
   the next script. This is the fix for the "leftover state from the last
   test breaks the next test" problem.
5. Reads the PASS/FAIL badge out of that script's HTML report.
6. Produces a consolidated summary at the end:
   - Console table of every script's result
   - `Results\BatchSummary_<Suite>_<timestamp>.txt`
   - Per-script raw console output saved to `Results\BatchLogs\<Suite>_<TC>_<timestamp>.log`
     (useful for debugging a failure without re-running it)

A batch run can safely be left running unattended — one script failing does
NOT stop the batch; it resets and moves on to the next script.

---

## 6. How "reset to Welcome screen" works

**Component:** `Components/Reset_to_welcome.py`

This is a best-effort recovery utility (also usable standalone: `python
Components\Reset_to_welcome.py`). Regardless of what screen the SCO is
currently stuck on — mid-basket, mid-payment, a hung "Cancel Purchase" or
"Assistance Needed" popup, an attendant login screen, etc. — it repeatedly:
1. Identifies the current screen.
2. If already at the Welcome screen → done, exit success.
3. Otherwise tries a priority-ordered list of recovery clicks (void/cancel
   sale buttons → dismiss popups → leave attendant overlays) and re-checks.
4. Repeats up to 25 rounds (~40s) before giving up and logging a diagnostic
   dump + screenshot for troubleshooting.

It never raises/crashes the batch — it always returns control so the next
script can attempt to run (even if the reset itself wasn't fully successful,
you'll see a clear `RESET: FAILED` marker in the console/log to investigate).

---

## 7. Key domain knowledge (already discovered — don't re-investigate these)

### Tender / payment buttons (NCR NEXTGENUI "Select Payment Type" screen)
| auto_id | Payment type |
|---|---|
| `Tender1` | Cash (may be blocked depending on SCO config) |
| `Tender2` | **Cash** |
| `Tender3` | **Card (Full Payment)** ← use this for card/EFT payment |
| `Tender4` | Card & Cash Out |

> ⚠️ `Tender2` was historically (incorrectly) assumed to be Card in some
> older code/docs (see `sco-automation.instructions.md`, which is stale on
> this point). `Components/Complete_transaction.py` now correctly uses
> `Tender3`.

### "Assistance Needed — Cancel Purchase" popup
Can appear unpredictably (immediately, with a delay, or multiple times) after
clicking `PayButton`. `Complete_transaction.py` auto-detects and declines it via:
Store Log In (`StoreLogin` → enter `ms` / `abcd1234`) → click the `No` control
(a `Text` element with `title="No"`, not a `No_Button`). Declining returns the
SCO to the **basket/scan screen**, not the tender screen — the code re-clicks
`PayButton` and retries automatically.

### Other confirmed UI quirks
- Never use `is_enabled()` on NCR SCO popup buttons — it returns `False` even
  when clickable. Always use `exists()` then click directly.
- Never stop `RemedyEFTPOSServer` / `MultiSimulator.exe` during a test run.
- EFT approval timeout should be 90s minimum (manual/simulated approval).

For full up-to-date details, see the "known issues" tables inside individual
component docstrings (`Complete_transaction.py`, `Reset_to_welcome.py`) and
`sco-automation.instructions.md`.

---

## 8. Adding a new test case

1. Add a data row to `Data\RegressionSale.csv` (`Banner`, `TC_ID`, `Iteration`,
   plus whatever columns the scenario needs).
2. Copy the closest existing script in the relevant suite folder as a
   template (same `Banner` value, same import pattern at the top).
3. Update `TC_ID` / `BANNER` / `ITERATION` constants and the scenario-specific
   steps.
4. Run it standalone first (Section 5a) to verify before adding it to batch runs.
5. It will automatically be picked up by that suite's `run_all_<Suite>.py`
   next time the batch runs (no registration step needed — it just discovers
   `TC_*.py` files).

---

## 9. Reports & troubleshooting

- **Individual report:** `Results\<TC_ID>.html` — green "PASSED" or red
  "FAILED" badge at the top, step-by-step table, screenshots on failures.
- **Batch summary:** `Results\BatchSummary_<Suite>_<timestamp>.txt`
- **Raw console logs (batch only):** `Results\BatchLogs\`
- If a script errors with an import error (`ModuleNotFoundError`), re-run the
  offline package install command from Section 2.
- If the SCO is left in a strange/stuck state after a manual (non-batch) test
  run, run the reset utility directly:
  ```powershell
  cd "C:\Pywin\RTL Automation"
  .\Scripts\python.exe "Scripts\SCO_Workspace\Components\Reset_to_welcome.py"
  ```

---

## 10. Questions / escalation

For anything not covered here, check:
- `sco-automation.instructions.md` (domain rules/auto_id reference — flag
  anything that looks contradictory to what's in this guide, some content
  there predates the Tender2/3 fix above)
- Component docstrings (each `Components/*.py` file documents its own flow)
- Git history / commit messages for the reasoning behind recent fixes
