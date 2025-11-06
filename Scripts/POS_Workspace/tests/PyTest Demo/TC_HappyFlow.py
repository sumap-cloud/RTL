from pywinauto import Application
import sys
from pathlib import Path
import time
import pytest
import pytest_html
from PIL import ImageGrab
from datetime import datetime
import os

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing necessary components for POS automation
from Scripts.POS_Workspace.Components.funds.change_screen_funds import chnagescreen_funds
from Scripts.POS_Workspace.Components.Tenders.tenderSelection import process_tender
from Scripts.POS_Workspace.Components.Common_components.pos_login import mainlogic
from Scripts.POS_Workspace.Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Scripts.POS_Workspace.Components.Salemode.Keyin_item import Kayin_EAN_POS
from Scripts.POS_Workspace.Components.Salemode.item_search import perform_item_search
from Scripts.POS_Workspace.Components.Salemode.PLUMenu import click_plu_path
from Scripts.POS_Workspace.Components.Salemode.basket_with_itemdetails import get_basket_info
from Scripts.POS_Workspace.Components.Recall.recall_transction import recall_transaction
from Scripts.POS_Workspace.Components.Recall.transaction_selction_recall import find_transaction
from Scripts.POS_Workspace.Components.Recall.recall_intervention_List import solve_intervention
from Scripts.POS_Workspace.Components.legislation.ageRestriction_window import handle_age_restriction
from Scripts.POS_Workspace.Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Scripts.POS_Workspace.Components.Common_components.ResonCode_popup import  handle_select_reason_code_popup
from Scripts.POS_Workspace.Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Scripts.POS_Workspace.Components.Loyalty.validate_loyalty_card import validate_loyalty_card
from Scripts.POS_Workspace.Components.Recall.transaction_selction_recallv2 import select_recall_transaction

from Scripts.POS_Workspace.Components.Tenders.Cash_tender_payment import process_tenders

# Global list to store screenshots for the report
screenshot_list = []

def capture_screenshot(step_name, extra):
    """Capture screenshot and add it to the HTML report"""
    try:
        # Create screenshots directory if it doesn't exist
        screenshot_dir = Path(__file__).parent / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"step_{step_name.replace(' ', '_').replace(':', '')}_{timestamp}.png"
        filepath = screenshot_dir / filename
        
        # Capture screenshot
        screenshot = ImageGrab.grab()
        screenshot.save(str(filepath))
        
        # Read the image as binary data and encode to base64 string
        # pytest-html expects base64 encoded STRING, not bytes
        with open(str(filepath), 'rb') as f:
            image_data = f.read()
        
        import base64
        base64_string = base64.b64encode(image_data).decode('utf-8')
        
        # Add to pytest-html report - content must be base64 string
        extra.append(pytest_html.extras.png(base64_string, name=step_name))
        
        # Store for reference
        screenshot_list.append({
            'step': step_name,
            'path': str(filepath),
            'filename': filename
        })
        
        print(f"📸 Screenshot captured: {filename}")
        return str(filepath)
    except Exception as e:
        print(f"⚠️ Failed to capture screenshot: {e}")
        import traceback
        traceback.print_exc()
        return None

