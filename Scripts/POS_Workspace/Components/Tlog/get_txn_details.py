from pywinauto import Application
import sys
from pathlib import Path
import time

from Scripts.POS_Workspace.Components.Tlog.transaction_details import capture_transaction_details

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing necessary components for POS automation

from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Components.Returns.search_typeselection import handle_search_type_selection
from Components.Tlog.Enhanced_Receipts import capture_and_interact
from Components.Tlog.tlog import login_and_get_session,lookup_transaction
def get_transaction_details():
    app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
    # Add logic to extract transaction details from the application
    win= app.window(title_re=".*R10PosClient.*")
    win.set_focus()
    
    #navigation to reprintreceipt
    if not toggle_menu_navigate(["Reprint Receipt"]):
        print("Failed to navigate to Reprint Receipt")
        return False
    time.sleep(2)  # Wait for the menu to open
    
    if not capture_and_interact(button_title_to_click="Search transaction"):
        print("\nFailed to capture and interact with the Enhanced Reprint screen.")
        
    time.sleep(2)  # Wait for the Enhanced Reprint screen to load
    
    time.sleep(2)  # Wait for the screen to be fully rendered
    if not handle_search_type_selection(action="click_pos_parameters"):
        print("\nThe script did not run properly.")
        return False
    time.sleep(2)  # Wait for the search type selection to complete
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
#get_transaction_details()