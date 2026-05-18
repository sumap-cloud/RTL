# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: pos_login
# @Purpose: Manages POS application login process and session validation
# @Dependencies: pywinauto, subprocess, os
# @Input_Params: username, password, terminal_type (optional)
# @Return_Values: Tuple of (app, window) objects, Boolean success indicator
# @Used_By_Tests: All test cases (TC001-TC012), TC012_invalid_login_error_validation for initial setup and fallback validation
# @Known_Limitations: Password visibility not masked in logs
# ============================================

"""
Component: POS Login Handler
Location: Components/Common_components/pos_login.py

Purpose:
    Manages the POS application login process, including application launch,
    state verification, and credentials entry.

Flow Context:
    - First step in any POS automation scenario
    - Handles both fresh launch and existing session
    - Validates POS readiness before proceeding

UI Elements:
    1. Login Window:
       - Username Field (type: Edit)
       - Password Field (type: Edit)
       - Login Button (type: Button)
       
    2. No Sale Button:
       - Used to verify POS ready state
       - Type: Button
       - State: Should be enabled when POS is ready

    3. Application Window:
       - Title Pattern: ".*R10PosClient.*"
       - Type: Window
       - Should be visible and active

Functions:
    mainlogic(username: str, password: str) -> bool:
        Purpose: Handle complete login flow
        Args:
            - username: POS operator username
            - password: POS operator password
        Returns:
            - True: Login successful and POS ready
            - False: Any step failed

Error Handling:
    - POS not running (auto-launches)
    - Invalid credentials
    - POS not responding
    - No Sale button not ready
    - Window focus issues

Usage Example:
    ```python
    # Basic login flow:
    if mainlogic("ATcash5", "abcd1234"):
        print("POS ready for operations")
    else:
        print("Login failed or POS not ready")
    ```

Validation Steps:
    1. Pre-login:
       - Check if POS is running
       - Launch if needed
       - Wait for window to be ready
    
    2. During Login:
       - Enter credentials
       - Handle any popups
       - Wait for main screen
    
    3. Post-login:
       - Verify No Sale button
       - Check POS state
       - Ensure window focus

Common Issues:
    1. POS Launch:
       - Path not found
       - Already running
       - Window not responding
    
    2. Login Problems:
       - Credentials rejected
       - Session conflicts
       - System not ready
    
    3. State Verification:
       - No Sale button disabled
       - Window focus lost
       - Unexpected popups

Notes:
    - Always use with proper exception handling
    - Allow sufficient wait times
    - Verify POS state before proceeding
"""

import subprocess
import time
import random
from pywinauto import Application
from pywinauto.findwindows import find_windows
from Components.Common_components.handle_any_popup_POS import handle_Any_popup


def launch_pos():
    """
    Launch the POS application using launch.bat.
    """
    bat_path = r".\Scripts\POS_Workspace\Components\Common_components\launch.bat"
    try:
        # Use Popen to launch the batch file without waiting for it to complete
        subprocess.Popen([bat_path], shell=True)
        print(f"✅ Launched POS application using: {bat_path}")
        # Wait for the application to initialize
        time.sleep(20)
        return True
    except Exception as e:
        print(f"❌ Failed to launch POS application: {e}")
        return False

