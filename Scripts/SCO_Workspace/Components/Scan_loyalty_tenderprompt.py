"""
Scan_loyalty_tenderprompt.py
----------------------------
Transitions the SCO from sale mode to the loyalty prompt, then scans the EDR
loyalty card at the loyalty prompt screen (BEFORE clicking CustomSkip).

Flow:
  1. Click PayButton to move from sale mode to the payment flow.
  2. Wait for the loyalty prompt (CustomSkip button) to appear.
  3. Scan the loyalty card barcode at the prompt (do NOT click CustomSkip first).
  4. Wait for loyalty acceptance indicators (points banner, choice offer popup).
  5. Set global_instance.is_loyaltycard_added = True.

Use this component for test scenarios where the loyalty card is scanned at
the tender-mode loyalty prompt (AFTER PayButton), e.g.:
    - TC_002: Registered card > 2000 pts (scan at loyalty prompt, then redeem)

This component handles the PayButton click — do NOT call move_to_tendermode()
before this function.

IMPORTANT: After this call succeeds, the SCO may show a choice offer popup
(ContainerButtonList). Call redeem_choice_offer() next to handle it, then
call complete_transaction() for the EFT payment.
"""

import sys
import time
import ctypes
import win32gui
from pathlib import Path
from pywinauto import timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.Add_item import _try_click_button, _resolve_wrapper, _handle_giftcard_activation
from Components.Scan_item import scan_item
from Components.report import logger

_user32 = ctypes.windll.user32
_VK_MENU = 0x12
_KEYEVENTF_KEYUP = 0x0002


def _focus_sco_window(win):
    try:
        hwnd = win.wrapper_object().handle
    except Exception:
        hwnd = None

    if hwnd:
        try:
            if win32gui.GetForegroundWindow() == hwnd:
                return
            _user32.keybd_event(_VK_MENU, 0, 0, 0)
            _user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)
            win32gui.SetForegroundWindow(hwnd)
            if win32gui.GetForegroundWindow() == hwnd:
                return
        except Exception:
            pass

    try:
        win.set_focus()
    except Exception:
        pass


def _idle_screen_visible(win):
    try:
        start_btn = win.child_window(auto_id="StartScanButton", control_type="Button")
        return start_btn.exists(timeout=0.2)
    except Exception:
        return False


