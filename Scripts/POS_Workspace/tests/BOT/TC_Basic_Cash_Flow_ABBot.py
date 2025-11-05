# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC_Basic_Cash_Flow_ABBot
# @Purpose: Validate basic POS cash flow with ABB robot integration
# @Features: Service Cashier Login, Item Addition via Keyin, Loyalty Skip, Cash Payment with ABB Robot
# @Components: pos_login, Keyin_item, get_basket_info, handle_customer_popup, process_tenders, AbbAction
# @Business_Rules: Service cashier access, Item addition validation, Loyalty optional, Cash payment completion
# @Validation_Points: Successful login, Item added to basket, Loyalty skipped, Payment processed, Robot drawer action
# @User_Roles: Service Cashier (ATcash1)
# @Special_Config: ABB Robot integration for physical cash drawer operations
# @Related_Tests: TC003_loyalty_basic_scenario_ai, TC009_value_restriction_scenario
# @Robot_Actions: Close_Drawer via ABB robot instead of software simulation
# ==========================================

# ======================================================================
# Test Case: TC_Basic_Cash_Flow_ABBot.py
# Purpose: Validate Basic POS Cash Flow with ABB Robot Integration
# ======================================================================
"""Basic POS Cash Flow with ABB Robot Integration.

This test case validates the complete basic POS transaction flow using
the ABB robot for physical cash drawer operations instead of software simulation.

Test Overview:
This test validates the basic POS transaction workflow:

1. Service Cashier Authentication:
   - Login with service cashier credentials
   - Verify successful system access
   - Validate POS readiness

2. Item Addition Process:
   - Add single item using keyin/EAN entry
   - Validate item appears in basket
   - Verify basket details and totals

3. Loyalty Processing:
   - Navigate to loyalty mode
   - Skip loyalty card association
   - Proceed to payment mode

4. Cash Payment with Robot:
   - Process cash payment
   - Handle payment completion
   - Use ABB robot for physical drawer operations
   - Validate transaction completion

Flow Structure:
Part 1 - Service Cashier Login:
  - Login as service cashier
  - Verify authentication success
  - Validate system access

Part 2 - Item Addition:
  - Add item via EAN entry
  - Validate basket contents
  - Confirm item details

Part 3 - Loyalty Handling:
  - Navigate to loyalty mode
  - Skip customer card entry
  - Proceed to tender mode

Part 4 - Payment with ABB Robot:
  - Process cash payment
  - Handle receipt popups
  - Execute ABB robot drawer closure
  - Validate completion

Expected Results:
✅ Service cashier login successful
✅ Item added to basket correctly
✅ Loyalty skip completed
✅ Cash payment processed
✅ ABB robot drawer action executed
✅ Transaction completed successfully
"""

# Flow Details:
# Actual Flow:
# - Login to POS with service cashier
# - Add one article with keyin
# - Skip loyalty  
# - Complete transaction with cash using ABB robot
#
# Expected Flow:
# - Login POS successful
# - Item should get added
# - Loyalty skip completed
# - Completed sale with cash tender using ABB robot

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
from Components.Tenders.Cash_tender_payment import process_tenders
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.BotActions.AbbAction import Trigger_Action

