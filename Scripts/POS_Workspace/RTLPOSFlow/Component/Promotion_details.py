import time
import re
import sys
import csv
from pathlib import Path

from pywinauto import Application, timings, Desktop

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component.Update_csv import update_csv_value
from Component import global_instance
from Component.report import logger




def promotion_details(banner, TC_ID, Iteration, data_file="SaleData.csv", transaction_data_file="TransactionData.csv"):
    DATA_FILE = data_file
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path = parent_path / 'resources' / data_file
    file_path2 = parent_path / 'resources' / transaction_data_file
    # print(f"Reading credentials from: {file_path}")
    promotion_desc= get_csv_value(file_path, banner, TC_ID, Iteration, 'Promotion_description')

    promotion_description_list = promotion_desc.split(';') if isinstance(promotion_desc, str) else promotion_desc

    title_regex = ".*R10PosClient.*"
    app = None
    win = None

    try:
        time.sleep(5)  # Wait for the loyalty popup to appear
        print("Attempting to connect to the application for tender selection...")
        app = Application(backend="uia").connect(title_re=title_regex, timeout=5)
        win = app.window(title_re=title_regex)
        win.set_focus()
        print(f"✅ Connected to POS application for tender selection.")
    except Exception as e:
        print(f"❌ Could not connect to POS application for tender selection: {e}")
        return None

    if promotion_desc:
        print(f"✅ Promotion description found: {promotion_desc}")
        for promo in promotion_description_list:
            promo_ctrl = win.child_window(title_re=f".*{re.escape(promo)}.*", control_type="ListItem")
            if promo_ctrl.exists(timeout=5):
                promo_ctrl_wrapper = promo_ctrl.wrapper_object()
                child = promo_ctrl_wrapper.children()
                if child and len(child) > 2:
                    promo_price = child[2].window_text().strip()
                    promo_price_formatted = f"{abs(float(promo_price)):.2f}"
                    global_instance.total_promotions_price += float(promo_price_formatted)
                    global_instance.promotion_price_list.append(promo_price_formatted)
                    global_instance.promotion_description_list.append(promo)
                    print(f"✅ Promotion '{promo}' is displayed on the POS with price: {promo_price_formatted}.")
                    logger.log(f"✅ Promotion '{promo}' is displayed on the POS with price: {promo_price_formatted}.", status="pass")
                else:
                    print(f"❌ Promotion price is not displayed on the POS.")
                    logger.log(f"❌ Promotion price is not displayed on the POS.", status="fail")
                    logger.take_screenshot(f"Promotion_{promo}_Price_Not_Found")
            else:
                print(f"❌ Promotion '{promo}' not found on the POS.")
                logger.log(f"❌ Promotion '{promo}' not found on the POS.", status="fail")
                logger.take_screenshot(f"Promotion_{promo}_Not_Found")
    else:
        print(f"⚠️ No promotion description found.")
        logger.log(f"⚠️ No promotion description found.", status="info")

    

    app_window = None

    try:
        app_window = Desktop(backend="uia").window(auto_id="GraphicCustomerDisplayID")

        # Verify connection
        app_window.draw_outline()

        parent_container = app_window.child_window(auto_id="ReceiptViewIDCustomerDispaly", control_type="Custom")

        # 2. Get all children of that specific container
        all_children = parent_container.children()
        points = 0.0
        # Based on your dump, the '16' is near the end. 
        # You can find it by looking for the label and taking the next one.
        for i, child in enumerate(all_children):
            if "Points Collected:" in child.window_text():
                # The value '16' is the very next child in the list
                points_value_element = all_children[i + 1]
                points = points_value_element.window_text()
                # print(f"Found Points via Child Navigation: {points}")
                break
        global_instance.loyalty_points = points
        print(f"✅ Loyalty points collected: {global_instance.loyalty_points}")
        logger.log(f"✅ Loyalty points collected: {global_instance.loyalty_points}", status="pass")
    except Exception as e:
        print(f"❌ Could not connect to Customer Display: {e}")
        logger.log(f"❌ Unable to get points from customer screen", status="fail")
        logger.take_screenshot("Customer_Display_Connection_Error")