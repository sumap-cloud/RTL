"""
Complete_transaction.py
-----------------------
Completes the SCO transaction in tender mode via Card (EFT) payment.

Flow (Card-Only SCO, EFT service + MultiSimulator running):
  1. Dismiss any lingering popups.
  2. Click the Card payment button (Tender2).
  3. Wait for the EFT simulator to auto-approve the card payment.
  4. Handle any receipt popup if it appears.
  5. Wait for the transaction to complete (thank-you / idle screen).
  6. Log pass/fail with screenshots on every failure.

The EFT MultiSimulator auto-approves card payments when
RemedyEFTPOSServer is running.
"""

import sys
import re
import time
from datetime import datetime
from pathlib import Path
from pywinauto import Application, timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger

# ----- Tunable timeouts (seconds) ----------------------------------------
_PAYMENT_SCREEN_TIMEOUT = 20  # Time to wait for the payment selection screen
_EFT_APPROVAL_TIMEOUT = 90   # Time to wait for EFT auto-approval (manual simulator)
_TRANSACTION_COMPLETE_TIMEOUT = 45  # Time to wait for transaction-complete screen
# --------------------------------------------------------------------------

# Known auto_ids for card payment buttons on NCR SCO.
# From live control dump: Card tender = Tender2 on NCR NEXTGENUI.
_CARD_BUTTON_AIDS = [
    ("Tender2", "Button"),       # NCR NEXTGENUI SCO — "Card" confirmed from control dump
    ("PaymentCard", "Button"),
    ("CardButton", "Button"),
]


