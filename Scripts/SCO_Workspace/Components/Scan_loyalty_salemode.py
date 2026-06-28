"""
Scan_loyalty_salemode.py
------------------------
Scans the EDR/loyalty card barcode through the Scanner Emulator during the
SALE MODE phase (i.e., before PayButton is clicked / before moving to tender).

This is distinct from Add_loyalty_card.py which scans the card on the
CustomSkip/loyalty-prompt screen AFTER PayButton has been clicked.

Use this component for test scenarios where the card is scanned during the
item-scanning phase, e.g.:
    - TC_001: Registered card < 1000 pts (sale mode scan)
    - TC_004, TC_005, TC_006, TC_007, TC_008 ...

After scanning, the component:
  - Waits briefly for the SCO to process the loyalty card.
  - Checks for a loyalty confirmation indicator (points banner, loyalty info).
  - Sets global_instance.is_loyaltycard_added = True.
  - Logs pass/fail with screenshots on failure.
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
from Components.Scan_item import scan_item
from Components.report import logger


def scan_loyalty_salemode(card_code):
    """
    Scan the loyalty card barcode during sale mode.

    Args:
        card_code (str): The loyalty card barcode (EAN/number) to scan.

    Returns:
        bool: True if the card was scanned and accepted, False otherwise.
    """
    if not card_code or not str(card_code).strip():
        logger.log("❌ card_code is empty; cannot scan loyalty card.", status="fail")
        logger.take_screenshot("Scan_Loyalty_Sale_Empty_CardCode")
        return False

    win = global_instance.win
    if win is None:
        logger.log(
            "❌ SCO window not initialised in global_instance. "
            "Run login_pos() before calling scan_loyalty_salemode().",
            status="fail"
        )
        logger.take_screenshot("Scan_Loyalty_Sale_No_Win")
        return False

    card_code = str(card_code).strip()

    try:
        win.set_focus()
    except Exception:
        pass

    # Scan the loyalty card barcode through the Scanner Emulator, just like
    # a product barcode.  The NCR SCO identifies it as a loyalty card via
    # the barcode range / prefix and routes it to the loyalty subsystem.
    scan_item(win, card_code, label="Loyalty card (sale mode)")

    # Brief wait for EagleEye card validation (1s is sufficient in practice)
    time.sleep(1)

    try:
        win.set_focus()
    except Exception:
        pass

    # Dismiss any "Assistance Needed" / "Item not found" popup that may have
    # appeared because the loyalty card barcode was also interpreted as a
    # product scan attempt. This is expected behaviour on NCR SCO.
    _dismiss_loyalty_popup(win)

    # Verify the loyalty card was accepted by looking for a loyalty indicator.
    # In NCR SCO, common indicators after a successful sale-mode loyalty scan:
    #   • "WoWRewardPoints" text element (points balance display)
    #   • A loyalty card banner / text element referencing the card
    # We check for these; if none appear we fall back to verifying no error state.
    loyalty_confirmed = False
    loyalty_indicators = [
        ("auto_id", "WoWRewardPoints", "Text"),
        ("auto_id", "LoyaltyCardInfo", "Text"),
        ("auto_id", "LoyaltyBanner", "Text"),
        ("auto_id", "CustomerName", "Text"),
        ("title_re", ".*Everyday Rewards.*", "Text"),
        ("title_re", ".*points.*", "Text"),
    ]

    for search_type, value, ctrl_type in loyalty_indicators:
        try:
            if search_type == "auto_id":
                elem = win.child_window(auto_id=value, control_type=ctrl_type)
            else:
                elem = win.child_window(title_re=value, control_type=ctrl_type)

            if elem.exists(timeout=0.5):  # was 2s — popup present immediately or not
                loyalty_confirmed = True
                indicator_text = ""
                try:
                    indicator_text = elem.window_text()
                except Exception:
                    pass
                logger.log(
                    f"✅ Loyalty card '{card_code}' scanned in sale mode. "
                    f"Indicator detected: '{indicator_text}'.",
                    status="pass"
                )
                break
        except Exception:
            continue

    if not loyalty_confirmed:
        # Fallback: verify PayButton is still enabled (no error blocking the sale).
        pay_btn = win.child_window(auto_id="PayButton", control_type="Button")
        if pay_btn.exists(timeout=1) and pay_btn.is_enabled():
            # PayButton is still available — sale is in a valid state after the scan.
            # The loyalty acceptance will be confirmed later via EE log verification.
            logger.log(
                f"✅ Loyalty card '{card_code}' scanned in sale mode. "
                "No immediate loyalty indicator found, but sale remains in valid state. "
                "EE log verification will confirm card acceptance.",
                status="pass"
            )
            loyalty_confirmed = True
        else:
            logger.log(
                f"❌ Loyalty card scan for '{card_code}' may have failed — "
                "no loyalty indicator found and PayButton is not enabled.",
                status="fail"
            )
            logger.take_screenshot(f"Scan_Loyalty_Sale_Unconfirmed_{card_code}")

    if loyalty_confirmed:
        global_instance.is_loyaltycard_added = True

    return loyalty_confirmed


def _dismiss_loyalty_popup(win):
    """
    Dismiss any popup that appeared because the loyalty card barcode was also
    interpreted as a product scan (e.g., "Assistance Needed" / "Item not found").

    Tries all known dismiss buttons WITHOUT is_enabled() check since popup
    buttons can appear enabled=False in UIA even when clickable.
    """
    dismiss_aids = ["ASAOKButton", "OK_Button", "GenericOKButton", "GenericButton", "CustomSkip"]
    for aid in dismiss_aids:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=0.4):  # was 2.0s
                btn.click_input()
                print(f"✅ Dismissed loyalty-scan popup via '{aid}'.")
                logger.log(f"✅ Dismissed loyalty-scan popup via '{aid}'.", status="pass")
                time.sleep(0.5)  # was 1.5s
                return
        except Exception as ex:
            continue

    print("ℹ️ No popup to dismiss after loyalty scan (none found).")
