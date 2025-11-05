from pywinauto import Application, findwindows, timings
from pathlib import Path
import sys
import time

def solve_intervention():
    """
    This function automates solving an intervention list item in the POS system.
    It connects to the application, captures text from the specific intervention screen areas,
    prints it, finds the 'Solve' button, and clicks it.
    """
    # Regular expression to match the window title of your POS application
    application_window_title = ".*R10PosClient.*"

    try:
        # Step 1: Connect to the already running POS application
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        
        # Get the main window object
        win = app.window(title_re=application_window_title)
        win.set_focus()

        # Step 2: Capture text from specific panes on the intervention screen
        all_texts = []
        
        # Helper function to extract text from a given UI element and its children
        def capture_text_from_container(container):
            for control in container.descendants():
                try:
                    text = control.window_text()
                    # Add text if it's not empty and not already in our list
                    if text and text.strip() and text not in all_texts:
                        all_texts.append(text)
                except Exception:
                    # Some controls might not have text, so we continue
                    continue

        # Try to find the container for the intervention list (left pane)
        # We locate it by finding the "Intervention List" header (with a less strict search) and then getting its parent container
        try:
            # Removed control_type to make the search less restrictive
            list_container = win.child_window(title="Intervention List", auto_id="TextBlock",control_type="Text").parent()
            capture_text_from_container(list_container)
        except findwindows.ElementNotFoundError:
            print("Warning: Could not find the 'Intervention List' pane.")
        
        # Try to find the container for the item details and action buttons (right pane)
        # We locate it by finding the "Solve" button and then getting its grandparent,
        # as the item details and buttons might be in sibling containers.
        try:
            actions_container = win.child_window(title="Solve", control_type="Button").parent().parent()
            capture_text_from_container(actions_container)
        except findwindows.ElementNotFoundError:
            print("Warning: Could not find the pane containing the 'Solve' button.")

        # Print the captured texts from the targeted areas
        if all_texts:
            # Filter out some common, non-useful text
            filtered_texts = [t for t in all_texts if "DataPager" not in t and "BlankSpace" not in t]
            for text in filtered_texts:
                print(text)
        else:
            print("No text could be captured from the intervention screen areas.")


        # Step 3: Find the 'Solve' button again to perform the click
        solve_button = win.child_window(title="Solve", control_type="Button")

        # Step 4: Click the 'Solve' button
        if solve_button.exists() and solve_button.is_enabled():
            solve_button.click()
            print("Clicking the 'Solve' button...")
            return True
        else:
            print("Error: Could not find the 'Solve' button or it was not enabled.")
            print("Please make sure you are on the 'Intervention List' screen.")

    except timings.TimeoutError:
        print(f"Connection timed out. Please make sure the POS application with title matching '{application_window_title}' is running.")
    except findwindows.ElementNotFoundError:
        print("Could not find the specified window or button. The application might not be on the correct screen, or the button text might be different.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# This block allows the script to be run directly from the command line
if __name__ == "__main__":
    solve_intervention()

