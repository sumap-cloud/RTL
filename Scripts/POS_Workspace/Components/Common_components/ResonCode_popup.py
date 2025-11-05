import time
import re
from pywinauto import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError

def handle_select_reason_code_popup(app, expected_reasons=None, reason_to_click="Technical Issues"):
    """
    Finds the 'Select reason code' popup, verifies the reasons, and selects one.

    Args:
        app (pywinauto.Application): The application object.
        expected_reasons (set, optional): A set of expected reason strings. 
                                           If None or empty, a default set is used.
                                           Defaults to None.
        reason_to_click (str, optional): The text of the button to click. 
                                         Defaults to "Technical Issues".
    """
    print(f"\n--- Handling Popup (expecting to click '{reason_to_click}') ---")
    
    # Define the default set of reasons based on the provided image
    default_reasons = {
        "Double Scan", "Insufficient Funds", "Restricted Item Sales",
        "Technical Issues", "Unwanted Goods"
    }
    
    # If expected_reasons is not provided or is empty, use the default set.
    if not expected_reasons:
        print("No custom reasons provided. Using default set.")
        expected_reasons = default_reasons
    else:
        print("Using custom set of expected reasons.")

    try:
        # Get the top-most window, which should be the popup
        popup = app.top_window()
        popup.wait('visible', timeout=10)
        print(f"✅ Popup window found with title: '{popup.window_text()}'")

        # Find all buttons within the popup to verify the reason codes
        all_buttons = {b.window_text() for b in popup.descendants(control_type="Button") if b.window_text() and b.window_text() != 'Cancel'}
        
        # Print all found reason codes
        print("\n--- Available Reason Codes ---")
        for reason in sorted(list(all_buttons)):
            # Highlight if the reason is one we expect
            marker = "✅" if reason in expected_reasons else "  "
            print(f" {marker} - {reason}")
        print("----------------------------\n")

        # Check if all expected reason codes are present
        if expected_reasons.issubset(all_buttons):
            print("✅ All expected reason codes are visible.")
            
            # Click the specified reason button if it exists
            if reason_to_click in all_buttons:
                print(f"🖱️ Clicking '{reason_to_click}'...")
                popup.child_window(title=reason_to_click, control_type="Button").click_input()
                print(f"✅ '{reason_to_click}' button clicked successfully.")
            else:
                print(f"⚠️ Button '{reason_to_click}' not found in the available reasons.")
        else:
            missing_reasons = expected_reasons - all_buttons
            print(f"❌ ERROR: Missing expected reason codes: {missing_reasons}")

    except (TimeoutError, MatchError) as e:
        print(f"❌ An error occurred while handling the popup: {e}")
        # For debugging, you can uncomment the line below
        # app.top_window().print_control_identifiers()

def main():
    """
    Main function to connect to the POS and handle the reason code popup.
    """
    try:
        # Connect to the running application
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS window found and focused.")
    except Exception as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    # --- USAGE EXAMPLES ---

    # Example 1: Use default reasons. This will try to click the default
    # button ("Technical Issues"), which is not in this list, and show a warning.
    print("\n>>> Running with default reasons and default click target...")
    handle_select_reason_code_popup(app)

    # Example 2: Handle the 'Price Override' popup by specifying the button to click.
    print("\n>>> Running with default reasons and a CUSTOM click target...")
    handle_select_reason_code_popup(app, reason_to_click="Price Discrepancy", expected_reasons={ "Close to Date", "Damaged Stock", "Price Discrepancy", "Rain Check"})

    # Example 3: Handle a completely different popup with custom reasons and a custom click.
    # print("\n>>> Running with completely custom reasons and click target...")
    # custom_reasons = {"Double Scan", "Technical Issues", "Unwanted Goods"}
    # handle_select_reason_code_popup(
    #     app, 
    #     expected_reasons=custom_reasons, 
    #     reason_to_click="Technical Issues"
    # )


if __name__ == "__main__":
    # IMPORTANT: Make sure the popup is visible on screen
    # BEFORE you run this script.
    print("Please ensure the 'Price Override Reason' or other reason popup is open now.")
    time.sleep(3) # Gives you a moment to switch to the app
    main()

