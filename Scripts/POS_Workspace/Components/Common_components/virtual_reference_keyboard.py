# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: virtual_reference_keyboard
# @Purpose: Simulates typing on the POS on-screen alphanumeric keyboard
# @Dependencies: pywinauto.Application
# @Input_Params: enter (string to type)
# @Return_Values: None
# @Used_By_Tests: Multiple test cases including TC001-TC008
# @Known_Limitations: Limited special character support, case-sensitivity handling
# ============================================

from pywinauto import Application
import time

def Virtual_keyboard_reference(enter=""):
    """
    Connects to the POS application, finds the virtual keyboard,
    and types the provided string, handling mixed-case characters.

    Args:
        enter (str): The string to be typed into the virtual keyboard.
    """
    if not enter:
        print("Error: No string provided to type.")
        return

    print(f"--- Starting Virtual Keyboard Automation to type: '{enter}' ---")

    try:
        # --- Connection Setup ---
        application_window_title = ".*R10PosClient.*"
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()

        # Assuming the virtual keyboard is a popup window
        virtualKayboard = win.child_window(class_name="Popup")
        virtualKayboard.wait('ready', timeout=10)
        print("Virtual keyboard found.")

    except Exception as e:
        print(f"Could not find the application or virtual keyboard. Error: {e}")
        return # Exit the function if setup fails

    # --- Nested Helper Function ---
    def click_key(key_title):
        """Finds a key by its title and clicks it."""
        try:
            # Use descendants to find the button within the keyboard window
            button = virtualKayboard.descendants(title=key_title, control_type="Button")[0]
            print(f"Clicking '{key_title}'")
            button.click_input()
            time.sleep(0.2) # A small delay for stability
            return True
        except IndexError:
            print(f"Button '{key_title}' not found")
            return False
        except Exception as e:
            print(f"An error occurred when trying to click '{key_title}': {e}")
            return False

    # --- Nested Main Typing Logic ---
    def type_string(text_to_type):
        """Types a mixed-case string by handling capital letters."""
        caps_lock_button = "A ↔ a"
        
        for char in text_to_type:
            if 'a' <= char <= 'z' or '0' <= char <= '9':
                if not click_key(char): return False
            elif 'A' <= char <= 'Z':
                print(f"--- Handling capital letter: {char} ---")
                if not click_key(caps_lock_button): return False
                if not click_key(char): return False
                if not click_key(caps_lock_button): return False
                print(f"--- Finished handling: {char} ---")
            else:
                print(f"Character '{char}' is not standard and will be skipped.")
        
        return True

    # --- Script Execution ---
    if type_string(enter):
        print("\nString typed successfully.")
        if click_key("OK"):
            print("Clicked 'OK'. Automation finished.")
        else:
            print("Could not click 'OK' button.")
    else:
        print("\nAutomation failed during typing.")

# --- Example of how to call this function from another file ---
# To use this in another script, you would do:
#
# from virtual_keyboard_automation import Virtual_keyboard
#
# Virtual_keyboard(enter="YourTextHere123")
#
if __name__ == "__main__":
    # This block allows you to run this script directly for testing
    Virtual_keyboard_reference(enter="ATmgr5")

