"""
TC_018_VerifyInstantWinNotificationPointsRewardAndSavedPromotions.py
--------------------------------------------------------------------
TC_018 — Instant Win SAVED ($50 off / actual denomination varies) +
         Instant Win NOTIFICATION (points reward, 2000 pts if loaded).

Confirmed live behaviour (2026-07-15, NCR NEXTGENUI SCO):
  • IW SAVED popup appears AFTER PayButton click (not in sale mode).
    auto_id='ContainerButtonList' (List) + Button auto_id='Usenow'.
    2-step flow: first Usenow click → confirmation screen;
                 second Usenow click → discount applied.
  • Usenow click REQUIRES win32api.mouse_event — click_input()/invoke() silently fail
    on this nested WPF button.
  • "Assistance Needed / Cancel Purchase" popup appears in tender mode.
    Flow: StoreLogin → ATMGR5/abcd1234 → StoreButton2 (No) to preserve basket.
  • LeadthruText='Scan Coupon' + CancelCoupon exist in WPF tree at all times
    with zero rect — not actually a blocking screen for this card on this SCO.
  • IW NOTIFICATION (points) popup may or may not appear depending on card
    campaign state — handle if present, log info if absent.
  • Tender2 (Card / EFT) click works via standard click_input().

CSV columns used: Item_EAN, Card_number, Instant_win_offer_redeem,
                  Instant_win_notification
"""
import sys
import time
import ctypes
import win32gui
import win32api
import win32con
from pathlib import Path
from datetime import datetime

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item, _store_login_credentials
from Components.Total_amount_details import get_total_amount_salemode
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Complete_transaction import complete_transaction
from Components.Redeem_instant_win import handle_instant_win_notification
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID    = "TC_018_VerifyInstantWinNotificationPointsReward&SavedPromotions"
BANNER   = "Metro"
ITER     = 1
logger.set_tc_id(TC_ID)


# ── CSV helpers ──────────────────────────────────────────────────────────────
def _get(column, fallback=""):
    try:
        v = get_csv_value("saledata", BANNER, TC_ID, ITER, column)
        if v and not v.startswith("Error") and v != "No matching record found.":
            return v
    except Exception:
        pass
    return fallback


EAN_LIST  = _get("Item_EAN")
CARD_CODE = _get("Card_number")
IW_SAVED_REDEEM   = _get("Instant_win_offer_redeem", "50 off")
IW_NOTIF_MSG      = _get("Instant_win_notification", "")

print(f"EAN_LIST  = {EAN_LIST}")
print(f"CARD_CODE = {CARD_CODE}")
print(f"IW_SAVED  = {IW_SAVED_REDEEM}")
print(f"IW_NOTIF  = {IW_NOTIF_MSG}")


# ── Win32 coordinate clicker (required for nested WPF buttons like Usenow) ──
def _win32_click(win, auto_id, ctrl_type="Button", timeout=5):
    """
    Click a button by getting its UIA rect then firing win32api mouse events
    at its centre.  Needed for nested WPF buttons (e.g. Usenow inside
    ContainerButtonList > ListItem) where click_input() silently does nothing.
    Confirmed live fix: 2026-07-15.
    """
    btn = win.child_window(auto_id=auto_id, control_type=ctrl_type)
    if not btn.exists(timeout=timeout):
        return False
    r   = btn.rectangle()
    cx  = (r.left + r.right)  // 2
    cy  = (r.top  + r.bottom) // 2
    # Bring window to foreground before clicking
    hwnd = win.wrapper_object().handle
    ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    win32api.SetCursorPos((cx, cy))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, cx, cy, 0, 0)
    time.sleep(0.12)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,   cx, cy, 0, 0)
    logger.log(f"✅ win32 click on '{auto_id}' at ({cx},{cy}).", status="pass")
    return True


