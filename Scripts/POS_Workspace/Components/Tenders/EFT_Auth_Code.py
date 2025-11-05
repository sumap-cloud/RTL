from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Common_components.virtual_reference_keyboard import Virtual_keyboard_reference


def handle_auth_code_screen(window, auth_code_to_enter):
    """
    Finds elements on the Manual EFT Authorization Code screen, enters the auth code, and clicks OK.
    
    Args:
        window: The main application window object from pywinauto.
        auth_code_to_enter (str): The authorization code to enter.
    """
    print("--- Starting to handle the Auth Code screen ---")
    
    # Wait for the elements on the new screen to be available
    window.wait('visible', timeout=20)
    
    # --- Element Identification ---
    # Define the properties of the elements we want to find on this screen
    elements_to_find = {
        "instructional_text": {
            "title_re": ".*Manual EFT Processing.*", 
            "auto_id": "Title", 
            "control_type": "Text"
        },
        "auth_code_input": {
            "auto_id": "tbNewPrice_InnerText", 
            "control_type": "Edit"
        },
        "virtual_keyboard_button": {
            "auto_id": "VirtualKeypadButton",
            "control_type": "Button"
        },
        "ok_button": {
            "title": "OK", 
            "auto_id": "GenericCommandButtonTemplete_Ok", 
            "control_type": "Button"
        },
        "cancel_button": {
            "title": "Cancel", 
            "auto_id": "GenericCommandButtonTemplete_Cancel", 
            "control_type": "Button"
        }
    }
    
    found_elements = {}
    
    # Find and report each element
    for name, properties in elements_to_find.items():
        try:
            element = window.child_window(**properties)
            if element.exists():
                found_elements[name] = element
                element_text = element.window_text()
                # Use a placeholder for the text of certain elements for clarity
                if name == "auth_code_input":
                    element_text = "[Authorization Code Input Field]"
                elif name == "virtual_keyboard_button":
                    element_text = "[Virtual Keyboard Button]"
                
                print(f"SUCCESS: Found element '{element_text}' with control type '{element.friendly_class_name()}'")
            else:
                print(f"FAILURE: Could not find the element identified as '{name}'.")
        except Exception as e:
            print(f"ERROR: An exception occurred while finding '{name}': {e}")

    print("\n--- Element capturing finished ---")

    # --- Action Execution ---
    print(f"\n--- Entering authorization code: '{auth_code_to_enter}' ---")
    
    if 'virtual_keyboard_button' in found_elements:
        print("Action: Clicking the virtual keyboard button...")
        found_elements['virtual_keyboard_button'].click_input()
        print("SUCCESS: The virtual keyboard button was clicked.")
        
        if auth_code_to_enter:
            print(f"Action: Entering authorization code '{auth_code_to_enter}' using the virtual keyboard...")
            Virtual_keyboard_reference(enter=auth_code_to_enter)
            print("SUCCESS: Authorization code entered.")
            
            # Click the OK button after entering the code
            if 'ok_button' in found_elements:
                print("Action: Clicking the OK button...")
                found_elements['ok_button'].click_input()
                print("SUCCESS: The OK button was clicked.")
            else:
                print("ERROR: Could not click the OK button because it was not found.")
        else:
            print("ERROR: No authorization code was provided to enter.")
    else:
        print("ERROR: Cannot perform action because the virtual keyboard button was not found.")

    return found_elements

if __name__ == "__main__":
    try:
        # --- CONFIGURATION ---
        # This section now demonstrates how to call the reusable function.
        # You can now import and call `handle_auth_code_screen` from other scripts.
        AUTH_CODE = "987678"

        # Connect to the R10PosClient application
        print("Connecting to the R10PosClient application...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        
        # Get the main window and set focus
        win_var = app.window(title_re=".*R10PosClient.*")
        win_var.set_focus()
        print("Successfully connected to the application window.")

        # Call the function to handle the screen logic
        handle_auth_code_screen(win_var, auth_code_to_enter=AUTH_CODE)

    except Exception as e:
        print(f"An error occurred during the main process: {e}")

