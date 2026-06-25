import time
import sys
from pathlib import Path
from pywinauto import Application, timings

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component import global_instance
from Component.report import logger
from Reusable.Tendermode_balance import get_balance_due




def handle_round_up_popup():

    total_amount = get_balance_due()
    print(f"⚠️ Checking for Round up popup eligibility:{total_amount}")
    if float(total_amount) % 1 >= 0:
        print("⚠️ Total amount has a decimal component. Handling Round up action.")
        
        time.sleep(4)
        # Wait for the Round up popup to appear
        app1 = None
        win1 = None
        
        # if Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*").exists(timeout=5):

        try:
            time.sleep(5)  
            app1 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
            win1 = app1.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
            win1.set_focus()

            roundup_popup = win1.child_window(title_re=".*Round up to.*", auto_id="SuggestedAmountButton", control_type="Button")
            balance_msg = win1.child_window(title_re=".*Balance Due:.*", auto_id="BalanceDueText", control_type="Edit")
            # win1.print_control_identifiers()
            print(f"✅ Round up popup detected: '{roundup_popup.window_text()}'.")

            if roundup_popup.exists(timeout=5):
                print(f"✅ Round up popup detected with balance message: '{balance_msg.window_text()}'.")
                logger.log(f"✅ Round up popup detected with balance message: '{balance_msg.window_text()}'.", status="pass")
                win1.child_window(title="Skip", auto_id="MessageBoxCommandButtonTemplate", control_type="Button").click_input()
                print("✅ Clicked on Round up button.")
                logger.log("✅ Clicked on Round up button.", status="pass")
            else:
                print("❌ Round up popup or balance message not detected.")
                logger.log("❌ Round up popup or balance message not detected.", status="fail")
                logger.take_screenshot("Round_Up_Popup_Not_Detected")

        except Exception as e:
        # else:
            print(f"❌ Could not connect to Round up popup: {e}")
            logger.log(f"❌ Could not connect to Round up popup: {e}", status="fail")
            logger.take_screenshot("Round_Up_Popup_Connection_Failed")
            
    else:
        print("⚠️ Total amount does not have a decimal component. Skipping Round up action.")
        

    return True