def scan_loyalty_tenderprompt(card_code, require_acceptance=False):
    """
    Click PayButton, wait for the loyalty prompt, then scan the loyalty card.

    This is the tender-mode loyalty scan path. Distinct from sale-mode scan in
    Scan_loyalty_salemode.py. Use when the loyalty card should be presented at
    the loyalty prompt that appears after PayButton is clicked.

    Args:
        card_code (str): EDR loyalty card barcode to scan.

    Returns:
        bool: True if loyalty card was scanned (and likely accepted), False on error.
    """
    if not card_code or not str(card_code).strip():
        logger.log("❌ card_code is empty; cannot scan loyalty card at tender prompt.", status="fail")
        logger.take_screenshot("Scan_Loyalty_Prompt_Empty_CardCode")
        return False

    win = global_instance.win
    if win is None:
        logger.log(
            "❌ SCO window not initialised. Call login_pos() first.",
            status="fail"
        )
        logger.take_screenshot("Scan_Loyalty_Prompt_No_Win")
        return False

    card_code = str(card_code).strip()

    try:
        win.set_focus()
    except Exception:
        pass

    # --- Step 1: Dismiss any pending PopupFrame before clicking PayButton ---
    # The Bricks/collectable offer popup can appear slightly after the last item
    # scan, outside _handle_scan_popups' 0.4s window. If still present here,
    # it must be dismissed before PayButton or it will disrupt the loyalty flow.
    # Also handles gift card "Assistance Needed" (StoreLogin) if it follows.
    try:
        pframe_pre = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if pframe_pre.exists(timeout=0.5):
            list1_pre = win.child_window(auto_id="List1Button")
            if list1_pre.exists(timeout=0.3):
                list1_pre.click_input()
                time.sleep(0.5)
                print("✅ Pre-PayButton: dismissed Bricks/collectable popup (List1Button=Yes).")
                logger.log("✅ Pre-PayButton: Bricks popup dismissed (List1Button=Yes).", status="pass")
                # Gift card activation (StoreLogin → StoreButton1) may follow scam warning
                _handle_giftcard_activation(win)
    except Exception:
        pass

    # Also handle StoreLogin if it appeared without a preceding PopupFrame
    try:
        stl = win.child_window(auto_id="StoreLogin", control_type="Button")
        if stl.exists(timeout=0.5):
            logger.log("✅ Pre-PayButton: StoreLogin popup detected — handling.", status="pass")
            _handle_giftcard_activation(win)
    except Exception:
        pass

    # --- Step 2: Click PayButton to move to the payment/loyalty prompt ---
    print("➡️ Clicking PayButton to reach loyalty prompt...")
    logger.log("✅ Proceeding to payment to reach loyalty prompt.", status="pass")

    if not _try_click_button(win, "PayButton", timeout=5.0):
        logger.log(
            "❌ PayButton not found/clickable. Cannot reach loyalty prompt.",
            status="fail"
        )
        logger.take_screenshot("Scan_Loyalty_Prompt_PayButton_Not_Found")
        return False

    print("✅ PayButton clicked.")

    # --- Step 2: Wait for the loyalty prompt (CustomSkip) to appear ---
    # CustomSkip is the "skip / no card" button on the loyalty prompt screen.
    # We wait for it to confirm the prompt is visible, then scan without clicking it.
    def _loyalty_prompt_visible():
        return _resolve_wrapper(win, "CustomSkip", timeout=0.05) is not None

    try:
        timings.wait_until(10.0, 0.2, _loyalty_prompt_visible)
        print("✅ Loyalty prompt (CustomSkip) visible — scanning card...")
        logger.log("✅ Loyalty prompt screen detected.", status="pass")
    except timings.TimeoutError:
        logger.log(
            "⚠️ Loyalty prompt (CustomSkip) did not appear within 10 s. "
            "Attempting card scan anyway.",
            status="pass"
        )
        logger.take_screenshot("Scan_Loyalty_Prompt_CustomSkip_Timeout")

    # --- Step 3: Scan the loyalty card at the prompt ---
    scan_item(win, card_code, label="Loyalty card (tender prompt)")
    _focus_sco_window(win)
    time.sleep(0.5)

    # --- Step 4: Wait for loyalty card to be processed ---
    # For cards with >2000 points, the $10 redemption option appears as a
    # tender button on the payment selection screen (not as a popup here).
    # We wait briefly for any immediate popup (collectable offer, PopupFrame)
    # that some scenarios may show, then return so complete_transaction()
    # can handle the payment-screen tender selection.
    print("⏳ Waiting for Bricks popup or loyalty acceptance (up to 8 s)...")
    logger.log("⏳ Waiting up to 8 s for Bricks/loyalty popup after card scan.", status="pass")

    popup_appeared = False
    deadline = time.time() + 15          # extended: gift card activation adds ~5s
    while time.time() < deadline:
        # ContainerButtonList = choice offer popup (some scenarios only).
        try:
            popup = win.child_window(auto_id="ContainerButtonList", control_type="List")
            if popup.exists(timeout=0.1):
                popup_appeared = True
                print("✅ Choice offer popup (ContainerButtonList) detected.")
                logger.log(
                    f"✅ Loyalty card '{card_code}' accepted — ContainerButtonList visible.",
                    status="pass"
                )
                break
        except Exception:
            pass

        # Gift card activation: "Assistance Needed" popup with StoreLogin button.
        # Delegates to the shared _handle_giftcard_activation which uses a fully
        # dynamic, multi-strategy credential entry approach.
        try:
            store_login_btn = win.child_window(auto_id="StoreLogin", control_type="Button")
            if store_login_btn.exists(timeout=0.1):
                print("✅ Gift card 'Assistance Needed' popup — handling activation.")
                logger.log("✅ StoreLogin popup detected — handling gift card activation.", status="pass")
                _handle_giftcard_activation(win)
                # Extend deadline so the choice-offer popup still has time to appear
                deadline = max(deadline, time.time() + 12)
                continue
        except Exception:
            pass

        # Bricks / collectable offer popup (confirmed live auto_ids):
        #   PopupFrame (Pane) present AND List1Button (Yes) present on win
        # IMPORTANT: search List1Button on win directly (not on pframe child),
        # matching the same pattern that works in Add_item._handle_scan_popups.
        try:
            pframe = win.child_window(auto_id="PopupFrame", control_type="Pane")
            if pframe.exists(timeout=0.1):
                # Search List1Button on win (not pframe) — more reliable across WPF nesting
                list1 = win.child_window(auto_id="List1Button", control_type="Button")
                if list1.exists(timeout=0.3):
                    popup_appeared = True
                    print("✅ Bricks/collectable offer popup — clicking Yes (List1Button).")
                    logger.log(
                        f"✅ Loyalty card '{card_code}' accepted — "
                        "Bricks popup dismissed (List1Button=Yes).",
                        status="pass"
                    )
                    list1.click_input()
                    time.sleep(0.4)
                    break

                # Fallback: older popup button patterns
                for real_btn in ["RedeemButton", "SkipCollectableOfferPrompt"]:
                    child = pframe.child_window(auto_id=real_btn)
                    if child.exists(timeout=0.05):
                        popup_appeared = True
                        print(f"✅ Offer popup (PopupFrame/{real_btn}) detected.")
                        logger.log(
                            f"✅ Loyalty card '{card_code}' accepted — "
                            f"PopupFrame/{real_btn} visible.",
                            status="pass"
                        )
                        break
                if popup_appeared:
                    break
        except Exception:
            pass

        time.sleep(0.1)

    if not popup_appeared:
        if _idle_screen_visible(win):
            logger.log(
                f"❌ SCO returned to the welcome screen after scanning loyalty card '{card_code}'. "
                "The active transaction is no longer available.",
                status="fail",
            )
            print("❌ SCO returned to welcome screen after loyalty scan.")
            logger.take_screenshot("Scan_Loyalty_Prompt_Returned_To_Welcome")
            return False

        try:
            skip_btn = win.child_window(auto_id="CustomSkip", control_type="Button")
            if skip_btn.exists(timeout=0.5):
                logger.log(
                    f"❌ Loyalty prompt still visible after scanning card '{card_code}'. "
                    "Card was not accepted by SCO.",
                    status="fail",
                )
                print("❌ Loyalty prompt still visible after card scan — card not accepted.")
                logger.take_screenshot("Scan_Loyalty_Prompt_Card_Not_Accepted")
                return False
        except Exception:
            pass

        print("ℹ️ No immediate popup — redemption likely offered at payment screen.")
        logger.log(
            "ℹ️ No ContainerButtonList/PopupFrame popup after loyalty scan. "
            "Redemption may appear as a tender option on the payment screen.",
            status="pass"
        )
        logger.take_screenshot("Scan_Loyalty_No_Offer_Popup")  # diagnose what's on screen
        accepted = _verify_loyalty_accepted(win, card_code)
        if require_acceptance and not accepted:
            logger.log(
                f"❌ Loyalty card '{card_code}' was scanned, but no accepted/active "
                "transaction indicator was found.",
                status="fail",
            )
            logger.take_screenshot("Scan_Loyalty_Prompt_Not_Accepted")
            return False

    global_instance.is_loyaltycard_added = True
    return True


