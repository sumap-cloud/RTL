
from pywinauto import Application
import sys
from pathlib import Path
import time

from Scripts.POS_Workspace.Components.Common_components.Approvalrequired import handle_approval_popup
from Scripts.POS_Workspace.Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Scripts.POS_Workspace.Components.Returns.refund_tbr import handle_refund_screen
from Scripts.POS_Workspace.Components.Returns.returnssalemode import returns_item_selection
from Scripts.POS_Workspace.Components.Returns.search_typeselection import handle_search_type_selection
from Scripts.POS_Workspace.Components.Returns.tbr_load_transaction import handle_transaction_return_screen
from Components.Returns.search_transaction import search_transaction_and_enter_number
from Components.Common_components.handle_any_popup_POS import handle_Any_popup

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

# Add the project root and Components directory to the Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
components_path = project_root / 'Components'
if str(components_path) not in sys.path:
    sys.path.insert(0, str(components_path))
    
from Components.Common_components.pos_login import mainlogic
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Tenders.tenderSelection import process_tender
from Components.Tenders.eft_processingpage import handle_eft_transaction
from Components.Tenders.Manual_EFT_Processing import handle_manual_eft_screen
from Components.Tenders.EFT_Auth_Code import handle_auth_code_screen
from Components.Common_components.cashDrawer import cashdrawer_move_and_close

def eftmanual():
    print("\n--- Step 1: Starting the main application and logging in ---")
    application_window_title = ".*R10PosClient.*"  # Replace with the actual title of your application window

    try:
        mainlogic("ATcash5", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)  # Increased timeout
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False
    time.sleep(2)  # Wait for the application to stabilize  
    
    if not Kayin_EAN_POS( eans_to_add = [
           "9315087102204"
        ]):
        print("Failed to add item by EAN. Exiting script.")
        return False
    time.sleep(2)  # Wait for item to be added
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("✓ Navigated to Loyalty Mode")
    time.sleep(4)  # Wait for EFT processing page to load 
    if not handle_customer_popup(app, None):
        print("Failed to handle customer popup. Exiting script.")
        return False
    time.sleep(3)  # Wait for EFT processing page to load
    if not handle_eft_transaction():
        print("Failed to handle EFT transaction. Exiting script.")
        return False
    time.sleep(2)  # Wait for EFT processing page to load
    ACTION_TO_PERFORM = "Yes"  # Change to "No" if you want to test the 'No' button
    if not handle_manual_eft_screen(win, ACTION_TO_PERFORM):  # Change to "no" if you want to test the 'No' button
        print("Failed to handle manual EFT screen. Exiting script.")
        
    time.sleep(2)  # Wait for EFT processing page to load
    if not handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234"):
        print("Failed to handle approval popup. Exiting script.")
    if not handle_auth_code_screen(win, auth_code_to_enter="655666"):
        print("Failed to handle auth code screen. Exiting script.")
        return False
    time.sleep(2)  # Wait for EFT processing page to load
    is_successful = cashdrawer_move_and_close(status_to_set="close")
    time.sleep(2)  # Wait for cash drawer to close

    if is_successful:
        print("\n--- SCRIPT SUCCEEDED ---")
    else:
        print("\n--- SCRIPT FAILED ---")

    time.sleep(2)  # Wait for cash drawer to close
    
    if not toggle_menu_navigate(["Returns", "Transaction Based", "APPROVAL"]):
        print("Failed to navigate to Returns > Transaction Based > Approval. Exiting script.")
        return False
    time.sleep(2)  # Wait for the Returns > Transaction Based > Approval screen to load
    if not handle_transaction_return_screen(action="click_search"):
        print("\nThe script did not run properly.")
        return False
    time.sleep(2)
    # --- Step 7: Select Search Type and Enter Transaction Number ---
    if not handle_search_type_selection(action="click_pos_parameters"):
        print("\nThe script did not run properly.")
        return False
    time.sleep(2)
    if not search_transaction_and_enter_number():
        print("\nThe script did not run properly.")
        return False
    time.sleep(2)
    return_article_name = None  # Not specified as we're using the last transaction
    target_quantity = 1       # Number of items to return
    reason = "Double Scan" 

    if not returns_item_selection(
        article_to_return=return_article_name,
        quantity=target_quantity,
        reason_code=reason
    ):
        print("\n--- Failed to process return item selection ---")
    else:
        print("\n--- Successfully processed return item selection ---")
    time.sleep(2)
    #clicking ok button to navigate to tenders in  TBR(trasnaction based return) return
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("Clicked OK buttonto navigate to Tender Mode in TBR return")
    time.sleep(2)

    # --- Step 8: Handle Any Popups ---
    was_handled = handle_Any_popup()

    # This logic will now correctly report when no popup is found.
    if was_handled:
        print("\nPopup was successfully handled.")
    else:
        print("\nNo popup was handled (either not found, no button was clicked, or an error occurred).")
    time.sleep(2)
    # handle refund screen and complete transaction based return
    result_switch = handle_refund_screen(expected_tender='EFT')
    if result_switch:
        print("\n✅ Test Case 1 completed successfully.")
    else:
        print("\n❌ Test Case 1 failed.")
    
    if not handle_manual_eft_screen(win, ACTION_TO_PERFORM):  # Change to "no" if you want to test the 'No' button
        print("Failed to handle manual EFT screen. Exiting script.")
        
    time.sleep(2)  # Wait for EFT processing page to load
    if not handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234"):
        print("Failed to handle approval popup. Exiting script.")
    if not handle_auth_code_screen(win, auth_code_to_enter="655666"):
        print("Failed to handle auth code screen. Exiting script.")
        return False
    time.sleep(2)  # Wait for EFT processing page to load
    is_successful = cashdrawer_move_and_close(status_to_set="close")

    if is_successful:
        print("\n--- SCRIPT SUCCEEDED ---")
    else:
        print("\n--- SCRIPT FAILED ---")

    
    print("✓ EFT Manual Process Completed Successfully")
    return True


eftmanual()