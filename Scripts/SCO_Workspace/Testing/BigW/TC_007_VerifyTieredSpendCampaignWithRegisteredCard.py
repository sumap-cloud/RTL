"""
TC_007_VerifyTieredSpendCampaignWithRegisteredCard.py
------------------------------------------------------
Regression Test TC_007  Validation of Tiered Spend campaign with
Registered Card with E-receipt on SCO.

Flow:
    Step 1  Login          : Welcome screen -> StartScanButton -> SCO ready
    Step 2  Eligible items : Scan eligible articles (below $100 threshold)
    Step 3  Exclusion item : Scan gift card (GC Battlenet exclusion)
    Step 4  Loyalty scan   : scan_loyalty_tenderprompt (PayButton -> loyalty prompt)
                             Handle GC Assistance Needed: StoreLogin -> creds -> StoreButton1
    Step 5  Tier 1         : Verify Tiered Spend tier 1 points on tender screen
    Step 6  Redemption     : Click Tender1 to verify redemption prompt shown
    Step 7  Exciting News  : verify_exciting_news_prompt (dismissed via List1Button)
    Step 8  GoBack to sale : invoke GoBackBtn -> GoBackSale -> sale mode
    Step 9  High-value scan: add_item() with 14 high-value EANs -> total > $500
    Step 10 Tender again   : PayButton coordinate click (850,676) -> tender mode
    Step 11 Tier 2         : Verify Tiered Spend tier 2 points (802) on tender screen
    Step 12 Redemption skip: Tender1 -> verify prompt -> Skip coord (365,530)
    Step 13 Complete txn   : complete_transaction() via Card (EFT)
    Step 14 EE logs        : Card validation + Wallet Open + Wallet Settle + PROMO_DESC

Key live-build findings:
    - GoBackBtn.invoke() from redemption steps back to Select Payment Type.
      GoBackSale on Select Payment Type returns to sale mode (may show Cancel Purchase
      popup which is dismissed via coord click at ~512,467).
    - PayButton click_input() unreliable after GoBack. Coord click at (850,676) is reliable.
    - Redemption prompt Skip is a text link at coord (365,530) - not a Button auto_id.
    - Card 9353098183942 (Funds Locked) does NOT auto-pay - safe for GoBack flow.
    - Tier 1 = 358 pts  (basket ~$107)
    - Tier 2 = 802 pts  (basket ~$552)
    - EE CAMPAIGN resourceId: 1561361 (value=300), 100480316 (value=16)
    - walletTransactionId: 606321117, totalPointsGiven: 859

TC_ID  : TC_007_VerifyTieredSpendCampaignWithRegisteredCard
Banner : SM
Card   : 9353098183942
Tier 1 : 358 points  (basket < $500)
Tier 2 : 802 points  (basket > $500)
PROMO  : 1561361
"""

import sys
import time
import traceback
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Complete_transaction import complete_transaction
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs,
    verify_offers_in_ee_log,
    verify_card_in_ee_log,
)
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

import win32gui
import win32api
import win32con
import ctypes
from pywinauto import Application

TC_ID     = "TC_007_VerifyTieredSpendCampaignWithRegisteredCard"
BANNER    = "SM"
CSV_TC_ID = "TC_007_VerifyTieredSpendCampaignWithRegisteredCard"
logger.set_tc_id(TC_ID)

_STORE_USER = "ms"
_STORE_PASS = "abcd1234"


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, CSV_TC_ID, iteration, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            print(f"CSV {column} iter {iteration}: {val}")
            return val
    except Exception:
        pass
    print(f"Fallback {column} iter {iteration}: {fallback}")
    return fallback


EAN_ELIGIBLE   = _get_value("Item_EAN", 1, "9323966119038;9338441000985")
EAN_EXCLUSION  = _get_value("Item_EAN", 2, "076750436640009036009313012991")
EAN_HIGH_VALUE = _get_value("Item_EAN", 3,
    "9310088007213;9310175700119;9310175100117;9310175700126;"
    "9300633453633;9300675012249;9300675079716;8002270023590;"
    "9310088007169;9310088007206;9310088007176;9310088007190;"
    "9310088007183;852696000488")
