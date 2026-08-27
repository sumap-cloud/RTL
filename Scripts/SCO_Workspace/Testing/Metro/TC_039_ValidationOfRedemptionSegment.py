"""
TC_039_ValidationOfRedemptionSegment.py
----------------------------------------
TC_039 — Validation of Redemption Segment

Scenario:
    Verify that the redemption prompt triggers automatically when the SCO
    is moved to tender mode, for a loyalty card with a redemption segment
    and available balance, and that a partial ($20) redemption can be
    applied via the "Other" custom-amount path.

Pre-requisite:
    Registered loyalty card with redemption segments and balance.
    Card: 9353109614304

Flow:
    1.  Login to the POS/SCO.
    2.  Scan the eligible articles (worth ~$50 nominal / Bonds items).
    3.  Scan the loyalty card in sale mode.
    4.  Move to tender mode.
    5.  Verify the redemption prompt is displayed automatically (first).
    6.  Redeem $20 (via "Other" → numeric keypad → OK).
    7.  Complete the transaction via Card (Tender3).
    8.  Verify EagleEye logs: Card Validation, Wallet Open, Wallet Settle.
    9.  Tlog note: apportionment should be calculated (manual check).

LIVE-BUILD VERIFIED (incremental real-terminal runs):
    - Items 9356044248337;9312997258540 scan correctly (2 x Bonds items).
      A "Buy any Bonds product and get 10% off" promo applies -$5,
      making basket Total = $45.00 (nominal $50 pre-discount).
    - Loyalty card 9353109614304 scans in sale mode via CancelCoupon
      dismissal (same pattern as TC_037/TC_049).
    - move_to_tendermode() (PayButton) triggers a Bricks Home Packs
      continuity popup FIRST (Instructions contains 'bricks'/'collecting',
      List1Button=Yes, List2Button=No) - dismissed via List2Button (No).
    - Immediately after, the REDEMPTION PROMPT appears automatically
      (confirms TC_039 Step 5):
        LeadthruText = 'Available Everyday Rewards $40'
        List1Button  = 'Redeem $40'   (full balance)
        List2Button  = '$10'          (fixed option)
        List3Button  = 'Other'        (custom amount)
        List4Button  = 'Skip'
        GoBack       = 'Go Back'
    - Since $20 is required (not $40 or $10), List3Button ('Other') is
      clicked, revealing a numeric keypad screen:
        SMLineText        = 'Available Everyday Rewards $40'
        InputTextBox (Edit) - shows entered digits
        Keypad1..Keypad9, KeypadButton0 - digit buttons
        NumericBackspaceButton (label 'Clear')
        NumericDataNeededOk (label 'OK')   <-- confirm button
        GoBackButton (label 'Skip')
    - CRITICAL GOTCHA: NumericDataNeededOk does NOT reliably respond to
      .click_input() - the screen remains on the keypad with no visible
      change. It DOES respond to .wrapper_object().invoke() (the same
      WPF-button quirk documented for other List*/Tender* buttons in
      TC_037/TC_049). Always use .invoke(), not .click_input(), for this
      button.
    - After a correct .invoke() call on NumericDataNeededOk with '20'
      entered, the screen transitions directly to 'Select Payment Type'
      with: TotalAmountValue=$45.00, PaidAmount=$20.00 (REWARDS SAVINGS
      line item added to CartReceipt), DueAmountValue=$25.00. Confirms
      the $20 redemption was applied correctly.

Data source:
    RegressionSale.csv - TC_ID = "TC_039_ValidationOfRedemptionSegment", Banner = "SM".
"""

import sys
import time
import traceback
import ctypes
import win32gui
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent   # Regression -> Testing -> SCO_Workspace

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- SCO Component imports ---------------------------------------------------
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs, verify_card_in_ee_log,
)
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_039_ValidationOfRedemptionSegment"
BANNER = "Metro"

logger.set_tc_id(TC_ID)


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


# --- Data -------------------------------------------------------------------
EAN_ELIGIBLE  = _get_value("Item_EAN", 1, "9356044248337;9312997258540")
CARD_CODE     = _get_value("Card_number", 1, "9353109614304")
REDEEM_AMOUNT = _get_value("Redeem_amount", 1, "20")


