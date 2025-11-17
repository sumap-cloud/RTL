# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC001_paidout
# @Features: Paid Out, Cash Management, Denomination Handling, Financial Controls
# @Components: paidout_Navigation, all_denomination_check, numpad_QTY_funds, capture_cash_summary, delete_summary_funds, total_paid_out, Select_relevent_account_paidout, Paidout_relevent_category_selection, paidout_finalize, chnagescreen_funds, cashdrawer_move_and_close
# @Business_Rules: Denomination entry and validation, Category selection requirements, Reference number tracking, GST handling
# @Validation_Points: Denomination accuracy, Amount calculation, Category selection, Reference capture, Receipt documentation
# @User_Roles: ATcash1
# @Special_Config: Cash drawer operation, Paid out category permissions
# @Related_Tests: TC001_paidout_with_screenshots
# ==========================================

# ======================================================================
# Test Case: TC001_paidout.py
# Purpose: Validate POS Paid Out Functionality and Cash Management
# 
# Test Overview:
# This test case validates the POS system's Paid Out functionality including
# denomination handling, cash management, and accounting categorization:
#
# 1. Cash Management Features:
#    - Denomination entry
#    - Amount validation
#    - Cash drawer handling
#    - Summary verification
#
# 2. Paid Out Process:
#    - Category selection
#    - Reference number entry
#    - GST handling
#    - Account allocation
#
# 3. Financial Controls:
#    - Amount verification
#    - Authorization levels
#    - Documentation
#    - Audit trail
#
# Flow Structure:
# Part 1 - Setup:
#   - POS login with cashier credentials
#   - Navigate to Paid Out function
#   - Verify access rights
#
# Part 2 - Cash Processing:
#   - Enter denominations
#   - Validate amounts
#   - Review summary
#   - Handle corrections
#
# Part 3 - Paid Out Details:
#   - Select category
#   - Enter reference
#   - Process GST
#   - Complete transaction
#
# Key Validation Points:
# 1. Amount Processing:
#    - Denomination accuracy
#    - Total calculation
#    - GST computation
#
# 2. Category Management:
#    - Valid selection
#    - Reference capture
#    - Account allocation
#
# 3. Documentation:
#    - Reference number
#    - Category details
#    - Amount breakdown
#    - GST recording
#
# Error Prevention:
# - Amount validation
# - Category verification
# - Reference checks
# - Drawer management
# ======================================================================

from pywinauto import Application
import sys
from pathlib import Path
import time
import allure
import os
from datetime import datetime

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing necessary components for POS automation
from Components.funds.funds_navigation import paidout_Navigation
from Components.funds.denomOCR_checkall_navigattion import all_denomination_check, navigate_and_click_path
from Components.funds.Numpad_Qty_Funds import numpad_QTY_funds
from Components.funds.Cash_summary_and_Delete import capture_cash_summary, delete_summary_funds
from Components.funds.total_paid_out_funds import total_paid_out
from Components.funds.paid_out_acction_validation import Select_relevent_account_paidout
from Components.funds.Paidout_relevent_category import Paidout_relevent_category_selection
from Components.Common_components.pos_login import mainlogic
from Components.funds.paidout_reference import paidout_finalize
from Components.funds.change_screen_funds import chnagescreen_funds
#from Components.Common_components.cashDrawer import cashdrawer_move_and_close

# --- Helper Functions ---
def setup_screenshot_directory():
    """Create screenshots directory if it doesn't exist"""
    screenshot_dir = Path(__file__).parent / "screenshots"
    screenshot_dir.mkdir(exist_ok=True)
    return screenshot_dir

def capture_screenshot(step_name, description=""):
    """Capture screenshot and attach to allure report"""
    try:
        screenshot_dir = setup_screenshot_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_filename = f"{step_name}_{timestamp}.png"
        screenshot_path = screenshot_dir / screenshot_filename
        
        # Capture screenshot using pyautogui
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save(str(screenshot_path))
        
        # Attach to allure report
        allure.attach.file(
            str(screenshot_path), 
            name=f"Screenshot: {step_name}",
            attachment_type=allure.attachment_type.PNG
        )
        print(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)
    except Exception as e:
        print(f"Failed to capture screenshot: {e}")
        return None

