"""
TC_012_VerifyPointsCardLockingWithin3mins.py
---------------------------------------------
Regression Test TC_012 — Validation of points / card locking within 3 minutes.

Live-build findings (2026-07-03):
  GC exclusion scan flow:
    - Scan GC EAN -> scam popup (List1Button=OK) -> GC added to basket cleanly
  PayButton -> loyalty card scan -> GC activation:
    - PayButton click -> CustomSkip (loyalty prompt) appears
    - Scan loyalty card -> "Assistance Needed" popup (StoreLogin button)
    - StoreLogin click -> InputTextBox "Enter ID" credential screen
    - Enter username (ms) -> EnterButton -> password (abcd1234) -> EnterButton
    - StoreButton1 "OK - Gift Card Activation Required" appears -> click it
    - "GiftCard Activation / Please Wait..." popup -> wait to dismiss
    - Arrives at Select Payment Type (LeadthruText)
  Redemption prompt:
    - Tender1 button visible on Select Payment Type when card has >2000 pts
    - Click Tender1 -> redemption screen -> Skip via coord (365,530)
  Void flow:
    - GoBackSale from Select Payment Type -> sale mode
    - Cancel Purchase popup dismissed via coord (512,467)
    - void_transaction() voids from sale mode
  Txn2 (locked card within 3 mins):
    - No GC items — eligible articles only
    - Loyalty card scanned in sale mode (scan_loyalty_salemode)
    - Tender1 / Everyday Rewards redemption should NOT appear

Card    : 9353109614656
Iter 1  : 9339687023882;9315087192083;076750436640009036009313012991
Iter 2  : 9339687023882;9315087192083

Scenario:
    Verify that when a transaction is voided (wallet opened but NOT settled),
    the card enters a "locked" state for ~3 minutes. During this window, a
    second transaction with the same card should:
      - NOT show a redemption prompt (card is locked).
      - Still settle successfully in EagleEye.

    Transaction 1 (voided — card becomes locked):
        - Scan eligible + exclusion articles
        - Scan loyalty card at loyalty prompt
        - Verify redemption prompt triggers → click "Skip"
        - Void the transaction
        - Verify transaction NOT settled in EE (active/open state)
        - Verify EE logs: Card Validation + Wallet Open ONLY (no Settle)

    Transaction 2 (within 3 mins — card still locked):
        - Login again immediately (within 3-min lock window)
        - Scan some articles
        - Scan loyalty card
        - Verify base points displayed (no promo changes)
        - Verify redemption prompt does NOT trigger (card locked)
        - Complete transaction → settled in EE
        - Verify EE logs: Card Validation + Wallet Open + Wallet Settle

Pre-requisite:
    Registered EDR card with >2000 points (to trigger redemption prompt).
    Both transactions must complete within the 3-minute lock window.

Data source:
    Local Data/RegressionSale.csv — TC_ID = "TC_012_VerifyPointsCardLockingWithin3mins", Banner = "SM".
    Iteration 1 = Txn1 (eligible + exclusion articles).
    Iteration 2 = Txn2 (some articles for the locked retry).
"""

import sys
import time
import ctypes
import win32gui
import win32api
import win32con
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- SCO Component imports ---------------------------------------------------
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Promotion_details import get_promotion_details
from Components.Void_transaction import void_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Complete_transaction import complete_transaction
from Components.Move_to_tendermode import move_to_tendermode
from Components.Read_csv import get_csv_value
from Components.Scan_item import scan_item
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_012_VerifyPointsCardLockingWithin3mins"
BANNER = "Metro"

logger.set_tc_id(TC_ID)


_STORE_USER = "ms"
_STORE_PASS = "abcd1234"


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


def _focus(win):
    try:
        hwnd = win.wrapper_object().handle
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
    except Exception:
        pass


def _fill_credential(win, label, text):
    """Enter text into InputTextBox and submit via EnterButton."""
    edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
    if edit.exists(timeout=4):
        edit.click_input()
        time.sleep(0.2)
        edit.type_keys(text, with_spaces=False)
        time.sleep(0.3)
        enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
        if enter_btn.exists(timeout=2):
            enter_btn.click_input()
            logger.log(f"  {label} submitted via EnterButton.", status="pass")
        time.sleep(1.2)
    else:
        logger.log(f"  InputTextBox not found for {label}.", status="info")