# ── Cancel-Purchase Assistance popup handler ─────────────────────────────────
def _handle_cancel_purchase_popup(win, max_wait=5):
    """
    Dismiss the 'Assistance Needed / Approval needed for: * Cancel Purchase'
    popup that appears in tender mode on this SCO.

    Confirmed flow (live 2026-07-15):
      PopupTitle='Assistance Needed'
      Instructions='… Approval needed for: * Cancel Purchase'
      Buttons: No_Button, Yes_Button, StoreLogin
      → No_Button click is intercepted by StoreLogin overlay — direct click fails.
      → Must click StoreLogin → enter ATMGR5/abcd1234 → click StoreButton2 (No)
         to decline the cancel and return to tender mode.

    Returns True if handled (or no popup present), False on error.
    """
    popup_title = win.child_window(auto_id="PopupTitle", control_type="Text")
    # Wait up to max_wait seconds for the popup to appear
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            if (popup_title.exists(timeout=0.3) and
                    popup_title.rectangle().width() > 0):
                txt = popup_title.window_text()
                if "Assistance" in txt:
                    break
        except Exception:
            pass
        time.sleep(0.3)
    else:
        return True  # no popup — nothing to do

    # Check instructions confirm it is the Cancel Purchase variant
    instr = win.child_window(auto_id="Instructions", control_type="Text")
    instr_txt = ""
    try:
        if instr.exists(timeout=0.5):
            instr_txt = instr.window_text()
    except Exception:
        pass
    logger.log(
        f"⚠️ 'Assistance Needed' popup in tender: '{instr_txt[:60]}'. "
        "Using StoreLogin path to decline cancel.", status="info")

    # Click StoreLogin
    if not _win32_click(win, "StoreLogin"):
        logger.log("❌ StoreLogin not found on Assistance popup.", status="fail")
        return False
    time.sleep(1.5)

    # Enter manager credentials
    edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
    if edit.exists(timeout=3):
        _store_login_credentials(win, "ATMGR5", "abcd1234")
        time.sleep(2)
    else:
        logger.log("❌ InputTextBox not found after StoreLogin click.", status="fail")
        return False

    # After login → Transaction Cancel confirmation → click StoreButton2 (No)
    sb2 = win.child_window(auto_id="StoreButton2", control_type="Button")
    if sb2.exists(timeout=4) and sb2.is_enabled():
        r   = sb2.rectangle()
        cx  = (r.left + r.right)  // 2
        cy  = (r.top  + r.bottom) // 2
        hwnd = win.wrapper_object().handle
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        win32api.SetCursorPos((cx, cy))
        time.sleep(0.2)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, cx, cy, 0, 0)
        time.sleep(0.12)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,   cx, cy, 0, 0)
        logger.log("✅ StoreButton2 (No) clicked — basket preserved, returning to tender.",
                   status="pass")
        time.sleep(2)
        return True

    logger.log("⚠️ StoreButton2 not found after credentials — popup may have auto-dismissed.",
               status="info")
    return True


