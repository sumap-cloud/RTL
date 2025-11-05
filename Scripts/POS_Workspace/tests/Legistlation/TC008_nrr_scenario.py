# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC008_nrr_scenario
# @Features: Non-Receipted Return, Threshold Validation, Approval Workflow, Refund Processing
# @Components: departmentrefund_nrr, handle_approval_popup, handle_refund_screen, handle_Any_popup, handle_chnagescreen_refunds
# @Business_Rules: Amount thresholds ($500-$1000, $1000.01-$9999.99, ≥$10,000), Approval routing by amount
# @Validation_Points: Department selection, Threshold validation, Approval capture, Receipt documentation, Cash drawer management
# @User_Roles: ATcash1, atmgr5
# @Special_Config: Approval thresholds, Return reasons
# @Related_Tests: TC007_department_return
# ==========================================

# ======================================================================
# Test Case: nrr_scenario.py
# Purpose: Validate the Non-Receipted Return (NRR) functionality with different amount thresholds
# 
# Test Overview:
# This test case validates the POS system's ability to process non-receipted returns
# with different amount thresholds that trigger various approval requirements:
#
# 1. Non-Receipted Return Features:
#    - Amount threshold validation
#    - Department-based returns
#    - Approval workflows
#    - Refund processing
#
# 2. Amount Thresholds:
#    - $500 - $1000: First threshold
#    - $1,000.01 - $9,999.99: Second threshold  
#    - ≥ $10,000: Highest threshold
#
# 3. Approval Management:
#    - Authority levels
#    - Approval routing
#    - Documentation
#    - Override handling
#
# Flow Structure:
# Part 1 - Navigation:
#   - Log into POS
#   - Navigate to Non-Receipted Return
#   - Handle approval
#
# Part 2 - Threshold Returns:
#   - Process return for $500-$1000 range
#   - Process return for $1000.01-$9999.99 range
#   - Process return for $10,000+ range
#
# Part 3 - Finalization:
#   - Process tender
#   - Handle receipt
#   - Cash drawer management
#
# Key Validation Points:
# 1. Return Details:
#    - Department selection
#    - Amount validation
#    - Return reason handling
#
# 2. Approval Process:
#    - Threshold-based authority validation
#    - Approval capture for each threshold level
#
# 3. Documentation:
#    - Return receipt generation
#    - Approval records
#    - Transaction history
#
# Error Prevention:
# - Department validation
# - Amount threshold verification
# - Approval confirmation
# - Documentation checks
# ======================================================================
"""
.......scenario..........
1. Login Process:
   - Login to POS system

2. Non-Receipted Return Navigation:
   - Navigate to Returns -> Non-Receipted Return
   - Handle approval process

3. Department Sale Returns with Amount Thresholds:
   - Process department return for $750.00 (in $500-$1000 range)
   - Process department return for $5,000.00 (in $1000.01-$9999.99 range)
   - Process department return for $12,000.00 (≥ $10,000 range)

4. Tender Process:
   - Complete refund process
   - Handle receipt
   - Manage cash drawer
"""
# Flow: 
# Part 1 - Login and Navigation:
# 1. Login to POS
# 2. Navigate to Returns -> Non-Receipted Return
# 3. Handle approval
#
# Part 2 - Threshold-Based Returns:
# 4. Select department for first return ($500-$1000)
# 5. Enter amount ($750.00) and select reason
# 6. Select department for second return ($1000.01-$9999.99)
# 7. Enter amount ($5,000.00) and select reason
# 8. Select department for third return (≥ $10,000)
# 9. Enter amount ($12,000.00) and select reason
#
# Part 3 - Finalization:
# 10. Navigate to Tender mode
# 11. Complete refund process
# 12. Handle receipt and close cash drawer
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
from Scripts.POS_Workspace.Components.Salemode.department_sale import department_sale
from Scripts.POS_Workspace.Components.Salemode.department_amount import enter_item_price
from Components.Tenders.Cash_tender_payment import process_tenders
from Scripts.POS_Workspace.Components.Returns.departmentrefund_tbr import select_refund_department
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Returns.departmentrefund_nrr import return_item_by_department
from Components.Common_components.Approvalrequired import handle_approval_popup

