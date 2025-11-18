from pywinauto import Application
import time
import re
import pytesseract
from PIL import ImageGrab
import sys
import cv2  # Added for OpenCV
import numpy as np  # Added for OpenCV

# --- IMPORTANT ---
# Set this path to your Tesseract installation.
# This is the line you were asking about.
# Find where you installed Tesseract-OCR and put the path to tesseract.exe here.
# The 'r' before the string is important.
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # Test if tesseract is found by getting its version
    pytesseract.get_tesseract_version()
    print("Tesseract-OCR found at the specified path.")
except Exception as e:
    print("--- TESSERACT_CMD_ERROR ---")
    print(f"Could not find Tesseract at the path: '{pytesseract.pytesseract.tesseract_cmd}'")
    print("Please install Tesseract-OCR from the official GitHub page.")
    print("Then, update the 'pytesseract.pytesseract.tesseract_cmd' path in this script (line 15).")
    print(f"Error details: {e}")
    sys.exit(1) # Exit if Tesseract is not found


def connect_to_app():
    """
    Connects to the R10PosClient application window.
    """
    print("Connecting to app...")
    try:
        # Connect to the app with a timeout
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        print("Successfully connected to window.")
        return app, win
    except Exception as e:
        print(f"Failed to connect to application: {e}")
        return None, None

def validate_header_with_ocr(win):
    """
    Takes a screenshot of the window's header, crops it,
    and uses Tesseract OCR to find expected text.
    """
    if not win:
        print("Cannot run OCR, no valid window provided.")
        return

    try:
        print("\n--- Starting OCR Header Validation ---")
        rect = win.rectangle()
        
        if not rect or rect.width() <= 0 or rect.height() <= 0:
            print("Error: Invalid window coordinates for OCR.")
            return

        bbox_coords = (rect.left, rect.top, rect.right, rect.bottom)
        print(f"Taking screenshot for OCR at: {bbox_coords}")
        screenshot = ImageGrab.grab(bbox=bbox_coords)

        # Crop to the header area (top 60 pixels)
        header_height = 60
        header_area = (0, 0, rect.width(), header_height)
        header_image = screenshot.crop(header_area)
        
        # Save for debugging if needed
        # header_image.save("debug_header_crop.png")

        # Use Tesseract to read text from the header image
        header_text = pytesseract.image_to_string(header_image)
        print(f"--- OCR Found Text ---\n{header_text}\n----------------------")

        # --- Validation ---
        expected_texts = ["Woolworths", "POS:", "testing"]
        all_found = True

        for text in expected_texts:
            if re.search(text, header_text, re.IGNORECASE):
                print(f"VALIDATION: Found '{text}'")
            else:
                print(f"VALIDATION FAILED: Did not find '{text}'")
                all_found = False
        
        if all_found:
            print("-------------------------------------")
            print("OCR VALIDATION SUCCESSFUL: All text found.")
            print("-------------------------------------")
        else:
            print("-------------------------------------")
            print("OCR VALIDATION FAILED: Missing some text.")
            print("-------------------------------------")

    except Exception as e:
        print("An error occurred during OCR validation.")
        print("Tesseract Error: " + str(e))
        if "tesseract is not installed" in str(e).lower():
            print("\n*** TESSERACT_CMD_ERROR ***")
            print(f"The path '{pytesseract.pytesseract.tesseract_cmd}' is incorrect.")
            print("Please check the path at the top of this script.")


