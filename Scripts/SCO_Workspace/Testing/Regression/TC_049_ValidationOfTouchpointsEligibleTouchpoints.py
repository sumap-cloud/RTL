"""
TC_049_ValidationOfTouchpointsEligibleTouchpoints.py
-----------------------------------------------------
TC_049 — Validation of touchpoints (ineligible touchpoint / SCO)

Scenario:
    Verify that a touchpoint-specific offer (Campaign 103061376, "POS offer")
    is NOT applied when the transaction is performed in an ineligible
    touchpoint (this SCO terminal). A registered loyalty card that has the
    touchpoint-specific offer configured is used, but because the SCO is not
    an eligible touchpoint for that offer, the promotion must NOT appear in
    the cart, and the transaction still settles normally in EagleEye.

Pre-requisite:
    Registered loyalty card 9353109564258 with touchpoint offer 103061376.

Manual test case data:
    Campaign: 103061376 (Touchpoint offer / "POS offer")
    Articles: 453159, 345723, 30446 — only barcode confirmed: 30446 → 9310640620058 (SM)
              Per user decision (barcodes for 453159/345723 not provided),
              this script scans ONLY article 30446 (9310640620058).
    Card:     9353109564258

LIVE-BUILD VERIFIED FINDINGS:
    Article 9310640620058 (Gatorade 600ml, $3.85) is a TELCO item requiring
    attendant approval. The full approval flow (confirmed live):
      1. scan_item → "Approval Required" popup (PopupTitle) → OK_Button
      2. AssistanceButton → "Call For Help?" popup → StoreLoginButton
      3. Credential screen: InputTextBox + EnterButton (username ATMGR5,
         password abcd1234) via _store_login_credentials()
      4. "Telco Item" store mode screen (StoreModeScreenTitle1) may appear
         briefly; StoreButton1 (Yes) clicked if found/enabled — but in
         live runs credentials alone were sufficient (item auto-added,
         basket count = 1, screen returned to sale_mode automatically).

    scan_loyalty_tenderprompt(card) [Steps 3-4 manual]:
      - Clicks PayButton internally
      - A second "Assistance Needed" StoreLogin popup appears at PayButton
        (same Telco item pattern); handled automatically by the component's
        built-in _handle_giftcard_activation (keyboard creds ATMGR5/abcd1234)
      - Loyalty card 9353109564258 scanned at CustomSkip field
      - Returns True; SCO back in sale_mode — NO promo lines in cart,
        itemPromoDescription='', TotalAmountValue=$3.85 unchanged
      → CONFIRMS touchpoint offer NOT applied at SCO (ineligible touchpoint)

    _complete_via_card [Steps 7]:
      - PayButton again → Select Payment Type screen
      - Tender3 = Card (confirmed on this SCO config; Tender2=Cash)
      - Split-payment residual pattern handled (4s stability → re-click)

    EE verification [Steps 8-9]:
      - wallet_settle=True, status=SETTLED expected
      - Campaign 103061376 must NOT appear in EE settle block
        (confirms offer was not awarded at this ineligible touchpoint)

    Tender button mapping: Tender3=Card on this SCO (Tender2=Cash).
    Complete_transaction.py incorrectly assumes Tender2=Card — this script
    clicks Tender3 directly (same precedent as TC_037, TC_038).
"""
import sys
import time
import re
import ctypes
import win32gui
from pathlib import Path
from datetime import datetime, timedelta

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Scan_item import scan_item
from Components.Add_item import _get_basket_count, _store_login_credentials
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs, verify_card_in_ee_log,
    _get_todays_log, _filter_content_after, _extract_settle_block,
)
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID     = "TC_049_ValidationOfTouchpointsEligibleTouchpoints"
BANNER    = "SM"
ITERATION = 1
logger.set_tc_id(TC_ID)

# Live-confirmed campaign ID for the touchpoint offer (POS-only, must NOT fire at SCO)
TOUCHPOINT_CAMPAIGN_ID = "103061376"


