---
description: SCO Automation — NCR NEXTGENUI. Auto-loaded for all SCO_Workspace scripts.
applyTo: 'Scripts/SCO_Workspace/**'
---

# SCO Automation — NCR NEXTGENUI Domain Knowledge

## ⚠️ CRITICAL: Card-Only SCO
- `RemedyEFTPOSServer` + `MultiSimulator.exe` must stay **RUNNING** — they auto-approve card payments
- **NEVER** call `ensure_EFTSimulator_closed()` or `ensure_services_stopped()` before payment
- Card payment button = **`Tender2`** (not Tender1=Cash, which is blocked on this SCO)

## Tender Button auto_ids (from live control dump)
| auto_id | Payment Type |
|---|---|
| `Tender1` | Cash — **BLOCKED** on Card-Only SCO |
| `Tender2` | **Card EFT ← always use this** |
| `Tender3` | Card Split Payment |
| `OtherPaymentButton` | Gift Cards & Other |

## Loyalty Scan in Sale Mode — Popup Behaviour
Scanning loyalty card barcode in sale mode triggers **two things**:
1. ✅ Loyalty card accepted (`Loyaltyregistered='Registered'`, `WoWRewardPoints` shown)
2. ❌ Also treated as unknown product EAN → "Item not found" → **"Assistance Needed" popup**

**This popup blocks PayButton.** Dismiss immediately after loyalty scan.

### Dismiss order (ASAOKButton FIRST):
```python
for aid in ["ASAOKButton", "OK_Button", "GenericOKButton", "GenericButton", "CustomSkip"]:
    btn = win.child_window(auto_id=aid, control_type="Button")
    if btn.exists(timeout=2.0):   # ← NO is_enabled() check
        btn.click_input()
        time.sleep(1.5)
        break
```

## ⚠️ NEVER use `is_enabled()` on NCR SCO Popup Buttons
Popup buttons return `is_enabled()=False` in UIA even when they ARE clickable.
Always use `exists()` only, then click directly.

