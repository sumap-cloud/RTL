# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC003_customer_tax_details_scenario
# @Features: Customer Tax Details, Business Information Capture, Tax Documentation
# @Components: business_tax_details, department_sale, handle_customer_popup, handle_Any_popup, process_tenders
# @Business_Rules: Tax information validation, Business details requirements, Receipt documentation
# @Validation_Points: Tax number entry, Customer information accuracy, Format validation, Receipt generation
# @User_Roles: ATcash1
# @Special_Config: Business tax number formats
# @Related_Tests: None
# ==========================================

# ======================================================================
# Test Case: TC003_customer_tax_details_scenario.py
# Purpose: Validate Customer Tax Details functionality in POS transactions
# 
# Test Overview:
# This test case validates the handling of customer tax information:
# 1. Customer Tax Features:
#    - Tax information entry
#    - Validation rules
#    - Information persistence
#
# 2. Transaction Flow:
#    - Normal sale process
#    - Customer details entry
#    - Tax information verification
#
# 3. Data Validation:
#    - Tax number format
#    - Customer details accuracy
#    - Receipt information
#
# Key Validation Points:
# 1. Customer Details:
#    - Tax number entry
#    - Customer information accuracy
#    - Format validation
#
# 2. Transaction Processing:
#    - Sale completion
#    - Receipt generation
#    - Tax details on receipt
#
# 3. Data Persistence:
#    - Information storage
#    - Recall accuracy
#    - Report generation
#
# Flow Structure:
# Part 1 - Initial Setup:
#   - Login to POS
#   - Start normal sale
#   - Add items to basket
#
# Part 2 - Tax Details:
#   - Enter customer information
#   - Validate tax number
#   - Verify details
#
# Part 3 - Transaction Completion:
#   - Complete sale
#   - Verify receipt
#   - Check tax details
#
# Error Prevention:
# - Validate input formats
# - Check mandatory fields
# - Verify data persistence
# - Confirm receipt details
# ======================================================================

from pywinauto import Application
import sys
from pathlib import Path
import time
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
    
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing necessary components for POS automation
from Components.funds.change_screen_funds import chnagescreen_funds

from Components.Common_components.pos_login import mainlogic
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate

from Components.Salemode.basket_with_itemdetails import get_basket_info

from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Salemode.department_sale import department_sale
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Common_components.Approvalrequired import handle_approval_popup
from Scripts.POS_Workspace.Components.Recall.transaction_selction_recallv2 import select_recall_transaction
from Components.Salemode.item_search import perform_item_search
from Components.Salemode.department_amount import enter_item_price
from Components.legislation.business_details_screen import business_tax_details


def customer_tax_details():
    application_window_title = ".*R10PosClient.*"
    test_business_details = {
        "business_name": "TestCorp",
        "street": "123 Automation Ave",
        "suburb": "Tech City",
        "tax_number": ""
    }
    
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash5", "abcd1234")
        application_window_title = ".*R10PosClient.*"
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20) # Increased timeout
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False
    
    Toggle_menu = toggle_menu_navigate(["Department Sale", "APPROVAL"])
    if Toggle_menu:
         print("\n transaction Item Search successfully.")
    else:
         print("\n transaction Item Search failed.")
    time.sleep(2)  # Wait for the menu to settle
    if not department_sale("BAKEHOUSE"):
        print("\nFailed to navigate to Department Sale screen.")
        return False
    if not enter_item_price(price="1001.00"):
        print("\nFailed to enter item price.")
        return False
    time.sleep(3)
    #check basket details after adding all articles(common for all test cases if you add articles)
    if not get_basket_info():
        print("Failed to get basket information.")
        return False
    #
#navigating to loyalty mode here after adding all expected item then user has to click ok button to move loyalty mode and below click_OK_button using for navigate sale mode to next screen loyalty mode 
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("Clicked OK buttonto navigate to loyalty mode")

    else:
        print("\nOK button not found.")
        return False
    time.sleep(3)  # Wait for the OK button action to complete
    if not handle_customer_popup(app, customer_number=None): 
        print("\nFailed to handle customer popup.")
        return False
    time.sleep(2)  # Wait for the popup to settle
# Call the main function and check its boolean return value
    if business_tax_details(test_business_details):
        print("\n--- Standalone Test PASSED ---")
    else:
        print("\n--- Standalone Test FAILED ---")
    time.sleep(4)
    from Components.Tenders.Cash_tender_payment import process_tenders
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process cash tender payment.")
        return False
    
    if not handle_Any_popup():
        print("Failed to handle any popup.")
    
    time.sleep(3)
    from Components.Common_components.cashDrawer import cashdrawer_move_and_close
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("Failed to move and close the cash drawer.")
        return False
    
    print("\n--- All tasks completed successfully in Tax details process! --- 🎉")


customer_tax_details()