# --- Helper Function for Denomination Entry ---
@allure.step("Enter denomination quantity: {denomination_path} with {quantity}")
def enter_denomination_quantity(win_app, denomination_path, quantity):
    """
    Process denomination entry for Paid Out transaction.
    
    This function handles the complete workflow for entering a specific
    denomination quantity in the Paid Out screen:
    1. Navigation to denomination
    2. Quantity entry
    3. Validation of entry
    
    Args:
        win_app: The main application window instance
        denomination_path (str): Navigation path to denomination (e.g., "Note>$100")
        quantity (str): Quantity to enter for the denomination
        
    Returns:
        bool: True if denomination entry successful, False otherwise
        
    Validation:
        - Proper navigation to denomination
        - Successful quantity entry
        - UI state after entry
        
    Error Handling:
        - Navigation failures
        - Entry errors
        - UI state issues
    """
    print(f"  Attempting to enter {quantity} for '{denomination_path}'...")
    if not navigate_and_click_path(win_app, denomination_path):
        print(f"  Failed to navigate and click on '{denomination_path}'.")
        return False
    if not numpad_QTY_funds(quantity):
        print(f"  Failed to enter quantity '{quantity}' for '{denomination_path}'.")
        return False
    return True

@allure.epic("POS System Testing")
@allure.feature("Cash Management")
@allure.story("Paid Out Functionality")
@allure.title("TC001 - Validate POS Paid Out Functionality and Cash Management")
@allure.description("""
This test validates the complete Paid Out workflow including:
- Login and access verification  
- Denomination entry and validation
- Category selection and reference entry
- GST handling and finalization
""")
@allure.severity(allure.severity_level.CRITICAL)
@allure.testcase("TC001_paidout")
def test_funds_paidout():
    """
    Execute complete Paid Out test scenario with all validations.
    
    This function tests the entire Paid Out workflow including:
    1. Login and access verification
    2. Denomination entry and validation
    3. Category selection and reference entry
    4. GST handling and finalization
    
    Test Configuration:
        - Login: ATcash1 with appropriate permissions
        - Category: Team Recognition (configurable)
        - Reference: TestRef123 (for tracking)
        - GST: $25.50 (for tax calculation)
        
    Validation Steps:
        1. Application Access:
           - Login success
           - Permission verification
           - UI accessibility
           
        2. Denomination Processing:
           - Multiple denomination types
           - Quantity entry
           - Amount calculation
           - Summary verification
           
        3. Transaction Details:
           - Category selection
           - Reference entry
           - GST calculation
           - Final amount validation
           
        4. Completion Checks:
           - Summary capture
           - Drawer handling
           - Documentation
           
    Error Handling:
        - Login failures
        - Navigation issues
        - Entry errors
        - Processing problems
        
    Returns:
        bool: True if all steps complete successfully, False on any failure
    """
    application_window_title = ".*R10PosClient.*"
    paidout_category_name = "Team Recognition"
    paidout_reference_number = "TestRef123"
    paidout_gst_amount = "25.50"

    # --- Step 1: Log in to the POS application ---
    with allure.step("Step 1: Starting the main application and logging in"):
        print("\n--- Step 1: Starting the main application and logging in ---")
        try:
            mainlogic("ATcash1", "abcd1234")
            app = Application(backend="uia").connect(title_re=application_window_title, timeout=20) # Increased timeout
            win = app.window(title_re=application_window_title)
            win.set_focus()
            print(f"Successfully connected to application: '{application_window_title}'")
            allure.attach(f"Connected to: {application_window_title}", name="Application Connection", attachment_type=allure.attachment_type.TEXT)
            capture_screenshot("login_success", "Application login successful")
        except Exception as e:
            print(f"Failed to connect or log in to the POS application: {e}")
            allure.attach(str(e), name="Login Error", attachment_type=allure.attachment_type.TEXT)
            return False

    # --- Step 2: Navigate to PAID OUT account ---
    with allure.step("Step 2: Navigating to the PAID OUT account"):
        print("\n--- Step 2: Navigating to the PAID OUT account ---")
        if not paidout_Navigation(app_title=application_window_title):
            print("Failed to navigate to the 'PAID OUT' account.")
            allure.attach("Navigation failed", name="Navigation Error", attachment_type=allure.attachment_type.TEXT)
            capture_screenshot("navigation_failed", "Failed to navigate to Paid Out")
            return False
        
        if not Select_relevent_account_paidout(win):
            print("Failed to select the 'Paid Out' account after navigation.")
            allure.attach("Account selection failed", name="Account Selection Error", attachment_type=allure.attachment_type.TEXT)
            capture_screenshot("account_selection_failed", "Failed to select Paid Out account")
            return False
        
        capture_screenshot("paid_out_account_selected", "Paid Out account successfully selected")

    # --- Step 3: Check denominations and initial entry ---
    with allure.step("Step 3: Checking all denominations and entering initial quantities"):
        print("\n--- Step 3: Checking all denominations and entering initial quantities ---")
        if not all_denomination_check():
            print("Failed to check all denominations.")
            allure.attach("Denomination check failed", name="Denomination Check Error", attachment_type=allure.attachment_type.TEXT)
            return False
        
        # Using the helper function for repeated denomination entry
        denominations_to_enter_initial = [
            ("Note>$100", "5"),
            ("Coin>$1", "5"),
            ("Roll>20c", "5")
        ]
        for path, qty in denominations_to_enter_initial:
            if not enter_denomination_quantity(win, path, qty):
                capture_screenshot("denomination_entry_failed", f"Failed to enter {path} with {qty}")
                return False # Exit immediately on first failure
        
        capture_screenshot("denomination_entry_complete", "All initial denominations entered successfully")

    # --- Step 4: Capture and verify cash summary ---
    with allure.step("Step 4: Capturing and verifying cash summary"):
        print("\n--- Step 4: Capturing and verifying cash summary ---")
        summary_details = capture_cash_summary(win)
        if not summary_details:
            print("No data captured from the summary to verify. This might indicate an issue.")
            allure.attach("No summary data captured", name="Summary Capture Error", attachment_type=allure.attachment_type.TEXT)
            return False 
        print(f"Cash Summary Captured: {summary_details}")
        allure.attach(str(summary_details), name="Cash Summary Details", attachment_type=allure.attachment_type.TEXT)
        capture_screenshot("cash_summary_captured", "Cash summary details captured")

    # --- Step 5: Delete summary funds and re-enter a denomination ---
    with allure.step("Step 5: Deleting summary funds and re-entering '$100 Note'"):
        print("\n--- Step 5: Deleting summary funds and re-entering '$100 Note' ---")
        if not delete_summary_funds():
            print("Failed to delete summary funds.")
            allure.attach("Failed to delete summary funds", name="Delete Summary Error", attachment_type=allure.attachment_type.TEXT)
            return False

        # Re-entering quantity for Note>$100 after deletion
        if not enter_denomination_quantity(win, "Note>$100", "5"):
            return False

    # --- Step 6: Total paid out funds and click Paid Out button ---
    with allure.step("Step 6: Totaling paid out funds and proceeding to category selection"):
        print("\n--- Step 6: Totaling paid out funds and proceeding to category selection ---")
        if not total_paid_out():
            print("Failed to total paid out funds.")
            allure.attach("Failed to total paid out funds", name="Total Funds Error", attachment_type=allure.attachment_type.TEXT)
            return False

        paid_out_btn = win.child_window(title="Paid Out", control_type="Button")
        if paid_out_btn.exists() and paid_out_btn.is_enabled(): # Check if enabled
            paid_out_btn.click_input()
            print("Clicked 'Paid Out' button.")
        else:
            print("Paid Out button not found or not enabled. Cannot proceed.")
            allure.attach("Paid Out button not found or not enabled", name="Button Error", attachment_type=allure.attachment_type.TEXT)
            return False

    # --- Step 7: Select category and finalize paid out ---
    with allure.step(f"Step 7: Selecting category '{paidout_category_name}' and finalizing paid out"):
        print(f"\n--- Step 7: Selecting category '{paidout_category_name}' and finalizing paid out ---")
        if not Paidout_relevent_category_selection(paidout_category_name):
            print(f"Failed to select the category '{paidout_category_name}'.")
            allure.attach(f"Failed to select category: {paidout_category_name}", name="Category Selection Error", attachment_type=allure.attachment_type.TEXT)
            return False
        
        if not paidout_finalize(paidout_reference_number, paidout_gst_amount):
            print(f"Failed to finalize the paid out with reference '{paidout_reference_number}' and GST '{paidout_gst_amount}'.")
            allure.attach(f"Failed to finalize with ref: {paidout_reference_number}, GST: {paidout_gst_amount}", name="Finalization Error", attachment_type=allure.attachment_type.TEXT)
            return False

    # --- Step 8: Capture final amount and message, then close cash drawer ---
    with allure.step("Step 8: Capturing final details and closing cash drawer"):
        print("\n--- Step 8: Capturing final details and closing cash drawer ---")
        final_details = chnagescreen_funds()
        if not final_details:
            print("Failed to capture final amount and message after paid out.")
            allure.attach("Failed to capture final details", name="Final Details Error", attachment_type=allure.attachment_type.TEXT)
            return False
        print(f"Final Paid Out Details: {final_details}")
        allure.attach(str(final_details), name="Final Paid Out Details", attachment_type=allure.attachment_type.TEXT)
        
        time.sleep(2)  # Wait for the UI to update after finalization
        from Components.Common_components.cashDrawer import cashdrawer_move_and_close
        
        if not cashdrawer_move_and_close(status_to_set="close"):
            print("Failed to close the cash drawer.")
            allure.attach("Cash drawer close failed", name="Cash Drawer Error", attachment_type=allure.attachment_type.TEXT)
            return False
        
        print("\n--- All tasks completed successfully in paid out process! --- 🎉")
        allure.attach("All test steps completed successfully", name="Test Completion", attachment_type=allure.attachment_type.TEXT)
        capture_screenshot("test_completion", "All paid out tasks completed successfully")
        return True

# --- Execute the test ---
if __name__ == "__main__":
    test_funds_paidout()
