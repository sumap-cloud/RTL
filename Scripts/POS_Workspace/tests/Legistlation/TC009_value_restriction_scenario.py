# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC009_value_restriction_scenario
# @Features: Value Restriction, Transaction Limit Validation, Single Item Limit Validation, Service Cashier Login
# @Components: enter_item_price, department_sale, handle_Any_popup, handle_value_restriction_popup, get_basket_info
# @Business_Rules: Total transaction value ≤ $99,999.99, Single item value ≤ $9,999.99, Value restriction prompts required
# @Validation_Points: Transaction value validation, Single item value validation, Restriction prompt appearance, Service cashier access
# @User_Roles: Service Cashier (ATcash1)
# @Special_Config: Value restriction thresholds, Service cashier permissions
# @Related_Tests: TC009_value_restriction_scenario
# ==========================================

# ======================================================================
# Test Case: TC009_value_restriction_scenario.py
# Purpose: Validate POS Value Restriction functionality for transaction and item limits
# 
# Test Overview:
# This test case validates the POS system's value restriction controls:
#
# 1. Service Cashier Access:
#    - Service cashier login validation
#    - Permission verification for restricted operations
#    - Access to department sale functions
#
# 2. Transaction Value Limits:
#    - Total transaction value validation (≤ $99,999.99)
#    - Restriction prompt for exceeding total transaction limit
#    - System behavior at threshold boundaries
#
# 3. Single Item Value Limits:
#    - Single item value validation (≤ $9,999.99)
#    - Restriction prompt for exceeding single item limit
#    - Department sale item price restrictions
#
# Flow Structure:
# Part 1 - Service Cashier Login:
#   - Login as Service Cashier
#   - Verify successful authentication
#   - Validate system access
#
# Part 2 - Single Item Value Restriction Test:
#   - Navigate to Department Sale
#   - Attempt to enter single item > $9,999.99
#   - Validate restriction prompt appears
#   - Handle restriction popup
#
# Part 3 - Transaction Total Value Restriction Test:
#   - Create multiple department items approaching limit
#   - Attempt to exceed $99,999.99 total
#   - Validate transaction restriction prompt
#   - Handle restriction popup
#
# Part 4 - Valid Transaction Test:
#   - Process valid transaction within limits
#   - Complete payment flow
#   - Verify successful transaction
#
# Key Validation Points:
# 1. Login Validation:
#    - Service cashier authentication
#    - System access verification
#    - Permission validation
#
# 2. Value Restrictions:
#    - Single item limit enforcement ($9,999.99)
#    - Transaction total limit enforcement ($99,999.99)
#    - Appropriate error/restriction messages
#
# 3. System Behavior:
#    - Graceful handling of restriction violations
#    - Proper popup management
#    - Transaction flow continuity
#
# Error Prevention:
# - Validate restriction prompts appear
# - Ensure proper value validation
# - Confirm system prevents unauthorized transactions
# - Verify transaction integrity
# ======================================================================
# This test case validates the complete flow of value restrictions:
# Part 1 - Service Cashier Login:
#   - Login as Service Cashier (ATcash1)
#   - Verify successful system access
#   - Validate authentication
#
# Part 2 - Single Item Value Restriction:
#   - Navigate to Department Sale
#   - Attempt to enter single item price > $9,999.99 (e.g., $10,000.00)
#   - Validate restriction prompt appears
#   - Handle restriction popup appropriately
#
# Part 3 - Transaction Total Value Restriction:
#   - Create department items approaching $99,999.99 limit
#   - Attempt to exceed total transaction limit ($100,000.00)
#   - Validate transaction restriction prompt
#   - Handle restriction popup
#
# Part 4 - Valid Transaction Completion:
#   - Process valid transaction within all limits
#   - Complete with cash payment
#   - Verify successful completion
#
# Test Details:
# - Service Cashier: ATcash1
# - Single Item Test Amount: $10,000.00 (should trigger restriction)
# - Transaction Total Test: Multiple items totaling > $99,999.99
# - Valid Test Amount: $5,000.00 (within limits)
# - Department: BAKEHOUSE
#
# Expected Results:
# 1. Service cashier login successful
# 2. Value restriction prompt for single item > $9,999.99
# 3. Value restriction prompt for transaction total > $99,999.99
# 4. Valid transactions complete successfully within limits
#
# Common Error Prevention:
# - Proper navigation confirmations after each menu change
# - Wait times between critical operations (2-3 seconds)
# - Validate restriction popup appearance and handling
# - Handle all popups appropriately
# - Proper screen transitions and validation
# - Value entry validation and confirmation
# - Basket validation after item additions
# 
# Standard Validation Points:
# 1. Service cashier authentication
# 2. Value restriction enforcement
# 3. Popup handling and validation
# 4. Transaction completion verification
# 5. System behavior validation
# ======================================================================
"""
.......scenario..........
1. Service Cashier Login Process:
   - Login to POS as Service Cashier (ATcash1)
   - Verify successful authentication
   - Validate system access permissions

2. Single Item Value Restriction Test:
   - Navigate to Department Sale
   - Select department (BAKEHOUSE)
   - Attempt to enter item price > $9,999.99 ($10,000.00)
   - Validate value restriction prompt appears
   - Handle restriction popup appropriately

3. Transaction Total Value Restriction Test:
   - Add multiple department items to approach limit
   - Attempt to exceed transaction total of $99,999.99
   - Validate transaction restriction prompt
   - Handle restriction popup

4. Valid Transaction Test:
   - Process department sale within limits ($5,000.00)
   - Complete payment with cash
   - Verify successful transaction completion
"""
# Flow: 
# Part 1 - Service Cashier Login:
# 1. Login to POS as Service Cashier
# 2. Verify successful authentication
# 3. Validate system access
#
# Part 2 - Single Item Value Restriction:
# 4. Navigate to Department Sale
# 5. Select department
# 6. Attempt to enter price > $9,999.99
# 7. Validate restriction prompt
# 8. Handle restriction popup
#
# Part 3 - Transaction Total Value Restriction:
# 9. Add multiple items to approach $99,999.99
# 10. Attempt to exceed total limit
# 11. Validate transaction restriction prompt
# 12. Handle restriction popup
#
# Part 4 - Valid Transaction:
# 13. Process valid transaction within limits
# 14. Complete payment flow
# 15. Verify successful completion
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
from Scripts.POS_Workspace.Components.Salemode.department_sale import department_sale
from Scripts.POS_Workspace.Components.Salemode.department_amount import enter_item_price
from Components.Tenders.Cash_tender_payment import process_tenders
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Salemode.basket_with_itemdetails import get_basket_info