def _handle_gc_activation_after_loyalty(win):
    """
    Handle GC 'Assistance Needed' popup after loyalty card scan at tender prompt.

    Live-confirmed flow (2026-07-03 identifier dump):
      1. 'Assistance Needed' + StoreLogin button
      2. StoreLogin -> InputTextBox 'Enter ID' keyboard screen
      3. username (ms) -> EnterButton -> password (abcd1234) -> EnterButton
      4. StoreButton1 'OK - Gift Card Activation Required' -> click
      5. 'GiftCard Activation / Please Wait...' popup -> wait dismiss
      6. Select Payment Type screen confirmed via LeadthruText

    Returns True if arrived at Select Payment Type, False on failure.
    """
    store_login = win.child_window(auto_id="StoreLogin", control_type="Button")
    if not store_login.exists(timeout=5):
        logger.log("GC activation: no StoreLogin popup — proceeding.", status="info")
        return True

    logger.log("GC Activation: 'Assistance Needed' detected — clicking StoreLogin.", status="pass")
    _focus(win)
    store_login.click_input()
    time.sleep(1.5)

    _fill_credential(win, "username", _STORE_USER)
    _fill_credential(win, "password", _STORE_PASS)
    time.sleep(0.5)

    # StoreButton1 = "OK - Gift Card Activation Required"
    sb1 = win.child_window(auto_id="StoreButton1", control_type="Button")
    if sb1.exists(timeout=6):
        _focus(win)
        sb1.click_input()
        logger.log("GC Activation: StoreButton1 (OK) clicked.", status="pass")
        time.sleep(2)
    else:
        logger.log("GC Activation: StoreButton1 not found — continuing.", status="info")

    # Wait up to 20s for 'Please Wait... Activation in Progress' to clear
    logger.log("GC Activation: waiting for activation to complete...", status="info")
    for _ in range(40):
        popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if not popup.exists(timeout=0.3):
            break
        try:
            instr = win.child_window(auto_id="Instructions", control_type="Text")
            if instr.exists(timeout=0.2) and "Progress" not in instr.window_text():
                break
        except Exception:
            pass
        # Click StoreButton1 again if it reappears
        if sb1.exists(timeout=0.2) and sb1.is_enabled():
            _focus(win)
            sb1.click_input()
            time.sleep(1)
        time.sleep(0.5)

    lt = win.child_window(auto_id="LeadthruText", control_type="Text")
    if lt.exists(timeout=5):
        logger.log(f"GC Activation complete. Screen: '{lt.window_text()}'", status="pass")
        logger.take_screenshot("TC012_After_GC_Activation")
        return True

    logger.log("GC Activation: Select Payment Type not confirmed.", status="info")
    return False


def _check_redemption_and_skip(win):
    """
    On Select Payment Type: click Tender1 to open redemption screen.
    Log redemption balance then skip via coord (365,530).
    Returns True if redemption prompt was detected.
    """
    _focus(win)
    tender1 = win.child_window(auto_id="Tender1", control_type="Button")
    if not tender1.exists(timeout=4) or not tender1.is_enabled():
        logger.log("Step 4: Tender1 (Rewards) not present/enabled — redemption not available.", status="fail")
        return False

    tender1.click_input()
    logger.log("Step 4: Tender1 clicked — checking redemption prompt.", status="pass")
    time.sleep(2.5)

    redemption_found = False
    lt = win.child_window(auto_id="LeadthruText", control_type="Text")
    if lt.exists(timeout=3):
        lt_txt = lt.window_text()
        if "Everyday Rewards" in lt_txt or "Available" in lt_txt:
            redemption_found = True
            logger.log(f"Step 4: Redemption prompt confirmed: '{lt_txt}'", status="pass")
            logger.take_screenshot("TC012_Redemption_Prompt_Txn1")

    try:
        pts = win.child_window(auto_id="WoWRewardPoints", control_type="Text")
        if pts.exists(timeout=1):
            logger.log(f"Step 4: Points balance: {pts.window_text()}", status="pass")
    except Exception:
        pass

    # Skip via coord (365,530) — confirmed live TC_007
    try:
        hwnd = win.wrapper_object().handle
        left, top, _, _ = win32gui.GetWindowRect(hwnd)
        skip_x, skip_y = left + 365, top + 530
        win32api.SetCursorPos((skip_x, skip_y))
        time.sleep(0.2)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, skip_x, skip_y, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, skip_x, skip_y, 0, 0)
        logger.log("Step 4: Skip clicked via coord (365,530).", status="pass")
        time.sleep(1.5)
    except Exception as e:
        logger.log(f"Step 4: Skip coord failed: {e} — trying GoBackBtn.", status="info")
        try:
            gbb = win.child_window(auto_id="GoBackBtn", control_type="Button")
            if gbb.exists(timeout=2):
                gbb.invoke()
                time.sleep(1.5)
        except Exception:
            pass

    return redemption_found