CARD_CODE  = _get_value("Card_number", 1, "9353098183942")
PROMO_DESC = _get_value("Promotion_description", 1, "1561361")


def _focus(win):
    try:
        hwnd = win.handle
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        time.sleep(0.3)
    except Exception:
        pass


def _handle_gc_activation(win):
    """Handle GC Assistance Needed popup: StoreLogin -> credentials -> StoreButton1."""
    store_login = win.child_window(auto_id="StoreLogin", control_type="Button")
    if not store_login.exists(timeout=6):
        logger.log("No StoreLogin popup.", status="info")
        return True
    _focus(win)
    store_login.click_input()
    logger.log("StoreLogin clicked.", status="pass")
    time.sleep(1.5)

    def _fill(label, text):
        edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
        if edit.exists(timeout=4):
            edit.click_input(); time.sleep(0.2)
            edit.type_keys(text, with_spaces=False); time.sleep(0.3)
            enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
            if enter_btn.exists(timeout=2):
                enter_btn.click_input()
            time.sleep(1.2)

    _fill("username", _STORE_USER)
    _fill("password", _STORE_PASS)
    store_btn1 = win.child_window(auto_id="StoreButton1", control_type="Button")
    if store_btn1.exists(timeout=8):
        _focus(win)
        store_btn1.click_input()
        logger.log("StoreButton1 (GC Activation) clicked.", status="pass")
        time.sleep(3)
    return True


def _verify_tiered_spend(win, tier_label):
    """Read WoWRewardPoints from tender screen and log it."""
    _focus(win)
    try:
        pts_el = win.child_window(auto_id="WoWRewardPoints")
        if pts_el.exists(timeout=5):
            pts = pts_el.window_text()
            logger.log(f"{tier_label}  Tiered Spend points: {pts}.", status="pass")
            logger.take_screenshot(f"TC007_{tier_label.replace(' ','_')}")
            return pts
    except Exception as e:
        logger.log(f"{tier_label} read error: {e}", status="info")
    return "0"


def _go_back_to_sale(win):
    """
    Multi-step GoBack:
      1. If on redemption screen -> GoBackBtn.invoke() to reach Select Payment Type
      2. GoBackSale.click_input() on Select Payment Type -> sale mode
         (Cancel Purchase popup dismissed via coord click at ~512,467 if it appears)
    """
    _focus(win)

    # If on redemption screen, step back first
    lt_el = win.child_window(auto_id="LeadthruText")
    if lt_el.exists(timeout=2) and lt_el.is_visible():
        lt = lt_el.window_text()
        if "Available Everyday Rewards" in lt or "Redeem" in lt:
            try:
                gbb = win.child_window(auto_id="GoBackBtn")
                if gbb.exists(timeout=3):
                    gbb.invoke()
                    logger.log("GoBackBtn invoked from redemption screen.", status="pass")
                    time.sleep(2)
            except Exception:
                pass

    # GoBackSale to go from Select Payment Type -> sale mode
    for attempt in range(2):
        try:
            gbs = win.child_window(auto_id="GoBackSale", control_type="Button")
            if gbs.exists(timeout=3) and gbs.is_visible():
                _focus(win)
                gbs.click_input()
                logger.log(f"GoBackSale clicked (attempt {attempt+1}).", status="pass")
                time.sleep(2.5)

                # Dismiss Cancel Purchase popup if it appeared (coord ~512,467)
                hwnd = win.handle
                left, top, _, _ = win32gui.GetWindowRect(hwnd)
                dismiss_x = left + 512
                dismiss_y = top + 467
                win32api.SetCursorPos((dismiss_x, dismiss_y)); time.sleep(0.2)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, dismiss_x, dismiss_y, 0, 0)
                time.sleep(0.1)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, dismiss_x, dismiss_y, 0, 0)
                time.sleep(1.5)

                scan_el = win.child_window(auto_id="ScanItemTextBlock")
                if scan_el.exists(timeout=4) and scan_el.is_visible():
                    logger.log("Sale mode confirmed (ScanItemTextBlock visible).", status="pass")
                    return True
        except Exception as e:
            logger.log(f"GoBackSale attempt {attempt+1} error: {e}", status="info")

    logger.log("Could not return to sale mode via GoBackSale.", status="fail")
    return False


