import cv2
import pytesseract
import numpy as np
from pywinauto.application import Application
from PIL import Image
import re

# --- IMPORTANT ---
# You must have Google's Tesseract-OCR engine installed and in your system's PATH.
# Download it from: https://github.com/UB-Mannheim/tesseract/wiki
# After installation, you might need to specify the path to the executable, like this:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_all_text_from_window(win, preprocess=True, region=None):
    """
    Extracts all detectable text from a region of the window using OCR.

    Args:
        win: The pywinauto window object.
        preprocess: Whether to apply image preprocessing.
        region: Optional tuple (left, top, right, bottom) to specify a search area.

    Returns:
        A list of all detected text strings.
    """
    # 1. Capture a screenshot of the window
    screenshot = win.capture_as_image()

    # If a region is specified, crop the screenshot to that region
    if region:
        screenshot = screenshot.crop(region)

    screenshot_np = np.array(screenshot)
    img_rgb = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    if preprocess:
        # 2. Image Pre-processing with OpenCV
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        denoised = cv2.medianBlur(binary, 3)
        processed_img = denoised
    else:
        processed_img = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    # 3. Use Tesseract to get all data
    custom_config = r'--oem 1 --psm 6'
    ocr_data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT, config=custom_config)

    # 4. Collect and return all non-empty text strings
    all_text = []
    n_boxes = len(ocr_data['level'])
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text:
            all_text.append(text)
            (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
            cv2.rectangle(img_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow('OCR Full Extraction', img_rgb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return all_text

def find_element_by_ocr(win, target_text, preprocess=True, region=None):
    """
    Finds a UI element by text within a specific region of the window.

    Args:
        win: The pywinauto window object.
        target_text: The text of the UI element to find.
        preprocess: Whether to apply image preprocessing.
        region: Optional tuple (left, top, right, bottom) to specify a search area.

    Returns:
        A tuple (x, y) of the center coordinates of the found text, or None if not found.
    """
    screenshot = win.capture_as_image()
    
    # If a region is specified, crop the screenshot
    if region:
        screenshot = screenshot.crop(region)

    screenshot_np = np.array(screenshot)
    img_rgb = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    if preprocess:
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        denoised = cv2.medianBlur(binary, 3)
        processed_img = denoised
    else:
        processed_img = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    custom_config = r'--oem 1 --psm 6'
    ocr_data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT, config=custom_config)

    n_boxes = len(ocr_data['level'])
    for i in range(n_boxes):
        if re.search(target_text, ocr_data['text'][i], re.IGNORECASE):
            (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
            
            # Adjust coordinates to be relative to the full window if a region was used
            if region:
                center_x = x + w // 2 + region[0]
                center_y = y + h // 2 + region[1]
            else:
                center_x = x + w // 2
                center_y = y + h // 2

            print(f"Found '{target_text}' at coordinates: ({center_x}, {center_y})")
            # For visualization, we draw on the original uncropped image
            full_screenshot_np = np.array(win.capture_as_image())
            full_img_rgb = cv2.cvtColor(full_screenshot_np, cv2.COLOR_RGB2BGR)
            # Adjust box coordinates for drawing
            draw_x = x + region[0] if region else x
            draw_y = y + region[1] if region else y
            cv2.rectangle(full_img_rgb, (draw_x, draw_y), (draw_x + w, draw_y + h), (0, 255, 0), 2)
            cv2.imshow('OCR Detection', full_img_rgb)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return (center_x, center_y)

    print(f"'{target_text}' not found.")
    return None

if __name__ == "__main__":
    try:
        app_title_regex = ".*R10PosClient.*"
        print(f"Attempting to connect to application with title regex: {app_title_regex}")

        app = Application(backend="uia").connect(title_re=app_title_regex, timeout=20)
        win = app.window(title_re=app_title_regex)
        win.set_focus()

        # --- OPTIONAL: Define a region to speed up the search ---
        # These are example coordinates. You'll need to find the right values for your app.
        # You can use a tool like Paint to find pixel coordinates.
        # Format: (left, top, right, bottom)
        keypad_region = (500, 450, 800, 750) # Example region for the keypad

        # --- 1. Extract all text from a specific region ---
        print("\n--- Extracting all detectable text from the keypad region ---")
        detected_texts = extract_all_text_from_window(win, region=keypad_region)
        print("Detected text elements:")
        for text in detected_texts:
            print(f"- {text}")
        print("-----------------------------------------------------\n")

        # --- 2. Find and click on a specific UI element within that region ---
        target_text_to_find = "OK" 
        print(f"Now, attempting to find and click on: '{target_text_to_find}' in the keypad region")
        element_coords = find_element_by_ocr(win, target_text_to_find, region=keypad_region)

        if element_coords:
            win.click_input(coords=element_coords)
            print(f"Clicked on '{target_text_to_find}'")

    except Exception as e:
        print(f"An error occurred: {e}")
