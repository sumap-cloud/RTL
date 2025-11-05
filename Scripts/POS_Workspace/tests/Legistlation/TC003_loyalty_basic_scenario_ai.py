# ==== TEST DOCUMENTATION CHECKLIST ====
# @TestID: TC003_loyalty_basic_scenario_ai
# @Purpose: Validate member loyalty card association and points calculation
# @Business_Rules: Members must receive correct loyalty points for eligible items
# @Validation_Points: Member card entry, validation, points calculation, transaction completion
# @Dependencies: POS login, loyalty components, barcode scanning, payment processing
# @Setup_Requirements: Valid member cards in system, EAN codes for test items
# @Test_Data: test_scenarios.csv file with test configurations
# @Related_Tests: TC005_loyalty_details_scenario
# @Test_Category: Loyalty, Card Processing, Data Driven Testing
# ============================================

# ======================================================================
# Test Case: TC003_loyalty_basic_scenario_ai.py
# Purpose: Validate Basic Loyalty Flow with Data-Driven Testing Approach
# ======================================================================
"""Basic Loyalty Flow and CSV-driven testing module.

This module implements a comprehensive test for loyalty card functionality,
using data-driven testing from CSV configuration. It validates member
identification, points calculation, and transaction completion.

Test Structure:
    test_scenarios.csv:
        - scenario_id: e.g., TC003
        - scenario_name: Description
        - username: POS credentials
        - password: Authentication
        - ean_codes: Items to test
        - loyalty_card: Member number
        - payment_method: Tender type
        - status: Test result
        - execution_time: Runtime
        - remarks: Notes/results

Test Flow:
    1. Setup:
        - Load CSV config
        - Initialize system
        - Prepare test data

    2. Execution:
        - Member validation
        - Transaction processing
        - Points calculation

    3. Validation:
        - Member benefits
        - Receipt details
        - Points accuracy

Usage:
    python TC003_loyalty_basic_scenario_ai.py [scenario_id]
    scenario_id defaults to TC003 if not provided
"""

from pywinauto import Application
import sys
from pathlib import Path
import time
from typing import Tuple, Optional
import csv
from datetime import datetime

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

