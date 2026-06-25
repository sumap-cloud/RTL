"""
Redeem_reward_voucher.py
------------------------
Handles the EagleEye Reward Voucher redemption flow on NCR SCO.

Triggered after clicking the reward tender button (e.g., Tender3).
The SCO raises an 'Assistance Needed' popup (store login required),
then shows a 'Card Tender Declined' screen with voucher redemption options.

Full flow:
  1. Click the reward tender button (configurable, default 'Tender3').
  2. Wait for 'Assistance Needed' popup.
  3. Perform store login (attendant credentials).
  4. Handle 'Card Tender Declined' → click OK.
  5. Click 'Rewards Vouchers'.
  6. Select the first available voucher amount from the configured list.
  7. Confirm via List4Button and navigate back via GoBack.
  8. Wait for 'Select Payment Type' to confirm return to payment screen.

After this function returns True, call complete_transaction() to pay
the remaining balance by card (Tender2 / EFT).

Usage example:
    from Components.Redeem_reward_voucher import redeem_reward_voucher
    redeem_reward_voucher(
        reward_tender_id="Tender3",
        voucher_options=["Redeem $10", "$10", "Skip"],
        username="ms",
        password="abcd1234",
    )
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

_DEFAULT_VOUCHER_OPTIONS = ["Redeem $30", "Redeem $10", "$10", "$15", "$30", "Skip"]
_DEFAULT_USERNAME = "ms"
_DEFAULT_PASSWORD = "abcd1234"


def redeem_reward_voucher(
    reward_tender_id="Tender3",
    voucher_options=None,
    username=_DEFAULT_USERNAME,
    password=_DEFAULT_PASSWORD,
):
    """
    Click the reward tender and complete the EagleEye voucher redemption flow.

    Args:
        reward_tender_id (str): auto_id of the reward tender button on the
            payment screen (default 'Tender3'). Pass None to skip clicking
            and start from the 'Assistance Needed' popup directly.
        voucher_options (list[str]): Ordered list of voucher amount labels to
            try. The first label found on screen is selected.
        username (str): Store attendant username for the login popup.
        password (str): Store attendant password.

    Returns:
        bool: True if voucher redemption completed and SCO returned to the
            'Select Payment Type' screen. False on any unrecoverable failure.
    """
    if voucher_options is None:
        voucher_options = _DEFAULT_VOUCHER_OPTIONS

    win = global_instance.win
    if win is None:
        logger.log("❌ SCO window not initialised. Call login_pos() first.", status="fail")
        return False

    try:
        win.set_focus()
    except Exception:
        pass

    # -----------------------------------------------------------------------
    # Step 1: Click the reward tender button (e.g., Tender3).
    # -----------------------------------------------------------------------
    if reward_tender_id:
        print(f"➡️ Clicking reward tender button: '{reward_tender_id}'...")
        try:
            btn = win.child_window(auto_id=reward_tender_id, control_type="Button")
            if not btn.exists(timeout=5.0):
                logger.log(
                    f"❌ Reward tender button '{reward_tender_id}' not found on payment screen.",
                    status="fail",
                )
                logger.take_screenshot("Redeem_Voucher_Tender_Not_Found")
                return False
            btn.click_input()
            print(f"✅ Reward tender '{reward_tender_id}' clicked.")
            logger.log(f"✅ Reward tender '{reward_tender_id}' clicked.", status="pass")
        except Exception as e:
            logger.log(
                f"❌ Failed to click reward tender '{reward_tender_id}': {e}",
                status="fail",
            )
            logger.take_screenshot("Redeem_Voucher_Tender_Click_Failed")
            return False

    # -----------------------------------------------------------------------
    # Step 2: Wait for 'Assistance Needed' popup.
    # -----------------------------------------------------------------------
    print("⏳ Waiting for 'Assistance Needed' popup...")
    try:
        popup_title = win.child_window(auto_id="PopupTitle", control_type="Text")
        timings.wait_until(
            15.0,
            0.2,
            lambda: popup_title.exists(timeout=0.1)
            and "Assistance" in (popup_title.window_text() or ""),
        )
        print("✅ 'Assistance Needed' detected — performing store login...")
        logger.log("✅ 'Assistance Needed' popup detected.", status="pass")
    except timings.TimeoutError:
        logger.log(
            "⚠️ 'Assistance Needed' popup did not appear in 15 s — attempting login anyway.",
            status="pass",
        )
        logger.take_screenshot("Redeem_Voucher_Assistance_Timeout")

    # -----------------------------------------------------------------------
    # Step 3: Store login.
    # -----------------------------------------------------------------------
    if not _do_store_login(win, username, password):
        return False

    # -----------------------------------------------------------------------
    # Step 4: Wait for 'Card Tender Declined' screen then click OK.
    # -----------------------------------------------------------------------
    print("⏳ Waiting for 'Card Tender Declined' screen...")
    try:
        screen_title = win.child_window(auto_id="StoreModeScreenTitle1", control_type="Text")
        timings.wait_until(15.0, 0.2, lambda: screen_title.exists(timeout=0.1))
        msg = screen_title.window_text()
        print(f"✅ Store mode screen: '{msg}'")
        logger.log(f"✅ StoreModeScreenTitle1: '{msg}'", status="pass")
    except timings.TimeoutError:
        logger.log(
            "⚠️ 'Card Tender Declined' screen not detected in 15 s — continuing.",
            status="pass",
        )
        logger.take_screenshot("Redeem_Voucher_Declined_Timeout")

    _click_ok(win)

    # -----------------------------------------------------------------------
    # Step 5: Click 'Rewards Vouchers'.
    # -----------------------------------------------------------------------
    print("➡️ Clicking 'Rewards Vouchers'...")
    try:
        rewards_txt = win.child_window(title="Rewards Vouchers", control_type="Text")
        timings.wait_until(10.0, 0.2, lambda: rewards_txt.exists(timeout=0.1))
        rewards_txt.click_input()
        print("✅ 'Rewards Vouchers' clicked.")
        logger.log("✅ 'Rewards Vouchers' clicked.", status="pass")
    except timings.TimeoutError:
        logger.log("❌ 'Rewards Vouchers' text not found.", status="fail")
        logger.take_screenshot("Redeem_Voucher_Rewards_Vouchers_Not_Found")
        return False
    except Exception as e:
        logger.log(f"❌ Error clicking 'Rewards Vouchers': {e}", status="fail")
        logger.take_screenshot("Redeem_Voucher_Rewards_Vouchers_Error")
        return False

    # -----------------------------------------------------------------------
    # Step 6: Select the first available voucher amount.
    # -----------------------------------------------------------------------
    selected = _click_first_available_option(win, voucher_options)
    if selected is None:
        logger.log(
            f"❌ None of the voucher options were available: {voucher_options}",
            status="fail",
        )
        logger.take_screenshot("Redeem_Voucher_Option_Not_Found")
        return False
    print(f"✅ Voucher option selected: '{selected}'.")
    logger.log(f"✅ Voucher option '{selected}' selected.", status="pass")

    # -----------------------------------------------------------------------
    # Step 7: Confirm via List4Button.
    # -----------------------------------------------------------------------
    print("➡️ Clicking List4Button (confirm voucher)...")
    try:
        list4 = win.child_window(auto_id="List4Button", control_type="Button")
        timings.wait_until(10.0, 0.2, lambda: list4.exists(timeout=0.1))
        list4.click_input()
        print("✅ List4Button clicked.")
        logger.log("✅ List4Button (confirm voucher) clicked.", status="pass")
    except timings.TimeoutError:
        logger.log("❌ List4Button not found.", status="fail")
        logger.take_screenshot("Redeem_Voucher_List4Button_Not_Found")
        return False
    except Exception as e:
        logger.log(f"❌ Error clicking List4Button: {e}", status="fail")
        logger.take_screenshot("Redeem_Voucher_List4Button_Error")
        return False

    # -----------------------------------------------------------------------
    # Step 8: Go Back to payment screen.
    # -----------------------------------------------------------------------
    print("➡️ Clicking GoBack...")
    try:
        goback = win.child_window(auto_id="GoBack", control_type="Button")
        timings.wait_until(10.0, 0.2, lambda: goback.exists(timeout=0.1))
        goback.click_input()
        print("✅ GoBack clicked.")
        logger.log("✅ GoBack — returning to payment screen.", status="pass")
    except timings.TimeoutError:
        logger.log("❌ GoBack button not found.", status="fail")
        logger.take_screenshot("Redeem_Voucher_GoBack_Not_Found")
        return False
    except Exception as e:
        logger.log(f"❌ Error clicking GoBack: {e}", status="fail")
        logger.take_screenshot("Redeem_Voucher_GoBack_Error")
        return False

    # -----------------------------------------------------------------------
    # Step 9: Confirm we are back at 'Select Payment Type'.
    # -----------------------------------------------------------------------
    print("⏳ Waiting for 'Select Payment Type'...")
    try:
        leadthru = win.child_window(auto_id="LeadthruText", control_type="Text")
        timings.wait_until(
            15.0,
            0.2,
            lambda: leadthru.exists(timeout=0.1)
            and "Select Payment" in (leadthru.window_text() or ""),
        )
        print("✅ 'Select Payment Type' confirmed.")
        logger.log("✅ Returned to 'Select Payment Type' screen.", status="pass")
    except timings.TimeoutError:
        logger.log(
            "⚠️ 'Select Payment Type' not confirmed in 15 s — continuing to card payment.",
            status="pass",
        )
        logger.take_screenshot("Redeem_Voucher_PaymentType_Timeout")

    global_instance.reward_redeem_status = True
    logger.log(f"✅ Reward voucher redeemed: '{selected}'.", status="pass")
    return True


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _do_store_login(win, username, password):
    """Click StoreLogin, enter username, press Enter, enter password, press Enter."""
    try:
        store_btn = win.child_window(auto_id="StoreLogin", control_type="Button")
        timings.wait_until(10.0, 0.2, lambda: store_btn.exists(timeout=0.1))
        store_btn.click_input()
        print("✅ StoreLogin button clicked.")

        _set_input_text(win, username)
        _click_enter(win)
        print(f"✅ Username '{username}' entered.")

        _set_input_text(win, password)
        _click_enter(win)
        print("✅ Password entered.")

        logger.log("✅ Store login completed.", status="pass")
        return True
    except timings.TimeoutError as e:
        logger.log(f"❌ Store login timed out: {e}", status="fail")
        logger.take_screenshot("Redeem_Voucher_Login_Timeout")
        return False
    except Exception as e:
        logger.log(f"❌ Store login error: {e}", status="fail")
        logger.take_screenshot("Redeem_Voucher_Login_Error")
        return False


def _set_input_text(win, value, timeout=10):
    """Type into the InputTextBox field."""
    box = win.child_window(auto_id="InputTextBox", control_type="Edit")
    timings.wait_until(timeout, 0.2, lambda: box.exists(timeout=0.1))
    box.set_text(value)


def _click_enter(win, timeout=10):
    """Click the EnterButton."""
    btn = win.child_window(auto_id="EnterButton", control_type="Button")
    timings.wait_until(timeout, 0.2, lambda: btn.exists(timeout=0.1))
    btn.click_input()


def _click_ok(win, timeout=8):
    """Click any OK-like button on screen."""
    for aid in ["OK_Button", "GenericOKButton", "ASAOKButton"]:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=1.0):
                btn.click_input()
                print(f"✅ OK button ('{aid}') clicked.")
                logger.log(f"✅ OK button '{aid}' clicked.", status="pass")
                return
        except Exception:
            continue
    # Title-based fallback (the user code uses title_re=".*OK.*")
    try:
        btn = win.child_window(title_re="(?i)^ok$", control_type="Button")
        if btn.exists(timeout=2.0):
            btn.click_input()
            print("✅ OK button clicked (title match).")
            logger.log("✅ OK button clicked (title match).", status="pass")
    except Exception:
        pass


def _click_first_available_option(win, options, timeout_per=3.0):
    """Try each option in order; click and return the first one found."""
    for label in options:
        try:
            ctrl = win.child_window(title=label, control_type="Text")
            if ctrl.exists(timeout=timeout_per):
                ctrl.click_input()
                return label
        except Exception:
            continue
    return None
