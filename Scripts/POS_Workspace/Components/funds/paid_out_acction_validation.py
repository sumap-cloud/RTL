# File: pos_automation.py

import time
from pywinauto.application import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError

def Select_relevent_account_paidout(win):
    """
    Handles the 'Paid Out' screen, scrolls through accounts, and selects a specific one.

    Args:
        win: The main application window object from pywinauto.

    Returns:
        bool: True if the account is selected successfully, False otherwise.
    """
    try:
        # --- Step 7: Identify the "Paid Out" screen/pane ---
        print("\nLooking for the 'Paid Out' screen elements...")
        # Wait for a unique element on this screen to ensure it's loaded
        win.child_window(title="Select relevant account:", control_type="Text").wait('visible', timeout=20)
        print("Successfully identified the 'Paid Out' screen.")

        # --- Step 8: Capture all relevant account buttons with scrolling ---
        print("\n--- Capturing all relevant account buttons (with scrolling) ---")
        all_account_names = set()

        # Find the scroll arrow buttons. This might need adjustment based on inspection.
        # This assumes the scroll buttons are the first two buttons without a title.
        scroll_buttons = [b for b in win.descendants(control_type="Button") if not b.window_text()]
        up_arrow = scroll_buttons[0] if len(scroll_buttons) > 0 else None
        down_arrow = scroll_buttons[1] if len(scroll_buttons) > 1 else None

        if not down_arrow or not up_arrow:
            raise MatchError("Could not find the scroll arrow buttons.")

        # Scroll down to find all accounts
        while True:
            all_buttons = win.descendants(control_type="Button")
            for btn in all_buttons:
                button_text = btn.window_text()
                # Filter for buttons that look like accounts (e.g., "057 Christmas Subsidy")
                if button_text and len(button_text) > 4 and button_text[:3].isdigit():
                    all_account_names.add(button_text)

            if not down_arrow.is_enabled():
                print("Down arrow is disabled. Reached the end of the list.")
                break
            
            print("Clicking down arrow to scroll...")
            down_arrow.click()
            time.sleep(0.5)

        if all_account_names:
            print("\nFound the following account options:")
            for account in sorted(list(all_account_names)):
                print(f"- {account}")
        else:
            print("Warning: No account buttons were found.")
        
        print("---------------------------------")

        # --- Step 9: Scroll back to the top of the list ---
        print("\n--- Scrolling back to the top ---")
        while up_arrow.is_enabled():
            print("Clicking up arrow to scroll to top...")
            up_arrow.click()
            time.sleep(0.5)
        print("Reached the top of the list.")
        print("---------------------------------")

        # --- Step 10: Select the "057 Christmas Subsidy" account ---
        print("\n--- Selecting '057 Christmas Subsidy' ---")
        christmas_subsidy_button = win.child_window(title="043 Petty Cash", control_type="Button").wait('enabled', timeout=10)
        print("Found '057 Christmas Subsidy' button. Clicking it...")
        christmas_subsidy_button.click_input()
        print("'057 Christmas Subsidy' button clicked successfully.")
        time.sleep(1)

    except (TimeoutError, MatchError, IndexError) as e:
        print(f"Error on 'Paid Out' screen: {e}")
        print("Please ensure you are on the correct screen and the UI elements are as expected.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred on the 'Paid Out' screen: {e}")
        return False
        
    return True
def main():
    #"""Main function to automate the 'Paid Out' action in the POS application.
    application_window_title = ".*R10PosClient.*"
    main()
    app = Application(backend="uia").connect(title_re=application_window_title, timeout=10)
    win = app.window(title_re=application_window_title)
    win.set_focus()
    Select_relevent_account_paidout(win)
    print("Automation script finished.")
if __name__ == "__main__":
    
        main()
    
