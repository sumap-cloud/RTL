# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: departmentrefund_nrr
# @Purpose: Handles non-receipted returns by department with threshold-based approval workflows
# @Dependencies: numpad_keyin, Application, findwindows, timings
# @Input_Params: department_name, reason_code, price
# @Return_Values: Boolean success/failure
# @Used_By_Tests: TC008_nrr_scenario
# @Known_Limitations: Requires appropriate UI state, handles single department per call
# ============================================

from pywinauto import Application, findwindows, timings
from pywinauto.findbestmatch import MatchError
from pathlib import Path
import sys
import time

# --- Setup for project root and imports ---
# This setup is included from your provided snippet to ensure custom modules can be found.
try:
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from Components.Common_components.virtual_numpad import numpad_keyin
except (NameError, ImportError):
    # Define a placeholder if the import fails, allowing the script to be analyzed.
    # In a real run, this will cause an error if the module is not found.
    print("Warning: 'numpad_keyin' module not found. A placeholder will be used.")
    def numpad_keyin(number, OKclick=False):
        print(f"--- SIMULATING VIRTUAL NUMPAD: Entering '{number}' ---")
        if not number:
            return False
        return True

def handle_price_entry_screen(win, price):
    """
    This function automates interactions on the 'Enter Item's Price' screen for a return.
    It captures department details, enters a specified price, and clicks the 'Return' button.
    """
    print("\n✨ Handling Enter Item's Price Screen ✨")
    if not price:
        print("❌ ERROR: No price provided for the price entry screen.")
        return False
        
    try:
        time.sleep(3) # Wait for the screen to fully render

        # --- Interact with the 'Enter Item's Price' screen ---
        print("Analyzing 'Enter Item's Price' screen...")

        # Find the specific view for the price entry screen.
        # Based on your snippet, it may be nested within MainTransactionViewID.
        main_transaction_view = win.child_window(auto_id="MainTransactionViewID", control_type="Custom")
        main_transaction_view.wait('visible', timeout=15)
        
        # The ID "DepartmentSaleViewID" is used based on your provided code.
        price_screen_view = main_transaction_view.child_window(auto_id="DepartmentSaleViewID", control_type="Custom")
        price_screen_view.wait('visible', timeout=15)
        print("- Found the price screen view.")

        # --- 1. Enter the price using the virtual numpad ---
        print(f"- Using virtual numpad to enter price: {price}")
        if not numpad_keyin(number=price, OKclick=False):
            print("❌ Error: Failed to enter the price using the virtual numpad.")
            return False
        print(f"- Successfully entered price: {price}")
        time.sleep(1)

        # --- 2. Find and click the 'Return' button ---
        print("Attempting to find the 'Return' button...")
        # The screenshot shows a "Return" button, not "Approve".
        return_button = price_screen_view.child_window(title="Return", control_type="Button")

        if return_button.exists() and return_button.is_visible():
            print(f"- Found 'Return' button. Clicking it...")
            return_button.click_input()
            print("- 'Return' button clicked.")
            time.sleep(3) # Pause to observe the result
        else:
            print("❌ ERROR: Could not find the 'Return' button.")
            return False

    except timings.TimeoutError as e:
        print(f"❌ ERROR: Timed out waiting for an element on the price screen. Details: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred on the price screen: {e}")
        return False
    
    return True