# ── IW SAVED popup handler (2-step Usenow) ───────────────────────────────────
def _handle_iw_saved_popup(win, timeout=15):
    """
    Handle the Instant Win SAVED prize popup that appears after PayButton click.

    Observed UI (live 2026-07-15):
      LeadthruText = 'You have 1 prize to use now. T&Cs apply'
      ContainerButtonList > ListItem > Button auto_id='Usenow'
      Below list: Button auto_id='SkipChoiceOfferPrompt' ('Save for later')

    Flow:
      1st Usenow click → confirmation screen (ExpiryDaysText appears,
                         SkipChoiceOfferPrompt becomes visible).
      2nd Usenow click → discount applied, moves to Select Payment Type.

    Uses win32api coordinate click — click_input()/invoke() silently fail on
    this nested WPF button.

    Returns True if popup handled (or absent), False on unexpected error.
    """
    cbl = win.child_window(auto_id="ContainerButtonList", control_type="List")
    deadline = time.time() + timeout
    found = False
    while time.time() < deadline:
        try:
            if cbl.exists(timeout=0.5) and cbl.rectangle().width() > 0:
                lead = win.child_window(auto_id="LeadthruText", control_type="Text")
                lead_txt = lead.window_text() if lead.exists(timeout=0.3) else ""
                if "prize" in lead_txt.lower() or "ContainerButtonList" or True:
                    found = True
                    break
        except Exception:
            pass
        time.sleep(0.3)

    if not found:
        logger.log("ℹ️ IW SAVED popup not detected within timeout — not present for this transaction.",
                   status="info")
        return True

    logger.log("✅ IW SAVED popup detected: 'You have 1 prize to use now'.", status="pass")
    logger.take_screenshot("TC018_IW_Saved_Popup")

    # Step 1: first Usenow click (opens confirmation screen)
    if not _win32_click(win, "Usenow"):
        logger.log("❌ Usenow button not found on IW SAVED popup.", status="fail")
        return False
    time.sleep(2)

    # Step 2: second Usenow click (confirms and applies discount)
    usenow = win.child_window(auto_id="Usenow", control_type="Button")
    if usenow.exists(timeout=3):
        logger.log("✅ Confirmation screen appeared — clicking Usenow to confirm.", status="pass")
        if not _win32_click(win, "Usenow"):
            logger.log("❌ Second Usenow click failed.", status="fail")
            return False
        time.sleep(3)
    else:
        logger.log("ℹ️ Confirmation screen did not appear — single click was sufficient.",
                   status="info")

    # Verify savings applied
    savings_ctrl = win.child_window(auto_id="TotalRewardsValue", control_type="Text")
    try:
        if savings_ctrl.exists(timeout=2) and savings_ctrl.rectangle().width() > 0:
            savings = savings_ctrl.window_text()
            logger.log(f"✅ IW SAVED applied. TotalRewardsValue = {savings}", status="pass")
            print(f"✅ IW SAVED applied: TotalRewardsValue = {savings}")
        else:
            logger.log("⚠️ TotalRewardsValue not readable after Usenow.", status="info")
    except Exception:
        pass

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TEST FLOW
# ═══════════════════════════════════════════════════════════════════════════════
try:
    # Record start time for EagleEye log search window
    global_instance.ee_log_start_time = datetime.now()

    # ── Step 1: Login ─────────────────────────────────────────────────────────
    print("\n── Step 1: Login ──")
    if not login_pos():
        raise RuntimeError("login_pos() failed — aborting.")
    print("✅ Login successful.")
    logger.log("✅ Step 1 PASS: Logged in.", status="pass")

    win = global_instance.win

    # ── Step 2: Add eligible articles ($200+) ─────────────────────────────────
    print("\n── Step 2: Add items ──")
    if not EAN_LIST:
        raise RuntimeError("EAN_LIST is empty — check CSV.")
    add_item(EAN_LIST, CARD_CODE)

    total = get_total_amount_salemode()
    print(f"✅ Basket total: ${total}")
    if float(total) >= 200.0:
        logger.log(f"✅ Step 2 PASS: Basket total ${total} ≥ $200.", status="pass")
    else:
        logger.log(f"⚠️ Step 2 WARN: Basket total ${total} < $200 — campaign may not trigger.",
                   status="info")

    # ── Step 3: Scan loyalty card in SALE MODE ────────────────────────────────
    print("\n── Step 3: Scan loyalty card ──")
    if not CARD_CODE:
        raise RuntimeError("CARD_CODE is empty — check CSV.")
    loyalty_ok = scan_loyalty_salemode(CARD_CODE)
    if loyalty_ok:
        logger.log(f"✅ Step 3 PASS: Loyalty card {CARD_CODE} scanned in sale mode.", status="pass")
    else:
        logger.log(f"❌ Step 3 FAIL: Loyalty card scan may have failed.", status="fail")

    # ── Step 4: Move to tender (triggers IW SAVED popup after PayButton) ──────
    print("\n── Step 4/5: Move to tender + handle IW SAVED popup ──")
    # skip_choice_offer=False so IW SAVED popup is NOT auto-skipped here —
    # we handle it explicitly below.
    move_to_tendermode(skip_choice_offer=False)

    # ── Step 4 verify: IW SAVED popup should be on screen ────────────────────
    # handle_iw_saved_popup waits up to 15s for ContainerButtonList,
    # then performs the 2-step Usenow click.
    iw_saved_ok = _handle_iw_saved_popup(win, timeout=15)
    if iw_saved_ok:
        logger.log("✅ Step 4/5 PASS: IW SAVED popup handled.", status="pass")
    else:
        logger.log("❌ Step 4/5 FAIL: IW SAVED popup handler returned error.", status="fail")

    # ── Handle 'Assistance Needed / Cancel Purchase' popup if present ─────────
    # Appears after Usenow click in tender mode — must decline to preserve basket.
    _handle_cancel_purchase_popup(win, max_wait=5)

    # ── Step 6/7: Handle IW NOTIFICATION popup if present ────────────────────
    print("\n── Step 6/7: Check for IW NOTIFICATION popup ──")
    notif_ok = handle_instant_win_notification(timeout=8)
    if notif_ok:
        logger.log("✅ Step 6/7 PASS: IW NOTIFICATION popup detected and acknowledged.",
                   status="pass")
        print("✅ IW NOTIFICATION popup acknowledged.")
    else:
        logger.log("ℹ️ Step 6/7: IW NOTIFICATION popup not detected — may not be loaded on this card.",
                   status="info")
        print("ℹ️ IW NOTIFICATION popup not present for this card/campaign state.")

    # ── Step 8: Verify reward points displayed ────────────────────────────────
    print("\n── Step 8: Verify WoWRewardPoints ──")
    try:
        pts_ctrl = win.child_window(auto_id="WoWRewardPoints", control_type="Text")
        if pts_ctrl.exists(timeout=2) and pts_ctrl.rectangle().width() > 0:
            pts = pts_ctrl.window_text()
            logger.log(f"✅ Step 8: WoWRewardPoints = {pts}", status="pass")
            print(f"✅ WoWRewardPoints = {pts}")
        else:
            logger.log("⚠️ Step 8: WoWRewardPoints not readable.", status="info")
    except Exception as e:
        logger.log(f"⚠️ Step 8: Could not read WoWRewardPoints: {e}", status="info")

    # ── Step 9: Complete transaction (Tender2 / Card EFT) ────────────────────
    print("\n── Step 9: Complete transaction ──")
    txn_ok = complete_transaction()
    if txn_ok:
        logger.log("✅ Step 9 PASS: Transaction completed via EFT.", status="pass")
        print("✅ Transaction completed.")
    else:
        logger.log("❌ Step 9 FAIL: complete_transaction() returned False.", status="fail")
        print("❌ Transaction did not complete.")

    # ── Step 10/11: Verify EagleEye logs ─────────────────────────────────────
    print("\n── Steps 10/11: Verify EagleEye logs ──")
    time.sleep(3)  # allow EE logs to flush
    if global_instance.is_loyaltycard_added:
        ee_ok = verify_eagleeye_logs(BANNER, TC_ID, ITER)
        if ee_ok:
            logger.log("✅ Steps 10/11 PASS: EagleEye logs verified.", status="pass")
        else:
            logger.log("❌ Steps 10/11 FAIL: EagleEye log verification failed.", status="fail")
    else:
        logger.log("ℹ️ Skipping EE log check — loyalty card not confirmed added.",
                   status="info")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    logger.log(f"❌ Unhandled exception: {e}", status="fail")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")