def _verify_loyalty_accepted(win, card_code):
    """Check for loyalty acceptance indicators after scanning at the tender prompt."""
    if _idle_screen_visible(win):
        logger.log(
            f"❌ Loyalty card '{card_code}' could not be verified because SCO is on the welcome screen.",
            status="fail",
        )
        return False

    indicators = [
        ("WoWRewardPoints",   "Text"),   # Points balance visible after acceptance
        ("Loyaltyregistered", "Text"),   # "Registered" status label
        # NOTE: RewardTextBlock ('Current Rewards Balance') is ALWAYS present in the
        # SCO sidebar even at idle — do NOT use it as a loyalty-accepted indicator.
    ]

    for auto_id, ctrl_type in indicators:
        try:
            elem = win.child_window(auto_id=auto_id, control_type=ctrl_type)
            if elem.exists(timeout=2):
                indicator_text = ""
                try:
                    indicator_text = elem.window_text()
                except Exception:
                    pass
                logger.log(
                    f"✅ Loyalty card '{card_code}' accepted at tender prompt. "
                    f"Indicator '{auto_id}': '{indicator_text}'.",
                    status="pass"
                )
                return True
        except Exception:
            continue

    logger.log(
        f"ℹ️ Loyalty card '{card_code}' scanned at tender prompt. "
        "No immediate indicator — EE log will confirm acceptance.",
        status="info"
    )
    return False
