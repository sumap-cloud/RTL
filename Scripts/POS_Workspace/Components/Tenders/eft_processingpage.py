import re
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError

# Adjust import based on how the script is run
from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
    
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    # This works when the file is part of a package
from Components.Tenders.tenderSelection import process_tender

class EftProcessor:
    """
    A class to handle all interactions with the EFT processing view in the POS application.
    """
    def __init__(self):
        """Initializes the processor and connects to the POS application."""
        self.app = None
        self.win = None
        try:
            # Connect to the POS application upon creation of the object
            self.app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
            self.win = self.app.window(title_re=".*R10PosClient.*")
            self.win.set_focus()
            print("✅ Connected to R10PosClient application.")
        except ElementNotFoundError:
            print("❌ R10PosClient application window not found during initialization.")
            # Re-raise the exception so any script using this class knows the app isn't running.
            raise

    def process_eft_view(self, click_approve=False):
        """
        Connects to the POS application, processes the EFT view,
        and handles dynamic monetary values. Returns True on success, False on failure.
        """
        try:
            # First, define the specification for the EFT view
            eft_view = self.win.child_window(auto_id="EFTAmountViewID", control_type="Custom")
            # Then, wait for it to be ready
            eft_view.wait('exists enabled visible ready', timeout=15)
            print("\n✅ EFTAmountViewID found")
        except TimeoutError:
            print("❌ EFTAmountViewID not found within the timeout period.")
            return False

        # --- Dynamically Capture UI elements with changing values ---
        money_pattern = re.compile(r"[\d,]+\.\d{2}")

        try:
            balance_label = eft_view.child_window(title=" Balance Due:", control_type="Text")
            balance_label_rect = balance_label.rectangle()
        except ElementNotFoundError:
            print("❌ Could not find the 'Balance Due:' label.")
            return False

        all_children = eft_view.children()
        candidate_controls = [c for c in all_children if money_pattern.match(c.window_text() or '')]

        if not candidate_controls:
            print("❌ No controls with monetary values found on the screen.")
            return False

        balance_amount_control = None
        min_distance = float('inf')
        for control in candidate_controls:
            try:
                control_rect = control.rectangle()
                if control_rect.left > balance_label_rect.right and abs(control_rect.top - balance_label_rect.top) < 25:
                    distance = control_rect.left - balance_label_rect.right
                    if distance < min_distance:
                        min_distance = distance
                        balance_amount_control = control
            except Exception:
                continue

        if not balance_amount_control:
            print("❌ Failed to dynamically locate the balance amount value.")
            return False

        try:
            total_amount_control = eft_view.child_window(auto_id="tbTotalAmount_InnerText")
        except ElementNotFoundError:
            total_amount_control = next((c for c in candidate_controls if c != balance_amount_control), None)

        if not total_amount_control:
            print("❌ Failed to dynamically locate the total amount value.")
            return False

        # --- Capture the rest of the UI elements ---
        cashout_edit = eft_view.child_window(auto_id="tbCashBack_InnerText", control_type="Edit")
        approve_button = eft_view.child_window(title="Approve", control_type="Button")
        cancel_button = eft_view.child_window(title="Cancel", control_type="Button")

        # Print captured values
        print(f"Balance Amount: {balance_amount_control.window_text()}")
        print(f"Cashout Amount: {cashout_edit.window_text()}")
        print(f"Total Amount: {total_amount_control.window_text()}")

        # --- Capture suggested cashout amounts ---
        try:
            cashout_suggestion_EFT = self.win.child_window(class_name="CashOutSuggestedAmountView")
            suggested_listbox = cashout_suggestion_EFT.child_window(auto_id="SuggestedCashListBox", control_type="List")
            suggestion_items = suggested_listbox.children(control_type="ListItem")

            print("\n💡 Suggested Cashout Amounts:")
            for item in suggestion_items:
                try:
                    print(f" - {item.window_text()}")
                except Exception as e:
                    print(f"⚠️ Error reading suggestion item: {e}")
        except ElementNotFoundError:
            print("ℹ️ Suggested cashout amounts view not found. Skipping.")

        # Optionally click Approve
        if click_approve:
            print("\n🟢 Clicking Approve button...")
            approve_button.click_input()
            print("✅ Approved successfully.")

        return True

def process_eft_view(click_approve=False):
    """
    A simple, importable function that handles the EFT view processing.
    It creates an EftProcessor instance and calls its method.
    """
    try:
        eft_handler = EftProcessor()
        return eft_handler.process_eft_view(click_approve=click_approve)
    except ElementNotFoundError:
        # This error is raised if the app window is not found during initialization.
        # The EftProcessor class already prints a detailed message.
        return False
    except Exception as e:
        print(f"An unexpected error occurred during the EFT view process: {e}")
        return False

# --- NEW REUSABLE COMPONENT ---
def handle_eft_transaction():
    """
    Handles a complete EFT transaction by selecting the EFT tender
    and approving the EFT view. This is the primary function to be called
    from other workflow files for a standard EFT payment.
    
    Returns:
        bool: True if the entire process is successful, False otherwise.
    """
    print("▶️ Starting full EFT transaction...")
    try:
        # Step 1: Select the EFT tender
        print("  1. Selecting EFT tender...")
        if not process_tender(tender_name="EFT"):
            print("❌ Failed to select EFT tender. Aborting transaction.")
            return False
        print("  ✅ EFT tender selected successfully.")

        # Step 2: Process the EFT view and approve it
        print("\n  2. Processing EFT view...")
        if not process_eft_view(click_approve=True):
            print("❌ Failed to process the EFT view. Transaction may be incomplete.")
            return False
        
        print("\n✅ Full EFT transaction completed successfully.")
        return True

    except Exception as e:
        print(f"An unexpected error occurred during the full EFT transaction workflow: {e}")
        return False

# This block allows you to run this file by itself for testing purposes.
if __name__ == "__main__":

    # This calls the new, all-in-one function.
    if handle_eft_transaction():
        print("\n✅ Standalone test PASSED.")
    else:
        print("\n❌ Standalone test FAILED.")

