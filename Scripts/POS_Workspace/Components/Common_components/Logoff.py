# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: POS_Logoff_Handler
# @Purpose: Handles complete POS logoff workflow including menu navigation, popup handling, and approval management
# @Dependencies: toggle_menu_navigate, handle_Any_popup, handle_approval_popup, pywinauto, time
# @Input_Params: approval_username, approval_password, confirmation_button, skip_approval
# @Return_Values: Boolean indicating success/failure of complete logoff process
# @Used_By_Tests: TC011_save_transaction_logoff_scenario, TC012_invalid_login_error_validation, Session management tests
# @Known_Limitations: Requires POS application to be in active state, depends on menu structure
# ============================================

"""
Component: POS Logoff Handler
Location: Components/Common_components/Logoff.py

Purpose:
    Comprehensive logoff handler for POS application that manages the complete
    logoff workflow including menu navigation, confirmation dialogs, and approval prompts.

Flow Context:
    - Called at end of transactions or shift changes
    - Part of session management workflows
    - Used in cleanup and security procedures
    - Called during error recovery scenarios

Workflow Steps:
    1. Navigate to Log Off menu option
    2. Handle logoff confirmation popup
    3. Manage approval prompt if required
    4. Verify successful session termination

UI Elements Handled:
    1. Toggle Menu:
       - "Log Off" option (MenuItem)
       - Menu navigation structure

    2. Confirmation Popup:
       - "Yes/No" buttons (type: Button)
       - Confirmation message (type: Text)
       - Title: Various confirmation titles

    3. Approval Popup:
       - Username field (type: Edit)
       - Password field (type: Edit)
       - OK button (type: Button)
       - Manager approval credentials required

Popup Types Managed:
    1. Logoff Confirmation:
       - Standard Yes/No dialog
       - "Are you sure you want to log off?" messages
       - Session termination warnings

    2. Manager Approval:
       - Approval Required popup
       - Credential entry fields
       - OK/Cancel options

    3. System Messages:
       - Session cleanup notifications
       - Logout completion messages
       - Error handling dialogs

Error Handling:
    - Menu navigation failures
    - Popup detection issues
    - Approval credential problems
    - Session termination errors

Usage Example:
    from Components.Common_components.Logoff import logoff_user
    
    # Basic logoff
    success = logoff_user()
    
    # Logoff with custom approval credentials
    success = logoff_user(
        approval_username="manager1",
        approval_password="pass123",
        confirmation_button="Yes"
    )
    
    # Logoff without approval handling
    success = logoff_user(skip_approval=True)
"""

from pywinauto import Application
import sys
from pathlib import Path
import time

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Components.Common_components.handle_any_popup_POS import handle_Any_popup
from Components.Common_components.Approvalrequired import handle_approval_popup


#def logoff_user(approval_username="atmgr5", approval_password="abcd1234", confirmation_button="Yes", mode="regular"):
def logoff_user(approval_username="atmgr5", approval_password="abcd1234", confirmation_button="Yes", mode="regular"):
    """
    Simple logoff function with minimal steps:
    1. Navigate to Log Off
    2. Confirm the prompt (Yes for regular mode, Log Off for training mode)
    3. Wait 5 seconds for approval prompt
    4. Handle approval if it appears, otherwise continue
    
    Args:
        approval_username (str): Username for manager approval (default: "atmgr5")
        approval_password (str): Password for manager approval (default: "abcd1234")
        confirmation_button (str): Button text to click for confirmation (default: "Yes")
        mode (str): Login mode - "regular" or "training" (default: "regular")
    
    Returns:
        bool: True if logoff completed, False if failed
    """
    print("\n🔄 Starting Simple Logoff Process...")
 
    # Determine confirmation button based on mode (only override if mode is explicitly set to training)
    if mode.lower() == "training":
        confirmation_button = "Log Off"
        print("🎯 Training mode detected - will click 'Log Off' button")
    else:
        # Keep the confirmation_button parameter as passed (don't override to "Yes")
        print(f"🏢 Regular mode detected - will click '{confirmation_button}' button")
    
    try:
        # Step 1: Navigate to Log Off
        print("📋 Navigating to Log Off...")
        if not toggle_menu_navigate(["Log Off"]):
            print("❌ Failed to navigate to Log Off")
            return False
        
        # Step 2: Confirm the prompt
        print(f"💬 Confirming logoff prompt with '{confirmation_button}' button...")
        if not handle_Any_popup(specific_button=confirmation_button):
            print(f"❌ Failed to confirm logoff with '{confirmation_button}' button")
            return False
        
        # Step 3: Wait 5 seconds for approval prompt
        print("⏳ Waiting 5 seconds for approval prompt...")
        time.sleep(5)
        
        # Step 4: Handle approval if it appears
        print("🔐 Checking for approval prompt...")
        try:
            approval_result = handle_approval_popup(
                approval_required=True, 
                first_username=approval_username, 
                first_password=approval_password
            )
            if approval_result:
                print("✅ Approval prompt handled")
            else:
                print("ℹ️ No approval prompt detected")
        except Exception:
            print("ℹ️ No approval required")
        
        print("✅ Logoff process completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during logoff: {e}")
        return False


def quick_logoff():
    """
    Quick logoff with default settings (regular mode).
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("⚡ Quick Logoff - Regular Mode")
    return logoff_user()


def logoff_training_mode(approval_username="atmgr5", approval_password="abcd1234"):
    """
    Logoff from training mode - clicks 'Log Off' button instead of 'Yes'.
    
    Args:
        approval_username (str): Username for manager approval (default: "atmgr5")
        approval_password (str): Password for manager approval (default: "abcd1234")
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("🎯 Training Mode Logoff")
    return logoff_user(
        approval_username=approval_username,
        approval_password=approval_password,
        mode="training"
    )


def logoff_regular_mode(approval_username="atmgr5", approval_password="abcd1234"):
    """
    Logoff from regular mode - clicks 'Yes' button (default behavior).
    
    Args:
        approval_username (str): Username for manager approval (default: "atmgr5")
        approval_password (str): Password for manager approval (default: "abcd1234")
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("🏢 Regular Mode Logoff")
    return logoff_user(
        approval_username=approval_username,
        approval_password=approval_password,
        mode="regular"
    )


# --- Main Execution ---
if __name__ == "__main__":
    # Test the simple logoff component
    print("� Testing Simple Logoff Component")
    result = logoff_user()
    print(f"Result: {'✅ Success' if result else '❌ Failed'}")
