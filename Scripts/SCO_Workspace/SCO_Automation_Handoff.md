# SCO Automation — Agent Handoff Document

**Project:** NCR NEXTGENUI Self-Checkout (SCO) Test Automation  
**Tech Stack:** Python + pywinauto (UIA backend) + smbclient  
**Working Directory:** `C:\Pywinauto\R10_Pywin_Automation\Scripts\SCO_Workspace`  
**Python Interpreter:** `C:\Pywinauto\R10_Pywin_Automation\Scripts\python.exe`

---

## 1. Project Overview

Automated test suite for Woolworths SCO terminals using **NCR NEXTGENUI** software. Tests verify that EDR (Everyday Rewards) loyalty card transactions are correctly processed and settled via **EagleEye (EE)**.

**What EagleEye is:** A loyalty/voucher platform that validates cards, opens wallet sessions, and settles transactions. All tests verify EE logs after transaction completion.

---

## 2. Repository Structure

```
SCO_Workspace/
├── Components/                    ← Reusable automation modules
│   ├── global_instance.py         ← Shared state (win, app, reward_redeem_status, etc.)
│   ├── Login_POS.py               ← Connect to SCO window, verify idle
│   ├── Add_item.py                ← Scan EAN barcodes into basket
│   ├── Scan_item.py               ← Low-level barcode input helper
│   ├── Scan_loyalty_salemode.py   ← Scan EDR card BEFORE PayButton (sale mode)
│   ├── Scan_loyalty_tenderprompt.py ← Scan EDR card AFTER PayButton (loyalty prompt)
│   ├── Move_to_tendermode.py      ← Click PayButton → wait for payment screen
│   ├── Complete_transaction.py    ← Click Tender2 (Card) → wait for EFT completion
│   ├── Redeem_reward_voucher.py   ← Tender3 → attendant login → voucher select → GoBack
│   ├── Redeem_collectable_offer.py ← PopupFrame collectable offer handler
│   ├── Redeem_choice_offer.py     ← ContainerButtonList choice offer (OCR-based)
│   ├── Verify_EagleEye_logs.py    ← Read EE log file, verify settle/open/validate events
│   ├── Promotion_details.py       ← Read promotion prices from basket
│   ├── Total_amount_details.py    ← Read basket total amounts
│   ├── Read_csv.py                ← Read test data from SMB share CSV
│   ├── Update_csv.py              ← Write results back to CSV
│   └── report.py                  ← HTML report logger + screenshot capture
├── Testing/                       ← Test scripts (one per TC)
│   ├── TC_001_SCO_Registeredcardlessthan1000points.py   ✅ WORKING
│   └── TC_002_SCO_Registeredcardmorethan2000points.py   🔧 IN PROGRESS
├── Results/                       ← HTML reports saved here per run
├── resources/                     ← Local resource files
├── sco-automation.instructions.md ← Auto-loaded domain rules (keep updated)
├── setup_TC001_csv_data.py        ← One-time CSV row writer for TC_001
└── setup_TC002_csv_data.py        ← One-time CSV row writer for TC_002
```

---

## 3. Test Data — CSV

**Remote CSV path (what scripts read):**
```
\\10.80.19.218\d$\RTL_Pywinauto\SaleData.csv
```
**Local copy (for reference only — scripts do NOT read this):**
```
C:\Pywinauto\R10_Pywin_Automation\Scripts\POS_Workspace\RTLPOSFlow\resources\SaleData.csv
```

**CSV Columns:**
| Column | Description |
|--------|-------------|
| `Banner` | `SM` for Woolworths SCO |
| `TC_ID` | e.g. `TC_001`, `TC_002` |
| `Iteration` | `1` (integer) |
| `EAN_Codes` | Semicolon-separated EAN barcodes e.g. `9310072000282;9310072000282` |
| `Item_EAN` | Alternate single EAN column (fallback) |
| `Card_number` | EDR loyalty card barcode |
| `Choice_offer` | e.g. `$10` (only needed for redemption TCs) |

**Current data rows:**
| Banner | TC_ID | Iteration | EAN_Codes | Card_number | Choice_offer |
|--------|-------|-----------|-----------|-------------|--------------|
| SM | TC_001 | 1 | `9310072000282` | `9353109614779` | _(empty)_ |
| SM | TC_002 | 1 | `9310072000282;9310072000282;9310072000282;9310072000282;9310072000282` | `9353109614656` | `$10` |

**To read a value in a test script:**
```python
from Components.Read_csv import get_csv_value
val = get_csv_value("saledata", "SM", "TC_003", 1, "Card_number")
```

> ⚠️ `get_csv_value()` uses `smbclient` internally — never use Python `open()` on UNC paths, it raises `[Errno 22]`.