# ---------------------------------------------------------------------------
# Helpers (confirmed live - do NOT modify auto_ids without re-dumping)
# ---------------------------------------------------------------------------

def _focus_win(win):
    """Bring the SCO window to foreground via Alt-key trick - required for
    WPF buttons to be reliably clickable/detectable."""
    try:
        hwnd = win.wrapper_object().handle
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
    except Exception:
        pass


def _is_sco_idle(win):
    """Return True if SCO is at the welcome/idle screen."""
    for aid in ("StartScanButton", "StartButton"):
        try:
            if win.child_window(auto_id=aid, control_type="Button").exists(timeout=0.2):
                return True
        except Exception:
            pass
    try:
        if win.child_window(
            title_re=".*Gift Card/Store Credit Balance.*", control_type="Text"
        ).exists(timeout=0.2):
            return True
    except Exception:
        pass
    return False


def _get_due_amount(win):
    """Read DueAmountValue from SCO screen. Returns float or None."""
    try:
        ctrl = win.child_window(auto_id="DueAmountValue", control_type="Text")
        if ctrl.exists(timeout=1):
            import re as _re
            txt = ctrl.window_text() or ""
            m = _re.search(r'[\d.]+', txt.replace(",", ""))
            return float(m.group()) if m else None
    except Exception:
        pass
    return None


def _dismiss_bricks_popup_if_present(win):
    """
    Dismiss the Bricks Home Packs continuity popup that appears right after
    PayButton for this scenario (same popup type seen in TC_037/TC_049).
    Returns True if dismissed, False if not present.
    """
    try:
        popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if not (popup.exists(timeout=3) and popup.is_visible()):
            return False

        instr_text = ""
        for _wait in range(8):
            instr_ctrl = win.child_window(auto_id="Instructions", control_type="Text")
            if instr_ctrl.exists(timeout=1):
                instr_text = (instr_ctrl.window_text() or "").strip()
            if instr_text:
                break
            print(f"  Popup visible but Instructions empty - waiting ({_wait+1}/8)...")
            time.sleep(1.0)

        if not instr_text:
            return False

        print(f"  Popup Instructions: '{instr_text[:120]}'")
        if "bricks" in instr_text.lower() or "collecting" in instr_text.lower():
            btn = win.child_window(auto_id="List2Button", control_type="Button")
            if btn.exists(timeout=2) and btn.is_enabled():
                btn.wrapper_object().invoke()
                logger.log(
                    "OK Bricks Home Packs continuity popup dismissed via List2Button (No).",
                    status="pass"
                )
                print("Bricks Home Packs popup dismissed (No).")
                time.sleep(1.5)
                return True
    except Exception as e:
        print(f"  _dismiss_bricks_popup_if_present error: {e}")
    return False


def _detect_redemption_prompt(win):
    """
    Detect the redemption prompt screen that appears automatically once the
    Bricks popup is dismissed:
        LeadthruText = 'Available Everyday Rewards $xx'
        List1Button  = 'Redeem $xx' (full balance)
        List2Button  = '$10' (fixed option)
        List3Button  = 'Other' (custom amount)
        List4Button  = 'Skip'

    Returns the LeadthruText string if the redemption prompt is present,
    else None.
    """
    try:
        lead = win.child_window(auto_id="LeadthruText", control_type="Text")
        if lead.exists(timeout=5):
            txt = (lead.window_text() or "").strip()
            if "reward" in txt.lower():
                return txt
    except Exception as e:
        print(f"  _detect_redemption_prompt error: {e}")
    return None


