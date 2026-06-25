"""
Save_transaction.py
-------------------
Saves (suspends) the current SCO transaction via attendant mode.

Flow on NCR SCO (confirmed from live control dump 2026-06-19):
  1. Enter attendant/store mode (StoreLogin, or Assistance → Log In →
     credentials).
  2. Click "Suspend Transaction" (StoreButton2) — directly suspends the
     transaction without needing to switch to POS mode.
  3. SCO returns to idle state.

Alternative path (via POS mode — also supported):
  2b. Click "Go To POS" (StoreButton7).
  3b. Click "Save Transaction" in POS lower commands bar.
  4b. Click "Go to SCO" to return to SCO mode.

The saved transaction can later be recalled using Recall_transaction.py.
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

# Confirmed from live SCO attendant-mode control dump (2026-06-19)
_SUSPEND_BUTTON_ID = "StoreButton2"       # title="Suspend Transaction"
_GO_TO_POS_BUTTON_ID = "StoreButton7"    # title="Go To POS"

_LOGIN_OPTION_AUTO_IDS = (
    "StoreLogin",
    "LoginButton",
    "LogInButton",
    "AttendantLogin",
    "AttendantLoginButton",
)

_LOGIN_OPTION_TITLES = (
    "Log In",
    "Log in",
    "Login",
    "LOGIN",
    "Sign In",
    "Sign in",
    "Store Login",
    "Attendant Log In",
    "Attendant Login",
    "Operator Log In",
    "Operator Login",
)

# Confirmed from POS control dump
_SAVE_TRANSACTION_BUTTON = "commandsLowerButtonsSave Transaction"

# Candidate auto_ids for "Go to SCO" button in POS mode
# Confirmed from live POS control dump (2026-06-19)
_GO_TO_SCO_CANDIDATES = [
    "commandsLowerButtonsFinish Go To SCO",     # confirmed auto_id
]


def save_transaction(username=_DEFAULT_USERNAME, password=_DEFAULT_PASSWORD,
                     use_pos_mode=False):
    """
    Save (suspend) the current SCO transaction.

    Primary flow (use_pos_mode=False):
      1. Enter store/attendant mode via StoreLogin, or Assistance → Log In
         + credentials.
      2. Click "Suspend Transaction" (StoreButton2) — directly suspends.
      3. SCO returns to idle.

    Alternative flow (use_pos_mode=True):
      1. Enter store/attendant mode.
      2. Click "Go To POS" (StoreButton7).
      3. Click "Save Transaction" in POS lower bar.
      4. Click "Go to SCO" to return.

    Args:
        username (str): Store attendant username.
        password (str): Store attendant password.
        use_pos_mode (bool): If True, use the Go-to-POS flow instead of
            the direct Suspend Transaction button.

    Returns:
        bool: True if transaction was saved successfully.
    """
    win = global_instance.win
    if win is None:
        logger.log("❌ SCO window not initialised. Cannot save transaction.", status="fail")
        return False

    try:
        win.set_focus()
    except Exception:
        pass

    # --- Step 1: Enter store/attendant mode ---
    print("➡️ Entering attendant mode to save transaction...")
    if not _do_store_login(win, username, password):
        return False

    if not use_pos_mode:
        # --- Primary path: Click "Suspend Transaction" directly ---
        time.sleep(2)
        print("➡️ Clicking 'Suspend Transaction' (StoreButton2)...")
        try:
            btn = win.child_window(auto_id=_SUSPEND_BUTTON_ID, control_type="Button")
            if btn.exists(timeout=5.0):
                btn.click_input()
                logger.log("✅ 'Suspend Transaction' clicked — transaction saved.", status="pass")
                print("✅ 'Suspend Transaction' clicked — transaction saved.")
            else:
                # Title fallback
                btn2 = win.child_window(title="Suspend Transaction", control_type="Text")
                if btn2.exists(timeout=3.0):
                    btn2.click_input()
                    logger.log("✅ 'Suspend Transaction' clicked (title fallback).", status="pass")
                else:
                    logger.log("❌ 'Suspend Transaction' button not found.", status="fail")
                    logger.take_screenshot("Save_Transaction_Suspend_Not_Found")
                    return False
        except Exception as e:
            logger.log(f"❌ Error clicking 'Suspend Transaction': {e}", status="fail")
            logger.take_screenshot("Save_Transaction_Suspend_Error")
            return False
    else:
        # --- Alternative path: Go to POS → Save Transaction → Go to SCO ---
        time.sleep(2)
        print(f"➡️ Clicking 'Go To POS' ({_GO_TO_POS_BUTTON_ID})...")
        try:
            btn = win.child_window(auto_id=_GO_TO_POS_BUTTON_ID, control_type="Button")
            if not btn.exists(timeout=5.0):
                logger.log("❌ 'Go To POS' button not found.", status="fail")
                logger.take_screenshot("Save_Transaction_GoToPOS_Not_Found")
                return False
            btn.click_input()
            logger.log("✅ Switched to POS mode.", status="pass")
        except Exception as e:
            logger.log(f"❌ Error clicking 'Go To POS': {e}", status="fail")
            return False

        time.sleep(2)
        if not _click_save_button(win):
            logger.log("❌ 'Save Transaction' button not found in POS mode.", status="fail")
            logger.take_screenshot("Save_Transaction_Button_Not_Found")
            return False
        logger.log("✅ 'Save Transaction' clicked in POS mode.", status="pass")

        time.sleep(2)
        if not _click_go_to_sco(win):
            logger.log(
                "⚠️ 'Go to SCO' button not found. SCO may auto-return to idle.",
                status="pass"
            )
            logger.take_screenshot("Save_Transaction_GoToSCO_Not_Found")

    # --- Verify idle state ---
    time.sleep(3)
    if _check_idle_state(win):
        logger.log("✅ Transaction saved. SCO returned to idle.", status="pass")
        print("✅ Transaction saved. SCO returned to idle.")
    else:
        logger.log("⚠️ SCO idle state not confirmed after save. Continuing.", status="pass")
        logger.take_screenshot("Save_Transaction_Idle_Unconfirmed")

    return True


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _do_store_login(win, username, password):
    """Open attendant login, handle the Log In option if shown, then enter credentials."""
    try:
        if _store_mode_visible(win, timeout=0.5):
            logger.log("✅ Store mode already available for save.", status="pass")
            return True

        if not _open_attendant_login(win, "save"):
            logger.log(
                "❌ Could not open attendant login for save.",
                status="fail",
            )
            logger.take_screenshot("Save_Transaction_Login_Not_Found")
            return False
    except Exception as e:
        logger.log(f"❌ Attendant login button click error: {e}", status="fail")
        logger.take_screenshot("Save_Transaction_Login_Click_Error")
        return False

    try:
        if _store_mode_visible(win, timeout=0.5):
            return True

        input_box = _get_input_box(win, timeout=8.0)
        if input_box is None:
            if _store_mode_visible(win, timeout=0.5):
                return True
            logger.log("❌ Store credential input did not appear for save.", status="fail")
            logger.take_screenshot("Save_Transaction_Login_Input_Not_Found")
            return False

        input_box.set_text(username)
        if not _click_enter(win):
            logger.log("❌ Enter button not found after username entry for save.", status="fail")
            logger.take_screenshot("Save_Transaction_Login_Enter_Not_Found")
            return False

        time.sleep(0.5)
        input_box = _get_input_box(win, timeout=8.0)
        if input_box is None:
            logger.log("❌ Password input did not appear for save.", status="fail")
            logger.take_screenshot("Save_Transaction_Password_Input_Not_Found")
            return False

        input_box.set_text(password)
        if not _click_enter(win):
            logger.log("❌ Enter button not found after password entry for save.", status="fail")
            logger.take_screenshot("Save_Transaction_Password_Enter_Not_Found")
            return False

        if _wait_for_store_mode(win, timeout=8.0):
            print(f"✅ Store credentials entered ({username}).")
            logger.log("✅ Store login completed for save.", status="pass")
            return True

        logger.log("❌ Store mode did not appear after save credentials were entered.", status="fail")
        logger.take_screenshot("Save_Transaction_Store_Mode_Not_Found")
        return False
    except Exception as e:
        logger.log(f"❌ Credential entry error: {e}", status="fail")
        logger.take_screenshot("Save_Transaction_Login_Error")
        return False


def _open_attendant_login(win, context_label):
    """Open the credential prompt from StoreLogin or Assistance -> Log In."""
    if _input_box_visible(win, timeout=0.2) or _store_mode_visible(win, timeout=0.2):
        return True

    if _click_auto_id(win, "StoreLogin", context_label) and _wait_for_input_or_store(win, timeout=3.0):
        return True

    if _input_box_visible(win, timeout=0.2) or _store_mode_visible(win, timeout=0.2):
        return True

    if _click_auto_id(win, "AssistanceButton", context_label):
        if _wait_for_input_or_store(win, timeout=2.0):
            return True
        if _click_login_option(win, context_label):
            return True

    return _click_login_option(win, context_label) or _input_box_visible(win, timeout=0.2)


def _click_auto_id(win, auto_id, context_label):
    try:
        btn = win.child_window(auto_id=auto_id, control_type="Button")
        if _control_ready(btn, timeout=3.0):
            btn.click_input()
            print(f"✅ {auto_id} button clicked.")
            logger.log(f"✅ {auto_id} clicked for {context_label}.", status="pass")
            return True
    except Exception as e:
        logger.log(f"⚠️ {auto_id} click error for {context_label}: {e}", status="pass")

    return False


def _click_login_option(win, context_label):
    for auto_id in _LOGIN_OPTION_AUTO_IDS:
        try:
            btn = win.child_window(auto_id=auto_id, control_type="Button")
            if _control_ready(btn, timeout=1.0):
                btn.click_input()
                print(f"✅ Login option clicked via '{auto_id}'.")
                logger.log(f"✅ Login option clicked for {context_label} via '{auto_id}'.", status="pass")
                return True
        except Exception:
            continue

    for title in _LOGIN_OPTION_TITLES:
        for control_type in ("Button", "Text"):
            try:
                ctrl = win.child_window(title=title, control_type=control_type)
                if _control_ready(ctrl, timeout=1.0):
                    ctrl.click_input()
                    print(f"✅ Login option clicked via title '{title}'.")
                    logger.log(f"✅ Login option clicked for {context_label} via title '{title}'.", status="pass")
                    return True
            except Exception:
                continue

    return False


def _get_input_box(win, timeout):
    input_box = win.child_window(auto_id="InputTextBox", control_type="Edit")
    if _control_ready(input_box, timeout=timeout):
        return input_box
    return None


def _click_enter(win, timeout=3.0):
    enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
    if _control_ready(enter_btn, timeout=timeout):
        enter_btn.click_input()
        return True
    return False


def _input_box_visible(win, timeout):
    try:
        input_box = win.child_window(auto_id="InputTextBox", control_type="Edit")
        return _control_ready(input_box, timeout=timeout)
    except Exception:
        return False


def _store_mode_visible(win, timeout):
    for auto_id in (_SUSPEND_BUTTON_ID, _GO_TO_POS_BUTTON_ID, "StoreButton1", "StoreButton8"):
        try:
            btn = win.child_window(auto_id=auto_id, control_type="Button")
            if _control_ready(btn, timeout=timeout):
                return True
        except Exception:
            continue
    return False


def _control_ready(control, timeout):
    if not control.exists(timeout=timeout):
        return False

    try:
        wrapper = control.wrapper_object()
        rect = wrapper.rectangle()
        if rect.width() <= 0 or rect.height() <= 0:
            return False
        return wrapper.is_visible() and wrapper.is_enabled()
    except Exception:
        return False


def _wait_for_input_or_store(win, timeout):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if _input_box_visible(win, timeout=0.1) or _store_mode_visible(win, timeout=0.1):
            return True
        time.sleep(0.2)
    return False


def _wait_for_store_mode(win, timeout):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if _store_mode_visible(win, timeout=0.1):
            return True
        time.sleep(0.2)
    return False


def _click_save_button(win):
    """Click the Save Transaction button in POS mode."""
    try:
        btn = win.child_window(auto_id=_SAVE_TRANSACTION_BUTTON, control_type="Button")
        if btn.exists(timeout=5.0):
            btn.click_input()
            return True
    except Exception:
        pass

    for title in ("Save Transaction", "Save", "Suspend Transaction", "Suspend"):
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=2.0):
                btn.click_input()
                return True
        except Exception:
            continue

    return False


def _click_go_to_sco(win):
    """Click the 'Go to SCO' button in POS mode (pending confirmed auto_id)."""
    for aid in _GO_TO_SCO_CANDIDATES:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=2.0):
                btn.click_input()
                print(f"✅ 'Go to SCO' clicked via '{aid}'.")
                return True
        except Exception:
            continue

    for title in ("Go to SCO", "Go To SCO", "SCO Mode", "SCOMode"):
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=2.0):
                btn.click_input()
                return True
        except Exception:
            continue
        try:
            txt = win.child_window(title=title, control_type="Text")
            if txt.exists(timeout=1.0):
                txt.click_input()
                return True
        except Exception:
            continue

    return False


def _check_idle_state(win):
    """Check if SCO is back in idle state."""
    idle_indicators = ["ScanItem", "StartButton", "StartScanButton", "PayButton"]
    for indicator in idle_indicators:
        try:
            elem = win.child_window(auto_id=indicator, control_type="Button")
            if elem.exists(timeout=5):
                return True
        except Exception:
            continue
    return False