---

## 4. EAN Code Used in ALL SCO Tests

```
EAN: 9310072000282  →  Arn Tim Tam 200g  →  $2.40 each
```

Only the **card number** changes per test case. Quantity of items changes based on scenario (e.g. need >$10 basket for $10 redemption → scan 5 items = $12.00).

---

## 5. Tender Button auto_ids (CONFIRMED from live dump)

| auto_id | Payment Type |
|---------|-------------|
| `Tender1` | Cash — **BLOCKED** on this Card-Only SCO |
| `Tender2` | **Card (EFT) — always use this** |
| `Tender3` | Reward Voucher (triggers attendant login flow) |
| `Tender4` | Present but type unknown — check per scenario |
| `OtherPaymentButton` | Gift Cards & Other |

---

## 6. ⚠️ CRITICAL Rules — Read Before Writing Any Code

### Rule 1: NEVER use `is_enabled()` on NCR SCO popup buttons
Popup buttons return `is_enabled() = False` in UIA even when they are fully clickable. **Always use `exists()` only, then click directly.**
```python
# ✅ CORRECT
btn = win.child_window(auto_id="ASAOKButton", control_type="Button")
if btn.exists(timeout=2.0):
    btn.click_input()

# ❌ WRONG — will never click
if btn.exists() and btn.is_enabled():
    btn.click_input()
```

### Rule 2: NEVER stop EFT services before payment
`RemedyEFTPOSServer` + `MultiSimulator.exe` must stay **RUNNING** at all times during tests. They auto-approve the card payment. Never call:
- `ensure_EFTSimulator_closed()`
- `ensure_services_stopped()`

### Rule 3: NEVER use sidebar elements to detect tender screen
These elements are **permanently visible** in the SCO sidebar across ALL screens (idle, sale, tender):
- `TotalAmountValue`
- `DueAmountValue`
- `RewardTextBlock` ("Current Rewards Balance")
- `WoWRewardPoints`

Using them as screen-detection indicators causes immediate false-positives. Only use **payment-overlay-exclusive** controls: `Tender2`, `Tender1`, `TenderGroupMenuViewExitButton`.

### Rule 4: PopupFrame is always present — do NOT treat as a popup
`PopupFrame` (Pane) always exists in the UIA tree with 7 permanent navigation buttons (`UNavMoveToLeftButton`, `UNavLeftButton`, etc.). Only treat it as a real popup when it also contains `RedeemButton` or `SkipCollectableOfferPrompt`.

### Rule 5: EFT timeout must be 90 seconds minimum
The EFT simulator is operated manually by the operator. `_EFT_APPROVAL_TIMEOUT = 90` — do not reduce below 60s.

### Rule 6: Do NOT call move_to_tendermode() before scan_loyalty_tenderprompt()
`scan_loyalty_tenderprompt()` clicks PayButton itself. Calling `move_to_tendermode()` first will click PayButton twice.

---

## 7. Loyalty Scan — Two Paths

| Scenario | Component | Description |
|----------|-----------|-------------|
| Card scanned **before PayButton** (sale mode) | `Scan_loyalty_salemode.py` | Used in TC_001 |
| Card scanned **after PayButton** (loyalty prompt screen) | `Scan_loyalty_tenderprompt.py` | Used in TC_002+ |

**Sale mode scan** triggers an "Assistance Needed" popup (card barcode treated as unknown EAN). This popup MUST be dismissed before proceeding to `move_to_tendermode()`. The component handles this automatically.

**Tender prompt scan** flow:
1. `scan_loyalty_tenderprompt()` clicks PayButton
2. Waits for `CustomSkip` button (loyalty prompt screen)
3. Scans the card barcode
4. Waits briefly for any popup
5. Returns — the redemption (if any) happens at the payment screen

---

## 8. Redemption Flow for TC_002 (>2000 pts, $10 redemption)

After loyalty scan at tender prompt → payment screen shows **Tender3**:

```
click Tender3
  → "Assistance Needed" popup (store login required)
    → StoreLogin button → enter username ("ms") → EnterButton
    → enter password ("abcd1234") → EnterButton
  → "Card Tender Declined" screen
    → click OK (ASAOKButton or OK_Button)
  → click "Rewards Vouchers" (Text control)
  → select voucher: "Redeem $10" or "$10" (whichever appears)
  → click List4Button (confirm)
  → click GoBack
  → SCO returns to "Select Payment Type"
then click Tender2 (Card EFT) for remaining balance
```

Component: `Redeem_reward_voucher.py`

---

## 9. Completed Test Cases