## UNC Path / SMB CSV Access
Python `open()` raises `[Errno 22]` on `\\server\share\` UNC paths.
**Always use `smbclient.open_file()`** — affects `Read_csv.py` and `Update_csv.py`.

## CSV Column Names
- SCO_Workspace: `EAN_Codes` | POS_Workspace: `Item_EAN` — always try both.

## Key Control auto_ids
| auto_id | Purpose |
|---|---|
| `PayButton` | Move from sale → tender mode |
| `Tender2` | Card EFT payment button |
| `CustomSkip` | Skip loyalty prompt after PayButton |
| `ASAOKButton` | Dismiss "Assistance Needed" popup |
| `OK_Button` | Generic popup OK |
| `No_Button` | Receipt popup "No" |
| `Loyaltyregistered` | Text: "Registered" when loyalty accepted |
| `WoWRewardPoints` | Points balance text |
| `DueAmountValue` | Balance due on tender screen |

## Tender Screen Detection — `_is_tender_screen_visible`
`TotalAmountValue` and `DueAmountValue` are **permanently visible** in the SCO sidebar even in sale/idle mode.
**NEVER use them** to detect tender mode — they cause instant false-positives.
Only use buttons exclusive to the payment overlay: `Tender2`, `Tender1`, `TenderGroupMenuViewExitButton`.

## EFT Approval Timeout
`_EFT_APPROVAL_TIMEOUT` = **90 seconds** — the EFT simulator is operated manually, so the approval wait must be generous.
Do not reduce below 60 seconds.

## ⚠️ EagleEye Log Start Time — Set in Login_POS (NOT Complete_transaction)
For loyalty-prompt-scan TCs (TC_002, TC_003, ...), the EagleEye **card validation** and **wallet/open** events fire at the moment the loyalty card is scanned — which is BEFORE `complete_transaction()` runs. Recording `ee_log_start_time` inside `complete_transaction()` makes `verify_eagleeye_logs()` miss those events → false fails like "Card Validation event NOT found" + "Wallet Open event NOT found".

**Fix already applied:**
- `Login_POS.py` sets `global_instance.ee_log_start_time = datetime.now()` at the end of successful login.
- `Complete_transaction.py` only sets it if still `None` (won't overwrite the earlier value).

When adding new components that should bracket EE events (e.g. a future training-mode launcher), follow the same pattern: set the start time as early as possible, never overwrite a non-None value.


Path: `C:\Retalix\EEAdapter\Logs\EEAdapter_{YYYY-MM-DD}.{n}.log`
- Card Validation: `"via POST to validate card number"`
- Wallet Open: `"wallet/open"`
- Wallet Settle: `"wallet/settle"` or `"via POST to Settle Wallet"`

## Debug Rule
`logger.log()` only writes to HTML report — always add `print()` alongside it for real-time console visibility when debugging.

## TC_001 Test Data
- EAN: `9310072000282` (Arn Tim Tam 200g, $2.40)
- Card: `9353109614779` (Registered EDR, < 1000 pts)
- CSV: Banner=`SM`, TC_ID=`TC_001`, Iteration=`1`

## TC_002 Test Data
- EAN: `9310072000282` (same article as TC_001)
- Card: `9353109614656` (Registered EDR, > 2000 pts — with $10 redemption)
- Choice_offer: `$10` (OCR search string for the offer card)
- CSV: Banner=`SM`, TC_ID=`TC_002`, Iteration=`1`

## Loyalty Scan Paths — Two Components
| Scenario | Component | When |
|---|---|---|
| Sale mode (before PayButton) | `Scan_loyalty_salemode.py` | TC_001 |
| Tender prompt (after PayButton) | `Scan_loyalty_tenderprompt.py` | TC_002+ |

**`Scan_loyalty_tenderprompt`** clicks PayButton, waits for `CustomSkip` (loyalty prompt), scans card WITHOUT clicking CustomSkip, then waits for loyalty acceptance / choice offer popup.
**Do NOT call `move_to_tendermode()` before `scan_loyalty_tenderprompt()`** — it handles PayButton itself.

## EAN for all future TCs
All SCO test scenarios use EAN `9310072000282` (Arn Tim Tam 200g, $2.40). Only the EDR card number changes per TC.

## Exciting News Prompt — TC_003 to TC_006, TC_010, TC_011
Triggered when the customer's **earned points cross 2000** during the transaction. The prompt's text is **segment-dependent**:

| Card / Segment | OCR trigger phrase |
|---|---|
| Registered EDR (TC_003) | `"Exciting News! You've just earned $xx ..."` |
| SFC seg 105 (TC_004) | `"banked $xx into your Christmas savings"` |
| QFF seg 104 (TC_005) | `"converted xxx Qantas Points"` |
| Temporary (TC_006) — unregistered | `"Great news – you could save $xx off future shop"` |
| SFL seg 109 (TC_010) | `"YOUR SAVINGS ARE GROWING"` |
| AirNZ seg 110 (TC_011) | `"earned $xx Airpoints Dollars"` |

**Popup timing (CRITICAL for sale-mode TCs: TC_004, TC_005, TC_006):**
The Exciting News popup OR a Choice Offer screen fires **immediately after PayButton click**, blocking `Tender2` from appearing.
- `Move_to_tendermode.py` handles both inline after its 10s Tender2 wait times out:
  1. `_dismiss_exciting_news_popup_if_present()` — checks `Instructions` Text in PopupFrame, dismisses via `List1Button`
  2. `_skip_choice_offer_if_present()` — checks `ContainerButtonList`, skips via `SkipChoiceOfferPrompt`
- TC_006 (Temporary card `9344450008836`) confirmed to show a Choice Offer screen with `RewardTextBlock='Current Rewards Balance: $30'` and `LeadthruText='You have 1 discount to select from'`.
**Dismiss buttons (try in order):** `List1Button` (text="OK" — **confirmed correct for PopupFrame**), `List2Button` (text="Yes"), then fallbacks `ContinueButton`, `OK_Button`, `ASAOKButton`, `GenericOKButton`, `GenericButton`, `CustomSkip`, `SkipChoiceOfferPrompt`.
**Popup structure (from live TC_003 dump):** The prompt lives inside `PopupFrame` (Pane) with `Instructions` (Text) holding the message and `List1Button`/`List2Button` as the action buttons. Same `List#Button` pattern used by Reward Voucher flow — these are **generic list-action buttons** the SCO reuses for multiple popups.
**Behaviour:** Returns `False` (non-fatal) if no prompt detected — the prompt depends on the card's live point balance, which can drift between runs.

## TC_003 → TC_006 Test Data
| TC | Card | Segment | Loyalty scan path | Component sequence (after add_item) |
|---|---|---|---|---|
| TC_003 | `9353105847300` | Registered EDR | tender prompt | `scan_loyalty_tenderprompt` → `verify_exciting_news_prompt` → `complete_transaction` |
| TC_004 | `9355215896100` | SFC (105) | sale mode | `scan_loyalty_salemode` → `move_to_tendermode` → `verify_exciting_news_prompt` → `complete_transaction` |
| TC_005 | `9355215896056` | QFF (104) | sale mode | `scan_loyalty_salemode` → `move_to_tendermode` → `verify_exciting_news_prompt` → `complete_transaction` |
| TC_006 | `9344450008836` | Temporary (unregistered) | sale mode | `scan_loyalty_salemode` → `move_to_tendermode` → `verify_exciting_news_prompt` → `complete_transaction` |

All four use `Banner=SM`, `Iteration=1`, basket = 5× `9310072000282` (~$12). EE expectations: `expect_wallet_open=True`, `expect_wallet_settle=True`.

CSV setup: run `setup_TC003_to_TC006_csv_data.py` once to upsert all 4 rows into `\\10.80.19.218\d$\RTL_Pywinauto\SaleData.csv`.
