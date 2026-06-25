# ======================================================================
# Test Case: TC003_loyalty_basic_scenario_ai.py
# Purpose: Validate Basic Loyalty Flow with Data-Driven Testing Approach
# ======================================================================

from pywinauto import Application
import sys
from pathlib import Path
import time
from typing import Tuple, Optional
import csv
from datetime import datetime
import re

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing necessary components for POS automation
from Components.Common_components.pos_login import mainlogic
from Components.Salemode.Keyin_item import Kayin_EAN_POS
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Common_components.cashDrawer import cashdrawer_move_and_close
from Components.Salemode.basket_with_itemdetails import get_basket_info
from Components.Common_components.OCR_balancedue import get_balance_due_from_screen
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from RTLPOSFlow.utils.ReprintReceipt import ReprintReceiptFlow

# --- Global Variables for Data Identification ---
BANNER_NAME = "SM"
ITERATION = "1"
# Automatically takes the filename without .py extension
SCRIPT_TC_ID = Path(__file__).stem 
DATA_FILE = "SaleData.csv"
TRANSACTION_DATA_FILE = "TransactionData.csv" 

# --- CSV Data Handling Functions ---
def read_scenario_data(scenario_id: str = "TC003") -> dict:
    """Read and parse test scenario data from SaleData.csv using Banner, TC_ID, and Iteration."""
    csv_path = Path(__file__).parent / DATA_FILE
    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Match based on Banner, TC_ID, and Iteration
                if (row['Banner'].strip() == BANNER_NAME and 
                    row['TC_ID'].strip() == SCRIPT_TC_ID and 
                    str(row['Iteration']).strip() == str(ITERATION)):
                    
                    ean_list = [code.strip() for code in row['Item_EAN'].split(',')]
                    
                    mapped_row = {
                        'scenario_id': row['TC_ID'],
                        'username': row['Username'],
                        'password': row['Password'],
                        'ean_codes': ean_list,
                        'loyalty_card': row['Card_number'],
                        'payment_method': row['Payment_method'],
                        'status': row.get('status', ''),
                        'execution_time': row.get('execution_time', ''),
                        'remarks': row.get('remarks', '')
                    }
                    print(f"\n✅ Found scenario data in {DATA_FILE} for: {SCRIPT_TC_ID} (Iteration {ITERATION})")
                    return mapped_row

        print(f"❌ No matching row found for Banner: {BANNER_NAME}, TC_ID: {SCRIPT_TC_ID}, Iteration: {ITERATION}")
        return None
    except Exception as e:
        print(f"❌ Error reading {DATA_FILE}: {e}")
        return None