### ✅ TC_001 — Registered Card < 1000 Points (No Redemption)
**File:** `Testing/TC_001_SCO_Registeredcardlessthan1000points.py`
**Flow:** `login_pos → add_item(1×EAN) → scan_loyalty_salemode → move_to_tendermode → complete_transaction → verify_eagleeye_logs`
**Card:** `9353109614779`
**Status:** PASSING

### 🔧 TC_002 — Registered Card > 2000 Points ($10 Redemption)
**File:** `Testing/TC_002_SCO_Registeredcardmorethan2000points.py`
**Flow:** `login_pos → add_item(5×EAN=$12) → scan_loyalty_tenderprompt → redeem_reward_voucher(Tender3) → complete_transaction(Tender2) → verify_eagleeye_logs`
**Card:** `9353109614656`
**Status:** IN PROGRESS — `redeem_reward_voucher` component just built, not yet tested end-to-end

---

## 10. How to Create a New Test Case

### Step 1: Add CSV row
Open `\\10.80.19.218\d$\RTL_Pywinauto\SaleData.csv` and add:
```
SM,TC_003,1,9310072000282,9310072000282,<card_number>,<choice_offer_if_any>
```

### Step 2: Create the test script
Copy the closest existing TC as a template. Pattern:

```python
"""TC_00X description"""
import sys
from pathlib import Path
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode  # or tenderprompt
from Components.Move_to_tendermode import move_to_tendermode         # only for salemode path
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID = "TC_00X"
BANNER = "SM"
ITERATION = 1
logger.set_tc_id(TC_ID)

def _get_value(column, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback

EAN_LIST  = _get_value("EAN_Codes", None) or _get_value("Item_EAN", "9310072000282")
CARD_CODE = _get_value("Card_number", "<fallback_card>")

try:
    if not login_pos(): raise RuntimeError("login_pos failed")
    add_item(EAN_LIST, CARD_CODE)
    # ... scenario-specific steps ...
    if not complete_transaction(): raise RuntimeError("complete_transaction failed")
    ee_result = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    if not ee_result["all_passed"]:
        logger.log("❌ EagleEye verification failed.", status="fail")
    else:
        logger.log(f"✅ {TC_ID} PASSED.", status="pass")
except Exception as e:
    logger.log(f"❌ Unexpected error in {TC_ID}: {e}", status="fail")
    print(f"❌ {TC_ID} ERROR: {e}")
    logger.take_screenshot(f"{TC_ID}_Unexpected_Error")
finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
```

### Step 3: Run the test
```
& C:\Pywinauto\R10_Pywin_Automation\Scripts\python.exe C:\Pywinauto\R10_Pywin_Automation\Scripts\SCO_Workspace\Testing\TC_00X_<name>.py
```

### Step 4: Check results
- Console output — real-time progress
- `Results/TC_00X.html` — full HTML report with screenshots

---

## 11. Component API Quick Reference

### `login_pos()`
Connects to the SCO window (NCR NEXTGENUI) and verifies idle state.
Returns `bool`.

### `add_item(ean_list, card_code)`
- `ean_list`: string of semicolon-separated EANs or single EAN
- `card_code`: loyalty card (used for validation logging only — NOT scanned here)
- Scans each EAN barcode, waits for item to appear in basket
- Returns `bool`

### `scan_loyalty_salemode(card_code)`
Scans loyalty card in sale mode (before PayButton). Automatically dismisses "Assistance Needed" popup.
Returns `bool`.

### `scan_loyalty_tenderprompt(card_code)`
Clicks PayButton, waits for loyalty prompt (`CustomSkip`), scans card, waits 3s for popup.
Returns `bool`. **Do NOT call `move_to_tendermode()` before this.**

### `move_to_tendermode()`
Clicks PayButton, waits for payment overlay (`Tender2` visible).
Only use this after `scan_loyalty_salemode()` (TC_001 pattern).
Returns `bool`.

### `redeem_reward_voucher(reward_tender_id, voucher_options, username, password)`
Full Tender3 → attendant login → voucher select flow.
- `reward_tender_id`: default `"Tender3"`
- `voucher_options`: list of labels to try, e.g. `["Redeem $10", "$10", "Skip"]`
- `username`: default `"ms"`, `password`: default `"abcd1234"`
- Sets `global_instance.reward_redeem_status = True` on success
Returns `bool`.

### `complete_transaction()`
Finds Card button (Tender2), clicks it, waits 90s for EFT auto-approval.
Handles receipt popup (`No_Button`) and any mid-EFT `ASAOKButton` popups.
Returns `bool`.

### `verify_eagleeye_logs(expect_wallet_open, expect_wallet_settle)`
Reads `C:\Retalix\EEAdapter\Logs\EEAdapter_{date}.{n}.log` from `ee_log_start_time`.
Returns dict: `{"all_passed": bool, "wallet_open": bool, "wallet_settle": bool, "settled_status": str}`

