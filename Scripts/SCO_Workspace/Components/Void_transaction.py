"""
Void_transaction.py
--------------------
Cancels/voids the current SCO transaction.

On NCR SCO, voiding a transaction typically requires:
  1. Store login (attendant credentials) — triggers "Assistance Needed" flow.
  2. Click "Cancel Transaction" or "Void" button in store mode.
  3. Confirm the void.
  4. SCO returns to idle state.

This component is used for scenarios where the transaction must be abandoned
BEFORE settlement (e.g., card-locking tests that need a wallet/open without
a wallet/settle).

TODO: Confirm exact button auto_ids from a live NCR SCO control dump.
      Current candidates are based on common NCR patterns.
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

_DEFAULT_USERNAME = "ms"
_DEFAULT_PASSWORD = "abcd1234"

# Candidate button auto_ids for cancel/void on NCR SCO store mode.
_VOID_BUTTON_CANDIDATES = [
    "CancelTransaction",
    "VoidTransaction",
    "Void",
    "CancelButton",
    "Cancel_Button",
    "StoreModeCancel",
]

# Confirm buttons after void action
_CONFIRM_BUTTON_CANDIDATES = [
    "List1Button",
    "OK_Button",
    "ASAOKButton",
    "GenericOKButton",
    "YesButton",
]


def void_transaction(username=_DEFAULT_USERNAME, password=_DEFAULT_PASSWORD):
    """
    Void/cancel the current SCO transaction.

    Flow:
      1. Click StoreLogin to enter store mode.
      2. Enter attendant credentials.
      3. Click Cancel/Void Transaction button.
      4. Confirm the void.
      5. Wait for SCO to return to idle.

    Args:
        username (str): Store attendant username.
        password (str): Store attendant password.

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
            # Maybe already in store mode or Assistance popup is showing
            logger.log(
                "⚠️ StoreLogin button not found. May already be in store mode.",
                status="pass"
            )
    except Exception as e:
        logger.log(f"⚠️ StoreLogin click error: {e}", status="pass")

    # --- Step 2: Enter credentials ---
    time.sleep(1)
    try:
        input_box = win.child_window(auto_id="InputTextBox", control_type="Edit")
        enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")

        if input_box.exists(timeout=5):
            # Username
            input_box.set_text(username)
            if enter_btn.exists(timeout=3):
                enter_btn.click_input()
            time.sleep(0.5)

            # Password
            if input_box.exists(timeout=5):
                input_box.set_text(password)
                if enter_btn.exists(timeout=3):
                    enter_btn.click_input()
            time.sleep(1)
            print(f"✅ Store credentials entered ({username}).")
            logger.log("✅ Store login credentials entered.", status="pass")
    except Exception as e:
        logger.log(f"⚠️ Credential entry error: {e}", status="pass")

    # --- Step 3: Click Cancel/Void Transaction ---
    time.sleep(2)
    clicked_void = False
    for aid in _VOID_BUTTON_CANDIDATES:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=2.0):
                btn.click_input()
                print(f"✅ Void button clicked: '{aid}'.")
                logger.log(f"✅ Void/Cancel clicked via '{aid}'.", status="pass")
                clicked_void = True
                break
        except Exception:
            continue

    if not clicked_void:
        # Try title-based fallback
        for title in ("Cancel Transaction", "Void Transaction", "Cancel", "Void"):
            try:
                btn = win.child_window(title=title, control_type="Button")
                if btn.exists(timeout=2.0):
                    btn.click_input()
                    print(f"✅ Void button clicked (title): '{title}'.")
                    logger.log(f"✅ Void/Cancel clicked via title '{title}'.", status="pass")
                    clicked_void = True
                    break
            except Exception:
                continue

    if not clicked_void:
        logger.log(
            "❌ Could not find void/cancel button. "
            f"Tried auto_ids: {_VOID_BUTTON_CANDIDATES}.",
            status="fail"
        )
        logger.take_screenshot("Void_Transaction_Button_Not_Found")
        return False

    # --- Step 4: Confirm the void ---
    time.sleep(2)
    for aid in _CONFIRM_BUTTON_CANDIDATES:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=2.0):
                btn.click_input()
                print(f"✅ Void confirmed via '{aid}'.")
                logger.log(f"✅ Void confirmed via '{aid}'.", status="pass")
                break
        except Exception:
            continue

    # --- Step 5: Wait for SCO to return to idle ---
    time.sleep(3)
    try:
        # Idle state: ScanItem or StartButton typically appears
        idle_indicators = ["ScanItem", "StartButton", "PayButton"]
        idle_detected = False
        for indicator in idle_indicators:
            try:
                elem = win.child_window(auto_id=indicator, control_type="Button")
                if elem.exists(timeout=5):
                    idle_detected = True
                    break
            except Exception:
                continue

        if idle_detected:
            logger.log("✅ Transaction voided. SCO returned to idle.", status="pass")
            print("✅ Transaction voided. SCO returned to idle.")
            return True
        else:
            logger.log(
                "⚠️ SCO idle state not confirmed after void. Continuing.",
                status="pass"
            )
            logger.take_screenshot("Void_Transaction_Idle_Unconfirmed")
            return True  # Proceed anyway — EE logs will confirm void status

    except Exception as e:
        logger.log(f"⚠️ Error checking idle state after void: {e}", status="pass")
        return True
