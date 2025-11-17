# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC002_agerestiction_Scenario
# @Features: Age Restriction, Save/Recall Transaction, Multiple Item Addition Methods
# @Components: handle_age_restriction, perform_item_search, Kayin_EAN_POS, click_plu_path, recall_transaction, recall_intervention_List
# @Business_Rules: Items marked 18+ require age verification, Age verification persists through transaction save/recall
# @Validation_Points: Age restriction prompt appearance, Verification persistence, Basket integrity during save/recall
# @User_Roles: ATcash5
# @Special_Config: Age restricted products configuration
# @Related_Tests: None
# ==========================================

# ======================================================================
# Test Case: TC002_agerestiction_Scenario.py
# Purpose: Validate Age Restriction functionality with Save/Recall Transaction
# 
# Test Overview:
# This test case validates multiple core POS functionalities:
# 1. Age Restriction Features:
#    - Age verification for 18+ items
#    - Age verification for 21+ items
#    - Multiple verification points (initial sale and recall)
#
# 2. Item Addition Methods:
#    - Item Search (for age-restricted items)
#    - Key-in EAN (direct product code entry)
#    - PLU Menu (category navigation)
#
# 3. Transaction Management:
#    - Save Transaction functionality
#    - Recall Transaction process
#    - Intervention handling
#
# Key Validation Points:
# 1. Age Restriction:
#    - Proper prompt display
#    - Age verification rules
#    - Item description accuracy
#
# 2. Save/Recall:
#    - Transaction persistence
#    - Item details preservation
#    - Intervention resolution
#
# 3. Basket Management:
#    - Item details accuracy
#    - Price verification
#    - Multiple item types handling
#
# Flow Structure:
# Part 1 - Initial Sale Setup:
#   - Login as Service Cashier
#   - Add age-restricted item via Item Search
#   - Handle age verification
#   - Add regular items (EAN and PLU)
#
# Part 2 - Save/Recall Process:
#   - Save transaction
#   - Recall transaction
#   - Handle interventions
#   - Re-verify age restrictions
#
# Part 3 - Transaction Completion:
#   - Handle loyalty
#   - Process payment
#   - Handle receipt and drawer
#
# Error Prevention:
# - Validate each item addition
# - Verify age restriction prompts
# - Ensure proper intervention handling
# - Confirm transaction states
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
from Components.funds.change_screen_funds import chnagescreen_funds

from Components.Common_components.pos_login import mainlogic
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Salemode.item_search import perform_item_search
from Components.Salemode.PLUMenu import click_plu_path
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Recall.recall_transction import recall_transaction
from Components.Recall.transaction_selction_recall import find_transaction
from Components.Recall.recall_intervention_List import solve_intervention
from Components.legislation.ageRestriction_window import handle_age_restriction
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup

from Components.Common_components.handle_any_popup_POS import handle_Any_popup

from Scripts.POS_Workspace.Components.Recall.transaction_selction_recallv2 import select_recall_transaction

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



