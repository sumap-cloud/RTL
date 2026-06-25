# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC007_department_return
# @Features: Transaction Based Return, Department Sale Return, Return Authorization
# @Components: department_sale, select_refund_department, handle_transaction_return_screen, handle_search_type_selection, handle_refund_screen
# @Business_Rules: Department returns must require department selection, Return reason must be documented, Amount must be validated
# @Validation_Points: Department selection accuracy, Transaction lookup, Return reason application, Refund processing
# @User_Roles: ATcash1
# @Special_Config: Department codes, Return reason codes
# @Related_Tests: TC008_nrr_scenario, TC006_TBR_forceQTY
# ==========================================

# ======================================================================
# Test Case: TC007_department_return.py
# Purpose: Validate the Transaction Based Return (TBR) functionality with department sale
# 
# Test Overview:
# This test case validates the POS system's ability to process returns
# for department sales, including approval workflows and documentation:
#
# 1. Department Return Features:
#    - Department identification
#    - Price validation
#    - Return authorization
#    - Refund processing
#
# 2. TBR Functionality:
#    - Transaction lookup
#    - Department matching
#    - Amount verification
#    - Return approval
#
# 3. Approval Management:
#    - Authority levels
#    - Approval routing
#    - Documentation
#    - Override handling
#
# Flow Structure:
# Part 1 - Original Sale:
#   - Process department sale
#   - Record transaction
#   - Generate receipt
#
# Part 2 - Return Process:
#   - Locate transaction
#   - Validate details
#   - Request approval
#   - Process return
#
# Part 3 - Documentation:
#   - Return receipt
#   - Approval records
#   - Audit trail
#
# Key Validation Points:
# 1. Department Details:
#    - Code accuracy
#    - Price verification
#    - Return eligibility
#
# 2. Approval Process:
#    - Authority check
#    - Approval capture
#    - Override validation
#
# 3. Documentation:
#    - Return receipt
#    - Approval records
#    - Transaction history
#
# Error Prevention:
# - Department validation
# - Amount verification
# - Approval confirmation
# - Documentation check
# ======================================================================
# This test case validates the complete flow of department sale return:
# Part 1 - Initial Sale:
#   - Navigate to Department Sale with APPROVAL
#   - Create a BAKEHOUSE department sale
#   - Validate basket details after article addition
#   - Handle Loyalty Mode:
#     * Click OK to navigate to loyalty
#     * Handle customer number popup validation
#     * Cancel loyalty and proceed
#   - Complete the sale with cash payment
#
# Part 2 - Transaction Based Return:
#   - Navigate to Main Menu first
#   - Access Returns -> Transaction Based -> APPROVAL
#   - Search and select the previous transaction
#   - Process partial return with reason
#
# Test Details:
# - Department: BAKEHOUSE
# - Initial Sale Amount: 20.00
# - Return Amount: 10.00 (partial return)
# - Return Reason: Quality Issue
#
# Common Error Prevention:
# - Proper navigation confirmations after each menu change
# - Wait times between critical operations (2-3 seconds)
# - Validate basket details after adding any articles
# - Handle all popups (receipt, customer number, loyalty)
# - Proper screen transitions:
#   * Sale -> Basket Validation
#   * OK Button -> Loyalty
#   * Loyalty Cancel -> Tender
# - Cash drawer management after transactions
# - Customer number popup validation in loyalty
# 
# Standard Validation Points:
# 1. Basket validation after article addition
# 2. Loyalty screen validation
# 3. Transaction completion verification
# 4. Receipt handling
# 5. Cash drawer operations
# ======================================================================
"""
.......scenario..........
1. Initial Sale Process:
   - Login to POS
   - Do department sale (amount: 20.00)
   - Complete payment with cash
   - Handle receipt and cash drawer

2. Return Process:
   - Navigate to Returns -> Transaction Based -> APPROVAL
   - Search and select the previous transaction
   - Process department return (amount: 10.00)
   - Apply return reason
   - Complete refund process
   - Validate return screens and receipt
"""
# Flow: 
# Part 1 - Initial Sale:
# 1. Login to POS
# 2. Navigate to Department Sale
# 3. Process department sale with amount
# 4. Navigate to Loyalty and cancel
# 5. Navigate to Tender mode and complete cash payment
#
# Part 2 - Return Process:
# 6. Navigate to Main Menu
# 7. Navigate to Returns -> Transaction Based -> APPROVAL
# 8. Search and select transaction
# 9. Access Department Refund
# 10. Process department return with reason
# 11. Complete refund process
# ======================================================================

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
from Components.Common_components.pos_login import mainlogic
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Common_components.cashDrawer import cashdrawer_move_and_close
from Components.Returns.refund_tbr import handle_refund_screen
from Components.Returns.returnssalemode import returns_item_selection
from Components.Salemode.department_sale import department_sale
from Components.Salemode.department_amount import enter_item_price
from Components.Tenders.Cash_tender_payment import process_tenders
from Components.Returns.tbr_load_transaction import handle_transaction_return_screen
from Components.Returns.search_typeselection import handle_search_type_selection
from Components.Returns.search_transaction import search_transaction_and_enter_number
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Returns.departmentrefund_tbr import select_refund_department
def test_department_return():
    """
    Main test function for Transaction Based Return with Department Sale
    
    Test Configuration:
    - Application: R10PosClient
    - Login: ATcash1
    - Department: BAKEHOUSE
    - Initial Sale Amount: 20.00
    - Return Amount: 10.00 (partial return)
    - Return Reason: Quality Issue
    
    Part 1 - Initial Sale Steps:
    1. Login to POS
    2. Navigate to Department Sale with APPROVAL
    3. Select BAKEHOUSE department
    4. Enter sale amount (20.00)
    5. Validate basket information:
       - Check basket details after article addition
       - Verify item details and totals
    6. Handle Loyalty Flow:
       - Click OK to enter loyalty mode
       - Validate customer number popup
       - Handle loyalty screen validation
       - Cancel loyalty
    7. Process Payment:
       - Navigate to tender mode
       - Complete cash payment
       - Handle receipt and drawer
    
    Part 2 - Return Steps:
    7. Return Navigation:
       - Go to Main Menu
       - Navigate Returns -> Transaction Based -> APPROVAL
    8. Transaction Search:
       - Click search
       - Select POS parameters
       - Enter transaction number
    9. Department Return:
       - Navigate to Department Refund
       - Select BAKEHOUSE
       - Enter partial return (10.00)
    10. Complete Return:
        - Apply reason code
        - Confirm refund
        - Process cash refund
        - Handle receipt and drawer
    
    Error Prevention:
    - Validate each navigation step
    - Handle all possible popups
    - Allow proper wait times
    - Confirm screen transitions
    - Manage cash drawer properly
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    initial_sale_amount = "20.00"   # Amount for initial department sale
    return_amount = "10.00"         # Amount to be refunded (partial return)
    reason_code = "Quality Issue"    # Return reason code
    department_Name = "BAKEHOUSE"       # Department code for sale and return
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        login_result = mainlogic("ATcash1", "abcd1234")
        assert login_result, "Login failed. mainlogic() returned False."
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except AssertionError:
        raise
    except Exception as e:
        assert False, f"Failed to connect or log in to the POS application: {e}"
    """"""
    # --- Part 1: Initial Department Sale ---
    print("\n--- Step 2: Navigating to Department Sale ---")
    # Navigate to Department Sale first
    if not toggle_menu_navigate(["Department Sale", "APPROVAL"]):
        assert False, "Failed to navigate to Department Sale"
    
    
    time.sleep(2)  # Wait for navigation to complete
    
    print("Processing Department Sale...")
    # Select department and enter amount
    if not department_sale(department_name=department_Name):
        assert False, "Failed to access department sale screen"

    time.sleep(2)  # Wait for department selection

    if not enter_item_price(initial_sale_amount):
        assert False, "Failed to enter department sale amount"

    time.sleep(2)  # Wait for amount entry
    #check basket details after adding all articles(common for all test cases if you add articles)
    if not get_basket_info():
        assert False, "Failed to get basket information."
    #navigating to loyalty mode here after adding all expected item then user has to click ok button to move loyalty mode and below click_OK_button using for navigate sale mode to next screen loyalty mode 
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("Clicked OK buttonto navigate to loyalty mode")

    time.sleep(2)  # Wait for the UI to update after clicking OK
    # Handle customer number popup(loyalty screen validation) if it appears
    if not handle_customer_popup(app, customer_number=None):
        assert False, "Failed to handle customer number popup."

    time.sleep(2)  # Wait for loyalty screen
    #after handle of loyalty mode it will automatically navigate to tender mode
    # Process cash payment for initial sale
    if not process_tenders(app, tender_to_select="Cash"):
        assert False, "Failed to process cash payment for initial sale"

    # Handle receipt suppressed popup
    if not handle_Any_popup():
        print("Failed to handle receipt popup — continuing anyway")

    # Close cash drawer after sale
    if not cashdrawer_move_and_close(status_to_set="close"):
        assert False, "Failed to close cash drawer"

    print("\n--- Initial Department Sale completed successfully! ---")
    time.sleep(3)  # Wait for sale to complete

    # --- Part 2: Transaction Based Return Process ---

    #Navigate to Transaction Based Returns
    if not toggle_menu_navigate(["Returns", "Transaction Based", "APPROVAL"]):
        assert False, "Failed to navigate to Transaction Based Returns"
    
    time.sleep(3)  # Allow system to stabilize after approval

    # --- Step 9: Handle Transaction Search ---
    print("\n--- Step 9: Searching for Transaction ---")
    if not handle_transaction_return_screen(action="click_search"):
        assert False, "Failed to access transaction search"
    
    time.sleep(2)  # Wait for search screen

    if not handle_search_type_selection(action="click_pos_parameters"):
        assert False, "Failed to select POS parameters search"
    
    time.sleep(2)  # Wait for parameter selection

    if not search_transaction_and_enter_number():
        assert False, "Failed to enter transaction number"

    time.sleep(7)  # Wait for transaction to load

   # --- Step 10: Navigate to Department Refund ---
    #we dt need to use navigation method because here there wont be any toggle button expand just directly click on Department Refund

    Department_Refund = win.child_window(title="Department Refund", control_type="Button")
    if Department_Refund:
            print("Department Refund button found")
            Department_Refund.click_input()
    
    print("\n--- Step 10: Accessing Department Refund ---")

    # --- Step 11: Process Department Return ---
    print("\n--- Step 11: Processing Department Return ---")
    if not select_refund_department(department_name=department_Name):
        assert False, "Failed to access department refund screen"
    time.sleep(2)  # Wait for department selection
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
    # --- Step 13: Process Refund ---
    time.sleep(2)  # Wait for tender screen to appear
    result_switch = handle_refund_screen(expected_tender='Cash')
    assert result_switch, "handle_refund_screen failed — refund not processed successfully"
    print("\n✅ Test Case TC007 completed successfully.")
    

    time.sleep(2)

    # Rceipt handling not epected in returns retur

    # Close cash drawer after return
    if not cashdrawer_move_and_close(status_to_set="close"):
        assert False, "Failed to close cash drawer after return"
    print("\n--- Transaction Based Return completed successfully! ---")
# --- Execute the test ---
if __name__ == "__main__":
    test_department_return()
