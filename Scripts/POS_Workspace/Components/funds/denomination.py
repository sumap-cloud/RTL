import time
from pywinauto.application import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError
from pywinauto.controls.uia_controls import ButtonWrapper, EditWrapper, ListViewWrapper

# --- Step 1: Define a method to type using the on-screen number pad ---
def type_on_numpad(win, text_to_type: str):
    """
    Simulates typing a string of digits using the on-screen number pad.

    Args:
        win: The main application window wrapper.
        text_to_type: The string of digits to type (e.g., "123").
    """
    print(f"Typing '{text_to_type}' on the number pad...")
    for char in text_to_type:
        # Find the button with the corresponding digit and click it
        win.child_window(title=char, control_type="Button").click_input()
        time.sleep(0.1) # Small delay between clicks

# --- Step 2: NEW - Define a robust method to get only denomination buttons ---
def get_denomination_buttons(win):
    """
    Gets all buttons from the window and filters out non-denomination buttons.

    Args:
        win: The main application window wrapper.

    Returns:
        A list of ButtonWrapper objects for the denomination buttons.
    """
    all_buttons = win.descendants(control_type="Button")
    # Define text of buttons to exclude (number pad, actions, etc.)
    excluded_texts = ["OK", "Cancel", "<<", "X", "C", ".", "Delete All", "Delete", "Paid Out"]
    # Also exclude the single-digit numpad buttons
    excluded_texts.extend([str(i) for i in range(10)])

    denom_buttons = []
    for button in all_buttons:
        text = button.window_text()
        # Only include buttons that have text and are not in the excluded list
        if text and text not in excluded_texts:
            denom_buttons.append(button)
    return denom_buttons

# --- Step 3: Define the method to process a single denomination ---
def process_denomination(win, denom_button: ButtonWrapper, ok_button: ButtonWrapper, summary_list: ListViewWrapper):
    """
    Clicks a denomination button, enters a quantity of 1 using the number pad,
    clicks OK, and captures the result from the summary list.

    Args:
        win: The main application window wrapper.
        denom_button: The specific denomination button to click.
        ok_button: The 'OK' button on the number pad.
        summary_list: The list control that displays the cash summary.
    """
    try:
        denom_text = denom_button.window_text()
        if not denom_text:  # This check is now mostly redundant but safe to keep
            return

        print(f"Processing '{denom_text}'...")

        print(f"Clicking '{denom_text}' button...")
        denom_button.click_input()
        time.sleep(0.5)

        # Enter quantity '1' using the number pad
        type_on_numpad(win, "1")
        time.sleep(0.5)

        # Click the "OK" button on the number pad
        print("Clicking 'OK'...")
        ok_button.click_input()
        time.sleep(1)  # Wait for the summary to update

        # --- Capture the updated cash summary ---
        print("Capturing cash summary...")
        summary_items = summary_list.texts()
        if summary_items:
            flat_list = [item for sublist in summary_items for item in sublist]
            if flat_list:
                print(f"Last entry in summary: {flat_list[-1]}")
            else:
                print("Cash summary list is empty after flattening.")
        else:
            print("Cash summary is empty.")
        print("-" * 20)

    except (MatchError, TimeoutError, IndexError) as denom_err:
        print(f"Error processing button '{denom_button.window_text()}': {denom_err}")

# --- Main script execution ---
if __name__ == "__main__":
    app_title = ".*R10PosClient.*"
    tab_names = ["Coin", "Note", "Roll"]

    try:
        # --- Step 4: Connect to the Application ---
        print(f"Attempting to connect to '{app_title}'...")
        app = Application(backend="uia").connect(title_re=app_title, timeout=20)
        win = app.window(title_re=app_title)
        win.wait('ready', timeout=20)
        win.set_focus()
        print("Successfully connected to the window.")

        # --- Step 5: Verify the "Select Denominations" Screen ---
        print("\nLooking for the 'Select Denominations' screen...")
        win.child_window(title="Select Denominations:", control_type="Text").wait('visible', timeout=20)
        print("Successfully identified the 'Select Denominations' screen.")

        # --- Step 6: Interact with each denomination by tab ---
        print("\n--- Interacting with each denomination ---")

        ok_button = win.child_window(auto_id="OK", control_type="Button")
        summary_list = win.child_window(auto_id="SummaryList", control_type="List")
        tab_control = win.child_window(auto_id="denominationTabControl", control_type="Tab")

        for tab_name in tab_names:
            try:
                print(f"\nSwitching to '{tab_name}' tab...")
                tab_control.child_window(title=tab_name, control_type="TabItem").click_input()
                time.sleep(1.5)

                # Use the new robust function to get buttons
                denomination_buttons = get_denomination_buttons(win)
                print(f"Found {len(denomination_buttons)} denomination buttons in '{tab_name}' tab.")

                for denom_button in denomination_buttons:
                    process_denomination(win, denom_button, ok_button, summary_list)

            except (MatchError, TimeoutError) as tab_err:
                print(f"Could not find or click the '{tab_name}' tab: {tab_err}")
                continue

        print("\n--- Finished processing all denominations ---")

        # --- Step 7: Test multi-digit entry and clearing with the number pad ---
        print("\n--- Testing number pad input and clear button ---")
        try:
            print("Switching to 'Note' tab for number pad test...")
            tab_control.child_window(title="Note", control_type="TabItem").click_input()
            time.sleep(1.5)

            # Use the new robust function again to find a button to click
            denom_buttons_for_test = get_denomination_buttons(win)
            if denom_buttons_for_test:
                first_button = denom_buttons_for_test[0]
                print(f"Clicking '{first_button.window_text()}' to activate quantity entry...")
                first_button.click_input()
                time.sleep(0.5)

                type_on_numpad(win, "42")
                time.sleep(1)

                print("Testing the clear '<<' button...")
                backspace_button = win.child_window(title="<<", control_type="Button")
                backspace_button.click_input()
                time.sleep(0.5)
                backspace_button.click_input()
                time.sleep(1)
                print("Quantity cleared.")

                type_on_numpad(win, "5")
                ok_button.click_input()
                print("Entered '5' and clicked OK.")
                time.sleep(1)
            else:
                print("Could not find any denomination buttons for the number pad test.")

        except Exception as numpad_err:
            print(f"An error occurred during the number pad test: {numpad_err}")

        # --- Step 8: Final actions (uncomment to use) ---
        # ... (rest of the script remains the same) ...

    except TimeoutError:
        print("Error: The 'Select Denominations:' text was not found or the application did not connect in time.")
        print("Please ensure the application is running and you are on the correct screen.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
