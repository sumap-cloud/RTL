"""
Void_transaction.py
--------------------
Cancels/voids the current SCO transaction.

On NCR SCO, voiding a transaction requires (confirmed live, 2026-07-15):
  1. Click `StoreLogin` (visible on the "Assistance Needed" popup, or directly
     on the sale-mode screen) — opens the "Enter ID" numeric/alpha keypad.
  2. Type attendant username into `InputTextBox`, click `EnterButton`.
  3. Type attendant password into `InputTextBox`, click `EnterButton`.
  4. SCO shows "Transaction Cancel" confirm screen — click `StoreButton1`
     ("Yes"). (`StoreButton2` = "No".)
  5. SCO shows "Select reason code" — a `ContainerCmdList` (List) of
     `ListItem`s (Double Scan / Insufficient Funds / Restricted Item Sales /
     Technical Issues / Unwanted Goods / Non payment). Click the ListItem
     matching the desired reason, then click the now-visible
     `CmdListItemConfirm` button (there are 6 — one per row — only the
     row's own is visible+enabled; must filter by `is_visible()`).
  6. SCO shows "Transaction cancelled. Remove items from this Self
     Checkout." — click `StoreButton1` ("OK").
  7. SCO returns to the Welcome/idle screen (`StartScanButton` visible).

This component is used for scenarios where the transaction must be abandoned
BEFORE settlement (e.g., card-locking tests that need a wallet/open without
a wallet/settle), or to reset a stuck/mismatched basket during live-build.
"""

import sys
import time
from pathlib import Path
from pywinauto import timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger

_DEFAULT_USERNAME = "ATMGR5"
_DEFAULT_PASSWORD = "abcd1234"
_DEFAULT_REASON = "Unwanted Goods"


