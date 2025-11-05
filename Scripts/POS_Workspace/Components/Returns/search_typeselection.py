import time
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

# Define a constant for the main application window title
APPLICATION_WINDOW_TITLE = ".*R10PosClient.*"

def handle_search_type_selection(action="click_pos_parameters"):
    """
    Connects to the 'Search Type Selection' screen, identifies its buttons,
    and performs a specified click action.

    Args:
        action (str): The button to click. Defaults to 'click_pos_parameters'.
                      Options: "click_pos_parameters", "click_serial_no",
                               "click_loyalty_card", "click_back".

    Returns:
        bool: True if the action was completed successfully, False otherwise.
    """
    try:
        # --- Connection ---
        print("Connecting to the application...")
        app = Application(backend="uia").connect(title_re=APPLICATION_WINDOW_TITLE, timeout=20)
        win = app.window(title_re=APPLICATION_WINDOW_TITLE)
        win.set_focus()
        print("Successfully connected.")
        time.sleep(1)

        # --- Verify Screen and Find Buttons ---
        print("\nVerifying 'Search Type Selection' screen...")
        win.child_window(title="Search Type Selection", control_type="Text").wait('visible')
        print("SUCCESS: Found title 'Search Type Selection'.")

        # --- ACTION STEP ---
        # Based on the 'action' parameter, find and click the corresponding button.
        button_to_click = ""
        if action == "click_pos_parameters":
            button_to_click = "POS Parameters"
        elif action == "click_serial_no":
            button_to_click = "Serial no."
        elif action == "click_loyalty_card":
            button_to_click = "Search By Loyalty Card"
        elif action == "click_back":
            button_to_click = "Back"
        else:
            print(f"ERROR: Invalid action '{action}' specified.")
            return False

        print(f"\nAttempting to click the '{button_to_click}' button...")
        button = win.child_window(title=button_to_click, control_type="Button")
        button.wait('visible')
        button.click()
        print(f"SUCCESS: Clicked the '{button_to_click}' button.")

        return True  # Indicate success

    except ElementNotFoundError as e:
        print(f"\nERROR: A required UI element was not found on the 'Search Type Selection' screen.")
        print(f"Details: {e}")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred in handle_search_type_selection.")
        print(f"Error details: {e}")
        return False

# This block allows the script to be run directly for testing
if __name__ == "__main__":
    print("--- Running Search Type Selection script as a standalone test ---")
    # This test will click the 'POS Parameters' button by default.
    # Change the action parameter to test other buttons.
    if not handle_search_type_selection(action="click_pos_parameters"):
        print("\nThe script did not run properly.")

    print("\n--- Script finished ---")