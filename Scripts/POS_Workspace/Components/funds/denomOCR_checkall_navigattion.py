import pytesseract
from PIL import Image, ImageGrab, ImageEnhance, ImageFilter, ImageOps
import time
import re
from pywinauto.application import Application
from pytesseract import Output

#NavigationPath = ""  # Example path to click a specific denomination
# --- IMPORTANT ---
# You must have Google's Tesseract-OCR engine installed and in your system's PATH.
# Download it from: https://github.com/UB-Mannheim/tesseract/wiki
# After installation, you might need to specify the path to the executable, like this:
# Make sure this path is correct for your system.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_for_light_text(image):
    """
    Preprocessing optimized for light text on a light background by inverting colors.
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
    '5c' -> 0.05, '$1' -> 1.0, etc. Works for Coins, Notes, and Rolls.
    """
    # Find the first monetary value in the string
    match = re.search(r'(\$\d+|\d+c)', denomination)
    if not match: return float('inf') # Should not happen with current logic

    value_str = match.group(1).replace('$', '').replace('c', '')
    value = float(value_str)
    
    if 'c' in match.group(1):
        return value / 100
    return value


# --- Main Functions for Automation ---

def find_and_click_tab(win, tab_name):
    """
    Finds a tab by its text ("Coin", "Note", or "Roll") using OCR and clicks it.
    """
    print(f"\nAttempting to find and click the '{tab_name}' tab...")
    try:
        rect = win.rectangle()
        roi_left, roi_top, roi_right, roi_bottom = rect.left, rect.top, rect.right, rect.top + (rect.height() // 2)
        screenshot = ImageGrab.grab(bbox=(roi_left, roi_top, roi_right, roi_bottom))

        img_gray = screenshot.convert('L')
        config = '--psm 11' 
        ocr_data = pytesseract.image_to_data(img_gray, config=config, output_type=Output.DICT)
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            confidence = int(ocr_data['conf'][i])
            if text.lower() == tab_name.lower() and confidence > 70:
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                center_x, center_y = x + w // 2, y + h // 2
                
                print(f"Found '{tab_name}' tab at window coordinates: ({center_x}, {center_y}). Clicking...")
                win.click_input(coords=(center_x, center_y))
                return True
                
        print(f"Warning: Could not find the '{tab_name}' tab with sufficient confidence.")
        return False

    except Exception as e:
        print(f"An error occurred while trying to click tab '{tab_name}': {e}")
        return False

def process_and_click_denominations(win, view_name="Denominations"):
    """
    Captures the screen, finds all coin/note/roll denominations, and clicks them.
    This is the unified, working logic for all tabs.
    """
    rect = win.rectangle()
    roi_left, roi_top, roi_right, roi_bottom = rect.left, rect.top, rect.right, rect.top + (rect.height() // 2)
    
    print(f"Capturing top half of the window: ({roi_left}, {roi_top}, {roi_right}, {roi_bottom})")
    screenshot = ImageGrab.grab(bbox=(roi_left, roi_top, roi_right, roi_bottom))
    screenshot.save(f"pos_screenshot_{view_name.lower()}.png")

    processed_light_text = preprocess_for_light_text(screenshot)
    processed_dark_text = preprocess_for_dark_text(screenshot)
    
    processed_light_text.save(f"processed_{view_name.lower()}_inverted.png")
    processed_dark_text.save(f"processed_{view_name.lower()}_basic.png")
    print(f"Saved '{view_name}' processing images for review.")

    # Using a strict whitelist to only find the basic monetary values.
    # This improves reliability for all tabs.
    config = '--psm 11 -c tessedit_char_whitelist=0123456789$c'
    denomination_pattern = r'(\$\d+|\d+c)'
    denomination_coords = {}

    # --- OCR PASS 1 (for light text) ---
    print(f"\n--- Scanning for {view_name} (Inverted Image)... ---")
    ocr_data_pass1 = pytesseract.image_to_data(processed_light_text, config=config, output_type=Output.DICT)
    for i in range(len(ocr_data_pass1['text'])):
        text = ocr_data_pass1['text'][i]
        if re.fullmatch(denomination_pattern, text):
            x, y, w, h = ocr_data_pass1['left'][i], ocr_data_pass1['top'][i], ocr_data_pass1['width'][i], ocr_data_pass1['height'][i]
            center_x, center_y = x + w // 2, y + h // 2
            denomination_coords[text] = (center_x, center_y)
            print(f"Found '{text}' at window coordinates: ({center_x}, {center_y})")

    # --- OCR PASS 2 (for dark text) ---
    print(f"\n--- Scanning for {view_name} (Basic Image)... ---")
    ocr_data_pass2 = pytesseract.image_to_data(processed_dark_text, config=config, output_type=Output.DICT)
    for i in range(len(ocr_data_pass2['text'])):
        text = ocr_data_pass2['text'][i]
        if re.fullmatch(denomination_pattern, text):
            x, y, w, h = ocr_data_pass2['left'][i], ocr_data_pass2['top'][i], ocr_data_pass2['width'][i], ocr_data_pass2['height'][i]
            center_x, center_y = x + w // 2, y + h // 2
            denomination_coords[text] = (center_x, center_y)
            print(f"Found '{text}' at window coordinates: ({center_x}, {center_y})")

    if not denomination_coords:
        print(f"\n[No {view_name} found to click in this view.]")
        return

    sorted_denominations = sorted(list(denomination_coords.keys()), key=custom_sort_key)

    print("\n" + "="*40)
    print(f"     FINAL COMBINED & SORTED {view_name.upper()}")
    print("="*40)
    print(sorted_denominations)
    print("="*40 + "\n")

    print(f"--- Starting to click {view_name} in order ---")
    for denom in sorted_denominations:
        coords = denomination_coords[denom]
        print(f"Clicking on '{denom}' at {coords}...")
        win.click_input(coords=coords)
        time.sleep(1)

    print(f"\nAll {view_name} in this view have been clicked.")

    # --- Final printout for Rolls as requested ---
    if view_name == "Rolls":
        described_rolls = []
        for denom in sorted_denominations:
            # Re-calculate value to determine if it's a "Bundle"
            value_str = denom.replace('$', '').replace('c', '')
            value = float(value_str)
            is_cent = 'c' in denom
            
            if not is_cent and value >= 5:
                described_rolls.append(f"{denom} Bundle")
            else:
                described_rolls.append(f"{denom} Roll")
        
        print("\n" + "="*40)
        print("     FINAL COMBINED & SORTED ROLL DENOMINATIONS")
        print("="*40)
        print(described_rolls)

def navigate_and_click_path(win, path):
    """
    Navigates to a tab and clicks a specific denomination based on a path string.
    Example path: "Note>$100"
    """
    try:
        tab_name, denomination = path.split('>')
        print(f"\n--- Navigating path: Clicking '{denomination}' in '{tab_name}' tab ---")

        if not find_and_click_tab(win, tab_name):
            print(f"Path navigation failed: Could not find tab '{tab_name}'.")
            return
        
        time.sleep(1.5) # Wait for UI to update

        # Now, find the specific denomination
        rect = win.rectangle()
        roi_left, roi_top, roi_right, roi_bottom = rect.left, rect.top, rect.right, rect.top + (rect.height() // 2)
        screenshot = ImageGrab.grab(bbox=(roi_left, roi_top, roi_right, roi_bottom))

        processed_light_text = preprocess_for_light_text(screenshot)
        processed_dark_text = preprocess_for_dark_text(screenshot)

        config = '--psm 11 -c tessedit_char_whitelist=0123456789$c'
        
        # Combine data from both preprocessing methods
        all_ocr_data = [
            pytesseract.image_to_data(processed_light_text, config=config, output_type=Output.DICT),
            pytesseract.image_to_data(processed_dark_text, config=config, output_type=Output.DICT)
        ]

        for ocr_data in all_ocr_data:
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i]
                if text == denomination:
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    center_x, center_y = x + w // 2, y + h // 2
                    print(f"Found '{denomination}' at coordinates ({center_x}, {center_y}). Clicking...")
                    win.click_input(coords=(center_x, center_y))
                    print(f"Successfully clicked path '{path}'.")
                    return True # Exit after finding and clicking

        print(f"Path navigation failed: Could not find denomination '{denomination}' in tab '{tab_name}'.")
        return True
    except Exception as e:
        print(f"An error occurred during path navigation for '{path}': {e}")


def all_denomination_check():
    """
    The main function that orchestrates the entire process:
    1. Connects to the application.
    2. Clicks 'Coin' tab and processes denominations.
    3. Clicks 'Note' tab and processes denominations.
    4. Clicks 'Roll' tab and processes denominations.
    5. Performs a specific path-based navigation and click.
    """
    try:
        app_title_regex = ".*R10PosClient.*" 
        print(f"Attempting to connect to application with title regex: {app_title_regex}")
        
        app = Application(backend="uia").connect(title_re=app_title_regex, timeout=20)
        win = app.window(title_re=app_title_regex)
        
        print("Successfully connected. Bringing window to the front...")
        win.set_focus()
        time.sleep(2) 

        # --- STEP 1: PROCESS COINS ---
        print("\n" + "#"*50)
        print("### STEP 1: PROCESSING COINS")
        print("#"*50)
        if find_and_click_tab(win, "Coin"):
            time.sleep(1.5)
            process_and_click_denominations(win, "Coins")
        else:
            print("Could not find 'Coin' tab. Skipping coin processing.")

        # --- STEP 2: PROCESS NOTES ---
        print("\n" + "#"*50)
        print("### STEP 2: PROCESSING NOTES")
        print("#"*50)
        if find_and_click_tab(win, "Note"):
            time.sleep(1.5)
            process_and_click_denominations(win, "Notes")
        else:
            print("Could not find 'Note' tab. Skipping note processing.")

        # --- STEP 3: PROCESS ROLLS ---
        print("\n" + "#"*50)
        print("### STEP 3: PROCESSING ROLLS")
        print("#"*50)
        if find_and_click_tab(win, "Roll"):
            time.sleep(1.5)
            # Re-using the same proven logic for rolls
            process_and_click_denominations(win, "Rolls")
        else:
            print("Could not find 'Roll' tab. Skipping roll processing.")
        return True

        # --- STEP 4: PATH-BASED NAVIGATION ---
        # print("\n" + "#"*50)
        # print("### STEP 4: PERFORMING PATH-BASED SELECTION")
        # print("#"*50)
        #navigate_and_click_path(win, NavigationPath)
        #"Note>$100"
        #print("\nAutomation workflow has finished.")

    except Exception as e:
        print(f"A critical error occurred during the main workflow: {e}")

# Run the main function
#if __name__ == "__main__":
    #all_denomination_check("Note>$100")
