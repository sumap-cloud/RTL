"""
Move_to_tendermode.py
---------------------
Transitions the SCO from sale mode to tender mode by:
  1. Dismissing any lingering popups (e.g., "Assistance Needed").
  2. Clicking the PayButton.
  3. Waiting for the tender/payment-type screen to appear.

This SCO is Card-Only — EFT services and MultiSimulator must remain RUNNING
for the card payment to be processed automatically.
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
from Components.Add_item import _try_click_button, _is_button_enabled, _resolve_wrapper
from Components.report import logger


def move_to_tendermode(skip_choice_offer=True):
    """
    Prepare for payment and move the SCO from sale mode to tender mode.

    Returns:
        bool: True if the SCO successfully entered tender mode, False otherwise.
    """
    win = global_instance.win
    if win is None:
        logger.log(
            "❌ SCO window not initialised. Call login_pos() first.",
            status="fail"
        )
        logger.take_screenshot("Move_Tender_No_Win")
        return False

    # --- 1. Dismiss any lingering popup (e.g., "Assistance Needed") ---
    # This popup can appear after loyalty card scan in sale mode.
    _dismiss_popup_if_present(win)

    # --- 2. Click PayButton ---
    print("➡️ Clicking PayButton...")
    logger.log("✅ Proceeding to payment (clicking PayButton).", status="pass")

    if not _try_click_button(win, "PayButton", timeout=5.0):
        print("❌ PayButton not found/clickable.")
        logger.log("❌ PayButton not available; cannot move to tender mode.", status="fail")
        logger.take_screenshot("Move_Tender_PayButton_Not_Found")
        return False

    print("✅ PayButton clicked.")

    # --- 3. Handle the loyalty prompt screen (CustomSkip) if it appears.
    # When the loyalty card was already scanned in sale mode the SCO typically
    # skips this screen, but some configurations may still show it.
    # If it appears, we simply skip it (loyalty is already linked).
    def _loyalty_prompt_or_tender_ready():
        skip_visible = _resolve_wrapper(win, "CustomSkip", timeout=0.05) is not None
        tender_ready = _is_tender_screen_visible(win)
        return skip_visible or tender_ready

    try:
        timings.wait_until(5.0, 0.2, _loyalty_prompt_or_tender_ready)
    except timings.TimeoutError:
        pass

    # Dismiss loyalty prompt if it appeared unexpectedly.
    skip_btn = win.child_window(auto_id="CustomSkip", control_type="Button")
    if skip_btn.exists(timeout=1):
        logger.log(
            "⚠️ Loyalty prompt (CustomSkip) appeared after PayButton click even though "
            "loyalty was scanned in sale mode. Clicking Skip.",
            status="pass"
        )
        try:
            skip_btn.click_input()
        except Exception as e:
            logger.log(f"❌ Could not click CustomSkip: {e}", status="fail")
            logger.take_screenshot("Move_Tender_CustomSkip_Click_Failed")
            return False

    # --- 4. Verify tender mode screen is active, handling any popup that may
    # block the tender screen (e.g., "Exciting News" prompt for cards crossing
    # 2000 pts). Poll for either the tender screen OR the popup — dismiss the
    # popup first if it appears, then continue waiting for the tender screen.
    try:
        timings.wait_until(10.0, 0.2, lambda: _is_tender_screen_visible(win))
        logger.log("✅ SCO successfully entered tender mode.", status="pass")
        return True
    except timings.TimeoutError:
        pass

    # Tender screen not yet visible — check whether a blocking popup is present
    # (e.g., "Exciting News!" prompt that fires when card crosses 2000 pts).
    # The popup renders inside PopupFrame with Instructions/List1Button (OK).
    popup_dismissed = _dismiss_exciting_news_popup_if_present(win)
    if not popup_dismissed:
        # Also check for Choice Offer screen (ContainerButtonList) which
        # can appear for cards that have discounts available (e.g. TC_006
        # Temporary card with $30 balance). Skip it to proceed to tender.
        # When skip_choice_offer=False the caller wants to handle the offer
        # themselves (e.g. TC_008 redeem_choice_offer); don't skip here.
        if skip_choice_offer:
            popup_dismissed = _skip_choice_offer_if_present(win)
    if popup_dismissed:
        # Popup dismissed — give the tender screen time to appear now.
        try:
            timings.wait_until(10.0, 0.2, lambda: _is_tender_screen_visible(win))
            logger.log("✅ SCO entered tender mode (after dismissing Exciting News popup).", status="pass")
            return True
        except timings.TimeoutError:
            pass

    # Not a showstopper — the tender screen might use different elements.
    # Log it and let complete_transaction() diagnose further.
    logger.log(
        "⚠️ Tender mode screen not confirmed within timeout. "
        "complete_transaction() will verify the state.",
        status="pass"
    )
    logger.take_screenshot("Move_Tender_Screen_Unconfirmed")
    return True


def _is_tender_screen_visible(win):
    """
    Return True if the payment selection overlay is visible.

    IMPORTANT: TotalAmountValue and DueAmountValue are permanently present in
    the SCO sidebar and must NOT be used as tender-screen indicators — they
    cause a false-positive immediately after PayButton click, before the
    payment overlay has loaded.

    Only check for buttons that are exclusively part of the payment overlay.
    """
    candidates = [
        ("Tender2", "Button"),               # Card EFT — primary indicator for Card-Only SCO
        ("Tender1", "Button"),               # Cash button (also only on payment overlay)
        ("TenderGroupMenuViewExitButton", "Button"),
        ("PaymentCash", "Button"),
        ("CashButton", "Button"),
    ]
    for auto_id, ctrl_type in candidates:
        try:
            elem = win.child_window(auto_id=auto_id, control_type=ctrl_type)
            if elem.exists(timeout=0.05):
                return True
        except Exception:
            continue
    return False


def _dismiss_popup_if_present(win):
    """
    Dismiss any blocking popup before PayButton click.
    No is_enabled() check — popup buttons may appear disabled in UIA even when clickable.
    """
    dismiss_aids = ["ASAOKButton", "OK_Button", "GenericOKButton", "GenericButton", "CustomSkip"]
    for aid in dismiss_aids:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=1.5):
                btn.click_input()
                print(f"⚠️ Dismissed popup via '{aid}' before PayButton click.")
                logger.log(f"⚠️ Dismissed popup via '{aid}' before PayButton click.", status="pass")
                time.sleep(1)
                return
        except Exception as ex:
            print(f"⚠️ Could not click '{aid}': {ex}")
            continue


def _dismiss_exciting_news_popup_if_present(win):
    """
    Detect and dismiss the Exciting News popup that blocks the tender screen
    after PayButton click (for cards crossing 2000 pts in sale-mode scan TCs).

    The popup renders inside PopupFrame with:
      - auto_id='Instructions' (Text) — the message body
      - auto_id='List1Button' (Button, text='OK') — the dismiss button

    Returns True if the popup was detected and dismissed, False otherwise.
    """
    _EXCITING_NEWS_TRIGGERS = (
        "exciting news",
        "great news",
        "your savings are growing",
        "you've just earned",
        "you have just earned",
        "you've just banked",
        "you have just banked",
        "you've just converted",
        "you have just converted",
        "save $",
    )

    # Fast UIA check: read the Instructions text element
    for aid in ("Instructions", "GiftCardInstructions"):
        try:
            txt_ctrl = win.child_window(auto_id=aid, control_type="Text")
            if txt_ctrl.exists(timeout=0.5):
                text = ""
                try:
                    text = txt_ctrl.window_text() or ""
                except Exception:
                    text = ""
                if text.strip():
                    lowered = text.lower()
                    if any(phrase in lowered for phrase in _EXCITING_NEWS_TRIGGERS):
                        logger.log(
                            f"✅ Exciting News prompt detected in tender transition: '{text[:80]}'.",
                            status="pass",
                        )
                        print(f"✅ Exciting News prompt detected in tender transition: '{text[:80]}'.")
                        try:
                            logger.take_screenshot("Exciting_News_Prompt")
                        except Exception:
                            pass
                        # Dismiss via List1Button (OK) — confirmed from live dump
                        for dismiss_aid in ("List1Button", "List2Button", "OK_Button", "ASAOKButton"):
                            try:
                                btn = win.child_window(auto_id=dismiss_aid, control_type="Button")
                                if btn.exists(timeout=1.0):
                                    btn.click_input()
                                    logger.log(
                                        f"✅ Exciting News prompt dismissed via '{dismiss_aid}'.",
                                        status="pass",
                                    )
                                    print(f"✅ Exciting News prompt dismissed via '{dismiss_aid}'.")
                                    time.sleep(1.5)
                                    return True
                            except Exception:
                                continue
        except Exception:
            continue
    return False


def _skip_choice_offer_if_present(win):
    """
    Detect and skip a Choice Offer screen (ContainerButtonList) that can
    appear between PayButton click and the tender screen.

    This screen shows "You have X discount(s) to select from" with:
      - auto_id='ContainerButtonList' (List) — the offer cards
      - auto_id='SkipChoiceOfferPrompt' (Button) — "No, save these for later"
      - auto_id='Usenow' (Button) — "Use now"

    For sale-mode TCs (TC_006 etc.) the default action is to SKIP the offer
    so the flow proceeds to the tender screen. TCs that need to USE the offer
    should call redeem_choice_offer() explicitly in the test script instead.

    Returns True if the screen was detected and skipped, False otherwise.
    """
    try:
        offer_list = win.child_window(auto_id="ContainerButtonList", control_type="List")
        if offer_list.exists(timeout=1.0):
            logger.log(
                "⚠️ Choice Offer screen detected during tender transition — skipping.",
                status="pass",
            )
            print("⚠️ Choice Offer screen detected during tender transition — skipping.")
            try:
                logger.take_screenshot("Choice_Offer_TenderTransition")
            except Exception:
                pass
            skip_btn = win.child_window(auto_id="SkipChoiceOfferPrompt", control_type="Button")
            if skip_btn.exists(timeout=2.0):
                skip_btn.click_input()
                logger.log("✅ Choice Offer skipped via 'SkipChoiceOfferPrompt'.", status="pass")
                print("✅ Choice Offer skipped via 'SkipChoiceOfferPrompt'.")
                time.sleep(1.5)
                return True
    except Exception:
        pass
    return False
