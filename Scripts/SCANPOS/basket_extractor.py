from pywinauto.application import Application
from PIL import ImageGrab, ImageOps
import pytesseract
import json
import re

# --- TESSERACT CONFIGURATION ---
# If Tesseract is not in your system's PATH, you'll need to uncomment
# and update the line below to point to your tesseract.exe
# Example:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# -------------------------------

def parse_all_text_elements(element):
    """
    Finds all descendant controls with text and organizes them into a dictionary.
    """
    print("--- Finding all descendant elements with non-empty text titles ---")
    item_data = {
        "Description": None,
        "Quantity": None,
        "Unit": None,
        "Subtotal": None,
        "Discount": None,
        "Message": None,
        "CodeLabel": None,
        "ItemID": None,
        "TotalInfo": None,
        "OtherText": []
    }
    
    try:
        all_descendants = element.descendants()
        print(f"Found {len(all_descendants)} total descendants. Parsing known AutoIDs...")

        for elem in all_descendants:
            try:
                title = elem.window_text()
                if not title:
                    continue

                auto_id = elem.element_info.automation_id
                
                if auto_id == "DescriptionTextBlock":
                    item_data["Description"] = title
                elif auto_id == "QuantityTextBlock":
                    item_data["Quantity"] = title
                elif auto_id == "MessageTextBlock":
                    item_data["Message"] = title
                elif auto_id == "CodeStr":
                    item_data["CodeLabel"] = title
                elif auto_id == "ItemIdTextBlockID":
                    item_data["ItemID"] = title
                elif auto_id == "13.00": # From your log, this seems to be the subtotal
                    item_data["Subtotal"] = title
                elif auto_id == "3.00": # From your log, this seems to be the discount
                    item_data["Discount"] = title
                elif "total in basket" in title:
                    item_data["TotalInfo"] = title
                elif (auto_id is None or auto_id == "") and title == "Unit": # Handle 'Unit'
                    item_data["Unit"] = title
                elif (auto_id is None or auto_id == "") and title.isdigit(): # Handle other numbers
                    pass # Ignoring '0' and '1' for now
                else:
                    # Add any other recognized text, just in case
                    if auto_id != "ItemDetailsViewID":
                        item_data["OtherText"].append(f"Title: '{title}', AutoID: '{auto_id}'")

            except Exception as e:
                pass
                
    except Exception as e:
        print(f"Error finding descendants: {e}")
        
    return item_data

def ocr_original_price(element):
    """
    Takes a targeted screenshot of the top-right corner of the element
    to find the original price.
    """
    print("\n--- Performing targeted OCR for Original Price ---")
    try:
        rect = element.rectangle()
        
        # Define a *smaller* bounding box for the original price.
        # Based on screenshots and logs, it's in the top-right corner.
        # Full coords: (L531, T70, R846, B245)
        # Description ends at R745. Price is to the right of that.
        # Price is vertically aligned with description (T79 to B113).
        
        # Bounding Box: (left, top, right, bottom)
        bbox = (rect.left + 210, rect.top + 5, rect.right - 5, rect.top + 50)
        # Tuned box: (531+210=741, 70+5=75, 846-5=841, 70+50=120)
        # This creates a box: (L741, T75, R841, B120)
        # This should cover the "$10.00" area.
        
        print(f"Targeted OCR Bounding Box: {bbox}")
        
        img = ImageGrab.grab(bbox=bbox, all_screens=True)
        
        # Pre-process: convert to grayscale
        img = img.convert('L')
        
        # Save for debugging
        img.save("debug_ocr_price_screenshot.png")
        print("Saved debug_ocr_price_screenshot.png (grayscale crop)")

        # Use Tesseract
        custom_config = r'--psm 7' # Treat as single text line
        text = pytesseract.image_to_string(img, config=custom_config)
        
        if not text.strip():
            print("[No text found by OCR in this region]")
            return None
            
        print(f"OCR Raw Text: '{text.strip()}'")
        
        # Find something that looks like a price
        # This regex looks for digits, a decimal, and two more digits.
        match = re.search(r'[\$\d-]*\.\d{2}', text)
        
        if match:
            price = match.group(0)
            print(f"Parsed Original Price: {price}")
            return price
        else:
            print("[OCR found text, but no price matched]")
            return None

    except Exception as e:
        print(f"An error occurred during OCR process: {e}")
        return None

def capture_basket_text_hybrid():
    """
    Connects to the POS application and uses a hybrid approach
    to capture all item details.
    """
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=20)
    except Exception as e:
        print(f"Error connecting to application: {e}")
        print("Please ensure the R10PosClient application is running.")
        return

    win = app.window(title_re=".*R10PosClient.*")
    win.set_focus()

    description_container = win.child_window(control_type="Custom", auto_id="LineDetailsViewID")
    if not description_container.exists():
        print("Error: Could not find the 'LineDetailsViewID' container.")
        return
        
    item_view = description_container.child_window(auto_id="ItemDetailsViewID", control_type="Custom")
    
    search_base_element = item_view
    if not item_view.exists():
        print("Could not find 'ItemDetailsViewID', using 'LineDetailsViewID' directly.")
        search_base_element = description_container

    # 1. Get all data possible with pywinauto
    item_data = parse_all_text_elements(search_base_element)
    
    # 2. Get the missing original price with OCR
    original_price = ocr_original_price(search_base_element)
    item_data["OriginalPrice"] = original_price

    # 3. Print the final combined data
    print("\n--- Combined Item Details ---")
    print(json.dumps(item_data, indent=2))
    print("-------------------------------")


if __name__ == "__main__":
    capture_basket_text_hybrid()

