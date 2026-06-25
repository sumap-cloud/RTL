from pywinauto import Application
import time

def initialize_and_login(title_regex, username, password):
    """Initializes connection and handles Login/Unlock."""
    print(f"Initializing connection to: {title_regex}")
    try:
        win = Application(backend="uia").connect(title_re=title_regex, timeout=15)
        app = win.window(title_re=title_regex)
        app.set_focus()

        # Handle Screensaver
        sav = app.child_window(class_name="MediaElement", found_index=0)
        if sav.exists(timeout=5):
            print("Screensaver detected. Dismissing...")
            sav.click_input()
            time.sleep(1)

        # UI Elements
        login_btn = app.child_window(title="Login", control_type="Button")
        unlock_btn = app.child_window(title="Unlock", control_type="Button")
        locked_label = app.child_window(title_re="Locked by", control_type="Text")

        if login_btn.exists(timeout=3):
            print("Path: Standard Login")
            login_btn.click_input()
            app.child_window(auto_id="UserName", control_type="Edit").set_text(username)
            app.child_window(auto_id="Password", control_type="Edit").set_text(password)
            app.child_window(title="Login", control_type="Button").click_input()
        elif unlock_btn.exists(timeout=3) and locked_label.exists():
            print("Path: Session Unlock")
            app.child_window(auto_id="Password", control_type="Edit").set_text(password)
            unlock_btn.click_input()
        else:
            print("Application already at dashboard or in unknown state.")
        return app
    except Exception as e:
        print(f"❌ Initialization Error: {e}")
        return None

def reasoncode_popup_handler(reason_code):
    try:
        popup_res_con = Application(backend="uia").connect(title_re=".*Retalix.*Presentation.*", timeout=5)
        popup_res_win = popup_res_con.window(title_re=".*Retalix.*Presentation.*")
        popup_res_win.set_focus()
        reason_btn = popup_res_win.child_window(title=reason_code, control_type="Button")
        if reason_btn.exists(timeout=3):
            reason_btn.click_input()
            print(f"✅ Reason '{reason_code}' selected.")
    except Exception as e:
        print(f"❌ Reason Selection Failed: {e}")

def approval_popup_handler(username, password):
    print("Requesting Manager Approval...")
    try:
        popup_conn = Application(backend="uia").connect(title_re=".*Retalix.*Presentation.*", timeout=5)
        popup_win = popup_conn.window(title_re=".*Retalix.*Presentation.*")
        popup_win.set_focus()
        
        user_field = popup_win.child_window(auto_id="ValueTextBox", control_type="Edit")
        pass_field = popup_win.child_window(auto_id="Password", control_type="Edit")

        if user_field.exists(timeout=5):
            user_field.click_input()
            user_field.type_keys(username)
            pass_field.click_input()
            pass_field.type_keys(password)
            
            user_field.click_input()
            time.sleep(1)
            ok_btn = popup_win.child_window(title="OK", control_type="Button")
            if ok_btn.exists(): # Timeout goes inside .exists(), not child_window
                ok_btn.click_input()
            
            time.sleep(1)
            reasoncode_popup_handler("Unwanted Goods")
        else:
            print("❌ Manager Login fields not found.")
    except Exception as e:
        print(f"❌ Approval Failed: {e}")

# ==============================================================================
# MAIN EXECUTION BLOCK
# ==============================================================================

# Step 1: Initialize and Login in one line
app = initialize_and_login(".*R10PosClient.*", "Atcash1", "abcd1234")

if app:
    nosale_btn = app.child_window(title="No Sale", control_type="Button")
    void_btn = app.child_window(title="Void Transaction", control_type="Button")

    print("Waiting for dashboard to stabilize...")

    if nosale_btn.exists(timeout=12): 
        print("✅ Success: At Dashboard.")
    elif void_btn.exists(timeout=3):
        print("Detected Void state. Processing approval...")
        void_btn.click_input()
        approval_popup_handler("AtMgr5", "abcd1234")
        
        print("Verifying final state...")
        if nosale_btn.exists(timeout=10):
            if nosale_btn.is_enabled():
                print("⭐⭐ FINAL SUCCESS: Void complete. No Sale is ENABLED.")
            else:
                print("⚠️ Warning: At Dashboard, but No Sale is DISABLED.")
        else:
            print("❌ Error: Dashboard not found after Void sequence.")
    else:
        print("❌ Error: UI state unrecognized.")
        app.print_control_identifiers()