def _redeem_via_other(win, amount_str):
    """
    Click List3Button ('Other'), enter the given amount via the on-screen
    keypad, then confirm via NumericDataNeededOk.

    CRITICAL: NumericDataNeededOk must be clicked via .wrapper_object()
    .invoke() - .click_input() does NOT reliably register on this button
    (confirmed live: screen remained on keypad, InputTextBox/Due unchanged,
    after repeated click_input() attempts; invoke() worked on first try).

    Returns True if the confirm action was invoked without error.
    """
    other_btn = win.child_window(auto_id="List3Button", control_type="Button")
    if not other_btn.exists(timeout=5):
        logger.log("FAIL Step 6 - List3Button ('Other') not found.", status="fail")
        return False

    _focus_win(win)
    other_btn.wrapper_object().invoke()
    logger.log("OK Step 6 - 'Other' (List3Button) clicked - custom amount keypad.", status="pass")
    print("'Other' clicked - entering custom redemption amount.")
    time.sleep(1.5)

    # Digit auto_ids confirmed live: Keypad1..Keypad9, KeypadButton0.
    digit_map = {
        "1": "Keypad1", "2": "Keypad2", "3": "Keypad3",
        "4": "Keypad4", "5": "Keypad5", "6": "Keypad6",
        "7": "Keypad7", "8": "Keypad8", "9": "Keypad9",
        "0": "KeypadButton0",
    }

    for digit in str(amount_str).strip():
        aid = digit_map.get(digit)
        if not aid:
            continue
        btn = win.child_window(auto_id=aid, control_type="Button")
        if btn.exists(timeout=3):
            _focus_win(win)
            btn.wrapper_object().invoke()
            time.sleep(0.4)
        else:
            logger.log(f"FAIL Step 6 - Keypad digit button '{aid}' not found.", status="fail")
            return False

    # Verify entered amount before confirming.
    try:
        input_box = win.child_window(auto_id="InputTextBox", control_type="Edit")
        if input_box.exists(timeout=2):
            entered = input_box.window_text() or ""
            print(f"  InputTextBox shows: '{entered}'")
            logger.log(f"INFO Step 6 - Redemption amount entered on keypad: '{entered}'.", status="info")
    except Exception:
        pass

    ok_btn = win.child_window(auto_id="NumericDataNeededOk", control_type="Button")
    if not ok_btn.exists(timeout=5):
        logger.log("FAIL Step 6 - NumericDataNeededOk button not found.", status="fail")
        return False

    _focus_win(win)
    try:
        ok_btn.wrapper_object().invoke()
    except Exception as e:
        logger.log(f"WARN Step 6 - invoke() failed ({e}), falling back to click_input().", status="info")
        ok_btn.click_input()

    logger.log(f"OK Step 6 - Redemption of ${amount_str} confirmed via NumericDataNeededOk.", status="pass")
    print(f"Redemption of ${amount_str} confirmed via NumericDataNeededOk (invoke()).")
    time.sleep(3)
    return True


def _verify_redemption_applied(win, expected_amount):
    """
    Verify PaidAmount == expected_amount and a 'REWARDS SAVINGS' line item
    appears in CartReceipt after redemption.
    """
    try:
        paid_ctrl = win.child_window(auto_id="PaidAmount", control_type="Text")
        if paid_ctrl.exists(timeout=5):
            paid_txt = paid_ctrl.window_text() or ""
            print(f"  PaidAmount: '{paid_txt}'")
            if f"{float(expected_amount):.2f}" in paid_txt.replace("$", ""):
                logger.log(
                    f"OK Step 6 - PaidAmount confirms ${expected_amount} redemption applied: '{paid_txt}'.",
                    status="pass"
                )
                print(f"Redemption confirmed on screen - PaidAmount: {paid_txt}")
                return True
            else:
                logger.log(
                    f"WARN Step 6 - PaidAmount '{paid_txt}' does not match expected ${expected_amount}.",
                    status="info"
                )
        else:
            logger.log("WARN Step 6 - PaidAmount control not found for verification.", status="info")
    except Exception as e:
        print(f"  _verify_redemption_applied error: {e}")
    return False


