import time
from pywinauto.application import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError


def _handle_approval_popup(app, username="atmgr5", password="abcd1234"):
    """
    Flexibly handles a potential "Approval Required" popup by entering credentials and clicking OK.
    Continues the process even if approval is not needed or if there are minor issues.

    Args:
        app (pywinauto.application.Application): The application instance.
        username (str): The username to enter (default: atmgr5).
        password (str): The password to enter (default: abcd1234).

    Returns:
        bool: Always returns True to ensure process continues.
    """
    try:
        print("\n--- Checking for Approval Popup ---")
        # Quick check for approval window without waiting
        try:
            top_window = app.top_window()
            if "Approval" not in top_window.window_text():
                print("✓ No approval needed, continuing...")
                return True
        except:
            print("✓ No approval window detected, continuing...")
            return True

        # If we get here, we found an approval window
        print(f"✅ Found approval window: '{top_window.window_text()}'")
        
        # Find credential fields
        edit_controls = top_window.descendants(control_type="Edit")
        if len(edit_controls) >= 2:
            print("  - Entering credentials...")
            edit_controls[0].set_text(username)
            edit_controls[1].set_text(password)
            
            # Look for OK button
            ok_buttons = top_window.descendants(title="OK", control_type="Button")
            if ok_buttons and ok_buttons[0].is_enabled():
                ok_buttons[0].click()
                print("✅ Credentials submitted successfully")
            else:
                print("! OK button not found or not enabled, but continuing...")
        else:
            print("! No credential fields found, but continuing...")
            
        return True

    except (TimeoutError, MatchError) as e:
        print(f"! Note: {str(e)}")
        print("  Continuing with process...")
        return True
    except Exception as e:
        print(f"! Unexpected situation: {str(e)}")
        print("  Continuing with process...")
        return True

def _validate_buttons(window, expected_buttons, menu_name):
    """
    Helper function to validate if expected buttons are visible in the current window.

    Args:
        window (pywinauto.controls.uia_controls.UIAWrapper): The window to check for buttons.
        expected_buttons (list): A list of button titles expected to be visible.
        menu_name (str): A descriptive name for the current menu (for logging).

    Returns:
        bool: True if all expected buttons are found, False otherwise.
    """
    print(f"Validating {menu_name} buttons...")
    buttons = window.descendants(control_type="Button")
    visible_buttons = {b.window_text() for b in buttons if b.is_visible() and b.window_text()}
    missing_buttons = [btn for btn in expected_buttons if btn not in visible_buttons]

    if not missing_buttons:
        print(f"All expected {menu_name} buttons visible.")
        return True
    else:
        print(f"Warning: Missing {menu_name} buttons: {', '.join(missing_buttons)}")
        return False

