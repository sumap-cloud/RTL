import time
from pywinauto import Application, timings

def add_item_by_ean(win, ean):
    """
    Adds a single item to the basket using its EAN. Checks if input is clear first.

    Args:
        win: The pywinauto window object for the application.
        ean: The EAN code (as a string or number) of the item to add.
    
    Returns:
        True if the item was added successfully, False otherwise.
    """
    print(f"\n=== Adding item: {ean} ===")
    
    def click_button_by_text(text, timeout=5):
        """
        Finds and clicks a button based on its visible text.
        Waits until the button is found or timeout is reached.
        """
        try:
            # More efficient way to wait for a button
            button = win.child_window(title=text, control_type="Button", found_index=0)
            button.wait('visible enabled', timeout=timeout)
            button.click_input()
            # print(f"Clicked '{text}' button.") # Uncomment for detailed logging
            return True
        except timings.TimeoutError:
            print(f"❌ Timed out waiting for button with text: '{text}'")
            return False
        except Exception as e:
            print(f"❌ Error clicking button '{text}': {e}")
            return False
    
    # --- VALIDATION STEP ---
    # Check if the input area is clear by looking for the prompt text.
    try:
        # This static text is visible only when the input field is empty and ready.
        prompt_text = win.child_window(title="Please Scan/Enter Item Code", control_type="Text")
        prompt_text.wait('visible', timeout=2) # Wait a short time to see if it's there.
        print("✅ Input field is ready.")
    except timings.TimeoutError:
        # If the prompt text is not found, assume the field has an entry and needs clearing.
        print("⚠️  Input field not ready. Attempting to clear...")
        if not click_button_by_text("C"):
            print("⚠️  'Clear' (C) button not found. Falling back to Backspace '<<'.")
            # Fallback to clicking backspace multiple times if 'C' isn't available
            for _ in range(20): 
                # This is a fallback and might not be needed if 'C' always exists
                backspace_button = win.child_window(title="<<", control_type="Button", found_index=0)
                if backspace_button.exists() and backspace_button.is_visible():
                    backspace_button.click_input()
                    time.sleep(0.05)
                else:
                    break # Stop if backspace is no longer visible
        time.sleep(0.2) # Small pause after clearing
    
    # Enter each digit of the EAN
    for digit in str(ean):
        if not click_button_by_text(digit):
            print(f"❌ Failed to enter digit: {digit}")
            return False
        time.sleep(0.1) # Pause between digit presses
    
    # Confirm the entry by clicking 'OK'
    if not click_button_by_text("OK"):
        print("❌ Failed to click OK button")
        return False
    
    print(f"✅ Successfully processed item: {ean}")
    return True

def Kayin_EAN_POS(eans_to_add):
    """
    Main function to connect to the application and add a list of items by EAN.
    """
    try:
        # Connect to the running application
        print("Connecting to the R10PosClient application...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=20)
        win = app.window(title_re=".*R10PosClient.*")
        
        print("Application found. Setting focus.")
        win.set_focus()  # Ensure the window is focused before interacting
        
        # --- List of EANs to add ---
        # You can add or remove any EANs from this list.
       
        
        print(f"\nFound {len(eans_to_add)} items to add.")

        # Loop through the list and add each item
        for item_ean in eans_to_add:
            success = add_item_by_ean(win, item_ean)
            if not success:
                print(f"‼️ Halting script because an error occurred while adding item {item_ean}.")
                break # Stop the loop if an item fails to be added
            time.sleep(1) # Wait for 1 second before adding the next item
        
        print("\n=== Script finished ===")
        return True
    except timings.TimeoutError:
        print("\n❌ Error: Could not find the application window within the timeout period.")
        print("Please ensure the 'R10PosClient' application is running and the main window is visible.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    Kayin_EAN_POS( eans_to_add = [
            "8720400000210",
            "9300624010500",
            "8712345678905"
        ])

