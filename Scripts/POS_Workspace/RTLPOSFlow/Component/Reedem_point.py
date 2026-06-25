import time
import sys
from pathlib import Path
from pywinauto import Application, timings
# import pyautogui
# from PIL import ImageGrab

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component import global_instance
from Component.report import logger

def redeem_point(banner, TC_ID, Iteration, data_file="SaleData.csv"):

    # title_regex = ".*R10PosClient.*"
    DATA_FILE = data_file
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path = parent_path / 'resources' / data_file
    # print(f"Reading credentials from: {file_path}")
    redeem_amount = get_csv_value(file_path, banner, TC_ID, Iteration, 'Redeem_amount')

    app = None
    win = None

    # if redeem_amount == "":
    #     print("⚠️ No redeem amount specified. Skipping redeem points action.")
    #     return False
    
    try:
        time.sleep(5)  # Wait for the loyalty popup to appear
        app = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        win = app.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        win.set_focus()

        redeem_amount_popup = win.child_window(title_re=".*Current Rewards Balance:.*", auto_id="MessageTextBox", control_type="Edit")
        
        print(f"✅ Current Rewards Balance popup detected: '{redeem_amount_popup.window_text()}'.")
        logger.log(f"✅ Current Rewards Balance popup detected: '{redeem_amount_popup.window_text()}'.", status="pass")
        if redeem_amount_popup.exists(timeout=5):
            if redeem_amount == "":
                win.child_window(title="Do Not\nRedeem", auto_id="MessageBoxCommandButtonTemplate", control_type="Button").click_input()
                logger.log("⚠️ No redeem amount specified. Skipping redeem points action.", status="pass")
                print("⚠️ No redeem amount specified. Skipping redeem points action.")
                # return True
            else:
                enter_amount = win.child_window(auto_id="InputProductNumber", control_type="Edit")
                enter_amount.click_input()
                enter_amount.type_keys(redeem_amount)
                enter_amount.click_input()
                win.child_window(title="Redeem", auto_id="MessageBoxCommandButtonTemplate", control_type="Button").click_input()
                print(f"✅ Clicked on Current Rewards Balance popup.")
                global_instance.reward_redeem_status = True
                global_instance.redeem_amount = f"{float(redeem_amount):.2f}"
                print(f"💵 Redeem Amount: {global_instance.redeem_amount}")
                logger.log(f"💵 Redeem Amount: {global_instance.redeem_amount}", status="pass")
        else:
            print(f"⚠️ Current Rewards Balance popup not detected.")
            logger.log("⚠️ Current Rewards Balance popup not detected.", status="fail")
            logger.take_screenshot("Current_Rewards_Balance_popup_not_detected")
            return False

    except Exception as e:
        print(f"⚠️ Could not connect to Point Redemption popup: {e}")
        logger.log("⚠️ Current Rewards Balance popup not detected.", status="fail")
        logger.take_screenshot("Current_Rewards_Balance_popup_not_detected")

    return True
        
    


    # if float(global_instance.total_amount_salemode) % 1 != 0:
    #     print("⚠️ Total amount has a decimal component. Handling Round up action.")
        
    #     time.sleep(4)
    #     # win.set_focus()
    #     # Wait for the Round up popup to appear
    #     app1 = None
    #     win1 = None
        
    #     # if Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*").exists(timeout=5):

    #     try:
    #         time.sleep(5)  
    #         app1 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
    #         win1 = app1.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
    #         win1.set_focus()

    #         roundup_popup = win1.child_window(title_re=".*Round up to.*", auto_id="SuggestedAmountButton", control_type="Button")
    #         balance_msg = win1.child_window(title_re=".*Balance Due:.*", auto_id="BalanceDueText", control_type="Edit")
    #         # win1.print_control_identifiers()
    #         print(f"✅ Round up popup detected: '{roundup_popup.window_text()}'.")

    #         if roundup_popup.exists(timeout=5):
    #             print(f"✅ Round up popup detected with balance message: '{balance_msg.window_text()}'.")
    #             win1.child_window(title="Skip", auto_id="MessageBoxCommandButtonTemplate", control_type="Button").click_input()
    #             print("✅ Clicked on Round up button.")
    #         else:
    #             print("❌ Round up popup or balance message not detected.")

    #     except Exception as e:
    #     # else:
    #         print(f"❌ Could not connect to Round up popup: {e}")
            
    # else:
    #     print("⚠️ Total amount does not have a decimal component. Skipping Round up action.")
        

    # return True