def login_to_pos(username, password):
    """
    Logs into the POS application.
    This version has been MODIFIED to use a virtual keyboard for credential entry.
    """
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
    except Exception as e:
        print(f"❌ Failed to connect to POS application: {e}")
        return False

    # --- Initial Login Screen Handling (Screensaver/Overlay) ---
    login_btn = win.child_window(auto_id="UCLoginScreenLoginButton", control_type="Button")
    if not login_btn.exists(timeout=5):
        print("ℹ️ Login button not found. Trying to dismiss possible screen saver or overlay...")
        try:
            # Attempt to click away a potential screensaver
            screensaver = win.child_window(class_name="MediaElement")
            if screensaver.exists(timeout=3):
                print("ℹ️ Screen saver detected. Attempting to dismiss...")
                screensaver.click_input()
                time.sleep(1)
        except Exception:
            print("ℹ️ Screen saver not detected or could not be dismissed.")

        # If the button is still not found, try a general click on the window
        if not win.child_window(auto_id="UCLoginScreenLoginButton", control_type="Button").exists(timeout=3):
            print("ℹ️ Clicking on the window to dismiss any other overlay...")
            rect = win.rectangle()
            x = random.randint(rect.left + 50, rect.right - 50)
            y = random.randint(rect.top + 50, rect.bottom - 50)
            win.click_input(coords=(x, y))
            time.sleep(1)
    if not handle_Any_popup("Skip"):
        print("Failed to handle any popup.")
    # --- Click the initial login button to bring up the credential screen ---
    login_btn = win.child_window(auto_id="UCLoginScreenLoginButton", control_type="Button")
    if login_btn.exists(timeout=5):
        login_btn.wait("enabled", timeout=10)
        login_btn.click_input()
        print("✅ Initial Login button clicked.")
    else:
        print("❌ Login button not found after all attempts. Cannot proceed with login.")
        return False

    # --- VIRTUAL KEYBOARD LOGIC ---
    # This section is integrated from your provided virtual keyboard script.

    key_map = {
        'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g',
        'h': 'h', 'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
        'o': 'o', 'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u',
        'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z',
        'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G',
        'H': 'H', 'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N',
        'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T', 'U': 'U',
        'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
        '7': '7', '8': '8', '9': '9'
    }
    is_caps_on = False

    def toggle_caps():
        """Clicks the caps lock button and updates its state."""
        nonlocal is_caps_on
        try:
            # Assuming the caps lock button has a distinct identifier.
            # You might need to adjust "A ↔ a" if the title is different.
            caps_button = win.child_window(title_re=".*[aA] ↔ [aA].*", control_type="Button")
            if caps_button.exists(timeout=2):
                caps_button.click_input()
                is_caps_on = not is_caps_on
                print(f"✔️ Toggled Caps Lock. New state: {'ON' if is_caps_on else 'OFF'}")
                time.sleep(0.2)
            else:
                print("⚠️ Could not find Caps Lock button.")
        except Exception as e:
            print(f"❌ Error clicking Caps Lock button: {e}")

    def type_with_virtual_keyboard(text_to_type):
        """Simulates typing using the virtual keyboard, handling case correctly."""
        nonlocal is_caps_on
        for char in text_to_type:
            if char.isalpha():
                should_be_upper = char.isupper()
                if (should_be_upper and not is_caps_on) or \
                   (not should_be_upper and is_caps_on):
                    toggle_caps()

            if char in key_map:
                key_name = key_map[char]
                try:
                    # Find the button by its current text (e.g., 'a' or 'A')
                    key_button = win.child_window(title=key_name, control_type="Button")
                    if key_button.exists(timeout=2):
                        key_button.click_input()
                        print(f"✔️ Clicked '{key_name}'")
                        time.sleep(0.1) # A small delay can improve reliability
                    else:
                        print(f"⚠️ Could not find key: '{key_name}'")
                except Exception as e:
                    print(f"❌ Error clicking key '{key_name}': {e}")
            else:
                print(f"⚠️ Character '{char}' not in key_map")

    # --- Enter Username with Virtual Keyboard ---
    username_field = win.child_window(auto_id="UserName", control_type="Edit")
    if username_field.exists(timeout=5):
        username_field.wait("ready", timeout=10)
        username_field.click_input() # Focus the field to ensure keyboard targets it
        print(f"✅ User ID field found. Typing with virtual keyboard: {username}")
        type_with_virtual_keyboard(username)
    else:
        print("❌ User ID field not found.")
        return False

    # --- Enter Password with Virtual Keyboard ---
    password_field = win.child_window(auto_id="Password", control_type="Edit")
    if password_field.exists(timeout=5):
        password_field.wait("ready", timeout=10)
        password_field.click_input() # Focus the field
        print(f"✅ Password field found. Typing with virtual keyboard: {'*' * len(password)}")
        type_with_virtual_keyboard(password)
    else:
        print("❌ Password field not found.")
        return False

    # --- Click the final sign-in button ---
    loginrc_btn = win.child_window(auto_id="UCSignInOKButton", control_type="Button")
    if loginrc_btn.exists(timeout=5):
        loginrc_btn.wait("enabled", timeout=5)
        loginrc_btn.click_input()
        print("✅ Sign-in OK button clicked.")
        time.sleep(2)
        print("🎉 Login attempted. Check POS for success.")
        return True
    else:
        print("❌ Login OK button not found.")
        return False


def check_nosale(win):
    """
    Check if the 'No Sale' button is enabled and visible.
    """
    try:
        nosale_btn = win.child_window(auto_id="commandsLowerButtonsNo Sale", control_type="Button")
        if nosale_btn.exists() and nosale_btn.is_visible():
            print("✅ 'No Sale' button is enabled and exists.")
            return True
        else:
            print("❌ 'No Sale' button is not enabled or does not exist.")
            return False
    except Exception as e:
        print(f"❌ Error checking for 'No Sale' button: {e}")
        return False

def mainlogic(UserName, Password):
    """
    Main execution flow for the POS automation.
    """
    pos_title_re = ".*R10PosClient.*"

    def is_pos_running():
        """Checks if the POS application window exists."""
        try:
            wins = find_windows(title_re=pos_title_re)
            return len(wins) > 0
        except Exception:
            return False

    # --- Main Flow Logic ---
    if is_pos_running():
        print("ℹ️ POS is already running. Checking for No Sale button...")
        try:
            app = Application(backend="uia").connect(title_re=pos_title_re)
            win = app.window(title_re=pos_title_re)
            win.set_focus()
            if check_nosale(win):
                print("✅ POS is ready. No Sale button is present.")
                return True
            else:
                print("ℹ️ No Sale button not found. Attempting login...")
                if login_to_pos(UserName, Password):
                    print("✅ Logged in successfully. Re-checking No Sale button...")
                    if check_nosale(win):
                        print("✅ No Sale button found after login.")
                        return True
                    else:
                        print("❌ No Sale button still not found after login.")
                        return False
                else:
                    print("❌ Login failed. Cannot check No Sale button.")
                    return False
        except Exception as e:
            print(f"❌ An error occurred while interacting with the running POS: {e}")
            return False

    else:
        print("ℹ️ POS is not running. Launching POS...")
        if launch_pos():
            try:
                if login_to_pos(UserName, Password):
                    print("✅ Logged in successfully. Checking No Sale button...")
                    app = Application(backend="uia").connect(title_re=pos_title_re)
                    win = app.window(title_re=pos_title_re)
                    win.set_focus()
                    if check_nosale(win):
                        print("✅ No Sale button found after login.")
                        return True
                    else:
                        print("❌ No Sale button not found after login.")
                else:
                    print("❌ Login failed after launch. Cannot check No Sale button.")
            except Exception as e:
                print(f"❌ An error occurred after launching POS: {e}")
        else:
            print("❌ Failed to launch the POS application.")


#if __name__ == "__main__":
    # To run the script, uncomment the line below
    #mainlogic("Atcash1", "abcd1234")
    #print("Script loaded. Call mainlogic() to start the automation.")
