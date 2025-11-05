# -*- coding: utf-8 -*-
"""
This script provides a full login automation and error-checking function 
for the R10PosClient application. It uses pywinauto to interact with the UI 
and OCR to robustly verify different error messages.

Prerequisites:
- Tesseract-OCR engine must be installed: https://github.com/UB-Mannheim/tesseract/wiki
- Python libraries: pip install pywinauto Pillow pytesseract

Test Case Usage:
- TC012_invalid_login_error_validation: Uses attempt_login, find_visible_error, 
  and dismiss_screensaver_and_navigate_to_login for comprehensive login error validation
- Error Message Validation: "Invalid user or password, please follow company procedure to manage your user profile."
- Security Compliance Testing: Validates exact error message text for compliance requirements
"""
import pytesseract
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError
import time

# --- Configuration ---
# IMPORTANT: Update this path to your Tesseract-OCR installation directory.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def find_visible_error(window_title, potential_errors):
    """
    Captures an application window and uses OCR to see if any of a list of error messages are visible.

    Args:
        window_title (str): The exact title of the application window.
        potential_errors (list): A list of error strings to search for.

    Returns:
        str: The error message string that was found, or None if no errors were found.
    """
    try:
        app = Application(backend="uia").connect(title=window_title, timeout=10)
        main_window = app.window(title=window_title)
        
        # Give the UI a moment to update after a click
        time.sleep(1)

        screenshot = main_window.capture_as_image()
        extracted_text = pytesseract.image_to_string(screenshot)
        clean_text = " ".join(extracted_text.split())

        for error in potential_errors:
            if error in clean_text:
                return error # Return the specific error message found
        
        return None # No errors were found

    except (ElementNotFoundError, FileNotFoundError):
        return "Could not connect to the application or find Tesseract."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def dismiss_screensaver_and_navigate_to_login(main_window):
    """
    Helper function to dismiss screensaver and navigate to login screen.
    Returns True if login fields are found, False otherwise.
    """
    print("🔍 Checking for login fields or attempting to dismiss screensaver...")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Try to find the username and password fields
            username_field = main_window.child_window(auto_id="UserName", control_type="Edit")
            password_field = main_window.child_window(auto_id="Password", control_type="Edit")
            
            if username_field.exists(timeout=2) and password_field.exists(timeout=2):
                print(f"✅ Found login fields on attempt {attempt + 1}")
                return True
                
        except Exception:
            pass
        
        # If fields not found, try to dismiss screensaver or navigate to login
        if attempt < max_attempts - 1:
            print(f"⚠️ Attempt {attempt + 1}: Login fields not found, trying to dismiss screensaver...")
            
            try:
                # First, try to find and click the main login button (from screensaver/main screen)
                try:
                    main_login_btn = main_window.child_window(title="Login", auto_id="UCLoginScreenLoginButton", control_type="Button")
                    if main_login_btn.exists(timeout=2):
                        print("✅ Found main screen login button, clicking to navigate to login form...")
                        main_login_btn.click_input()
                        time.sleep(2)
                        continue
                except Exception:
                    pass
                
                # If main login button not found, try screensaver dismissal strategies
                print("🖱️ Trying to dismiss screensaver...")
                
                # Strategy 1: Click center of screen
                try:
                    win_rect = main_window.rectangle()
                    center_x = win_rect.width() // 2
                    center_y = win_rect.height() // 2
                    print(f"🖱️ Clicking center of window at relative coordinates ({center_x}, {center_y})")
                    main_window.click_input(coords=(center_x, center_y))
                    time.sleep(2)
                except Exception as e:
                    print(f"⚠️ Center click failed: {e}")
                    
                    # Strategy 2: Try simple window click
                    try:
                        print("🖱️ Trying simple window click...")
                        main_window.click_input()
                        time.sleep(2)
                    except Exception as e2:
                        print(f"⚠️ Simple click also failed: {e2}")
                        
                        # Strategy 3: Try sending a key press to wake up screen
                        try:
                            print("⌨️ Trying key press to wake screen...")
                            main_window.send_keys(' ')  # Send space key
                            time.sleep(2)
                        except Exception as e3:
                            print(f"⚠️ Key press failed: {e3}")
                
            except Exception as e:
                print(f"⚠️ Screensaver dismissal attempt failed: {e}")
    
    print("❌ Failed to find login fields after all attempts")
    return False

def attempt_login(username, password, error_list):
    """
    Attempts to log in with a given username and password, then checks for errors.
    Now includes screensaver handling and navigation to login screen.
    """
    print(f"\n--- Attempting login with Username: '{username}', Password: '{password}' ---")
    try:
        app = Application(backend="uia").connect(title="R10PosClient", timeout=10)
        main_window = app.window(title="R10PosClient")
        main_window.set_focus()  # Ensure the main window is focused
        
        # First, try to dismiss screensaver and navigate to login screen if needed
        if not dismiss_screensaver_and_navigate_to_login(main_window):
            print("❌ Could not find or navigate to login fields")
            return False
        
        # Find controls using their AutomationId
        username_field = main_window.child_window(auto_id="UserName", control_type="Edit")
        password_field = main_window.child_window(auto_id="Password", control_type="Edit")
        login_button = main_window.child_window(auto_id="UCSignInOKButton", control_type="Button")

        # Type credentials and click login
        username_field.set_edit_text('') # Clear field
        username_field.type_keys(username, with_spaces=True)
        password_field.set_edit_text('') # Clear field
        password_field.type_keys(password)
        login_button.click()

        # Check for any of the specified errors
        error_found = find_visible_error("R10PosClient", error_list)

        if error_found:
            print(f"Result: FAILED. Error message found: '{error_found}'")
            return False # Login failed
        else:
            print("Result: SUCCESS. No error messages detected.")
            return True # Login likely succeeded

    except Exception as e:
        print(f"An error occurred during the login attempt: {e}")
        return False


def main():
    """
    Main function to run a sequence of login checks for the R10PosClient application.
    """
    # List of all possible error messages to check for
    possible_errors = [
        "Please enter user name",
        "Please Enter password",
        "Invalid user or password, please follow company procedure to manage your user profile"
    ]
    
    # --- Start Login Scenarios ---
    
    # Scenario 1: Password only (missing username)
    attempt_login(username="", password="somepassword", error_list=possible_errors)

    # Scenario 2: Username only (missing password)
    attempt_login(username="someuser", password="", error_list=possible_errors)
    
    # Scenario 3: Incorrect username and password
    login_ok = attempt_login(username="wronguser", password="wrongpassword", error_list=possible_errors)

    # Scenario 4: If any previous login failed, try with default credentials
    if not login_ok:
        print("\n--- Previous login failed. Trying default credentials as a fallback. ---")
        attempt_login(username="Atmgr5", password="abcd1234", error_list=possible_errors)


if __name__ == "__main__":
    main()

