import sys
from pathlib import Path
import re
import pytesseract
from PIL import ImageGrab

from pywinauto import Application, timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Redeem_collectable_offer import redeem_collectable_offer
from Components import global_instance


app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")

# from Components.Redeem_collectable_offer import redeem_collectable_offer

win.set_focus()
win.print_control_identifiers()

global_instance.app = app
global_instance.win = win

# redeem_collectable_offer("Collectable", "You have earned 2 Bricks Home packs, Are you collecting these? If yes, please call the attendant._No")


# txt = win.child_window(auto_id="Instructions", control_type="Text").window_text()
# print(f"Text from 'Instructions' control: '{txt}'")
# txt_updated = txt.replace('\n', ' ')
# print(f"Updated text: '{txt_updated}'")





# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# target_offer_text = "Would you like to apply your Woolworths Credit Card 10 percent off your shop?"  # The unique text to look for in the offer card

# try:
#     # 1. Locate the main container holding all the offer boxes
#     offer_list = win.child_window(auto_id="ContainerButtonList", control_type="List")
    
#     # 2. Get all individual offer boxes (ListItems)
#     offer_items = offer_list.children(control_type="ListItem")
    
#     print(f"🔍 Found {len(offer_items)} offer(s) on screen. Scanning...")
    
#     for index, item in enumerate(offer_items):
#         # 3. Get the bounding box for THIS SPECIFIC offer card
#         rect = item.rectangle()
#         pad = 5
#         bbox = (rect.left - pad, rect.top - pad, rect.right + pad, rect.bottom + pad)
        
#         # 4. Take a mini-screenshot of just this offer card
#         screenshot = ImageGrab.grab(bbox)
#         clean_image = screenshot.convert('L') # Grayscale
#         width, height = clean_image.size
#         zoomed_image = clean_image.resize((width * 2, height * 2)) # Zoom for clarity
        
#         # 5. Run OCR on this specific card
#         # Replace newlines with spaces to make phrase matching easier
#         extracted_text = pytesseract.image_to_string(zoomed_image, config='--psm 6').replace('\n', ' ')
        
#         print(f"--- Text from Offer Box {index + 1} ---")
#         print(extracted_text)
        
#         # 6. Check if this box contains the text we want (using .lower() for safety)
#         if target_offer_text.lower() in extracted_text.lower():
#             print(f"✅ Match found in Box {index + 1}!")
            
#             # # 7. Find and click the 'Use now' button INSIDE this specific item
#             # use_now_btn = item.child_window(auto_id="Usenow", control_type="Button")
#             # use_now_btn.click_input()
#             # print("🖱️ Clicked 'Use now'.")

#             # 7. Find and click the 'Use now' button INSIDE this specific item
#             button_clicked = False
#             for btn in item.descendants(control_type="Button"):
#                 if btn.element_info.automation_id == "Usenow":
#                     btn.click_input()
#                     print("🖱️ Clicked 'Use now'.")
#                     button_clicked = True
#                     break # Stop looking once we click it
            
#             if button_clicked:
#                 print("✅ Successfully interacted with the offer!")
#             else:
#                 print(f"❌ Target offer containing '{target_offer_text}' was not found.")
    
#     # Optional: If the target offer isn't there, click "No, save these discounts"
#     # skip_btn = win.child_window(auto_id="SkipChoiceOfferPrompt", control_type="Button")
#     # skip_btn.click_input()
    


# except Exception as e:
#     print(f"⚠️ Error interacting with offers: {e}")
   

