from pywinauto import timings, Application, findwindows
from pywinauto.findbestmatch import MatchError
import time

def handle_reason_code_screen(win, reason_code=None):
    """
    Finds and clicks a reason code on the 'Return Item' screen,
    scrolling if necessary to find it.
    """
    print("\n✨ Return Item Reason Code Screen Detected ✨")
    reason_to_click = reason_code if reason_code else "Double Scan"
    
    try:
        # --- Step 1: Detect scrolling and collect all button texts ---
        all_found_buttons = set()
        down_arrow = None
        up_arrow = None

        try:
            # Check for scroll buttons using the provided auto_id
            down_arrow = win.child_window(auto_id="ConsumableDataPagerButtonDownID", control_type="Button")
            up_arrow = win.child_window(auto_id="ConsumableDataPagerButtonUpID", control_type="Button") # Assuming similar ID for up arrow
        except (MatchError, timings.TimeoutError):
            print("- No scrolling functionality detected.")
        
        if down_arrow and down_arrow.exists():
            print("- Scrolling detected. Collecting all available reason codes...")
            # Scroll to the top to ensure a consistent starting point
            if up_arrow.exists():
                while up_arrow.is_enabled():
                    up_arrow.click_input()
                    time.sleep(0.5)

            # Use a more robust loop to ensure the last page is always processed
            while True:
                current_buttons = {b.window_text() for b in win.descendants(control_type="Button")}
                all_found_buttons.update(current_buttons)

                if down_arrow.is_enabled():
                    down_arrow.click_input()
                    time.sleep(0.5)
                else:
                    # Can't scroll further, so break the loop
                    break
        else:
            # If no scrolling, just grab the visible buttons
            all_found_buttons = {b.window_text() for b in win.descendants(control_type="Button")}

        # Filter out common non-reason code buttons for cleaner printing
        non_reason_codes = {'', 'Cancel', 'OK', 'C', 'X', '<<', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.'}
        all_found_reasons = {b for b in all_found_buttons if b not in non_reason_codes}


        print("\n--- Captured Reason Codes ---")
        for reason in sorted(list(all_found_reasons)):
            print(f"  - {reason}")
        print("----------------------------\n")
        
        # --- Step 2: Find and click the target reason code ---
        # Scroll back to the top to begin the search
        if up_arrow and up_arrow.exists():
            while up_arrow.is_enabled():
                up_arrow.click_input()
                time.sleep(0.5)

        # Loop through pages again to find and click the target button
        while True:
            try:
                target_button = win.child_window(title=reason_to_click, control_type="Button")
                if target_button.is_visible():
                    print(f"🖱️ Clicking '{reason_to_click}'...")
                    target_button.click_input()
                    print(f"✅ '{reason_to_click}' button clicked successfully.")
                    return True
            except MatchError:
                # Button not visible on this page, continue to next
                pass

            if down_arrow and down_arrow.is_enabled():
                down_arrow.click_input()
                time.sleep(0.5)
            else:
                # Scrolled through all pages and did not find the button
                print(f"❌ ERROR: Could not find '{reason_to_click}' to click it after scanning all pages.")
                return False

    except (timings.TimeoutError, MatchError) as e:
        print(f"❌ An error on the reason code screen: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred in handle_reason_code_screen: {e}")
        return False


if __name__ == '__main__':
    application_window_title = "R10PosClient"

    try:
        print("Connecting to the POS application...")
        # Connect to the running application
        app = Application(backend="uia").connect(title=application_window_title, timeout=20)
        
        win = app.window(title=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{win.window_text()}'")

        # Directly call the handler to check the reason code screen
        if handle_reason_code_screen(win):
            print("\nReason code handled successfully.")
        else:
            print("\nFailed to handle reason code.")


    except (findwindows.ElementNotFoundError, timings.TimeoutError):
        print(f"❌ ERROR: Could not find the POS application window ('{application_window_title}').")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

