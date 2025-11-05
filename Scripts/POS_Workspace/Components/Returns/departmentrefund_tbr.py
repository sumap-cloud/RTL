from pywinauto import Application, findwindows, timings
from pywinauto.findbestmatch import MatchError
import sys
import time

def handle_reason_code_screen(win, reason_code=None):
    """
    Finds and clicks a reason code on the 'Return Item' screen,
    scrolling if necessary to find it.
    """
    print("\n✨ Return Item Reason Code Screen Detected ✨")
    reason_to_click = reason_code if reason_code else "Double Scan"
    
    try:
        # --- Step 1: Detect scrolling and collect all button texts ---
        all_found_buttons = set()
        down_arrow = None
        up_arrow = None

        try:
            # Check for scroll buttons using the provided auto_id
            down_arrow = win.child_window(auto_id="ConsumableDataPagerButtonDownID", control_type="Button")
            up_arrow = win.child_window(auto_id="ConsumableDataPagerButtonUpID", control_type="Button") # Assuming similar ID for up arrow
        except (MatchError, timings.TimeoutError):
            print("- No scrolling functionality detected.")
        
        if down_arrow and down_arrow.exists():
            print("- Scrolling detected. Collecting all available reason codes...")
            # Scroll to the top to ensure a consistent starting point
            if up_arrow.exists():
                while up_arrow.is_enabled():
                    up_arrow.click_input()
                    time.sleep(0.5)

            # Use a more robust loop to ensure the last page is always processed
            while True:
                current_buttons = {b.window_text() for b in win.descendants(control_type="Button")}
                all_found_buttons.update(current_buttons)

                if down_arrow.is_enabled():
                    down_arrow.click_input()
                    time.sleep(0.5)
                else:
                    # Can't scroll further, so break the loop
                    break
        else:
            # If no scrolling, just grab the visible buttons
            all_found_buttons = {b.window_text() for b in win.descendants(control_type="Button")}

        # Filter out common non-reason code buttons for cleaner printing
        non_reason_codes = {'', 'Cancel', 'OK', 'C', 'X', '<<', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.'}
        all_found_reasons = {b for b in all_found_buttons if b not in non_reason_codes}


        print("\n--- Captured Reason Codes ---")
        for reason in sorted(list(all_found_reasons)):
            print(f"  - {reason}")
        print("----------------------------\n")
        
        # --- Step 2: Find and click the target reason code ---
        # Scroll back to the top to begin the search
        if up_arrow and up_arrow.exists():
            while up_arrow.is_enabled():
                up_arrow.click_input()
                time.sleep(0.5)

        # Loop through pages again to find and click the target button
        while True:
            try:
                target_button = win.child_window(title=reason_to_click, control_type="Button")
                if target_button.is_visible():
                    print(f"🖱️ Clicking '{reason_to_click}'...")
                    target_button.click_input()
                    print(f"✅ '{reason_to_click}' button clicked successfully.")
                    return True
            except MatchError:
                # Button not visible on this page, continue to next
                pass

            if down_arrow and down_arrow.is_enabled():
                down_arrow.click_input()
                time.sleep(0.5)
            else:
                # Scrolled through all pages and did not find the button
                print(f"❌ ERROR: Could not find '{reason_to_click}' to click it after scanning all pages.")
                return False

    except (timings.TimeoutError, MatchError) as e:
        print(f"❌ An error on the reason code screen: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred in handle_reason_code_screen: {e}")
        return False

def select_refund_department(department_name):
    """
    This function automates interactions on the 'Department Return' or similar screens
    in the POS system. It finds and clicks a department button by name, then handles
    the subsequent reason code screen.

    Args:
        department_name (str): The name of the department to select (e.g., "BAKEHOUSE").
    """
    application_window_title = "R10PosClient"
    category = department_name

    try:
        print("Connecting to the POS application...")
        # Connect to the running application
        app = Application(backend="uia").connect(title=application_window_title, timeout=20)
        
        win = app.window(title=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{win.window_text()}'")

        # Wait for the window to be fully ready
        win.wait('ready', timeout=30)
        time.sleep(2)  # A brief pause for the UI to settle completely
        print("Application window is ready.")

        # --- Interact with the 'Department' screen ---
        print(f"\n--- Step 1: Finding the '{category}' button ---")

        try:
            # Since there are no scroll buttons, we search for the button directly.
            # We use `title_re` because the button's full text might include numbers or newlines.
            department_button = win.child_window(title_re=f".*{category}.*", control_type="ListItem")
            
            department_button.wait('visible', timeout=15)
            print(f"- Found '{category}' button.")
            
            # Click the button to select the department
            department_button.click_input()
            print(f"- Successfully clicked '{category}'.")
            time.sleep(1) # Wait for the reason code screen to appear

            # --- Step 2: Handle the reason code screen ---
            if not handle_reason_code_screen(win, reason_code="Double Scan"):
                return False # Exit if reason code handling fails

            time.sleep(3)  # Pause to observe the result on the screen

        except timings.TimeoutError:
            print(f"Error: Could not find the '{category}' button on the screen.")
            return False
        except Exception as e:
            print(f"An error occurred while trying to click the department button: {e}")
            return False

        except Exception as e:
            print(f"- An error occurred while trying to click 'Cancel': {e}")


    except timings.TimeoutError:
        print(f"Failed to connect to the POS application. Timed out waiting for window with title '{application_window_title}'.")
        return False
    except findwindows.ElementNotFoundError:
        print("Failed to find the application window. Make sure the application is running and the title is correct.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

    return True

if __name__ == "__main__":
    # We are calling the function to select the "BAKEHOUSE" department as shown in the new image.
    if select_refund_department(department_name="BAKEHOUSE"):
        print("\nAutomation script finished successfully.")
    else:
        print("\nAutomation script failed.")