def complete_transaction():
    """
    Finalise the SCO transaction via Card (EFT) payment.

    The MultiSimulator auto-approves the card payment when
    RemedyEFTPOSServer is running.

    Returns:
        bool: True if the transaction completed successfully, False otherwise.
    """
    win = global_instance.win
    if win is None:
        logger.log(
            "❌ SCO window not initialised. Call login_pos() first.",
            status="fail"
        )
        return False

    # Record timestamp so Verify_EagleEye_logs can search from this point.
    # IMPORTANT: only set if not already set earlier — e.g. login_pos() sets
    # it at test start so loyalty-card validate / wallet-open events that
    # fire BEFORE this function are inside the search window.
    if global_instance.ee_log_start_time is None:
        global_instance.ee_log_start_time = datetime.now()

    try:
        win.set_focus()
    except Exception:
        pass

    # ------------------------------------------------------------------
    # Step 0a: If SCO already returned to idle, the transaction completed
    # before this function was called (e.g., EFT processed during redemption).
    # Retry for up to 3 s with a longer per-check timeout to handle screen
    # transitions where WPF briefly removes elements from the UIA tree.
    # ------------------------------------------------------------------
    for _ in range(3):
        try:
            start_scan = win.child_window(auto_id="StartScanButton", control_type="Button")
            if start_scan.exists(timeout=1.0):
                logger.log(
                    "✅ SCO already at idle/complete state — transaction completed "
                    "before complete_transaction() searched for the card button.",
                    status="pass"
                )
                return True
        except Exception:
            pass
        time.sleep(0.5)

    # ------------------------------------------------------------------
    # Step 0b: Dismiss any active popup (e.g., "Assistance Needed")
    # ------------------------------------------------------------------
    _dismiss_any_popup(win)

    # ------------------------------------------------------------------
    # Step 0c: Handle intermediate screens before payment selection.
    #   - "Scan Coupon" screen  → click CancelCoupon to skip
    #   - Store Authorisation popup → dismiss via GoBackButton / Cancel
    # ------------------------------------------------------------------
    _handle_pre_payment_screens(win)

    # ------------------------------------------------------------------
    # Step 1: Dump all tender buttons (diagnostic) then find and click
    # the Card payment button (Tender2).
    # NOTE: Reward tender (Tender3) must be handled BEFORE this function
    # via redeem_reward_voucher() — see TC_002 for the full flow.
    # ------------------------------------------------------------------
    _log_payment_buttons(win)

    card_btn = _find_card_button(win)
    if card_btn is None:
        try:
            pay_btn = win.child_window(auto_id="PayButton", control_type="Button")
            if pay_btn.exists(timeout=2.0):
                pay_btn.click_input()
                print("✅ PayButton clicked from basket view before card payment.")
                logger.log("✅ PayButton clicked from basket view before card payment.", status="pass")
                time.sleep(2)
                _handle_pre_payment_screens(win)
                _log_payment_buttons(win)
                card_btn = _find_card_button(win)
        except Exception as e:
            print(f"⚠️ Could not click PayButton before card payment retry: {e}")

    if card_btn is None:
        logger.log(
            "❌ Card payment button not found on tender/payment screen. "
            "Taking diagnostic screenshot.",
            status="fail"
        )
        logger.take_screenshot("Complete_Txn_Card_Button_Not_Found")
        _dump_controls(win, "Complete_Txn_Control_Dump")
        return False

    try:
        card_btn.click_input()
        print("✅ Card button (Tender2) clicked — waiting for EFT auto-approval...")
        logger.log("✅ Card payment button (Tender2) clicked.", status="pass")
    except Exception as e:
        logger.log(f"❌ Failed to click Card payment button: {e}", status="fail")
        logger.take_screenshot("Complete_Txn_Card_Button_Click_Failed")
        return False

    # ------------------------------------------------------------------
    # Step 2: Wait for EFT auto-approval.
    # The MultiSimulator processes the card payment automatically.
    # We wait for either transaction completion or a pinpad-related screen.
    # ------------------------------------------------------------------
    logger.log("⏳ Waiting for EFT auto-approval from MultiSimulator...", status="pass")

    # Wait for the payment to process — check for completion indicators
    # or pinpad interaction messages.
    completed = _wait_for_eft_completion(win)

    if completed:
        logger.log("✅ Transaction completed successfully via Card payment.", status="pass")
    else:
        # EFT is already in progress — do NOT dismiss popups here as that
        # would cancel the EFT session. Only handle the receipt popup.
        _handle_receipt_popup(win)

        # Try waiting one more time.
        completed = _wait_for_completion_idle(win, timeout=15)
        if completed:
            logger.log("✅ Transaction completed successfully via Card payment.", status="pass")
        else:
            logger.log(
                "⚠️ Transaction completion not confirmed within timeout. "
                "The transaction may still have completed — check EE logs.",
                status="pass"
            )
            logger.take_screenshot("Complete_Txn_Completion_Unconfirmed")

    return completed


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_card_button(win):
    """Try each known auto_id for the Card tender button. Return first match or None."""
    for auto_id, ctrl_type in _CARD_BUTTON_AIDS:
        print(f"🔍 Looking for card button: auto_id='{auto_id}'...")
        try:
            btn = win.child_window(auto_id=auto_id, control_type=ctrl_type)
            if btn.exists(timeout=_PAYMENT_SCREEN_TIMEOUT / len(_CARD_BUTTON_AIDS)):
                print(f"✅ Found card button: '{auto_id}'")
                return btn
        except Exception as ex:
            print(f"⚠️ Error finding '{auto_id}': {ex}")
            continue

    # Last resort: title-based search.
    for title in ["Card", "Pay Card", "Pay with Card", "EFTPOS"]:
        try:
            btn = win.child_window(title_re=f"(?i)^{re.escape(title)}$", control_type="Button")
            if btn.exists(timeout=1):
                print(f"✅ Found card button by title: '{title}'")
                return btn
        except Exception:
            continue

    print("❌ Card button NOT found on payment screen.")
    return None


def _wait_for_eft_completion(win):
    """
    Wait for the EFT payment to be processed by MultiSimulator.

    After clicking Card (Tender2), the SCO communicates with the EFT service.
    The MultiSimulator auto-approves the transaction. We wait for either:
    - Transaction completion indicators (thank-you, idle screen)
    - Receipt popup (means payment succeeded, need to dismiss)

    Returns:
        bool: True if transaction completed, False if timeout.
    """
    deadline = time.time() + _EFT_APPROVAL_TIMEOUT
    while time.time() < deadline:
        # Check for idle/completion indicators.
        if _check_completion_indicators(win):
            return True

        # Check for receipt popup — means payment was approved.
        # NOTE: No is_enabled() check — NCR SCO popup buttons report False in UIA even when clickable.
        try:
            no_btn = win.child_window(auto_id="No_Button", control_type="Button")
            if no_btn.exists(timeout=0.3):
                no_btn.click_input()
                logger.log("✅ Receipt popup dismissed (clicked 'No').", status="pass")
                time.sleep(2)
                if _check_completion_indicators(win):
                    return True
                continue
        except Exception:
            pass

        # Check for generic OK popup that might need dismissal during payment.
        # NOTE: No is_enabled() check — NCR SCO popup buttons report False in UIA even when clickable.
        try:
            ok_btn = win.child_window(auto_id="OK_Button", control_type="Button")
            if ok_btn.exists(timeout=0.3):
                ok_btn.click_input()
                logger.log("✅ Dismissed OK popup during EFT processing.", status="pass")
                time.sleep(1)
                continue
        except Exception:
            pass

        # Check for "Assistance Needed" popup during EFT processing.
        # NOTE: No is_enabled() check — NCR SCO popup buttons report False in UIA even when clickable.
        try:
            asa_btn = win.child_window(auto_id="ASAOKButton", control_type="Button")
            if asa_btn.exists(timeout=0.3):
                asa_btn.click_input()
                logger.log("✅ Dismissed ASAOKButton popup during EFT processing.", status="pass")
                time.sleep(1)
                continue
        except Exception:
            pass

        time.sleep(1)

    return False


