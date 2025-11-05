# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC012_basic_sale_flow
# @Features: Basic Sale Flow, Cash Tender, Loyalty Skip
# @Components: POS Login, Item Entry, Basket Validation, Payment Processing
# @Business_Rules: Basic sale transaction flow with cash payment
# @Validation_Points: Login success, Item addition, Basket contents, Payment completion
# @User_Roles: ATcash1 (Service Cashier)
# @Special_Config: None
# @Related_Tests: TC011_save_transaction_logoff_scenario
# @Dependencies: None
# @Timing_Requirements: Standard processing times
# ==========================================

import pytest
from datetime import datetime
import os
from PIL import ImageGrab
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

@pytest.mark.pos
@pytest.mark.sale
def test_basic_sale_flow(pytestconfig):
    """
    Main test function for basic sale flow with cash tender payment
    
    Test Flow:
    1. Login to POS system
    2. Add item to basket
    3. Validate basket contents
    4. Skip loyalty if prompted
    5. Complete sale with cash tender
    6. Verify cash drawer status
    
    Returns:
        bool: True if all test steps completed successfully, False on any failure
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    test_item_ean = "9300675079686"
    loyaltycarnumber = None
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting POS application and logging in ---")
    try:
        # Initialize COM
        import pythoncom
        pythoncom.CoInitialize()
        
        # Try to connect to existing window first
        try:
            app = Application(backend="uia").connect(title_re=application_window_title, timeout=5)
            print("Found existing POS window, will try to use it")
        except Exception as connect_error:
            print(f"No existing window found ({connect_error}), logging in...")
            mainlogic("ATcash1", "abcd1234")
            time.sleep(5)  # Give the application time to start
            app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("✅ Successfully connected to POS application")
        take_screenshot("login_success")
        
    except Exception as e:
        print(f"❌ Failed to connect or log in to the POS application: {e}")
        take_screenshot("login_failure")
        pytest.fail(f"Login failed: {e}")
    finally:
        # Cleanup COM
        pythoncom.CoUninitialize()
    
    # --- Step 2: Add Item ---
    print(f"\n--- Step 2: Adding item (EAN: {test_item_ean}) ---")
    if not Kayin_EAN_POS(eans_to_add=[test_item_ean]):
        print("❌ Failed to add item")
        return False
    
    # Wait for item to reflect in basket
    print("⏳ Waiting for item to reflect in basket...")
    time.sleep(3)
    take_screenshot("item_added_to_basket")
    
    # --- Step 3: Validate Basket ---
    if not validate_basket_contents():
        print("❌ Failed to validate basket contents")
        return False
    okaybutton = win.child_window(title="OK", control_type="Button")
    if okaybutton.exists():
        take_screenshot("basket_validation")
        okaybutton.click_input()
        print("✅ Basket validation passed")
    time.sleep(4)
    # --- Step 4: Handle Loyalty Popup ---
    print("\n--- Step 4: Handling loyalty popup ---")
    if not handle_customer_popup(app, loyaltycarnumber):
        print("❌ Failed to handle loyalty popup")
        return False
    time.sleep(2)
    from Components.Tenders.Cash_tender_payment import process_tenders
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process cash tender payment.")
        return False
    
    print("\n--- Step 5: Processing cash tender payment ---")
    take_screenshot("payment_processing")
    if not handle_Any_popup(specific_button="Close"):
        print("❌ popup not handled")
        take_screenshot("popup_handling_failure")
        
    
    time.sleep(2)
    # --- Step 6: Verify Cash Drawer ---
    print("\n--- Step 6: Verifying cash drawer status ---")
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to verify cash drawer status")
        return False
    
    # --- Test Summary ---
    print("\n🎉 --- Basic sale flow completed successfully! --- 🎉")
    print("\n✅ Test Summary:")
    print("   - POS login completed successfully")
    print(f"   - Item added successfully (EAN: {test_item_ean})")
    print("   - Basket validation passed")
    print("   - Loyalty popup handled")
    print("   - Cash tender payment processed")
    print("   - Cash drawer status verified")
    
    return True

# Create screenshots directory if it doesn't exist
SCREENSHOT_DIR = project_root / 'test_screenshots' / datetime.now().strftime('%Y%m%d_%H%M%S')
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def take_screenshot(name):
    """
    Capture screenshot of the entire screen
    
    Args:
        name (str): Name of the screenshot
    
    Returns:
        str: Path to the saved screenshot
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{name}_{timestamp}.png"
    filepath = SCREENSHOT_DIR / filename
    
    # Capture and save screenshot
    screenshot = ImageGrab.grab()
    screenshot.save(str(filepath))
    return str(filepath)

# --- Execute the test ---
if __name__ == "__main__":
    test_basic_sale_flow()