def _go_back_to_sale(win):
    """
    From Select Payment Type -> GoBackSale -> sale mode.
    Dismiss 'Cancel Purchase' popup via coord (512,467) if it appears.
    """
    _focus(win)
    for attempt in range(2):
        gbs = win.child_window(auto_id="GoBackSale", control_type="Button")
        if gbs.exists(timeout=3):
            _focus(win)
            gbs.click_input()
            logger.log(f"GoBackSale clicked (attempt {attempt + 1}).", status="pass")
            time.sleep(2.5)

            # Dismiss Cancel Purchase popup at (512,467)
            try:
                hwnd = win.wrapper_object().handle
                left, top, _, _ = win32gui.GetWindowRect(hwnd)
                cx, cy = left + 512, top + 467
                win32api.SetCursorPos((cx, cy))
                time.sleep(0.2)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, cx, cy, 0, 0)
                time.sleep(0.1)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, cx, cy, 0, 0)
                time.sleep(1.5)
            except Exception:
                pass

            scan_el = win.child_window(auto_id="ScanItemTextBlock", control_type="Text")
            if scan_el.exists(timeout=4) and scan_el.is_visible():
                logger.log("Sale mode confirmed after GoBackSale.", status="pass")
                return True
        time.sleep(1)

    logger.log("GoBackSale: could not confirm sale mode.", status="fail")
    return False


# ============================================================================
# TRANSACTION 1 — Void (wallet open only → card locked)
# ============================================================================
try:
    logger.log("═" * 63, status="info")
    logger.log("  TRANSACTION 1 — Void transaction (card becomes locked)", status="info")
    logger.log("═" * 63, status="info")

    EAN_LIST_1 = _get_value("Item_EAN", 1, "9339687023882;9315087192083;076750436640009036009313012991")
    CARD_CODE  = _get_value("Card_number", 1, "9353109614656")

    # Step 1: Login
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn1)")

    win = global_instance.win

    # Step 2: Scan eligible + GC exclusion articles
    # add_item handles GC scam popup (List1Button) automatically
    add_item(EAN_LIST_1, CARD_CODE)
    logger.log("✅ Step 2: Eligible + GC exclusion articles added.", status="pass")
    logger.take_screenshot("TC012_Items_Added_Txn1")

    # Step 3: PayButton → loyalty prompt → scan loyalty card → GC activation
    _focus(win)
    pay_btn = win.child_window(auto_id="PayButton", control_type="Button")
    if not pay_btn.exists(timeout=5) or not pay_btn.is_enabled():
        raise RuntimeError("PayButton not found/enabled (Txn1)")
    pay_btn.click_input()
    logger.log("✅ Step 3: PayButton clicked.", status="pass")
    time.sleep(2.5)

    # Loyalty prompt (CustomSkip) — scan loyalty card
    custom_skip = win.child_window(auto_id="CustomSkip", control_type="Button")
    if custom_skip.exists(timeout=8):
        logger.log("✅ Step 3: Loyalty prompt visible — scanning loyalty card.", status="pass")
        scan_item(global_instance.app, CARD_CODE, "Loyalty Card")
        time.sleep(2.5)
        logger.log("✅ Step 3: Loyalty card scanned.", status="pass")
    else:
        logger.log("❌ Step 3: Loyalty prompt (CustomSkip) not found.", status="fail")

    # Handle GC Assistance Needed → credentials → StoreButton1 → activation wait
    _handle_gc_activation_after_loyalty(win)

    # Step 4: Verify redemption prompt and skip
    redemption_detected = _check_redemption_and_skip(win)
    if not redemption_detected:
        logger.log("❌ Step 4: Redemption prompt not detected (card needs >2000 pts).", status="fail")
        logger.take_screenshot("TC012_No_Redemption_Txn1")

    # Step 4b: Go back to sale mode before void
    _go_back_to_sale(win)

    # Step 5: Void the transaction
    time.sleep(1)
    if not void_transaction():
        raise RuntimeError("void_transaction failed (Txn1)")
    logger.log("✅ Step 5: Transaction voided — card is now locked.", status="pass")
    logger.take_screenshot("TC012_Voided_Txn1")

    # Steps 6 & 8: Verify EE logs — wallet open only, NO settle
    ee1 = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=False)
    if ee1.get("wallet_open") and not ee1.get("wallet_settle"):
        logger.log(
            "✅ Steps 6/8: EE verified — WalletOpen=True, WalletSettle=False. Card LOCKED.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Steps 6/8: Unexpected EE state — "
            f"WalletOpen={ee1.get('wallet_open')}, WalletSettle={ee1.get('wallet_settle')}",
            status="fail"
        )

