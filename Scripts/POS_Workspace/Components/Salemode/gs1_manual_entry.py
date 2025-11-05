from pywinauto import Application, findwindows
import sys
from pathlib import Path
import time


current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Scripts.POS_Workspace.Components.Common_components.virtual_numpad import numpad_keyin

def handle_Any_popup():
    """
    Waits for a specific popup window and clicks a predefined button on it.
    This is used to handle error or confirmation popups that may appear.
    Returns:
        bool: True if a popup was found and a button was successfully clicked,
              False otherwise.
    """
    # --- Configuration ---
    window_title_pattern = r".*Retalix\.(Woolworths\.)?Client\.POS\.Presentation\.ViewModels.*"
    buttons_to_click = ["Cancel", "Close", "Skip", "No", "OK"]
    wait_timeout = 3 # Short timeout as this is a quick check

    print(f"\nChecking for a popup window matching: '{window_title_pattern}'...")

    try:
        app = Application(backend="uia").connect(title_re=window_title_pattern, timeout=wait_timeout)
        win = app.window(title_re=window_title_pattern)
        print(f"[SUCCESS] Popup window found with title: '{win.window_text()}'")
        win.set_focus()

        for button_text in buttons_to_click:
            try:
                button_to_click = win[button_text]
                if button_to_click.exists() and button_to_click.is_enabled():
                    print(f"Found clickable button: '{button_text}'. Clicking it now...")
                    button_to_click.click()
                    print("[ACTION] Button clicked successfully.")
                    time.sleep(1)
                    return True # Popup was successfully handled
            except findwindows.ElementNotFoundError:
                continue # This button wasn't found, try the next one
        
        print("[INFO] Popup found, but no specified buttons were found to click.")
        return False # Popup found but not handled

    except findwindows.ElementNotFoundError:
        print("[INFO] No popup found on screen.")
        return False # No popup, so not handled
    except Exception as e:
        print(f"An error occurred while checking for popup: {e}")
        return False # Error occurred, so not handled

