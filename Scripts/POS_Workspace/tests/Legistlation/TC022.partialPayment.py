from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing necessary components for POS automation
from Scripts.POS_Workspace.Components.Common_components.cashDrawer import cashdrawer_move_and_close
from Scripts.POS_Workspace.Components.funds.change_screen_funds import chnagescreen_funds
from Scripts.POS_Workspace.Components.Tenders.tenderSelection import process_tender
from Scripts.POS_Workspace.Components.Common_components.pos_login import mainlogic
from Scripts.POS_Workspace.Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Scripts.POS_Workspace.Components.Salemode.Keyin_item import Kayin_EAN_POS
from Scripts.POS_Workspace.Components.Salemode.item_search import perform_item_search
from Scripts.POS_Workspace.Components.Salemode.PLUMenu import click_plu_path
from Scripts.POS_Workspace.Components.Salemode.basket_with_itemdetails import get_basket_info
from Scripts.POS_Workspace.Components.Recall.recall_transction import recall_transaction
from Scripts.POS_Workspace.Components.Recall.transaction_selction_recall import find_transaction
from Scripts.POS_Workspace.Components.Recall.recall_intervention_List import solve_intervention
from Scripts.POS_Workspace.Components.legislation.ageRestriction_window import handle_age_restriction
from Scripts.POS_Workspace.Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Scripts.POS_Workspace.Components.Common_components.ResonCode_popup import  handle_select_reason_code_popup
from Scripts.POS_Workspace.Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Scripts.POS_Workspace.Components.Loyalty.validate_loyalty_card import validate_loyalty_card
from Scripts.POS_Workspace.Components.Recall.transaction_selction_recallv2 import select_recall_transaction

from Scripts.POS_Workspace.Components.Tenders.Cash_tender_payment import process_tenders
from Components.Tenders.CashPartialAmount import enter_cash_tender_amount

def test_BonusBuy():
    
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
 
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash5", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20) # Increased timeout
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False
    
    
    if not Kayin_EAN_POS(eans_to_add=["9300624016540"]):
        print("❌ Failed to add item using EAN code")
        return False
    
    time.sleep(5)

    # --- Step 4: Validate Basket Contents ---
    print("\n--- Step 4: Verifying basket details ---")
    # Check all added items, prices, and quantities are correct
    if not get_basket_info():
        print("❌ Failed to verify basket contents")
        return False

    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("✓ Navigated to Loyalty Mode")

    time.sleep(2)  # Wait for the UI to update after clicking OK
    if not handle_customer_popup(app, customer_number=None):
        print("Failed to handle customer number popup.")
        return False

    time.sleep(5)
    
    if not process_tender(tender_name="Cash", tender_option="Manual Entry"):
        print("Failed to process cash tender payment.")
        return False
    

    amount_to_test = "5.00"
    if not enter_cash_tender_amount(amount_to_test):
            print("\n Cash amount entry fail.")
            return False
           
            time.sleep(2)

    time.sleep(5)

    if not process_tender(tender_name="Cash"):
        print("Failed to process cash tender payment.")
        return False
    time.sleep(5)

    if not process_tenders(app, tender_to_select="Cash"):
        print("\n Failed cash tender completion")
        return False

    time.sleep(3)

    print("\n--- Step 5: Processing cash tender payment ---")
    if not handle_Any_popup(specific_button="Close"):
        print("❌ popup not handled")
        
    
    time.sleep(2)
    # --- Step 6: Verify Cash Drawer ---
    print("\n--- Step 6: Verifying cash drawer status ---")
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to verify cash drawer status")
        return False

    
    print("\n--- All tasks completed successfully in paid out process! --- 🎉")
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_BonusBuy()
