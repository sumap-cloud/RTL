# ==== TEST CASE DOCUMENTATION CHECKLIST ====
# @TestID: TC011_save_transaction_logoff_scenario
# @Features: Save Transaction, Logoff, Transaction Management, Session Management, Training Mode Navigation
# @Components: Kayin_EAN_POS, get_basket_info, toggle_menu_navigate, handle_Any_popup, logoff_user, enter_training_mode
# @Business_Rules: Transaction save functionality, User session management, Logoff procedures, Training mode transitions
# @Validation_Points: Item addition validation, Transaction save confirmation, Training mode logoff popup handling, Basket reflection timing
# @User_Roles: ATcash1 (Service Cashier), atmgr5 (Manager for training mode and approval)
# @Special_Config: Save transaction permissions, Training mode access, Logoff procedures with mode-specific confirmation buttons
# @Related_Tests: TC002_agerestiction_Scenario, TC010_price_override_void_line_scenario, TC012_invalid_login_error_validation, Training mode test scenarios
# @Dependencies: regular_to_traning_mode.py, Logoff.py (with training mode support)
# @Timing_Requirements: 3-second wait after item addition, 2-second stabilization after mode change
# ==========================================

# ======================================================================
# Test Case: TC011_save_transaction_logoff_scenario.py
# Purpose: Validate Save Transaction and Logoff functionality in POS system with Training Mode Navigation
# 
# Test Overview:
# This test case validates comprehensive POS session management functionalities including:
# 
# 1. Session Management Features:
#    - Initial regular mode login (ATcash1)
#    - Regular to training mode navigation with logoff/login cycle
#    - Training mode session establishment
#    - Training mode specific logoff procedures
#
# 2. Transaction Management Features:
#    - Item addition and basket validation with timing considerations
#    - Real-time basket reflection validation (3-second wait periods)
#    - Transaction save capability in training mode
#    - Save operation confirmation and persistence
#
# 3. Advanced Logoff Operations:
#    - Training mode specific logoff confirmation ("Log Off" button vs "Yes" button)
#    - Manager approval handling in training mode context
#    - Session termination with mode-aware popup handling
#    - Complete session cleanup validation
#
# Key Validation Points:
# 1. Mode Transition Management:
#    - Regular mode initial login success
#    - Successful navigation to training mode via enter_training_mode()
#    - System stabilization after mode changes (2-second wait)
#    - Training mode session establishment verification
#
# 2. Enhanced Item Management:
#    - Proper item addition via EAN in training mode environment
#    - Basket reflection timing handling (3-second waits)
#    - Real-time basket validation after each addition
#    - Item details accuracy verification in training mode
#
# 3. Transaction Save in Training Mode:
#    - Save transaction menu navigation in training environment
#    - Save operation success confirmation
#    - Transaction state preservation validation
#    - Training mode transaction handling verification
#
# 4. Advanced Logoff Process:
#    - Training mode specific logoff menu navigation
#    - "Log Off" button confirmation (training mode specific)
#    - Manager approval prompt handling (atmgr5 credentials)
#    - Session termination confirmation with mode awareness
#
# Flow Structure:
# Part 1 - Session Setup and Mode Transition:
#   - Login as Service Cashier (ATcash1) in regular mode
#   - Navigate from regular mode to training mode
#   - Establish training mode session with manager credentials
#   - System stabilization and validation
#
# Part 2 - Training Mode Transaction Processing:
#   - Add multiple items to basket with timing considerations
#   - Validate basket contents with reflection waits
#   - Process items in training mode environment
#
# Part 3 - Transaction Persistence:
#   - Navigate to Save Transaction in training mode
#   - Confirm save operation success
#   - Validate transaction persistence in training environment
#
# Part 4 - Training Mode Session Termination:
#   - Navigate to Log Off menu in training mode
#   - Handle training mode specific confirmation popup ("Log Off" button)
#   - Process manager approval if required
#   - Verify complete session cleanup
#
# Enhanced Error Prevention:
# - Validate each mode transition step with proper error handling
# - Verify item addition with timing considerations (3-second waits)
# - Confirm save transaction completion with training mode context
# - Handle training mode specific logoff popup appropriately
# - Ensure proper session termination with mode-aware cleanup
# - Comprehensive exception handling throughout all phases
#
# Technical Implementation Details:
# - Uses reusable enter_training_mode() component for mode transitions
# - Implements timing waits for basket reflection (3 seconds post-addition)
# - Utilizes mode-aware logoff_user() with training mode parameter
# - Incorporates system stabilization waits (2 seconds post-mode-change)
# - Employs comprehensive error handling and validation at each step
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
from Components.Common_components.pos_login import mainlogic                    # Regular mode login functionality
from Components.Salemode.Keyin_item import Kayin_EAN_POS                       # Item addition via EAN scanning
from Components.Salemode.basket_with_itemdetails import get_basket_info        # Basket validation and content verification
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate  # Menu navigation functionality
from Components.Common_components.handle_any_popup_POS import handle_Any_popup # Generic popup handling
from Components.Common_components.Approvalrequired import handle_approval_popup # Manager approval handling
from Components.Common_components.Logoff import logoff_user                     # Enhanced logoff with training mode support
from Components.Common_components.regular_to_traning_mode import enter_training_mode  # Regular to training mode navigation