def update_scenario_status(banner: str, tc_id: str, iteration: str, status: str, remarks: str = ""):
    """Update test execution status in SaleData.csv using Banner, TC_ID, and Iteration."""
    csv_path = Path(__file__).parent / DATA_FILE
    temp_path = csv_path.with_suffix('.tmp')
    try:
        rows = []
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            rows = list(reader)
        
        for row in rows:
            if (row['Banner'].strip() == banner and 
                row['TC_ID'].strip() == tc_id and 
                str(row['Iteration']).strip() == str(iteration)):
                row['status'] = status
                row['execution_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row['remarks'] = remarks
        
        with open(temp_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        temp_path.replace(csv_path)
        print(f"✅ Updated status for {tc_id}: {status}")
    except Exception as e:
        print(f"❌ Error updating {DATA_FILE}: {e}")

def update_transaction_logging(banner: str, tc_id: str, iteration: str, store_no: str = None, pos_no: str = None, trans_no: str = None, amount: str = None):
    """Log extracted Store, POS, Trans No, and Total Amount into TransactionData.csv."""
    csv_path = Path(__file__).parent / TRANSACTION_DATA_FILE
    temp_path = csv_path.with_suffix('.tmp')
    try:
        rows = []
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            rows = list(reader)

        updated = False
        current_date = datetime.now().strftime("%Y-%m-%d")
        for row in rows:
            if (row['Banner'].strip() == banner and 
                row['TC_ID'].strip() == tc_id and 
                str(row['Iteration']).strip() == str(iteration)):
                
                # Update only if values are provided (to allow partial updates)
                if store_no is not None: row['Store_No'] = store_no
                if pos_no is not None: row['Pos_No'] = pos_no
                if trans_no is not None: row['Transaction_No'] = trans_no
                if amount is not None: row['TransactionAmount'] = amount
                
                row['Transaction_Data'] = current_date
                updated = True
        
        if updated:
            with open(temp_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            temp_path.replace(csv_path)
            print(f"✅ TransactionData.csv updated (Amount: {amount}, Trans: {trans_no})")
    except Exception as e:
        print(f"❌ Error updating {TRANSACTION_DATA_FILE}: {e}")

def initialize_test_config(scenario_data: dict) -> dict:
    return {
        "credentials": {
            "username": scenario_data['username'],
            "password": scenario_data['password']
        },
        "items": {
            "ean_codes": scenario_data['ean_codes']
        },
        "loyalty": {
            "card_number": scenario_data['loyalty_card']
        },
        "payment": {
            "method": scenario_data['payment_method']
        },
        "application": {
            "window_title": ".*R10PosClient.*"
        }
    }

# Test Configuration - Placeholder (will be overridden in main)
TEST_CONFIG = {}

class TestFailureException(Exception):
    """Custom exception for test failures"""
    pass

def validate_step(condition: bool, message: str, screenshot: bool = False) -> bool:
    if not condition:
        print(f"Failed: {message}")
        return False
    print(f"Passed: {message}")
    return True

def perform_login() -> Tuple[Optional[Application], Optional[Application.window]]:
    try:
        mainlogic(TEST_CONFIG["credentials"]["username"], 
                  TEST_CONFIG["credentials"]["password"])
        
        app = Application(backend="uia").connect(
            title_re=TEST_CONFIG["application"]["window_title"], 
            timeout=20
        )
        win = app.window(title_re=TEST_CONFIG["application"]["window_title"])
        win.set_focus()
        
        return app, win
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return None, None

def add_items_to_basket(win) -> bool:
    if not validate_step(
        Kayin_EAN_POS(eans_to_add=TEST_CONFIG["items"]["ean_codes"]),
        "Adding items by EAN"
    ):
        return False
    
    time.sleep(2) 
    
    if not validate_step(
        get_basket_info(),
        "Validating basket contents"
    ):
        return False
    
    click_OK_button = win.child_window(title="OK", control_type="Button")
    return validate_step(
        click_OK_button.exists(timeout=5) and click_OK_button.click_input() is None,
        "Navigating to loyalty mode"
    )

def process_loyalty_card(app) -> bool:
    return validate_step(
        handle_customer_popup(app, TEST_CONFIG["loyalty"]["card_number"]),
        "Processing loyalty card"
    )

def complete_payment(app) -> Optional[str]:
    """Complete payment and return the captured balance amount."""
    balance = get_balance_due_from_screen()
    if not validate_step(balance is not None, "Getting balance due"):
        return None
    print(f"Current balance due: ${balance}")
    
    # --- UPDATE TransactionAmount BEFORE completing transaction ---
    update_transaction_logging(
        BANNER_NAME, SCRIPT_TC_ID, ITERATION, 
        amount=str(balance)
    )
    
    from Components.Tenders.Cash_tender_payment import process_tenders
    
    if not all([
        validate_step(handle_Any_popup(), "Handling pre-payment popup"),
        validate_step(
            process_tenders(app, tender_to_select=TEST_CONFIG["payment"]["method"]),
            "Processing payment"
        ),
        validate_step(handle_Any_popup(), "Handling post-payment popup")
    ]):
        return None
    
    if validate_step(cashdrawer_move_and_close(status_to_set="close"), "Handling cash drawer"):
        return str(balance)
    return None

def cleanup_on_failure():
    try:
        handle_Any_popup()
        cashdrawer_move_and_close(status_to_set="close")
    except Exception as e:
        print(f"Cleanup failed: {str(e)}")

def test_basic_loyalty_flow() -> Tuple[bool, Optional[str]]:
    """Execute test flow and return (Success_Status, Total_Amount)."""
    app = None
    win = None
    captured_amount = None
    try:
        print("\n--- Step 1: Starting the main application and logging in ---")
        app, win = perform_login()
        if not all([app, win]):
            raise TestFailureException("Login failed")

        print("\n--- Step 2: Adding items and validating basket ---")
        if not add_items_to_basket(win):
            raise TestFailureException("Item addition or basket validation failed")

        time.sleep(2)

        print("\n--- Step 3: Processing loyalty card ---")
        if not process_loyalty_card(app):
            raise TestFailureException("Loyalty card processing failed")

        time.sleep(2)

        print("\n--- Step 4: Completing payment ---")
        captured_amount = complete_payment(app)
        if captured_amount is None:
            raise TestFailureException("Payment processing failed")

        print("\n--- All tasks completed successfully! --- 🎉")
        return True, captured_amount

    except TestFailureException as e:
        print(f"\nTest failed: {str(e)}")
        cleanup_on_failure()
        return False, captured_amount
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        cleanup_on_failure()
        return False, captured_amount
    finally:
        print("\n--- Step 5: Reprinting receipt via toggle menu (always runs) ---")
        try:
            try:
                title_re = TEST_CONFIG.get('application', {}).get('window_title', '.*R10PosClient.*')
            except Exception:
                title_re = '.*R10PosClient.*'

            rep = ReprintReceiptFlow(title_re=title_re)

            if not rep.open_reprint_and_search():
                print("Failed to open Reprint Receipt via toggle menu or connect to POS window")
            else:
                if not rep.open_pos_parameters():
                    print("Failed to open POS Parameters")
                try:
                    store_no, pos_no, trans_no = rep.extract_store_pos_trans()
                    print(f"Store No.: {store_no if store_no else 'Not found'}")
                    print(f"POS No.: {pos_no if pos_no else 'Not found'}")
                    print(f"Trans' No.: {trans_no if trans_no else 'Not found'}")
                    
                    # Log extracted data to TransactionData.csv (updates existing row with Store/POS/Trans)
                    update_transaction_logging(
                        BANNER_NAME, 
                        SCRIPT_TC_ID, 
                        ITERATION, 
                        store_no=str(store_no) if store_no else "N/A", 
                        pos_no=str(pos_no) if pos_no else "N/A", 
                        trans_no=str(trans_no) if trans_no else "N/A"
                    )
                except Exception as ex:
                    print(f"Exception extracting values: {ex}")

            try:
                if rep.click_cancel():
                    print("Clicked Cancel via ReprintReceiptFlow.")
                else:
                    print("Cancel button not found via ReprintReceiptFlow.")
            except Exception as e:
                print(f"Exception during Cancel: {e}")

        except Exception as e:
            print(f"Exception during Reprint Receipt navigation: {e}")


# --- Execute the test ---
if __name__ == "__main__":
    # Get scenario data
    scenario_data = read_scenario_data()
    
    if not scenario_data:
        sys.exit(1)
    
    # Initialize test configuration
    TEST_CONFIG = initialize_test_config(scenario_data)
    
    try:
        # Execute test
        start_time = datetime.now()
        success, final_amount = test_basic_loyalty_flow()
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Update scenario status in SaleData.csv
        if success:
            update_scenario_status(
                BANNER_NAME, SCRIPT_TC_ID, ITERATION,
                "Completed",
                f"Successfully completed in {execution_time:.2f} seconds"
            )
        else:
            update_scenario_status(
                BANNER_NAME, SCRIPT_TC_ID, ITERATION,
                "Failed",
                "Test failed. Check logs for details"
            )
            sys.exit(1)
    except Exception as e:
        update_scenario_status(
            BANNER_NAME, SCRIPT_TC_ID, ITERATION,
            "Failed",
            f"Error: {str(e)}"
        )
        sys.exit(1)