### `redeem_collectable_offer(offer_type, collectable_offer_list)`
Handles `PopupFrame` collectable offers.
- `collectable_offer_list`: `"message text_ButtonLabel"` (underscore separates message from button)
- Semicolon-separated for multiple offers
- Button label defaults to `"No"` if omitted

### `redeem_choice_offer(choice_offer)`
OCR-based. Looks for `ContainerButtonList` popup, finds card matching `choice_offer` text, clicks "Use now".
Used for scenarios where choice offer appears as a popup (NOT the Tender3 flow).

---

## 12. EagleEye Log File

**Path:** `C:\Retalix\EEAdapter\Logs\EEAdapter_{YYYY-MM-DD}.{n}.log`

**What to look for:**
| Event | Log contains |
|-------|-------------|
| Card Validation | `"via POST to validate card number"` |
| Wallet Open | `"wallet/open"` |
| Wallet Settle | `"wallet/settle"` OR `"via POST to Settle Wallet"` |

`verify_eagleeye_logs()` reads the log automatically from `global_instance.ee_log_start_time` (set at start of `complete_transaction()`).

---

## 13. Remaining Test Cases to Build

These are the test cases still to be developed. For each one:
1. Get the EDR card number from the test owner
2. Add CSV row
3. Create test script following the patterns above

| TC_ID | Scenario | Key Difference from TC_001/002 |
|-------|----------|-------------------------------|
| TC_003 | Unregistered card | No EE wallet events expected |
| TC_004 | Card not in EagleEye | EE returns error/no-match |
| TC_005 | Collectable offer | `redeem_collectable_offer()` after loyalty scan |
| TC_006 | Instant win offer | `redeem_collectable_offer(offer_type="Instant Win")` |
| TC_007+ | Other banners (Metro, BigW, BWS) | Change `BANNER` from `"SM"` |

> Ask the test owner for the specific card numbers and exact voucher/offer text for each TC before writing the scripts.

---

## 14. Running Tests

### Pre-requisites (manual — operator must do before each run):
1. `RemedyEFTPOSServer` must be running
2. `MultiSimulator.exe` must be running
3. NCR SCO application must be open and at idle (scan screen)

### Run command:
```powershell
& C:\Pywinauto\R10_Pywin_Automation\Scripts\python.exe `
  C:\Pywinauto\R10_Pywin_Automation\Scripts\SCO_Workspace\Testing\TC_001_SCO_Registeredcardlessthan1000points.py
```

### Reports:
Saved to `Scripts\SCO_Workspace\Results\TC_001.html` (auto-named by TC_ID).

---

## 15. Known Issues & Solutions

| Issue | Root Cause | Fix Applied |
|-------|-----------|-------------|
| `is_enabled()` returns False on clickable buttons | NCR WPF UIA quirk | Removed all `is_enabled()` checks — use `exists()` only |
| ASAOKButton dismissed EFT during payment | `_dismiss_any_popup` called on EFT pinpad screen | Removed popup dismissal from EFT wait loop fallback |
| Tender screen detected too early (false positive) | `TotalAmountValue`/`DueAmountValue` always in sidebar | Only use `Tender2`/`Tender1` for tender screen detection |
| `PopupFrame` always detected as "popup" | 7 nav buttons always present as children | Only treat as popup when `RedeemButton`/`SkipCollectableOfferPrompt` present |
| Choice offer popup missed (auto-dismissed) | Script slept before polling | Removed sleep, immediate polling at 0.1s intervals |
| 3 items scanned instead of 5 | `PayButton` enabled early triggered fast-path | Keep scanning remaining items even when PayButton enabled |
| SMB CSV raises `[Errno 22]` | Python `open()` doesn't support UNC paths | Always use `smbclient.open_file()` in Read_csv.py |
| TC_002 `complete_transaction` failed | Tender3 (reward) triggers full attendant login flow, not just a button click | Created `Redeem_reward_voucher.py` to handle full flow |

---

## 16. File Naming Convention

Test scripts: `TC_00X_SCO_<ScenarioName>.py`
Components: `PascalCase.py` (e.g. `Scan_loyalty_salemode.py`)
Results: Auto-named by logger using `TC_ID`

---

## 17. Adding New Component Rules to `sco-automation.instructions.md`

When you discover a new critical auto_id, timing rule, or SCO quirk — **add it to `sco-automation.instructions.md`**. This file is auto-loaded for all SCO_Workspace scripts and acts as the domain knowledge base for future agents.

Location: `C:\Pywinauto\R10_Pywin_Automation\Scripts\SCO_Workspace\sco-automation.instructions.md`
