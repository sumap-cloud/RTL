# main.py
from pywinauto.application import Application
from pywinauto import findwindows
import time

# --- Numpad Button Definitions ---
# This dictionary maps the logical button names to their on-screen text or ID.
numpad_buttons = {
    '1': "1", '2': "2", '3': "3", '4': "4", '5': "5",
    '6': "6", '7': "7", '8': "8", '9': "9", '0': "0",
    'OK': "OK", 'Clear': "C", 'Backspace': "<<", 'X': "X"
}

def press_numpad_keys(age_dialog, key_sequence):
    """
    Presses a sequence of on-screen numpad buttons silently.

    Args:
        age_dialog: The pywinauto window object.
        key_sequence (str): A string of characters to press from the numpad_buttons dict.
    """
    for key in key_sequence:
        # Find the button by its title, which corresponds to the key.
        button = age_dialog.child_window(title=key, control_type="Button")
        if button.exists():
            button.click_input()
            time.sleep(0.05) # A very brief pause between clicks

def get_ordered_window_data(age_dialog):
    """
    Finds, cleans, and returns an ordered list of text data from the window,
    excluding the virtual numpad and other unwanted elements.

    Args:
        age_dialog: The pywinauto window object for the age restriction dialog.
    
    Returns:
        A list of strings containing the cleaned text from the window.
    """
    window_texts = []
    numpad_titles = list(numpad_buttons.values())
    # List of exact text to ignore in the output
    unwanted_text = ['OnScreenKeyboard', 'OnScreenKeyboardSection', '.', 'OR']

    try:
        all_controls = age_dialog.descendants()
        for control in all_controls:
            try:
                control_text = control.window_text()
                # Clean up the text by removing newlines and extra spaces
                cleaned_text = ' '.join(control_text.split()) if control_text else ''

                # Add the text if it's meaningful and not in our exclusion lists
                if cleaned_text and cleaned_text not in numpad_titles and cleaned_text not in unwanted_text:
                    # Avoid adding duplicates to the list
                    if cleaned_text not in window_texts:
                        window_texts.append(cleaned_text)
            except Exception:
                # Some controls may not have text properties, so we can ignore errors.
                continue
    except Exception as e:
        print(f"An error occurred while trying to read window data: {e}")
    
    return window_texts


def handle_age_restriction(date_of_birth=None):
    """
    Connects to the POS application and handles the age restriction dialog
    using a regular expression for the window title.

    Args:
        date_of_birth (str, optional): The DOB to input (e.g., "01012000").
                                       Defaults to None.
    """
    # Regex pattern to find the window.
    age_restriction_title_re = ".*AgeRestrictionInputExtensionViewModel.*"
    try:
        # 1. Connect to the application using the regex title.
        print(f"Connecting to age restriction dialog...")
        app = Application(backend="uia").connect(title_re=age_restriction_title_re, timeout=30)
        age_dialog = app.window(title_re=age_restriction_title_re)
        age_dialog.set_focus()
        print("Connected successfully.")

        # 2. Get and print the cleaned window data in a structured format.
        print("\n--- Window Details ---")
        window_data = get_ordered_window_data(age_dialog)
        for item in window_data:
            print(f"- {item}")
        print("----------------------\n")


        # 3. Decide action based on whether a DOB was provided.
        if date_of_birth:
            # If DOB is provided, enter it via the numpad.
            print(f"Entering Date of Birth: {date_of_birth}...")
            press_numpad_keys(age_dialog, date_of_birth)
            
            print("Clicking 'OK' button...")
            ok_button = age_dialog.child_window(title="OK", control_type="Button")
            ok_button.click_input()
        else:
            # If no DOB is provided, click the confirmation element.
            print("No DOB provided. Clicking the 'Over 25' confirmation...")
            confirm_element = age_dialog.child_window(title="I confirm, the customer appears to be over the age of 25", control_type="Text")
            confirm_element.click_input()
        
        time.sleep(2) # Wait for the dialog to close
        print("Age restriction handled successfully!")
        return True
    except findwindows.ElementNotFoundError:
        print(f"Error: Could not find the age restriction dialog. Please ensure it is open.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False



# --- Main execution ---
if __name__ == "__main__":
    handle_age_restriction(date_of_birth=None)