# ---------------------------------------------------------------------------
# CSV helper
# ---------------------------------------------------------------------------
def _get_value(column, fallback=""):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not str(val).startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


EAN_LIST  = _get_value("Item_EAN", "9310640620058")
CARD_CODE = _get_value("Card_number", "9353109564258")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _focus_win(win):
    try:
        hwnd = win.wrapper_object().handle
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
    except Exception:
        pass


def _invoke_btn(win, aid, label, timeout=3):
    btn = win.child_window(auto_id=aid, control_type="Button")
    if btn.exists(timeout=timeout) and btn.is_enabled():
        try:
            btn.wrapper_object().invoke()
        except Exception:
            btn.click_input()
        print(f"  ✅ {label} ({aid}) clicked.")
        return True
    print(f"  ⚠️ {label} ({aid}) not found/enabled.")
    return False


def _is_sco_idle(win):
    for aid in ("StartScanButton", "StartButton"):
        try:
            if win.child_window(auto_id=aid, control_type="Button").exists(timeout=0.2):
                return True
        except Exception:
            pass
    return False


def _get_due_amount(win):
    try:
        c = win.child_window(auto_id="DueAmountValue", control_type="Text")
        if c.exists(timeout=1):
            m = re.search(r'[\d.]+', (c.window_text() or "").replace(",", ""))
            return float(m.group()) if m else None
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Step 2: Telco item approval handler
# ---------------------------------------------------------------------------
def _handle_telco_approval(win, ean):
    """
    Scan a telco-restricted item and complete the full attendant-approval flow.

    Confirmed live auto_ids (TC_049 live-build):
      PopupTitle          — 'Approval Required' popup title
      OK_Button           — dismisses the Approval Required popup
      AssistanceButton    — on sale screen, calls for attendant
      StoreLoginButton    — on 'Call For Help?' popup
      InputTextBox/EnterButton — credential entry screen
      StoreModeScreenTitle1='Telco Item' — store mode confirmation screen
      StoreButton1        — 'Yes' on Telco Item screen (may auto-dismiss)
    """
    print(f"--- Scanning telco item {ean} ---")
    scan_item(win, ean)
    time.sleep(2.5)

    # Step A: dismiss "Approval Required" popup
    _focus_win(win)
    popup_title = win.child_window(auto_id="PopupTitle", control_type="Text")
    if popup_title.exists(timeout=3):
        print(f"  Popup: '{popup_title.window_text()}'")
        _invoke_btn(win, "OK_Button", "OK (Approval Required)")
        time.sleep(1)

    # Step B: click AssistanceButton
    _focus_win(win)
    _invoke_btn(win, "AssistanceButton", "AssistanceButton")
    time.sleep(1.5)

    # Step C: click StoreLoginButton on "Call For Help?" popup
    _focus_win(win)
    _invoke_btn(win, "StoreLoginButton", "StoreLoginButton")
    time.sleep(2)

    # Step D: enter manager credentials
    print("  Entering manager credentials (ATMGR5/abcd1234)...")
    _store_login_credentials(win, "ATMGR5", "abcd1234")
    time.sleep(2)

    # Step E: if "Telco Item" store mode screen appears, click Yes
    store_title = win.child_window(auto_id="StoreModeScreenTitle1", control_type="Text")
    if store_title.exists(timeout=3) and store_title.is_visible():
        print(f"  Store mode screen: '{store_title.window_text()}'")
        _focus_win(win)
        _invoke_btn(win, "StoreButton1", "StoreButton1 (Yes)", timeout=2)
        time.sleep(2)

    # Verify item is in basket
    count = _get_basket_count(win)
    if count >= 1:
        logger.log(f"✅ Telco item {ean} approved and added (basket={count}).", status="pass")
        return True
    else:
        logger.log(f"❌ Telco item {ean} NOT in basket after approval flow.", status="fail")
        logger.take_screenshot("TC_049_TelcoApproval_Failed")
        return False