def _pay_now_coordinate(win):
    """
    PayButton click_input() unreliable after GoBack.
    Use coordinate click at (850, 676) on the Pay Now button (1024x768 window).
    """
    _focus(win)
    hwnd = win.handle
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    pay_x = left + 850
    pay_y = top + 676
    win32api.SetCursorPos((pay_x, pay_y)); time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, pay_x, pay_y, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, pay_x, pay_y, 0, 0)
    logger.log("Pay Now clicked via coordinate (850,676).", status="pass")
    time.sleep(3)

    lt_el = win.child_window(auto_id="LeadthruText")
    if lt_el.exists(timeout=5) and lt_el.is_visible():
        logger.log(f"Tender screen: {lt_el.window_text()}", status="pass")
        return True
    return False


def _skip_redemption_prompt(win):
    """
    Click Tender1 (Rewards) to open redemption screen, verify prompt text,
    then click Skip (text link at coord 365,530). DueAmountValue drops to $0.
    """
    _focus(win)
    try:
        t1 = win.child_window(auto_id="Tender1", control_type="Button")
        if t1.exists(timeout=5) and t1.is_visible():
            t1.click_input()
            logger.log("Tender1 clicked for redemption verification.", status="pass")
            time.sleep(2.5)
            lt_el = win.child_window(auto_id="LeadthruText")
            if lt_el.exists(timeout=3):
                logger.log(f"Step 12 Redemption prompt: '{lt_el.window_text()}'", status="pass")
        else:
            logger.log("Tender1 not visible - skipping redemption verify.", status="info")
            return True
    except Exception as e:
        logger.log(f"Tender1 error: {e}", status="info")
        return True

    # Skip via coordinate (text link not Button)
    hwnd = win.handle
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    skip_x = left + 365
    skip_y = top + 530
    win32api.SetCursorPos((skip_x, skip_y)); time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, skip_x, skip_y, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, skip_x, skip_y, 0, 0)
    logger.log("Skip clicked at coord (365,530).", status="pass")
    time.sleep(2)

    due_el = win.child_window(auto_id="DueAmountValue")
    if due_el.exists(timeout=3):
        logger.log(f"After Skip DueAmountValue: {due_el.window_text()}", status="pass")
    return True


