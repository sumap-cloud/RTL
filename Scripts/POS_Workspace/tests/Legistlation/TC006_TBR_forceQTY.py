# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC006_TBR_forceQTY
# @Features: Transaction Based Return, Force Quantity, Return Reason Selection
# @Components: handle_force_quantity, search_transaction_and_enter_number, returns_item_selection, adjust_return_quantity, handle_refund_screen
# @Business_Rules: Force quantity validation, Return quantity limits, Return reason documentation
# @Validation_Points: Force quantity entry, Transaction lookup, Return item selection, Quantity adjustment, Refund processing
# @User_Roles: ATcash1
# @Special_Config: Force quantity items configuration
# @Related_Tests: TC007_department_return
# ==========================================

# ======================================================================
# Test Case: TC006_TBR_forceQTY.py
# Purpose: Validate the Transaction Based Return (TBR) functionality with force quantity items
# 
# Test Overview:
# This test case validates the POS system's handling of Transaction Based Returns
# specifically for items that require forced quantity entry:
#
# 1. Force Quantity Features:
#    - Manual quantity entry
#    - Quantity validation
#    - Price calculation
#    - Return processing
#
# 2. TBR Functionality:
#    - Original transaction lookup
#    - Item identification
#    - Return validation
#    - Refund processing
#
# 3. Transaction Management:
#    - Multiple item handling
#    - Price verification
#    - Refund calculation
#    - Receipt processing
#
# Flow Structure:
# Part 1 - Original Sale:
#   - Add force quantity items
#   - Process transaction
#   - Generate receipt
#
# Part 2 - Return Process:
#   - Initiate TBR
#   - Locate transaction
#   - Verify items
#   - Process return
#
# Part 3 - Completion:
#   - Calculate refund
#   - Process payment
#   - Generate documentation
#
# Key Validation Points:
# 1. Force Quantity:
#    - Proper quantity entry
#    - Price calculation
#    - Total verification
#
# 2. Return Processing:
#    - Transaction lookup
#    - Item matching
#    - Refund accuracy
#
# 3. Documentation:
#    - Receipt details
#    - Return documentation
#    - Audit trail
#
# Error Prevention:
# - Validate quantities
# - Verify calculations
# - Check documentation
# - Ensure proper approval
# ======================================================================
# 2. Complete the sale with cash payment
# 3. Perform transaction based return
# 4. Validate refund process and screens
# ======================================================================
"""
.......scenario..........
Login to POS
Select transaction based return under returns in toggle menu
Retrieve the transaction to return the items and select the Force quantity item to refund
Select any of the reasons and return the item
Validate the return reason ,Quantity & item price details in receipt,EJ,Tlog(reason codes)and also validate customer & operator dispaly

"""
from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
# Resolves the current file path and sets up proper import paths for components
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
    
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing necessary components for POS automation
from Components.Common_components.handle_chnage_screen import handle_chnagescreen_refunds

from Components.Common_components.pos_login import mainlogic
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Components.Salemode.Keyin_item import Kayin_EAN_POS

from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup

from Components.Common_components.handle_any_popup_POS import handle_Any_popup


from Components.Returns.search_transaction import search_transaction_and_enter_number
from Components.Salemode.forceqty import handle_force_quantity
from Components.Returns.returnssalemode import returns_item_selection

from Components.Returns.refund_tbr import handle_refund_screen

