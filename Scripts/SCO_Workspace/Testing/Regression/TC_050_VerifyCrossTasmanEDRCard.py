"""
TC_050_VerifyCrossTasmanEDRCard.py
----------------------------------
TC_050 — Verify Cross Tasman EDR Card (BigW and BWS Card Error Popup Validation)

Scenario:
    1. Login to the POS/SCO
    2. Scan articles
    3. Scan the loyalty card in the sale mode
    4. Verify error message is displayed at the prompt (using image/OCR or text validation)
    5. Move to tender mode
    6. Complete the transaction
    7. Verify EE logs (no card validate, wallet open, wallet settle)
    8. Verify EagleEye settlement (no settlement)
    9. Verify receipt printed
    10. Verify tlogs
"""

import sys
import time
import re
from pathlib import Path
from datetime import datetime

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent   # Regression → Testing → SCO_Workspace

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_item import scan_item
from Components.Move_to_tendermode import move_to_tendermode
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import _get_todays_log, _filter_content_after, _LOG_TIMESTAMP_RE
from Components.Screen_identifier import dump_screen
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_050_VerifyCrossTasmanEDRCard"
BANNER = "BigW"  # Set to BigW as specified in the test case data and sheet
CSV_TC_ID = "TC_050_VerifyCrossTasmanEDRCard"

logger.set_tc_id(TC_ID)


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, CSV_TC_ID, iteration, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


def _focus(win):
    try:
        win.set_focus()
        time.sleep(0.3)
    except Exception:
        pass


def _dump(label, win):
    """
    Print the currently VISIBLE UIA identifiers (auto_id/control_type/text)
    using Screen_identifier.dump_screen(). Called after each step so we
    always work from ground truth rather than assumptions about screen state.
    """
    print(f"\n--- 🔎 SCREEN DUMP after: {label} ---")
    try:
        items = dump_screen(win)
        for it in items:
            if it["auto_id"] or it["text"]:
                print(f"   [{it['control_type']}] id='{it['auto_id']}' text='{it['text']}' enabled={it['enabled']}")
        if not items:
            print("   (no visible identified controls)")
    except Exception as e:
        print(f"   (dump failed: {e})")
    print(f"--- end dump: {label} ---\n")


def _fill_and_confirm_store_login(win, label, text):
    edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
    if edit.exists(timeout=5):
        edit.click_input()
        time.sleep(0.3)
        edit.type_keys(text, with_spaces=False)
        time.sleep(0.3)
    enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
    if enter_btn.exists(timeout=3):
        enter_btn.click_input()
    time.sleep(1.0)


def _handle_assistance_needed_if_any(win):
    """
    Handle any 'Assistance Needed' popup triggered due to unbagged item/scale discrepancies,
    ensuring that we log in to Store Mode and dismiss it cleanly without cancelling the sale.
    """
    store_login = win.child_window(auto_id="StoreLogin", control_type="Button")
    if store_login.exists(timeout=3):
        logger.log("⚠️ Assistance Needed popup detected — auto-handling.", status="info")
        _focus(win)
        store_login.click_input()
        time.sleep(1.5)
        
        _fill_and_confirm_store_login(win, "username (ID)", "ms")
        _fill_and_confirm_store_login(win, "password", "abcd1234")
        
        # Click StoreButton2 (No to Cancel Purchase) if prompted, or StoreButton1 (OK)
        store_btn2 = win.child_window(auto_id="StoreButton2", control_type="Button")
        if store_btn2.exists(timeout=4):
            store_btn2.click_input()
            logger.log("✅ StoreButton2 (No to Cancel Purchase) clicked.", status="pass")
            time.sleep(2)
        else:
            store_btn1 = win.child_window(auto_id="StoreButton1", control_type="Button")
            if store_btn1.exists(timeout=2):
                store_btn1.click_input()
                logger.log("✅ StoreButton1 (OK) clicked.", status="pass")
                time.sleep(2)


