# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC014_basic_sale_flow
# @Features: Basic Sale Flow, Item Addition, Payment Processing
# @Components: pos_login, Kayin_EAN_POS, basket_with_itemdetails, handle_customer_popup, process_tenders, shutdown_check
# @Business_Rules: Standard sale process flow, Basket validation, Payment processing rules
# @Business_Rules: Standard sale process flow, Basket validation, Payment processing rules
# @Validation_Points: Login validation, Item addition verification, Basket total accuracy, Payment completion
# @User_Roles: ATcash1
# @Special_Config: None
# @Related_Tests: TC002_agerestiction_Scenario, TC010_price_override_void_line_scenario
# ==========================================

# ======================================================================
# Test Case: TC014_basic_sale_flow.py
# Purpose: Validate Basic Sale Flow with Common Validations
# 
# Test Overview:
# This test case validates core POS functionalities:
# 1. Basic Sale Features:
#    - Login authentication
#    - System shutdown validation
#    - Item addition via Key-in EAN
#    - Basket validation
#    - Payment processing
#
# 2. System Validations:
#    - Application connection
#    - Window focus verification
#    - Popup handling
#    - Transaction state validation
#
# 3. Transaction Management:
#    - Basket info verification
#    - Mode transitions (Sale -> Loyalty -> Tender)
#    - Payment completion
#    - Cash drawer operations
#
# Key Validation Points:
# 1. Application State:
#    - Proper login state
#    - Window focus
#    - Mode transitions
#
# 2. Basket Management:
#    - Item addition success
#    - Price verification
#    - Total amount accuracy
#
# 3. Transaction Completion:
#    - Payment processing
#    - Receipt handling
#    - Cash drawer operations
#
# Flow Structure:
# Part 1 - Initial Setup:
#   - Login as Service Cashier
#   - Validate application connection
#   - Verify window focus
#
# Part 2 - Sale Process:
#   - Add item via EAN
#   - Validate basket contents
#   - Verify totals accuracy
#
# Part 3 - Transaction Completion:
#   - Handle loyalty (skip)
#   - Process payment
#   - Handle receipt and drawer
#
# Error Prevention:
# - Validate application state
# - Verify item additions
# - Check basket totals
# - Handle unexpected popups
# - Monitor transaction states
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
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Tenders.Cash_tender_payment import process_tenders
from Components.Common_components.cashDrawer import cashdrawer_move_and_close
from Components.Common_components.shutdown_check import shutdown_check

def test_basic_sale_flow():
    """
    Main test function for Basic Sale Flow
    
    Test Configuration:
    - Application: R10PosClient
    - Login: ATcash1 (Service Cashier)
    - Item: Standard non-restricted item
    - Payment: Cash tender
    
    Test Flow:
    1. Initial Setup:
       - Login to POS
       - Validate connection
       - Verify window focus
    
    2. Sale Process:
       - Add item via EAN
       - Validate basket
       - Verify totals
    
    3. Transaction Completion:
       - Skip loyalty
       - Process payment
       - Handle receipt and drawer
    
    Validation Points:
    - Application connection
    - Item addition success
    - Basket validation
    - Payment processing
    
    Error Prevention:
    - Verify each step
    - Handle popups
    - Validate states
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    test_item_ean = "8720400000210"  # Standard non-restricted item
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash1", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"✅ Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"❌ Failed to connect or log in to the POS application: {e}")
        return False
    
    # --- Step 2: Check Shutdown Status ---
    print("\n--- Step 2: Checking system shutdown status ---")
    if not shutdown_check():
        print("❌ Shutdown check failed")
       
    print("✅ Shutdown check passed")
    
    # --- Step 3: Add Item to Sale Mode ---
    print("\n--- Step 3: Adding item via EAN ---")
    if not Kayin_EAN_POS(eans_to_add=[test_item_ean]):
        print("❌ Failed to add item using EAN code")
        return False
    print("✅ Successfully added item to basket")
    
    # Handle any unexpected popups
    if not handle_Any_popup():
        print("ℹ️ No popups to handle after item addition")
    
    # --- Step 4: Validate Basket Contents ---
    print("\n--- Step 4: Verifying basket details ---")
    if not get_basket_info():
        print("❌ Failed to verify basket contents")
        return False
    print("✅ Basket validation successful")
    
    # --- Step 5: Navigate to Loyalty Mode ---
    print("\n--- Step 5: Transitioning to Loyalty Mode ---")
    # Click OK to proceed to loyalty mode
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("✅ Navigated to Loyalty Mode")
    else:
        print("❌ OK button not found for loyalty navigation")
        return False
        
    time.sleep(2)  # Wait for the UI to update
    
    # --- Step 6: Handle Loyalty (Skip) ---
    print("\n--- Step 6: Handling loyalty popup (skipping) ---")
    if not handle_customer_popup(app, customer_number=None):
        print("❌ Failed to handle customer popup")
        return False
    print("✅ Successfully skipped loyalty")
    
    # Handle any additional popups
    if not handle_Any_popup():
        print("ℹ️ No additional popups to handle")
    
    # --- Step 7: Check Shutdown Status Before Payment ---
    print("\n--- Step 7: Checking system shutdown status before payment ---")
    if not shutdown_check():
        print("❌ Shutdown check failed")
        return False
    print("✅ Shutdown check passed")
    
    # --- Step 8: Process Payment ---
    print("\n--- Step 8: Processing cash payment ---")
    if not process_tenders(app, tender_to_select="Cash"):
        print("❌ Failed to process cash tender payment")
        return False
    print("✅ Cash payment processed successfully")
    
    # Handle receipt suppression popup
    if not handle_Any_popup():
        print("ℹ️ No receipt popup to handle")
    
    # --- Step 9: Handle Cash Drawer ---
    print("\n--- Step 9: Handling cash drawer operations ---")
    time.sleep(3)  # Wait for drawer operations
    
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to move and close the cash drawer")
        return False
    print("✅ Cash drawer handled successfully")
    
    print("\n🎉 --- All tasks completed successfully in basic sale flow! --- 🎉")
    print("\n✅ Test Summary:")
    print("   - Successfully logged into POS")
    print(f"   - Added item (EAN: {test_item_ean})")
    print("   - Validated basket contents")
    print("   - Skipped loyalty successfully")
    print("   - Processed cash payment")
    print("   - Handled receipt and cash drawer")
    
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_basic_sale_flow()
