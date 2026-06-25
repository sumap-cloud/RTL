"""
Move_back_to_salemode.py
-------------------------
Transitions the SCO from tender/loyalty mode BACK to sale mode so that
additional items can be scanned mid-transaction.

Used by scenarios that require:
  - Scanning extra items after initial loyalty scan (e.g., Tiered Spend TCs).
  - Returning to the basket view after verifying offers in tender mode.

TODO: Identify the exact button auto_id from a live NCR SCO control dump.
      Candidate possibilities:
        - "GoBack" / "BackButton" / "CancelButton" / "AddMoreItems"
        - "ReturnToSale" / "ScanMoreItems"

Once identified, replace the placeholder logic below.
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


# Known candidate button auto_ids for "go back to sale mode" on NCR SCO.
# These will be tried in order; the first one found and clickable wins.
_BACK_BUTTON_CANDIDATES = [
    "GoBackBtn",        # ← confirmed from live NCR SCO control dump
    "CancelButton",
    "GoBack",
    "BackButton",
    "AddMoreItems",
    "ReturnToSale",
    "ScanMoreItems",
    "Back",
]


def move_back_to_salemode():
    """
    Attempt to move the SCO from tender/loyalty mode back to sale mode.

    Returns:
        bool: True if the SCO returned to sale mode (scan mode indicators
              detected), False otherwise.
    """
    win = global_instance.win
    if win is None:
        logger.log(
            "❌ SCO window not initialised. Cannot move back to sale mode.",
            status="fail"
        )
        return False

    try:
        win.set_focus()
    except Exception:
        pass

    # Try each candidate button
    clicked = False
    for aid in _BACK_BUTTON_CANDIDATES:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=2.0):
                btn.click_input()
                print(f"✅ Clicked '{aid}' to move back to sale mode.")
                logger.log(f"✅ Clicked '{aid}' to move back to sale mode.", status="pass")
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        logger.log(
            "❌ Could not find a 'back to sale mode' button. "
            f"Tried: {_BACK_BUTTON_CANDIDATES}. "
            "Update _BACK_BUTTON_CANDIDATES with the correct auto_id from a live dump.",
            status="fail"
        )
        logger.take_screenshot("Move_Back_SaleMode_Button_Not_Found")
        return False

    # Wait for sale mode indicators (item scan area / PayButton visible)
    time.sleep(2)
    try:
        pay_btn = win.child_window(auto_id="PayButton", control_type="Button")
        timings.wait_until(10.0, 0.3, lambda: pay_btn.exists(timeout=0.1))
        logger.log("✅ SCO returned to sale mode (PayButton available).", status="pass")
        print("✅ SCO returned to sale mode.")
        return True
    except timings.TimeoutError:
        logger.log(
            "⚠️ PayButton not detected after clicking back button. "
            "Sale mode return unconfirmed.",
            status="fail"
        )
        logger.take_screenshot("Move_Back_SaleMode_Unconfirmed")
        return False
