import time
from pywinauto.application import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError

# --- Step 1: Connect to the Application ---
# Use the title of your application window
app_title = ".*R10PosClient.*"


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

            # --- Step 3: Verify Expansion and Click "Returns" ---
            collapse_button = win.child_window(auto_id=collapse_button_id, control_type="Button")
            if collapse_button.wait('visible', timeout=5):
                print("Menu expanded successfully.")
                
                print("\n--- Finding and Clicking the 'Returns' Button ---")
                returns_button = win.child_window(title="Returns", control_type="Button")
                returns_button.wait('enabled', timeout=5)
                returns_button.click()
                print("'Returns' button clicked successfully.")
                
                # --- Step 4: Click "Transaction Based" Button ---
                print("\n--- Clicking 'Transaction Based' Button ---")
                tb_button = win.child_window(title="Transaction Based", control_type="Button")
                tb_button.wait('enabled', timeout=10)
                tb_button.click()
                print("'Transaction Based' button clicked successfully.")
                time.sleep(1) # Wait for popup

                # --- Step 5: Handle "Approval Required" Popup ---
                print("\n--- Handling 'Approval Required' Popup ---")
                try:
                    # Use app.top_window() to get the popup
                    popup = app.top_window()
                    popup.wait('visible', timeout=10)
                    print(f"Popup window found with title: '{popup.window_text()}'")
                    
                    edit_fields = popup.descendants(control_type="Edit")
                    if len(edit_fields) >= 2:
                        print("Entering credentials...")
                        edit_fields[0].set_text("atmgr5")
                        edit_fields[1].set_text("abcd1234")
                        
                        ok_button = popup.child_window(title="OK", control_type="Button")
                        ok_button.click()
                        print("Credentials submitted successfully.")
                        time.sleep(1) # Wait for next screen to load

                        # --- Step 6: Click "Search transaction" Button ---
                        print("\n--- Clicking 'Search transaction' Button ---")
                        try:
                            # After login, the context is back to the main window
                            search_button = win.child_window(title="Search transaction", control_type="Button")
                            search_button.wait('enabled', timeout=10)
                            print("Found 'Search transaction' button. Clicking it...")
                            search_button.click()
                            print("'Search transaction' button clicked successfully.")
                            time.sleep(1) # Wait for next screen to load

                            # --- Step 7: Verify Search Type and Click "POS Parameters" ---
                            print("\n--- Verifying Search Type Selection Screen ---")
                            try:
                                expected_search_buttons = {"POS Parameters", "Serial no.", "Search By Loyalty Card"}
                                
                                win.child_window(title="POS Parameters", control_type="Button").wait('visible', timeout=10)
                                
                                visible_buttons = {b.window_text() for b in win.descendants(control_type="Button")}
                                
                                if expected_search_buttons.issubset(visible_buttons):
                                    print("All search type buttons are visible.")
                                    
                                    print("Clicking 'POS Parameters' button...")
                                    pos_button = win.child_window(title="POS Parameters", control_type="Button")
                                    pos_button.click()
                                    print("'POS Parameters' button clicked successfully.")
                                    time.sleep(1)

                                    # --- Step 8: Click Retrieve on Search Transaction Screen ---
                                    print("\n--- Verifying Search Transaction Screen ---")
                                    try:
                                        # Wait for the screen to load by checking for the Retrieve button
                                        print("Waiting for 'Retrieve' button to appear...")
                                        retrieve_button = win.child_window(title="Retrieve", control_type="Button")
                                        retrieve_button.wait('visible', timeout=10)
                                        
                                        print("Screen loaded. Clicking 'Retrieve' button...")
                                        retrieve_button.click()
                                        print("'Retrieve' button clicked successfully.")

                                    except (TimeoutError, MatchError) as retrieve_err:
                                        print(f"Error on Search Transaction screen: {retrieve_err}")

                                else:
                                    missing = expected_search_buttons - visible_buttons
                                    print(f"Error: Missing search type buttons: {missing}")

                            except (TimeoutError, MatchError) as pos_err:
                                print(f"Error on Search Type Selection screen: {pos_err}")

                        except (TimeoutError, MatchError) as search_err:
                            print(f"Error finding 'Search transaction' button: {search_err}")

                    else:
                        print("Error: Could not find credential fields in popup.")

                except (TimeoutError, MatchError, IndexError) as pop_err:
                    print(f"Error handling popup: {pop_err}")

            else:
                print("Error: Clicked the expand button, but the menu does not appear to be open.")
        else:
            print("Expand button is not visible. The menu might already be open.")

    except (MatchError, TimeoutError) as e:
        print(f"Error during initial steps: {e}")


except Exception as e:
    print(f"An unexpected error occurred: {e}")
