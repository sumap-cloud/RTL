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
from Component.report import logger


def redeem_collectable_offer(banner, TC_ID, Iteration):
    
    DATA_FILE = "SaleData.csv"
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path=parent_path /'resources'/ 'SaleData.csv'

    collectable_offer = get_csv_value(file_path, banner, TC_ID, Iteration, 'Collectable_offer')
    
    app1 = None
    win1 = None

    try:
        time.sleep(5)  # Wait for the loyalty popup to appear
        print("Attempting to connect to the application for collectable offer redemption...")
        app1 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        win1 = app1.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        
        win1.set_focus()
        popup_title = win1.child_window(title="Do you want me to apply it now?", auto_id="MessageTextBox", control_type="Edit")

        print(f"✅ Collectable redeem popup is existed and connected successfully.")
    except Exception as e:
        print(f"❌ Collectable redeem popup is not exist: {e}")
        return False
    
   
    if popup_title.exists(timeout=5):
        print(f"✅ Choice offer popup detected: '{popup_title.window_text()}' offered.")
        logger.log(f"✅ Choice offer popup detected: '{popup_title.window_text()}' offered.", status="pass")
        if collectable_offer.strip() == "":
            win1.child_window(title="Save for Next Shop", control_type="Button").click_input()
            print("⚠️ No collectable offer specified to redeem. Skipping offer redemption.")
            logger.log("⚠️ No collectable offer specified to redeem. Skipping offer redemption.", status="pass")

            # return True
        else:
            offer_btn = win1.child_window(title_re=f".*{collectable_offer}.*", auto_id="button", control_type="Button")
            if offer_btn.exists(timeout=5):
                offer_btn.click_input()
                print(f"✅ Redeemed choice offer '{collectable_offer}'.")
                logger.log(f"✅ Redeemed choice offer '{collectable_offer}'.", status="pass")
            else:
                print(f"❌ Choice offer button '{collectable_offer}' not found.")
                logger.log(f"❌ Choice offer button '{collectable_offer}' not found.", status="fail")
                logger.take_screenshot(f"Choice_Offer_Button_{collectable_offer}_Not_Found")
                return False

    else:
        print("❌ Choice offer popup not detected.")
        logger.log("❌ Choice offer popup not detected.", status="fail")
        logger.take_screenshot("Choice_Offer_Popup_Not_Detected")

    return True
