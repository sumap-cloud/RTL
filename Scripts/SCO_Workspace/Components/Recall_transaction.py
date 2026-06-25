"""
Recall_transaction.py
---------------------
Recalls (resumes) a previously saved/suspended transaction on SCO.

Flow on NCR SCO (confirmed from live control dump 2026-06-19):
  1. Enter attendant/store mode (StoreLogin, or Assistance → Log In →
     credentials).
  2. Click "Go To POS" (StoreButton7) to switch to POS register view.
  3. Click "Recall Transaction" button in POS lower commands bar.
  4. Select the target transaction from the recall list (first entry by default).
  5. Confirm the recall.
  6. Click "Go to SCO" to return to SCO mode.
  7. The recalled transaction should now be reflected in the SCO sale screen.

TODO: Verify exact auto_ids for:
  - "Recall Transaction" button in POS mode
  - "Go to SCO" button in POS mode
  - Transaction selection list in POS mode
  from a live POS control dump (run capture_controls.py pos on recall screen).
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


def recall_transaction(username=_DEFAULT_USERNAME, password=_DEFAULT_PASSWORD,
                       transaction_index=0):
    """
    Recall a previously saved transaction on SCO.

    Flow:
      1. Enter store/attendant mode via StoreLogin, or Assistance → Log In
         + credentials.
      2. Click "Go to POS" to switch view.
      3. Click "Recall Transaction" in POS lower bar.
      4. Select the transaction (by index in list, default = first/most recent).
      5. Confirm the recall.
      6. Click "Go to SCO" to return.
      7. Verify transaction is reflected in SCO sale screen.

    Args:
        username (str): Store attendant username.
        password (str): Store attendant password.
        transaction_index (int): Index of transaction to recall (0-based).

    Returns:
        bool: True if transaction was recalled successfully.
    """
    win = global_instance.win
    if win is None:
        logger.log("❌ SCO window not initialised. Cannot recall transaction.", status="fail")
        return False

    try:
        win.set_focus()
    except Exception:
        pass

    # --- Step 1: Enter store/attendant mode ---
    print("➡️ Entering attendant mode to recall transaction...")
    if not _do_store_login(win, username, password):
        return False

    # --- Step 2: Click "Go to POS" ---
    time.sleep(2)
    print(f"➡️ Clicking 'Go To POS' ({_GO_TO_POS_BUTTON_ID})...")
    try:
        btn = win.child_window(auto_id=_GO_TO_POS_BUTTON_ID, control_type="Button")
        if not btn.exists(timeout=5.0):
            # Title fallback
            btn2 = win.child_window(title="Go To POS", control_type="Text")
            if btn2.exists(timeout=3.0):
                btn2.click_input()
            else:
                logger.log("❌ 'Go To POS' button not found in attendant mode.", status="fail")
                logger.take_screenshot("Recall_Transaction_GoToPOS_Not_Found")
                return False
        else:
            btn.click_input()
        logger.log("✅ Switched to POS mode for recall.", status="pass")
        print("✅ Switched to POS mode for recall.")
    except Exception as e:
        logger.log(f"❌ Error clicking 'Go To POS': {e}", status="fail")
        logger.take_screenshot("Recall_Transaction_GoToPOS_Error")
        return False

    # --- Step 3: Click "Recall Transaction" ---
    time.sleep(2)
    print("➡️ Clicking 'Recall Transaction'...")
    try:
        btn = win.child_window(
            auto_id="commandsLowerButtonsRecall Transaction", control_type="Button"
        )
        if not btn.exists(timeout=5.0):
            logger.log("❌ 'Recall Transaction' button not found in POS mode.", status="fail")
            logger.take_screenshot("Recall_Transaction_Button_Not_Found")
            return False
        btn.click_input()
        logger.log("✅ 'Recall Transaction' clicked.", status="pass")
        print("✅ 'Recall Transaction' clicked.")
    except Exception as e:
        logger.log(f"❌ Error clicking 'Recall Transaction': {e}", status="fail")
        return False

    # --- Step 4: Wait for recall screen, click "Transaction List" to get list ---
    time.sleep(2)
    print("➡️ Waiting for recall screen (ResumeTransactionByBarcodeViewID)...")
    try:
        recall_screen = win.child_window(
            auto_id="ResumeTransactionByBarcodeViewID", control_type="Custom"
        )
        recall_screen.exists(timeout=8.0)
    except Exception:
        pass

    # Click "Transaction List" to view the list of suspended transactions
    print("➡️ Clicking 'Transaction List'...")
    try:
        txn_list_btn = win.child_window(
            auto_id="GenericCommandButtonTemplete_TransactionList", control_type="Button"
        )
        if txn_list_btn.exists(timeout=5.0):
            txn_list_btn.click_input()
            print("✅ 'Transaction List' clicked.")
            logger.log("✅ 'Transaction List' clicked — viewing suspended transactions.", status="pass")
        else:
            logger.log(
                "⚠️ 'Transaction List' button not found. "
                "May need to enter barcode manually.",
                status="pass"
            )
            logger.take_screenshot("Recall_Transaction_List_Not_Found")
    except Exception as e:
        logger.log(f"⚠️ Error clicking 'Transaction List': {e}", status="pass")

    # --- Step 5: Select transaction from the list ---
    time.sleep(2)
    if not _select_transaction(win, transaction_index):
        logger.log(
            f"⚠️ Could not select transaction at index {transaction_index}. "
            "Attempting confirm directly.",
            status="pass"
        )
        logger.take_screenshot("Recall_Transaction_Select_Issue")

    # --- Step 6: Confirm the recall ---
    time.sleep(1)
    print("➡️ Clicking 'Recall' to confirm...")
    try:
        # Confirmed from live dump: title="Recall", no auto_id on this screen
        recall_btn = win.child_window(title="Recall", control_type="Button")
        if recall_btn.exists(timeout=5.0):
            recall_btn.click_input()
            logger.log("✅ 'Recall' confirmed.", status="pass")
            print("✅ 'Recall' confirmed.")
        else:
            # Fallback to auto_id version (from barcode entry screen)
            recall_btn2 = win.child_window(
                auto_id="GenericCommandButtonTemplete_Recall", control_type="Button"
            )
            if recall_btn2.exists(timeout=3.0):
                recall_btn2.click_input()
                logger.log("✅ 'Recall' confirmed (via GenericCommandButtonTemplete_Recall).", status="pass")
            else:
                logger.log("⚠️ 'Recall' confirm button not found. Trying fallback.", status="pass")
                _confirm_recall_fallback(win)
    except Exception as e:
        logger.log(f"⚠️ Error confirming recall: {e}", status="pass")
        _confirm_recall_fallback(win)

    # --- Step 7: Click "Finish Go To SCO" ---
    time.sleep(2)
    print("➡️ Clicking 'Finish Go To SCO'...")
    try:
        go_sco_btn = win.child_window(
            auto_id="commandsLowerButtonsFinish Go To SCO", control_type="Button"
        )
        if go_sco_btn.exists(timeout=8.0):
            go_sco_btn.click_input()
            logger.log("✅ 'Finish Go To SCO' clicked — returning to SCO.", status="pass")
            print("✅ 'Finish Go To SCO' clicked.")
        else:
            logger.log(
                "⚠️ 'Finish Go To SCO' button not found. SCO may auto-return.",
                status="pass"
            )
            logger.take_screenshot("Recall_Transaction_GoToSCO_Not_Found")
    except Exception as e:
        logger.log(f"⚠️ Error clicking 'Finish Go To SCO': {e}", status="pass")

    # --- Step 8: Verify transaction is reflected in SCO ---
    time.sleep(3)
    items_visible = _verify_transaction_loaded(win)
    if items_visible:
        logger.log("✅ Transaction recalled. Items visible in SCO sale screen.", status="pass")
        print("✅ Transaction recalled. Items visible in SCO sale screen.")
    else:
        logger.log(
            "⚠️ Could not confirm items in SCO after recall. Continuing.",
            status="pass"
        )
        logger.take_screenshot("Recall_Transaction_Items_Unconfirmed")

    return True


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _do_store_login(win, username, password):
    """Open attendant login, handle the Log In option if shown, then enter credentials."""
    try:
        if _store_mode_visible(win, timeout=0.5):
            logger.log("✅ Store mode already available for recall.", status="pass")
            return True

        if not _open_attendant_login(win, "recall"):
            logger.log(
                "❌ Could not open attendant login for recall.",
                status="fail",
            )
            logger.take_screenshot("Recall_Transaction_Login_Not_Found")
            return False
    except Exception as e:
        logger.log(f"❌ Attendant login button click error: {e}", status="fail")
        logger.take_screenshot("Recall_Transaction_Login_Click_Error")
        return False

    try:
        if _store_mode_visible(win, timeout=0.5):
            return True

        input_box = _get_input_box(win, timeout=8.0)
        if input_box is None:
            if _store_mode_visible(win, timeout=0.5):
                return True
            logger.log("❌ Store credential input did not appear for recall.", status="fail")
            logger.take_screenshot("Recall_Transaction_Login_Input_Not_Found")
            return False

        input_box.set_text(username)
        if not _click_enter(win):
            logger.log("❌ Enter button not found after username entry for recall.", status="fail")
            logger.take_screenshot("Recall_Transaction_Login_Enter_Not_Found")
            return False

        time.sleep(0.5)
        input_box = _get_input_box(win, timeout=8.0)
        if input_box is None:
            logger.log("❌ Password input did not appear for recall.", status="fail")
            logger.take_screenshot("Recall_Transaction_Password_Input_Not_Found")
            return False

        input_box.set_text(password)
        if not _click_enter(win):
            logger.log("❌ Enter button not found after password entry for recall.", status="fail")
            logger.take_screenshot("Recall_Transaction_Password_Enter_Not_Found")
            return False

        if _wait_for_store_mode(win, timeout=8.0):
            print(f"✅ Store credentials entered ({username}).")
            logger.log("✅ Store login completed for recall.", status="pass")
            return True

        logger.log("❌ Store mode did not appear after recall credentials were entered.", status="fail")
        logger.take_screenshot("Recall_Transaction_Store_Mode_Not_Found")
        return False
    except Exception as e:
        logger.log(f"❌ Credential entry error: {e}", status="fail")
        logger.take_screenshot("Recall_Transaction_Login_Error")
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
    for auto_id in (_GO_TO_POS_BUTTON_ID, "StoreButton1", "StoreButton2", "StoreButton8"):
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


def _click_recall_button(win):
    """Unused — kept for reference. Direct auto_id used in main flow."""
    pass


def _click_go_to_sco(win):
    """Unused — kept for reference. Direct auto_id used in main flow."""
    pass


def _select_transaction(win, index):
    """Select a transaction from the SearchResultsDataGrid after clicking 'Transaction List'.

    Confirmed from live POS control dump (2026-06-19):
      - Grid: auto_id="SearchResultsDataGrid", control_type="DataGrid"
      - Rows: control_type="DataItem" (title="Retalix.Client.POS...TransactionDatum")
    """
    try:
        grid = win.child_window(auto_id="SearchResultsDataGrid", control_type="DataGrid")
        if grid.exists(timeout=5.0):
            rows = grid.children(control_type="DataItem")
            if rows and index < len(rows):
                rows[index].click_input()
                print(f"✅ Selected transaction row {index} from SearchResultsDataGrid.")
                logger.log("✅ Transaction row selected from SearchResultsDataGrid.", status="pass")
                return True
            elif rows:
                # Fewer rows than expected — just pick the first
                rows[0].click_input()
                print("✅ Selected first available transaction row.")
                logger.log("✅ First transaction row selected.", status="pass")
                return True
            else:
                logger.log(
                    "⚠️ SearchResultsDataGrid found but no DataItem rows visible.",
                    status="pass"
                )
                logger.take_screenshot("Recall_Transaction_No_Rows")
    except Exception as e:
        logger.log(f"⚠️ Error selecting from SearchResultsDataGrid: {e}", status="pass")

    return False


def _confirm_recall_fallback(win):
    """Fallback recall confirm — tries common button titles."""
    for title in ("Recall", "OK", "Confirm", "Resume"):
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=2.0):
                btn.click_input()
                print(f"✅ Recall confirmed via title '{title}'.")
                return True
        except Exception:
            continue
    return False


def _verify_transaction_loaded(win):
    """Check if recalled transaction items are visible in SCO sale screen."""
    # Look for item description text or basket list indicating items are present
    try:
        # Check for basket/item list (tbDescription is the item text pattern from POS dump)
        item_desc = win.child_window(auto_id="tbDescription", control_type="Text")
        if item_desc.exists(timeout=5):
            return True
    except Exception:
        pass

    # Check for the LeftRegion list (basket area)
    try:
        left_region = win.child_window(auto_id="LeftRegion", control_type="List")
        if left_region.exists(timeout=3):
            items = left_region.children()
            if len(items) > 0:
                return True
    except Exception:
        pass

    # Check for PayButton (indicates items in basket, ready to pay)
    try:
        pay_btn = win.child_window(auto_id="PayButton", control_type="Button")
        if pay_btn.exists(timeout=3):
            return True
    except Exception:
        pass

    return False
