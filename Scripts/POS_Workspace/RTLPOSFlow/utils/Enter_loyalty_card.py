# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: loyalty_popup_validation
# @Purpose: Handles customer loyalty popups and validation operations
# @Dependencies: pywinauto.application.Application, pywinauto.findwindows, pywinauto.timings
# @Input_Params: customer_number (optional), app, window
# @Return_Values: Boolean indicating success/failure of popup handling
# @Used_By_Tests: TC003_loyalty_basic_scenario_ai, TC005_loyalty_details_scenario
# @Known_Limitations: Popup handling depends on specific element IDs/texts
# ============================================
# ============================================
# @Component: loyalty_popup_validation
# @Purpose: Handles customer loyalty popups and validation operations
# ============================================

from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError
import time

def connect_to_app():
    """Connects to the running R10PosClient application."""
    try:
        app = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        win = app.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        print("✅ Successfully connected to the application.")
        return app
    except ElementNotFoundError:
        print("❌ Application 'R10PosClient' not found. Please make sure it is running.")
        return None

def handle_customer_popup(app, customer_number):
    """
    Handles the customer number popup.
    - If a customer_number is provided, it enters the number and clicks OK.
    - If customer_number is None or empty, it clicks the 'Cancel' button.
    """
    # app = connect_to_app()
    
    if not app:
        print("❌ Application not connected.")
        return False

    try:
        # Find the top-most popup window using the app instance
        # app, win = connect_to_app()
        # popup = app.top_window()
        try:
            app = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
            popup = app.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
            print("✅ Successfully connected to the application.")
        
        except ElementNotFoundError:
            print("❌ Application 'R10PosClient' not found. Please make sure it is running.")

        popup = app.top_window()
        popup.set_focus()
        print(f"📝 Found Popup Window: '{popup.window_text()}'")

        # --- Find and print the title and message of the popup ---
        popup_texts = []
        text_elements = popup.descendants(control_type="Text")
        for elem in text_elements:
            try:
                text = elem.window_text().strip()
                if text and text not in ["Enter Customer Card:", "OK", "Cancel"]:
                    popup_texts.append(text)
            except:
                continue
        
        if len(popup_texts) >= 1:
            print(f"✅ Found Popup Title: '{popup_texts[0]}'")

        if customer_number:
            print(f"▶️ Attempting to enter customer number using virtual keyboard: {customer_number}")
            input_fields = popup.descendants(control_type="Edit")

            if not input_fields:
                print("❌ No input fields found in the popup.")
                return False

            customer_input = input_fields[0]
            customer_input.set_focus()

            # --- VIRTUAL KEYBOARD LOGIC ---
            is_caps_on = False

            def toggle_caps():
                nonlocal is_caps_on
                try:
                    # Using title_re to handle potential space or case differences in the toggle button
                    caps_button = popup.child_window(title_re=".*[aA] ↔ [aA].*", control_type="Button", found_index=0)
                    if caps_button.exists(timeout=2):
                        caps_button.click_input()
                        is_caps_on = not is_caps_on
                        print(f"✔️ Toggled Caps Lock. New state: {'ON' if is_caps_on else 'OFF'}")
                        time.sleep(0.3)
                except Exception as e:
                    print(f"❌ Error toggling Caps: {e}")

            def type_with_virtual_keyboard(text_to_type):
                nonlocal is_caps_on
                for char in text_to_type:
                    # Determine search criteria based on character type
                    if char.isalpha():
                        should_be_upper = char.isupper()
                        if (should_be_upper and not is_caps_on) or (not should_be_upper and is_caps_on):
                            toggle_caps()
                        # The buttons in the image use lowercase labels (q, w, e...)
                        search_title = char.lower()
                    else:
                        # For numbers, use the character directly (1, 2, 3...)
                        search_title = char

                    try:
                        # Use found_index=0 to distinguish the button from any background text elements
                        key_button = popup.child_window(title=search_title, control_type="Button", found_index=0)
                        if key_button.exists(timeout=2):
                            key_button.click_input()
                            print(f"✔️ Clicked '{search_title}'")
                            time.sleep(0.1)
                        else:
                            print(f"⚠️ Key '{search_title}' not found. Falling back to direct typing.")
                            customer_input.type_keys(char)
                    except Exception as e:
                        print(f"❌ Error clicking key '{search_title}': {e}")
            
            # Execute virtual typing
            type_with_virtual_keyboard(str(customer_number))
            print(f"✅ Finished typing: {customer_number}")

            # Finalize by clicking OK
            try:
                ok_button = popup.child_window(title="OK", control_type="Button", found_index=0)
                print("⏳ Waiting for 'OK' button...")
                ok_button.wait('enabled', timeout=5)
                ok_button.click_input()
                print("✅ Successfully clicked 'OK'.")
            except TimeoutError:
                print("❌ 'OK' button was not enabled in time.")
                return False

        else:
            print("▶️ No customer number provided. Clicking 'Cancel'.")
            cancel_button = popup.child_window(title="Cancel", control_type="Button", found_index=0)
            cancel_button.click_input()
            print("✅ Successfully clicked 'Cancel'.")

        return True

    except ElementNotFoundError:
        print("❌ Could not find the popup or required elements.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def main():
    app, win = connect_to_app()
    if app and win:
        # Test with a number
        customer_number_provided = "9344402191258"
        handle_customer_popup(app, customer_number_provided)

if __name__ == "__main__":
    main()