def tbr_forceqty():
    """
    Main test function for Transaction Based Return with Force Quantity
    
    Test Configuration:
    - Application: R10PosClient
    - Test Article: EAN 9313820000664 (Force Quantity enabled)
    - Initial Sale Quantity: 9
    - Return Quantity: 4
    - Return Reason: Double Scan
    
    Test Steps:
    1. Initial Sale Process
       - Login to POS
       - Add force quantity item
       - Complete sale with cash payment
    2. Return Process
       - Navigate to Returns -> Transaction Based
       - Search and select the transaction
       - Process return with reason code
       - Complete refund
    """
    application_window_title = ".*R10PosClient.*"
    return_article_name = None  # Not specified as we're using the last transaction
    target_quantity = 4        # Number of items to return
    reason = "Double Scan"     # Return reason code
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash1", "abcd1234")
        application_window_title = ".*R10PosClient.*"
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20) # Increased timeout
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False
    #9300624016601
    # --- Step 2: Add Force Quantity Article to Sale ---
    # Article EAN: 9313820000664 - This is a force quantity enabled article
    # The Kayin_EAN_POS function handles:
    # 1. Finding the EAN input field
    # 2. Entering the EAN code
    # 3. Validating the item is added to basket
    if not Kayin_EAN_POS(eans_to_add=["9313820000664"]):
        print("Failed to add items by EAN.")
        return False
        
    time.sleep(2)  # Wait for the UI to update after clicking PLU
    # --- Step 3: Handle Force Quantity Screen ---
    # Purpose: Enter the required quantity for the force quantity article
    # - Quantity to enter: 9
    # - The handle_force_quantity function:
    #   1. Locates the quantity input field
    #   2. Enters the specified quantity
    #   3. Validates the quantity is accepted
    if handle_force_quantity(win, quantity_to_enter="9"):
            print("\nForce quantity handled successfully.")
    else:
            print("\nFailed to handle force quantity screen.")
    #navigating to loyalty mode here after adding all expected item then user has to click ok button to move loyalty mode and below click_OK_button using for navigate sale mode to next screen loyalty mode 
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("Clicked OK button in age restriction window.")

    # handle loyalty prompty by clicking cancel button
    time.sleep(2)  # Wait for the UI to update after clicking OK
    if not handle_customer_popup(app, customer_number=None):
        print("Failed to handle customer number popup.")
        return False
    from Components.Tenders.Cash_tender_payment import process_tenders
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process cash tender payment.")
        return False
    # here we will get receipt supressed popup after payment done successfully
   
    if not handle_Any_popup():
        print("Failed to handle any popup.")
        return False
    time.sleep(3)
    from Components.Common_components.cashDrawer import cashdrawer_move_and_close
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("Failed to move and close the cash drawer.")
        return False
    

    
    print("\n--- All tasks completed successfully in paid out process! --- 🎉")
    # --- Step 7: Navigate to Transaction Based Returns ---
    # Purpose: Access the TBR functionality through menu navigation
    # Navigation Path: Returns -> Transaction Based -> APPROVAL
    # The toggle_menu_navigate function:
    # 1. Opens the toggle menu
    # 2. Navigates through the specified menu path
    # 3. Validates each menu selection
    time.sleep(5)  # Allow system to stabilize after previous operations
    Toggle_menu = toggle_menu_navigate(["Returns","Transaction Based", "APPROVAL"])
    if Toggle_menu:
         print("\nSuccessfully navigated to Transaction Based Returns.")
    else:
         print("\nFailed to navigate to Transaction Based Returns.")
    time.sleep(2) 
    # --- Step 3: Handle Transaction Return Screen ---
    from Components.Returns.tbr_load_transaction import handle_transaction_return_screen
    from Scripts.POS_Workspace.Components.Returns.search_typeselection import handle_search_type_selection

    if not handle_transaction_return_screen(action="click_search"):
        print("\nThe main script did not run properly.")
    time.sleep(2)

    if not handle_search_type_selection(action="click_pos_parameters"):
        print("\nThe script did not run properly.")    
    time.sleep(2)
    if not search_transaction_and_enter_number():
        print("\nThe main script did not run properly.")
    time.sleep(5)



    # --- Step 8: Select Items for Return ---
    # Purpose: Process the return of items with specific parameters
    # Parameters:
    # - article_to_return: None (uses the last transaction's item)
    # - quantity: 4 (partial return of the original 9 items)
    # - reason_code: "Double Scan"
    # 
    # The returns_item_selection function:
    # 1. Identifies the item to be returned
    # 2. Sets the return quantity
    # 3. Applies the return reason code
    # 4. Validates the return details
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
    result_switch = handle_refund_screen(expected_tender='Cash')
    if result_switch:
        print("\n✅ Test Case 1 completed successfully.")
    else:
        print("\n❌ Test Case 1 failed.")
    
    # --- Step 9: Process Final Refund Screen ---
    # Purpose: Capture and validate the final refund screen details
    # The handle_final_refund_screen function captures:
    # 1. Header information
    # 2. Title of the refund screen
    # 3. Tender details (refund amount and method)
    # 4. System messages and sub-messages
    # 5. Validates all required information is present
    time.sleep(2)
    captured_data = handle_chnagescreen_refunds()

    # Display and validate refund details
    if captured_data:
        print("\n================= Final Refund Summary =================")
        print(f"Header: {captured_data.get('header', 'N/A')}")
        print(f"Title: {captured_data.get('title', 'N/A')}")
        print(f"Tender Details: {captured_data.get('tender_details', 'N/A')}")
        print(f"Message: {captured_data.get('message', 'N/A')}")
        print(f"Sub-Message: {captured_data.get('sub_message', 'N/A')}")
        print("=======================================================")
        print("\n✅ Return process completed successfully.")
    else:
        print("\n❌ Standalone test failed.")
    #close cash drawer after refund done successfully
    time.sleep(3)
    from Components.Common_components.cashDrawer import cashdrawer_move_and_close
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("Failed to move and close the cash drawer.")
        return False
    

tbr_forceqty()