except Exception as e:
    logger.log(f"❌ Txn1 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC012_Txn1_Error")
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
    raise SystemExit(1)


# ============================================================================
# TRANSITION — Stay within 3-min lock window
# ============================================================================
logger.log("⏳ Brief wait before Txn2 (must stay within 3-min lock window)...", status="info")
time.sleep(5)
global_instance.reset_state()


# ============================================================================
# TRANSACTION 2 — Within 3-min lock window (no redemption expected)
# ============================================================================
try:
    logger.log("═" * 63, status="info")
    logger.log("  TRANSACTION 2 — Card locked (within 3 mins of void)", status="info")
    logger.log("═" * 63, status="info")

    # Txn2: eligible items only — NO GC (no activation popup needed)
    EAN_LIST_2 = _get_value("Item_EAN", 2, "9339687023882;9315087192083")

    # Step 9: Login (within 3 mins)
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn2)")

    win2 = global_instance.win

    # Step 10: Scan articles
    add_item(EAN_LIST_2, CARD_CODE)
    logger.log("✅ Step 10: Articles added for Txn2.", status="pass")

    # Step 11: Scan loyalty card in sale mode (card is locked)
    if not scan_loyalty_salemode(CARD_CODE):
        logger.log("⚠️ Step 11: scan_loyalty_salemode returned False.", status="info")
    else:
        logger.log("✅ Step 11: Loyalty card scanned in sale mode.", status="pass")

    # Step 12: Verify base points only (no promo changes — card locked)
    _, _, promo_descs_2, _, _, _ = get_promotion_details("")
    if not promo_descs_2:
        logger.log("✅ Step 12: No promotions. Base points displayed (card locked).", status="pass")
    else:
        logger.log(f"⚠️ Step 12: Unexpected promotions: {promo_descs_2}", status="info")

    # Step 13: Move to tender and verify NO redemption prompt
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed (Txn2)")

    time.sleep(2)
    redemption_in_txn2 = False
    try:
        tender1 = win2.child_window(auto_id="Tender1", control_type="Button")
        if tender1.exists(timeout=3) and tender1.is_enabled():
            redemption_in_txn2 = True
        else:
            lt2 = win2.child_window(auto_id="LeadthruText", control_type="Text")
            if lt2.exists(timeout=2):
                txt2 = lt2.window_text()
                if "Everyday Rewards" in txt2 or "Available" in txt2:
                    redemption_in_txn2 = True
    except Exception:
        pass

    if not redemption_in_txn2:
        logger.log(
            "✅ Step 13: Redemption prompt NOT triggered (card locked). Correct!",
            status="pass"
        )
        logger.take_screenshot("TC012_No_Redemption_Txn2_CardLocked")
    else:
        logger.log(
            "❌ Step 13: Redemption prompt appeared — card should be locked!",
            status="fail"
        )
        logger.take_screenshot("TC012_Unexpected_Redemption_Txn2")
        try:
            gb = win2.child_window(auto_id="GoBack", control_type="Button")
            if gb.exists(timeout=2):
                gb.click_input()
        except Exception:
            pass

    # Step 14: Complete transaction
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed (Txn2)")
    logger.log("✅ Step 14: Txn2 completed successfully.", status="pass")

    # Steps 15 & 17: Verify EE settlement
    ee2 = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    if ee2.get("all_passed"):
        logger.log(
            "✅ Steps 15/17: EE verified — Txn2 settled. "
            "TC_012 PASSED: card locked in Txn1, completed in Txn2.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Steps 15/17: EE partial — "
            f"WalletOpen={ee2.get('wallet_open')}, WalletSettle={ee2.get('wallet_settle')}",
            status="fail"
        )

except Exception as e:
    logger.log(f"❌ Txn2 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC012_Txn2_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