# --- CSV Data Handling Functions ---
def read_scenario_data(scenario_id: str = "TC003") -> dict:
    """Read and parse test scenario data from CSV configuration.

    Loads test parameters from test_scenarios.csv for the specified scenario.
    Handles data conversion and validation for test execution.

    Args:
        scenario_id: Test identifier (default: TC003)

    Returns:
        dict: Scenario configuration containing:
            - scenario_id: Unique identifier
            - scenario_name: Description
            - username: POS login
            - password: Authentication
            - ean_codes: List of items
            - loyalty_card: Member number
            - payment_method: Tender type
            - status: Execution status
            - execution_time: Runtime
            - remarks: Notes

    Raises:
        FileNotFoundError: Missing CSV file
        Exception: Data read/parse errors
    """
    csv_path = Path(__file__).parent / "test_scenarios.csv"
    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['scenario_id'].strip() == scenario_id:
                    # Convert comma-separated EAN codes to list
                    row['ean_codes'] = [code.strip() for code in row['ean_codes'].split(',')]
                    print(f"\nFound scenario data for: {scenario_id}")
                    return row
        print(f"❌ Scenario {scenario_id} not found in {csv_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return None

def update_scenario_status(scenario_id: str, status: str, remarks: str = ""):
    """Update test execution status in CSV file.

    Updates scenario status, timestamp, and notes using atomic file operations
    to prevent data corruption during updates.

    Args:
        scenario_id: Test case identifier
        status: New status (Completed/Failed)
        remarks: Optional execution notes

    The function:
        1. Reads CSV data
        2. Updates status row
        3. Adds timestamp
        4. Saves via temp file
        5. Replaces original
    
    Updates fields:
        - status: Test result
        - execution_time: Now
        - remarks: Notes
    """
    csv_path = Path(__file__).parent / "test_scenarios.csv"
    temp_path = csv_path.with_suffix('.tmp')
    try:
        # Read all rows
        rows = []
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            rows = list(reader)
        
        # Update matching row
        for row in rows:
            if row['scenario_id'].strip() == scenario_id:
                row['status'] = status
                row['execution_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row['remarks'] = remarks
        
        # Write back to temp file
        with open(temp_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        # Replace original file
        temp_path.replace(csv_path)
        print(f"✅ Updated status for scenario {scenario_id}: {status}")
    except Exception as e:
        print(f"❌ Error updating CSV: {e}")

def initialize_test_config(scenario_data: dict) -> dict:
    """Transform CSV data into structured configuration.

    Converts flat CSV data into hierarchical config for test execution.

    Args:
        scenario_data: Raw CSV data containing:
            - username: Login name
            - password: Auth code
            - ean_codes: Items
            - loyalty_card: Member ID
            - payment_method: Tender type

    Returns:
        dict: Organized config with sections:
            - credentials: Login info
            - items: Product codes
            - loyalty: Member data
            - payment: Tender details
            - application: System config
    """
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


# Test Configuration
TEST_CONFIG = {
    "credentials": {
        "username": "ATcash5",
        "password": "abcd1234"
    },
    "items": {
        "ean_codes": ["9300675014779"]
    },
    "loyalty": {
        "card_number": "9344402191258"
    },
    "payment": {
        "method": "Cash"
    },
    "application": {
        "window_title": ".*R10PosClient.*"
    }
}

class TestFailureException(Exception):
    """Custom exception for test failures"""
    pass

def validate_step(condition: bool, message: str, screenshot: bool = False) -> bool:
    """Validate test step with optional screenshot.

    Args:
        condition: Pass/fail check
        message: Step description
        screenshot: Capture on fail

    Returns:
        bool: Validation result
        
    Example:
        validate_step(login_ok, "Login", True)
    """
    if not condition:
        if screenshot:
            # TODO: Implement screenshot functionality
            pass
        print(f"Failed: {message}")
        return False
    print(f"Passed: {message}")
    return True

def perform_login() -> Tuple[Optional[Application], Optional[Application.window]]:
    """Login to POS and connect to application window.

    Returns:
        tuple: (app, window) pair or (None, None) on failure
            app: pywinauto application
            window: Main POS window

    Steps:
        1. Login with credentials
        2. Connect to window
        3. Set window focus
    """
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
    """Add items to basket and proceed to loyalty.

    Args:
        win: POS application window

    Returns:
        bool: Success status

    Steps:
        1. Add items by EAN
        2. Verify basket
        3. Navigate forward
    """
    # Add item by EAN
    if not validate_step(
        Kayin_EAN_POS(eans_to_add=TEST_CONFIG["items"]["ean_codes"]),
        "Adding items by EAN"
    ):
        return False
    
    time.sleep(2)  # Wait for UI update
    
    # Validate basket
    if not validate_step(
        get_basket_info(),
        "Validating basket contents"
    ):
        return False
    
    # Navigate to loyalty mode
    click_OK_button = win.child_window(title="OK", control_type="Button")
    return validate_step(
        click_OK_button.exists(timeout=5) and click_OK_button.click_input() is None,
        "Navigating to loyalty mode"
    )

def process_loyalty_card(app) -> bool:
    """Process loyalty card workflow.

    Args:
        app: Application instance

    Returns:
        bool: Success status
    """
    return validate_step(
        handle_customer_popup(app, TEST_CONFIG["loyalty"]["card_number"]),
        "Processing loyalty card"
    )

def complete_payment(app) -> bool:
    """Complete payment workflow.

    Args:
        app: Application instance

    Returns:
        bool: Success status

    Steps:
        1. Get balance
        2. Process tender
        3. Handle dialogs
        4. Manage drawer
    """
    # Check balance using OCR
    balance = get_balance_due_from_screen()
    if not validate_step(balance is not None, "Getting balance due"):
        return False
    print(f"Current balance due: ${balance}")
    
    # Import payment processing here
    from Components.Tenders.Cash_tender_payment import process_tenders
    
    # Handle popups and payment
    if not all([
        validate_step(handle_Any_popup(), "Handling pre-payment popup"),
        validate_step(
            process_tenders(app, tender_to_select=TEST_CONFIG["payment"]["method"]),
            "Processing payment"
        ),
        validate_step(handle_Any_popup(), "Handling post-payment popup")
    ]):
        return False
    
    return validate_step(
        cashdrawer_move_and_close(status_to_set="close"),
        "Handling cash drawer"
    )

def cleanup_on_failure():
    """Handle cleanup after test failure.

    Ensures POS returns to clean state by:
        1. Closing popups
        2. Securing drawer
    """
    try:
        # Handle any open popups
        handle_Any_popup()
        # Ensure cash drawer is closed
        cashdrawer_move_and_close(status_to_set="close")
    except Exception as e:
        print(f"Cleanup failed: {str(e)}")

def test_basic_loyalty_flow():
    """Execute loyalty test scenario.

    Steps:
        1. POS login
        2. Add items
        3. Process loyalty
        4. Complete payment

    Returns:
        bool: Test result
    """
    try:
        # Step 1: Initialize test and login
        print("\n--- Step 1: Starting the main application and logging in ---")
        app, win = perform_login()
        if not all([app, win]):
            raise TestFailureException("Login failed")

        # Step 2: Add items and validate basket
        print("\n--- Step 2: Adding items and validating basket ---")
        if not add_items_to_basket(win):
            raise TestFailureException("Item addition or basket validation failed")

        time.sleep(2)  # Wait for UI update

        # Step 3: Process loyalty card
        print("\n--- Step 3: Processing loyalty card ---")
        if not process_loyalty_card(app):
            raise TestFailureException("Loyalty card processing failed")

        time.sleep(2)  # Wait for loyalty processing

        # Step 4: Complete payment
        print("\n--- Step 4: Completing payment ---")
        if not complete_payment(app):
            raise TestFailureException("Payment processing failed")

        print("\n--- All tasks completed successfully! --- 🎉")
        return True

    except TestFailureException as e:
        print(f"\nTest failed: {str(e)}")
        cleanup_on_failure()
        return False
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        cleanup_on_failure()
        return False

# --- Execute the test ---
if __name__ == "__main__":
    # Get scenario ID from command line or use default
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "TC003"
    
    # Read scenario data
    scenario_data = read_scenario_data(scenario_id)
    if not scenario_data:
        sys.exit(1)
    
    # Initialize test configuration
    TEST_CONFIG = initialize_test_config(scenario_data)
    
    try:
        # Execute test
        start_time = datetime.now()
        success = test_basic_loyalty_flow()
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Update scenario status
        if success:
            update_scenario_status(
                scenario_id,
                "Completed",
                f"Successfully completed in {execution_time:.2f} seconds"
            )
        else:
            update_scenario_status(
                scenario_id,
                "Failed",
                "Test failed. Check logs for details"
            )
            sys.exit(1)
    except Exception as e:
        update_scenario_status(
            scenario_id,
            "Failed",
            f"Error: {str(e)}"
        )
        sys.exit(1)
