from pywinauto import Application, findwindows, timings
from pathlib import Path
import sys
import time

def department_sale(department_name):
    """
    This function automates interactions on the 'Department Sale' screen of the POS system.
    It identifies all department buttons, scrolls to the bottom, then scrolls back to the top,
    and finally clicks on the 'BAKEHOUSE' department.
    """
    application_window_title = "R10PosClient"
    category = department_name 
    try:
        print("Connecting to the POS application...")
        app = Application(backend="uia").connect(title=application_window_title, timeout=20)
        
        win = app.window(title=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{win.window_text()}'")

        win.wait('ready', timeout=30)
        time.sleep(2) # Wait for UI to settle
        print("Application window is ready.")

        # --- Interact with the 'Department Sale' screen ---
        print("\nAnalyzing 'Department Sale' screen...")

        try:
            # Find the main container for the department sale view
            department_sale_view = win.child_window(auto_id="DepartmentLookupViewID", control_type="Custom")
            department_sale_view.wait('visible', timeout=15)
            print("- Found the main 'Department Sale' view.")

            # --- Capture all department buttons, including scrolling ---
            print("\n--- Step 1: Collecting all department buttons by scrolling down ---")
            
            department_listbox = department_sale_view.child_window(auto_id="lbDepartmentIdItems", control_type="List")
            department_listbox.wait('visible', timeout=10)

            down_arrow_button = department_sale_view.child_window(auto_id="LeftRegionDataPagerButtonDownID", control_type="Button")
            up_arrow_button = department_sale_view.child_window(auto_id="LeftRegionDataPagerButtonUpID", control_type="Button")


            # Use a set to store unique department names to avoid duplicates
            all_department_names = set()
            initial_items_collected = False

            while True:
                # Get the current list of visible department items
                department_items = department_listbox.children(control_type="ListItem")
                
                new_items_found = False
                if department_items:
                    for item in department_items:
                        item_text = item.window_text()
                        if item_text not in all_department_names:
                            all_department_names.add(item_text)
                            new_items_found = True
                
                # On the first run, we must collect items before checking the button state
                if not initial_items_collected:
                    initial_items_collected = True

                # Check if the down arrow is enabled and visible
                if down_arrow_button.is_enabled():
                    print("- Down arrow is enabled. Clicking to scroll down...")
                    down_arrow_button.click_input()
                    time.sleep(1) # Wait for the list to scroll
                else:
                    print("- Down arrow is disabled. All departments collected.")
                    break
            
            # Print the final, unique list of departments
            print("\n--- All Departments Found ---")
            for name in sorted(list(all_department_names)):
                  print(f"  - Found button: '{name.replace('\\n', ' ')}'")

            # --- Step 2: Scroll back to the top of the list ---
            print("\n--- Step 2: Scrolling back to the top ---")
            while up_arrow_button.is_enabled():
                print("- Up arrow is enabled. Clicking to scroll up...")
                up_arrow_button.click_input()
                time.sleep(1) # Wait for the list to scroll
            
            print("- Reached the top of the list.")
             # The category we want to click
            # --- Step 3: Find and click the 'BAKEHOUSE' button ---
            print("\n--- Step 3: Clicking 'BAKEHOUSE' ---")
            try:
                # The text might contain a newline character depending on how pywinauto reads it.
                # Using a regex search with `title_re` is more robust.
                bakehouse_button = department_listbox.child_window(title_re=f".*{category}.*", control_type="ListItem")
                bakehouse_button.wait('visible', timeout=10)
                print("- Found 'BAKEHOUSE' button.")
                bakehouse_button.click_input()
                print("- Successfully clicked 'BAKEHOUSE'.")
                time.sleep(3) # Pause to observe the result
            except timings.TimeoutError:
                print("Error: Could not find the 'BAKEHOUSE' button after scrolling back to the top.")
                return False
            except Exception as e:
                print(f"An error occurred while trying to click 'BAKEHOUSE': {e}")
                return False

            # Find the 'Cancel' button to close the screen for a clean exit
            print("\n- Finding 'Cancel' button to finish.")
            cancel_button = department_sale_view.child_window(title="Cancel", control_type="Button")
            if cancel_button.exists() and cancel_button.is_visible():
                print(f"- Found 'Cancel' button. Clicking it to exit.")
                cancel_button.click_input()
            else:
                print("\n- Could not find 'Cancel' button to click.")


        except timings.TimeoutError:
            print("Error: Timed out waiting for the 'Department Sale' screen elements to appear.")
            return False
        except Exception as e:
            print(f"An error occurred while analyzing the screen: {e}")
            return False
            
    except timings.TimeoutError:
        print(f"Failed to connect to the POS application. Timed out waiting for window with title matching '{application_window_title}'.")
        return False
    except findwindows.ElementNotFoundError:
        print(f"Failed to find the application window. Make sure the application is running and the title is correct.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

    return True

if __name__ == "__main__":
    if department_sale(department_name="BAKEHOUSE"):
        print("\nAutomation script finished successfully.")
    else:
        print("\nAutomation script failed.")
