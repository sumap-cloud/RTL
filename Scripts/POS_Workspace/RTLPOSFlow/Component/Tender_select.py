# child_window(auto_id="TenderGroupMenuViewExitButton", control_type="Button")
# child_window(title="Remove Loyalty", auto_id="commandsLowerButtonsRemove Loyalty", control_type="Button")

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
from Component.Update_csv import update_csv_value
from Component import global_instance
from Component.Cash_drawer import cashdrawer_move_and_close
from Reusable.Tendermode_balance import get_balance_due
from Component.report import logger


def tender_select(tender_type, banner, TC_ID, Iteration, data_file="SaleData.csv", transaction_data_file="TransactionData.csv"):
    DATA_FILE = data_file
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path = parent_path / 'resources' / data_file
    file_path2 = parent_path / 'resources' / transaction_data_file
    # print(f"Reading credentials from: {file_path}")
    
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
        return False
    
    if tender_type.strip() == "":
        print("⚠️ No tender type specified.")
        logger.log("⚠️ No tender type specified to complete transaction.", status="fail")
        logger.take_screenshot("No_Tender_Type_Error")
        return False
    elif win.child_window(auto_id="TenderGroupMenuViewExitButton", control_type="Button").exists(timeout=5):

        if global_instance.is_loyaltycard_added:
            win.child_window(title="Remove Loyalty", auto_id="commandsLowerButtonsRemove Loyalty", control_type="Button").exists(timeout=5)
            print("✅ Loyalty card is currently added. 'Remove Loyalty' button is available.")
        else:
            print("⚠️ Loyalty card was not added. Skipping tender selection as it may not be in the correct state.")

        try:
            tender_btn = win.child_window(title_re=f".*{tender_type}.*", auto_id="TenderItemTemplateCash", control_type="Button")
            if tender_btn.exists(timeout=5):
                tender_btn.click_input()
                print(f"✅ Selected tender type: '{tender_type}'.")
                logger.log(f"✅ Selected tender type: '{tender_type}'.", status="pass")
            else:
                print(f"❌ Tender button '{tender_type}' not found.")
                logger.log(f"❌ Tender button '{tender_type}' not found.", status="fail")
                logger.take_screenshot(f"Tender_Button_{tender_type}_Not_Found")
        except Exception as e:
            print(f"❌ Error during tender selection: {e}")
            logger.log(f"❌ Error during tender selection.", status="fail")
            logger.take_screenshot("Tender_Selection_Error")

        if tender_type.lower() == "cash":
            # Wait for the EFTPOS popup to appear
            time.sleep(5)
            win.child_window(title="Cash",auto_id="TenderItemTemplateCash", control_type="Button").click_input()
            cash_suggestion_window =  win.child_window(auto_id="SuggestedCashListBox", control_type="List")

            if cash_suggestion_window.exists(timeout=5):
                most_matching_suggested_cash = win.child_window(auto_id="SuggestedCashListBoxButton0", control_type="Button")
                # raw_text = win.child_window(auto_id="SuggestedCashListBoxButton0", control_type="Button")

                all_children = most_matching_suggested_cash.children()

                # 3. Check if the list is empty to prevent an IndexError
                if len(all_children) > 0:
                    
                    # Grab the very first child (Index 0)
                    first_child = all_children[0]
                    
                    # 4. Extract the text
                    raw_text = first_child.window_text().strip()
                    # logger.log(f"✅ The most matching suggested cash button: '{raw_text}'", status="pass")
                else:
                    print("❌ Error: Could not find suggested cash button.")
                    logger.log(f"❌ Error: Could not find suggested cash button.", status="fail")
                    logger.take_screenshot("Suggested_Cash_Button_Not_Found")


                print(f"🔍 Raw text from the most matching suggested cash button: '{raw_text}'")
                suggested_amount_format = 0.0
                total_amount_format = 0.0

                if not raw_text:
                    print("❌ No text found on the most matching suggested cash button.")
                else:
                    suggested_amount_str = raw_text.replace("$", "").strip()
                    suggested_amount_format = round(float(suggested_amount_str), 1)
                    print(f"💵 Suggested Cash Amount: {suggested_amount_format}")

                   
                    balance_due_tendermode = None
                    
                    balance_due_tendermode = get_balance_due()

                    print(f"Extracted Balance Due from Tender Mode: '{balance_due_tendermode}'")



                    global_instance.total_amount_tendermode = balance_due_tendermode
                    # global_instance.total_amount_tendermode = balance_due_tendermode.replace("$", "").strip()

                    # 1. Safely grab the values, defaulting to 0.0 if they are empty strings or None
                    tender_amount = float(global_instance.total_amount_tendermode) if global_instance.total_amount_tendermode else 0.0
                    redeem_amount = float(global_instance.redeem_amount) if global_instance.redeem_amount else 0.0
                    promo_price = float(global_instance.promotions_price) if global_instance.promotions_price else 0.0
                    total_sale = float(global_instance.total_amount_salemode) if global_instance.total_amount_salemode else 0.0

                    # 2. Now perform your mathematical comparison safely
                    if total_sale == (tender_amount + redeem_amount + promo_price):
                        print("✅ Total amount in tender mode matches total amount in sale mode.")
                        
                    else:
                        print(f"❌ Total amount mismatch! Sale mode: {total_sale}, Tender mode: {tender_amount}, Redeem amount: {redeem_amount}, Promotions price: {promo_price}")

                    update_csv_value(file_path2, banner, TC_ID,Iteration, 'TransactionAmount', float(global_instance.total_amount_tendermode))

                    total_amount_format = round(float(global_instance.total_amount_tendermode), 1)
                    # total_amount_format = round(float(global_instance.total_amount_salemode)-float(global_instance.promotions_price)-float(global_instance.redeem_amount), 1)
                    print(f"💵 Formatted Balance Due from Tender Mode: {balance_due_tendermode}")
                    print(f"💰 Total Amount from Tender Mode: {total_amount_format}")

                if suggested_amount_format != "":
                    print("Clicking on the most matching suggested cash amount...")
                    most_matching_suggested_cash.click_input()

                    if total_amount_format <= 30.0:
                        try:
                            win2 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*", timeout=15)
                            app2 = win2.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
                            app2.set_focus()

                            receipt_popup = app2.child_window(title="No", control_type="Button")
                            if receipt_popup.exists(timeout=5):
                                receipt_popup.click_input()
                                print("✅ Found the receipt suppress popup, and handling it by clicking 'No' to proceed with the transaction.")
                            else:
                                print("⚠️ Receipt suppress popup not detected. Continuing without handling it.")
                            # app.print_control_identifiers()
                        except Exception as e:
                            print(f"❌ Receipt suppress popup handling error: {e}")
                            logger.log(f"❌ Receipt suppress popup handling error: {e}", status="fail")
                            logger.take_screenshot("Receipt_Suppress_Popup_Handling_Error")

                    time.sleep(5)  # Wait for the cash drawer to open before attempting to close it
                    cashdrawer_move_and_close(status_to_set="close")

                    # print(f"✅ Clicked on the most matching suggested cash amount: '{global_instance.total_amount_tendermode}'.")
                    print("Cash drawer has been moved and closed.")
                else:
                    print(f"❌ Suggested cash amount '{suggested_amount_format}' does not match the balance due '{total_amount_format}'.")
            else:
                print("❌ Cash tender suggestion is not detected.")
                logger.take_screenshot("Cash_Tender_Suggestion_Not_Detected")
                return False
                # update_csv_value(file_path, banner, TC_ID, Iteration, 'Eftpos_popup', 'No')

    else:
        print("❌ Not in the correct state for tender selection. Required buttons not found.")
        return False

    return True