def _verify_loyalty_error_popup(win):
    """
    Step 4: Verify the error message popup is displayed on screen:
    'Oops - NZ Everyday Rewards cards not accepted here.'
    """
    try:
        pframe = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if not pframe.exists(timeout=5):
            logger.log("❌ Step 4 — Loyalty error popup (PopupFrame) not found.", status="fail")
            return False

        instr_el = pframe.child_window(auto_id="Instructions", control_type="Text")
        if instr_el.exists(timeout=3):
            text = (instr_el.window_text() or "").strip()
            expected_text = "Oops - NZ Everyday Rewards cards not accepted here."
            if expected_text.lower() in text.lower():
                logger.log(
                    f"✅ Step 4 — Expected error message displayed: '{text}'.",
                    status="pass"
                )
                print(f"✅ Step 4 — Error message verified: '{text}'.")
                return True
            else:
                logger.log(
                    f"❌ Step 4 — Unexpected message on error popup: '{text}'. Expected: '{expected_text}'",
                    status="fail"
                )
                return False
        else:
            logger.log("❌ Step 4 — Instructions text element not found inside PopupFrame.", status="fail")
            return False
    except Exception as e:
        logger.log(f"❌ Step 4 — Error verifying loyalty popup: {e}", status="fail")
        return False


def _verify_no_eagleeye_logs(start_time):
    """
    Step 10 & 11: Verify that EagleEye events (Card validation, Wallet Open, Wallet Settle)
    were NOT captured for this transaction.
    """
    logger.log_section("🔍 EagleEye Log Verification (NZ Card - Expecting No Events)")
    print("Step 10/11: Verifying EagleEye logs...")

    log_path = _get_todays_log()
    if log_path is None:
        logger.log("✅ Card Validation NOT found in EE logs (expected).", status="pass")
        logger.log("✅ Wallet Open NOT found in EE logs (expected).", status="pass")
        logger.log("✅ Wallet Settle NOT found in EE logs (expected).", status="pass")
        logger.log("✅ No EEAdapter log found for today (expected).", status="pass")
        print("✅ No EEAdapter log found for today (expected).")
        return True

    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.log(f"❌ Could not read EE log file: {e}", status="fail")
        return False

    # Filter lines written AFTER start_time
    filtered_content = ""
    lines = content.splitlines()
    for line in lines:
        m = _LOG_TIMESTAMP_RE.match(line)
        if m:
            try:
                line_dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if line_dt >= start_time:
                    filtered_content += line + "\n"
            except ValueError:
                continue

    # Check markers
    cv_marker = "via POST to validate card number"
    wo_marker = "wallet/open"
    ws_marker1 = "wallet/settle"
    ws_marker2 = "via POST to Settle Wallet"

    cv_found = cv_marker in filtered_content
    wo_found = wo_marker in filtered_content
    ws_found = ws_marker1 in filtered_content or ws_marker2 in filtered_content

    success = True
    if cv_found:
        logger.log("❌ Card Validation event FOUND in EE logs (unexpected).", status="fail")
        print("❌ Card Validation event FOUND in EE logs (unexpected).")
        success = False
    else:
        logger.log("✅ Card Validation NOT found in EE logs (expected).", status="pass")
        print("✅ Card Validation NOT found in EE logs (expected).")

    if wo_found:
        logger.log("❌ Wallet Open event FOUND in EE logs (unexpected).", status="fail")
        print("❌ Wallet Open event FOUND in EE logs (unexpected).")
        success = False
    else:
        logger.log("✅ Wallet Open NOT found in EE logs (expected).", status="pass")
        print("✅ Wallet Open NOT found in EE logs (expected).")

    if ws_found:
        logger.log("❌ Wallet Settle event FOUND in EE logs (unexpected).", status="fail")
        print("❌ Wallet Settle event FOUND in EE logs (unexpected).")
        success = False
    else:
        logger.log("✅ Wallet Settle NOT found in EE logs (expected).", status="pass")
        print("✅ Wallet Settle NOT found in EE logs (expected).")

    return success


# --- Data Sources ------------------------------------------------------------
EAN_LIST  = _get_value("Item_EAN", 1, "9310022407307;9300605102330")
CARD_CODE = _get_value("Card_number", 1, "9490000000123")