def automate_gs1_screen(Gs1Amount):
    """
    Connects to the R10PosClient application and automates the GS1 barcode
    manual entry screen.
    Returns True on success, False on failure.
    """
    try:
        # Step 1: Connect to the running application
        print("Connecting to the application...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        
        # Get the main application window
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("Successfully connected to the main window.")
        time.sleep(1)

        # Step 2: Access the GS1 Manual Entry child window
        print("Accessing the barcode info screen...")
        barcode_screen = win.child_window(
            class_name="Gs1DatabarManualEntryView", 
            auto_id="Gs1DatabarManualEntryViewID"
        )
        barcode_screen.wait('visible', timeout=10)
        print("Barcode info screen is visible.")

        # --- Part 1: Capturing Initial Data ---
        print("\n--- Capturing Initial Data ---")
        gtin_label = barcode_screen.child_window(title="GTIN:", control_type="Text")
        gtin_value = barcode_screen.child_window(title_re=r"^\(01\)", control_type="Text")
        price_label = barcode_screen.child_window(title="Price($):", control_type="Text")
        price_value = barcode_screen.child_window(title="15.00", control_type="Text")

        if gtin_label.exists() and gtin_value.exists():
            print(f"Captured Text: {gtin_label.window_text()} {gtin_value.window_text()}")
        if price_label.exists() and price_value.exists():
             print(f"Captured Text: {price_label.window_text()} {price_value.window_text()}")

        # --- Part 2: Performing Actions & Capturing Dynamic Data ---
        print("\n--- Performing Actions & Capturing Dynamic Data ---")
        
        quick_sale_yes_radio = barcode_screen.child_window(title="Yes", control_type="RadioButton", found_index=0)
        if quick_sale_yes_radio.exists():
            print("Selecting 'Yes' for Quick Sale...")
            quick_sale_yes_radio.click_input()
            time.sleep(1)

            original_price_label = barcode_screen.child_window(title="Original Price($):", control_type="Text")
            original_price_value = barcode_screen.child_window(title="15.00", control_type="Text")
            
            if original_price_label.wait('visible', timeout=5) and original_price_value.exists():
                print(f"Captured Dynamic Text: {original_price_label.window_text()} {original_price_value.window_text()}")
            else:
                print("Could not find 'Original Price($):' field after selection.")

            price_input_container = barcode_screen.child_window(auto_id="PriceTextControl", control_type="ListItem")
            if price_input_container.wait('visible', timeout=5):
                price_edit_box = price_input_container.child_window(control_type="Edit")
                if price_edit_box.wait('visible', timeout=2):
                     print("Entering new price into the Price($) input box...")
                     price_edit_box.click_input()
                     time.sleep(0.5)
                     numpad_keyin(number=Gs1Amount, OKclick=False)
                else:
                     print("Could not find the editable input box for Price($).")
            else:
                print("Could not find the container for the Price($) input box.")
        else:
            print("Could not find 'Quick Sale' radio button.")
            return False

        expiry_date_yes_radio = barcode_screen.child_window(title="Yes", control_type="RadioButton", found_index=1)
        if expiry_date_yes_radio.exists():
            print("Selecting 'Yes' for Expiry Date...")
            expiry_date_yes_radio.click_input()
            time.sleep(1)

            expiry_label = barcode_screen.child_window(title_re="^Expiry/ Best before/ Sell By Date.*", control_type="Text")
            if expiry_label.exists():
                 print(f"Verified label is visible: '{expiry_label.window_text().strip()}'")
            else:
                print("Could not find 'Expiry/ Best before...' label.")
            
            date_edit_box = barcode_screen.child_window(auto_id="DateTextBox", control_type="Edit")
            if date_edit_box.exists():
                print("Entering Expiry Date via virtual numpad...")
                date_edit_box.click_input()
                time.sleep(0.5)
                numpad_keyin(number="31122025", OKclick=False)
                time.sleep(1)
            else:
                print("Could not find the Expiry Date text box.")
        else:
            print("Could not find 'Expiry Date' radio button.")
            return False

        # --- Part 3: Clicking Buttons ---
        print("\n--- Clicking Buttons ---")

        confirm_button = barcode_screen.child_window(title="Confirm", control_type="Button", auto_id="CommandButton")
        if confirm_button.exists():
            print("Clicking the 'Confirm' button...")
            confirm_button.click()
            time.sleep(2) # Wait for potential popup

            # --- MODIFIED SECTION START ---
            # Check if a popup appeared after confirming
            if handle_Any_popup():
                print("\nPopup was detected and handled. Re-entering new amount...")
                
                # Re-enter the new price as requested
                price_input_container = barcode_screen.child_window(auto_id="PriceTextControl", control_type="ListItem")
                if price_input_container.wait('visible', timeout=5):
                    price_edit_box = price_input_container.child_window(control_type="Edit")
                    if price_edit_box.wait('visible', timeout=2):
                         print("Entering new price '10.00'...")
                         price_edit_box.click_input()
                         time.sleep(0.5)
                         numpad_keyin(number="10.00", OKclick=False)
                    else:
                         print("Could not find editable price box for second attempt.")
                         return False
                else:
                    print("Could not find price input container for second attempt.")
                    return False
                
                # Find and click the confirm button again
                confirm_button_again = barcode_screen.child_window(title="Confirm", control_type="Button", auto_id="CommandButton")
                if confirm_button_again.exists():
                    print("Clicking the 'Confirm' button again...")
                    confirm_button_again.click()
                else:
                    print("Could not find the 'Confirm' button for the second click.")
                    return False
            # --- MODIFIED SECTION END ---

            print("Automation script finished successfully.")
            time.sleep(1)
            return True
        else:
            print("Could not find the 'Confirm' button.")
            return False
            
    except Exception as e:
        print(f"An error occurred during GS1 automation: {e}")
        return False

if __name__ == "__main__":
    print("Running GS1 automation script directly for testing...")
    if automate_gs1_screen("25.00"):
        print("\n--- Standalone Test PASSED ---")
    else:
        print("\n--- Standalone Test FAILED ---")