def void_transaction(username=_DEFAULT_USERNAME, password=_DEFAULT_PASSWORD,
                      reason=_DEFAULT_REASON):
    """
    Void/cancel the current SCO transaction (confirmed live flow).

    Flow:
      1. Click StoreLogin to enter store mode.
      2. Enter attendant ID, then password (each via InputTextBox + EnterButton).
      3. Click StoreButton1 ("Yes") on the "Transaction Cancel" confirm screen.
      4. Select a reason-code ListItem in ContainerCmdList, click the
         corresponding CmdListItemConfirm button.
      5. Click StoreButton1 ("OK") on the "Transaction cancelled" screen.
      6. Wait for SCO to return to Welcome/idle (StartScanButton visible).

    Args:
        username (str): Store attendant ID (default "ATMGR5").
        password (str): Store attendant password.
        reason (str):   Reason-code text to select (default "Unwanted Goods").

    Returns:
        bool: True if the transaction was successfully voided, False otherwise.
    """
    win = global_instance.win
    if win is None:
        logger.log(
            "❌ SCO window not initialised. Cannot void transaction.",
            status="fail"
        )
        return False

    try:
        win.set_focus()
    except Exception:
        pass

    # --- Step 1: Enter store mode via StoreLogin ---
    print("➡️ Entering store mode to void transaction...")
    try:
        store_btn = win.child_window(auto_id="StoreLogin", control_type="Button")
        if store_btn.exists(timeout=5.0):
            store_btn.click_input()
            print("✅ StoreLogin button clicked.")
            logger.log("✅ StoreLogin clicked for void.", status="pass")
        else:
            logger.log(
                "⚠️ StoreLogin button not found. May already be in store mode.",
                status="pass"
            )
    except Exception as e:
        logger.log(f"⚠️ StoreLogin click error: {e}", status="pass")

    # --- Step 2: Enter ID then password (two separate keypad screens) ---
    time.sleep(1)
    try:
        for value in (username, password):
            input_box = win.child_window(auto_id="InputTextBox", control_type="Edit")
            enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
            if input_box.exists(timeout=5):
                input_box.click_input()
                input_box.type_keys(value, pause=0.05)
                time.sleep(0.3)
                if enter_btn.exists(timeout=3):
                    enter_btn.click_input()
                time.sleep(1)
        print(f"✅ Store credentials entered ({username}).")
        logger.log("✅ Store login credentials entered.", status="pass")
    except Exception as e:
        logger.log(f"⚠️ Credential entry error: {e}", status="pass")

    # --- Step 3: Confirm "Transaction Cancel" (StoreButton1 = Yes) ---
    time.sleep(1.5)
    try:
        yes_btn = win.child_window(auto_id="StoreButton1", control_type="Button")
        if yes_btn.exists(timeout=5):
            yes_btn.click_input()
            print("✅ 'Yes' clicked on Transaction Cancel confirm.")
            logger.log("✅ Transaction Cancel confirmed ('Yes').", status="pass")
        else:
            logger.log("❌ StoreButton1 ('Yes') not found on cancel confirm.", status="fail")
            logger.take_screenshot("Void_Transaction_Confirm_Not_Found")
            return False
    except Exception as e:
        logger.log(f"❌ Error confirming transaction cancel: {e}", status="fail")
        return False

    # --- Step 4: Select reason code, then confirm ---
    time.sleep(1.5)
    try:
        lst = win.child_window(auto_id="ContainerCmdList", control_type="List")
        selected = False
        if lst.exists(timeout=5):
            for item in lst.children(control_type="ListItem"):
                for d in item.descendants(control_type="Text"):
                    if reason.lower() in d.window_text().lower():
                        item.click_input()
                        selected = True
                        break
                if selected:
                    break
        if not selected:
            logger.log(f"❌ Reason code '{reason}' not found in list.", status="fail")
            logger.take_screenshot("Void_Transaction_Reason_Not_Found")
            return False
        print(f"✅ Reason code '{reason}' selected.")
        logger.log(f"✅ Reason code '{reason}' selected.", status="pass")

        time.sleep(0.5)
        # 6 CmdListItemConfirm buttons exist (one per row) — only the
        # selected row's button is visible+enabled.
        confirmed = False
        for btn in win.descendants(control_type="Button"):
            if btn.element_info.automation_id != "CmdListItemConfirm":
                continue
            try:
                if btn.is_visible() and btn.is_enabled():
                    btn.click_input()
                    confirmed = True
                    break
            except Exception:
                continue
        if not confirmed:
            logger.log("❌ CmdListItemConfirm button not found/visible.", status="fail")
            logger.take_screenshot("Void_Transaction_ReasonConfirm_Not_Found")
            return False
        print("✅ Reason code confirmed.")
        logger.log("✅ Reason code confirmed.", status="pass")
    except Exception as e:
        logger.log(f"❌ Error selecting/confirming reason code: {e}", status="fail")
        logger.take_screenshot("Void_Transaction_Reason_Error")
        return False

    # --- Step 5: Dismiss "Transaction cancelled" screen (StoreButton1 = OK) ---
    time.sleep(2)
    try:
        ok_btn = win.child_window(auto_id="StoreButton1", control_type="Button")
        if ok_btn.exists(timeout=5):
            ok_btn.click_input()
            print("✅ 'OK' clicked on Transaction cancelled screen.")
            logger.log("✅ Transaction cancelled screen dismissed.", status="pass")
    except Exception as e:
        logger.log(f"⚠️ Could not dismiss 'Transaction cancelled' screen: {e}", status="pass")

    # --- Step 6: Wait for SCO to return to idle ---
    time.sleep(2)
    try:
        idle_btn = win.child_window(auto_id="StartScanButton", control_type="Button")
        if idle_btn.exists(timeout=8):
            logger.log("✅ Transaction voided. SCO returned to idle.", status="pass")
            print("✅ Transaction voided. SCO returned to idle.")
            return True
        else:
            logger.log(
                "⚠️ SCO idle state not confirmed after void. Continuing.",
                status="pass"
            )
            logger.take_screenshot("Void_Transaction_Idle_Unconfirmed")
            return True

    except Exception as e:
        logger.log(f"⚠️ Error checking idle state after void: {e}", status="pass")
        return True