@pytest.mark.smoke
def test_BonusBuy(extra):
    """
    Happy Flow - Bonus Buy Transaction
    
    Complete happy flow test including:
    - Login to POS application
    - Adding items using EAN codes
    - Loyalty validation
    - Cash payment processing
    """
    
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
 
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash5", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20) # Increased timeout
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"✓ Successfully connected to application: '{application_window_title}'")
        time.sleep(1)  # Wait for UI to settle
        capture_screenshot("Step 1: Login Complete", extra)
    except Exception as e:
        print(f"❌ Failed to connect or log in to the POS application: {e}")
        capture_screenshot("Step 1: Login Failed", extra)
        pytest.fail(f"Failed to connect or log in: {e}")
    
    
    # --- Step 2: Add first item ---
    print("\n--- Step 2: Add first item (EAN: 9300624016540) ---")
    if not Kayin_EAN_POS(eans_to_add=["9300624016540"]):
        print("❌ Failed to add item using EAN code")
        capture_screenshot("Step 2: Add First Item Failed", extra)
        pytest.fail("Failed to add first item")
    print("✓ First item added successfully")
    time.sleep(2)
    capture_screenshot("Step 2: First Item Added", extra)
    time.sleep(3)

    # --- Step 3: Add second item ---
    print("\n--- Step 3: Add second item (EAN: 1220000062412) ---")
    if not Kayin_EAN_POS(eans_to_add=["1220000062412"]):
        print("❌ Failed to add item using EAN code")
        capture_screenshot("Step 3: Add Second Item Failed", extra)
        pytest.fail("Failed to add second item")
    print("✓ Second item added successfully")
    time.sleep(2)
    capture_screenshot("Step 3: Second Item Added", extra)
    time.sleep(3)

    # --- Step 4: Validate Basket Contents ---
    print("\n--- Step 4: Verifying basket details ---")
    if not get_basket_info():
        print("❌ Failed to verify basket contents")
        capture_screenshot("Step 4: Basket Verification Failed", extra)
        pytest.fail("Failed to verify basket contents")
    print("✓ Basket verified successfully")
    time.sleep(1)
    capture_screenshot("Step 4: Basket Verified", extra)

    # --- Step 5: Validate loyalty card and handle customer popup ---
    print("\n--- Step 5: Validate loyalty card and handle customer popup ---")
    if not validate_loyalty_card():
        print("❌ Failed to get Customer Screen Info")
        capture_screenshot("Step 5: Loyalty Validation Failed", extra)
        pytest.fail("Failed to validate loyalty card")

    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("✓ Navigated to Loyalty Mode")

    time.sleep(2)  # Wait for the UI to update after clicking OK
    if not handle_customer_popup(app, customer_number=None):
        print("❌ Failed to handle customer number popup")
        capture_screenshot("Step 5: Customer Popup Failed", extra)
        pytest.fail("Failed to handle customer popup")
    print("✓ Loyalty validation completed")
    time.sleep(2)
    capture_screenshot("Step 5: Loyalty Complete", extra)
    time.sleep(3)

    # --- Step 6: Process cash tender payment ---
    print("\n--- Step 6: Process cash tender payment ---")
    if not process_tender(tender_name="Cash"):
        print("❌ Failed to process cash tender payment")
        capture_screenshot("Step 6: Cash Tender Failed", extra)
        pytest.fail("Failed to process cash tender")
    print("✓ Cash tender initiated")
    time.sleep(3)

    if not process_tenders(app, tender_to_select="Cash"):
        print("❌ Failed cash tender completion")
        capture_screenshot("Step 6: Cash Tender Completion Failed", extra)
        pytest.fail("Failed to complete cash tender")
    print("✓ Cash tender completed")
    time.sleep(2)
    capture_screenshot("Step 6: Cash Tender Complete", extra)
    time.sleep(1)

    # --- Step 7: Handle payment completion popups ---
    print("\n--- Step 7: Handle payment completion popups ---")
    if not handle_Any_popup(specific_button="Close"):
        print("❌ popup not handled")

    if not handle_Any_popup(specific_button="Yes"):
        print("❌ Failed to handle any popup")
        capture_screenshot("Step 7: Popup Handling Failed", extra)
        pytest.fail("Failed to handle popup")
    print("✓ Popups handled successfully")
    time.sleep(2)
    capture_screenshot("Step 7: Popups Handled", extra)
    time.sleep(1)

    # --- Step 8: Close cash drawer ---
    print("\n--- Step 8: Close cash drawer ---")
    from Scripts.POS_Workspace.Components.Common_components.cashDrawer import cashdrawer_move_and_close
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("❌ Failed to move and close the cash drawer")
        capture_screenshot("Step 8: Cash Drawer Close Failed", extra)
        pytest.fail("Failed to close cash drawer")
    print("✓ Cash drawer closed successfully")
    time.sleep(2)
    capture_screenshot("Step 8: Cash Drawer Closed", extra)
    
    print("\n--- All tasks completed successfully in paid out process! --- 🎉")

# --- Execute the test ---
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--html=report.html", "--self-contained-html"])
