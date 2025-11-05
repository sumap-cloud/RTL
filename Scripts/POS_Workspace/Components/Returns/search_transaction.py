import time
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

# MODIFIED IMPORT:
# The original "from .select_date_range..." is a relative import,
# which only works when this script is imported as part of a larger package.
# By removing the dot, we make it a direct import, which works when
# running this file directly because Python checks the current directory.
from Scripts.POS_Workspace.Components.Returns.select_daterangeSCreen import selectdaterange

# Define a constant for the main application window title
APPLICATION_WINDOW_TITLE = ".*R10PosClient.*"

def search_transaction_and_enter_number():
    """
    Handles the main transaction search screen: displays content,
    opens the date range popup, enters a transaction number, and clicks retrieve.

    Returns:
        bool: True if all actions were completed successfully, False otherwise.
    """
    try:
        # Connect to the application
        app = Application(backend="uia").connect(title_re=APPLICATION_WINDOW_TITLE, timeout=20)
        win = app.window(title_re=APPLICATION_WINDOW_TITLE)
        win.wait('ready', timeout=20)

        # Find the main form using its specific auto_id
        search_form = win.child_window(auto_id="TransactionBasedReturnPOSParameresSearchViewID", control_type="Custom")
        search_form.wait('visible', timeout=10)

        # --- Display Screen Content ---
        print("\n--- Search Transaction Screen ---")
        list_form = search_form.child_window(auto_id="ListForm", control_type="List")
        for item in list_form.children(control_type="ListItem"):
            label_text = item.window_text()
            try:
                input_boxes = item.children(control_type="Edit")
                input_value = input_boxes[0].window_text() if input_boxes else "<no input box>"
                print(f"{label_text.ljust(15)} {input_value or '<empty>'}")
            except (ElementNotFoundError, IndexError):
                print(f"{label_text.ljust(15)} <error reading value>")
        print("---------------------------------")

        # --- Interact with Date Range Popup ---
        print("\nOpening date range selector...")
        select_range_btn = search_form.child_window(title="Select Range", control_type="Button")
        select_range_btn.click_input()
        time.sleep(1) # Give the popup a moment to appear

        # Call the function from the other module
        if not selectdaterange(action="click_cancel"):
            print("\nError: The date range selection was not handled properly.")
            # return False # Uncomment if you want the script to stop on failure
        
        print("\nDate range interaction complete.")
        time.sleep(1) # Wait for main window to be active again
        
        # --- Enter a transaction number ---
        trans_no_input = search_form.child_window(auto_id="FieldTransactionNumber_InnerText", control_type="Edit")
        if trans_no_input.exists():
            transaction_number = "5843" # Updated to match image for consistency
            print(f"\nTyping '{transaction_number}' into 'Trans' No.' field...")
            #trans_no_input.type_keys(transaction_number, with_spaces=True)
            print("Typing complete.")
            time.sleep(1)

            # --- Click the Retrieve button ---
            print("\nClicking the 'Retrieve' button...")
            retrieve_btn = search_form.child_window(title="Retrieve", control_type="Button")
            if retrieve_btn.exists():
                retrieve_btn.click_input()
                print("'Retrieve' button clicked.")
                time.sleep(2) # Wait a moment for the next action/screen
            else:
                print("Error: Could not find the 'Retrieve' button.")

        else:
            print("Error: Could not find the 'Trans' No.' input field.")
        
        return True # Success

    except ElementNotFoundError:
        print(f"Error: Could not find an application window with title matching '{APPLICATION_WINDOW_TITLE}'.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in search_transaction: {e}")
        return False

# This block allows the script to be run directly for testing
if __name__ == "__main__":
    print("--- Running Transaction Searcher as a standalone script ---")
    if not search_transaction_and_enter_number():
        print("\nThe script did not run properly.")
    print("\n--- Script finished ---")

