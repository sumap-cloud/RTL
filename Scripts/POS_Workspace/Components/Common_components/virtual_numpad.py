# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: virtual_numpad
# @Purpose: Simulates interaction with the POS on-screen numeric keypad
# @Dependencies: pywinauto.Application, timings, findbestmatch, findwindows
# @Input_Params: number (string to enter), OKclick (boolean)
# @Return_Values: Boolean indicating success/failure
# @Used_By_Tests: Multiple test cases including TC001-TC008
# @Known_Limitations: Sensitive to UI timing and layout changes
# ============================================

import time
from pywinauto import Application, timings, findbestmatch, findwindows

def numpad_keyin(number="1.23", OKclick=True):
    """
    Connects to the POS application, finds the virtual numpad, and enters
    the specified number by clicking the on-screen buttons.

    Args:
        number (str): The number to be entered as a string, e.g., "12.27".
        OKclick (bool): If True, the 'OK' button will be clicked after entering the number.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # --- 1. Connect to the Application ---
        print(f"\nAttempting to key in '{number}' via virtual numpad...")
        app = Application(backend="uia").connect(title="R10PosClient", timeout=20)
        win = app.window(title="R10PosClient")
        win.set_focus()
        main_view = win.child_window(auto_id="MainTransactionViewID", control_type="Custom")

        # --- 2. Locate the Numpad View ---
        keypad_container = main_view.child_window(auto_id="PosKeyPadId", control_type="Custom")
        numpad_view = keypad_container.child_window(auto_id="KeyPadControlId", control_type="Custom")
        numpad_view.wait('visible', timeout=10)
        print("- Found the virtual numpad view.")

        # --- 3. Map All Numpad Buttons for Reliability ---
        print("- Mapping all numpad buttons...")
        button_map = {}
        all_buttons = numpad_view.descendants(control_type="Button")

        for btn in all_buttons:
            title = btn.window_text()
            if title:
                if title not in button_map:
                    button_map[title] = []
                button_map[title].append(btn)
        
        if not button_map:
            print("- Error: No buttons were found in the numpad view.")
            return False
        print(f"- Map created. Found buttons for: {list(button_map.keys())}")

        # --- 4. Click Each Button for the Input Number ---
        for char in str(number):
            print(f"- Clicking button for character: '{char}'")
            if char not in button_map:
                raise findbestmatch.MatchError(f"No button found for character '{char}' in the map.")

            clicked = False
            for button in button_map[char]:
                if button.is_visible() and button.is_enabled():
                    button.click_input()
                    clicked = True
                    break
            
            if not clicked:
                raise Exception(f"Found button(s) for '{char}', but none were visible or enabled.")
            time.sleep(0.2)

        # --- 5. Conditionally Click the "OK" Button ---
        if OKclick:
            print("- Clicking the 'OK' button...")
            if 'OK' not in button_map:
                raise findbestmatch.MatchError("No 'OK' button found in the map.")
            
            ok_clicked = False
            for ok_button in button_map['OK']:
                if ok_button.is_visible() and ok_button.is_enabled():
                    ok_button.click_input()
                    ok_clicked = True
                    break
            
            if not ok_clicked:
                raise Exception("Found 'OK' button(s), but none were visible or enabled.")
        else:
            print("- Skipping 'OK' button click as requested.")
        
        print(f"- Successfully processed '{number}'.")
        return True

    except (timings.TimeoutError, findwindows.ElementNotFoundError) as e:
        print(f"\nError: Could not find the application or a required element. Details: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during numpad interaction: {e}")
        return False

if __name__ == '__main__':
    # This block demonstrates how to use the function.
    # It will run if you execute this file directly.
    print("--- STANDALONE TEST FOR numpad_keyin ---")
    
    # You can change the number here for testing purposes.
    # The POS application must be running and on a screen with the numpad visible.
    
    # print("\n--- Test Case 1: Entering number and clicking OK ---")
    # if numpad_keyin(number="12.27", OKclick=True):
    #     print("\nTest Case 1 finished successfully.")
    # else:
    #     print("\nTest Case 1 failed.")

    # Pause to allow for manual intervention if needed, e.g., re-opening the numpad
    #time.sleep(5) 

    print("\n--- Test Case 2: Entering number WITHOUT clicking OK ---")
    QTY="5X"
    if numpad_keyin(number=QTY, OKclick=False):
        print("\nTest Case 2 finished successfully.")
    else:
        print("\nTest Case 2 failed.")

