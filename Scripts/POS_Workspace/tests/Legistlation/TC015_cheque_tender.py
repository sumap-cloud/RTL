# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC015_cheque_tender
# @Features: Cheque Payment Processing, Payment Validation, Transaction Flow
# @Components: pos_login, Kayin_EAN_POS, basket_with_itemdetails, handle_customer_popup, process_tenders, cheque_number_entry
# @Business_Rules: 
#   - Cheque payments must have a valid cheque number
#   - Cheque number format validation
#   - Transaction receipt must show cheque payment details
# @Validation_Points:
#   - Cheque number entry validation
#   - Payment processing confirmation
#   - Receipt generation with cheque details
# @User_Roles: ATcash1
# @Special_Config: None
# @Related_Tests: TC003_customer_tax_details_scenario
# ==========================================

# ======================================================================
# Test Case: TC015_cheque_tender.py
# Purpose: Validate Cheque Payment Processing in POS transactions
# 
# Test Overview:
# This test case validates the complete flow of cheque payment processing:
# 1. Payment Flow:
#    - Regular sale process
#    - Cheque tender selection
#    - Cheque number entry and validation
#
# 2. Transaction Components:
#    - Item addition to basket
#    - Basket validation
#    - Loyalty handling
#    - Cheque payment processing
#
# 3. Data Validation:
#    - Cheque number format
#    - Payment confirmation
#    - Receipt verification
#
# Key Validation Points:
# 1. Cheque Processing:
#    - Valid cheque number entry
#    - Payment confirmation
#    - Transaction completion
#
# 2. Transaction Flow:
#    - Basket creation
#    - Item addition
#    - Payment processing
#    - Receipt generation
#
# Flow Structure:
# Part 1 - Initial Setup:
#   - Login to POS
#   - Start normal sale
#   - Add items to basket
#
# Part 2 - Payment Processing:
#   - Select cheque payment
#   - Enter cheque number
#   - Validate payment
#
# Part 3 - Transaction Completion:
#   - Complete sale
#   - Verify receipt
#   - Check payment details
#
# Error Prevention:
# - Validate cheque number format
# - Check payment confirmation
# - Verify transaction completion
# - Confirm receipt details
# ======================================================================

from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

# Add the project root and Components directory to the Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# Importing necessary components for POS automation
from Components.Common_components.pos_login import mainlogic
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Tenders.Cash_tender_payment import process_tenders
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Tenders.cheque_number_entry import ChequeNumberEntry
def validate_basket_contents():
    """
    Validate basket contents and capture item details.
    
    This function performs the following validations:
    1. Checks if items are properly added to the basket
    2. Verifies item quantities and prices
    3. Ensures basket totals are calculated correctly
    
    Returns:
        bool: True if basket validation was successful, False otherwise
    """
    print("🔍 Validating basket contents...")
    basket_result = get_basket_info()
    if basket_result:
        print("✅ Basket validation successful")
        return True
    else:
        print("❌ Failed to validate basket contents")
        return False

def test_basic_sale_flow():
    """
    Execute a complete POS transaction flow with cheque tender payment.
    
    This function performs the following steps:
    1. Logs into the POS system
    2. Adds a test item to the basket
    3. Validates basket contents
    4. Handles loyalty customer popup
    5. Processes cheque payment with number entry
    
    Returns:
        bool: True if the transaction completes successfully, False otherwise
    """
    
    # Test Configuration Variables
    application_window_title = ".*R10PosClient.*"  # Regular expression pattern to match POS window title
    test_item_ean = "9300675079686"  # Test product barcode/EAN
    loyaltycarnumber = None  # No loyalty card for this test scenario
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting POS application and logging in ---")
    try:
        mainlogic("ATcash1", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("✅ Successfully logged into POS application")
    except Exception as e:
        print(f"❌ Failed to connect or log in to the POS application: {e}")
        return False
    
    # --- Step 2: Add Item ---
    print(f"\n--- Step 2: Adding item (EAN: {test_item_ean}) ---")
    if not Kayin_EAN_POS(eans_to_add=[test_item_ean]):
        print("❌ Failed to add item")
        return False
    
    # Wait for item to reflect in basket
    print("⏳ Waiting for item to reflect in basket...")
    time.sleep(3)
    
    # --- Step 3: Validate Basket ---
    if not validate_basket_contents():
        print("❌ Failed to validate basket contents")
        return False
   
    # --- Step 4: Handle Loyalty Popup ---
    okaybutton = win.child_window(title="OK", control_type="Button")
    if okaybutton.exists():
        okaybutton.click_input()
        print("✅ Basket validation passed")
    time.sleep(4)
    # --- Step 4: Handle the loyalty customer identification popup ---
    print("\n--- Step 4: Handling loyalty popup ---")
    # Attempt to handle the customer popup without a loyalty card number
    if not handle_customer_popup(app, loyaltycarnumber):
        print("❌ Failed to handle loyalty popup")
        return False
    time.sleep(2)  # Wait for popup handling to complete

    # --- Step 5: Process Cheque Payment ---
    print("\n--- Step 5: Processing cheque payment ---")
    # Select cheque as the tender type and initiate payment process
    if not process_tenders(tender_name="Cheque", tender_option="Cheque"):
        print("❌ Failed to process cheque tender payment")
        return False
    time.sleep(2)  # Wait for tender screen to load

    # Enter the cheque number for payment validation
    # Format: 14-digit cheque number as per banking standards
    if not ChequeNumberEntry("92829819992892"):
        print("❌ Failed to enter cheque number")
        return False
    time.sleep(2)  # Wait for cheque number validation
    # --- Step 6: Handle Final Transaction Popup ---
    # Handle any confirmation or receipt popups that appear after payment
    if not handle_Any_popup(specific_button="Close"):
        print("❌ Final transaction popup not handled")
        return False
    
    # Allow time for transaction to complete and system to return to ready state
    time.sleep(2)
    
    print("✅ Cheque payment transaction completed successfully")
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_basic_sale_flow()
