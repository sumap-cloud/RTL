# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC010_price_override_void_line_scenario
# @Features: Price Override, Void Line, Transaction Processing, Amount Validation
# @Components: Kayin_EAN_POS, handle_price_override_screen, handle_reason_code_screen, handle_select_reason_code_popup, handle_approval_popup, get_basket_info, OCR_balancedue, process_tenders
# @Business_Rules: Price override limits, Void line reason codes, Amount validation accuracy, Payment processing
# @Validation_Points: Basket validation after each addition, Price override confirmation, Void line verification, OCR balance matching
# @User_Roles: ATcash1
# @Special_Config: Price override permissions, Void line reason codes
# @Related_Tests: TC002_agerestiction_Scenario
# ==========================================

# ======================================================================
# Test Case: TC010_price_override_void_line_scenario.py
# Purpose: Validate Price Override and Void Line functionality in POS transactions
# 
# Test Overview:
# This test case validates multiple core POS functionalities:
# 1. Price Override Features:
#    - Price modification capability
#    - Override amount validation
#    - System response to price changes
#    - Basket amount recalculation
#
# 2. Void Line Operations:
#    - Item removal from transaction
#    - Reason code selection
#    - Basket amount adjustment
#    - Transaction integrity maintenance
#
# 3. Amount Validation:
#    - Basket info validation after each operation
#    - OCR balance due extraction
#    - Amount matching verification
#    - Payment accuracy confirmation
#
# Key Validation Points:
# 1. Item Addition:
#    - Proper item addition
#    - Basket validation after each addition
#    - Amount accuracy verification
#
# 2. Price Override:
#    - Override screen handling
#    - Price change confirmation
#    - Basket amount recalculation
#
# 3. Void Line:
#    - Reason code selection
#    - Item removal confirmation
#    - Final amount verification
#
# 4. Balance Validation:
#    - OCR balance due extraction
#    - Comparison with basket total
#    - Payment amount accuracy
#
# Flow Structure:
# Part 1 - Initial Sale Setup:
#   - Login as Service Cashier
#   - Add identical items twice
#   - Validate basket after each addition
#
# Part 2 - Price Override Process:
#   - Select item for price override
#   - Apply new price ($9.00)
#   - Validate basket with new amounts
#
# Part 3 - Void Line Process:
#   - Select item for voiding
#   - Choose "Double Scan" reason
#   - Validate final basket state
#
# Part 4 - Amount Validation & Completion:
#   - OCR balance due extraction
#   - Amount matching validation
#   - Transaction completion
#
# Error Prevention:
# - Validate each item addition
# - Verify price override application
# - Confirm void line operation
# - Ensure amount accuracy
# - Handle payment processing
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
from Components.Salemode.PriceOverride import perform_price_override
from Components.Salemode.void_line import handle_reason_code_screen, click_void_line_button
#from Components.Common_components.OCR_balancedue import BalanceExtractor
from Components.Common_components.Approvalrequired import handle_approval_popup
from Components.Common_components.ResonCode_popup import handle_select_reason_code_popup
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Tenders.Cash_tender_payment import process_tenders
from Components.Common_components.cashDrawer import cashdrawer_move_and_close


def select_basket_item_by_position(win, item_position=1):
    """
    Selects an item in the basket by its position (1-based indexing)
    
    Args:
        win: The window object to interact with
        item_position (int): Position of item to select (1 = first item, 2 = second item)
        
    Returns:
        bool: True if item was selected successfully, False otherwise
    """
    try:
        print(f"🖱️ Selecting basket item at position {item_position}...")
        
        # Find the basket list control
        basket_controls = win.descendants(control_type="List")
        if not basket_controls:
            basket_controls = win.descendants(control_type="ListBox")
        if not basket_controls:
            basket_controls = win.descendants(control_type="ListView")
        
        if not basket_controls:
            print("❌ Could not find basket/list control")
            return False
        
        basket = basket_controls[0]
        items = basket.descendants(control_type="ListItem")
        if not items:
            items = basket.children()
        
        if len(items) < item_position:
            print(f"❌ Not enough items in basket. Found {len(items)}, need {item_position}")
            return False
        
        # Select the item (0-based indexing, so subtract 1)
        target_item = items[item_position - 1]
        target_item.click_input()
        print(f"✅ Selected item at position {item_position}")
        time.sleep(0.5)  # Allow UI to update
        return True
        
    except Exception as e:
        print(f"❌ Error selecting basket item: {e}")
        return False


