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
from Components.Tlog.get_txn_details import get_transaction_details
from Scripts.POS_Workspace.Components.Tlog.receiptseparator import Fastentry_Tlogvalidation
from Components.Common_components.virtual_numpad import numpad_keyin
from Components.Common_components.getdb_v1 import execute_query

def GCMvalidation():
    
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
    my_server = r"10.80.79.2\SQLEXPRESS" # Use r"..." for strings with backslashes
    my_query = "Select TOP 1 PO.Code from Retail .. CAT_ProductRestriction PR WITH(NOLOCK) inner join Retail .. CAT_StoreRangeProduct CP WITH (NOLOCK)  on CP.Product_Id = PR.Product_Id inner join Retail..CAT_ProductIdentifier PO WITH (NOLOCK) on PO.Product_id = CP.Product_id Where  PR.RestrictionType ='2' and PR.IsRestricted ='1' and PO.Code like '9%';"
    barcodes = execute_query(my_server, my_query)

    if barcodes:
            print(f"Successfully fetched {len(barcodes)} barcodes: {barcodes}")
            
            # 4. Call your function with the list
            print("\nSending list to Kayin_EAN_POS...")    
    else:
            print("No barcodes found matching the query.")
    if not Kayin_EAN_POS( eans_to_add = barcodes):
        print("Failed to key in item with EAN 1234567890123")
        return False
    time.sleep(2)  # Wait for the UI to update
    