def toggle_menu_navigate(navigation_steps):
    app_title=".*R10PosClient.*"
    """
    Automates navigation through a POS application based on a list of steps.
    Each step can be a button title, or "APPROVAL" to trigger credential handling.

    Args:
        app_title (str): A regular expression for the title of the application window.
        navigation_steps (list): A list of strings, where each string is either:
                                 - The exact title of a button to click.
                                 - The special keyword "APPROVAL" to indicate an approval popup.

    Returns:
        bool: True if the automation completes successfully, False otherwise.
    """
    # --- Define Expected Buttons (can be moved to config or passed as args for more flexibility) ---
    expected_main_menu_buttons = [
        "Rain Check", "Recall Transaction", "Reprint Receipt", "Reprint Last", "Lock",
        "Balance Enquiry", "User Barcode", "Cash Withdrawal", "Log Off",
        "Department Sale", "EMV Report", "Price Enquiry", "EFT Log On", "Report Abuse",
        "Software Verification", "Reset Hardware", "Change Order Request", "Pick Up Voucher",
        "Item Search", "Returns", "Funds Management", "Lotteries & Lotto Payout",
        "Parcel Pickup", "Home Delivery", "No Sale" # Added Void Transaction
    ]

    expected_funds_management_buttons = [
        "Go Back", "PoS Declaration", "Tender Correction", "Paid Out", "Paid In",
        "Pick Up at PoS", "Tender Loan"
    ]
    
    expected_returns_buttons = [ # Example for returns submenu, you'll need to fill this out based on your UI
        "Go Back", "Transaction Based", "Item Based", "Receipt Based"
    ]

    # Map menu names to their expected buttons for validation
    menu_button_map = {
        "main menu": expected_main_menu_buttons,
        "funds management": expected_funds_management_buttons,
        "returns": expected_returns_buttons,
        # Add other menu button lists as needed
    }

    try:
        # --- Step 1: Connect to the Application ---
        print(f"Connecting to '{app_title}'...")
        app = Application(backend="uia").connect(title_re=app_title, timeout=20)
        win = app.window(title_re=app_title)
        win.restore()
        win.set_focus()
        print("Connected to application.")

        # --- Step 2: Find and Click the Expand Button if necessary ---
        expand_button_id = 'TransactionCommandListButtonsViewExpandButtonID'
        collapse_button_id = 'TransactionCommandListButtonsViewCollapseButton'

        try:
            # Removed 'timeout' argument as it was causing the error
            expand_button = win.child_window(auto_id=expand_button_id, control_type="Button")
            if expand_button.is_visible():
                print("Expanding menu...")
                expand_button.click()
                time.sleep(1) # Give UI time to expand
                # Verify menu expanded
                # Removed 'timeout' argument as it was causing the error
                collapse_button = win.child_window(auto_id=collapse_button_id, control_type="Button")
                if not collapse_button.is_visible():
                    print("Error: Menu did not expand.")
                    return False
                print("Menu expanded.")
            else:
                print("Expand button not found or menu already open.")
        except (TimeoutError, MatchError):
            print("Expand button not found or menu already open.")
            pass # Menu might already be open or the button doesn't exist

        current_menu = "main menu" # Start at the main menu for validation
        _validate_buttons(win, menu_button_map.get(current_menu.lower(), []), current_menu)


        # --- Step 3: Iterate through navigation steps ---
        for i, step in enumerate(navigation_steps):
            step = step.strip() # Clean up any whitespace

            if step.upper() == "APPROVAL":
                print("Checking for approval...")
                _handle_approval_popup(app)  # Will continue regardless of result
                # Give UI time to settle after any approval handling
                time.sleep(1)
                continue # Move to the next navigation step

            print(f"Clicking '{step}' button...")
            try:
                target_button = win.child_window(title=step, control_type="Button").wait('enabled', timeout=10)
                target_button.click()
                time.sleep(1) # Wait for the new UI to load

                # Update current menu context for validation
                # This logic can be more sophisticated if sub-menus are not simply named after their parent button
                current_menu = step.lower()
                _validate_buttons(win, menu_button_map.get(current_menu.lower(), []), current_menu)


            except (TimeoutError, MatchError) as e:
                print(f"Error: Failed to click '{step}': {e}")
                return False

        print("\nAutomation script finished successfully.")
        return True

    except (TimeoutError, MatchError) as e:
        print(f"Error: Could not connect to application: {e}")
        return False
    except Exception as e:
        print(f"Error: Unexpected error during navigation: {e}")
        return False

# This block allows you to run this script directly for testing
if __name__ == '__main__':
    print("Starting automation test...")

   
    # --- Example 3: Void Transaction > Approval ---
    print("\n--- Running Test Case 3: Void Transaction > Approval ---")
    
    #success3 = toggle_menu_navigate(["Void Transaction", "APPROVAL"])
    success3 = toggle_menu_navigate(["Returns", "Transaction Based", "APPROVAL"])
    if success3:
        print("\nTest Case 3 successful.")
    else:
        print("\nTest Case 3 failed.")