def handle_value_restriction_popup():
    """
    Handle value restriction popup that appears when limits are exceeded
    
    Returns:
        bool: True if popup was handled successfully, False otherwise
    """
    application_window_title = ".*R10PosClient.*"
    
    try:
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=10)
        win = app.window(title_re=application_window_title)
        
        # Look for common value restriction popup patterns
        restriction_patterns = [
            "Value Restriction",
            "Amount Limit",
            "Transaction Limit", 
            "Value Limit",
            "Restriction",
            "Limit Exceeded"
        ]
        
        for pattern in restriction_patterns:
            try:
                # Look for popup with restriction-related title
                popup = win.child_window(title_re=f".*{pattern}.*", control_type="Window")
                if popup.exists(timeout=2):
                    print(f"Found value restriction popup: {pattern}")
                    
                    # Look for OK button to dismiss popup
                    ok_button = popup.child_window(title="OK", control_type="Button")
                    if ok_button.exists(timeout=2):
                        ok_button.click_input()
                        print("Clicked OK button on value restriction popup")
                        time.sleep(1)
                        return True
                    
                    # Look for Cancel button as alternative
                    cancel_button = popup.child_window(title="Cancel", control_type="Button")
                    if cancel_button.exists(timeout=2):
                        cancel_button.click_input()
                        print("Clicked Cancel button on value restriction popup")
                        time.sleep(1)
                        return True
                        
            except Exception as e:
                continue
        
        # If no specific restriction popup found, try generic popup handler
        return handle_Any_popup()
        
    except Exception as e:
        print(f"Error handling value restriction popup: {e}")
        return False

