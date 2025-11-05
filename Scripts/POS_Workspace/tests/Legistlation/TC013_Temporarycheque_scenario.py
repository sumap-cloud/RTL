# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC004_complete_sale_cheque_scenario
# @Features: POS Login, Manual Item Addition, Loyalty Skip, Temporary Cheque Tender
# @Components: pos_login, Kayin_EAN_POS, handle_customer_popup, TemporaryChequeWorkflowHandler
# @Business_Rules: Sale completion via temporary cheque, Loyalty handling, Cheque validation
# @Validation_Points: Login success, Item addition, Loyalty skip, Cheque tender completion
# @User_Roles: ATcash5
# @Special_Config: Temporary cheque tender configuration
# @Related_Tests: None
# ==========================================

# ======================================================================
# Test Case: TC004_complete_sale_cheque_scenario.py
# Purpose: Validate Complete Sale Process using Temporary Cheque Payment
# 
# Test Overview:
# This test case validates the complete sale flow with temporary cheque:
# 1. Authentication Features:
#    - POS login validation
#    - Sale mode access verification
#
# 2. Item Management:
#    - Manual item addition
#    - Basket verification
#    - Price validation
#
# 3. Loyalty Processing:
#    - Loyalty prompt handling
#    - Skip functionality verification
#
# 4. Temporary Cheque Features:
#    - Cheque details entry
#    - Template selection
#    - Endorsement handling
#
# Key Validation Points:
# 1. POS Access:
#    - Login credentials
#    - Mode transitions
#    - UI navigation
#
# 2. Sale Processing:
#    - Item addition accuracy
#    - Basket management
#    - Total calculation
#
# 3. Payment Handling:
#    - Cheque details validation
#    - Endorsement completion
#    - Receipt generation
#
# Flow Structure:
# Part 1 - Initial Setup:
#   - Login to POS
#   - Access sale mode
#   - Verify system readiness
#
# Part 2 - Sale Process:
#   - Add items manually
#   - Verify basket contents
#   - Handle loyalty skip
#
# Part 3 - Payment Process:
#   - Enter cheque details
#   - Handle endorsements
#   - Complete transaction
#
# Error Prevention:
# - Validate login status
# - Verify item additions
# - Check cheque details
# - Confirm endorsements
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

from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Salemode.basket_with_itemdetails import get_basket_info

from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup

from Components.Tenders.Temporary_Cheque_Complete_Workflow import TemporaryChequeWorkflowHandler


def test_complete_sale_cheque():
    """
    Main test function for Complete Sale with Temporary Cheque
    
    Test Configuration:
    - Application: R10PosClient
    - Login: ATcash5 (Service Cashier)
    - Item Addition: Manual Key-in
    - Payment: Temporary Cheque
    
    Test Flow:
    1. Initial Setup:
       - Login to POS
       - Verify application access
       - Check sale mode
    
    2. Sale Process:
       - Add item manually
       - Verify basket contents
       - Handle loyalty skip
    
    3. Payment Process:
       - Process temporary cheque
       - Handle endorsements
       - Complete transaction
    
    Validation Points:
    - Login success verification
    - Item addition confirmation
    - Basket details accuracy
    - Cheque details validation
    - Transaction completion
    
    Error Prevention:
    - Verify each step completion
    - Validate data entry
    - Check transaction status
    - Confirm receipt generation
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    cheque_details = {
        "Account Name": "Test Account",
        "BSB Number": "123456",
        "Account Number": "987654321",
        "Cheque Number": "101111",
        "Bank Name": "Test Bank",
        "Bank Location": "Test Branch"
    }
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash5", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("✓ Successfully logged into POS")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

    # --- Step 2: Add Item via Key normal article without any prompt (9300675079686 this article price is 11.99) ---
    print("\n--- Step 2: Adding item through manual key entry ---")
    if not Kayin_EAN_POS(eans_to_add=["9300675079686"]):
        print("❌ Failed to add item via key")
        return False
    print("✓ Item added successfully")

    # --- Step 3: Verify Basket after adding all items ---
    print("\n--- Step 3: Verifying basket contents ---")
    if not get_basket_info():
        print("❌ Failed to verify basket")
        return False
    print("✓ Basket verified")

    # --- Step 4: Navigate to Loyalty  by clicking ok button ---
    print("\n--- Step 4: Transitioning to loyalty mode ---")
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("✓ Navigated to loyalty mode")
    else:
        print("❌ Failed to navigate to loyalty mode")
        return False

    time.sleep(2)  # Wait for UI update

    # --- Step 5: Skip Loyalty because no customer number is provided ---
    print("\n--- Step 5: Handling loyalty prompt ---")
    if not handle_customer_popup(app, customer_number=None):
        print("❌ Failed to handle loyalty popup")
        return False
    print("✓ Loyalty skipped")

    # --- Step 6: Process Temporary Cheque Payment ---
    print("\n--- Step 6: Processing temporary cheque payment ---")
    workflow_handler = TemporaryChequeWorkflowHandler()
    if not workflow_handler.complete_temporary_cheque_workflow(
        amount="11.99",
        cheque_details=cheque_details,
        template_name="Small - 160 X 70"
    ):
        print("❌ Failed to process temporary cheque payment")
        return False
    print("✓ Temporary cheque payment processed")

    # --- Step 7: Handle Receipt Popup ---
    print("\n--- Step 7: Handling receipt generation ---")
    if not handle_Any_popup():
        print("❌ Failed to handle receipt popup")
        return False
    print("✓ Receipt handled")

    # --- Step 8: Handle Cash Drawer ---
    print("\n--- Step 8: Managing cash drawer ---")
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to close cash drawer")
        return False
    print("✓ Cash drawer closed")

    print("\n✨ Test completed successfully!")
    return True


# --- Execute the test ---
if __name__ == "__main__":
    test_complete_sale_cheque()
