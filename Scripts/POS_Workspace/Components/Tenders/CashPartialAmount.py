from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError, WindowNotFoundError
from pywinauto.controls.uia_controls import ButtonWrapper, EditWrapper
from Scripts.POS_Workspace.Components.Common_components.virtual_numpad import numpad_keyin
import time
import sys
import re # Keep re for pattern matching in get_balance_due

# --- Application Configuration ---
# Define the application title regex here so it's easy to change
APP_TITLE_RE = ".*R10PosClient.*"

# def _click_numpad_key(numpad_win, key):
#     """
#     Helper function to click a specific key on the on-screen numpad.
#     Searches within the specific keyboard section for robustness.
#     """
#     try:
#         # Find the specific keyboard section within the numpad container first
#         keyboard_section = numpad_win.child_window(auto_id="OnScreenKeyboardSection", control_type="Custom")
#         # Now search for the key within that specific section
#         key_button = keyboard_section.child_window(title=key, auto_id=key, control_type="Button")

#         # Check if button exists and is enabled before clicking
#         # Adding a short wait here in case the button appears slightly delayed
#         if key_button.exists(timeout=2) and key_button.is_enabled():
#             key_button.click_input()
#             time.sleep(0.1) # Small delay between clicks
#             return True
#         else:
#             print(f"Error: Numpad key '{key}' not found or not enabled within the keyboard section.")
#             return False
#     except ElementNotFoundError:
#          # Increased clarity in error message
#         print(f"Error: Could not find the 'OnScreenKeyboardSection' or the key '{key}' within the numpad container '{numpad_win.element_info.name}'.")
#         return False
#     except Exception as e:
#         print(f"Error clicking numpad key '{key}': {e}")
#         return False

def get_balance_due_from_tender_screen(tender_amount_screen):
    """
    Attempts to find and return the balance due text from the tender amount screen
    by locating the specific container and finding the value control within it,
    verifying its automation_id looks like currency.
    """
    balance_due_value = "N/A"
    try:
        # 1. Find the specific container for the balance due info based on logs
        balance_due_container = tender_amount_screen.child_window(auto_id="restrictionBalanceDue", control_type="Custom")
        balance_due_container.wait('visible', timeout=5) # Wait for container

        # 2. Find the Custom control within THIS container that holds the value.
        all_customs_in_container = balance_due_container.descendants(control_type="Custom")

        potential_values = []
        for ctrl in all_customs_in_container:
            try:
                auto_id = ctrl.automation_id
                # Heuristic: Check if the automation_id looks like a currency value
                if auto_id and re.fullmatch(r'\$?\d+(\.\d{1,2})?', auto_id.strip()):
                    if auto_id.strip() != "0.00":
                        potential_values.append(auto_id.strip().replace('$', '')) # Store cleaned value

            except Exception:
                # Ignore controls lacking necessary properties
                continue

        # If multiple potential values were found, prefer the last one (often the updated value)
        if potential_values:
            balance_due_value = potential_values[-1]
        else:
             # Fallback if specific pattern fails: check window_text as well within the container
            for ctrl in all_customs_in_container:
                try:
                    text = ctrl.window_text()
                    if text and re.fullmatch(r'\$?\d+(\.\d{1,2})?', text.strip()):
                        if text.strip() != "$0.00": # Avoid initial zero if possible
                            balance_due_value = text.strip().replace('$', '')
                            break # Take first match in fallback
                except Exception:
                    continue
            
            if balance_due_value == "N/A":
                print("Warning: Could not find balance due value control (matching currency pattern) within 'restrictionBalanceDue' container using auto_id or window_text.")

    except ElementNotFoundError:
        print("Warning: Could not find the 'restrictionBalanceDue' container used to locate Balance Due.")
        balance_due_value = "Container Not Found"
    except Exception as e:
        print(f"Error trying to get Balance Due: {e}")
        balance_due_value = "Error"

    return balance_due_value