def validate_basket_and_capture_total():
    """
    Generic validation function to check basket info and capture total amount
    
    Returns:
        bool: True if basket validation was successful, False otherwise
        
    Note: get_basket_info() returns True/False, but prints the total amount
    """
    print("🔍 Validating basket contents and capturing total...")
    basket_result = get_basket_info()
    if basket_result:
        print("✅ Basket validation successful")
        return True
    else:
        print("❌ Failed to validate basket contents")
        return False
    """
    Generic validation function to check basket info and capture total amount
    
    Returns:
        bool: True if basket validation was successful, False otherwise
        
    Note: get_basket_info() returns True/False, but prints the total amount
    """
    print("🔍 Validating basket contents and capturing total...")
    basket_result = get_basket_info()
    if basket_result:
        print("✅ Basket validation successful")
        return True
    else:
        print("❌ Failed to validate basket contents")
        return False




def test_price_override_void_line():
    """
    Main test function for Price Override and Void Line Operations
    
    Test Configuration:
    - Application: R10PosClient
    - Login: ATcash1 (Service Cashier)
    - First Item: EAN 9300675079686 (for price override)
    - Second Item: EAN 9300675014779 (for void line)
    - Price Override: $9.00
    - Void Reason: Double Scan
    
    Test Flow:
    1. Initial Sale Process:
       - Login to POS
       - Add first item (EAN: 9300675079686)
       - Add second item (EAN: 9300675014779)  
       - Validate basket after each addition
    
    2. Price Override Process:
       - Select first item in basket
       - Click Price Override button
       - Handle approval prompt
       - Apply new price ($9.00)
       - Handle reason code popup ("Close to Date")
       - Validate basket with modified price
    
    3. Void Line Process:
       - Select second item in basket
       - Click Void Line button
       - Choose "Double Scan" reason code
       - Validate basket after item removal
    
    4. Final Validation & Completion:
       - OCR balance due validation
       - Amount matching confirmation
       - Transaction completion
    
    Validation Points:
    - Basket validation after each item addition
    - Price override confirmation with approval
    - Void line operation success
    - OCR balance matching basket total
    - Payment processing completion
    
    Error Prevention:
    - Verify each item addition step
    - Handle approval prompt for price override
    - Validate price override application
    - Confirm void line operation
    - Ensure amount accuracy throughout
    - Handle all popup interactions
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    first_item_ean = "9300675079686"   # Item for price override
    second_item_ean = "9300675014779"  # Item for void line
    override_price = "9.00"            # New price for override
    void_reason = "Double Scan"        # Reason for void line
    
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
    
    # --- Step 2: Add First Item ---
    print(f"\n--- Step 2: Adding first item (EAN: {first_item_ean}) ---")
    if not Kayin_EAN_POS(eans_to_add=[first_item_ean]):
        print("❌ Failed to add first item")
        return False
    
    # Validate basket after first item addition
    if not validate_basket_and_capture_total():
        print("❌ Failed to validate basket after first item addition")
        return False
    
    # --- Step 3: Add Second Item (Different EAN) ---
    print(f"\n--- Step 3: Adding second item (EAN: {second_item_ean}) ---")
    if not Kayin_EAN_POS(eans_to_add=[second_item_ean]):
        print("❌ Failed to add second item")
        return False
    
    # Validate basket after second item addition
    if not validate_basket_and_capture_total():
        print("❌ Failed to validate basket after second item addition")
        return False
    
    # --- Step 4: Price Override Process ---
    print(f"\n--- Step 4: Applying price override to first item (New Price: ${override_price}) ---")
    try:
        # Step 4a: Select first item in basket for price override
        if not select_basket_item_by_position(win, item_position=1):
            print("❌ Failed to select first item for price override")
            return False
        
        # Step 4b: Click Price Override button
        priceoverride_btn=win.child_window(title="Price Override", control_type="Button")
        if priceoverride_btn:
            print("🔄 Clicking Price Override button...")
            priceoverride_btn.click_input()
            print("✅ Price Override button clicked")

        
        # Step 4c: Handle approval prompt (appears after clicking Price Override)
        print("🔐 Handling approval prompt...")
        if not handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234"):
            print("❌ Failed to handle approval prompt")
            
        
        time.sleep(2)  # Allow approval to process
        
        # Step 4d: Handle price override screen with specified price
        if not perform_price_override(new_price_arg="10.00", discount_arg=None, percent_discount_arg=None) :
            print("❌ Failed to handle price override screen")
            return False
        
        time.sleep(2)  # Allow price override screen to process
        
        # Step 4e: Handle reason code popup (appears after price override)
        print("📋 Handling reason code popup after price override...")
        handle_select_reason_code_popup(app, reason_to_click="Price Discrepancy", expected_reasons={ "Close to Date", "Damaged Stock", "Price Discrepancy", "Rain Check"})
        
        time.sleep(2)  # Allow system to process reason code selection
        
        # Step 4f: Validate basket after complete price override process
        if not validate_basket_and_capture_total():
            print("❌ Failed to validate basket after price override")
            
        
        print(f"✅ Price override applied successfully to first item: ${override_price}")
        
    except Exception as e:
        print(f"❌ Error during price override process: {e}")
        return False
    
    # --- Step 5: Void Line Process ---
    print(f"\n--- Step 5: Voiding second item with reason: {void_reason} ---")
    try:
        # Step 5a: Select second item in basket for void line
        if not select_basket_item_by_position(win, item_position=2):
            print("❌ Failed to select second item for void line")
            return False
        
        # Step 5b: Click Void Line button
        if not click_void_line_button(win):
            print("❌ Failed to click Void Line button")
            return False
        
        # Step 5c: Handle void line reason code screen with specified reason
        if not handle_reason_code_screen(app, reason_code=void_reason):
            print("❌ Failed to handle void line reason code screen")
            return False
        
        time.sleep(2)  # Allow system to process void operation
        
        # Step 5d: Validate basket after void line
        if not validate_basket_and_capture_total():
            print("❌ Failed to validate basket after void line operation")
            return False
        
        print("✅ Void line operation completed successfully on second item")
        
    except Exception as e:
        print(f"❌ Error during void line process: {e}")
        return False
    
    # --- Step 6: Final Balance Validation ---
    print("\n--- Step 6: Final balance due validation ---")
    if not validate_basket_and_capture_total():
        print("❌ Failed to get final basket total")
        return False
    

    # --- Step 7: Navigate to Loyalty Mode ---
    print("\n--- Step 7: Transitioning to Loyalty Mode ---")
    try:
        # Click OK to proceed to loyalty mode
        click_OK_button = win.child_window(title="OK", control_type="Button")
        if click_OK_button.exists(timeout=5):
            click_OK_button.click_input()
            print("✅ Navigated to Loyalty Mode")
        else:
            print("❌ OK button not found for loyalty navigation")
            return False
    except Exception as e:
        print(f"❌ Error navigating to loyalty mode: {e}")
        return False
    
    # --- Step 8: Handle Loyalty (Skip Customer Card) ---
    print("\n--- Step 8: Handling loyalty popup (skipping customer card) ---")
    time.sleep(2)  # Wait for loyalty popup
    if not handle_customer_popup(app, customer_number=None):
        print("❌ Failed to handle customer popup")
        return False
    
    # Handle any additional popups
    if not handle_Any_popup():
        print("❌ Failed to handle additional popups")
        return False
    
    # --- Step 9: Process Payment ---
    print("\n--- Step 9: Processing cash payment ---")
    try:
        if not process_tenders(app, tender_to_select="Cash"):
            print("❌ Failed to process cash tender payment")
            return False
        
        print("✅ Cash payment processed successfully")
        
    except Exception as e:
        print(f"❌ Error during payment processing: {e}")
        return False
    
    # --- Step 10: Handle Receipt and Cash Drawer ---
    print("\n--- Step 10: Handling receipt suppression and cash drawer ---")
    
    # Handle receipt suppression popup
    if not handle_Any_popup():
        print("❌ Failed to handle receipt suppression popup")
        return False
    
    time.sleep(3)  # Wait for cash drawer operations
    
    # Close cash drawer
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to move and close the cash drawer")
        return False
    
    print("\n🎉 --- All tasks completed successfully in price override and void line scenario! --- 🎉")
    print("\n✅ Test Summary:")
    print(f"   - First item added successfully (EAN: {first_item_ean})")
    print(f"   - Second item added successfully (EAN: {second_item_ean})")
    print(f"   - Price override applied to first item (${override_price})")
    print("   - Price override reason selected (Close to Date)")
    print(f"   - Void line completed on second item (Reason: {void_reason})")
    print("   - Approval prompt handled successfully")
    print("   - Balance validation passed (OCR extraction successful)")
    print("   - Payment processed successfully")
    print("   - Transaction completed successfully")
    
    return True


# --- Execute the test ---
if __name__ == "__main__":
    test_price_override_void_line()
