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

def add_card(banner, TC_ID, Iteration, data_file="SaleData.csv"):

    # title_regex = ".*R10PosClient.*"
    DATA_FILE = data_file
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path = parent_path / 'resources' / data_file
    # print(f"Reading credentials from: {file_path}")
    card_number = get_csv_value(file_path, banner, TC_ID, Iteration, 'Card_number')

    app = None
    win = None
    # if card_number == "":
    #     print("⚠️ No card number specified. Skipping loyalty card addition.")
    #     return False
    try:
        time.sleep(2)  # Wait for the loyalty popup to appear
        app = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        win = app.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        # win1.set_focus()
        # win1.print_control_identifiers()
    except Exception as e:
        print(f"❌ Could not connect to loyalty popup: {e}")
        return False
    # win.child_window(title="Loyalty Card Number", control_type="Edit").type_keys("1234567890")
    # win1.top_window()
    
    win.set_focus()


    if card_number == "":
        print("⚠️ No card number specified. Skipping loyalty card addition.")
        win.child_window(title="Cancel", control_type="Button").click_input()
        logger.log("⚠️ No card number specified. Skipping loyalty card addition.", status="pass")
        return False

    if(win.child_window(auto_id="ShopperIdentificationViewID", control_type="Custom").exists(timeout=5) & 
       win.child_window(title_re=".*ASK TO SCAN EVERYDAY REWARDS CARD.*", auto_id="Title", control_type="Text").exists(timeout=5) & 
       win.child_window(title="Collect points for every dollar spent to enjoy money off your shopping.", auto_id="Message", control_type="Text").exists(timeout=5)):
        print("Loyalty popup detected. Proceeding with card entry...")
        logger.log("Loyalty popup detected. Proceeding with card entry...", status="pass")

        win.child_window(auto_id="ValueTextBox", control_type="Edit").click_input()
        win.child_window(auto_id="ValueTextBox", control_type="Edit").type_keys(card_number)
        win.child_window(title="Next", control_type="Button").click_input()
        actual_card_number = win.child_window(auto_id="ValueTextBox", control_type="Edit").get_value()
        if actual_card_number == card_number:
            print(f"✅ Card number '{card_number}' entered correctly.")
            logger.log(f"✅ Card number '{card_number}' entered correctly.", status="pass")
        else:
            print(f"❌ Card number entry mismatch. Expected: '{card_number}', Actual: '{actual_card_number}'")
            logger.log(f"❌ Card number entry mismatch. Expected: '{card_number}', Actual: '{actual_card_number}'", status="fail")
            logger.take_screenshot("Card_number_entry_mismatch")
            
        global_instance.is_loyaltycard_added = True
        print(f"💳 Loyalty card add status: {global_instance.is_loyaltycard_added}")
        win.child_window(title="OK", control_type="Button").click_input()
        print("✅ Loyalty card added successfully.")
        logger.log("✅ Loyalty card added successfully.", status="pass")
    else:
        print("❌ Loyalty popup not detected.")
        logger.log("❌ Loyalty popup not detected.", status="fail")
        logger.take_screenshot("Loyalty_popup_not_detected")
        return False

    return True