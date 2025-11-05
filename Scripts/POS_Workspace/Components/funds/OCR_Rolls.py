import pytesseract
from PIL import Image, ImageGrab, ImageEnhance, ImageFilter, ImageOps
import time
import re
from pywinauto.application import Application

# --- IMPORTANT ---
# You must have Google's Tesseract-OCR engine installed and in your system's PATH.
# Download it from: https://github.com/UB-Mannheim/tesseract/wiki
# After installation, you might need to specify the path to the executable.
# Ensure this path is correct for your system.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_for_light_text(image):
    """
    Preprocessing optimized for light text on a light background by inverting colors.
    """
    img = image.copy()
    img = img.convert('L')
    img = ImageOps.invert(img)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(3.0)
    img = img.point(lambda x: 0 if x < 170 else 255, '1')
    return img

def preprocess_for_dark_text(image):
    """
    Basic preprocessing for standard dark text on a light background.
    """
    img = image.copy()
    img = img.convert('L')
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    img = img.point(lambda x: 0 if x < 180 else 255, '1')
    return img

def find_base_denominations(image_pass1, image_pass2):
    """
    Runs a simple, highly reliable OCR pass to find only the monetary values.
    This is based on your original, working script.
    """
    config = '--psm 11 -c tessedit_char_whitelist=0123456789$c'
    denomination_pattern = r'(\$\d+|\d+c)'
    
    text_pass1 = pytesseract.image_to_string(image_pass1, config=config)
    found_pass1 = re.findall(denomination_pattern, text_pass1)
    
    text_pass2 = pytesseract.image_to_string(image_pass2, config=config)
    found_pass2 = re.findall(denomination_pattern, text_pass2)
    
    return set(found_pass1 + found_pass2)

def find_denominations_with_descriptions(image, config):
    """
    Uses pytesseract.image_to_data to find denominations and their full descriptions.
    """
    data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
    
    words = []
    for i in range(len(data['level'])):
        if int(data['conf'][i]) > 40 and data['text'][i].strip() != '':
            word_text = data['text'][i].strip()
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            words.append({'text': word_text, 'left': x, 'top': y, 'width': w, 'height': h, 'right': x + w, 'bottom': y + h})

    denomination_pattern = r'^(\$\d+|\d+c)$'
    results = []
    
    for word in words:
        if re.match(denomination_pattern, word['text']):
            denomination = word
            full_description = denomination['text']
            
            for other_word in words:
                if other_word is denomination: continue

                is_vertically_aligned = abs((denomination['top'] + denomination['height'] / 2) - (other_word['top'] + other_word['height'] / 2)) < (denomination['height'] * 0.75)
                is_to_the_right = other_word['left'] > denomination['right']
                is_close_horizontally = (other_word['left'] - denomination['right']) < (denomination['width'] * 1.5)

                is_below = other_word['top'] > denomination['bottom']
                is_close_vertically = (other_word['top'] - denomination['bottom']) < (denomination['height'] * 1.5)
                is_horizontally_aligned = abs((denomination['left'] + denomination['width'] / 2) - (other_word['left'] + other_word['width'] / 2)) < (denomination['width'] * 1.0)

                if (is_vertically_aligned and is_to_the_right and is_close_horizontally) or \
                   (is_below and is_close_vertically and is_horizontally_aligned):
                    full_description += ' ' + other_word['text']
                    break
            
            results.append(full_description)
            
    return results

def custom_sort_key(full_text):
    """
    Custom key for sorting denomination strings like '$10 Bundle' numerically.
    """
    match = re.search(r'(\$\d+|\d+c)', full_text)
    if not match: return float('inf')

    denomination = match.group(1)
    value_str = denomination.replace('$', '').replace('c', '')
    value = float(value_str)
    
    return value / 100 if 'c' in denomination else value

def capture_and_process_denominations():
    """
    Captures the screen and uses a hybrid OCR approach to get all denominations accurately.
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
        roi = (rect.left, rect.top, rect.right, rect.top + (rect.height() // 2))
        
        print(f"Capturing top half of the window: {roi}")
        screenshot = ImageGrab.grab(bbox=roi)
        screenshot.save("pos_screenshot_top_half.png")

        processed_light_text = preprocess_for_light_text(screenshot)
        processed_dark_text = preprocess_for_dark_text(screenshot)
        
        processed_light_text.save("processed_inverted.png")
        processed_dark_text.save("processed_basic.png")
        print("Saved 'processed_inverted.png' and 'processed_basic.png' for review.")

        # --- PASS 1: Get all base denominations reliably ---
        base_denominations = find_base_denominations(processed_light_text, processed_dark_text)
        print(f"\n--- Found Base Denominations (Reliable Pass): ---\n{sorted(list(base_denominations), key=custom_sort_key)}")

        # --- PASS 2: Get descriptions ---
        desc_config = '--psm 11 -c tessedit_char_whitelist=0123456789$cABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        found_pass1 = find_denominations_with_descriptions(processed_light_text, desc_config)
        found_pass2 = find_denominations_with_descriptions(processed_dark_text, desc_config)
        described_denominations = set(found_pass1 + found_pass2)
        print(f"\n--- Found Descriptions (Detailed Pass): ---\n{sorted(list(described_denominations), key=custom_sort_key)}")

        # --- MERGE RESULTS ---
        final_results = {}
        # First, add all base denominations as a fallback
        for denom in base_denominations:
            final_results[denom] = denom
        
        # Now, overwrite with the described versions if they exist
        for desc_denom in described_denominations:
            base_match = re.search(r'(\$\d+|\d+c)', desc_denom)
            if base_match:
                base_key = base_match.group(1)
                if len(desc_denom) > len(final_results.get(base_key, '')):
                    final_results[base_key] = desc_denom
        
        # --- NEW LOGIC: Assume 'Roll' for any undescribed denominations ---
        for key, value in final_results.items():
            # If the value is the same as the key, it means no description was found
            if key == value:
                final_results[key] = f"{value} Roll"

        # Get the final list of values and sort it
        sorted_denominations = sorted(list(final_results.values()), key=custom_sort_key)

        print("\n" + "="*40)
        print("    FINAL COMBINED & SORTED DENOMINATIONS")
        print("="*40)
        if sorted_denominations:
            print(sorted_denominations)
        else:
            print("[No denominations found.]")
        print("="*40 + "\n")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the main function
capture_and_process_denominations()
