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
            print(f"✅ Choice Offer popup detected: '{choice_offer_popup.window_text()}'.")
            if choice_offer == "" or choice_offer is None:
                win.child_window(auto_id="SkipChoiceOfferPrompt", control_type="Button").click_input()
                print("✅ Clicked 'No, save these discounts for later' on Choice Offer popup.")
                global_instance.reward_redeem_status = True
            else:
                try:
                    # 1. Locate the main container holding all the offer boxes
                    offer_list = win.child_window(auto_id="ContainerButtonList", control_type="List")
                    
                    # 2. Get all individual offer boxes (ListItems)
                    offer_items = offer_list.children(control_type="ListItem")
                    
                    print(f"🔍 Found {len(offer_items)} offer(s) on screen. Scanning...")
                    
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
                        
                        print(f"--- Text from Offer Box {index + 1} ---")
                        print(extracted_text)
                        
                        # 6. Check if this box contains the text we want (using .lower() for safety)
                        if choice_offer.lower() in extracted_text.lower():
                            print(f"✅ Choice offer found with description: '{extracted_text}'")
                            

                            # 7. Find and click the 'Use now' button INSIDE this specific item
                            button_clicked = False
                            for btn in item.descendants(control_type="Button"):
                                if btn.element_info.automation_id == "Usenow":
                                    btn.click_input()
                                    print("🖱️ Clicked 'Use now'.")
                                    button_clicked = True
                                    break # Stop looking once we click it
                            
                            if button_clicked:
                                print("✅ Successfully redeemed the choice offer!")
                            else:
                                print(f"❌ Target offer containing '{choice_offer}' was not found.")

                except Exception as e:
                    print(f"⚠️ Error interacting with offers: {e}")

        else:
            print("⚠️ Choice Offer popup did not appear within the expected time.")
    except Exception as e:
        print(f"⚠️ Error handling Choice Offer popup: {e}")


   
