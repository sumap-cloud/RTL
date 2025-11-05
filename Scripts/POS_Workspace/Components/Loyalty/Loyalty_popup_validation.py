# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: loyalty_popup_validation
# @Purpose: Handles customer loyalty popups and validation operations
# @Dependencies: pywinauto.application.Application, pywinauto.findwindows, pywinauto.timings
# @Input_Params: customer_number (optional), app, window
# @Return_Values: Boolean indicating success/failure of popup handling
# @Used_By_Tests: TC003_loyalty_basic_scenario_ai, TC005_loyalty_details_scenario
# @Known_Limitations: Popup handling depends on specific element IDs/texts
# ============================================

from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError
import time

def connect_to_app():
    """Connects to the running R10PosClient application."""
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        win = app.window(title_re=".*R10PosClient.*")
        print("✅ Successfully connected to the application.")
        return app, win
    except ElementNotFoundError:
        print("❌ Application 'R10PosClient' not found. Please make sure it is running.")
        return None, None

def handle_customer_popup(app, customer_number):
    """
    Handles the customer number popup.
    - If a customer_number is provided, it enters the number and clicks OK.
    - If customer_number is None or empty, it clicks the 'Cancel' button.
    """
    if not app:
        print("❌ Application not connected.")
        return False

    try:
        # Find the top-most popup window using the app instance
        popup = app.top_window()
        print(f"📝 Found Popup Window: '{popup.window_text()}'")

        # --- Find and print the title and message of the popup ---
        popup_title = None
        popup_message = None
        text_elements = popup.descendants(control_type="Text")
        
        popup_texts = []
        for elem in text_elements:
            try:
                text = elem.window_text().strip()
                if text and text not in ["Enter Customer Card:", "OK", "Cancel"]:
                    popup_texts.append(text)
            except:
                continue
        
        if len(popup_texts) >= 2:
            popup_title = popup_texts[0]
            popup_message = popup_texts[1]
            print(f"✅ Found Popup Title: '{popup_title}'")
            print(f"✅ Found Popup Message: '{popup_message}'")
        elif len(popup_texts) == 1:
            popup_title = popup_texts[0]
            print(f"✅ Found Popup Title: '{popup_title}'")
        else:
            print("⚠️ Could not find title or message text in the popup.")


        if customer_number:
            # --- Logic for when a customer number IS provided ---
            print(f"▶️ Attempting to enter customer number using virtual keyboard: {customer_number}")
            input_fields = popup.descendants(control_type="Edit")

            if not input_fields:
                print("❌ No input fields found for customer number in the popup.")
                return False

            customer_input = input_fields[0]
            customer_input.set_focus()

            # --- VIRTUAL KEYBOARD LOGIC ---
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
                nonlocal is_caps_on
                try:
                    caps_button = popup.child_window(title_re=".*[aA] ↔ [aA].*", control_type="Button")
                    if caps_button.exists(timeout=2):
                        caps_button.click_input()
                        is_caps_on = not is_caps_on
                        print(f"✔️ Toggled Caps Lock. New state: {'ON' if is_caps_on else 'OFF'}")
                        time.sleep(0.2)
                    else:
                        print("⚠️ Could not find Caps Lock button.")
                except Exception as e:
                    print(f"❌ Error clicking Caps Lock button: {e}")

            def type_with_virtual_keyboard(text_to_type):
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
                            key_button = popup.child_window(title=key_name, control_type="Button")
                            if key_button.exists(timeout=2):
                                key_button.click_input()
                                print(f"✔️ Clicked '{key_name}'")
                                time.sleep(0.1)
                            else:
                                print(f"⚠️ Could not find key: '{key_name}'")
                        except Exception as e:
                            print(f"❌ Error clicking key '{key_name}': {e}")
            
            # Use the virtual keyboard to type the number
            type_with_virtual_keyboard(customer_number)
            print(f"✅ Finished typing with virtual keyboard.")

            # Find and click the 'OK' button, waiting for it to be enabled
            try:
                ok_button = popup.child_window(title="OK", control_type="Button")
                print("⏳ Waiting for 'OK' button to be enabled...")
                ok_button.wait('enabled', timeout=3)
                ok_button.click_input()
                print("✅ Successfully clicked the 'OK' button.")
            except TimeoutError:
                print("❌ 'OK' button did not become enabled within 3 seconds.")
                return False

        else:
            # --- Logic for when a customer number IS NOT provided ---
            print("▶️ No customer number provided. Attempting to click 'Cancel'.")
            cancel_button = popup.child_window(title="Cancel", control_type="Button")
            cancel_button.click_input()
            print("✅ Successfully clicked the 'Cancel' button.")

        return True

    except ElementNotFoundError:
        print("❌ Could not find the popup window or one of its elements (Input field/OK/Cancel button).")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def main():
    """Main function to run the automation."""
    app, win = connect_to_app()

    if app and win:
        # --- To test entering a number, provide a string like below ---
        #customer_number_provided = "9344402191258"
        customer_number_provided = None
        
        # --- To test clicking Cancel, set the variable to None ---
        # customer_number_provided = None 

        handle_customer_popup(app, customer_number_provided)

if __name__ == "__main__":
    main()