def _check_completion_indicators(win):
    """Check if the SCO has returned to idle/thank-you state."""
    idle_auto_ids = [
        ("StartScanButton", "Button"),
        ("ThankYouMessage", "Text"),
        ("TransactionComplete", "Text"),
    ]
    for auto_id, ctrl_type in idle_auto_ids:
        try:
            elem = win.child_window(auto_id=auto_id, control_type=ctrl_type)
            if elem.exists(timeout=0.3):
                return True
        except Exception:
            continue

    # Check for the welcome/idle banner.
    try:
        leadthru = win.child_window(auto_id="LeadthruText", control_type="Text")
        if leadthru.exists(timeout=0.3):
            text = leadthru.window_text()
            if any(phrase in text.lower() for phrase in ["welcome", "start scanning", "ready"]):
                return True
    except Exception:
        pass

    return False


def _wait_for_completion_idle(win, timeout=15):
    """Wait for SCO to return to idle state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _check_completion_indicators(win):
            return True
        time.sleep(1)
    return False


def _handle_receipt_popup(win):
    """
    Dismiss the receipt-suppress popup if it appears.
    NOTE: No is_enabled() check — NCR SCO popup buttons report False in UIA even when clickable.
    """
    try:
        no_btn = win.child_window(auto_id="No_Button", control_type="Button")
        if no_btn.exists(timeout=2):
            no_btn.click_input()
            logger.log("✅ Receipt popup dismissed (clicked 'No').", status="pass")
            return
    except Exception:
        pass

    # Also try title-based 'No' button.
    try:
        no_btn = win.child_window(title="No", control_type="Button")
        if no_btn.exists(timeout=2):
            no_btn.click_input()
            logger.log("✅ Receipt popup dismissed within SCO window.", status="pass")
    except Exception:
        pass


def _dismiss_any_popup(win):
    """
    Dismiss any active popup dialog that may be blocking the payment screen.
    No is_enabled() check — popup buttons may appear disabled in UIA when actually clickable.
    """
    popup_aids = ["ASAOKButton", "OK_Button", "GenericOKButton", "GenericButton", "ItemRemovedButton"]
    for aid in popup_aids:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=1):
                btn.click_input()
                print(f"✅ Dismissed popup via '{aid}' in Complete_transaction.")
                logger.log(f"✅ Dismissed popup via button '{aid}'.", status="pass")
                time.sleep(1)
                return
        except Exception as ex:
            print(f"⚠️ Could not click '{aid}': {ex}")
            continue


def _handle_pre_payment_screens(win, max_rounds=5):
    """
    Handle intermediate screens that appear BEFORE the payment type selection:

    1. Store Authorisation popup (auto_id='TitleControl' text='Store Authorisation')
       → dismiss via GoBackButton or Cancel button

    2. "Scan Coupon" screen (LeadthruText='Scan Coupon')
       → skip via CancelCoupon button

    Loops up to max_rounds times since dismissing one screen can reveal another.
    """
    for _ in range(max_rounds):
        handled = False

        # --- Blocking choice offer screen ---
        try:
            offer_list = win.child_window(auto_id="ContainerButtonList", control_type="List")
            if offer_list.exists(timeout=1.0):
                skip_btn = win.child_window(auto_id="SkipChoiceOfferPrompt", control_type="Button")
                if skip_btn.exists(timeout=1.0):
                    skip_btn.click_input()
                    print("✅ Choice Offer screen skipped before card payment.")
                    logger.log("✅ Choice Offer screen skipped before card payment.", status="pass")
                    time.sleep(1.5)
                    handled = True
        except Exception:
            pass

        # --- Exciting News / reward popup ---
        try:
            for text_aid in ("Instructions", "GiftCardInstructions"):
                txt_ctrl = win.child_window(auto_id=text_aid, control_type="Text")
                if txt_ctrl.exists(timeout=0.5):
                    txt = (txt_ctrl.window_text() or "").lower()
                    if any(phrase in txt for phrase in ("exciting news", "great news", "you've just earned", "you have just earned")):
                        for btn_aid in ("List1Button", "List2Button", "OK_Button", "ASAOKButton"):
                            btn = win.child_window(auto_id=btn_aid, control_type="Button")
                            if btn.exists(timeout=1.0):
                                btn.click_input()
                                print(f"✅ Exciting News popup dismissed before card payment via '{btn_aid}'.")
                                logger.log(
                                    f"✅ Exciting News popup dismissed before card payment via '{btn_aid}'.",
                                    status="pass"
                                )
                                time.sleep(1.5)
                                handled = True
                                break
                        break
        except Exception:
            pass

        # --- Store Authorisation popup ---
        try:
            title_ctrl = win.child_window(auto_id="TitleControl", control_type="Text")
            if title_ctrl.exists(timeout=1.0):
                txt = title_ctrl.window_text() or ""
                if "authoris" in txt.lower() or "authorization" in txt.lower():
                    # Try GoBackButton first (no credentials needed)
                    for aid in ("GoBackButton", "Cancel", "CPDCancel", "GoBack"):
                        try:
                            btn = win.child_window(auto_id=aid, control_type="Button")
                            if btn.exists(timeout=1.0):
                                btn.click_input()
                                print(f"✅ Store Authorisation popup dismissed via '{aid}'.")
                                logger.log(
                                    f"✅ Store Authorisation popup dismissed via '{aid}'.",
                                    status="pass"
                                )
                                time.sleep(1)
                                handled = True
                                break
                        except Exception:
                            continue
        except Exception:
            pass

        # --- Scan Coupon screen ---
        try:
            leadthru = win.child_window(auto_id="LeadthruText", control_type="Text")
            if leadthru.exists(timeout=1.0):
                txt = leadthru.window_text() or ""
                if "coupon" in txt.lower():
                    for aid in ("Continue", "CancelCoupon"):
                        try:
                            btn = win.child_window(auto_id=aid, control_type="Button")
                            if btn.exists(timeout=2.0):
                                btn.click_input()
                                print(f"✅ 'Scan Coupon' screen skipped via {aid}.")
                                logger.log(
                                    f"✅ 'Scan Coupon' intermediate screen skipped ({aid} clicked).",
                                    status="pass"
                                )
                                time.sleep(2)
                                handled = True
                                break
                        except Exception:
                            continue
        except Exception:
            pass

        if not handled:
            break


def _log_payment_buttons(win):
    """
    Print all Button auto_ids visible on the payment screen.
    Useful for diagnosing which tender buttons are available.
    """
    print("🔍 Payment screen buttons:")
    try:
        for ctrl in win.descendants():
            try:
                if ctrl.element_info.control_type == "Button":
                    aid = ctrl.element_info.automation_id or ""
                    txt = ctrl.window_text()[:40]
                    if aid or txt:
                        print(f"   Button auto_id='{aid}' text='{txt}'")
            except Exception:
                continue
    except Exception as e:
        print(f"   (button dump failed: {e})")


def _dump_controls(win, screenshot_name):
    """
    Log all visible controls to help diagnose unknown screen layouts.
    Called only on failure.
    """
    try:
        print("=== Control dump for diagnostic purposes ===")
        for ctrl in win.descendants():
            try:
                print(
                    f"  type={ctrl.element_info.control_type}, "
                    f"auto_id='{ctrl.element_info.automation_id}', "
                    f"text='{ctrl.window_text()[:60]}'"
                )
            except Exception:
                continue
        print("=== End of control dump ===")
    except Exception as e:
        print(f"Control dump failed: {e}")
    logger.take_screenshot(screenshot_name)
