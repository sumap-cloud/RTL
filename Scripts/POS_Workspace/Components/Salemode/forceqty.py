from pywinauto.application import Application
import time
from collections import defaultdict
import sys
from pathlib import Path


# --- Setup system path to import custom modules ---
current_file_path = Path(__file__).resolve()
# Assuming the script is in Components/Salemode, we go up three levels to the project root
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Common_components.virtual_numpad import numpad_keyin


def handle_force_quantity(win, quantity_to_enter):
    """
    Handles the entire 'Force Quantity' workflow from capturing details to final approval.

    Args:
        win: The main application window object from pywinauto.
        quantity_to_enter (str or int): The quantity to be entered.

    Returns:
        bool: True if the entire process is successful, False otherwise.
    """
    try:
        # --- 1. Find the "Force Quantity" screen and wait for it to be visible ---
        details_view = win.child_window(auto_id="QuantityItemViewID", control_type="Custom")
        print("\nWaiting for the Force Quantity screen to appear...")
        details_view.wait('visible', timeout=15)
        print("Force Quantity screen is visible.")
        
        # --- 2. Capture and print details from the screen (for logging/verification) ---
        print("\nCapturing specified details from the screen...")
        captured_lines = []
        try:
            title_element = win.child_window(title="Force Quantity", control_type="Text")
            if title_element.exists():
                captured_lines.append(f"Found line: {title_element.window_text()}")
        except Exception: pass
        
        lines = defaultdict(list)
        descendant_elements = details_view.descendants()
        for elem in descendant_elements:
            if hasattr(elem, 'window_text'):
                elem_text = elem.window_text()
                rect = elem.element_info.rectangle
                if elem_text and elem_text.strip() and rect.width() > 0 and rect.height() > 0:
                    lines[rect.top].append(elem)
        for top_coord in sorted(lines.keys()):
            sorted_elements = sorted(lines[top_coord], key=lambda e: e.element_info.rectangle.left)
            line_text = "".join([elem.window_text() for elem in sorted_elements])
            if line_text and line_text.strip():
                captured_lines.append(f"Found line: {line_text}")

        print("\n--- Captured Details ---")
        if not captured_lines:
            print("Could not find any details to capture.")
        else:
            for line in captured_lines:
                if "Approve" not in line and "Cancel" not in line:
                    print(line)
        print("------------------------")

        # --- 3. Enter the quantity using the imported numpad function ---
        if numpad_keyin(number=str(quantity_to_enter), OKclick=False):
            print(f"\nQuantity '{quantity_to_enter}' entered successfully via numpad.")
            
            # --- 4. Click the final "Approve" button ---
            print("Finding the final 'Approve' button...")
            approve_button = details_view.child_window(title="Approve", control_type="Button")
            approve_button.click_input()
            print("Clicked 'Approve'.")
            return True  # Success
        else:
            print(f"\nFailed to enter quantity '{quantity_to_enter}' via numpad.")
            return False # Failure
            
    except Exception as e:
        print(f"\nAn error occurred during force quantity handling: {e}")
        return False # Failure

# --- Main execution block ---
# This makes the script runnable and the function reusable.
if __name__ == "__main__":
    try:
        # --- Connect to the main application window ---
        application_window_title = ".*R10PosClient.*"
        print(f"Connecting to application with title: {application_window_title}")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("Successfully connected to the main application window.")

        # --- Execute the test case using the reusable function ---
        if handle_force_quantity(win, quantity_to_enter="9"):
            print("\nTest Case finished successfully.")
        else:
            print("\nTest Case failed.")
            
    except Exception as e:
        print(f"\nAn error occurred during the main process: {e}")
        print("\nTips for troubleshooting:")
        print("1. Ensure the Force Quantity screen is triggered and visible before the script times out.")
        print("2. If the application is updated, the 'auto_id' or layout of the controls could change.")

