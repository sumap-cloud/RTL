# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: paidout_Navigation
# @Purpose: Navigates to the Funds Management -> Paid Out section in POS
# @Dependencies: pywinauto.application.Application, TimeoutError, MatchError
# @Input_Params: app_title - Window title to connect to
# @Return_Values: Boolean success/failure of navigation
# @Used_By_Tests: TC001_paidout, Other funds management tests
# @Known_Limitations: Requires specific UI state and button availability
# ============================================

# File: pos_automation.py

import time
from pywinauto.application import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError

def paidout_Navigation(app_title=".*R10PosClient.*"):
    """
    Automates the process of navigating to 'Funds Management' and then to 'Paid Out'
    in a Point of Sale (POS) application, handling an approval popup.

    Args:
        app_title (str): A regular expression for the title of the application window to connect to.

    Returns:
        bool: True if the automation completes successfully, False otherwise.
    """
    # --- Define Expected Buttons ---
    expected_main_menu_buttons = [
        "Rain Check", "Recall Transaction", "Reprint Receipt", "Reprint Last", "Lock",
        "Balance Enquiry", "User Barcode", "Cash Withdrawal", "Log Off",
        "Department Sale", "EMV Report", "Price Enquiry", "EFT Log On", "Report Abuse",
        "Software Verification", "Reset Hardware", "Change Order Request", "Pick Up Voucher",
        "Item Search", "Returns", "Funds Management", "Lotteries & Lotto Payout",
        "Parcel Pickup", "Home Delivery", "No Sale"
    ]

    expected_funds_management_buttons = [
        "Go Back", "PoS Declaration", "Tender Correction", "Paid Out", "Paid In",
        "Pick Up at PoS", "Tender Loan"
    ]

    try:
        # --- Step 1: Connect to the Application ---
        print(f"Attempting to connect to '{app_title}'...")
        app = Application(backend="uia").connect(title_re=app_title, timeout=20)
        win = app.window(title_re=app_title)
        win.restore()
        win.set_focus()
        print("Successfully connected to the window.")

        # --- Step 2: Find and Click the Expand Button ---
        expand_button_id = 'TransactionCommandListButtonsViewExpandButtonID'
        collapse_button_id = 'TransactionCommandListButtonsViewCollapseButton'
        
        print(f"\nLooking for expand button with auto_id: '{expand_button_id}'")
        
        try:
            expand_button = win.child_window(auto_id=expand_button_id, control_type="Button")
            
            if expand_button.is_visible():
                print("Expand button found. Clicking to open the menu...")
                expand_button.click()
                time.sleep(1)

                # --- Step 3: Verify Expansion and Validate Main Menu Buttons ---
                collapse_button = win.child_window(auto_id=collapse_button_id, control_type="Button")
                if not collapse_button.is_visible():
                    print("Error: Clicked the expand button, but the menu does not appear to be open.")
                    return False

                print("Menu expanded successfully.")
                
                # --- Main Menu Button Validation ---
                print("\n--- Validating Main Menu Buttons ---")
                buttons = win.descendants(control_type="Button")
                visible_buttons = [b.window_text() for b in buttons if b.is_visible() and b.window_text()]
                missing_buttons = [btn for btn in expected_main_menu_buttons if btn not in visible_buttons]

                if not missing_buttons:
                    print("All expected main menu buttons are visible.")
                else:
                    print(f"Warning: The following buttons were not found: {missing_buttons}")
                print("---------------------------------")
                
                # --- Step 4: Click "Funds Management" Button ---
                print("\n--- Clicking 'Funds Management' Button ---")
                funds_button = win.child_window(title="Funds Management", control_type="Button").wait('enabled', timeout=10)
                print("Found 'Funds Management' button. Clicking it...")
                funds_button.click()
                time.sleep(1)

                # --- Funds Management Button Validation ---
                print("\n--- Validating Funds Management Buttons ---")
                fm_buttons = win.descendants(control_type="Button")
                fm_visible_buttons = [b.window_text() for b in fm_buttons if b.is_visible() and b.window_text()]
                fm_missing_buttons = [btn for btn in expected_funds_management_buttons if btn not in fm_visible_buttons]

                if not fm_missing_buttons:
                    print("All expected funds management buttons are visible.")
                else:
                    print(f"Warning: The following funds management buttons were not found: {fm_missing_buttons}")
                print("---------------------------------")
                
                # --- Step 5: Click "Paid Out" Button ---
                print("\n--- Clicking 'Paid Out' Button ---")
                paid_out_button = win.child_window(title="Paid Out", control_type="Button").wait('enabled', timeout=10)
                print("'Paid Out' button is enabled. Clicking it...")
                paid_out_button.click()
                time.sleep(1) # Wait for popup

                # --- Step 6: Handle "Approval Required" Popup for Paid Out ---
                print("\n--- Handling 'Approval Required' Popup for Paid Out ---")
                approval_dialog = app.window(title_re=".*Approval.*", top_level_only=True).wait('ready', timeout=20)
                print(f"Popup window found with title: '{approval_dialog.window_text()}'")

                print("Entering credentials for Paid Out...")
                edit_controls = approval_dialog.descendants(control_type="Edit")
                if len(edit_controls) < 2:
                    print("Error: Could not find the required username/password fields on the popup.")
                    return False
                
                edit_controls[0].set_text("atmgr5")
                edit_controls[1].set_text("abcd1234")
                
                # --- FIX: Find the OK button using descendants ---
                # The 'child_window' method is not available on the UIAWrapper object.
                # We find the button the same way we found the edit fields.
                ok_buttons = approval_dialog.descendants(title="OK", control_type="Button")
                if ok_buttons:
                    ok_button = ok_buttons[0] # Get the first match
                    if ok_button.is_enabled():
                        print("Clicking 'OK' button...")
                        ok_button.click()
                        print("Paid Out credentials submitted successfully.")
                    else:
                        print("Error: 'OK' button is not enabled.")
                        return False
                else:
                    print("Error: Could not find the 'OK' button on the popup.")
                    return False

            else:
                print("Expand button is not visible. The menu might already be open.")
                # If the menu is already open, you might want to continue the script.
                # This part can be adjusted based on the application's behavior.

        except (TimeoutError, MatchError) as e:
            print(f"Error finding or interacting with a UI element: {e}")
            return False

    except (TimeoutError, MatchError) as e:
        print(f"Could not connect to the application. Please ensure it is running. Error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

    print("\nAutomation script finished successfully.")
    return True

# This block allows you to run this script directly for testing
if __name__ == '__main__':
    print("Running automation script directly for testing...")
    # You can change the title here if needed for your test environment
    success = paidout_Navigation(app_title=".*R10PosClient.*")
    if success:
        print("\nTest run completed successfully.")
    else:
        print("\nTest run failed.")