@allure.epic("POS System Testing")
@allure.feature("Age Restriction & Transaction Management")
@allure.story("Age Restriction with Save/Recall Transaction")
@allure.title("TC002 - Validate Age Restriction functionality with Save/Recall Transaction")
@allure.description("""
This test validates multiple core POS functionalities:
- Age verification for 18+ items
- Item addition methods (Search, EAN, PLU)
- Transaction save/recall process
- Intervention handling
""")
@allure.severity(allure.severity_level.CRITICAL)
@allure.testcase("TC002_agerestiction_Scenario")
def test_AgeRestriction():
    """
    Main test function for Age Restriction and Transaction Management
    
    Test Configuration:
    - Application: R10PosClient
    - Login: ATcash5 (Service Cashier)
    - Age Restricted Item: Henri Wintermans Cigars (18+)
    - Additional Items: Regular items via EAN and PLU
    
    Test Flow:
    1. Initial Sale Process:
       - Login to POS
       - Add age-restricted item via Item Search
       - Verify age restriction prompt
       - Add additional items (EAN + PLU)
       - Verify basket details
    
    2. Save/Recall Process:
       - Save transaction
       - Recall transaction
       - Handle interventions
       - Re-verify age restrictions
    
    3. Transaction Completion:
       - Handle loyalty flow
       - Process cash payment
       - Handle receipt and drawer
    
    Validation Points:
    - Age restriction prompt display
    - Item details accuracy
    - Transaction persistence
    - Intervention handling
    - Payment processing
    
    Error Prevention:
    - Verify each navigation step
    - Validate item additions
    - Check age restriction handling
    - Confirm transaction states
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    toggle_menu_navigate_path = ["Save Transaction"]  # Save transaction path
    item_to_search_for = "hw cigars"  # Age-restricted item
    item_to_select_from_list = "Henri Wintermans Cf Creme Cigars 10pk"  # Full item name
   
    
    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting the main application and logging in ---")
    try:
        mainlogic("ATcash5", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20) # Increased timeout
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"Failed to connect or log in to the POS application: {e}")
        return False
    
    # --- Step 2: Add Age Restricted Item via Item Search ---
    print("\n--- Step 2: Adding age-restricted item through Item Search ---")
    # Navigate to Item Search in toggle menu - this is one of the four ways to add items
    Toggle_menu = toggle_menu_navigate(["Item Search"])
    if Toggle_menu:
         print("✓ Navigated to Item Search successfully")
    else:
         print("❌ Failed to navigate to Item Search")
         return False

    # Search for age-restricted item (cigars - requires 18+ verification)
    if not perform_item_search(item_to_search_for, item_to_select_from_list):
        print("❌ Failed to find and select the age-restricted item")
        return False
    
    time.sleep(4)  # Wait for age restriction popup to appear

    # Handle the age restriction verification window
    # This appears immediately after selecting an age-restricted item
    if not handle_age_restriction(date_of_birth=None):
        print("❌ Failed to handle age restriction verification")
        return False

    # --- Step 3: Add Additional Items Using Different Methods ---
    print("\n--- Step 3: Adding items via different methods ---")
    
    # Method 1: Key-in EAN (direct product code entry)
    # This is useful when you have the exact product code
    if not Kayin_EAN_POS(eans_to_add=["8720400000210"]):
        print("❌ Failed to add item using EAN code")
        return False
    
    # Method 2: PLU Menu Navigation (category-based selection)
    # Navigate through: Heavy & Misc > Soft Drinks (10 Pack) > specific item
    if not click_plu_path(["Heavy & Misc", "Soft Drinks (10 Pack)", "coke z/s 10pk"]):
        print("❌ Failed to add item through PLU menu")
        return False
    time.sleep(2)  # Allow UI to update after PLU selection

    # --- Step 4: Validate Basket Contents ---
    print("\n--- Step 4: Verifying basket details ---")
    # Check all added items, prices, and quantities are correct
    if not get_basket_info():
        print("❌ Failed to verify basket contents")
        return False

    # --- Step 5: Save Transaction Process ---
    print("\n--- Step 5: Saving current transaction ---")
    # Save functionality allows transactions to be paused and resumed later
    # Useful for situations like customer forgot wallet or needs to get additional items
    Toggle_menu = toggle_menu_navigate(["Save Transaction"])
    if Toggle_menu:
        print("✓ Transaction saved successfully")
    else:
        print("❌ Failed to save transaction")
        return False
    time.sleep(2)  # Allow system to complete save operation

    # --- Step 6: Recall Transaction Process ---
    print("\n--- Step 6: Recalling saved transaction ---")
    # Navigate to Recall Transaction in toggle menu
    Toggle_menu = toggle_menu_navigate(["Recall Transaction"])
    if Toggle_menu:
        print("✓ Navigated to Recall Transaction")
    else:
        print("❌ Failed to access Recall Transaction")
        return False
    time.sleep(2)  # Allow UI to update

    # Three-step recall process:
    # 1. Initiate recall operation
    if not recall_transaction():
        print("❌ Failed to initiate transaction recall")
        return False

    # 2. Select the specific transaction from the list
    if not select_recall_transaction():
        print("❌ Failed to select transaction from recall list")
        return False

    # 3. Handle any interventions (like age restrictions) that need re-verification
    if not solve_intervention():
        print("❌ Failed to handle recall interventions")
     
    # --- Step 7: Re-handle Age Restriction ---
    print("\n--- Step 7: Re-verifying age restriction after recall ---")
    # Age restrictions must be re-verified after recall for security
    time.sleep(4)  # Allow time for age restriction popup
    if not handle_age_restriction(date_of_birth=None):
        print("❌ Failed to re-verify age restriction after recall")
        return False
    
    # --- Step 8: Additional Item Entry ---
    print("\n--- Step 8: Adding additional items after recall ---")
    time.sleep(3)  # Wait for UI stabilization
    if not Kayin_EAN_POS(eans_to_add=["8720400000210"]):
        print("❌ Failed to add post-recall items")
        return False

    # --- Step 9: Navigate to Loyalty Mode ---
    print("\n--- Step 9: Transitioning to Loyalty Mode ---")
    # POS requires explicit navigation between modes:
    # Sale Mode -> Loyalty Mode -> Tender Mode
    # This is done by clicking OK in sale mode to proceed to loyalty
    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
        print("✓ Navigated to Loyalty Mode")

    time.sleep(2)  # Wait for the UI to update after clicking OK
    if not handle_customer_popup(app, customer_number=None):
        print("Failed to handle customer number popup.")
        return False
    
    if not handle_Any_popup():
        print("Failed to handle any popup.")
        
    from Components.Tenders.Cash_tender_payment import process_tenders
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process cash tender payment.")
        return False
    # here we will get receipt supressed popup after payment done successfully
   
    if not handle_Any_popup():
        print("Failed to handle any popup.")
       
    time.sleep(3)
    from Components.Common_components.cashDrawer import cashdrawer_move_and_close
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("Failed to move and close the cash drawer.")
        return False
    

    
    print("\n--- All tasks completed successfully in paid out process! --- 🎉")
    return True

# --- Execute the test ---
if __name__ == "__main__":
    test_AgeRestriction()