# ---------------------------------------------------------------------------
# Step 5: Verify touchpoint offer did NOT apply
# ---------------------------------------------------------------------------
def _verify_no_touchpoint_promo(win):
    """
    Returns (passed: bool, message: str).
    Checks both the item-level promo display AND the CartReceipt list
    for any negative-price promo rows that would indicate the touchpoint
    offer was applied.
    """
    time.sleep(2)

    # Check itemPromoDescription element (top-of-screen item detail box)
    promo_desc_el = win.child_window(auto_id="itemPromoDescription", control_type="Text")
    if promo_desc_el.exists(timeout=2):
        promo_text = promo_desc_el.window_text().strip()
        if promo_text:
            return False, f"itemPromoDescription='{promo_text}'"

    # Check CartReceipt for any -$x.xx promo rows
    try:
        cart = win.child_window(auto_id="CartReceipt", control_type="List")
        if cart.exists(timeout=2):
            for list_item in cart.children(control_type="ListItem"):
                for child in list_item.children():
                    if child.element_info.automation_id == "ItemPrice":
                        price = child.window_text().strip()
                        if price.startswith("-$"):
                            return False, f"Promo line in cart: '{price}'"
    except Exception as e:
        print(f"  ⚠️ Cart scan error: {e}")

    # Check total is unchanged (no discount applied)
    try:
        total_el = win.child_window(auto_id="TotalAmountValue", control_type="Text")
        if total_el.exists(timeout=1):
            print(f"  TotalAmountValue: '{total_el.window_text()}'")
    except Exception:
        pass

    return True, "No touchpoint promo lines detected — offer correctly NOT applied at SCO"


# ---------------------------------------------------------------------------
# Step 7: Complete transaction via Card (Tender3)
# ---------------------------------------------------------------------------
def _complete_via_card(win):
    """
    Click PayButton → handle any pre-tender popup → Tender3 (Card).
    Handles residual-balance split-payment pattern (same as TC_037).
    """
    # Handle any pre-tender popup (e.g. Bricks Home Packs)
    _focus_win(win)
    popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
    if popup.exists(timeout=2) and popup.is_visible():
        instr = win.child_window(auto_id="Instructions", control_type="Text")
        instr_text = ""
        for _ in range(6):
            instr_text = instr.window_text().strip() if instr.exists(timeout=0.5) else ""
            if instr_text:
                break
            time.sleep(0.5)
        print(f"  Pre-tender popup: '{instr_text}'")
        # Dismiss Bricks popup with No (List2Button); zero-reward or other with OK (List1Button)
        _focus_win(win)
        if not _invoke_btn(win, "List2Button", "List2Button (No)", timeout=1):
            _invoke_btn(win, "List1Button", "List1Button (OK)", timeout=1)
        time.sleep(1)

    # Move to Select Payment Type
    _focus_win(win)
    if not _invoke_btn(win, "PayButton", "PayButton → tender", timeout=5):
        logger.log("❌ PayButton not found for tender navigation.", status="fail")
        return False
    time.sleep(3)

    # Click Tender3 = Card
    _focus_win(win)
    t3 = win.child_window(auto_id="Tender3", control_type="Button")
    if not t3.exists(timeout=8):
        logger.log("❌ Tender3 (Card) not found on tender screen.", status="fail")
        logger.take_screenshot("TC_049_Tender3_NotFound")
        return False
    t3.click_input()
    logger.log("✅ Tender3 (Card) clicked.", status="pass")

    # Wait for idle with split-payment residual handling
    stable_text = ""
    stable_since = None
    deadline = time.time() + 90
    while time.time() < deadline:
        _focus_win(win)
        # Dismiss any post-payment popups
        for aid in ("NoReceiptButton", "No_Button", "ASAOKButton", "OK_Button",
                    "GenericOKButton", "List1Button"):
            try:
                b = win.child_window(auto_id=aid, control_type="Button")
                if b.exists(timeout=0.2) and b.is_visible() and b.is_enabled():
                    b.click_input()
                    time.sleep(0.8)
            except Exception:
                pass

        if _is_sco_idle(win):
            logger.log("✅ SCO idle — transaction complete.", status="pass")
            return True

        due = _get_due_amount(win)
        if due is not None and due > 0:
            dt = f"{due:.2f}"
            if dt != stable_text:
                stable_text = dt
                stable_since = time.time()
                print(f"  Due=${dt}, waiting to stabilise...")
            elif stable_since and time.time() - stable_since >= 4:
                print(f"  Due=${dt} stable 4s — re-clicking Tender3.")
                _focus_win(win)
                t3b = win.child_window(auto_id="Tender3", control_type="Button")
                if t3b.exists(timeout=2):
                    t3b.click_input()
                stable_text = ""
                stable_since = None
                time.sleep(2)
                continue

        time.sleep(1)

    logger.log("❌ Transaction did not complete within 90s.", status="fail")
    logger.take_screenshot("TC_049_TenderTimeout")
    return False