def enter_cash_tender_amount(amount_to_enter):
    """
    Handles the Cash Tender Amount Entry screen by connecting to the app,
    finding the window, and entering the specified amount.

    :param amount_to_enter: The amount (string or number) to enter using the numpad.
    :return: True if successful, False otherwise.
    """
    print("\n--- Handling Cash Tender Amount Entry ---")
    try:
        # --- Self-contained connection logic ---
        print(f"Connecting to '{APP_TITLE_RE}'...")
        app = Application(backend="uia").connect(title_re=APP_TITLE_RE, timeout=10)
        win = app.window(title_re=APP_TITLE_RE)
        win.set_focus()
        print("✓ Successfully connected to application.")
        # --- End of connection logic ---

        # 1. Find the specific screen container
        tender_amount_screen = win.child_window(auto_id="TenderAmountViewID", control_type="Custom")
        tender_amount_screen.wait('visible', timeout=10)
        print("✓ Cash amount entry screen found.")

        # 2. Verify key elements to ensure it's the correct screen
        cash_title = tender_amount_screen.child_window(title="Cash", control_type="Text")
        amount_label_list_item = tender_amount_screen.child_window(title="Please Enter Amount", control_type="ListItem")
        cancel_button = tender_amount_screen.child_window(title="Cancel", auto_id="TenderAmountViewCancelCommand", control_type="Button")

        if not (cash_title.exists(timeout=2) and amount_label_list_item.exists(timeout=2) and cancel_button.exists(timeout=2)):
            print("❌ Error: Could not verify all key elements of the cash amount entry screen.")
            return False

        # 3. Get Balance Due using the refined pywinauto properties method
        balance_due = get_balance_due_from_tender_screen(tender_amount_screen)
        print(f"i Current Balance Due: ${balance_due}") # Display whatever value was found

        # 4. Find the number pad container
        numpad_win = win.child_window(auto_id="PosKeyPadId", control_type="Custom")
        numpad_win.wait('visible', timeout=5)

        # 5. Enter the amount using the number pad keys
        # amount_str = str(amount_to_enter)
        # print(f"Attempting to enter amount: {amount_str}")
        # for digit in amount_str:
        if not numpad_keyin(number="2.00", OKclick=True):
                # Error is printed within _click_numpad_key
            return False
        # print(f"✓ Amount '{amount_str}' entered via numpad.")

        # 6. Find and click the OK button on the number pad
        keyboard_section_for_ok = numpad_win.child_window(auto_id="OnScreenKeyboardSection", control_type="Custom")
        ok_button = keyboard_section_for_ok.child_window(title="OK", auto_id="OK", control_type="Button")
        if not keyboard_section_for_ok.exists(timeout=2):
            print("❌ Error: Could not find OnScreenKeyboardSection to click OK.")
            return False
        ok_button.wait('enabled', timeout=5) # Wait specifically for OK to become enabled
        if ok_button.is_enabled():
            ok_button.click_input()
            print("✓ Clicked OK button on numpad.")
            return True # Assume success after clicking OK
        else:
            print("❌ Error: Numpad OK button did not become enabled after entering amount.")
            return False

    except (ElementNotFoundError, WindowNotFoundError) as e:
        # Catch specific pywinauto errors
        print(f"❌ Error: Could not find a required UI element or the application window: {e}. Check auto_ids and screen state.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred in enter_cash_tender_amount: {e}")
        return False

# --- Example Usage (Only runs when script is executed directly) ---
if __name__ == "__main__":

    amount_to_test = "2.00" # Example amount

    print(f"--- Example: Attempting to enter {amount_to_test} ---")
    
    # IMPORTANT: Ensure the cash amount entry screen is the active screen
    # in the application before this script proceeds.
    print("!!! ENSURE THE CASH AMOUNT ENTRY SCREEN IS ACTIVE BEFORE PROCEEDING !!!")
    print("You have 5 seconds...")
    time.sleep(5) # Give user 5 seconds to switch to the correct screen manually

    # Call the new, self-contained function.
    # No need to pass 'main_win' anymore.
    if enter_cash_tender_amount(amount_to_test):
        print("\n✅ Cash amount entry successful.")
        # Add logic here for what happens *after* clicking OK successfully
        time.sleep(2) # Allow time for the next screen/state to appear
        print("Continuing script...")
        # e.g., handle_change_screen() or verify_next_state()
    else:
        print("\n❌ Cash amount entry failed.")
