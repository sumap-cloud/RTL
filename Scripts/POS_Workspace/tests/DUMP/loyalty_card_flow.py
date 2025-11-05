from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
from Components.Common_components.pos_login import mainlogic
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Common_components.cashDrawer import cashdrawer_move_and_close
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Tenders.Cash_tender_payment import process_tenders

def loyalty_card_flow():
    try:
        # --- Step 1: Log in to the POS application ---
        print("\n--- Step 1: Starting the main application and logging in ---")
        mainlogic("ATcash1", "abcd1234")
        application_window_title = ".*R10PosClient.*"
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False

    # --- Step 2: Key in an item with EAN in sale mode ---
    print("\n--- Step 2: Adding item to basket ---")
    if not Kayin_EAN_POS( eans_to_add = [
    
            "9300675014779"
    
        ]):
        print("Failed to key in item with EAN 1234567890123")
        return False

    # --- Step 3: Validate basket information ---
    print("\n--- Step 3: Validating basket information ---")
    if not get_basket_info():
        print("Failed to retrieve basket information")
        return False

    # --- Step 4: Navigate to loyalty mode ---
    print("\n--- Step 4: Navigating to loyalty mode ---")
    Okay_btn = win.child_window(title="OK", control_type="Button")
    if Okay_btn.exists():
        Okay_btn.click_input()
        print("Clicked OK button")
    time.sleep(3)  # Wait for the UI to update

    # --- Step 5: Handle loyalty card input ---
    print("\n--- Step 5: Entering loyalty card number ---")
    customernumber_provided = "9344402191258"  # Example loyalty card number
    if not handle_customer_popup(app,customernumber_provided):
        print("Failed to enter loyalty card number")
        return False
    time.sleep(2)  # Wait for the popup to settle

    # --- Step 6: Process payment with cash tender ---
    print("\n--- Step 6: Processing cash payment ---")
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process cash payment")
        return False

    # --- Step 7: Handle receipt popup ---
    print("\n--- Step 7: Handling receipt popup ---")
    if not handle_Any_popup():
        print("Failed to handle receipt popup")
        return False
    time.sleep(2)  # Wait for the popup to settle

    # --- Step 8: Handle cash drawer ---
    print("\n--- Step 8: Closing cash drawer ---")
    if not cashdrawer_move_and_close():
        print("Failed to close cash drawer")
        return False

    print("\n--- Loyalty Card Flow completed successfully ---")
    return True

if __name__ == "__main__":
    loyalty_card_flow()