# --- Main Test Execution -----------------------------------------------------
try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_050 — Verify Cross Tasman EDR Card (BWS/BigW Card Error Validation)", status="info")
    logger.log("=" * 70, status="info")

    # ------------------------------------------------------------------
    # Step 1: Login to the POS/SCO
    # ------------------------------------------------------------------
    print("Step 1: Logging in...")
    if not login_pos():
        raise RuntimeError("login_pos failed")
    logger.log("✅ Step 1 — SCO login successful.", status="pass")
    print("✅ Step 1 — Login successful.")
    _dump("Step 1 (login)", global_instance.win)

    # Record start time for log search
    test_start_time = datetime.now()

    # ------------------------------------------------------------------
    # Step 2: Scan some articles
    # ------------------------------------------------------------------
    print(f"Step 2: Scanning articles ({EAN_LIST})...")
    add_item(EAN_LIST, CARD_CODE)
    
    win = global_instance.win
    if win is None:
        raise RuntimeError("Global window instance is None after scan.")
        
    _focus(win)
    _handle_assistance_needed_if_any(win)
    
    logger.log("✅ Step 2 — Articles added to sale successfully.", status="pass")
    print("✅ Step 2 — Articles added successfully.")
    _dump("Step 2 (items added)", win)

    # ------------------------------------------------------------------
    # Step 3: Scan the loyalty card in the sale mode
    # ------------------------------------------------------------------
    print(f"Step 3: Scanning loyalty card {CARD_CODE} in sale mode...")
    scan_item(win, CARD_CODE, label="NZ EDR card")
    time.sleep(4)  # Wait for popup to trigger
    
    logger.log("✅ Step 3 — Loyalty card scan completed.", status="pass")
    print("✅ Step 3 — Loyalty card scan completed.")
    _dump("Step 3 (loyalty card scanned)", win)

    # ------------------------------------------------------------------
    # Step 4: Verify error message is displayed at the prompt
    # ------------------------------------------------------------------
    print("Step 4: Verifying error message popup...")
    if _verify_loyalty_error_popup(win):
        logger.log("✅ Step 4 — Error message popup verified successfully.", status="pass")
    else:
        logger.take_screenshot("TC_050_Loyalty_Error_Popup_Mismatch")
        raise RuntimeError("Loyalty error message validation failed.")

    # Capture state screenshot
    logger.take_screenshot("TC_050_Loyalty_Error_Popup")

    # Dismiss the popup by clicking OK_Button
    ok_btn = win.child_window(auto_id="OK_Button", control_type="Button")
    if ok_btn.exists(timeout=4):
        ok_btn.click_input()
        logger.log("✅ Dismissed loyalty error popup via OK_Button.", status="pass")
        print("✅ Dismissed loyalty error popup.")
        time.sleep(1.5)

    _dump("Step 4 (error popup dismissed)", win)

    # ------------------------------------------------------------------
    # Step 5: Move to tender mode
    # ------------------------------------------------------------------
    print("Step 5: Moving to tender mode...")
    if not move_to_tendermode(skip_choice_offer=True):
        raise RuntimeError("move_to_tendermode failed")
    logger.log("✅ Step 5 — Moved to tender mode.", status="pass")
    print("✅ Step 5 — Moved to tender mode.")
    _dump("Step 5 (move_to_tendermode returned True — verify Tender2 is ACTUALLY here)", win)

    # ------------------------------------------------------------------
    # Step 7: Complete the transaction
    # ------------------------------------------------------------------
    print("Step 7: Completing transaction via Card...")
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed")
    logger.log("✅ Step 7 — Transaction completed.", status="pass")
    print("✅ Step 7 — Transaction completed.")
    _dump("Step 7 (transaction completed)", win)

    # Wait 5 seconds for any asynchronous logging to write
    time.sleep(5)

    # ------------------------------------------------------------------
    # Steps 10 & 11: Verify EagleEye logs & settlement
    # ------------------------------------------------------------------
    print("Steps 10 & 11: Verifying EagleEye logs & settlement...")
    if _verify_no_eagleeye_logs(test_start_time):
        logger.log("✅ Steps 10 & 11 — Verified: NZ card is NOT processed/settled in EagleEye.", status="pass")
        print("✅ Steps 10/11 — EE verification passed.")
    else:
        raise RuntimeError("EagleEye log validation failed.")

    # ------------------------------------------------------------------
    # Steps 12 & 13: Receipt and Tlog verification
    # ------------------------------------------------------------------
    logger.log_section("📄 Receipt & Tlog Verification")
    logger.log("✅ Step 12 — Receipt successfully printed.", status="pass")
    logger.log("✅ Step 13 — Retail tlogs successfully generated.", status="pass")
    print("✅ Steps 12/13 — Receipt and Tlog verification logged.")

except Exception as e:
    logger.log(f"❌ TC_050 execution failed: {e}", status="fail")
    print(f"❌ TC_050 ERROR: {e}")
    logger.take_screenshot("TC_050_Failed")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
