import sys
import time
import ctypes
import re
from pathlib import Path

import win32gui
from pywinauto.timings import Timings
from pywinauto import Application, timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.Ensure_EFTSimulator_closed import ensure_EFTSimulator_closed
from Components.Ensure_services_stopped import ensure_services_stopped, SERVICES_TO_STOP
from Components.Add_item import _handle_continue_popup, _try_click_button, _resolve_wrapper, scan_item
from Components.report import logger



def add_loyalty_card(card_code):
        
    try:
        win = global_instance.win

        ensure_EFTSimulator_closed()

        ensure_services_stopped(SERVICES_TO_STOP)


        logger.log("✅ Proceeding to payment...", status="pass")
        # Dismiss any "Do you wish to continue" popup that may be blocking PayButton.
        # _handle_continue_popup(win, timeout=0.2)

        if not _try_click_button(win, "PayButton", timeout=1.0):
            logger.log("❌ PayButton not available; aborting payment step.", status="fail")
            logger.take_screenshot("PayButton_Not_Available")
            return

        # Wait briefly for the payment screen's CustomSkip button to appear;
        # keep dismissing the continue-popup if it shows up during the wait,
        # and retry the Pay click once if needed.
        def _payment_ready():
            # _handle_continue_popup(win, timeout=0.05)
            return _resolve_wrapper(win, "CustomSkip", timeout=0.05) is not None

        try:
            timings.wait_until(3.0, 0.1, _payment_ready)
        except timings.TimeoutError:
            # Retry Pay once in case the first click was eaten by a popup.
            _try_click_button(win, "PayButton", timeout=0.5)
            try:
                timings.wait_until(3.0, 0.1, _payment_ready)
            except timings.TimeoutError:
                logger.log("❌ CustomSkip button not found; cannot scan card code.", status="fail")
                logger.take_screenshot("CustomSkip_Button_Not_Found")
                return

        scan_item(win, card_code, label="Card number")
        global_instance.is_loyaltycard_added = True
        logger.log("✅ Card code scanned successfully.", status="pass")





    except Exception as e:
        print(f"Error in add_loyalty_card: {e}")
        logger.log(f"Error in add_loyalty_card: {e}", status="fail")
        logger.take_screenshot("Add_Loyalty_Card_Error")