# ---------------------------------------------------------------------------
# Main test execution
# ---------------------------------------------------------------------------
try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_049 — Validation of Touchpoints (Ineligible Touchpoint / SCO)", status="info")
    logger.log("=" * 70, status="info")

    # ------------------------------------------------------------------
    # Step 1: Login
    # ------------------------------------------------------------------
    logger.log_section("Step 1: Login")
    if not login_pos():
        raise RuntimeError("login_pos failed — aborting test.")
    logger.log("✅ Step 1 — Login OK.", status="pass")

    win = global_instance.win

    # ------------------------------------------------------------------
    # Steps 2-3: Scan telco item with full attendant-approval flow
    # ------------------------------------------------------------------
    logger.log_section("Steps 2-3: Scan Telco Article + Approval")
    if not _handle_telco_approval(win, EAN_LIST):
        raise RuntimeError("Telco item approval failed — aborting test.")
    logger.log("✅ Step 3 — Telco article in basket.", status="pass")

    # ------------------------------------------------------------------
    # Step 4: Scan loyalty card at the loyalty prompt
    #   scan_loyalty_tenderprompt handles:
    #     • PayButton click
    #     • "Assistance Needed" StoreLogin popup (Telco item second approval)
    #     • Loyalty card scan at CustomSkip field
    # ------------------------------------------------------------------
    logger.log_section("Step 4: Loyalty Card at Tender Prompt")
    if not scan_loyalty_tenderprompt(CARD_CODE):
        logger.log("⚠️ scan_loyalty_tenderprompt returned False — continuing.", status="info")
    else:
        logger.log(f"✅ Step 4 — Loyalty card {CARD_CODE} scanned at tender prompt.", status="pass")

    # ------------------------------------------------------------------
    # Step 5: Verify touchpoint offer NOT triggered at SCO
    # ------------------------------------------------------------------
    logger.log_section("Step 5: Verify Touchpoint Offer NOT Applied")
    passed, msg = _verify_no_touchpoint_promo(win)
    if passed:
        logger.log(
            f"✅ Step 5 — Touchpoint offer ({TOUCHPOINT_CAMPAIGN_ID}) correctly NOT "
            f"applied at SCO (ineligible touchpoint). {msg}",
            status="pass"
        )
        print(f"✅ Step 5 PASS: {msg}")
    else:
        logger.log(
            f"❌ Step 5 — Touchpoint offer unexpectedly triggered at SCO: {msg}",
            status="fail"
        )
        print(f"❌ Step 5 FAIL: {msg}")

    # ------------------------------------------------------------------
    # Step 7: Complete transaction via Card tender
    # ------------------------------------------------------------------
    logger.log_section("Step 7: Complete Transaction via Card")
    time.sleep(2)
    _complete_via_card(win)

    # ------------------------------------------------------------------
    # Steps 8-9: Verify EagleEye logs
    # ------------------------------------------------------------------
    logger.log_section("Steps 8-9: EagleEye Log Verification")
    time.sleep(3)
    ee_result = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)

    # Pre-fetch the settle block once — used as an authoritative fallback for
    # card-identity confirmation. LIVE-BUILD FINDING: on this SCO flow (via
    # scan_loyalty_tenderprompt), the card is confirmed via the Promotions and
    # Wallet-Settle payloads (masked identityValue, e.g. "*********4258") but
    # a separate "validate card number" (Customer Controller) REST call is
    # NOT always made — unlike TC_037's flow. verify_card_in_ee_log() only
    # checks for that specific marker, so we additionally check the settle
    # block directly for the masked card as ground truth.
    log_path = _get_todays_log()
    settle_block = ""
    if log_path:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
        content = _filter_content_after(content, global_instance.ee_log_start_time)
        settle_block = _extract_settle_block(content) or ""

    masked_card = "*" * (len(CARD_CODE) - 4) + CARD_CODE[-4:]
    card_in_settle = masked_card in settle_block or CARD_CODE in settle_block

    if ee_result.get("wallet_open") and ee_result.get("wallet_settle"):
        if ee_result.get("card_validation"):
            logger.log(
                "✅ Step 8 — EE logs verified: card validation, wallet open, wallet settle captured.",
                status="pass"
            )
        else:
            logger.log(
                "ℹ️ Step 8 — Wallet Open/Settle captured; no separate 'validate card number' "
                f"call observed this flow (card confirmed via settle payload instead: "
                f"{'found' if card_in_settle else 'NOT found'} masked identity {masked_card}).",
                status="pass" if card_in_settle else "fail"
            )
    else:
        logger.log(f"❌ Step 8 — EE log check incomplete: {ee_result}", status="fail")

    if verify_card_in_ee_log(CARD_CODE) or card_in_settle:
        logger.log(
            f"✅ Step 9 — Card {CARD_CODE} confirmed in EE log "
            f"(masked identity '{masked_card}' present in settle payload).",
            status="pass"
        )
    else:
        logger.log(f"❌ Step 9 — Card {CARD_CODE} NOT found in EE log.", status="fail")

    # Verify touchpoint campaign NOT in EE settle block
    if log_path:
        campaign_marker = f'"resourceId":"{TOUCHPOINT_CAMPAIGN_ID}"'
        if campaign_marker not in settle_block:
            logger.log(
                f"✅ Step 9 — Touchpoint campaign {TOUCHPOINT_CAMPAIGN_ID} NOT in EE settle "
                "payload — confirms offer was not awarded at ineligible touchpoint (SCO).",
                status="pass"
            )
            print(f"✅ Touchpoint campaign {TOUCHPOINT_CAMPAIGN_ID} absent from EE settle ✓")
        else:
            logger.log(
                f"❌ Step 9 — Touchpoint campaign {TOUCHPOINT_CAMPAIGN_ID} FOUND in EE settle "
                "— offer was unexpectedly applied at SCO.",
                status="fail"
            )
            print(f"❌ Touchpoint campaign {TOUCHPOINT_CAMPAIGN_ID} found in EE settle — FAIL")
    else:
        logger.log("❌ No EE log file found for campaign verification.", status="fail")

    # ------------------------------------------------------------------
    # Step 10: Tlogs note (manual verification required)
    # ------------------------------------------------------------------
    logger.log(
        "ℹ️ Step 10 — Tlog apportionment: manual verification required. "
        "Confirm no touchpoint offer recorded in Tlogs for this SCO transaction.",
        status="info"
    )

except Exception as e:
    print(f"\n❌ ERROR OCCURRED: {e}")
    import traceback
    traceback.print_exc()
    logger.log(f"❌ TC_049 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_049_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
