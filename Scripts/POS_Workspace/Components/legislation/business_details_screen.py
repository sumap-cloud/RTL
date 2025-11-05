# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: business_tax_details
# @Purpose: Manages entry of business tax information for receipts and invoices
# @Dependencies: Virtual_keyboard_reference, numpad_keyin
# @Input_Params: details - Dictionary containing business name, street, suburb, tax_number
# @Return_Values: Boolean success/failure of business details entry
# @Used_By_Tests: TC003_customer_tax_details_scenario
# @Known_Limitations: Some field validation depends on specific UI state
# ============================================

from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
# This setup allows the script to find custom modules in the project.
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Corrected the typo in the import path ('vertual' -> 'virtual')
from Components.Common_components.virtual_reference_keyboard import Virtual_keyboard_reference
from Components.Common_components.virtual_numpad import numpad_keyin


def business_tax_details(details):
    """
    Connects to the R10PosClient application and fills in the tax business details screen.

    This function is designed to be reusable by accepting a dictionary of details to fill in.

    Args:
        details (dict): A dictionary containing the business details.
                        Example: {
                            "business_name": "ATmgr5",
                            "street": "MainStreet",
                            "suburb": "Sydney",
                            "tax_number": "1227"
                        }

    Returns:
        bool: True if the automation completes successfully, False otherwise.
    """
    try:
        # 1. Connect to the application
        print("Connecting to the application...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=20)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("Successfully connected to the main window.")

        # Locate the specific view for tax details
        tax_screen_view = win.child_window(auto_id="AddTaxDetailsView", control_type="Custom")
        tax_screen_view.wait('visible', timeout=10)
        print("Tax details screen is visible.")


        # 2. Helper function to reduce repetitive code for text entry
        def _enter_text_with_keyboard(auto_id, text_to_enter, field_label):
            """Finds a field by auto_id, clicks its keyboard button, and enters text."""
            print(f"--- Entering '{field_label}' ---")
            wrapper = tax_screen_view.child_window(auto_id=auto_id)
            keyboard_button = wrapper.child_window(control_type="Button")
            
            if keyboard_button.exists():
                keyboard_button.click_input()
                time.sleep(0.5)
                Virtual_keyboard_reference(enter=text_to_enter)
                time.sleep(0.5)
                print(f"✅ Entered '{text_to_enter}' into {field_label}.")
                return True
            else:
                print(f"❌ Virtual keyboard button for '{field_label}' not found.")
                return False

        # 3. Fill in the form fields using the helper function
        if not _enter_text_with_keyboard("BuisnessNameTextControl", details["business_name"], "Business Name"): return False
        if not _enter_text_with_keyboard("StreetAddressTextControl", details["street"], "Street Address"): return False
        if not _enter_text_with_keyboard("SuburbTextControl", details["suburb"], "Suburb"): return False

        # 4. Interact with Numpad for Tax Number
        print("--- Entering 'Tax Number' ---")
        tax_number_wrapper = tax_screen_view.child_window(auto_id="TaxNumberControl")
        if tax_number_wrapper.exists():
            # Assuming the numpad is context-aware and appears on focus
            tax_number_wrapper.click_input() 
            time.sleep(0.5)
            numpad_keyin(number=details["tax_number"], OKclick=True)
            print(f"✅ Entered '{details['tax_number']}' into Tax Number.")
        else:
            print("❌ Tax Number input field not found.")
            return False

        # 5. Click the 'Confirm' button to submit
        print("\n--- Submitting Form ---")
        confirm_button = tax_screen_view.child_window(title="Confirm", control_type="Button")
        if confirm_button.exists():
            print("Clicking the 'Confirm' button...")
            confirm_button.click_input()
            print("✅ Form submitted successfully.")
            return True
        else:
            print("❌ 'Confirm' button not found.")
            return False

    except Exception as e:
        print(f"❌ An unexpected error occurred during tax details automation: {e}")
        return False

# --- Main Execution Block ---
# This part of the script only runs when you execute it directly.
# It allows you to test the 'automate_tax_details' function independently.
if __name__ == "__main__":
    print("Running Tax Details automation script directly for testing...")

    # Define the test data to be entered into the form
    test_business_details = {
        "business_name": "TestCorp",
        "street": "123 Automation Ave",
        "suburb": "Tech City",
        "tax_number": "122776"
    }
    
    # Call the main function and check its boolean return value
    if business_tax_details(test_business_details):
        print("\n--- Standalone Test PASSED ---")
    else:
        print("\n--- Standalone Test FAILED ---")
