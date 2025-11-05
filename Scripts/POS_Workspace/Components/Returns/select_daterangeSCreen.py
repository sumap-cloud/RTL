import time
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

# Define constant window titles for clarity and reusability
MAIN_APP_WINDOW_TITLE = ".*R10PosClient.*"
DATE_RANGE_WINDOW_TITLE = "Retalix.Client.POS.Presentation.ViewModels.ViewModels.DateRangeSelectionViewModel"

def selectdaterange(action="click_cancel"):
    """
    Connects to the Date Range Selection popup, captures its content,
    and performs a specified action.

    Args:
        action (str): Defines which button to click. Defaults to 'click_cancel'.
    
    Returns:
        bool: True if the action was completed successfully, False otherwise.
    """
    try:
        # Connect to the main application process first
        app = Application(backend="uia").connect(title_re=MAIN_APP_WINDOW_TITLE, timeout=10)

        # Now, find the specific popup window using its technical title
        date_win = app.window(title=DATE_RANGE_WINDOW_TITLE, control_type="Window")
        date_win.wait('visible', timeout=10)
        print("Successfully found the date range window.")

        # --- Capture and Display Screen Content ---
        print("\n--- Date Range Selection Screen ---")
        print("--- Found Buttons ---")
        buttons = date_win.descendants(control_type="Button")
        for button in buttons:
            print(f"- {button.window_text()}")
        print("---------------------")

        # --- ACTION STEP ---
        if action == "click_cancel":
            print("\nAttempting to click the 'Cancel' button...")
            cancel_button = date_win.child_window(title="Cancel", control_type="Button")
            cancel_button.click()
            print("'Cancel' button clicked successfully.")
        
        # Add other actions here if needed, e.g.:
        # if action == "click_last_week":
        #     date_win.child_window(title="Last Week").click()
        
        return True # Indicate success

    except ElementNotFoundError:
        print(f"\nError: Could not find the window '{DATE_RANGE_WINDOW_TITLE}'.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in select_date_range: {e}")
        return False

# This block allows the script to be run directly for testing
if __name__ == "__main__":
    print("--- Running Date Range Selector as a standalone script ---")
    # To test this file, you must manually open the date range popup first
    if not selectdaterange(action="click_cancel"):
        print("\nFunction did not run properly.")
    print("\n--- Script finished ---")
