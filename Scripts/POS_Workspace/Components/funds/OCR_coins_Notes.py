import pytesseract
from PIL import Image, ImageGrab, ImageEnhance, ImageFilter, ImageOps
import time
import re
from pywinauto.application import Application
from pytesseract import Output

# --- IMPORTANT ---
# You must have Google's Tesseract-OCR engine installed and in your system's PATH.
# Download it from: https://github.com/UB-Mannheim/tesseract/wiki
# After installation, you might need to specify the path to the executable, like this:
# Make sure this path is correct for your system.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_for_light_text(image):
    """
    Preprocessing optimized for light text on a light background by inverting colors.
    This is the method that successfully found '$1' and '$2' in a previous run.
    """
    img = image.copy()
    # Convert to grayscale
    img = img.convert('L')
    # Invert colors to make light text dark
    img = ImageOps.invert(img)
    # Enhance contrast aggressively
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(3.0)
    # Apply a threshold
    img = img.point(lambda x: 0 if x < 170 else 255, '1')
    return img

def preprocess_for_dark_text(image):
    """
    Basic preprocessing for standard dark text on a light background.
    This is more likely to correctly identify '5c'.
    """
    img = image.copy()
    # Convert to grayscale
    img = img.convert('L')
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    # Apply a threshold
    img = img.point(lambda x: 0 if x < 180 else 255, '1')
    return img

def custom_sort_key(denomination):
    """
    Custom key for sorting denomination strings numerically.
    '5c' -> 0.05, '$1' -> 1.0, etc.
    """
    value_str = denomination.replace('$', '').replace('c', '')
    value = float(value_str)
    if 'c' in denomination:
        return value / 100
    return value

def find_and_click_denominations():
    """
    Captures the screen, runs two different preprocessing methods,
    combines the OCR results to find all denominations, and then clicks them.
    """
    try:
        app_title_regex = ".*R10PosClient.*" 
        print(f"Attempting to connect to application with title regex: {app_title_regex}")
        
        app = Application(backend="uia").connect(title_re=app_title_regex, timeout=20)
        win = app.window(title_re=app_title_regex)
        
        print("Successfully connected. Bringing window to the front...")
        win.set_focus()
        time.sleep(2) 

        rect = win.rectangle()
        
        # We only capture the top half, as in the original script
        roi_left, roi_top, roi_right, roi_bottom = rect.left, rect.top, rect.right, rect.top + (rect.height() // 2)
        
        print(f"Capturing top half of the window: ({roi_left}, {roi_top}, {roi_right}, {roi_bottom})")
        screenshot = ImageGrab.grab(bbox=(roi_left, roi_top, roi_right, roi_bottom))
        screenshot.save("pos_screenshot_top_half.png")

        # --- RUN BOTH PREPROCESSING METHODS ---
        processed_light_text = preprocess_for_light_text(screenshot)
        processed_dark_text = preprocess_for_dark_text(screenshot)
        
        processed_light_text.save("processed_inverted.png")
        processed_dark_text.save("processed_basic.png")
        print("Saved 'processed_inverted.png' and 'processed_basic.png' for review.")

        # --- OCR CONFIG ---
        # PSM 11: Find as much text as possible in no particular order.
        config = '--psm 11 -c tessedit_char_whitelist=0123456789$c'
        denomination_pattern = r'(\$\d+|\d+c)'
        
        # --- NEW: Dictionary to store denominations and their coordinates ---
        denomination_coords = {}

        # --- OCR PASS 1 (for light text) ---
        print("\n--- Scanning for denominations (Inverted Image)... ---")
        ocr_data_pass1 = pytesseract.image_to_data(processed_light_text, config=config, output_type=Output.DICT)
        for i in range(len(ocr_data_pass1['text'])):
            text = ocr_data_pass1['text'][i]
            if re.fullmatch(denomination_pattern, text):
                x = ocr_data_pass1['left'][i]
                y = ocr_data_pass1['top'][i]
                w = ocr_data_pass1['width'][i]
                h = ocr_data_pass1['height'][i]
                
                # Calculate center coordinates relative to the window
                center_x = x + w // 2
                center_y = y + h // 2
                
                denomination_coords[text] = (center_x, center_y)
                print(f"Found '{text}' at window coordinates: ({center_x}, {center_y})")

        # --- OCR PASS 2 (for dark text) ---
        print("\n--- Scanning for denominations (Basic Image)... ---")
        ocr_data_pass2 = pytesseract.image_to_data(processed_dark_text, config=config, output_type=Output.DICT)
        for i in range(len(ocr_data_pass2['text'])):
            text = ocr_data_pass2['text'][i]
            if re.fullmatch(denomination_pattern, text):
                x = ocr_data_pass2['left'][i]
                y = ocr_data_pass2['top'][i]
                w = ocr_data_pass2['width'][i]
                h = ocr_data_pass2['height'][i]

                # Calculate center coordinates relative to the window
                center_x = x + w // 2
                center_y = y + h // 2

                # Add or overwrite coordinate data
                denomination_coords[text] = (center_x, center_y)
                print(f"Found '{text}' at window coordinates: ({center_x}, {center_y})")


        # --- COMBINE, SORT, AND CLICK RESULTS ---
        if not denomination_coords:
            print("\n[No denominations found to click.]")
            return

        sorted_denominations = sorted(list(denomination_coords.keys()), key=custom_sort_key)

        print("\n" + "="*40)
        print("    FINAL COMBINED & SORTED DENOMINATIONS")
        print("="*40)
        print(sorted_denominations)
        print("="*40 + "\n")

        # --- NEW: Clicking logic ---
        print("--- Starting to click denominations in order ---")
        for denom in sorted_denominations:
            coords = denomination_coords[denom]
            print(f"Clicking on '{denom}' at {coords}...")
            # Use click_input for more reliable clicking in UIA backend
            win.click_input(coords=coords)
            time.sleep(1) # Pause for 1 second between clicks

        print("\nAll denominations have been clicked.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the main function
find_and_click_denominations()
