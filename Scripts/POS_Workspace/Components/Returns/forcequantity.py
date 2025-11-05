"""
================================================================================
 Force Quantity Screen Handler
================================================================================

PURPOSE:
--------
This module is responsible for handling the "Force Quantity" or "Return Quantity"
pop-up window that appears in the POS application. It is designed to be a 
reusable component that can be imported and called from other automation scripts.

The main function, `adjust_return_quantity`, provides a single entry point to:
1. Connect to the specific quantity pop-up window.
2. Read the current data from the window (product name, quantity).
3. Programmatically adjust the quantity to a specified target by clicking the
   '+' and '-' buttons.
4. Confirm the new quantity by clicking the "OK" button.

The script is structured with private helper functions for internal logic and
a main public function for external use. It can also be run as a standalone
script for testing and debugging purposes.

"""
import json
import time
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError

# ==============================================================================
# SECTION 1: HELPER FUNCTIONS
# ==============================================================================

def _extract_window_data(win):
    """
    Private helper function to extract all required data and controls from the window.
    """
    product_title = "Title not found"
    try:
        # Focus search on the specific container for the content
        custom_view = win.child_window(auto_id="QuantityPickerViewID", control_type="Custom")
        all_descendants = custom_view.descendants()
        
        # Gather all unique, non-empty text elements within the container
        all_found_texts = {
            c.window_text() for c in all_descendants 
            if c.window_text() and c.window_text().strip()
        }

        # Define a set of known static text elements to ignore when finding the title
        known_texts = {"How many items to return?", "+", "-", "OK", "Cancel"}
        
        # Add the current quantity to the ignore list as well
        try:
            quantity_text = custom_view.child_window(auto_id="innerText", control_type="Edit").window_text()
            if quantity_text:
                known_texts.add(quantity_text)
        except ElementNotFoundError:
            pass # It's okay if the quantity field isn't found here

        # The product title is the remaining text after filtering out known elements
        possible_titles = all_found_texts - known_texts
        if possible_titles:
            product_title = possible_titles.pop()

    except Exception as e:
        print(f"⚠️ Warning: An error occurred while searching for the product title: {e}")

    quantity_element = win.child_window(auto_id="innerText", control_type="Edit")

    # Return a dictionary containing both the extracted data and the pywinauto control objects
    return {
        "data": {
            "product_title": product_title,
            "prompt_message": win.child_window(auto_id="MessageTextBox", control_type="Edit").window_text(),
            "current_quantity": quantity_element.window_text(),
        },
        "controls": {
            "ok": win.child_window(title="OK", control_type="Button"),
            "cancel": win.child_window(title="Cancel", control_type="Button"),
            "plus": win.child_window(title="+", control_type="Button"),
            "minus": win.child_window(title="-", control_type="Button"),
            "quantity_edit": quantity_element,
        }
    }

def _find_and_prepare_window():
    """
    Connects to the application window and returns the window object.
    """
    window_title_regex = ".*TransactionBasedReturnQuantityPickerViewModel.*"
    try:
        print(f"Attempting to connect to window: '{window_title_regex}'...")
        app = Application(backend="uia").connect(title_re=window_title_regex, timeout=10)
        win = app.window(title_re=window_title_regex)
        win.set_focus()
        print("✅ Successfully connected to the window.")
        return win
    except (ElementNotFoundError, TimeoutError):
        print(f"❌ ERROR: Window not found.")
        print("Please ensure the application and the dialog are open and visible.")
        return None

# ==============================================================================
# SECTION 2: MAIN REUSABLE FLOW FUNCTION
# ==============================================================================

def adjust_return_quantity(target_quantity):
    """
    Finds the return quantity screen, adjusts the quantity to the target value,
    and confirms. This is the single entry point for the entire flow.

    Args:
        target_quantity (int): The desired quantity to set on the screen.

    Returns:
        bool: True if the quantity was adjusted and confirmed successfully, False otherwise.
    """
    print("\n--- Starting Return Quantity Adjustment Flow ---")
    print(f"🎯 Target quantity set to: {target_quantity}")
    
    win = _find_and_prepare_window()
    if not win:
        return False

    window_info = _extract_window_data(win)

    # Print the captured data for logging and debugging
    print("\n--- Captured Window Data ---")
    print(json.dumps(window_info['data'], indent=4))
    print("--------------------------")
    
    controls = window_info['controls']
    quantity_edit = controls['quantity_edit']

    print("\n--- Adjusting Quantity to Target ---")
    if not all(controls.values()):
        print("❌ ERROR: Missing one or more required controls. Cannot adjust quantity.")
        return False
        
    try:
        max_attempts = 25  # A safety break to prevent potential infinite loops
        for _ in range(max_attempts):
            current_quantity_str = quantity_edit.window_text()
            current_quantity = int(current_quantity_str)

            print(f"  - Current: {current_quantity}, Target: {target_quantity}")

            if current_quantity == target_quantity:
                print("✅ Quantity matches the target.")
                break
            
            elif current_quantity < target_quantity:
                print("  - Clicking '+' button...")
                controls['plus'].click_input()
            
            else: # current_quantity > target_quantity
                print("  - Clicking '-' button...")
                controls['minus'].click_input()

            time.sleep(0.4)
        else:
            # This block runs if the loop finishes without hitting 'break'
            print("⚠️ Reached max attempts. The quantity may not have been set correctly.")
            return False

        print("\n🖱️ Clicking 'OK' button to confirm...")
        controls['ok'].click_input()
        print("✅ 'OK' button clicked. Flow complete.")
        return True

    except ValueError:
        print(f"❌ ERROR: Could not convert current quantity ('{current_quantity_str}') to a number.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred during quantity adjustment: {e}")
        return False

# ==============================================================================
# SECTION 3: EXECUTABLE BLOCK FOR STANDALONE TESTING
# ==============================================================================

if __name__ == "__main__":
    print("--- Running Return Quantity Handler in standalone mode for testing ---")
    
    # Define the quantity you want to set for this test run.
    test_target_quantity = 5

    # Run the entire reusable flow.
    success = adjust_return_quantity(test_target_quantity)

    if success:
        print("\n✅ Standalone test completed successfully.")
    else:
        print("\n❌ Standalone test failed.")

