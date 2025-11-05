# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC005_loyalty_details_scenario
# @Features: Loyalty Card Validation, Member Details Processing, Points Calculation
# @Components: handle_customer_popup, validate_loyalty_card, click_member_card_and_validate, process_tenders
# @Business_Rules: Member identification requirements, Card validation, Points allocation
# @Validation_Points: Card number validation, Member profile display, Points calculation, Receipt documentation
# @User_Roles: ATcash5
# @Special_Config: Loyalty card formats, Member tier configuration
# @Related_Tests: TC003_loyalty_basic_scenario_ai
# ==========================================

# ======================================================================
# Test Case: TC005_loyalty_details_scenario.py
# Purpose: Validate Advanced Loyalty Features and Member Details Processing
# 
# Test Overview:
# This test case validates the POS system's advanced loyalty functionality
# including member details, points calculation, and special promotions:
#
# 1. Member Processing:
#    - Member identification
#    - Profile validation
#    - Points balance
#    - Member tier handling
#
# 2. Points Features:
#    - Base points calculation
#    - Bonus points rules
#    - Points redemption
#    - Tier multipliers
#
# 3. Promotion Management:
#    - Member-specific offers
#    - Tier-based discounts
#    - Promotional multipliers
#    - Combo offers
#
# Flow Structure:
# Part 1 - Member Setup:
#   - Member card entry
#   - Profile validation
#   - Points verification
#
# Part 2 - Transaction Processing:
#   - Add qualifying items
#   - Apply promotions
#   - Calculate points
#
# Part 3 - Completion:
#   - Points allocation
#   - Receipt generation
#   - Member update
#
# Key Validation Points:
# 1. Member Details:
#    - Card validation
#    - Profile accuracy
#    - Tier status
#
# 2. Points Processing:
#    - Calculation accuracy
#    - Bonus qualification
#    - Redemption rules
#
# 3. Promotions:
#    - Offer application
#    - Discount calculation
#    - Combo validation
#
# Error Prevention:
# - Card validation
# - Points verification
# - Promotion rules
# - Receipt accuracy
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
from Components.Salemode.department_sale import department_sale
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Common_components.Approvalrequired import handle_approval_popup
from Scripts.POS_Workspace.Components.Recall.transaction_selction_recallv2 import select_recall_transaction
from Components.Salemode.item_searchv2 import perform_item_search
from Components.Salemode.department_amount import enter_item_price
from Components.Loyalty.validate_loyalty_card import validate_loyalty_card
from Components.Salemode.gs1_manual_entry import automate_gs1_screen
from Components.Loyalty.member_card_details import click_member_card_and_validate

def loyaltycard_validation():
    application_window_title = ".*R10PosClient.*"
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
    
    if not click_plu_path(["Heavy & Misc", "Soft Drinks (10 Pack)", "coke z/s 10pk"]):
        print("Failed to click PLU path for Apple Mi Apple 1Kg Punnet.")
        return 
    time.sleep(3)  # Wait for the UI to update after clicking PLU

    Toggle_menu = toggle_menu_navigate(["Department Sale", "APPROVAL"])
    if Toggle_menu:
         print("\n transaction Item Search successfully.")
    else:
         print("\n transaction Item Search failed.")
    time.sleep(2)  # Wait for the menu to settle
    if not department_sale("BAKEHOUSE"):
        print("\nFailed to navigate to Department Sale screen.")
        return False
    if not enter_item_price(price="11.00"):
        print("\nFailed to enter item price.")
        return False
    time.sleep(3)

    click_OK_button = win.child_window(title="OK", control_type="Button")
    if click_OK_button.exists(timeout=5):
        click_OK_button.click_input()
    else:
        print("\nOK button not found.")
        return False
    time.sleep(3)
    if not handle_customer_popup(app, "9344402191258"): 
        print("\nFailed to handle customer popup.")
        return False
    time.sleep(2)  # Wait for the popup to settle

    if not validate_loyalty_card():
        print("\n membercar details not captured")
        return False
    time.sleep(3)
    if not click_member_card_and_validate():
        print("\n membercard not validated")
        return False
    from Components.Tenders.Cash_tender_payment import process_tenders
    if not process_tenders(app, tender_to_select="Cash"):
        print("Failed to process cash tender payment.")
        return False
    
    if not handle_Any_popup():
        print("Failed to handle any popup.")
        return False
    time.sleep(3)
    from Components.Common_components.cashDrawer import cashdrawer_move_and_close
    if not cashdrawer_move_and_close(status_to_set="close"):
        print("Failed to move and close the cash drawer.")
        return False
# #9344402191258

loyaltycard_validation()