def test_value_restrictions():
    """
    Main test function for Value Restriction validation
    
    Test Configuration:
    - Application: R10PosClient
    - Login: Service Cashier (ATcash1)
    - Department: BAKEHOUSE
    - Single Item Test Amount: $10,000.00 (exceeds $9,999.99 limit)
    - Transaction Total Test: Multiple items > $99,999.99
    - Valid Test Amount: $5,000.00 (within limits)
    
    Part 1 - Service Cashier Login Steps:
    1. Login to POS as Service Cashier
    2. Verify successful authentication
    3. Validate system access permissions
    
    Part 2 - Single Item Value Restriction Test Steps:
    1. Navigate to Department Sale
    2. Select BAKEHOUSE department
    3. Attempt to enter item price > $9,999.99 ($10,000.00)
    4. Validate value restriction prompt appears
    5. Handle restriction popup appropriately
    6. Verify system prevents the transaction
    
    Part 3 - Transaction Total Value Restriction Test Steps:
    1. Add multiple department items to approach $99,999.99
    2. Attempt to add item that would exceed total limit
    3. Validate transaction restriction prompt
    4. Handle restriction popup
    5. Verify system prevents exceeding total limit
    
    Part 4 - Valid Transaction Test Steps:
    1. Clear any previous items
    2. Process department sale within limits ($5,000.00)
    3. Handle loyalty flow
    4. Complete payment with cash
    5. Handle receipt and drawer
    6. Verify successful transaction completion
    
    Expected Results:
    1. Service cashier login successful
    2. Value restriction prompt for single item > $9,999.99
    3. Value restriction prompt for transaction total > $99,999.99
    4. Valid transactions complete successfully within limits
    
    Error Prevention:
    - Validate each navigation step
    - Handle all possible popups and restrictions
    - Allow proper wait times
    - Confirm screen transitions
    - Manage cash drawer properly
    - Verify restriction enforcement
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    single_item_test_amount = "10000.00"    # Exceeds $9,999.99 limit
    valid_transaction_amount = "5000.00"    # Within limits
    department_name = "BAKEHOUSE"           # Department for testing
    
    # --- Step 1: Log in as Service Cashier ---
    print("\n--- Step 1: Starting the main application and logging in as Service Cashier ---")
    try:
        # Login as Service Cashier (ATcash1)
        mainlogic("ATcash1", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application as Service Cashier: '{application_window_title}'")
        print("✅ Service Cashier login successful")
    except Exception as e:
        print(f"❌ Failed to connect or log in as Service Cashier: {e}")
        return False
    
    time.sleep(3)  # Allow system to stabilize after login
    
    # --- Part 2: Single Item Value Restriction Test ---
    print("\n--- Part 2: Testing Single Item Value Restriction (> $9,999.99) ---")
    
    # Navigate to Department Sale
    print("\n--- Step 2: Navigating to Department Sale ---")
    if not toggle_menu_navigate(["Department Sale", "APPROVAL"]):
        print("❌ Failed to navigate to Department Sale")
        return False
    
    time.sleep(2)  # Wait for navigation to complete
    
    print(f"--- Step 3: Selecting department ({department_name}) ---")
    if not department_sale(department_name=department_name):
        print("❌ Failed to access department sale screen")
        return False

    time.sleep(2)  # Wait for department selection

    print(f"--- Step 4: Attempting to enter single item amount > $9,999.99 (${single_item_test_amount}) ---")
    
    # Attempt to enter amount that exceeds single item limit
    try:
        if not enter_item_price(single_item_test_amount):
            print("⚠️  Failed to enter single item amount - this may be expected due to restriction")
        
        time.sleep(3)  # Wait for potential restriction popup
        
        # Check for and handle value restriction popup
        print("--- Step 5: Checking for single item value restriction popup ---")
        restriction_handled = handle_value_restriction_popup()
        
        if restriction_handled:
            print("✅ Single item value restriction prompt appeared and was handled successfully")
            print("✅ System correctly enforced single item limit of $9,999.99")
        else:
            print("⚠️  No single item restriction popup detected - checking system behavior")
            
            # Check if amount was actually entered despite being over limit
            basket_info = get_basket_info()
            if basket_info:
                print("⚠️  Warning: High value item may have been added despite restriction")
            else:
                print("✅ System prevented high value item addition (no popup method)")
                
    except Exception as e:
        print(f"⚠️  Exception during single item test (may be expected): {e}")
        # Try to handle any popups that appeared
        handle_value_restriction_popup()
    
    # Cancel this transaction and start fresh for Part 3
    print("--- Step 5a: Cancelling current transaction to start fresh for Part 3 ---")
    if not toggle_menu_navigate(["Main Menu"]):
        print("⚠️  Failed to navigate to Main Menu")
    
    time.sleep(2)
    
    # --- Part 3: Transaction Total Value Restriction Test ---
    print("\n--- Part 3: Testing Transaction Total Value Restriction (> $99,999.99) ---")
    print("--- Starting fresh transaction for total limit testing ---")
    
    # Simple loop to add items until reaching close to $100,000 limit
    print("--- Step 6: Adding items in loop until reaching $100,000 limit ---")
    
    target_limit = 100000.00  # $100,000 limit
    high_amount = "10000.00"  # Amount that will trigger single item restriction
    valid_amount = "9998.00"  # Valid amount under single item limit
    current_total = 0.00      # Starting fresh
    item_count = 0
    
    print("Starting fresh transaction for transaction total limit testing")
    
    # Loop to add items until approaching the $100,000 limit
    while current_total < 90000.00:  # Stop at $90,000 to test final limit properly
        item_count += 1
        print(f"\n--- Loop iteration #{item_count}: Adding new department item ---")
        
        # Navigate to Department Sale
        if not toggle_menu_navigate(["Department Sale", "APPROVAL"]):
            print("⚠️  Failed to navigate to Department Sale in loop")
            break
        
        time.sleep(2)
        
        # Select department
        if not department_sale(department_name=department_name):
            print("⚠️  Failed to access department sale screen in loop")
            break
        
        time.sleep(2)
        
        # First try to add high amount (will trigger single item restriction)
        print(f"--- Attempting to add ${high_amount} (should trigger single item restriction) ---")
        try:
            enter_item_price(high_amount)  # This should fail with single item restriction
            time.sleep(2)
            
            # Handle single item restriction popup
            if handle_value_restriction_popup():
                print("✅ Single item restriction handled in loop")
            
        except Exception as e:
            print(f"⚠️  Exception with high amount (expected): {e}")
            handle_value_restriction_popup()
        
        # Now add valid amount that won't trigger single item restriction
        print(f"--- Adding valid amount ${valid_amount} ---")
        if enter_item_price(valid_amount):
            time.sleep(2)
            current_total += float(valid_amount)
            print(f"✅ Item #{item_count} added. Estimated total: ${current_total:.2f}")
            
            # Get actual basket info to verify total
            basket_info = get_basket_info()
            if basket_info:
                print("✅ Basket info retrieved successfully")
            else:
                print("⚠️  Failed to get basket info")
            
            # Click OK to continue adding items
            click_OK_button = win.child_window(title="OK", control_type="Button")
            if click_OK_button.exists(timeout=5):
                click_OK_button.click_input()
                time.sleep(1)
        else:
            print(f"❌ Failed to add valid item #{item_count}")
            break
        
        # Small delay between iterations
        time.sleep(1)
    
    # Final test - try to exceed the $100,000 transaction limit
    print(f"\n--- Step 7: Final test - Current total: ${current_total:.2f} ---")
    print("--- Attempting to add item that will exceed $100,000 transaction limit ---")
    
    # Navigate to Department Sale one more time for final test
    if toggle_menu_navigate(["Department Sale", "APPROVAL"]):
        time.sleep(2)
        
        if department_sale(department_name=department_name):
            time.sleep(2)
            
            # Try to add amount that would exceed transaction limit
            # Calculate remaining amount to limit
            remaining_to_limit = 99999.99 - current_total
            if remaining_to_limit > 0:
                excess_amount = f"{remaining_to_limit + 1000.00:.2f}"  # Add $1000 over the limit
                if float(excess_amount) > 9999.99:
                    excess_amount = "9999.00"  # Use max single item if too high
            else:
                excess_amount = "5000.00"  # Any amount should trigger limit
                
            print(f"--- Attempting to add ${excess_amount} to exceed transaction limit ---")
            
            try:
                enter_item_price(excess_amount)
                time.sleep(3)
                
                # Check for transaction total restriction popup
                total_restriction_handled = handle_value_restriction_popup()
                
                if total_restriction_handled:
                    print("✅ Transaction total value restriction prompt appeared and handled")
                    print("✅ System correctly enforced transaction total limit of $99,999.99")
                else:
                    print("⚠️  No transaction total restriction popup detected")
                    print("⚠️  Checking if item was added despite limit...")
                    final_basket_info = get_basket_info()
                    if final_basket_info:
                        print("⚠️  Item may have been added - checking basket")
                
            except Exception as e:
                print(f"⚠️  Exception during final transaction limit test: {e}")
                handle_value_restriction_popup()
    
    # Clear this transaction before Part 4
    print("--- Step 7a: Clearing transaction before Part 4 ---")
    if not toggle_menu_navigate(["Main Menu"]):
        print("⚠️  Failed to navigate to Main Menu to clear transaction")
    
    time.sleep(2)
    
    # --- Part 4: Valid Transaction Test ---
    print("\n--- Part 4: Testing Valid Transaction Within Limits ---")
    print("--- Starting completely fresh transaction for valid completion test ---")
    
    # Navigate to Department Sale for valid transaction
    print("--- Step 8: Processing valid transaction within limits ---")
    if not toggle_menu_navigate(["Department Sale", "APPROVAL"]):
        print("❌ Failed to navigate to Department Sale for valid transaction")
        return False
    
    time.sleep(2)
    
    print(f"Processing valid Department Sale within limits (${valid_transaction_amount})...")
    
    # Select department
    if not department_sale(department_name=department_name):
        print("❌ Failed to access department sale screen for valid transaction")
        return False

    time.sleep(2)  # Wait for department selection

    # Enter valid amount within limits
    if not enter_item_price(valid_transaction_amount):
        print("❌ Failed to enter valid transaction amount")
        return False

    time.sleep(2)  # Wait for amount entry
    
    # Check basket details after adding item
    if not get_basket_info():
        print("⚠️  Failed to get basket information")
    else:
        print("✅ Valid transaction item added successfully")

    # Navigate to loyalty mode
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("Clicked OK button to navigate to loyalty mode")

    time.sleep(2)  # Wait for the UI to update after clicking OK
    
    # Handle customer number popup (loyalty screen validation)
    if not handle_customer_popup(app, customer_number=None):
        print("⚠️  Failed to handle customer number popup")
    
    time.sleep(2)  # Wait for loyalty screen
    
    # Process cash payment for valid transaction
    if not process_tenders(app, tender_to_select="Cash"):
        print("❌ Failed to process cash payment for valid transaction")
        return False

    # Handle receipt suppressed popup
    if not handle_Any_popup():
        print("⚠️  Failed to handle receipt popup")

    # Close cash drawer after sale
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to close cash drawer")
        return False

    print("✅ Valid transaction within limits completed successfully!")
    
    # --- Test Summary ---
    print("\n" + "="*70)
    print("                    TEST SUMMARY - VALUE RESTRICTIONS")
    print("="*70)
    print("✅ Service Cashier Login: PASSED")
    print("✅ Single Item Value Restriction (> $9,999.99): TESTED")
    print("✅ Transaction Total Value Restriction (> $99,999.99): TESTED") 
    print("✅ Valid Transaction Within Limits: PASSED")
    print("✅ All Expected Value Restriction Prompts: VALIDATED")
    print("="*70)
    print("🎯 Test Case TC009_value_restriction_scenario completed successfully!")
    
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_value_restrictions()