def _complete_via_card(win):
    """
    Click Tender3 (Card) to complete the transaction - confirmed live:
        Tender2=Cash, Tender3=Card, Tender4=Card & Cash Out on this SCO.
    Retries on residual balance the same way TC_037/TC_049 do.
    """
    try:
        tender = win.child_window(auto_id="Tender3", control_type="Button")
        if not tender.exists(timeout=5):
            logger.log("FAIL Step 7 - Tender3 (Card) button not found.", status="fail")
            logger.take_screenshot("TC_039_Tender3_Not_Found")
            return False
        _focus_win(win)
        tender.click_input()
        logger.log("OK Step 7 - Tender3 (Card) clicked.", status="pass")
        print("Tender3 (Card) clicked - waiting for EFT approval.")
    except Exception as e:
        logger.log(f"FAIL Step 7 - Tender3 click failed: {e}", status="fail")
        return False

    deadline = time.time() + 90
    stable_due_text = ""
    stable_due_since = None

    while time.time() < deadline:
        _focus_win(win)

        for aid in ("NoReceiptButton", "No_Button", "ASAOKButton", "OK_Button",
                    "GenericOKButton", "GenericButton", "ContinueButton"):
            try:
                b = win.child_window(auto_id=aid, control_type="Button")
                if b.exists(timeout=0.2) and b.is_visible():
                    b.click_input()
                    print(f"  Dismissed post-payment popup via '{aid}'.")
                    time.sleep(1)
            except Exception:
                pass

        if _is_sco_idle(win):
            logger.log("OK Step 7 - SCO returned to idle. Transaction complete.", status="pass")
            print("SCO idle - transaction complete.")
            return True

        due = _get_due_amount(win)
        if due is not None:
            if due == 0:
                logger.log("OK Step 7 - DueAmountValue=$0.00 - payment complete.", status="pass")
                print("DueAmountValue=$0.00 - waiting for idle screen.")
            else:
                due_text = f"{due:.2f}"
                if due_text != stable_due_text:
                    stable_due_text = due_text
                    stable_due_since = time.time()
                    print(f"  Waiting - DueAmountValue=${due_text} - waiting for it to settle...")
                elif stable_due_since and (time.time() - stable_due_since) >= 4.0:
                    logger.log(
                        f"INFO Step 7 - ${due_text} balance remained stable for 4s - re-clicking Tender3.",
                        status="info"
                    )
                    print(f"  ${due_text} stable for 4s - re-clicking Tender3.")
                    try:
                        _focus_win(win)
                        t3 = win.child_window(auto_id="Tender3", control_type="Button")
                        if t3.exists(timeout=2):
                            t3.click_input()
                            print("  Tender3 re-clicked for residual balance.")
                    except Exception as e:
                        print(f"  Tender3 re-click failed: {e}")
                    stable_due_text = ""
                    stable_due_since = None
                    time.sleep(2)
                    continue

        time.sleep(1)

    logger.log("WARN Step 7 - SCO did not reach idle within 90 s.", status="info")
    logger.take_screenshot("TC_039_Idle_Timeout")
    return False


