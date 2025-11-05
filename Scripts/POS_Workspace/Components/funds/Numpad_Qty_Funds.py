from pywintypes import Time
from pywinauto.application import Application
import time
import re
import json

import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Common_components.POS_CONNECT import connect_to_pos_app

# --- Configuration ---
app_title = ".*R10PosClient.*"  # Regex for the application title
# Using a dictionary to map numpad digits to their control identifiers.
# These values have been confirmed from the print_control_identifiers() output.
numpad_buttons = {
    '1': "1",
    '2': "2",
    '3': "3",
    '4': "4",
    '5': "5",
    '6': "6",
    '7': "7",
    '8': "8",
    '9': "9",
    '0': "0",
    'OK': "OK",
    'Clear': "C",
    'Backspace': "<<",
    'X': "X"
}


def press_numpad_keys(window, key_sequence):

    print(f"Executing key sequence: {key_sequence}")
    for key in key_sequence:
        try:
            # Find the button by its 'auto_id' which is more reliable.
            button = window.child_window(auto_id=numpad_buttons[key], control_type="Button")
            if button.exists():
                print(f"Clicking button '{key}'")
                # Using click_input() for better reliability
                button.click_input()
                time.sleep(0.1) # Small delay between clicks
            else:
                print(f"Warning: Button '{key}' with auto_id '{numpad_buttons[key]}' not found.")
        except Exception as e:
            print(f"Error clicking button '{key}': {e}")

def numpad_QTY_funds(quantity):
        
        main_window = connect_to_pos_app(app_title) # Bring the window to the foregroun

        # Define the sequence of keys to press
        keys_to_press = list(quantity) + ['OK']

        # Call the function to press the numpad keys
        press_numpad_keys(main_window, keys_to_press)
        print("Quantity entry complete.")
        return True
#numpad_QTY_funds("77")  # Example usage, replace with actual quantity as needed