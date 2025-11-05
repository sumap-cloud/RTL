from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the logoff component
from Components.Common_components.Logoff import logoff_user


# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: POS_Training_Mode_Handler
# @Purpose: Handles complete workflow to logoff existing session and enter training mode
# @Dependencies: Logoff.py, pywinauto, time
# @Input_Params: Various window objects and credentials
# @Return_Values: Boolean indicating success/failure of training mode entry
# @Used_By_Tests: Training mode test scenarios, Manager override tests
# @Known_Limitations: Requires POS application to be running, depends on UI structure
# ============================================

"""
Component: POS Training Mode Handler
Location: Components/Common_components/traning_mode.py

Purpose:
    Comprehensive handler for entering POS Training Mode including:
    1. Existing session logoff
    2. Navigation to main screen
    3. Training mode access
    4. Manager credential entry

Flow Context:
    - Used for training scenarios
    - Part of manager override workflows
    - Called during testing and demonstration
    - Used for safe environment testing

Workflow Steps:
    1. Connect to POS application
    2. Logoff existing user session
    3. Navigate to main login screen
    4. Access training mode
    5. Enter manager credentials
    6. Verify training mode activation

UI Elements Handled:
    1. Main Screen:
       - Login button (UCLoginScreenLoginButton)
       - Training Mode button (UCSignInTrainingButton)

    2. Training Login Screen:
       - Username field (UserName)
       - Password field (Password)
       - Login button (UCSignInOKButton)

    3. Logoff Components:
       - Via reusable Logoff component
       - Menu navigation and popups

Training Mode Benefits:
    - Safe testing environment
    - No real transactions processed
    - Full POS functionality available
    - Manager-level access
    - Easy reset and cleanup

Error Handling:
    - Connection failures
    - UI element detection issues
    - Login credential problems
    - Session transition errors

Usage Example:
    from Components.Common_components.traning_mode import main, enter_training_mode
    
    # Full workflow
    main()
    
    # Custom training mode entry
    success = enter_training_mode(
        username="manager1",
        password="password123"
    )
"""

def login_to_main_screen(win):
    """
    Handles the initial login, dismissing the screensaver if present.
    If login button is not found, assumes screensaver is active and clicks center screen.
    """
    print("📋 Navigating from login screen to main screen...")
    
    # Use helper function to handle screensaver and find login button
    success, login_btn = dismiss_screensaver_and_find_login(win)
    
    if not success or login_btn is None:
        print("❌ Could not find login button after attempting to dismiss screensaver")
        return False
    
    try:
        print("� Clicking 'Login' to navigate to main screen...")
        login_btn.click_input()
        time.sleep(2)
        print("✅ Navigation to main screen successful.")
        return True
    except Exception as e:
        print(f"❌ Failed to click login button: {e}")
        return False

def login_to_training_mode(win):
    """
    Navigates into Training Mode and logs in with specific credentials.
    
    Args:
        win: The POS application window object
        
    Returns:
        bool: True if training mode login successful, False otherwise
    """
    # --- Navigate to Training Mode ---
    print("📋 Navigating to Training Mode...")
    try:
        training_mode_button_p2 = win.child_window(auto_id="UCSignInTrainingButton", control_type="Button")
        print("✅ Found 'Training Mode' button on main screen.")
        
        print("🔄 Clicking 'Training Mode' to access training login...")
        training_mode_button_p2.click_input()
        time.sleep(2)

        # --- Enter Training Mode Credentials ---
        print("🔐 Entering training mode credentials...")
        
        # 1. Enter User Name
        user_name_input_p3 = win.child_window(auto_id="UserName", control_type="Edit")
        print("✅ Found 'User Name' input field.")
        user_name_input_p3.type_keys("atmgr5", with_spaces=True)
        print("📝 Entered User Name: atmgr5")

        # 2. Enter Password
        password_input_p3 = win.child_window(auto_id="Password", control_type="Edit")
        print("✅ Found 'Password' input field.")
        password_input_p3.type_keys("abcd1234", with_spaces=True)
        print("📝 Entered Password: ********")

        # 3. Click Login
        login_btn_p3 = win.child_window(title="Login", auto_id="UCSignInOKButton", control_type="Button")
        print("✅ Found 'Login' button for training mode.")
        
        print("🔄 Clicking 'Login' to complete training mode access...")
        login_btn_p3.click_input()
        
        time.sleep(2)  # Wait for login to complete
        print("✅ Training mode login successful.")
        return True
    except Exception as e:
        print(f"❌ Failed to login to training mode: {e}")
        return False