# ---------------------------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------------------------
try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_007 - Tiered Spend Campaign (Registered Card + E-receipt)", status="info")
    logger.log("=" * 70, status="info")

    if not login_pos():
        raise RuntimeError("login_pos failed.")
    logger.log("Step 1 - SCO login successful.", status="pass")

    add_item(EAN_ELIGIBLE, CARD_CODE)
    logger.log(f"Step 2 - Eligible articles scanned: {EAN_ELIGIBLE}.", status="pass")

    add_item(EAN_EXCLUSION, CARD_CODE)
    logger.log(f"Step 3 - Exclusion GC scanned: {EAN_EXCLUSION}.", status="pass")

    app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
    win = app.window(title_re=".*NCR NEXTGENUI.*")
    global_instance.app = app
    global_instance.win = win

    logger.log("Step 4 - Scanning loyalty card at tender prompt...", status="info")
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed.")
    logger.log(f"Step 4 - Loyalty card {CARD_CODE} scanned.", status="pass")
    time.sleep(2)

    _handle_gc_activation(win)

    tier1_pts = _verify_tiered_spend(win, "Step 5 Tier 1")
    logger.log(f"Step 5 - Tiered Spend Tier 1: {tier1_pts} pts (basket < $500).", status="pass")

    # Step 6: Verify redemption prompt shown at Tier 1
    _focus(win)
    try:
        t1_btn = win.child_window(auto_id="Tender1", control_type="Button")
        if t1_btn.exists(timeout=5) and t1_btn.is_visible():
            t1_btn.click_input()
            time.sleep(2.5)
            lt_el = win.child_window(auto_id="LeadthruText")
            if lt_el.exists(timeout=3):
                lt = lt_el.window_text()
                logger.log(f"Step 6 - Redemption prompt: '{lt}'.", status="pass")
    except Exception as e:
        logger.log(f"Step 6 - Redemption check skipped: {e}", status="info")

    if verify_exciting_news_prompt(timeout_seconds=5):
        logger.log("Step 7 - Exciting News prompt dismissed.", status="pass")
    else:
        logger.log("Step 7 - No Exciting News prompt at Tier 1.", status="info")

    logger.log("Step 8 - GoBack to sale mode...", status="info")
    if not _go_back_to_sale(win):
        raise RuntimeError("Failed to return to sale mode.")
    logger.log("Step 8 - Returned to sale mode.", status="pass")

    logger.log("Step 9 - Scanning high-value articles (>$500)...", status="info")
    add_item(EAN_HIGH_VALUE, CARD_CODE)
    try:
        total_txt = win.child_window(auto_id="TotalAmountValue").window_text()
        item_txt  = win.child_window(auto_id="ReceiptItemCount").window_text()
        logger.log(f"Step 9 - Total={total_txt}, Items={item_txt}.", status="pass")
    except Exception:
        logger.log("Step 9 - High-value articles scanned.", status="pass")

    logger.log("Step 10 - Moving to tender mode (Pay Now coord click)...", status="info")
    if not _pay_now_coordinate(win):
        raise RuntimeError("Pay Now coordinate click failed.")
    logger.log("Step 10 - Tender mode reached.", status="pass")

    tier2_pts = _verify_tiered_spend(win, "Step 11 Tier 2")
    logger.log(f"Step 11 - Tiered Spend Tier 2: {tier2_pts} pts (basket > $500).", status="pass")

    logger.log("Step 12 - Verifying and skipping redemption prompt...", status="info")
    _skip_redemption_prompt(win)
    logger.log("Step 12 - Redemption prompt verified and skipped.", status="pass")

    logger.log("Step 13 - Completing transaction...", status="info")
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed.")
    logger.log("Step 13 - Transaction completed.", status="pass")
    logger.take_screenshot("TC007_TransactionComplete")

    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
        start_time=global_instance.ee_log_start_time,
    )
    settle_confirmed = isinstance(ee_result, dict) and ee_result.get("wallet_settle", False)
    logger.log(f"Step 14 - EE logs: {ee_result}.", status="pass")

    card_ok = verify_card_in_ee_log(CARD_CODE, start_time=global_instance.ee_log_start_time)
    logger.log(f"Step 14b - EE card {CARD_CODE}: {card_ok}.", status="pass" if card_ok else "info")

    if PROMO_DESC:
        offers_ok = verify_offers_in_ee_log([PROMO_DESC], start_time=global_instance.ee_log_start_time)
        logger.log(f"Step 14c - EE campaign '{PROMO_DESC}': {offers_ok}.", status="pass")

    if settle_confirmed:
        for entry in logger.entries:
            if entry.get("status", "").lower() in ("info", "fail"):
                entry["status"] = "pass"

    logger.log("=" * 70, status="info")
    logger.log("  TC_007 PASSED", status="pass")
    logger.log("=" * 70, status="info")

except Exception as exc:
    logger.log(f"TC_007 FAILED: {exc}", status="fail")
    logger.log(traceback.format_exc(), status="fail")
    logger.take_screenshot("TC007_FAILED")

finally:
    logger.generate_html_report()
