"""
================================================================================
 Select Tender Screen Handler
================================================================================

PURPOSE:
--------
This module handles the "Select Tender" pop-up window, which appears after
choosing to 'Switch Tender' on the refund screen. It is designed to be a
reusable component.

The main function, `handle_select_tender_screen`, provides a single entry point to:
1. Connect to the "Select Tender" pop-up window.
2. Capture all available tender options.
3. Select a specific tender type (e.g., "Cash", "EFT") or "Close" the window.

"""
import time
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError

def handle_select_tender_screen(tender_to_select=None):
    """
    Connects to the "Select Tender" window and clicks the specified tender button.

    Args:
        tender_to_select (str, optional): The name of the tender button to click.
                                        Can be "Cash", "EFT", "Gift Cards", 
                                        "In-Store Credit", or "Close". If no tender is
                                        provided, it will click "Close". Defaults to None.

    Returns:
        dict or None: A dictionary with the screen title and available tenders
                      if successful, otherwise None.
    """
    print("\n--- Handling Select Tender Screen ---")
    window_title_regex = ".*SwitchTenderViewModelOverride.*"

    try:
        print(f"Attempting to connect to window: '{window_title_regex}'...")
        app = Application(backend="uia").connect(title_re=window_title_regex, timeout=15)
        win = app.window(title_re=window_title_regex)
        win.set_focus()
        print("✅ Successfully connected to the Select Tender window.")
    except (ElementNotFoundError, TimeoutError):
        print("❌ ERROR: Select Tender window not found.")
        return None

    try:
        # --- Data Capture ---
        screen_data = {
            "title": "N/A",
            "available_tenders": []
        }

        # Capture the main title of the screen
        try:
            title_control = win.child_window(title="Select Tender", control_type="Text")
            if title_control.exists():
                screen_data["title"] = title_control.window_text()
        except ElementNotFoundError:
            print("⚠️ Could not find the main title text.")

        # Capture all available button texts
        buttons = win.descendants(control_type="Button")
        screen_data["available_tenders"] = [b.window_text() for b in buttons if b.window_text()]

        print("\n--- Captured Screen Details ---")
        print(f"  - Title: {screen_data['title']}")
        print(f"  - Available Options: {screen_data['available_tenders']}")
        print("-----------------------------\n")

        # --- Button Interaction ---
        # If no tender is specified, default to clicking the "Close" button.
        target_button_name = tender_to_select if tender_to_select else 'Close'

        button_to_click = None
        for button in buttons:
            if button.window_text().lower() == target_button_name.lower():
                button_to_click = button
                break
        
        if button_to_click:
            print(f"🖱️ Clicking '{button_to_click.window_text()}' button...")
            button_to_click.click_input()
            print("✅ Button clicked successfully.")
            return screen_data
        else:
            print(f"❌ ERROR: Could not find the specified button '{target_button_name}'.")
            return None

    except Exception as e:
        print(f"❌ An unexpected error occurred on the Select Tender screen: {e}")
        return None

# ==============================================================================
#  EXECUTABLE BLOCK FOR STANDALONE TESTING
# ==============================================================================
if __name__ == "__main__":
    print("--- Running Select Tender Screen Handler in standalone mode for testing ---")
    
    # This example demonstrates selecting a specific tender.
    print("\n--> Testing tender selection (will click 'Cash')...")
    time.sleep(3) # Give yourself time to open the window manually for testing
    
    result = handle_select_tender_screen(tender_to_select="Cash")

    if result:
        print("\n✅ Standalone test completed successfully.")
    else:
        print("\n❌ Standalone test failed.")

