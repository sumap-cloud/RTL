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


def redeem_choice_offer(choice_offer_list):
    
    # DATA_FILE = "SaleData.csv"
    # RESOURCE_DIR = current_file_path.parent.parent / "resources"

    # parent_path = Path(__file__).parent.parent
    # file_path=parent_path /'resources'/ 'SaleData.csv'
    # # print(f"Reading credentials from: {file_path}")
    # choice_offer_list = get_csv_value(file_path, banner, TC_ID, Iteration, 'Choice_offer')
    
    app1 = None
    win1 = None

    choice_offer = choice_offer_list.split(';') if ';' in choice_offer_list else choice_offer_list
    if isinstance(choice_offer, str):
        choice_offer = [choice_offer]

    print(f"Choice offer(s) to redeem: {choice_offer}")
    if choice_offer!="":
        
        for offer in choice_offer:
            print(f"Processing choice offer: '{offer}'")
            if '_' in offer:
                # Unpacks the list into two strings
                offer_msg, offer_btn_title = offer.split('_')
            else:
                # Fallback if no underscore exists
                offer_msg = offer
                offer_btn_title = "No" 

            # # Now this will work because offer_msg is a string
            # if msg.strip() == offer_msg.strip():
            #     print("Match found!")

            # print(f"Processing choice offer: '{offer}'")
            # offer_msg = offer.split('_') if '_' in offer else offer

            # offer_btn_title = offer.split('_') if '_' in offer else "No"
            # print(f"Processing choice offer: '{offer_msg}' with button title: '{offer_btn_title}'")
            try:
                time.sleep(5)  # Wait for the loyalty popup to appear
                print("Attempting to connect to the application for collectable offer redemption...")
                app1 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
                win1 = app1.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
                # win1.set_focus()
                # win1.print_control_identifiers()
                win1.set_focus()
                popup_title = win1.child_window(auto_id="MessageTextBox", control_type="Edit").exists(timeout=5)

                print(f"✅ Choice offer redeem popup is existed and connected successfully.")
            except Exception as e:
                print(f"❌ Choice offer redeem popup is not exist: {e}")
                logger.log(f"❌ Choice offer redeem popup is not exist: {e}", status="fail")
                logger.take_screenshot("Choice_Offer_Popup_Not_Found")
                return False
            
            # win1.set_focus()
            # popup_title = win1.child_window(title="Do you want me to apply it now?", auto_id="MessageTextBox", control_type="Edit")
            # if popup_title.exists(timeout=5):
            #     print(f"✅ Choice offer popup detected: '{popup_title.window_text()}' offered.")
            if offer_msg == None:
                win1.child_window(title_re=".*No.*", control_type="Button").click_input()
                print("⚠️ No choice offer specified to redeem. Skipping offer redemption.")
                logger.log("⚠️ No choice offer specified to redeem. Skipping offer redemption.", status="pass")

                # return True
            else:
                # offer_btn = win1.child_window(title_re=f".*{offer_btn_title}.*", auto_id="button", control_type="Button")
                
                # msg = win1.child_window(auto_id="MessageTextBox", control_type="Edit").window_text()
                msg = ""
                edit_ctrl = win1.child_window(auto_id="MessageTextBox", control_type="Edit")
                if edit_ctrl.exists(timeout=5):
                    msg = edit_ctrl.window_text()
                else:
                    print("❌ Could not find Edit control with auto_id='MessageTextBox'. Listing all Edit controls for debug:")
                    for ctrl in win1.descendants(control_type="Edit"):
                        print(f"  auto_id: '{getattr(ctrl.element_info, 'automation_id', '')}', text: '{ctrl.window_text()}'")
                    msg = ""
                choice_btn = win1.child_window(title=offer_btn_title, control_type="Button")
                # msg = win1.child_window(auto_id="MessageTextBox", control_type="Edit").window_text()

                # Replace newlines with spaces and collapse multiple spaces into one
                clean_msg = " ".join(msg.replace('\n', ' ').split())

                # 2. Clean up 'offer_msg' (from your CSV/Variable)
                clean_offer = " ".join(offer_msg.replace('\n', ' ').split())

                print(f"Offer popup message: '{clean_msg}' and '{clean_offer}'")
                if clean_msg == clean_offer:
                    choice_btn.click_input()
                    print(f"✅ Redeemed choice offer '{offer_msg}'.")
                    logger.log(f"✅ Handled choice offer '{offer_msg}'.", status="pass")
                else:
                    print(f"❌ Choice offer button '{offer_msg}' not found.")
                    logger.log(f"❌ Choice offer button '{offer_msg}' not found.", status="fail")
                    logger.take_screenshot(f"Choice_Offer_Button_{offer_msg}_Not_Found")
                    return False
        # return True
            # else:
            #     print("❌ Choice offer popup not detected.")
    else:
        try:
            time.sleep(5)  # Wait for the loyalty popup to appear
            print("Attempting to connect to the application for collectable offer redemption...")
            app1 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
            win1 = app1.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
            # win1.set_focus()
            # win1.print_control_identifiers()
            win1.set_focus()
            
            # print("⚠️ No choice offer specified to redeem. Skipping offer redemption.")
            win1.child_window(title="No", control_type="Button").click_input()
            print("⚠️ No choice offer specified to redeem. Skipping offer redemption.")
            logger.log("⚠️ No choice offer specified to redeem. Skipping offer redemption.", status="pass")
        except Exception as e:
            print(f"❌ Error occurred while handling no choice offer: {e}")
            logger.log(f"❌ Error occurred while handling no choice offer.", status="fail")
            logger.take_screenshot("No_Choice_Offer_Error")
            return False

    return True        