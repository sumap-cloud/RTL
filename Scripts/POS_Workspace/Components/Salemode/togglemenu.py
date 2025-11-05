import time
from pywinauto.application import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError

# --- Step 1: Connect to the Application ---
# Use the title of your application window
app_title = ".*R10PosClient.*"

# --- Define Expected Buttons ---
# This list contains all the buttons we expect to see after the menu is expanded,
# based on the second screenshot provided.
expected_buttons = [
    "Rain Check", "Recall Transaction", "Reprint Receipt", "Reprint Last", "Lock",
    "Balance Enquiry", "User Barcode", "Cash Withdrawal", "Log Off",
    "Department Sale", "EMV Report", "Price Enquiry", "EFT Log On", "Report Abuse",
    "Software Verification", "Reset Hardware", "Change Order Request", "Pick Up Voucher",
    "Item Search", "Returns", "Funds Management", "Lotteries & Lotto Payout",
    "Parcel Pickup", "Home Delivery", "No Sale"
]


try:
    # Connect to the application
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

            # --- Step 3: Verify Expansion and List All Buttons ---
            collapse_button = win.child_window(auto_id=collapse_button_id, control_type="Button")
            if collapse_button.is_visible():
                print("Menu expanded successfully.")
                
                # --- Step 4: Find and Click the "Returns" Button ---
                print("\n--- Clicking 'Returns' Button ---")
                try:
                    returns_button = win.child_window(title="Returns", control_type="Button")
                    if returns_button.is_enabled():
                        print("Found 'Returns' button. Clicking it...")
                        returns_button.click()
                        print("'Returns' button clicked successfully.")
                        
                        # --- Step 5: Click "Transaction Based" Button ---
                        print("\n--- Clicking 'Transaction Based' Button ---")
                        try:
                            # Wait for the "Transaction Based" button to be enabled for up to 10 seconds
                            tb_button = win.child_window(title="Transaction Based", control_type="Button")
                            print("Waiting for 'Transaction Based' button to become enabled...")
                            tb_button.wait('enabled', timeout=10)
                            
                            print("'Transaction Based' button is enabled. Clicking it...")
                            tb_button.click()
                            time.sleep(1) # Wait for popup

                            # --- Step 6: Handle "Approval Required" Popup ---
                            print("\n--- Handling 'Approval Required' Popup ---")
                            try:
                                # Switch to the top-level popup window
                                popup = win.top_window()
                                popup.wait('visible', timeout=20)
                                print(f"Popup window found with title: '{popup.window_text()}'")

                                # To find the correct controls for username and password,
                                # you might need to run: popup.print_control_identifiers()
                                
                                # Enter credentials
                                # Assuming the fields are the first and second "Edit" controls.
                                # This might need adjustment based on print_control_identifiers() output.
                                print("Entering credentials...")
                                popup.descendants(control_type="Edit")[0].set_text("diva")
                                popup.descendants(control_type="Edit")[1].set_text("diva")
                                
                                # Click OK
                                ok_button = popup.child_window(title="OK", control_type="Button")
                                if ok_button.is_enabled():
                                    print("Clicking 'OK' button...")
                                    ok_button.click()
                                    print("Credentials submitted successfully.")
                                else:
                                    print("Error: 'OK' button is not enabled.")

                            except (TimeoutError, MatchError, IndexError) as pop_err:
                                print(f"Error handling popup: {pop_err}")
                                print("Could not find the popup or its controls. Please check identifiers.")
                                # Uncomment the line below to help debug the popup
                                # win.top_window().print_control_identifiers()

                        except (TimeoutError, MatchError) as tb_err:
                             print(f"Error with 'Transaction Based' button: {tb_err}")

                    else:
                        print("Error: 'Returns' button found, but it is not enabled.")
                except MatchError:
                    print("Error: Could not find the 'Returns' button on the screen.")
                print("---------------------------------")

            else:
                print("Error: Clicked the expand button, but the menu does not appear to be open.")
        else:
            print("Expand button is not visible. The menu might already be open.")

    except MatchError:
        print(f"Error: Could not find the expand button with auto_id '{expand_button_id}'.")


except Exception as e:
    print(f"An error occurred: {e}")
