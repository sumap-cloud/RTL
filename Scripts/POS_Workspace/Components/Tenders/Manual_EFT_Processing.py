from pywinauto.application import Application
import time

def handle_manual_eft_screen(window, action_parameter):
    """
    Finds elements on the Manual EFT screen and performs an action based on the parameter.
    
    Args:
        window: The main application window object from pywinauto.
        action_parameter (str): The action to perform. Can be 'yes' or 'no'.
    """
    print("--- Starting to capture elements from the Manual EFT screen ---")
    
    # Wait for the elements to be available
    window.wait('ready', timeout=20)
    
    # --- Element Identification ---
    # Define the properties of the elements we want to find
    elements_to_find = {
        "eft_offline_text": {"title": "EFT is offline on this lane", "control_type": "Text"},
        "instructions_text": {"title_re": ".*Continue to Manual EFT Processing.*", "control_type": "Text"},
        "yes_button": {"title": "Yes", "control_type": "Button"},
        "no_button": {"title": "No", "control_type": "Button"}
    }
    
    found_elements = {}
    
    # Find and report each element
    for name, properties in elements_to_find.items():
        try:
            element = window.child_window(**properties)
            if element.exists():
                found_elements[name] = element
                # A more understandable console output
                print(f"SUCCESS: Found element '{element.window_text()}' with control type '{element.friendly_class_name()}'")
            else:
                print(f"FAILURE: Could not find the element identified as '{name}'.")
        except Exception as e:
            print(f"ERROR: An exception occurred while finding '{name}': {e}")

    print("\n--- Element capturing finished ---")

    # --- Action Execution ---
    # Perform an action based on the provided parameter
    print(f"\n--- Performing action based on parameter: '{action_parameter}' ---")
    
    action = action_parameter.lower()

    if action == 'yes':
        if 'yes_button' in found_elements:
            print("Action: Clicking the 'Yes' button...")
            found_elements['yes_button'].click_input() # Using click_input() for more reliable clicks
            print("SUCCESS: The 'Yes' button was clicked.")
        else:
            print("ERROR: Cannot perform action because the 'Yes' button was not found.")
    elif action == 'no':
        if 'no_button' in found_elements:
            print("Action: Clicking the 'No' button...")
            found_elements['no_button'].click_input()
            print("SUCCESS: The 'No' button was clicked.")
        else:
            print("ERROR: Cannot perform action because the 'No' button was not found.")
    else:
        print(f"INFO: No action was performed. The parameter '{action_parameter}' is not a valid choice ('yes' or 'no').")


if __name__ == "__main__":
    try:
        # --- CONFIGURATION ---
        # Set the desired action here. Options are "yes" or "no".
        ACTION_TO_PERFORM = "Yes" 

        # Connect to the R10PosClient application
        print("Connecting to the R10PosClient application...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        
        # Get the main window and set focus
        win_var = app.window(title_re=".*R10PosClient.*")
        win_var.set_focus()
        print("Successfully connected to the application window.")

        # Call the main function to handle the screen logic
        handle_manual_eft_screen(win_var, ACTION_TO_PERFORM)

    except Exception as e:
        print(f"An error occurred during the main process: {e}")