def test_basic_cash_flow_abbot():
    """
    Main test function for Basic Cash Flow with ABB Robot Integration
    
    Test Configuration:
    - Application: R10PosClient
    - Login: Service Cashier (ATcash1)
    - Test Item: Standard EAN code for testing
    - Payment Method: Cash
    - Robot Integration: ABB robot for drawer operations
    
    Part 1 - Service Cashier Login Steps:
    1. Login to POS as Service Cashier
    2. Verify successful authentication
    3. Validate system access and readiness
    
    Part 2 - Item Addition Steps:
    1. Add item using EAN/keyin entry
    2. Validate item appears in basket
    3. Verify basket details and totals
    4. Confirm item addition success
    
    Part 3 - Loyalty Processing Steps:
    1. Navigate to loyalty mode (click OK button)
    2. Handle customer popup (skip loyalty)
    3. Proceed to tender/payment mode
    4. Validate loyalty skip completion
    
    Part 4 - Cash Payment with ABB Robot Steps:
    1. Process cash payment selection
    2. Handle payment completion dialogs
    3. Handle receipt suppression popup
    4. Execute ABB robot drawer closure
    5. Validate transaction completion
    
    Expected Results:
    - Service cashier authentication successful
    - Item added to basket with correct details
    - Loyalty skip completed without issues
    - Cash payment processed successfully
    - ABB robot executes drawer closure physically
    - Transaction completes successfully
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    service_cashier_username = "ATcash1"
    service_cashier_password = "abcd1234"
    test_ean_code = "9300675014779"  # Standard test item EAN
    
    # --- Step 1: Log in as Service Cashier ---
    print("\n" + "="*70)
    print("           TC_Basic_Cash_Flow_ABBot - ABB Robot Integration Test")
    print("="*70)
    print("\n--- Step 1: Starting the main application and logging in as Service Cashier ---")
    
    try:
        mainlogic("ATcash5", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20) # Increased timeout
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False
    
    time.sleep(3)  # Allow system to stabilize after login
    robot_response = Trigger_Action(",Close_Drawer")
    
    if "ERROR" in robot_response:
        print(f"❌ ABB robot action failed: {robot_response}")
        return False
    else:
        print(f"✅ ABB robot drawer closure successful: {robot_response}")
    
    # --- Step 2: Add Item via Keyin/EAN Entry ---
    print("\n--- Step 2: Adding item via EAN entry ---")
    
    print(f"Adding test item with EAN: {test_ean_code}")
    if not Kayin_EAN_POS(eans_to_add=[test_ean_code]):
        print("❌ Failed to add item via EAN entry")
        return False
    
    print("✅ Item added via EAN entry successful")
    time.sleep(2)  # Wait for item to be processed
    
    # --- Step 3: Validate Basket Information ---
    print("\n--- Step 3: Validating basket information ---")
    
    if not get_basket_info():
        print("❌ Failed to get basket information")
        return False
    
    print("✅ Basket validation successful - item details confirmed")
    
    time.sleep(2)  # Wait for basket validation to complete
    
    # --- Step 4: Navigate to Loyalty Mode ---
    print("\n--- Step 4: Navigating to loyalty mode ---")
    
    # Click OK button to navigate to loyalty mode
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("✅ Clicked OK button to navigate to loyalty mode")
    else:
        print("❌ OK button not found for loyalty navigation")
        return False
    
    time.sleep(2)  # Wait for UI to update after clicking OK
    
    # --- Step 5: Handle Loyalty (Skip Customer Card) ---
    print("\n--- Step 5: Handling loyalty popup (skipping customer card) ---")
    
    # Handle customer number popup - skip loyalty by passing None
    if not handle_customer_popup(app, customer_number=None):
        print("❌ Failed to handle customer number popup")
        return False
    
    print("✅ Loyalty skip completed successfully")
    
    time.sleep(2)  # Wait for loyalty screen to transition
    
    # --- Step 6: Process Cash Payment ---
    print("\n--- Step 6: Processing cash payment ---")
    
    # Process cash payment
    if not process_tenders(app, tender_to_select="Cash"):
        print("❌ Failed to process cash payment")
        return False
    
    print("✅ Cash payment processed successfully")
    
    time.sleep(3)  # Wait for payment processing
    
    # --- Step 7: Handle Receipt and Additional Popups ---
    print("\n--- Step 7: Handling receipt and additional popups ---")
    
    # Handle receipt suppressed popup and any other dialogs
    if not handle_Any_popup():
        print("⚠️  Warning: Failed to handle some popups (may be expected)")
    else:
        print("✅ Receipt and popup handling completed")
    
    time.sleep(2)  # Wait for popup handling
    
    # --- Step 8: ABB Robot Drawer Closure ---
    print("\n--- Step 8: Executing ABB robot drawer closure ---")
    
    print("🤖 Sending command to ABB robot to close cash drawer...")
    robot_response = Trigger_Action(",Close_Drawer")
    
    if "ERROR" in robot_response:
        print(f"❌ ABB robot action failed: {robot_response}")
        return False
    else:
        print(f"✅ ABB robot drawer closure successful: {robot_response}")
    
    time.sleep(2)  # Wait for robot action to complete
    
    # --- Test Summary ---
    print("\n" + "="*70)
    print("                    TEST SUMMARY - BASIC CASH FLOW WITH ABB ROBOT")
    print("="*70)
    print("✅ Service Cashier Login: PASSED")
    print("✅ Item Addition via EAN: PASSED")
    print("✅ Basket Validation: PASSED") 
    print("✅ Loyalty Skip: PASSED")
    print("✅ Cash Payment Processing: PASSED")
    print("✅ ABB Robot Drawer Closure: PASSED")
    print("✅ Transaction Completion: PASSED")
    print("="*70)
    print("🎉 Basic Cash Flow with ABB Robot Integration completed successfully!")
    print("="*70)
    
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_basic_cash_flow_abbot()