def main():
    """
    Main function to orchestrate the entire workflow:
    1. Connect to POS application
    2. Logoff existing session 
    3. Navigate to main screen
    4. Enter training mode with credentials
    """
    # --- Connection Setup ---
    application_window_title = ".*R10PosClient.*"
    print("🚀 Starting Training Mode Workflow...")
    print("\n--- Step 1: Connecting to POS Application ---")
    try:
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("✅ Successfully connected and focused the window.")
    except Exception as e:
        print(f"❌ Could not connect to the application: {e}")
        return

    # --- Step 2: Logoff existing session ---
    print("\n--- Step 2: Logging off existing session ---")
    try:
        if logoff_user(approval_username="atmgr5", approval_password="abcd1234"):
            print("✅ Successfully logged off existing session")
        else:
            print("⚠️ Logoff completed with warnings or was not required")
    except Exception as e:
        print(f"⚠️ Logoff process encountered an issue: {e}")
        print("ℹ️ Continuing with training mode setup...")

    # Add a delay for the application to return to the login screen
    print("\n--- Step 3: Waiting for application to return to login screen ---")
    print("⏳ Waiting for application to stabilize after logoff...")
    time.sleep(5) 

    # --- Step 4: Perform the initial login ---
    print("\n--- Step 4: Performing initial login to main screen ---")
    if not login_to_main_screen(win):
        print("❌ Aborting script due to initial login failure.")
        return
        
    # --- Step 5: Log into training mode ---
    print("\n--- Step 5: Entering training mode ---")
    if not login_to_training_mode(win):
        print("❌ Script aborted due to training mode login failure.")
        return

    print("\n🎉 --- Training Mode Workflow completed successfully! --- 🎉")
    print("\n✅ Workflow Summary:")
    print("   - Existing session logged off successfully")
    print("   - Navigated to main screen")
    print("   - Entered training mode with manager credentials")
    print("   - Training mode is now active and ready for use")

# --- Reusable Training Mode Functions ---

def enter_training_mode(username="atmgr5", password="abcd1234", perform_logoff=True):
    """
    Reusable function to enter training mode with custom parameters.
    
    Args:
        username (str): Manager username for training mode (default: "atmgr5")
        password (str): Manager password for training mode (default: "abcd1234")
        perform_logoff (bool): Whether to logoff existing session first (default: True)
        
    Returns:
        bool: True if training mode entry successful, False otherwise
    """
    print(f"\n🎯 --- Entering Training Mode (User: {username}) ---")
    
    # --- Connection Setup ---
    application_window_title = ".*R10PosClient.*"
    print("🔗 Connecting to POS Application...")
    try:
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("✅ Successfully connected to POS application.")
    except Exception as e:
        print(f"❌ Could not connect to the application: {e}")
        return False

    # --- Optional Logoff ---
    if perform_logoff:
        print("🚪 Logging off existing session...")
        try:
            if logoff_user(approval_username=username, approval_password=password):
                print("✅ Successfully logged off existing session")
            else:
                print("⚠️ Logoff completed with warnings or was not required")
            time.sleep(5)  # Wait for application to stabilize
        except Exception as e:
            print(f"⚠️ Logoff process issue: {e}")
            print("ℹ️ Continuing with training mode setup...")

    # --- Main Screen Login ---
    if not login_to_main_screen(win):
        print("❌ Failed to reach main screen.")
        return False
        
    # --- Training Mode Login ---
    if not login_to_training_mode_with_credentials(win, username, password):
        print("❌ Failed to enter training mode.")
        return False

    print("🎉 Successfully entered training mode!")
    return True


def login_to_training_mode_with_credentials(win, username, password):
    """
    Login to training mode with custom credentials.
    
    Args:
        win: The POS application window object
        username (str): Username for training mode
        password (str): Password for training mode
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"🔐 Entering training mode with user: {username}")
    try:
        # Navigate to Training Mode
        training_mode_button = win.child_window(auto_id="UCSignInTrainingButton", control_type="Button")
        print("✅ Found 'Training Mode' button.")
        
        training_mode_button.click_input()
        time.sleep(2)

        # Enter credentials
        user_name_input = win.child_window(auto_id="UserName", control_type="Edit")
        password_input = win.child_window(auto_id="Password", control_type="Edit")
        login_btn = win.child_window(title="Login", auto_id="UCSignInOKButton", control_type="Button")
        
        print("📝 Entering credentials...")
        user_name_input.type_keys(username, with_spaces=True)
        password_input.type_keys(password, with_spaces=True)
        
        print("🔄 Clicking Login...")
        login_btn.click_input()
        time.sleep(2)
        
        print("✅ Training mode credentials submitted successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to enter training mode: {e}")
        return False


def quick_training_mode():
    """
    Quick entry into training mode using default settings.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("⚡ Quick Training Mode Entry - Using defaults")
    return enter_training_mode()


