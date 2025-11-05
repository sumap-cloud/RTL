import time
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError

def handle_receipt_popup(app, expected_text="Is a receipt required?", timeout=15):
    """
    Waits for a popup window containing specific text and handles it.
    Specifically, it looks for and clicks the 'Yes' button.
    """
    print(f"\n⏳ Waiting for popup containing text '{expected_text}' for up to {timeout} seconds...")
    
    popup = None
    start_time = time.time()
    
    # Loop until the timeout is reached, looking for the popup
    while time.time() - start_time < timeout:
        try:
            # Get the current top-level window
            potential_popup = app.top_window()
            # Check if a static text element with the expected content exists within this window
            if potential_popup.child_window(title=expected_text, control_type="Text").exists():
                popup = potential_popup
                print(f"✅ Found popup containing the expected text.")
                break  # Exit the loop once the popup is found
        except Exception:
            # Ignore errors if a transient window appears and disappears
            pass
        time.sleep(0.5) # Wait half a second before checking again

    # If the loop finishes and the popup was not found, report a timeout
    if popup is None:
        print(f"❌ Timeout: The popup with text '{expected_text}' did not appear within {timeout} seconds.")
        return False

    try:
        popup.set_focus()
        
        # --- Find and click the 'Yes' button ---
        print("\n🔎 Searching for the 'Yes' button...")
        
        # Look for a button with the text "Yes"
        yes_button = popup.child_window(title="Yes", control_type="Button", found_index=0)
        
        if yes_button.exists():
            print("🔘 Found 'Yes' button. Clicking it...")
            yes_button.click_input()
            print("✅ 'Yes' button clicked successfully.")
            print("🧾 Receipt handled.")
            return True
        else:
            print("❌ 'Yes' button not found in the popup.")
            # Optional: Print details of all buttons for debugging
            print("\n🕵️‍♂️ Debugging Info: Listing all buttons found in popup...")
            buttons = popup.descendants(control_type="Button")
            if not buttons:
                print("  - No buttons found at all.")
            for btn in buttons:
                try:
                    print(f"  - Text: '{btn.window_text()}', AutoID: '{btn.automation_id()}'")
                except Exception:
                    print(f"  - (Could not retrieve info for a button)")
            return False
            
    except ElementNotFoundError as e:
        print(f"❌ Error: A UI element within the popup was not found.")
        print(f"Details: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred while handling the popup: {e}")
        return False

if __name__ == "__main__":
    try:
        # Connect to the running application to test the receipt handler
        print("Connecting to application to test receipt handler...")
        app_conn = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        
        # Manually trigger the action that causes the receipt popup in your application,
        # then run this script.
        handle_receipt_popup(app_conn)
        
    except ElementNotFoundError:
        print("❌ Application window 'R10PosClient' not found. Is the application running?")
    except Exception as e:
        print(f"Failed to connect to the application: {e}")

