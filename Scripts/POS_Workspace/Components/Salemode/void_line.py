import time
import re
from pywinauto import Application, timings
from pywinauto.findwindows import ElementNotFoundError
#from pywinauto.errors import MatchError

def handle_reason_code_screen(app, reason_code="Double Scan"):
    """
    Finds the reason code pop-up, verifies the buttons, and clicks the specified reason.
    
    Args:
        app: The application object to interact with
        reason_code (str): The reason code to select (default: "Double Scan")
        
    Returns:
        bool: True if reason code was selected successfully, False otherwise
    """
    print("\n✨ Searching for Reason Code Pop-up...")
    
    # Expected reasons based on the screenshot
    expected_reasons = {
        "Double Scan", "Insufficient Funds", "Restricted Item Sales",
        "Technical Issues", "Unwanted Goods", "Incorrect item scanned"
    }

    try:
        # Find the pop-up window using its specific auto_id
        reason_popup = app.window(auto_id="TransparentWindowID", control_type="Window")
        reason_popup.wait('visible', timeout=15)
        reason_popup.set_focus()

        if reason_popup.exists():
            print("✅ 'Void Line' reason code pop-up found.")
            print("📝 Popup Window Title:", reason_popup.window_text())
            try:
                message_elem = reason_popup.child_window(auto_id="Message")
                message_text = message_elem.window_text().strip()
                if message_text:
                    print(f"📝 Message (automation_id='Message'): {message_text}")
            except Exception:
                pass  # No element with automation_id="Message"

            # Only print the first meaningful message (not labels or keyboard keys)
            texts = reason_popup.descendants(control_type="Text")
            main_message = None
            for txt in texts:
                msg = txt.window_text().strip()
                # Skip empty, single-char, or known keyboard/label texts
                if len(msg) > 2 and msg.lower() not in {"ok", "cancel", "yes", "no", "next", "back", "continue"} and not msg.islower():
                    main_message = msg
                    break
            if main_message:
                print(f"📝 Title : {main_message}")

            
            # --- NEW: Verify the reason codes are present ---
            all_buttons = {b.window_text() for b in reason_popup.descendants(control_type="Button") if b.window_text()}
            
            print("\n--- Verifying Reason Codes ---")
            if expected_reasons.issubset(all_buttons):
                print("✅ All expected reason codes are present.")
                
                # Click the specified reason code button
                print(f"\n🖱️ Clicking '{reason_code}'...")
                reason_popup.child_window(title=reason_code, control_type="Button").click_input()
                print(f"✅ '{reason_code}' button clicked successfully.")
                return True
            else:
                missing_reasons = expected_reasons - all_buttons
                print(f"❌ ERROR: Missing reason codes: {missing_reasons}")
                return False
            # --- END NEW SECTION ---

        else:
            print("❌ ERROR: Could not find the reason code pop-up after waiting.")
            return False

    except (timings.TimeoutError, ElementNotFoundError) as e:
        print(f"❌ An error occurred while handling the reason code screen: {e}")
        return False


def click_void_line_button(win):
    """
    Clicks the Void Line button to open the reason code screen.
    
    Args:
        win: The window object to interact with
        
    Returns:
        bool: True if button was clicked successfully, False otherwise
    """
    try:
        print("\n🖱️ Clicking 'Void Line' button...")
        void_line_button = win.child_window(title="Void Line", control_type="Button")
        void_line_button.wait('visible', timeout=10)
        void_line_button.click_input()
        time.sleep(1)  # Wait for popup to appear
        print("✅ Void Line button clicked successfully.")
        return True
    except (ElementNotFoundError, timings.TimeoutError) as e:
        print(f"❌ Could not find or click the 'Void Line' button. Error: {e}")
        return False


def void_line_item():
    """
    Connects to the POS application and performs the 'Void Line' action.
    """
    try:
        # Connect to the running POS application
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS window found and focused.")
    except (timings.TimeoutError, Exception) as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    # --- Click 'Void Line' and handle the reason code screen ---
    try:
        print("\n🖱️ Clicking 'Void Line' button...")
        #void_line_button = win.child_window(title="Void Line", control_type="Button")
        #void_line_button.click_input()
        
        # After clicking, call the function to handle the pop-up screen
        # Pass the 'app' object so it can find the new window
        handle_reason_code_screen(app)
        
        # Wait a moment for the action to complete and the UI to update
        time.sleep(2)
        print("\n✅ Void Line workflow completed.")

    except (ElementNotFoundError, Exception) as e:
        print(f"❌ Could not find or click the 'Void Line' button. Error: {e}")
    # --- END ---


if __name__ == "__main__":
    void_line_item()
