# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: handle_refund_screen
# @Purpose: Manages refund confirmation screens and tender selection
# @Dependencies: pywinauto.Application, ElementNotFoundError, TimeoutError
# @Input_Params: expected_tender
# @Return_Values: Boolean success/failure of refund process
# @Used_By_Tests: TC008_nrr_scenario, TC007_department_return, TC006_TBR_forceQTY
# @Known_Limitations: Requires specific UI state, depends on tender type availability
# ============================================

"""
================================================================================
 Refund Confirmation Screen Handler
================================================================================

PURPOSE:
--------
This module handles the final refund confirmation pop-up window.

The main function, `handle_refund_screen`, provides a single entry point to:
1. Connect to the refund pop-up window.
2. Check the current tender against an expected tender.
3. If they match, it confirms the refund.
4. If they don't match, it clicks 'Switch Tender' and calls the handler
   for the next screen to select the correct tender.

"""

import re
import time
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError
import sys
from pathlib import Path


# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
    
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from .switchtender_tbr import handle_select_tender_screen
from Components.Common_components.Approvalrequired import handle_approval_popup
def handle_refund_screen(expected_tender=None):
    """
    Connects to the refund confirmation window, checks the current tender, and
    either confirms it or switches to the expected tender.

    Args:
        expected_tender (str, optional): The name of the desired tender (e.g., 'Cash').
                                         If None, the function will confirm the default
                                         tender shown on the screen.

    Returns:
        dict or None: A dictionary with refund details if successful, otherwise None.
    """
    print("\n--- Handling Refund Confirmation Screen ---")
    window_title_regex = ".*ConfirmDefaultTenderForRefundViewModelOverride.*"

    try:
        print(f"Attempting to connect to window: '{window_title_regex}'...")
        app = Application(backend="uia").connect(title_re=window_title_regex, timeout=15)
        win = app.window(title_re=window_title_regex)
        win.set_focus()
        print("✅ Successfully connected to the refund window.")
    except (ElementNotFoundError, TimeoutError):
        print("❌ ERROR: Refund confirmation window not found.")
        return None

    try:
        # --- Data Capture ---
        refund_details = {
            "title": "N/A",
            "tender_type": "N/A",
            "amount": "N/A"
        }
        
        # Capture tender details from the screen
        tender_list_item = win.child_window(control_type="ListItem")
        tender_text = tender_list_item.child_window(control_type="Text").window_text()
        refund_details['tender_type'] = tender_text.replace(':', '').strip()
        
        print(f"\n--- Captured Refund Details: Tender is '{refund_details['tender_type']}' ---")

        # --- Conditional Logic ---
        current_tender = refund_details['tender_type']

        # If expected tender matches current (or none specified), confirm it.
        if expected_tender is None or current_tender.lower() == expected_tender.lower():
            print(f"✅ Current tender '{current_tender}' is as expected. Clicking 'Confirm'...")
            confirm_button = win.child_window(title="Confirm", control_type="Button")
            if confirm_button and confirm_button.exists():
                confirm_button.click_input()
                print("✅ 'Confirm' button clicked successfully.")
                return refund_details
            else:
                print("❌ ERROR: Could not find the 'Confirm' button.")
                return None
        else:
            # If tenders do not match, switch it.
            print(f"⚠️ Current tender '{current_tender}' does not match expected '{expected_tender}'. Switching...")
            switch_button = win.child_window(title="Switch Tender", control_type="Button")
            if switch_button and switch_button.exists():
                switch_button.click_input()
                print("✅ 'Switch Tender' button clicked.")
                handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234")
                time.sleep(2) # Wait for the next screen to appear

                # Call the handler for the "Select Tender" screen
                select_result = handle_select_tender_screen(tender_to_select=expected_tender)
                
                if select_result:
                    print("✅ Tender switched successfully.")
                    return refund_details
                else:
                    print(f"❌ Failed to select '{expected_tender}' on the next screen.")
                    return None
            else:
                print("❌ ERROR: Could not find 'Switch Tender' button.")
                return None

    except Exception as e:
        print(f"❌ An unexpected error occurred on the refund screen: {e}")
        return None

# ==============================================================================
#  EXECUTABLE BLOCK FOR STANDALONE TESTING
# ==============================================================================
if __name__ == "__main__":
    print("--- Running Refund Screen Handler in standalone mode for testing ---")
    
    # --- TEST CASE 1: Expected tender requires switching (e.g., to 'Cash') ---
    # This assumes the popup shows 'EFT' by default.
    print("\n--> Test Case 1: Expected tender requires a switch (to 'Cash').")
    print("    (Please ensure the Refund Confirmation window is open)")
    time.sleep(4)
    result_switch = handle_refund_screen(expected_tender='Cash')
    if result_switch:
        print("\n✅ Test Case 1 completed successfully.")
    else:
        print("\n❌ Test Case 1 failed.")

    # # --- TEST CASE 2: Expected tender matches current tender (e.g., EFT) ---
    # # This assumes you have closed and reopened the refund window for the second test.
    # print("\n--> Test Case 2: Expected tender matches current tender ('EFT'). Should click 'Confirm'.")
    # print("    (Please ensure the Refund Confirmation window is open again)")
    # time.sleep(4)
    # result_confirm = handle_refund_screen(expected_tender='EFT')
    # if result_confirm:
    #     print("✅ Test Case 2 completed successfully.")
    # else:
    #     print("❌ Test Case 2 failed.")

