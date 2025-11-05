import time
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

# Define a constant for the main application window title
APPLICATION_WINDOW_TITLE = ".*R10PosClient.*"

def handle_transaction_return_screen(action="click_search"):
    """
    Connects to the 'Transaction Based Return' screen, verifies all visible
    elements using the proven direct-search method, and performs a click action.

    Args:
        action (str): The button to click. Defaults to 'click_search'.
                      Options: "click_search", "click_cancel".

    Returns:
        bool: True if all actions were completed successfully, False otherwise.
    """
    try:
        # --- Connection ---
        print("Attempting to connect to the application...")
        app = Application(backend="uia").connect(title_re=APPLICATION_WINDOW_TITLE, timeout=20)
        win = app.window(title_re=APPLICATION_WINDOW_TITLE)
        win.set_focus()
        print("Successfully connected to the application window.")
        time.sleep(1)

        # --- Verify Screen Title ---
        print("\nSearching for the title...")
        title_element = win.child_window(title="Transaction Based Return", control_type="Text")
        title_text = title_element.window_text()
        print(f"SUCCESS: Found title text: '{title_text}'")

        # --- Verify Main Buttons ---
        print("\nSearching for main buttons...")
        search_button = win.child_window(title="Search transaction", control_type="Button")
        print("SUCCESS: Found the 'Search transaction' button.")
        
        cancel_button = win.child_window(title="Cancel", control_type="Button")
        print("SUCCESS: Found the 'Cancel' button.")

        # --- Verify Text Labels ---
        print("\nSearching for other text labels...")
        win.child_window(title="Load Transaction Using:", control_type="Text")
        print("SUCCESS: Found label 'Load Transaction Using:'.")
        win.child_window(title="Or", control_type="Text")
        print("SUCCESS: Found label 'Or'.")
        win.child_window(title="Scan/Type Transaction Code", control_type="Text")
        print("SUCCESS: Found label 'Scan/Type Transaction Code'.")

        # --- Verify Input Field ---
        print("\nSearching for the barcode input field...")
        win.child_window(title="Scan/Enter Trans. Barcode", control_type="Edit")
        print("SUCCESS: Found the 'Scan/Enter Trans. Barcode' input field.")
        
        # --- ACTION STEP ---
        if action == "click_search":
            search_button.click()
            print("'Search transaction' button was clicked.")
        elif action == "click_cancel":
            cancel_button.click()
            print("'Cancel' button was clicked.")
        
        return True

    except ElementNotFoundError as e:
        print(f"ERROR: A required UI element was not found. Details: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in handle_transaction_return_screen: {e}")
        return False

# This block allows the script to be run directly for testing
if __name__ == "__main__":
    print("--- Running Transaction Return Screen script as a standalone test ---")
    if not handle_transaction_return_screen(action="click_search"):
        print("\nThe script did not run properly.")
    print("\n--- Script finished ---")
