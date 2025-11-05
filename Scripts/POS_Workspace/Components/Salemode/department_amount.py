from pywinauto import Application, findwindows, timings
import time
from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Common_components.virtual_numpad import numpad_keyin

def enter_item_price(price):
    """
    This function automates interactions on the 'Enter Item's Price' screen of the POS system.
    It captures department details, enters a specified price, and clicks the 'Approve' button.
    """
    application_window_title = "R10PosClient"

    try:
        print("Connecting to the POS application...")
        app = Application(backend="uia").connect(title=application_window_title, timeout=20)
        
        win = app.window(title=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{win.window_text()}'")

        win.wait('ready', timeout=30)
        time.sleep(3) # Increased wait time for UI to fully render
        print("Application window is ready.")

        # --- Interact with the 'Enter Item's Price' screen ---
        print("\nAnalyzing 'Enter Item's Price' screen...")

        try:
            # First, we get the main transaction view which contains all other elements.
            print("Attempting to find the main transaction view...")
            main_transaction_view = win.child_window(auto_id="MainTransactionViewID", control_type="Custom")
            main_transaction_view.wait('visible', timeout=15)
            print("- Found the main transaction view.")

            # Now, find the price screen view within the main transaction view.
            print("Attempting to find the price screen view...")
            price_screen_view = main_transaction_view.child_window(auto_id="DepartmentSaleViewID", control_type="Custom")
            price_screen_view.wait('visible', timeout=15)
            print("- Found the price screen view.")


            # --- 1. CAPTURE DEPARTMENT INFORMATION (REVISED LOGIC) ---
            print("\nAttempting to capture department information...")
            
            # The title is in the main view, not the price screen view.
            department_sale_title_control = main_transaction_view.child_window(title="Department Sale", control_type="Text")
            department_sale_title = department_sale_title_control.window_text()

            department_id = ""
            department_name = ""

            # The ID and Name are inside the price_screen_view.
            static_text_controls = price_screen_view.children(control_type="Text")
            
            controls_list = list(static_text_controls)

            for i, control in enumerate(controls_list):
                control_text = control.window_text()
                
                if control_text == "Department ID:":
                    if i + 1 < len(controls_list):
                        department_id = controls_list[i+1].window_text()
                
                elif control_text == "Department:":
                    if i + 1 < len(controls_list):
                        department_name = controls_list[i+1].window_text()

            # Final check to see if all details were captured
            if all([department_sale_title, department_id, department_name]):
                 print("\n- Successfully captured all department details:")
                 print(f"  - Title: {department_sale_title}")
                 print(f"  - ID: {department_id}")
                 print(f"  - Name: {department_name}")
            else:
                print("\n- Warning: Not all department details were captured.")

            # --- 2. Find and enter the price ---
            # print("\nAttempting to find the price input field...")
            # price_input = price_screen_view.child_window(auto_id="tbPrice_InnerText", control_type="Edit")
            # price_input.wait('visible', timeout=10)
            # print(f"- Found price input field. Entering price: {price}")
            # price_input.set_edit_text(price)
            # time.sleep(1)

            if not numpad_keyin(number= price, OKclick=False):
                print("- Error: Failed to enter the price using the virtual numpad.")
                return False

            # --- 3. Find the 'Approve' and 'Cancel' buttons ---
            print("Attempting to find 'Approve' and 'Cancel' buttons...")
            approve_button = price_screen_view.child_window(title="Approve", control_type="Button")
            cancel_button = price_screen_view.child_window(title="Cancel", control_type="Button")

            if approve_button.exists() and approve_button.is_visible():
                print(f"- Found 'Approve' button. Enabled: {approve_button.is_enabled()}")
            else:
                print("- Could not find 'Approve' button.")
                return False

            if cancel_button.exists() and cancel_button.is_visible():
                print(f"- Found 'Cancel' button. Enabled: {cancel_button.is_enabled()}")
            else:
                print("- Could not find 'Cancel' button.")

            # --- 4. Click the 'Approve' button ---
            print("- Clicking 'Approve' button...")
            approve_button.click_input() # Uncomment to perform the click
            print("- 'Approve' button click simulated.")
            time.sleep(3) # Pause to observe the result

        except timings.TimeoutError as e:
            print(f"\nError: Timed out waiting for an element on the price screen to appear. Details: {e}")
            return False
        except Exception as e:
            print(f"An error occurred while analyzing the price screen: {e}")
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
    # You can change the price passed to the function here
    if enter_item_price(price="5.99"):
        print("\nPrice entry script finished successfully.")
    else:
        print("\nPrice entry script finished failed.")

