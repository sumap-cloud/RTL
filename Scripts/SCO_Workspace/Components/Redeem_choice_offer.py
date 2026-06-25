import sys
import time
import pytesseract
from pathlib import Path
from PIL import ImageGrab
from pywinauto import Application, timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def redeem_choice_offer(choice_offer):

    app = global_instance.app
    win = global_instance.win
    # win.print_control_identifiers()  # For debugging: print all controls to find the correct ones for the choice offer popup
    try:
        time.sleep(3)  # Wait for the choice offer popup to appear
        win.set_focus()
        choice_offer_popup = win.child_window(auto_id="ContainerButtonList", control_type="List")
        
        if choice_offer_popup.exists(timeout=5):
            # logger.log(f"✅ Choice Offer popup detected: '{choice_offer_popup.window_text()}'.", status="pass")
            print(f"✅ Choice Offer popup detected: '{choice_offer_popup.window_text()}'.")
            if choice_offer == "" or choice_offer is None:
                win.child_window(auto_id="SkipChoiceOfferPrompt", control_type="Button").click_input()
                logger.log("✅ Clicked 'No, save these discounts for later' on Choice Offer popup.", status="pass")
                print("✅ Clicked 'No, save these discounts for later' on Choice Offer popup.")
                global_instance.reward_redeem_status = True
                return True
            else:
                try:
                    # 1. Locate the main container holding all the offer boxes
                    offer_list = win.child_window(auto_id="ContainerButtonList", control_type="List")
                    
                    # 2. Get all individual offer boxes (ListItems)
                    offer_items = offer_list.children(control_type="ListItem")
                    
                    # logger.log(f"✅ Found {len(offer_items)} offer(s) on screen. Scanning...", status="pass")
                    print(f"✅ Found {len(offer_items)} offer(s) on screen. Scanning...")

                    if not offer_items:
                        logger.log("❌ No choice offers found on screen.", status="fail")
                        print("❌ No choice offers found on screen.")
                        logger.take_screenshot("Choice_Offer_List_Empty")
                        return False
                    
                    offer_found = False
                    for index, item in enumerate(offer_items):
                        # 3. Get the bounding box for THIS SPECIFIC offer card
                        rect = item.rectangle()
                        pad = 5
                        bbox = (rect.left - pad, rect.top - pad, rect.right + pad, rect.bottom + pad)
                        
                        # 4. Take a mini-screenshot of just this offer card
                        screenshot = ImageGrab.grab(bbox)
                        clean_image = screenshot.convert('L') # Grayscale
                        width, height = clean_image.size
                        zoomed_image = clean_image.resize((width * 2, height * 2)) # Zoom for clarity
                        
                        # 5. Run OCR on this specific card
                        # Replace newlines with spaces to make phrase matching easier
                        extracted_text = pytesseract.image_to_string(zoomed_image, config='--psm 6').replace('\n', ' ')
                        
                        # logger.log(f"✅ Text captured from Offer Box {index + 1}.", status="pass")
                        print(f"✅ Text captured from Offer Box {index + 1}.")
                        
                        # 6. Check if this box contains the text we want (using .lower() for safety)
                        if choice_offer.lower() in extracted_text.lower():
                            offer_found = True
                            logger.log(f"✅ Choice offer found with description: '{extracted_text}'.", status="pass")
                            print(f"✅ Choice offer found with description: '{extracted_text}'.")
                            

                            # 7. Find and click the 'Use now' button INSIDE this specific item
                            button_clicked = False
                            for btn in item.descendants(control_type="Button"):
                                if btn.element_info.automation_id == "Usenow":
                                    btn.click_input()
                                    logger.log("✅ Clicked 'Use now'.", status="pass")
                                    print("✅ Clicked 'Use now'.")
                                    button_clicked = True
                                    break # Stop looking once we click it
                            
                            if button_clicked:
                                logger.log("✅ Successfully redeemed the choice offer!", status="pass")
                                print("✅ Successfully redeemed the choice offer!")
                                global_instance.reward_redeem_status = True
                                return True
                            else:
                                logger.log(f"❌ 'Use now' button not found for choice offer '{choice_offer}'.", status="fail")
                                print(f"❌ 'Use now' button not found for choice offer '{choice_offer}'.")
                                logger.take_screenshot("Choice_Offer_UseNow_Button_Not_Found")

                    if not offer_found:
                        if len(offer_items) == 1:
                            for btn in offer_items[0].descendants(control_type="Button"):
                                if btn.element_info.automation_id == "Usenow":
                                    btn.click_input()
                                    logger.log(
                                        f"✅ Only one choice offer was displayed; clicked 'Use now' for '{choice_offer}' without OCR text match.",
                                        status="pass"
                                    )
                                    print(f"✅ Only one choice offer displayed — clicked 'Use now' for '{choice_offer}'.")
                                    global_instance.reward_redeem_status = True
                                    return True
                        logger.log(f"❌ Target offer containing '{choice_offer}' was not found.", status="fail")
                        print(f"❌ Target offer containing '{choice_offer}' was not found.")
                        logger.take_screenshot("Choice_Offer_Text_Not_Found")
                        return False

                except Exception as e:
                    logger.log(f"❌ Error interacting with offers: {e}", status="fail")
                    print(f"❌ Error interacting with offers: {e}")
                    logger.take_screenshot("Choice_Offer_Interaction_Error")
                    return False

        else:
            logger.log("❌ Choice Offer popup did not appear within the expected time.", status="fail")
            print("❌ Choice Offer popup did not appear within the expected time.")
            logger.take_screenshot("Choice_Offer_Popup_Not_Appeared")
            return False
    except Exception as e:
        logger.log(f"❌ Error handling Choice Offer popup: {e}", status="fail")
        print(f"❌ Error handling Choice Offer popup: {e}")
        logger.take_screenshot("Choice_Offer_Popup_Handler_Error")
        return False


   