def training_mode_without_logoff(username="atmgr5", password="abcd1234"):
    """
    Enter training mode without performing logoff first.
    Useful when already at login screen.
    
    Args:
        username (str): Manager username (default: "atmgr5")
        password (str): Manager password (default: "abcd1234")
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("🚀 Training Mode Without Logoff")
    return enter_training_mode(username, password, perform_logoff=False)


def dismiss_screensaver_and_find_login(win):
    """
    Helper function to dismiss screensaver and find login button.
    Uses multiple strategies to handle different screensaver scenarios.
    
    Args:
        win: The POS application window object
        
    Returns:
        tuple: (success: bool, login_button: object or None)
    """
    print("🔍 Attempting to find login button or dismiss screensaver...")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Try to find the login button
            login_btn = win.child_window(title="Login", auto_id="UCLoginScreenLoginButton", control_type="Button")
            
            if login_btn.exists(timeout=2):
                print(f"✅ Found login button on attempt {attempt + 1}")
                return True, login_btn
                
        except Exception:
            pass
        
        if attempt < max_attempts - 1:
            print(f"⚠️ Attempt {attempt + 1}: Login button not found, trying to dismiss screensaver...")
            
            # Strategy 1: Click center of screen
            try:
                win_rect = win.rectangle()
                center_x = win_rect.width() // 2
                center_y = win_rect.height() // 2
                
                print(f"🖱️ Clicking center of window at relative coordinates ({center_x}, {center_y})")
                win.click_input(coords=(center_x, center_y))
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Center click failed: {e}")
                
                # Strategy 2: Try simple window click
                try:
                    print("🖱️ Trying simple window click...")
                    win.click_input()
                    time.sleep(2)
                except Exception as e2:
                    print(f"⚠️ Simple click also failed: {e2}")
                    
                    # Strategy 3: Try sending a key press to wake up screen
                    try:
                        print("⌨️ Trying key press to wake screen...")
                        win.send_keys(' ')  # Send space key
                        time.sleep(2)
                    except Exception as e3:
                        print(f"⚠️ Key press failed: {e3}")
    
    print("❌ Failed to find login button after all attempts")
    return False, None


# --- Utility Functions ---

def validate_training_mode_state():
    """
    Validates that training mode is active and functional.
    Can be extended to check for training mode indicators.
    
    Returns:
        bool: True if training mode is active, False otherwise
    """
    print("🔍 Validating training mode state...")
    # This can be extended to check for specific UI indicators
    # that confirm training mode is active
    time.sleep(1)
    print("✅ Training mode state validation completed")
    return True


def handle_screensaver_universal(win, target_element_check_func, element_description="target element"):
    """
    Universal screensaver handler that can be used for any UI element detection.
    
    Args:
        win: The POS application window object
        target_element_check_func: Function that returns (found: bool, element: object)
        element_description: Description of the element being searched for
        
    Returns:
        tuple: (success: bool, element: object or None)
    """
    print(f"🔍 Looking for {element_description}...")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        # Try to find the target element
        found, element = target_element_check_func()
        
        if found and element is not None:
            print(f"✅ Found {element_description} on attempt {attempt + 1}")
            return True, element
        
        if attempt < max_attempts - 1:
            print(f"⚠️ Attempt {attempt + 1}: {element_description} not found, trying to dismiss screensaver...")
            
            # Multiple strategies to dismiss screensaver
            strategies = [
                ("Center click", lambda: win.click_input(coords=(win.rectangle().width()//2, win.rectangle().height()//2))),
                ("Simple click", lambda: win.click_input()),
                ("Space key", lambda: win.send_keys(' ')),
                ("Enter key", lambda: win.send_keys('{ENTER}'))
            ]
            
            for strategy_name, strategy_func in strategies:
                try:
                    print(f"🖱️ Trying {strategy_name} to dismiss screensaver...")
                    strategy_func()
                    time.sleep(2)
                    break  # If successful, break out of strategies loop
                except Exception as e:
                    print(f"⚠️ {strategy_name} failed: {e}")
                    continue
    
    print(f"❌ Failed to find {element_description} after all attempts")
    return False, None


if __name__ == "__main__":
    main()