def validate_orange_logo_with_opencv(win, exist=True):
    """
    Takes a screenshot of the window's header, crops to the logo area,
    and uses OpenCV to check for the color orange.

    Args:
        win: The pywinauto window object.
        exist (bool): If True, validates that the logo IS present.
                      If False, validates that the logo IS ABSENT.
    """
    if not win:
        print("Cannot run OpenCV, no valid window provided.")
        return

    try:
        # --- MODIFICATION: Updated print based on 'exist' parameter ---
        if exist:
            print("\n--- Starting OpenCV Logo Validation (Expecting Logo to EXIST) ---")
        else:
            print("\n--- Starting OpenCV Logo Validation (Expecting Logo to be ABSENT) ---")
            
        rect = win.rectangle()
        
        if not rect or rect.width() <= 0 or rect.height() <= 0:
            print("Error: Invalid window coordinates for OpenCV.")
            return

        bbox_coords = (rect.left, rect.top, rect.right, rect.bottom)
        print(f"Taking screenshot for OpenCV at: {bbox_coords}")
        screenshot = ImageGrab.grab(bbox=bbox_coords)
        
        # --- Crop to Header ---
        header_height = 60
        header_area = (0, 0, rect.width(), header_height)
        header_image = screenshot.crop(header_area)
        
        # --- Crop to Logo Area (in top-right) ---
        width, height = header_image.size
        
        left = int(width * 0.50)
        top = 5
        right = int(width * 0.70)
        bottom = height - 5
        
        logo_area_coords = (left, top, right, bottom)
        logo_crop_pil = header_image.crop(logo_area_coords)
        
        # Save for debugging if needed
        logo_crop_pil.save("debug_logo_crop.png")
        print(f"Saved logo crop to debug_logo_crop.png at coords {logo_area_coords}")

        # --- OpenCV Color Detection ---
        logo_cv = cv2.cvtColor(np.array(logo_crop_pil), cv2.COLOR_RGB2BGR)
        hsv_image = cv2.cvtColor(logo_cv, cv2.COLOR_BGR2HSV)

        # Define the color range for "orange" in HSV
        lower_orange = np.array([5, 100, 100])
        upper_orange = np.array([25, 255, 255])

        mask = cv2.inRange(hsv_image, lower_orange, upper_orange)
        orange_pixel_count = cv2.countNonZero(mask)

        # --- MODIFICATION: New validation logic based on 'exist' parameter ---
        
        threshold = 100
        logo_is_present = orange_pixel_count > threshold

        print(f"Found {orange_pixel_count} orange pixels (Threshold: {threshold}). Logo is present: {logo_is_present}")

        # Case 1: We expect the logo to exist AND it does
        if exist and logo_is_present:
            print("--------------------------------------------------")
            print("VALIDATION SUCCESSFUL: Found the orange logo as expected.")
            print("--------------------------------------------------")
        
        # Case 2: We expect the logo to exist BUT it doesn't
        elif exist and not logo_is_present:
            print("--------------------------------------------------")
            print(f"VALIDATION FAILED: Expected the orange logo, but it was ABSENT.")
            print(f"(Found {orange_pixel_count} pixels, but threshold is {threshold})")
            print("--------------------------------------------------")
        
        # Case 3: We expect the logo to be absent BUT it is present
        elif not exist and logo_is_present:
            print("--------------------------------------------------")
            print(f"VALIDATION FAILED: Expected the orange logo to be ABSENT, but it was PRESENT.")
            print(f"(Found {orange_pixel_count} pixels. Threshold is {threshold})")
            print("--------------------------------------------------")
        
        # Case 4: We expect the logo to be absent AND it is
        elif not exist and not logo_is_present:
            print("--------------------------------------------------")
            print("VALIDATION SUCCESSFUL: The orange logo was ABSENT, as expected.")
            print("--------------------------------------------------")
        
        # --- End of Modification ---

    except Exception as e:
        print(f"An error occurred during OpenCV validation: {e}")
        if "cv2" in str(e).lower() or "numpy" in str(e).lower():
            print("\n*** ERROR: OpenCV (cv2) or NumPy is not installed.")
            print("Please run: pip install opencv-python numpy")


if __name__ == "__main__":
    app, window = connect_to_app()

    if window:
        # Run the original OCR text validation
        validate_header_with_ocr(window)
        
        # --- MODIFICATION: Demonstrate the updated OpenCV validation ---
        
        # 1. Default behavior: Expect logo to exist (exist=True is the default)
        #print("\nTest Case 1: Checking if logo EXISTS (default)")
        #validate_orange_logo_with_opencv(window) 
        
        # 2. Explicitly expect logo to exist
        print("\nTest Case 2: Checking if logo EXISTS (explicit True)")
        validate_orange_logo_with_opencv(window, exist=True)
        
        # 3. Explicitly expect logo to be ABSENT
        #print("\nTest Case 3: Checking if logo is ABSENT (explicit False)")
        #validate_orange_logo_with_opencv(window, exist=False)
        # --- End of Modification ---
        
    else:
        print("Could not find the R10PosClient window.")