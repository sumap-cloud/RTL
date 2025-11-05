# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: handle_approval_popup
# @Purpose: Manages approval workflows with credential entry on popup dialogs
# @Dependencies: pywinauto.Application
# @Input_Params: approval_required, first_username, first_password
# @Return_Values: Boolean indicating success/failure of approval process
# @Used_By_Tests: TC008_nrr_scenario, Various approval-requiring tests
# @Known_Limitations: Requires specific virtual keyboard to be available, has fallback credentials
# ============================================

from pywinauto import Application
import time

def handle_approval_popup(approval_required=None, first_username=None, first_password=None):
    """
    Finds the 'Approval Required' popup and enters credentials using a virtual keyboard.
    Includes logic to retry with alternate credentials if the first attempt fails.
    Returns:
        bool: True if approval was handled successfully, False otherwise.
    """
    if not approval_required:
        print("\n✓ Approval not required for this operation.")
        return True

    try:
        # --- Connection and Window Setup ---
        application_window_title = "Retalix.Client.POS.Presentation.ViewModels.BRM.ManagerApprovalViewModel"
        print(f"--- Attempting to connect to window: '{application_window_title}' ---")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("✅ Successfully connected to the window.")

        # --- User Credentials ---
        # Use provided credentials or fall back to defaults
        username_to_enter = first_username if first_username else "Admin"
        password_to_enter = first_password if first_password else "Password123"
        
        # Second attempt (if first fails)
        username_retry = "Atmgr5"
        password_retry = "abcd1234"

        # --- Virtual Keyboard Logic ---
        key_map = {
            'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g',
            'h': 'h', 'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
            'o': 'o', 'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u',
            'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z',
            'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G',
            'H': 'H', 'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N',
            'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T', 'U': 'U',
            'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
            '7': '7', '8': '8', '9': '9'
        }
        is_caps_on = False

        def toggle_caps():
            """Clicks the caps lock button and updates its state."""
            nonlocal is_caps_on
            try:
                caps_button = win.child_window(title_re=".*A ↔ a.*", control_type="Button")
                if caps_button.exists(timeout=2):
                    caps_button.click_input()
                    is_caps_on = not is_caps_on
                    print(f"Toggled Caps Lock. New state: {'ON' if is_caps_on else 'OFF'}")
                    time.sleep(0.2)
                else:
                    print("Warning: Could not find Caps Lock button.")
            except Exception as e:
                print(f"Error clicking Caps Lock button: {e}")

        def type_with_virtual_keyboard(text_to_type):
            """Simulates typing using the virtual keyboard, handling case correctly."""
            nonlocal is_caps_on
            for char in text_to_type:
                if char.isalpha():
                    should_be_upper = char.isupper()
                    if (should_be_upper and not is_caps_on) or \
                       (not should_be_upper and is_caps_on):
                        toggle_caps()

                if char in key_map:
                    key_name = key_map[char]
                    try:
                        key_button = win.child_window(title=key_name, control_type="Button")
                        if key_button.exists(timeout=2):
                            key_button.click_input()
                            print(f"Clicked '{key_name}'")
                            time.sleep(0.1)
                        else:
                            print(f"Warning: Could not find key: '{key_name}'")
                    except Exception as e:
                        print(f"Error clicking key '{key_name}': {e}")
                else:
                    print(f"Warning: Character '{char}' not in key_map")

        # --- Interact with UI Elements ---
        print("Locating User Name field...")
        username_field = win.child_window(auto_id="ValueTextBox", control_type="Edit")
        if username_field.exists(timeout=5):
            username_field.wait("ready", timeout=10).click_input()
            print(f"Typing username: '{username_to_enter}'")
            type_with_virtual_keyboard(username_to_enter)
        else:
            print("Error: User Name field not found.")
            return False

        print("Locating Password field...")
        password_field = win.child_window(auto_id="Password", control_type="Edit")
        if password_field.exists(timeout=5):
            password_field.wait("ready", timeout=10).click_input()
            print("Typing password...")
            type_with_virtual_keyboard(password_to_enter)
        else:
            print("Error: Password field not found.")
            return False

        print("Locating and clicking the OK button...")
        ok_button = win.child_window(title="OK", control_type="Button")
        if ok_button.exists(timeout=5):
            ok_button.wait("ready", timeout=10).click()
            print("OK button clicked for the first attempt.")
        else:
            print("Error: OK button not found.")
            return False

        # --- Retry Logic ---
        time.sleep(1) # Wait for the UI to potentially show an error
        error_message = win.child_window(title="Invalid User Name or Password", control_type="Text")
        
        if error_message.exists(timeout=2):
            print("Login failed. Retrying with alternate credentials.")
            
            # Clear username field
            username_field.click_input()
            backspace_button = win.child_window(title="<<", control_type="Button")
            for _ in range(len(username_to_enter)):
                backspace_button.click_input()
                time.sleep(0.05)
            
            # Type new username
            print(f"Typing new username: '{username_retry}'")
            type_with_virtual_keyboard(username_retry)

            # Clear password field
            password_field.click_input()
            for _ in range(len(password_to_enter)):
                backspace_button.click_input()
                time.sleep(0.05)

            # Type new password
            print("Typing new password...")
            type_with_virtual_keyboard(password_retry)
            
            # Click OK again
            if ok_button.exists(timeout=5):
                ok_button.wait("ready", timeout=10).click()
                print("OK button clicked for the second attempt. Automation complete.")
            else:
                print("Error: OK button not found for retry.")
                return False
        else:
            print("Login successful on the first attempt. Automation complete.")
        
        return True

    except Exception as e:
        print(f"An error occurred during automation: {e}")
        return False

def main():
    """
    Main function to trigger the approval popup handling.
    """
    # Example of calling with default credentials
    handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234")

    # Example of calling with custom credentials (uncomment to use)
    # handle_approval_popup(approval_required=True, first_username="your_user", first_password="your_password")


if __name__ == "__main__":
    print("Please ensure the 'Approval Required' popup is open on the screen.")
    print("Starting automation in 3 seconds...")
    time.sleep(3)
    main()