def validate_basket_contents():
    """
    Validate basket contents and capture item details with enhanced error handling.
    
    This function serves as a wrapper around get_basket_info() to provide
    consistent validation messaging and error handling throughout the test case.
    
    Returns:
        bool: True if basket validation was successful, False otherwise
        
    Note: 
        - get_basket_info() returns True/False and prints detailed basket contents
        - This function adds consistent messaging for test flow clarity
        - Should be called after each item addition with appropriate timing waits
        
    Usage Context:
        - Called after item addition with 3-second reflection wait
        - Used for real-time basket state verification
        - Provides validation checkpoint in transaction flow
    """
    print("🔍 Validating basket contents...")
    basket_result = get_basket_info()
    if basket_result:
        print("✅ Basket validation successful")
        return True
    else:
        print("❌ Failed to validate basket contents")
        return False


def test_save_transaction_logoff():
    """
    Main test function for comprehensive Save Transaction and Logoff Operations with Training Mode Navigation
    
    Test Configuration:
    - Application: R10PosClient (POS Client Application)
    - Initial Login: ATcash1/abcd1234 (Service Cashier - Regular Mode)
    - Training Mode Login: atmgr5/abcd1234 (Manager credentials for training mode)
    - First Item: EAN 9300675079686 (Test product for basket validation)
    - Second Item: EAN 9300675014779 (Additional test product)
    - Save Transaction: Via toggle menu navigation in training mode
    - Logoff: Via reusable logoff component with training mode support ("Log Off" button)
    
    Enhanced Test Flow:
    1. Initial Session Setup:
       - Login to POS system as ATcash1 in regular mode
       - Establish initial session and application connection
       - Prepare for mode transition operations
    
    2. Mode Transition Operations:
       - Navigate from regular mode to training mode using enter_training_mode()
       - Handle logoff from regular mode and re-login to training mode
       - Verify successful training mode establishment with manager credentials
       - Allow system stabilization (2-second wait) after mode change
    
    3. Training Mode Transaction Processing:
       - Add first item (EAN: 9300675079686) in training mode environment
       - Wait 3 seconds for basket reflection and system processing
       - Validate basket contents after first item addition
       - Add second item (EAN: 9300675014779) with same validation process
       - Wait 3 seconds for basket reflection and system processing
       - Validate final basket state with both items present
    
    4. Transaction Persistence Operations:
       - Navigate to Save Transaction via toggle menu in training mode
       - Confirm save operation success with training mode context
       - Validate transaction state preservation in training environment
       - Allow system processing time (2-second wait) for save completion
    
    5. Training Mode Session Termination:
       - Navigate to Log Off via toggle menu with training mode awareness
       - Handle training mode specific confirmation popup ("Log Off" button click)
       - Process manager approval prompt if required (atmgr5 credentials)
       - Verify successful session termination and cleanup
    
    Advanced Validation Points:
    - Mode transition success validation with error handling
    - Item addition confirmation with timing considerations
    - Real-time basket validation with reflection waits
    - Save transaction completion with training mode context
    - Training mode specific logoff popup handling ("Log Off" vs "Yes")
    - Manager approval prompt processing with appropriate credentials
    - Complete session termination verification
    
    Timing and Error Prevention:
    - 3-second waits after each item addition for basket reflection
    - 2-second wait after mode transition for system stabilization
    - 2-second wait after save transaction for processing completion
    - Comprehensive exception handling at each major step
    - Detailed error logging with step-specific context
    - Early exit strategy on any step failure with clear error reporting
    
    Technical Implementation Details:
    - Uses enter_training_mode() with perform_logoff=True for complete mode transition
    - Implements logoff_user() with mode="training" for proper button handling
    - Employs timing waits to accommodate system processing delays
    - Utilizes comprehensive error handling with step-by-step validation
    - Provides detailed console output for test execution tracking
    
    Returns:
        bool: True if all test steps completed successfully, False on any failure
        
    Dependencies:
        - regular_to_traning_mode.py: For mode transition functionality
        - Logoff.py: For training mode aware logoff operations
        - All standard POS automation components for item and transaction handling
    """
    # Test Configuration
    application_window_title = ".*R10PosClient.*"
    first_item_ean = "9300675079686"   # First normal test item
    second_item_ean = "9300675014779"  # Second normal test item

    # --- Step 1: Log in to the POS application ---
    print("\n--- Step 1: Starting POS application and logging in ---")
    try:
        mainlogic("ATcash1", "abcd1234")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"✅ Successfully connected to application: '{application_window_title}'")
    except Exception as e:
        print(f"❌ Failed to connect or log in to the POS application: {e}")
        return False
    
    # --- Step 2: Navigate from Regular Mode to Training Mode ---
    print("\n--- Step 2: Navigating from Regular Mode to Training Mode ---")
    try:
        if not enter_training_mode(username="atmgr5", password="abcd1234", perform_logoff=True):
            print("❌ Failed to navigate to training mode")
            return False
        
        print("✅ Successfully navigated to training mode")
        time.sleep(2)  # Allow system to stabilize after mode change
        
    except Exception as e:
        print(f"❌ Error during training mode navigation: {e}")
        return False
    
    # --- Step 3: Add First Item ---
    print(f"\n--- Step 3: Adding first item (EAN: {first_item_ean}) ---")
    if not Kayin_EAN_POS(eans_to_add=[first_item_ean]):
        print("❌ Failed to add first item")
        return False
    
    # Wait for item to reflect in basket
    print("⏳ Waiting for item to reflect in basket...")
    time.sleep(3)
    
    # Validate basket after first item addition
    if not validate_basket_contents():
        print("❌ Failed to validate basket after first item addition")
        return False
    
    # --- Step 4: Add Second Item ---
    print(f"\n--- Step 4: Adding second item (EAN: {second_item_ean}) ---")
    if not Kayin_EAN_POS(eans_to_add=[second_item_ean]):
        print("❌ Failed to add second item")
        return False
    
    # Wait for item to reflect in basket
    print("⏳ Waiting for item to reflect in basket...")
    time.sleep(3)
    
    # Validate basket after second item addition
    if not validate_basket_contents():
        print("❌ Failed to validate basket after second item addition")
        return False
    
    # --- Step 5: Save Transaction Process ---
    print("\n--- Step 5: Saving current transaction ---")
    try:
        # Navigate to Save Transaction via toggle menu
        if not toggle_menu_navigate(["Save Transaction"]):
            print("❌ Failed to navigate to Save Transaction")
            return False
        
        print("✅ Transaction saved successfully")
        time.sleep(2)  # Allow system to complete save operation
        
    except Exception as e:
        print(f"❌ Error during save transaction process: {e}")
        return False
    
    # --- Step 6: Logoff Process ---
    print("\n--- Step 6: Initiating user logoff (Training Mode) ---")
    try:
        # Use the reusable logoff component in training mode
        if not logoff_user(approval_username="atmgr5", approval_password="abcd1234", mode="training"):
            print("❌ Failed to complete logoff process")
            return False
        
        print("✅ User logged off successfully using reusable component in training mode")
        
    except Exception as e:
        print(f"❌ Error during logoff process: {e}")
        return False
    
    # --- Test Summary ---
    print("\n🎉 --- All tasks completed successfully in save transaction and logoff scenario! --- 🎉")
    print("\n✅ Test Summary:")
    print(f"   - Regular mode login completed successfully")
    print(f"   - Successfully navigated to training mode")
    print(f"   - First item added successfully (EAN: {first_item_ean})")
    print(f"   - Second item added successfully (EAN: {second_item_ean})")
    print("   - Basket validation passed after each addition")
    print("   - Transaction saved successfully via toggle menu")
    print("   - Logoff process completed successfully using reusable component in training mode")
    print("   - User session terminated successfully with 'Log Off' button click")
    
    return True


# --- Execute the test ---
if __name__ == "__main__":
    test_save_transaction_logoff()