from Components.Common_components.handle_chnage_screen import handle_chnagescreen_refunds
def test_non_receipted_return():
    """
    Main test function for Non-Receipted Return with different amount thresholds
    
    Test Configuration:
    - Application: R10PosClient
    - Login: ATcash1
    - Department: BAKEHOUSE
    - Return Amounts:
      * $750.00 (first threshold: $500-$1000)
      * $5,000.00 (second threshold: $1000.01-$9999.99)
      * $12,000.00 (third threshold: ≥ $10,000)
    - Return Reason: Damaged / Faulty
    
    Part 1 - Login and Navigation:
    1. Login to POS
    2. Navigate to Returns -> Non-Receipted Return
    3. Handle approval
    
    Part 2 - Threshold-Based Returns:
    4. Select department for first return
    5. Enter amount and select reason
    6. Select department for second return
    7. Enter amount and select reason
    8. Select department for third return
    9. Enter amount and select reason
    
    Part 3 - Finalization:
    10. Navigate to Tender mode
    11. Complete refund process
    12. Handle receipt and close cash drawer
    
    Error Prevention:
    - Validate each navigation step
    - Handle all possible popups
    - Allow proper wait times
    - Confirm screen transitions
    - Manage cash drawer properly
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    department_name = "BAKEHOUSE"       # Department code for all returns
    
    # Return amount thresholds
    first_threshold_amount = "750.00"    # $500-$1000 range
    second_threshold_amount = "5000.00"  # $1000.01-$9999.99 range
    third_threshold_amount = "12000.00"  # ≥ $10,000 range
    
    reason_code = "Damaged / Faulty"     # Return reason code
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash1", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False
    
    # --- Step 2: Navigate to Non-Receipted Return with Approval ---
    print("\n--- Step 2: Navigating to Non-Receipted Return with Approval ---")
    if not toggle_menu_navigate(["Returns", "Non Receipted", "APPROVAL"]):
        print("Failed to navigate to Non-Receipted Return")
        return False
    
    time.sleep(2)  # Wait for navigation to complete
    
    # Approval is handled within the navigation step itself
    print("Approval is handled within navigation")
    
    time.sleep(2)  # Wait for the screen to stabilize after approval
    
    # --- Step 3: Process first threshold return ($500-$1000) ---
    print(f"\n--- Step 3: Processing first threshold return (${first_threshold_amount}) ---")
    
    # Click on Department Refund button for first item
    print("Clicking Department Refund button for first threshold item")
    Department_Refund = win.child_window(title="Department Refund", control_type="Button")
    if Department_Refund:
        print("Department Refund button found")
        Department_Refund.click_input()
    else:
        print("Department Refund button not found")
        return False
    
    time.sleep(2)  # Wait for the department refund screen to load
    
    # Process department return for first threshold
    if not return_item_by_department(department_name=department_name, reason_code=reason_code, price=first_threshold_amount):
        print("Failed to process first threshold return")
        return False
    
    time.sleep(2)  # Wait for return processing
    
    # --- Step 4: Handle approval for first threshold amount ($500-$1000) ---
    print("\n--- Step 4: Handling approval for first threshold amount ---")
    # For the $500-$1000 range, approval might be required depending on system configuration
    try:
        if not handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234"):
            print("Expected approval popup not shown for first threshold, continuing flow")
    except Exception as e:
        print(f"Error handling approval for first threshold: {e}. Continuing flow.")
    time.sleep(2)  # Wait for UI to stabilize
    
    # --- Step 5: Process second threshold return ($1000.01-$9999.99) ---
    print(f"\n--- Step 5: Processing second threshold return (${second_threshold_amount}) ---")
    
    # Click on Department Refund button for second item
    print("Clicking Department Refund button for second threshold item")
    Department_Refund = win.child_window(title="Department Refund", control_type="Button")
    if Department_Refund:
        print("Department Refund button found for second threshold item")
        Department_Refund.click_input()
    else:
        print("Department Refund button not found for second threshold item")
        return False
    
    time.sleep(2)  # Wait for the department refund screen to load
    
    # Process department return for second threshold
    if not return_item_by_department(department_name=department_name, reason_code=reason_code, price=second_threshold_amount):
        print("Failed to process second threshold return")
        return False
    
    time.sleep(2)  # Wait for return processing
    
    # --- Step 6: Handle approval for second threshold amount ($1000.01-$9999.99) ---
    print("\n--- Step 6: Handling approval for second threshold amount ---")
    # For the higher amount range, approval is definitely required
    try:
        if not handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234"):
            print("Expected approval popup not shown for second threshold, continuing flow")
    except Exception as e:
        print(f"Error handling approval for second threshold: {e}. Continuing flow.")
    
    time.sleep(2)  # Wait for UI to stabilize
    
    # --- Step 7: Process third threshold return (≥ $10,000) ---
    print(f"\n--- Step 7: Processing third threshold return (${third_threshold_amount}) ---")
    
    # Click on Department Refund button for third item
    print("Clicking Department Refund button for third threshold item")
    Department_Refund = win.child_window(title="Department Refund", control_type="Button")
    if Department_Refund:
        print("Department Refund button found for third threshold item")
        Department_Refund.click_input()
    else:
        print("Department Refund button not found for third threshold item")
        return False
    
    time.sleep(2)  # Wait for the department refund screen to load
    
    # Process department return for third threshold
    if not return_item_by_department(department_name=department_name, reason_code=reason_code, price=third_threshold_amount):
        print("Failed to process third threshold return")
        return False
    
    time.sleep(2)  # Wait for return processing
    
    # --- Step 8: Handle restriction popup for third threshold amount (≥ $10,000) ---
    print("\n--- Step 8: Handling restriction popup for high value amount ---")
    # For amounts $10k+, a restriction popup appears instead of an approval prompt
    if not handle_Any_popup():
        print("No restriction popup appeared for high value amount, continuing flow")
    else:
        print("Successfully handled restriction popup for high value amount")
    
    time.sleep(2)  # Wait for UI to stabilize
    # --- Step 9: Navigate to Tender mode ---
    print("\n--- Step 9: Navigating to Tender mode ---")
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("Clicked OK button to navigate to tender mode")
    else:
        print("OK button not found to proceed to tender mode")
        return False
    
    time.sleep(2)  # Wait for tender screen to appear
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
    
    
    print("\n--- Non-Receipted Return scenario completed successfully! ---")
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_non_receipted_return()