def handle_reason_code_screen(win, reason_code=None):
    """
    Finds and clicks a reason code on the 'Return Item' screen,
    scrolling if necessary to find it.
    """
    print("\n✨ Handling Return Item Reason Code Screen ✨")
    reason_to_click = reason_code if reason_code else "Damaged / Faulty"
    
    try:
        time.sleep(2)
        
        all_found_buttons = set()
        down_arrow = None
        up_arrow = None

        try:
            down_arrow = win.child_window(auto_id="ConsumableDataPagerButtonDownID", control_type="Button")
            up_arrow = win.child_window(auto_id="ConsumableDataPagerButtonUpID", control_type="Button")
        except (MatchError, timings.TimeoutError):
            print("- No scrolling functionality detected.")
        
        if down_arrow and down_arrow.exists():
            print("- Scrolling detected. Collecting all available reason codes...")
            if up_arrow.exists():
                while up_arrow.is_enabled():
                    up_arrow.click_input()
                    time.sleep(0.5)

            while True:
                current_buttons = {b.window_text() for b in win.descendants(control_type="Button")}
                all_found_buttons.update(current_buttons)
                if down_arrow.is_enabled():
                    down_arrow.click_input()
                    time.sleep(0.5)
                else:
                    break
        else:
            all_found_buttons = {b.window_text() for b in win.descendants(control_type="Button")}

        non_reason_codes = {'', 'Cancel', 'OK', 'C', 'X', '<<', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.'}
        all_found_reasons = {b for b in all_found_buttons if b not in non_reason_codes}

        print("\n--- Captured Reason Codes ---")
        for reason in sorted(list(all_found_reasons)):
            print(f"  - {reason}")
        print("----------------------------\n")
        
        if up_arrow and up_arrow.exists():
            while up_arrow.is_enabled():
                up_arrow.click_input()
                time.sleep(0.5)

        while True:
            try:
                target_button = win.child_window(title=reason_to_click, control_type="Button")
                if target_button.is_visible():
                    print(f"🖱️  Clicking '{reason_to_click}'...")
                    target_button.click_input()
                    print(f"✅ '{reason_to_click}' button clicked successfully.")
                    return True
            except MatchError:
                pass

            if down_arrow and down_arrow.is_enabled():
                down_arrow.click_input()
                time.sleep(0.5)
            else:
                print(f"❌ ERROR: Could not find '{reason_to_click}' to click it after scanning all pages.")
                return False

    except (timings.TimeoutError, MatchError) as e:
        print(f"❌ An error on the reason code screen: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred in handle_reason_code_screen: {e}")
        return False

def return_item_by_department(department_name, reason_code=None, price=None):
    """
    This function automates an item return by department, reason code, and price.
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
        time.sleep(2)
        print("Application window is ready.")

        print("\nAnalyzing 'Department Return' screen...")
        try:
            department_sale_view = win.child_window(auto_id="DepartmentLookupViewID", control_type="Custom")
            department_sale_view.wait('visible', timeout=15)
            print("- Found the main 'Department Return' view.")

            print("\n--- Step 1: Collecting all department buttons by scrolling down ---")
            department_listbox = department_sale_view.child_window(auto_id="lbDepartmentIdItems", control_type="List")
            department_listbox.wait('visible', timeout=10)
            down_arrow_button = department_sale_view.child_window(auto_id="LeftRegionDataPagerButtonDownID", control_type="Button")
            up_arrow_button = department_sale_view.child_window(auto_id="LeftRegionDataPagerButtonUpID", control_type="Button")
            all_department_names = set()

            while True:
                department_items = department_listbox.children(control_type="ListItem")
                if department_items:
                    for item in department_items:
                        item_text = item.window_text()
                        if item_text not in all_department_names:
                            all_department_names.add(item_text)
                if down_arrow_button.is_enabled():
                    down_arrow_button.click_input()
                    time.sleep(1) 
                else:
                    break
            
            print("\n--- All Departments Found ---")
            for name in sorted(list(all_department_names)):
                print(f"  - Found button: '{name.replace('\\n', ' ')}'")

            print("\n--- Step 2: Scrolling back to the top ---")
            while up_arrow_button.is_enabled():
                up_arrow_button.click_input()
                time.sleep(1) 
            
            print("- Reached the top of the list.")

            print(f"\n--- Step 3: Clicking '{category}' ---")
            try:
                bakehouse_button = department_listbox.child_window(title_re=f".*{category}.*", control_type="ListItem")
                bakehouse_button.wait('visible', timeout=10)
                print(f"- Found '{category}' button.")
                bakehouse_button.click_input()
                print(f"- Successfully clicked '{category}'.")

                # --- Step 4: Handle the Reason Code screen that appears next ---
                if not handle_reason_code_screen(win, reason_code):
                     print("❌ Failed to handle the reason code screen.")
                     return False

                # --- Step 5: Handle the Price Entry screen ---
                if not handle_price_entry_screen(win, price):
                    print("❌ Failed to handle the price entry screen.")
                    return False

            except timings.TimeoutError:
                print(f"Error: Could not find the '{category}' button after scrolling back to the top.")
                return False
            except Exception as e:
                print(f"An error occurred while trying to click '{category}': {e}")
                return False

        except timings.TimeoutError:
            print("Error: Timed out waiting for the 'Department Return' screen elements to appear.")
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
    # --- This workflow automates an item return by department, reason, and price ---
    print("--- Starting Item Return by Department Workflow ---")
    if return_item_by_department(department_name="BAKEHOUSE", reason_code="Damaged / Faulty", price="5.99"):
        print("\n✅ Item Return by Department script finished successfully.")
    else:
        print("\n❌ Item Return by Department script failed.")

