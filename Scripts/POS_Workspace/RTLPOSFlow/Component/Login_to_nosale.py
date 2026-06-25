import time
import re
import sys
import csv
from pathlib import Path

from pywinauto import Application, timings

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component.report import logger


@staticmethod
# def initialize_and_login(title_regex, username, password):
def initialize_and_login(banner, TC_ID, Iteration, data_file="SaleData.csv"):
    """Initializes connection, handles Login/Unlock, and validates dashboard or void flow."""

    title_regex = ".*R10PosClient.*"
    DATA_FILE = data_file
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path = parent_path / 'resources' / data_file
    # print(f"Reading credentials from: {file_path}")
    username = get_csv_value(file_path, banner, TC_ID, Iteration, 'Username')
    password = get_csv_value(file_path, banner, TC_ID, Iteration, 'Password')

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

        # ===== LOGIN / UNLOCK FLOW =====
        if login_btn.exists(timeout=3):
            print("Path: Standard Login")
            login_btn.click_input()
            app.child_window(auto_id="UserName", control_type="Edit").set_text(username)
            app.child_window(auto_id="Password", control_type="Edit").set_text(password)
            app.child_window(title="Login", control_type="Button").click_input()

        elif unlock_btn.exists(timeout=3) and locked_label.exists():
            print("Path: Session Unlock"+password)
            app.child_window(auto_id="Password", control_type="Edit").set_text(password)
            unlock_btn.click_input()

        else:
            print("Application already at dashboard or in unknown state.")

        print("Waiting for dashboard to stabilize...")

        # ===== DASHBOARD / VOID VALIDATION =====
        nosale_btn = app.child_window(title="No Sale", control_type="Button")
        void_btn = app.child_window(title="Void Transaction", control_type="Button")

        if nosale_btn.exists(timeout=12):
            print("✅ Success: At Dashboard.")
            logger.log("✅ Success: At Dashboard.", status="pass")

        elif void_btn.exists(timeout=3):
            print("Detected Void state. Processing approval...")
            void_btn.click_input()

            # if mgr_username and mgr_password:
            approval_popup_handler("ATMgr5", "abcd1234")
            # else:
            #     print("❌ Manager credentials missing for approval.")
            time.sleep(1)
            reasoncode_popup_handler("Unwanted Goods")
            
            print("Verifying final state...")
            if nosale_btn.exists(timeout=10):
                if nosale_btn.is_enabled():
                    print("⭐⭐ FINAL SUCCESS: Void complete. No Sale is ENABLED.")
                    logger.log("⭐⭐ FINAL SUCCESS: Void complete. No Sale is ENABLED.", status="pass")
                else:
                    print("⚠️ Warning: At Dashboard, but No Sale is DISABLED.")
                    logger.log("⚠️ Warning: At Dashboard, but No Sale is DISABLED.", status="fail")
                    logger.take_screenshot("No_Sale_button_disabled")
            else:
                print("❌ Error: Dashboard not found after Void sequence.")
                logger.log("❌ Error: Dashboard not found after Void sequence.", status="fail")
                logger.take_screenshot("Dashboard_not_found_after_Void_sequence")

        else:
            print("❌ Error: UI state unrecognized.")
            logger.log("❌ Error: UI state unrecognized.", status="fail")
            logger.take_screenshot("UI_state_unrecognized")

            # app.print_control_identifiers()

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
            if ok_btn.exists(timeout=3):
                ok_btn.click_input()

        else:
            print("❌ Manager Login fields not found.")

    except Exception as e:
        print(f"❌ Approval Failed: {e}")

