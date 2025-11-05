from pywinauto import Application
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



def basic_happy_flow():
    
    
    # step1: mainlogic is for logging in to the POS application
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
    # --- Step 2: Key in an item with EAN in sale mode
    if not Kayin_EAN_POS( eans_to_add = [
    
            "9300675014779"
    
        ]):
        print("Failed to key in item with EAN 1234567890123")
        return False
    # --- Step 3: Validate basket information(this is common reusable method for all flows after adding articles we have check check basket )
    if not get_basket_info():
        print("Failed to retrieve basket information")
        return False
    # --- Step 4: Click on the 'OK' button to navigate loyalty mode (this is common reusable method for all flows)
    Okay_btn = win.child_window(title="OK", control_type="Button")
    if Okay_btn.exists():
        Okay_btn.click_input()
        print("Clicked OK button")
    time.sleep(3)  # Wait for the UI to update
    # --- Step 5: Handle customer popup (customerpopup method we will use for loyalty handle)
    print("\n--- Step 2: Handling customer popup ---")
    customer_number=None
    if not handle_customer_popup(app,customer_number):
        print("Failed to handle customer popup")
        return False   
    time.sleep(3)  # Wait for the popup to settle
    # --- Step 6: Process tenders (in tender mode we will be having multiple tenders as of now we are choosing cash tender to complete transaction)
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process tenders")
        return False
    # --- Step 7: Handle any popups here we are using for handle receipt popup (receipt poup we will get after completing transaction)
    if not handle_Any_popup():
        print("Failed to handle any popup")
        return False
    time.sleep(2)  # Wait for the popup to settle
    # --- Step 8: Move and close cash drawer method we will use for close cashdrawer (for every cash sale we will be closing cash drawer)
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("Failed to move and close cash drawer")
        return False
    print("\n--- Basic Happy Flow completed successfully ---")

basic_happy_flow()
    