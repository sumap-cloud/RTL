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
from Components.funds.change_screen_funds import chnagescreen_funds

from Components.Common_components.pos_login import mainlogic
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Salemode.item_search import perform_item_search
from Components.Salemode.PLUMenu import click_plu_path
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Recall.recall_transction import recall_transaction
from Components.Recall.transaction_selction_recall import find_transaction
from Components.Recall.recall_intervention_List import solve_intervention
from Components.legislation.ageRestriction_window import handle_age_restriction
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Salemode.department_sale import department_sale
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Common_components.Approvalrequired import handle_approval_popup
from Scripts.POS_Workspace.Components.Recall.transaction_selction_recallv2 import select_recall_transaction
from Components.Salemode.item_search import perform_item_search
from Components.Salemode.department_amount import enter_item_price
from Components.Loyalty.validate_loyalty_card import validate_loyalty_card
from Components.Salemode.gs1_manual_entry import automate_gs1_screen
from Components.Loyalty.member_card_details import click_member_card_and_validate
from Components.Loyalty.Loyaltycardimage_OCR import validate_orange_logo_with_opencv
def loyaltycard_validation():
    application_window_title = ".*R10PosClient.*"
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
    
    if not click_plu_path(["Heavy & Misc", "Soft Drinks (10 Pack)", "coke z/s 10pk"]):
        print("Failed to click PLU path for Apple Mi Apple 1Kg Punnet.")
        return 
    time.sleep(3)  # Wait for the UI to update after clicking PLU


    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
    else:
        print("\nOK button not found.")
        return False
    time.sleep(3)
    if not handle_customer_popup(app, "9344402191258"): 
        print("\nFailed to handle customer popup.")
        return False
    time.sleep(4)  # Wait for the popup to settle
    
    was_handled_specific = handle_Any_popup(specific_button="Save for Next Shop")
    if was_handled_specific:
        print("\n✅ Specific popup handler finished successfully.")
    else:
        print("\n❌ Specific popup handler encountered a critical error.")

    time.sleep(3)
    
    # if not validate_loyalty_card():
    #     print("\n membercard details not captured")
    # else:
    #     print("\n membercard details captured successfully")
        
    time.sleep(3)
    if not validate_orange_logo_with_opencv(win, exist=True):
        print("\n Orange logo validated")
    

    if not click_member_card_and_validate():
        print("\n membercard not validated")
        return False
    from Components.Tenders.Cash_tender_payment import process_tenders
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process cash tender payment.")
        return False
    
    if not handle_Any_popup():
        print("Failed to handle any popup.")
        
    time.sleep(3)
    from Components.Common_components.cashDrawer import cashdrawer_move_and_close
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("Failed to move and close the cash drawer.")
        return False
    
# #9344402191258

loyaltycard_validation()