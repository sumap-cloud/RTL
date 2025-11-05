# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC013_sale_with_loyalty
# @Features: Basic Sale Flow with Loyalty Card, Cash Tender
# @Components: POS Login, Item Entry, Basket Validation, Loyalty Card Entry, Payment Processing
# @Business_Rules: Sale transaction flow with loyalty card and cash payment
# @Validation_Points: Login success, Item addition, Basket contents, Loyalty card entry, Payment completion
# @User_Roles: ATcash1 (Service Cashier)
# @Special_Config: None
# @Related_Tests: TC012_basic_sale_flow
# @Dependencies: None
# @Timing_Requirements: Standard processing times
# ==========================================

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
    
components_path = project_root / 'Components'
if str(components_path) not in sys.path:
    sys.path.insert(0, str(components_path))

# Importing necessary components for POS automation
from Components.Common_components.pos_login import mainlogic
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Tenders.Cash_tender_payment import process_tenders
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Common_components.cashDrawer import cashdrawer_move_and_close

def validate_basket_contents():
    """
    Validate basket contents and capture item details.
    
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

def test_sale_with_loyalty():
    """
    Main test function for sale flow with loyalty card and cash tender payment
    
    Test Flow:
    1. Login to POS system
    2. Add item to basket
    3. Validate basket contents
    4. Enter loyalty card number
    5. Complete sale with cash tender
    6. Verify cash drawer status
    
    Returns:
        bool: True if all test steps completed successfully, False on any failure
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    test_item_ean = "9300675079686"
    loyalty_card_number = "234565432234"

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
    
    # --- Step 3: Validate Basket (this is common methods for all scenario flow) ---
    if not validate_basket_contents():
        print("❌ Failed to validate basket contents")
        return False
    
    # to move sale mode to loyalty mode we have to click OK button
    okaybutton = win.child_window(title="OK", control_type="Button")
    if okaybutton.exists():
        okaybutton.click_input()
        print("✅ Basket validation passed")
    time.sleep(4)

    # --- Step 4: Handle Loyalty Card Entry ---
    print("\n--- Step 4: Entering loyalty card number ---")
    if not handle_customer_popup(app, loyalty_card_number):
        print("❌ Failed to enter loyalty card number")
        return False
    time.sleep(2)

    # --- Step 5: Process Cash Tender Payment ---
    print("\n--- Step 5: Processing cash tender payment ---")
    if not process_tenders(app, tender_to_select="Cash"):
        print("❌ Failed to process cash tender payment")
        return False
    
    if not handle_Any_popup(specific_button="Close"):
        print("❌ Popup not handled")
    
    time.sleep(2)
    
    # --- Step 6: Verify Cash Drawer ---
    print("\n--- Step 6: Verifying cash drawer status ---")
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to verify cash drawer status")
        return False
    
    # --- Test Summary ---
    print("\n🎉 --- Sale with loyalty card flow completed successfully! --- 🎉")
    print("\n✅ Test Summary:")
    print("   - POS login completed successfully")
    print(f"   - Item added successfully (EAN: {test_item_ean})")
    print("   - Basket validation passed")
    print(f"   - Loyalty card entered: {loyalty_card_number}")
    print("   - Cash tender payment processed")
    print("   - Cash drawer status verified")
    
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_sale_with_loyalty()