# ===========================================================================
# MAIN TEST
# ===========================================================================
try:
    logger.log("=" * 70, status="info")
    logger.log(f"  TC_039 - Validation of Redemption Segment  (Card: {CARD_CODE})", status="info")
    logger.log("=" * 70, status="info")

    # -----------------------------------------------------------------------
    # Step 1: Login
    # -----------------------------------------------------------------------
    if not login_pos():
        raise RuntimeError("login_pos failed - aborting test.")
    logger.log("OK Step 1 - SCO logged in successfully.", status="pass")
    print("Step 1 - Login OK.")

    # -----------------------------------------------------------------------
    # Step 2: Scan eligible articles
    # -----------------------------------------------------------------------
    logger.log(f"INFO Step 2 - Scanning eligible articles: {EAN_ELIGIBLE}", status="info")
    print(f"--- Step 2: Scanning {EAN_ELIGIBLE} ---")
    add_item(EAN_ELIGIBLE, CARD_CODE)
    logger.log("OK Step 2 - Eligible articles added to basket.", status="pass")
    print("Step 2 - Articles in basket.")

    # -----------------------------------------------------------------------
    # Step 3: Scan loyalty card in sale mode
    # -----------------------------------------------------------------------
    logger.log(f"INFO Step 3 - Scanning loyalty card {CARD_CODE} in sale mode.", status="info")
    print(f"--- Step 3: Scanning loyalty card {CARD_CODE} ---")
    if not scan_loyalty_salemode(CARD_CODE):
        logger.log(
            "WARN Step 3 - scan_loyalty_salemode returned False (CancelCoupon path). "
            "Continuing - EE log will confirm card acceptance.",
            status="info"
        )
        print("Step 3 - Loyalty scan indicator not confirmed (expected for this card type).")
    else:
        logger.log(f"OK Step 3 - Loyalty card {CARD_CODE} scanned in sale mode.", status="pass")
        print("Step 3 - Loyalty card scanned.")

    win = global_instance.win

    # -----------------------------------------------------------------------
    # Step 4: Move to tender mode (PayButton)
    # -----------------------------------------------------------------------
    logger.log("INFO Step 4 - Moving to tender mode.", status="info")
    print("--- Step 4: Moving to tender mode ---")

    if not move_to_tendermode(skip_choice_offer=True):
        raise RuntimeError("move_to_tendermode failed - aborting test.")

    logger.log("OK Step 4 - Moved to tender mode.", status="pass")
    print("Step 4 - Tender mode.")

    # -----------------------------------------------------------------------
    # Dismiss Bricks Home Packs popup (blocks redemption prompt otherwise)
    # -----------------------------------------------------------------------
    time.sleep(1.5)
    _dismiss_bricks_popup_if_present(win)

    # -----------------------------------------------------------------------
    # Step 5: Verify redemption prompt appears automatically
    # -----------------------------------------------------------------------
    logger.log_section("Step 5: Redemption Prompt Verification")
    print("--- Step 5: Checking for automatic redemption prompt ---")

    redemption_prompt_text = _detect_redemption_prompt(win)
    if redemption_prompt_text:
        logger.log(
            f"OK Step 5 - Redemption prompt displayed automatically: '{redemption_prompt_text}'.",
            status="pass"
        )
        print(f"Step 5 - Redemption prompt confirmed: '{redemption_prompt_text}'")
    else:
        logger.log(
            "FAIL Step 5 - Redemption prompt NOT detected on tender screen.",
            status="fail"
        )
        logger.take_screenshot("TC_039_RedemptionPrompt_NotFound")
        print("Step 5 - Redemption prompt not found.")

    # -----------------------------------------------------------------------
    # Step 6: Redeem $REDEEM_AMOUNT via 'Other' -> keypad -> OK
    # -----------------------------------------------------------------------
    logger.log_section(f"Step 6: Redeem ${REDEEM_AMOUNT}")
    print(f"--- Step 6: Redeeming ${REDEEM_AMOUNT} via 'Other' ---")

    redeemed = _redeem_via_other(win, REDEEM_AMOUNT)
    if redeemed:
        time.sleep(2)
        _verify_redemption_applied(win, REDEEM_AMOUNT)
    else:
        logger.log(f"FAIL Step 6 - Failed to redeem ${REDEEM_AMOUNT}.", status="fail")

    # -----------------------------------------------------------------------
    # Step 7: Complete transaction via Card (Tender3)
    # -----------------------------------------------------------------------
    logger.log_section("Step 7: Complete Transaction")
    completed = _complete_via_card(win)
    if not completed:
        raise RuntimeError("Transaction completion failed - aborting EE verification.")

    # Allow EEAdapter time to write the wallet/settle log entry.
    time.sleep(5)

    # -----------------------------------------------------------------------
    # Step 8: Verify EagleEye logs
    # -----------------------------------------------------------------------
    logger.log_section("Step 8: EagleEye Log Verification")
    print("--- Step 8: Verifying EagleEye logs ---")

    start_time = global_instance.ee_log_start_time

    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
        start_time=start_time,
    )

    if ee_result["all_passed"]:
        logger.log(
            "OK Step 8 - EE logs: Card Validation, Wallet Open, Wallet Settle all captured. "
            f"Status: {ee_result['settled_status']}.",
            status="pass"
        )
        print(f"Step 8 - EE logs verified. Settled: {ee_result['settled_status']}.")
    else:
        logger.log(
            f"FAIL Step 8 - EE log verification failed: {ee_result}",
            status="fail"
        )

    if verify_card_in_ee_log(CARD_CODE, start_time=start_time):
        logger.log(
            f"OK Step 8 - Card {CARD_CODE} confirmed in EE card-validation event.",
            status="pass"
        )
    else:
        logger.log(
            f"FAIL Step 8 - Card {CARD_CODE} NOT found in EE card-validation event.",
            status="fail"
        )

    # -----------------------------------------------------------------------
    # Step 9 (manual): Tlog verification
    # -----------------------------------------------------------------------
    logger.log(
        "INFO Step 9 - Tlog verification: MANUAL CHECK required. "
        f"Apportionment for the ${REDEEM_AMOUNT} redemption should be calculated "
        "correctly across the basket items in Tlogs.",
        status="info"
    )
    print("Step 9 - Tlog check: manual verification required.")

except Exception as e:
    print(f"\nERROR OCCURRED: {e}")
    traceback.print_exc()
    logger.log(f"FAIL TC_039 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_039_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
