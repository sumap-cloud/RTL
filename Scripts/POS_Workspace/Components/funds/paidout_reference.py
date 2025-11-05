from pywinauto.application import Application
import time

# --- Configuration ---
app_title = ".*R10PosClient.*"  # Regex for the application title
# Using a dictionary to map numpad digits to their control identifiers.
numpad_buttons = {
    '1': "1", '2': "2", '3': "3", '4': "4", '5': "5",
    '6': "6", '7': "7", '8': "8", '9': "9", '0': "0",
    '.': ".", 'OK': "OK", 'Clear': "C", 'Backspace': "<<", 'X': "X"
}

def press_numpad_keys(window, key_sequence):
    """
    Presses a sequence of on-screen numpad buttons.

    Args:
        window: The pywinauto window object.
        key_sequence (str or list): A string or list of characters/keys to press.
    """
    print(f"Executing numpad sequence: {list(key_sequence)}")
    for key in key_sequence:
        try:
            # Find the button by its 'auto_id' which is more reliable.
            button = window.child_window(auto_id=numpad_buttons[key], control_type="Button")
            if button.exists():
                print(f"Clicking button '{key}'")
                # Using click_input() for better reliability
                button.click_input()
                time.sleep(0.1) # Small delay between clicks for stability
            else:
                print(f"Warning: Button '{key}' with auto_id '{numpad_buttons[key]}' not found.")
        except KeyError:
            print(f"Error: Key '{key}' not found in the numpad_buttons dictionary.")
        except Exception as e:
            print(f"Error clicking button '{key}': {e}")


def paidout_finalize(reference_number, gst_amount):
    """
    Main function to connect, enter details, and handle approval popup.
    """
    #reference_number = "TestRef123"
    #gst_amount = "25.50"  # The GST amount you want to enter

    try:
        # --- Step 1: Connect to the Application ---
        print(f"Attempting to connect to '{app_title}'...")
       #  app_title = ".*R10PosClient.*"
        app = Application(backend="uia").connect(title_re=app_title, timeout=20)
        win = app.window(title_re=app_title)
        win.wait('ready', timeout=20)
        win.set_focus()
        print("Successfully connected to the application.")

        # --- Step 2: Find the Reference Edit field and enter text ---
        print(f"\nAttempting to enter reference number: {reference_number}")
        reference_edit = win.child_window(auto_id="tbREference_InnerText", control_type="Edit")
        reference_edit.wait('visible', timeout=10)
        reference_edit.type_keys(reference_number, with_spaces=True)
        print("Successfully entered the reference number.")
        time.sleep(1) # A small delay

        # --- Step 3: Find the GST Amount field and enter amount via numpad ---
        print(f"\nAttempting to enter GST amount: {gst_amount}")
        gst_amount_field = win.child_window(auto_id="tbGstAmount_InnerText", control_type="Edit")
        gst_amount_field.wait('visible', timeout=10)
        gst_amount_field.click_input()
        print("Clicked on the GST Amount input field.")
        time.sleep(0.5)

        # Use the function to press the numpad keys for the amount and confirm
        press_numpad_keys(win, gst_amount)
        press_numpad_keys(win, ['OK'])
        
        # --- Step 4: Handle the 'Approval Required' Popup ---
        print("\n--- Handling 'Approval Required' Popup ---")
        # Wait for the approval dialog to appear. It's a separate top-level window.
        approval_dialog = app.window(title_re=".*Approval.*", top_level_only=True).wait('ready', timeout=20)
        print(f"Popup window found with title: '{approval_dialog.window_text()}'")

        print("Entering credentials...")
        # Find all edit controls within the dialog
        edit_controls = approval_dialog.descendants(control_type="Edit")
        if len(edit_controls) >= 2:
            # Enter username and password into the first two edit fields
            edit_controls[0].set_text("atmgr5")
            edit_controls[1].set_text("abcd1234")
            print("Credentials entered.")

            # Find the OK button within the dialog
            ok_buttons = approval_dialog.descendants(title="OK", control_type="Button")
            if ok_buttons:
                ok_button = ok_buttons[0] # Get the first match
                if ok_button.is_enabled():
                    print("Clicking 'OK' button on popup...")
                    ok_button.click()
                    print("Credentials submitted successfully.")
                else:
                    print("Error: 'OK' button is not enabled on the popup.")
            else:
                print("Error: Could not find the 'OK' button on the popup.")
        else:
            print("Error: Could not find the required username/password fields on the popup.")

        # A final delay to observe the result
        print("\nAutomation sequence completed.")
        time.sleep(3)
        return True  # Indicate success
    
    except Exception as e:
        print(f"An error occurred during the main process: {e}")

if __name__ == "__main__":
    paidout_finalize("TestRef123", "25.50")  # Example usage, replace with actual values as needed
