import time
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError




from .tlog import login_and_get_session, lookup_transaction

# Define a constant for the main application window title
APPLICATION_WINDOW_TITLE = ".*R10PosClient.*"

def capture_transaction_details():
    """
    Connects to the R10PosClient application and captures the details
    from the 'Search Transaction' screen.

    Returns:
        dict: A dictionary containing the captured details (e.g., 
              {'Store No.': '2078'}). Returns an empty dictionary 
              if the capture fails.
    """
    captured_data = {}
    try:
        # Connect to the application
        app = Application(backend="uia").connect(title_re=APPLICATION_WINDOW_TITLE, timeout=20)
        win = app.window(title_re=APPLICATION_WINDOW_TITLE)
        win.wait('ready', timeout=20)

        # Find the main form using its specific auto_id
        search_form = win.child_window(auto_id="TransactionBasedReturnPOSParameresSearchViewID", control_type="Custom")
        search_form.wait('visible', timeout=10)

        print("\n--- Capturing Details from Search Transaction Screen ---")

        # --- Define the fields to capture with corrected auto_id values ---
        fields_to_capture = {
            "Store No.": "StoreId_InnerText",
            "Pos No.": "FieldTillId_InnerText",
            "Trans' No.": "FieldTransactionNumber_InnerText"
        }

        # --- Loop through and capture the value of each field ---
        for label, auto_id in fields_to_capture.items():
            try:
                # Find the input box associated with the label
                input_box = search_form.child_window(auto_id=auto_id, control_type="Edit")
                if input_box.exists():
                    captured_data[label] = input_box.window_text() or "<empty>"
                else:
                    captured_data[label] = "<not found>"
            except (ElementNotFoundError, IndexError):
                captured_data[label] = "<error reading value>"

        # Return the dictionary with the captured data
        return captured_data

    except ElementNotFoundError:
        print(f"Error: Could not find an application window with title matching '{APPLICATION_WINDOW_TITLE}'.")
        return captured_data # Return empty dictionary on failure
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return captured_data # Return empty dictionary on failure

# This block allows the script to be run directly for testing
if __name__ == "__main__":
    print("--- Running Transaction Details Capture Script ---")
    
    # Call the function to get the details
    print("--- Running Transaction Details Capture Script ---")
    
    # Call the function to get the details
    details = capture_transaction_details()
    
    # Check if the details dictionary is not empty
    if details:
        print("\n==========================================")
        print("         TRANSACTION DETAILS")
        print("==========================================")
        for label, value in details.items():
            print(f"  -> {label.ljust(12)}: {value}")
        print("==========================================")

        # --- Use the captured details to look up the transaction ---
        print("\n--- Proceeding to Transaction Lookup ---")
        
        # Assign captured details to variables
        STORE_NUMBER = details.get("Store No.")
        LANE_NUMBER = details.get("Pos No.")
        TRANSACTION_NUMBER = details.get("Trans' No.")
        ENV = "azwr10ast00004"  # Replace with your actual environment

        # Check if all required details were captured
        if STORE_NUMBER and LANE_NUMBER and TRANSACTION_NUMBER and STORE_NUMBER != "<not found>":
            session_token = login_and_get_session(ENV)
    
            if session_token:
                print("Successfully logged in. Looking up transaction...")
                lookup_transaction(session_token, ENV, STORE_NUMBER, LANE_NUMBER, TRANSACTION_NUMBER)
            else:
                print("Failed to get session token. Cannot look up transaction.")
        else:
            print("One or more transaction details were not found. Skipping lookup.")

    else:
        print("\nThe script did not capture any details.")
        
    print("\n--- Script finished ---")


